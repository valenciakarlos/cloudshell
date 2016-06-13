from quali_remote import *
import atexit
import inspect
import time
import subprocess

class Vcenter(object):
    def __init__(self, vcenter_params):
        self.pyVmomi = __import__("pyVmomi")
        self.server = vcenter_params['IP']
        self.username = vcenter_params['user']
        self.password = vcenter_params['password']
        self.content = ''
        self.service_instance = ''
        self.connect_to_vcenter()

    def create_datacenter(self, dcname=None, folder=None):
        datacenter = self.get_obj([self.pyVmomi.vim.Datacenter], dcname)
        if datacenter is not None:
            print("datacenter %s already exists" % dcname)
            return datacenter
        else:
            if len(dcname) > 79:
                raise ValueError("The name of the datacenter must be under 80 characters.")
            if folder is None:
                folder = self.service_instance.content.rootFolder
            if folder is not None and isinstance(folder, self.pyVmomi.vim.Folder):
                print("Creating Datacenter %s " % dcname)
                dc_moref = folder.CreateDatacenter(name=dcname)
                return dc_moref

    def create_cluster(self, cluster_name, datacenter, drs_enabled, drs_automation_level, ha_enabled):

        cluster = self.get_obj([self.pyVmomi.vim.ClusterComputeResource], cluster_name)
        if cluster is not None:
            print("cluster already exists")
            return cluster
        else:
            if cluster_name is None:
                raise ValueError("Missing value for name.")
            if datacenter is None:
                raise ValueError("Missing value for datacenter.")

            print("Creating Cluster %s " % cluster_name )
            # get cluster spec
            cluster_spec = self.pyVmomi.vim.cluster.ConfigSpecEx()
            # get DC object
            dc = self.get_obj([self.pyVmomi.vim.Datacenter], datacenter)
            host_folder = dc.hostFolder

            # set Cluster DRS setting
            drs_config = self.pyVmomi.vim.cluster.DrsConfigInfo()
            drs_config.enabled = drs_enabled
            drs_config.defaultVmBehavior = drs_automation_level
            drs_config.vmotionRate = 3
            cluster_spec.drsConfig = drs_config

            # set Power MGMT
            dpm_config = self.pyVmomi.vim.cluster.DpmConfigInfo()
            dpm_config.enabled = False
            dpm_config.hostPowerActionRate = 3
            cluster_spec.dpmConfig = dpm_config

            # set HA Setting
            das_config = self.pyVmomi.vim.cluster.DasConfigInfo()
            das_config.enabled = ha_enabled
            das_config.hostMonitoring = "enabled"
            das_config.failoverLevel = 1
            das_config.admissionControlEnabled = True
            das_config.vmMonitoring = 'vmAndAppMonitoring'

            default_vm_settings = self.pyVmomi.vim.cluster.DasVmSettings()
            default_vm_settings.restartPriority = "high"
            # default_vm_settings.isolationResponse = "powerOff"

            vm_tools_monitoring = self.pyVmomi.vim.cluster.VmToolsMonitoringSettings()
            vm_tools_monitoring.enabled = True
            vm_tools_monitoring.failureInterval = 30
            vm_tools_monitoring.minUpTime = 120
            vm_tools_monitoring.maxFailures = 3
            vm_tools_monitoring.maxFailureWindow = 3600

            default_vm_settings.vmToolsMonitoringSettings = vm_tools_monitoring
            das_config.defaultVmSettings = default_vm_settings
            cluster_spec.dasConfig = das_config


            cluster = host_folder.CreateClusterEx(name=cluster_name, spec=cluster_spec)
            return cluster

    def add_host(self, cluster_name, hostname, sslthumbprint,  username, password):
        host = self.get_obj([self.pyVmomi.vim.HostSystem], hostname)
        if host is not None:
            print("host already exists")
            return host
        else:
            if hostname is None:
                raise ValueError("Missing value for name.")
            cluster = self.get_obj([self.pyVmomi.vim.ClusterComputeResource], cluster_name)
            if cluster is None:
                error = 'Error - Cluster %s not found. Unable to add host %s' % (cluster_name, hostname)
                raise ValueError(error)

            try:
                hostspec = self.pyVmomi.vim.host.ConnectSpec(hostName=hostname,userName=username, sslThumbprint=sslthumbprint, password=password, force=True)
                task=cluster.AddHost(spec=hostspec,asConnected=True)
            except self.pyVmomi.vmodl.MethodFault as error:
                print "Caught vmodl fault : " + error.msg
                return -1
            self.wait_for_task(task)
            host = self.get_obj([self.pyVmomi.vim.HostSystem], hostname)
            return host

    def create_nasdatastore(self, host_name, nas_ip, nas_mount, datastore_name):

        if datastore_name is None:
            raise ValueError("Missing value for datastore_name.")
        if nas_ip is None:
            raise ValueError("Missing value for nas_ip.")
        if nas_mount is None:
            raise ValueError("Missing value for nas_mount.")
        if host_name is None:
            raise ValueError("Missing value for host_name.")

        print(host_name)
        host = self.get_obj([self.pyVmomi.vim.HostSystem], host_name)
        datastore_spec = self.pyVmomi.vim.host.NasVolume.Specification()
        datastore_spec.remoteHost=nas_ip
        datastore_spec.remotePath=nas_mount
        datastore_spec.localPath=datastore_name
        datastore_spec.accessMode="readWrite"

        datastore=host.configManager.datastoreSystem.CreateNasDatastore(datastore_spec)
        return datastore

    def get_vlan_ranges(self, vlan_ids):
        if not vlan_ids:
            return []

        if ',' not in vlan_ids:
            return [self.pyVmomi.vim.NumericRange(start=int(vlan_ids), end=int(vlan_ids))]
        else:
            vlans = []
            for grp in vlan_ids.split(','):
                if '-' not in grp:
                    vlans.append(self.pyVmomi.vim.NumericRange(start=int(grp), end=int(grp)))
                else:
                    parts = grp.split('-')
                    vlans.append(self.pyVmomi.vim.NumericRange(start=int(parts[0]), end=int(parts[1])))

            return vlans

    def add_dvPort_group(self, dvswitch, portgroup_name, num_ports, vlanmode, vlan_ids):
        if type(dvswitch) == str:
            dvswitch = self.get_obj([self.pyVmomi.vim.DistributedVirtualSwitch], dvswitch)

        if not portgroup_name:
            return
        
        exists = self.get_obj([self.pyVmomi.vim.dvs.DistributedVirtualPortgroup], portgroup_name)
        if exists:
            return

        dv_pg_spec = self.pyVmomi.vim.dvs.DistributedVirtualPortgroup.ConfigSpec()
        dv_pg_spec.name = portgroup_name
        dv_pg_spec.numPorts = num_ports
        dv_pg_spec.type = self.pyVmomi.vim.dvs.DistributedVirtualPortgroup.PortgroupType.earlyBinding

        dv_pg_spec.defaultPortConfig = self.pyVmomi.vim.dvs.VmwareDistributedVirtualSwitch.VmwarePortConfigPolicy()
        dv_pg_spec.defaultPortConfig.securityPolicy = self.pyVmomi.vim.dvs.VmwareDistributedVirtualSwitch.SecurityPolicy()

        if vlanmode.lower() == 'none':
            dv_pg_spec.defaultPortConfig.vlan = self.pyVmomi.vim.dvs.VmwareDistributedVirtualSwitch.VlanIdSpec()
            dv_pg_spec.defaultPortConfig.vlan.vlanId = 0
        elif vlanmode.lower() == 'vlan':
            dv_pg_spec.defaultPortConfig.vlan = self.pyVmomi.vim.dvs.VmwareDistributedVirtualSwitch.VlanIdSpec()
            dv_pg_spec.defaultPortConfig.vlan.vlanId = int(vlan_ids)
        elif vlanmode.lower() == 'trunk':
            dv_pg_spec.defaultPortConfig.vlan = self.pyVmomi.vim.dvs.VmwareDistributedVirtualSwitch.TrunkVlanSpec()
            dv_pg_spec.defaultPortConfig.vlan.vlanId = self.get_vlan_ranges(vlan_ids)

        dv_pg_spec.defaultPortConfig.securityPolicy.allowPromiscuous = self.pyVmomi.vim.BoolPolicy(value=True)
        dv_pg_spec.defaultPortConfig.securityPolicy.forgedTransmits = self.pyVmomi.vim.BoolPolicy(value=True)

        dv_pg_spec.defaultPortConfig.vlan.inherited = False
        dv_pg_spec.defaultPortConfig.securityPolicy.macChanges = self.pyVmomi.vim.BoolPolicy(value=False)
        dv_pg_spec.defaultPortConfig.securityPolicy.inherited = False

        task = dvswitch.AddDVPortgroup_Task([dv_pg_spec])
        self.wait_for_task(task)
        print "Successfully created DV Port Group ", portgroup_name

    def create_dvSwitch(self, datacenter, dvs_name, dvs_version, num_ports, hosts, nics):
        exists = self.get_obj([self.pyVmomi.vim.DistributedVirtualSwitch], dvs_name)
        if exists:
            return exists
        
        dvs_host_configs = []
        dvs_create_spec = self.pyVmomi.vim.DistributedVirtualSwitch.CreateSpec()
        dvs_config_spec = self.pyVmomi.vim.VmwareDistributedVirtualSwitch.ConfigSpec()
        dvs_config_spec.name = dvs_name
        dvs_config_spec.maxPorts = 2000
        dvs_config_spec.maxMtu = 9000
        dvs_config_spec.uplinkPortPolicy = self.pyVmomi.vim.DistributedVirtualSwitch.NameArrayUplinkPortPolicy()
        content = self.content
        _dc = self.get_obj([self.pyVmomi.vim.Datacenter], datacenter)
        if len(nics) == 1 and len(hosts) > 1:
            nics = nics * len(hosts)

        uplink_port_names = []
        for pnidx in range(0, num_ports):
            uplink_port_names.append("dvUplink%d" % pnidx)
        dvs_config_spec.uplinkPortPolicy.uplinkPortName = uplink_port_names

        h_index = 0
        for h in hosts:
            host = content.searchIndex.FindByIp(_dc, h, False)
            if host:
                pnic_specs = []
                for pn in nics[h_index].split(','):
                    if pn:
                        pnic_spec = self.pyVmomi.vim.dvs.HostMember.PnicSpec()
                        pnic_spec.pnicDevice = pn
                        pnic_specs.append(pnic_spec)
                
                dvs_host_config = self.pyVmomi.vim.dvs.HostMember.ConfigSpec()
                dvs_host_config.operation = self.pyVmomi.vim.ConfigSpecOperation.add
                dvs_host_config.host = host
                dvs_host_configs.append(dvs_host_config)
                dvs_host_config.backing = self.pyVmomi.vim.dvs.HostMember.PnicBacking()
                dvs_host_config.backing.pnicSpec = pnic_specs
                dvs_config_spec.host = dvs_host_configs
                h_index += 1

        dvs_create_spec.configSpec = dvs_config_spec
        dvs_create_spec.productInfo = self.pyVmomi.vim.dvs.ProductSpec(version=dvs_version)

        _network_folder = _dc.networkFolder
        task = _network_folder.CreateDVS_Task(dvs_create_spec)
        self.wait_for_task(task)
        print "Successfully created DVS ", dvs_name
        return self.get_obj([self.pyVmomi.vim.DistributedVirtualSwitch], dvs_name)

    def get_obj(self, vimtype, name):
        """
        Get the vsphere object associated with a given text name
        """
        obj = None
        container = self.content.viewManager.CreateContainerView(self.content.rootFolder, vimtype, True)
        for c in container.view:
            if c.name == name:
                obj = c
                break
        return obj

    def wait_for_task(self, task):
        while task.info.state == (self.pyVmomi.vim.TaskInfo.State.running or self.pyVmomi.vim.TaskInfo.State.queued):
            time.sleep(2)

        if task.info.state == self.pyVmomi.vim.TaskInfo.State.success:
            if task.info.result is not None:
                out = 'Task completed successfully, result: %s' % (task.info.result,)
                print out
        elif task.info.state == self.pyVmomi.vim.TaskInfo.State.error:
            out = 'Error - Task did not complete successfully: %s' % (task.info.error,)
            raise ValueError(out)
        return task.info.result

    def connect_to_vcenter(self):
        from pyVim import connect
        import ssl
        
        print("Connecting to %s using username %s" % (self.server, self.username))
        try:
            default_context = ssl._create_default_https_context
            _create_unverified_https_context = ssl._create_unverified_context
        except AttributeError:
            # Legacy Python that doesn't verify HTTPS certificates by default
            pass
        else:
             # Handle target environment that doesn't support HTTPS verification
            ssl._create_default_https_context = _create_unverified_https_context

        context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
        context.verify_mode = ssl.CERT_NONE
        requests.packages.urllib3.disable_warnings()
        self.service_instance = connect.SmartConnect(host=self.server,
                                                     user=self.username,
                                                     pwd=self.password,
                                                     port=443,
                                                     sslContext=context)
            
        ssl._create_default_https_context = default_context
        self.content = self.service_instance.RetrieveContent()
        about = self.service_instance.content.about
        print("Connected to %s, %s" % (self.server, about.fullName))
        atexit.register(connect.Disconnect, self.service_instance)

    def getsslThumbprint(self, ip):
        ssl_thumbprint = powershell('''
            $ComputerName = "''' + ip + '''"
            $Timeoutms=3000
            $port = 443
            [Net.ServicePointManager]::ServerCertificateValidationCallback = {$true}
            $req = [Net.HttpWebRequest]::Create("https://$computerName`:$port/")
            $req.Timeout = $Timeoutms
            try {$req.GetResponse() | Out-Null} catch {write-error "Couldn't connect to $computerName on port $port"; continue}
            if (!($req.ServicePoint.Certificate)) {write-error "No Certificate returned on $computerName"; continue}
            $certinfo = $req.ServicePoint.Certificate
            $a1 = $certinfo.GetCertHashString();
            write-host '<%<%', $a1
            ''').split('<%<%')[1].strip()


        # p1 = subprocess.Popen(('echo', '-n'), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # p2 = subprocess.Popen(('openssl', 's_client', '-connect', '{0}:443'.format(ip)), stdin=p1.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # p3 = subprocess.Popen(('openssl', 'x509', '-noout', '-fingerprint', '-sha1'), stdin=p2.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # out = p3.stdout.read()
        # ssl_thumbprint = out.split('=')[-1].strip()
        ssl_thumbprint = ":".join(ssl_thumbprint[i:i+2] for i in range(0, len(ssl_thumbprint), 2))

        return ssl_thumbprint

def vmPower(vmname, command, vcenter_ip, vcenter_user, vcenter_password):
    script = '''Add-PSSnapin VMware.VimAutomation.Core\n
    Connect-VIServer -Server ''' + vcenter_ip + ''' -User ''' + vcenter_user + ''' -Password ''' + vcenter_password + ''' -WarningAction SilentlyContinue\n '''
    if command.lower() == 'start':
        script += '''Start-VM -VM ''' + vmname + ''' -Confirm:$false'''
    elif command.lower() == 'stop':
        script += '''Stop-VM -VM ''' + vmname + ''' -Confirm:$false'''
    elif command.lower() == 'restart':
        script += '''Restart-VM -VM ''' + vmname + ''' -Confirm:$false'''
    powershell(script)

def deleteVMs(vmname, vcenter_ip, vcenter_user, vcenter_password):
    script = '''Add-PSSnapin VMware.VimAutomation.Core\n
    Connect-VIServer -Server ''' + vcenter_ip + ''' -User ''' + vcenter_user + ''' -Password ''' + vcenter_password + ''' -WarningAction SilentlyContinue\n
    Remove-VM -VM ''' + vmname + ''' -DeletePermanently -Confirm:$false'''
    powershell(script)

def getAdapterMac(vmname, vcenter_ip, vcenter_user, vcenter_password):
    script = '''Add-PSSnapin VMware.VimAutomation.Core\n
    Connect-VIServer -Server ''' + vcenter_ip + ''' -User ''' + vcenter_user + ''' -Password ''' + vcenter_password + ''' -WarningAction SilentlyContinue\n
    $a = Get-NetworkAdapter -VM "''' + vmname + '''" | Foreach-Object {$_.ExtensionData.MacAddress}\n
    write-host '<%<%', $a'''
    macs = powershell(script).split('<%<%')[1].strip().split(' ')
    return macs

def deployVM(string):
    with open(r'c:\ProgramData\QualiSystems\Shells.log', 'a') as f:
        f.write("Deploying VM using OVFTools with: " + string + '\r\n')
    subprocess.check_output(
        'C:\Program Files\VMware\VMware OVF Tool\ovftool.exe ' + string
    )

def changeVMadapter(vmname, nics, networks, vcenter_ip, vcenter_user, vcenter_password):
    script = '''Add-PSSnapin VMware.VimAutomation.Core\n
        Connect-VIServer -Server ''' + vcenter_ip + ''' -User ''' + vcenter_user + ''' -Password ''' + vcenter_password + ''' -WarningAction SilentlyContinue \n'''
    for (nic, network) in zip(nics, networks):
        if network != '':
            script += '''$myNetworkAdapters = Get-VM ''' + vmname + '''| Get-NetworkAdapter -Name "Network adapter ''' + nic + '''" \n'''
            script += '''Set-NetworkAdapter -NetworkAdapter $myNetworkAdapters -StartConnected:$true -Confirm:$false -Connected:$true -NetworkName "''' + network + '''" \n'''
    powershell (script)

def invokeScript(script, vmname, vmuser, vmpass, retry, delay, vcenter_ip, vcenter_user, vcenter_password):
    start = '''Add-PSSnapin VMware.VimAutomation.Core\n
    Connect-VIServer -Server ''' + vcenter_ip + ''' -User ''' + vcenter_user + ''' -Password ''' + vcenter_password + ''' -WarningAction SilentlyContinue\n'''
    script += ''
    script = start + 'Invoke-VMScript -ScriptText ' + script + ''' -VM "''' + vmname + '''" -GuestUser ''' + vmuser + ''' -GuestPassword ''' + vmpass
    while retry > 0:
        try:
            ans = powershell(script)
            if not 'error' in ans.lower():
                retry = 0
                finish = True
                return ans
            else:
                retry += -1
                time.sleep(delay)
                finish = ans
        except Exception, e:
            retry += -1
            time.sleep(delay)
            finish = e.message
    if finish is not True:
        raise Exception(finish)

def cleanup(vmname, vcenter_ip, vcenter_user, vcenter_password):
    script = '''Add-PSSnapin VMware.VimAutomation.Core\n
    Connect-VIServer -Server ''' + vcenter_ip + ''' -User ''' + vcenter_user + ''' -Password ''' + vcenter_password + ''' -WarningAction SilentlyContinue\n
    Stop-VM -VM ''' + vmname + ''' -Confirm:$false \n
    Remove-VM -VM ''' + vmname + ''' -Confirm:$false -DeletePermanently\n'''
    try:
        powershell(script)
    except:
        pass

def rebootESX(esxs, vcenter_ip, vcenter_user, vcenter_password):
    script = '''Add-PSSnapin VMware.VimAutomation.Core
$vcenterip = \'''' + vcenter_ip + '''\'
$vcenteruser = \'''' + vcenter_user + '''\'
$vcenterpassword = \'''' + vcenter_password + '''\'
$ESXs = \'''' + esxs + '''\'
$ESXs = $ESXs.Split(",")


Connect-VIServer $vcenterip -user $vcenteruser -Password $vcenterpassword


foreach ($ESXiServer in $ESXs) {
    Restart-VMHost $ESXiServer -Confirm:$false -RunAsync -Force
}

$timeout = new-timespan -Minutes 20
$sw = [diagnostics.stopwatch]::StartNew()
$connectedCount = 0
$runonce = 0..($ESXs.Count-1) | foreach { $false }
sleep 200
while ($sw.elapsed -lt $timeout){
    if ($connectedCount -ge $ESXs.Count){
        Write-Host "All ESXs Connected"
        break
    }
    sleep 10
    $n = 0
    foreach ($ESXiServer in $ESXs) {
        $v = Get-VMHost -Name $ESXiServer
        if ($v.ConnectionState -eq "Connected") {
            if ($runonce[$n] -eq $false){
                $connectedCount += 1
                $runonce[$n] = $true
                Write-Host $v " Connected"
            }
        }
        $n += 1
    }
    Write-Host "Sleeping 10 secs.."
}


        '''
    try:
        powershell(script)
        #print "ESX " + esx + ' is going to be rebooted #Reboot is commented out#'
    except:
        pass

def addVMKernel(esxs, ips, subnet, vds, portgroup, vcenter_ip, vcenter_user, vcenter_pass):
    script = '''
    Add-PSSnapin VMware.VimAutomation.Core
import-module VMware.VimAutomation.vds
$vcip = \'''' + vcenter_ip + '''\'
$vcuser = \'''' + vcenter_user + '''\'
$vcpass = \'''' + vcenter_pass + '''\'
$vmhost_array = \'''' + esxs + '''\'
$ip_array = \'''' + ips + '''\'
$subnet = \'''' + subnet + '''\'
$vds_name = \'''' + vds + '''\'
$portgroupname = \'''' + portgroup + '''\'

$ips = @()
foreach ($ip in $ip_array.split(",")){
    $ips = $ips + $ip
}



Connect-VIServer $vcip -user $vcuser -password $vcpass
$vds = Get-VDSwitch -Name $vds_name
$dvportgroup = Get-VDPortgroup -name $portgroupname -VDSwitch $vds
$n = 0
foreach ($vmhost in $vmhost_array.split(",")) {
if ($vmhost -ne ""){
$vmhost = Get-VMHost -Name $vmhost
New-VMHostNetworkAdapter -VMHost $vmhost -PortGroup $dvportgroup -VirtualSwitch $vds -IP $ips[$n] -SubnetMask $subnet
$n += 1
}
}

    '''
    powershell(script)


