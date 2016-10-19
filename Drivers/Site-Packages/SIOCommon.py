
import time
import re
import paramiko
from vCenterCommon import invokeScript
from quali_remote import ssh_upload, powershell
import uuid

# SSH Helper
def do_command(ssh1, command):
    if command:
        g = open(r'c:\ProgramData\QualiSystems\Shells.log', 'a')
        g.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': ssh : ' + command + '\r\n')
        g.close()
        stdin, stdout, stderr = ssh1.exec_command(command)
        stdin.close()
        a = []
        for line in stdout.read().splitlines():
            a.append(line + '\n')
        for line in stderr.read().splitlines():
            a.append(line + '\n')
        rv = '\n'.join(a)
        g = open(r'c:\ProgramData\QualiSystems\Shells.log', 'a')
        g.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': ssh result: ' + rv + '\r\n')
        g.close()
        return rv


def do_command_and_wait(chan, command, expect):
    g = open(r'c:\ProgramData\QualiSystems\Shells.log', 'a')
    g.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': ssh : ' + command + ' : wait for : ' + expect + '\r\n')
    g.close()
    chan.send(command + '\n')
    buff = ''
    #while buff.find(expect) < 0:
    while not re.search(expect, buff, 0):
        time.sleep(1)
        resp = chan.recv(9999)
        buff += resp
        #print resp

    g = open(r'c:\ProgramData\QualiSystems\Shells.log', 'a')
    g.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': replay : ' + buff + ' : wait for : ' + expect + '\r\n')
    return buff

def configureSIOnetwork(eth, ip, netmask, vmname, vcenter_ip, vcenter_username, vcenter_password, vmuser='root', vmpass='admin'):
    script = '''\"echo -e `\"BOOTPROTO=\'static\' `nIPADDR=\'''' + ip + '''\' `nDEVICE=\'''' + eth + '''\' `nNETMASK=\'''' + netmask + '''\' `nSTARTMODE=\'auto\' `nUSERCONTROL=\'no\'`\" > /etc/sysconfig/network/ifcfg-''' + eth + '"'
    invokeScript(script, vmname, vmuser, vmpass, 10, 10, vcenter_ip, vcenter_username, vcenter_password)

def configureSIORoute(eth, gateway, vmname, vcenter_ip, vcenter_username, vcenter_password, vmuser='root', vmpass='admin'):
    script = '''\"echo `\"default ''' + gateway + ' - ' + eth + '''`\" > /etc/sysconfig/network/routes"'''
    invokeScript(script, vmname, vmuser, vmpass, 10, 10, vcenter_ip, vcenter_username, vcenter_password)

def restartService(service, operation, vmname, vcenter_ip, vcenter_username, vcenter_password, vmuser='root', vmpass='admin'):
    script = '"service ' + service + ' ' + operation + '"'
    invokeScript(script, vmname, vmuser, vmpass, 3, 5, vcenter_ip, vcenter_username, vcenter_password)

def sioCommand(role, version, rpmswitch='rpm -i '):
    folder = '/root/install/'
    prefix = 'EMC-ScaleIO-'
    sufix = '.sles11.3.x86_64.rpm'
    if role == 'gateway':
        command = rpmswitch + folder + prefix + role + version + '.x86_64.rpm'
    else:
        command = rpmswitch + folder + prefix + role + version + sufix
    if role == 'mdm':
        command = 'MDM_ROLE_IS_MANAGER=1 ' + command
    elif role == 'tb':
        command = 'MDM_ROLE_IS_MANAGER=0 ' + command.replace('tb', 'mdm')
    return command

def installKey(ip, user='root', password='admin'):
    folder = '/root/install/'
    key = 'RPM-GPG-KEY-ScaleIO'
    command = 'rpm --import ' + folder + key
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # allow auto-accepting new hosts
        ssh.connect(ip, username=user, password=password)
        chan = ssh.invoke_shell()
        do_command_and_wait(chan, '', expect=r' ')
        do_command_and_wait(chan, command, expect=r'#')
    except Exception, e:
        print e


def installLIA(ip, liapassword, version='-1.32-3455.5', user='root', password='admin'):
    role = 'lia'
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # allow auto-accepting new hosts
        ssh.connect(ip, username=user, password=password)
        chan = ssh.invoke_shell()
        do_command_and_wait(chan, '', expect=r' ')
        command = 'TOKEN=' + liapassword + ' ' + sioCommand(role, version)
        do_command_and_wait(chan, command, expect=r' #')
    except Exception, e:
        print e


def installCallHome(ip, version='-1.32-3455.5', user='root', password='admin'):
    role = 'callhome'
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # allow auto-accepting new hosts
        ssh.connect(ip, username=user, password=password)
        chan = ssh.invoke_shell()
        do_command_and_wait(chan, '', expect=r' ')
        do_command_and_wait(chan, sioCommand(role, version), expect=r' #')
    except Exception, e:
        print e

def configureCallhome(ip, toemail='', fromemail='', calluser='', callpass='', customername='',smtpuser='', smtppass='', severity='', smtphost='localhost', port='25', tls='no', user='root', password='admin'):
    file = '''[general]
timeout = 600
# Set Max DataBase File Size before rotating
rotate = 10000
workdir = /opt/emc/scaleio/callhome/bin/
email_to = ''' + toemail + '''
email_from = ''' + fromemail + '''
event_db = /opt/emc/scaleio/mdm/logs/eventlog.db
# The User must provide the following parameter in order to use Call-Home mechanism
username = ''' + calluser + '''
password = ''' + callpass + '''
customer_name = ''' + customername + '''

[smtp]
host = ''' + smtphost + '''
port = ''' + port + '''
tls = ''' + tls + '''
username = ''' + smtpuser + '''
password = ''' + smtppass + '''

[email_alert]
email_to = ''' + toemail + '''
# Severity can be: warning, error, critical
severity = ''' + severity
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # allow auto-accepting new hosts
        ssh.connect(ip, username=user, password=password)
        chan = ssh.invoke_shell()
        do_command_and_wait(chan, '', expect=r' ')
        command = '''echo \"''' + file + '" > /opt/emc/scaleio/callhome/cfg/conf.txt'
        do_command_and_wait(chan, command, expect=r' #')
    except Exception, e:
        print e


def installSDS(ip, version='-1.32-3455.5', user='root', password='admin'):
    role = 'sds'
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # allow auto-accepting new hosts
        ssh.connect(ip, username=user, password=password)
        chan = ssh.invoke_shell()
        do_command_and_wait(chan, '', expect=r' ')
        # command = 'CONF=IOPS ' + sioCommand(role, version)
        # No longer need the CONF=IOPD. (not mentioned in the Docs)
        command = sioCommand(role, version)
        do_command_and_wait(chan, command, expect=r' #')
    except Exception, e:
        print e

def configureSDS(ip, ip2, ip3, adminpassword, license=False, user='root', password='admin'):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # allow auto-accepting new hosts
        ssh.connect(ip[0], username=user, password=password)
        chan = ssh.invoke_shell()
        do_command_and_wait(chan, '', expect=r' ')
        # Preper Primary
        command = 'scli --create_mdm_cluster --master_mdm_ip ' + ip[1] + ' --master_mdm_management_ip ' + ip[0] + ' --master_mdm_name mdm_primary --accept_license'
        do_command_and_wait(chan, command, expect=r'license')
        # Accept Certificate
        do_command_and_wait(chan, 'y', expect=r' #')
        # Login
        command = 'scli --login --username admin --password admin'
        do_command_and_wait(chan, command, expect=r' #')
        command = 'scli --set_password --old_password admin --new_password ' + adminpassword
        do_command_and_wait(chan, command, expect=r' #')
        command = 'scli --login --username admin --password ' + adminpassword
        do_command_and_wait(chan, command, expect=r' #')
        # License
        # if license:
        # nothing on how to install the new license
        if False:
            command = 'touch /tmp/siolicense.lsn'
            do_command_and_wait(chan, command, expect=r' #')
            # Transfer the license to the empty file
            ssh_upload(ip, user, password, license, '/tmp/siolicense.lsn')
            # Add license to the SIO system
            command = 'scli --set_license --mdm_ip ' + ip + ' --license_file /tmp/siolicense.lsn'
            do_command_and_wait(chan, command, expect=r' #')

        # Preper Secondary
        command = 'scli --add_standby_mdm --new_mdm_ip ' + ip2[1] + ' --mdm_role manager --new_mdm_management_ip ' + ip2[0] + ' --new_mdm_name mdm_secondary'
        do_command_and_wait(chan, command, expect=r' #')
        # Preper TB
        command = 'scli --add_standby_mdm --new_mdm_ip ' + ip3[1] + ' --mdm_role tb --new_mdm_name mdm_tiebreaker'
        do_command_and_wait(chan, command, expect=r' #')
        # Change to Cluster mode
        command = 'scli --switch_cluster_mode --cluster_mode 3_node --add_slave_mdm_name mdm_secondary --add_tb_name mdm_tiebreaker'
        do_command_and_wait(chan, command, expect=r' ')
    except Exception, e:
        print e

def configureMainStorage(primaryip, secondaryip, adminpassword, zp, backscan, sysname, user='root', password='admin', pd='PD1', sp='SP1'):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # allow auto-accepting new hosts
    ssh.connect(primaryip, username=user, password=password)
    chan = ssh.invoke_shell()
    do_command_and_wait(chan, '', expect=r' ')
    # Login
    command = 'scli --login --username admin --password ' + adminpassword
    do_command_and_wait(chan, command, expect=r' #')
    # Create Protection Domain
    command = 'scli --add_protection_domain --protection_domain_name ' + pd + ''
    do_command_and_wait(chan, command, expect=r' #')
    # Create Storage Pool
    command = 'scli --add_storage_pool --protection_domain_name ' + pd + ' --storage_pool_name ' + sp + ''
    do_command_and_wait(chan, command, expect=r' #')

    if zp:
        command = 'scli --modify_zero_padding_policy --protection_domain_name ' + pd + ' --storage_pool_name ' + sp + ' --enable_zero_padding'
        do_command_and_wait(chan, command, expect=r' #')
    if backscan:
        command = 'scli --enable_background_device_scanner --protection_domain_name ' + pd + ' --storage_pool_name ' + sp + ' --scanner_mode device_only'
        do_command_and_wait(chan, command, expect=r' #')
    command = 'scli --rename_system --new_name ' + sysname
    do_command_and_wait(chan, command, expect=r' #')


def addSdsStorage(primaryip, secondaryip, sdsarray, adminpassword, rmcache, faultlist='None', user='root', password='admin', pd='PD1', sp='SP1'):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # allow auto-accepting new hosts
    ssh.connect(primaryip, username=user, password=password)
    chan = ssh.invoke_shell()
    do_command_and_wait(chan, '', expect=r' ')
    # Login
    command = 'scli --login --username admin --password ' + adminpassword
    do_command_and_wait(chan, command, expect=r' #')
    for n in xrange(len(sdsarray)/2):
        sds_path = ''
        for x in xrange(sdsarray[(n * 2) + 1]):
            device_path = "/dev/sd" + str(chr((x + ord('b'))))
            sds_path += device_path + ','
        sds_path = sds_path[:-1]

        command = 'scli --add_sds --sds_ip ' + sdsarray[(n*2)] + ' --sds_name sds' + str(n) + ' --protection_domain_name ' + pd + ' --storage_pool_name ' + sp + ' --rmcache_size_mb ' + str(rmcache) + ' --device_path ' + sds_path
        if faultlist != None:
            command += ' --fault_set_name ' + faultlist[n]
        do_command_and_wait(chan, command, expect=r' #')



def installSDC(esx, file, password, username='root'):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # allow auto-accepting new hosts
        ssh.connect(esx, username=username, password=password)
        chan = ssh.invoke_shell()
        do_command_and_wait(chan, '', expect=r' ')
        # Create empty file
        command = 'touch /tmp/sdc.zip'
        do_command_and_wait(chan, command, expect=r'@')
        # Transfer the zip to the empty file
        ssh_upload(esx, username, password, file, '/tmp/sdc.zip')
        # Change ESX PartnerSupport level
        command = 'esxcli software acceptance set --level=PartnerSupported'
        do_command_and_wait(chan, command, expect=r'@')
        # Install SDC
        command = 'esxcli software vib install -d /tmp/sdc.zip'
        do_command_and_wait(chan, command, expect=r'@')
    except Exception, e:
        print e

def configureSDC(esx, password, ipstring, username='root'):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # allow auto-accepting new hosts
    ssh.connect(esx, username=username, password=password)
    chan = ssh.invoke_shell()
    do_command_and_wait(chan, '', expect=r' ')
    # Run SDC configurations
    esx_uuid = uuid.uuid4()
    command = 'esxcli system module parameters set -m scini -p "IoctlIniGuidStr=' + str(esx_uuid) + ' IoctlMdmIPStr=' + ipstring + '"'
    do_command_and_wait(chan, command, expect=r'@')
    # Backup config
    command = '/bin/auto-backup.sh'
    do_command_and_wait(chan, command, expect=r'@')
    # Load SDC Module
    command = 'esxcli system module load -m scini'
    do_command_and_wait(chan, command, expect=r'@')


def installSIOVM(ip, role, version='-1.32-3455.5', user='root', password='admin'):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # allow auto-accepting new hosts
        ssh.connect(ip, username=user, password=password)
        chan = ssh.invoke_shell()
        do_command_and_wait(chan, '', expect=r' ')
        do_command_and_wait(chan, sioCommand(role, version), expect=r' #')
    except Exception, e:
        print e

def installGateway(ip, adminpassword, version='-1.32-3455.5', user='root', password='admin'):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # allow auto-accepting new hosts
        ssh.connect(ip, username=user, password=password)
        chan = ssh.invoke_shell()
        do_command_and_wait(chan, '', expect=r' ')
        # Install Java
        do_command_and_wait(chan, 'rpm -i /root/install/jre-8u65-linux-x64.rpm', '#')
        command = "GATEWAY_ADMIN_PASSWORD=" + adminpassword + ' ' + sioCommand('gateway', version)
        do_command_and_wait(chan, command, expect=r' #')
    except Exception, e:
        print e

def configureGateway(ip, primaryip, secondaryip, zp, user='root', password='admin'):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # allow auto-accepting new hosts
    ssh.connect(ip, username=user, password=password)
    chan = ssh.invoke_shell()
    do_command_and_wait(chan, '', expect=r' ')
    command = 'sed -i -e \'s/mdm.ip.addresses=/mdm.ip.addresses=' + primaryip + ',' + secondaryip + '/g\' /opt/emc/scaleio/gateway/webapps/ROOT/WEB-INF/classes/gatewayUser.properties'
    do_command_and_wait(chan, command, expect=r' #')
    command = 'sed -i -e \'s/security.bypass_certificate_check=false/security.bypass_certificate_check=true/g\' /opt/emc/scaleio/gateway/webapps/ROOT/WEB-INF/classes/gatewayUser.properties'
    do_command_and_wait(chan, command, expect=r' #')
    command = 'service scaleio-gateway restart'
    do_command_and_wait(chan, command, expect=r' #')

def configureAutomaticstart(vms, dc, vcenter_ip, vcenter_user, vcenter_pass):
    script = '''
    Add-PSSnapin VMware.VimAutomation.Core
$vcenterip = \'''' + vcenter_ip + '''\'
$vcenteruser = \'''' + vcenter_user + '''\'
$vcenterpassword = \'''' + vcenter_pass + '''\'
$location = \'''' + dc + '''\'

Connect-VIServer $vcenterip -user $vcenteruser -Password $vcenterpassword

$vms = \'''' + vms + '''\'

$VMHosts = Get-VMHost -Location $location | Sort-Object Name

#Configure VM Host Start Policies
$VMHostStartPolicies = Get-VMHostStartPolicy -VMHost $VMHosts
Foreach ($VMHostStartPolicy in $VMHostStartPolicies) {
    Set-VMHostStartPolicy -VMHostStartPolicy $VMHostStartPolicy -Enabled:$TRUE -StartDelay 60 -StopAction GuestShutDown -StopDelay 60 -WaitForHeartBeat:$TRUE -Confirm:$FALSE
}


#Configure VM Startup Order
Foreach ($vm in ($vms.split(","))) {
    $po = Get-VMStartPolicy -VM $vm
    Set-VMStartPolicy -StartPolicy $po -StartAction PowerOn
}

    '''
    powershell(script)


def getSIOesxs(vcenter_ip, vcenter_user, vcenter_password, datacenter, master_esx, sio_cluster):
    script = '''
    function Get-FreeScsiLun {

  param (
  [parameter(ValueFromPipeline = $true,Position=1)]
  [ValidateNotNullOrEmpty()]
  [VMware.VimAutomation.Client20.VMHostImpl]
  $VMHost
  )

  process{
    $storMgr = Get-View $VMHost.ExtensionData.ConfigManager.DatastoreSystem

    $storMgr.QueryAvailableDisksForVmfs($null) | %{
      #New-Object PSObject -Property @{
        #VMHost = $VMHost.Name
        #CanonicalName = $_.CanonicalName
        #IsSSD = $_.ssd
        #CapacityGB = [Math]::Round($_.Capacity.Block * $_.Capacity.BlockSize / 1GB,2)
        $out = $VMHost.Name
        $out += ","
        $out += $_.CanonicalName
        $out += ","
        $out += $_.ssd
        $out += ","
        $out += [Math]::Round($_.Capacity.Block * $_.Capacity.BlockSize / 1GB,2)
        $out += ";"
        return $out

      #}
    }
  }
}
            Add-PSSnapin VMware.VimAutomation.Core
    $vcenterip = \'''' + vcenter_ip + '''\'
    $vcenteruser = \'''' + vcenter_user + '''\'
    $vcenterpassword = \'''' + vcenter_password + '''\'
    $vcenterdc = \'''' + datacenter + '''\'
    $masteresx = \'''' + master_esx + '''\'
    $sio_cluster = \'''' + sio_cluster + '''\'
    $exclideesxs = @()
    foreach ($exesx in $masteresx.split(",")) {
        $exclideesxs += $exesx
    }
    Connect-VIServer $vcenterip -user $vcenteruser -Password $vcenterpassword

$dchosts = Get-Datacenter $vcenterdc | Get-VMHost | Select Name

    $filter = @{'Guest.IPAddress' = "$vcenterip"}
    $vch = get-view -ViewType VirtualMachine -Filter $filter | select @{n='Host';e={get-vmhost -id $_.runtime.host}}
    $ip=get-WmiObject Win32_NetworkAdapterConfiguration|Where {$_.Ipaddress.length -gt 1}
    $csip = $ip.ipaddress[0]
    $filter = @{'Guest.IPAddress' = "$csip"}
    $csh = get-view -ViewType VirtualMachine -Filter $filter | select @{n='Host';e={get-vmhost -id $_.runtime.host}}
    $a = ''
    foreach ($ESXiServer in $dchosts) {
        if ($ESXiServer.Name -ne $vch.Host.Name) {
            if ($ESXiServer.Name -ne $csh.Host.Name) {
                if ($exclideesxs -notcontains $ESXiServer.Name) {
                    $v = Get-VMHost -Name $ESXiServer.Name
                    $a += $v.Name + ','
             }
                }
        }
    }

    $a =  $a.ToString().Substring(0,$a.Length-1)

$free = ''
$esx_matrix = ''
$count = 0
$freediskcount = 0
$sio_esxs = (Get-VMHost -Location $sio_cluster).name
foreach ($esx in $a.Split(",")){
    $ds = (Get-Datastore -VMHost $esx| Where-Object {$_.Name -like 'datastore*'}).Name
    $freediskcount = 0
    $free = Get-VMHost -Name $esx | Get-FreeScsiLun
    if ($free){
        foreach ($disk in $free.split(';')){
            $size = $disk.split(',')[3]
            $size = $size -as [float]
            if ($size -ge 100 -and $size -lt 6000){
                $freediskcount += 1
            }
        }
    }
    if ($freediskcount -gt 0){
        if ($sio_esxs -like $esx){
            if ($count -gt 2){
                $esx_matrix += $esx + ","
                $esx_matrix += "SDS,"
            }
            else{
                $esx_matrix += $esx + ","
                $esx_matrix += "MDM,"
                $count += 1
            }
        }
        else{
            $esx_matrix += $esx + ","
            $esx_matrix += "SDS,"
        }
    }
    else{
    $esx_matrix += $esx + ","
    $esx_matrix += "SDC,"
    }
    $esx_matrix += $ds + ','
    $esx_matrix += (Get-Cluster -VMHost $esx).Name + ";"

}
Write-Host '<%<%', $esx_matrix
    '''


    esxnodes = powershell(script).split('<%<%')[1].strip().split(';')
    return esxnodes


def getESXfreedisks(esxs, vcenter_ip, vcenter_user, vcenter_password):
    script = '''
function Get-FreeScsiLun {

  param (
  [parameter(ValueFromPipeline = $true,Position=1)]
  [ValidateNotNullOrEmpty()]
  [VMware.VimAutomation.Client20.VMHostImpl]
  $VMHost
  )

  process{
    $storMgr = Get-View $VMHost.ExtensionData.ConfigManager.DatastoreSystem

    $storMgr.QueryAvailableDisksForVmfs($null) | %{
      #New-Object PSObject -Property @{
        #VMHost = $VMHost.Name
        #CanonicalName = $_.CanonicalName
        #IsSSD = $_.ssd
        #CapacityGB = [Math]::Round($_.Capacity.Block * $_.Capacity.BlockSize / 1GB,2)
        $out = $VMHost.Name
        $out += ","
        $out += $_.CanonicalName
        $out += ","
        $out += $_.ssd
        $out += ","
        $out += [Math]::Round($_.Capacity.Block * $_.Capacity.BlockSize / 1GB,2)
        $out += ";"
        return $out

      #}
    }
  }
}
Add-PSSnapin VMware.VimAutomation.Core

$vcip = "''' + vcenter_ip + '''"
$vcuser = "''' + vcenter_user + '''"
$vcpass = "''' + vcenter_password + '''"

$Hosts = "''' + esxs + '''"
#$Hosts = "10.10.111.20"

Connect-VIServer $vcip -user $vcuser -password $vcpass
$result = ''
foreach ($esx in $Hosts.Split(",")){
    $result += Get-VMHost -Name $esx | Get-FreeScsiLun

    }
write-host "<%<%" $result.Substring(0, $result.Length-1)
    '''
    result = powershell(script)
    if not re.match('error|exception', result.lower()):
        return result
    else:
        return None


def createRDMdisk(vmname, diskpath, vcenter_ip, vcenter_user, vcenter_password):
    script ='''
    Add-PSSnapin VMware.VimAutomation.Core

$vcip = "''' + vcenter_ip + '''"
$vcuser = "''' + vcenter_user + '''"
$vcpass = "''' + vcenter_password + '''"

Connect-VIServer $vcip -user $vcuser -password $vcpass

New-HardDisk -VM \"''' + vmname + '''\" -DiskType RawPhysical -DeviceName /vmfs/devices/disks/''' + diskpath

    powershell(script)


def installvCenterplugin(gateway_ip, version, vcenter_ip, vcenter_user, vcenter_password):
    script = '''

    Add-PSSnapin VMware.VimAutomation.Core
    $vCenter=\'''' + vcenter_ip + '''\'
    $Username=\'''' + vcenter_user + '''\'
    $Password=\'''' + vcenter_password + '''\'
    $SVMGateway=\'''' + gateway_ip + '''\'
    $SIOVersion=\'''' + version + '''\'

        $userUrl = "https://" + $SVMGateway + "/resources/plugin"
    	$Server = $Server = Connect-VIServer -Server $vCenter -Protocol https -User $Username -Password $Password -ErrorAction Stop
        $extension = New-Object VMware.Vim.Extension
        $extension.Key = "com.emc.s3g.scaleio.vSpherePlugin"
        $extension.Company = "EMC"
    	$extension.Version = $SIOVersion
        $extension.LastHeartbeatTime = "2012-07-21T00:25:52.814418Z"
        $description = New-Object VMware.Vim.Description
        $description.Label = "ScaleIO Plugin"
        $description.Summary = "ScaleIO systems management"
        $extension.Description = $description
        $extension.ShownInSolutionManager = $false


        $client = New-Object VMware.Vim.ExtensionClientInfo
        $client.Version = $SIOVersion
        $client.Company = "EMC"
        $client.Type = "vsphere-client-serenity"
        $client.Url = $userUrl

        $clientDescription = New-Object VMware.Vim.Description
        $clientDescription.Label = "ScaleIO Plugin"
        $clientDescription.Summary = "ScaleIO systems management"
        $client.Description = $clientDescription

        $extension.Client = $client
    	$thumbprintWithColon = ""
        try {
            [System.Net.ServicePointManager]::ServerCertificateValidationCallback = {$true}
            $request = [System.Net.WebRequest]::Create("https://"+$SVMGateway)
            $respond = $request.GetResponse()
            if ($request) {
                $thumbprint = $request.ServicePoint.Certificate.GetCertHashString()
                $thumbprintWithColon = $thumbprint.Substring(0,2)
                for ($i=2; $i -lt $thumbprint.Length; $i+=2) {
                    $thumbprintWithColon += ":"
                    $thumbprintWithColon += $thumbprint.Substring($i,2)
                }
            }
        } catch {
            write-warning "Failed retrieving thumbprint from the server ($url)"
        }
        if ($thumbprintWithColon) {
        	$server = New-Object VMware.Vim.ExtensionServerInfo
        	$server.Company = "EMC"
        	$server.Type = "vsphere-client-serenity"
        	$server.Url = $userUrl
        	$server.adminEmail = "ScaleIO@emc.com"
        	$server.ServerThumbprint = $thumbprintWithColon

        	$serverDescription = New-Object VMware.Vim.Description
        	$serverDescription.Label = "ScaleIO Plugin"
        	$serverDescription.Summary = "ScaleIO systems management"
        	$server.Description = $serverDescription

        	$extension.Server = $server
        }

        $extMngr = Get-View ExtensionManager
        try{
        	write-host "Registering ScaleIO extension..."
        	try {
        	    $extMngr.UnregisterExtension("com.emc.s3g.scaleio.vSpherePlugin")
            } catch {}
        	$extMngr.UpdateViewData()
        	$extMngr.RegisterExtension($extension)

        } catch {
            $Host.UI.WriteErrorLine($_.Exception.Message)
            $Host.UI.WriteErrorLine("Cannot register ScaleIO extension. This can happen if the extension is already registered. To fix this problem, try to run unregisterScaleIOPlugin script and then rerun this script.")
        }
    Disconnect-VIServer -Server $vCenter -Confirm:$false -ErrorAction Stop

    '''
    powershell(script)


def addSdcNode(primaryip, esxips, adminpassword, user='root', password='admin'):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # allow auto-accepting new hosts
    ssh.connect(primaryip, username=user, password=password)
    chan = ssh.invoke_shell()
    do_command_and_wait(chan, '', expect=r' ')
    # Login
    command = 'scli --login --username admin --password ' + adminpassword
    do_command_and_wait(chan, command, expect=r' #')
    for esx in esxips:
        command = 'scli --add_sdc --sdc_ip ' + esx
        do_command_and_wait(chan, command, expect=r' #')



def getMaxVolume(primaryip, sp, adminpassword, user='root', password='admin'):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # allow auto-accepting new hosts
    ssh.connect(primaryip, username=user, password=password)
    chan = ssh.invoke_shell()
    do_command_and_wait(chan, '', expect=r' ')
    # Login
    command = 'scli --login --mdm_ip ' + primaryip + ' --username admin --password ' + adminpassword
    do_command_and_wait(chan, command, expect=r' #')
    command = "scli --query_all"
    result = do_command_and_wait(chan, command, expect=r' #')
    first = result.split("Storage Pool " + sp)
    first2 = first[1].split("and")
    # print first[0]
    second = first2[1].split("(")
    third = second[1].split(")")
    return third[0].strip().split(" ")[0]


def addVolume(primaryip, secondaryip, sdcs, adminpassword, volumetype, volumesize, user='root', password='admin', pd='PD1', sp='SP1', volume='VOL1'):
    max_volume = int(getMaxVolume(primaryip, sp, adminpassword, user, password))
    if int(volumesize) % 8 != 0:
        volumesize = (int(volumesize) / 8) * 8
    if (int(volumesize) <= max_volume) and not (int(volumesize) == 0):
        max_volume = volumesize
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # allow auto-accepting new hosts
    ssh.connect(primaryip, username=user, password=password)
    chan = ssh.invoke_shell()
    do_command_and_wait(chan, '', expect=r' ')
    # Login
    command = 'scli --login --username admin --password ' + adminpassword
    do_command_and_wait(chan, command, expect=r' #')
    command = 'scli --add_volume --protection_domain_name ' + pd + ' --volume_name ' + volume + ' --size_gb ' + str(max_volume) + ' --storage_pool_name ' + sp
    if volumetype.lower() == 'thick':
        command += ' --thick_provisioned'
    do_command_and_wait(chan, command, expect=r' #')
    for sdc in sdcs:
        command = 'scli --map_volume_to_sdc --allow_multi_map --volume_name ' + volume + ' --sdc_ip ' + sdc
        do_command_and_wait(chan, command, expect=r' #')



def addSioStorageToESX(sdcName, sio_datastore_name, vcenter_ip, vcenter_username, vcenter_password):
    powershell('''
    Add-PSSnapin VMware.VimAutomation.Core
    Connect-VIServer ''' + vcenter_ip + ''' -User ''' + vcenter_username + ''' -Password ''' + vcenter_password + '''

    $vmh = Get-VMHost -name ''' + sdcName + '''
    $storMgr = Get-View $vmh.ExtensionData.ConfigManager.DatastoreSystem
    $storMgr.QueryAvailableDisksForVmfs($null) | %{
      if ($_.CanonicalName.StartsWith("eui.")) {
        New-Datastore -VMHost $vmh -name ''' + sio_datastore_name + ''' -vmfs -path $_.CanonicalName
        break
      }
    }

    ''')

def changeRootPassword(primaryip, newpassword, user='root', password='admin'):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # allow auto-accepting new hosts
    ssh.connect(primaryip, username=user, password=password)
    chan = ssh.invoke_shell()
    do_command_and_wait(chan, '', expect=r' ')
    # Login
    command = 'passwd'
    do_command_and_wait(chan, command, expect=r'New Password:')
    command = newpassword
    do_command_and_wait(chan, command, expect=r'Reenter New Password:')
    command = newpassword
    do_command_and_wait(chan, command, expect=r'Password changed.')


def createFaultsets(primaryip, adminpassword, number='3', faultnameprefix='FaultSet-', pd='PD1', user='root', password='admin'):
    if (number == '') or (number == '0'):
        return None
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # allow auto-accepting new hosts
    ssh.connect(primaryip, username=user, password=password)
    chan = ssh.invoke_shell()
    do_command_and_wait(chan, '', expect=r' ')
    # Login
    command = 'scli --login --mdm_ip ' + primaryip + ' --username admin --password ' + adminpassword
    do_command_and_wait(chan, command, expect=r' #')
    faultlist = []
    for n in xrange(int(number)):
        command = 'scli --add_fault_set --protection_domain_name ' + pd + ' --fault_set_name ' + faultnameprefix + str(n)
        do_command_and_wait(chan, command, expect=r' #')
        faultlist.append(faultnameprefix + str(n))
    return faultlist

def getSvmDisks(vmname, vcenter_ip, vcenter_user, vcenter_password):
    script = '''
Add-PSSnapin VMware.VimAutomation.Core

$vcip = \'''' + vcenter_ip + '''\'
$vcuser = \'''' + vcenter_user + '''\'
$vcpass = \'''' + vcenter_password + '''\'
$vm = \'''' + vmname + '''\'
Connect-VIServer $vcip -user $vcuser -password $vcpass
$a = (get-vm $vm | Get-HardDisk).count

Write-Host '<%<%', $a

    '''
    result = powershell(script).split('<%<%')[1].strip()
    return result


def getESXDataIPs(vcenter_ip, vcenter_user, vcenter_password, datacenter, excludeesx):
    script = '''
    Add-PSSnapin VMware.VimAutomation.Core
    $vcenterip = \'''' + vcenter_ip + '''\'
    $vcenteruser = \'''' + vcenter_user + '''\'
    $vcenterpassword = \'''' + vcenter_password + '''\'
    $vcenterdc = \'''' + datacenter + '''\'
    $masteresx = \'''' + excludeesx + '''\'
    $exclideesxs = @()
    foreach ($exesx in $masteresx.split(",")) {
        $exclideesxs += $exesx
    }
    Connect-VIServer $vcenterip -user $vcenteruser -Password $vcenterpassword

$dchosts = Get-Datacenter $vcenterdc | Get-VMHost | Select Name

    $filter = @{'Guest.IPAddress' = "$vcenterip"}
    $vch = get-view -ViewType VirtualMachine -Filter $filter | select @{n='Host';e={get-vmhost -id $_.runtime.host}}
    $ip=get-WmiObject Win32_NetworkAdapterConfiguration|Where {$_.Ipaddress.length -gt 1}
    $csip = $ip.ipaddress[0]
    $filter = @{'Guest.IPAddress' = "$csip"}
    $csh = get-view -ViewType VirtualMachine -Filter $filter | select @{n='Host';e={get-vmhost -id $_.runtime.host}}
    $a = ''
    foreach ($ESXiServer in $dchosts) {
        if ($ESXiServer.Name -ne $vch.Host.Name) {
            if ($ESXiServer.Name -ne $csh.Host.Name) {
                if ($exclideesxs -notcontains $ESXiServer.Name) {
                    $v = Get-VMHost -Name $ESXiServer.Name
                    $v = $v.NetworkInfo.VirtualNic | Where {$_.DeviceName -eq 'vmk1'} | select IP
                    $a += $v.IP + ','
             }
                }
        }
    }

    $a =  $a.ToString().Substring(0,$a.Length-1)
    write-host '<%<%', $a
    '''
    result = powershell(script).split('<%<%')[1].strip()
    return result

def getSIOSvms(vcenter_ip, vcenter_user, vcenter_password, datacenter, excludeesx, vmprefix):
    script = '''
                Add-PSSnapin VMware.VimAutomation.Core
    $vcenterip = \'''' + vcenter_ip + '''\'
    $vcenteruser = \'''' + vcenter_user + '''\'
    $vcenterpassword = \'''' + vcenter_password + '''\'
    $vcenterdc = \'''' + datacenter + '''\'
    $masteresx = \'''' + excludeesx + '''\'
    $vmprefix = \'''' + vmprefix + '''\'
    $exclideesxs = @()
    foreach ($exesx in $masteresx.split(",")) {
        $exclideesxs += $exesx
    }
    Connect-VIServer $vcenterip -user $vcenteruser -Password $vcenterpassword
    $vms = Get-VM
    foreach($vm in $vms){
        if($vm.Name.StartsWith($vmprefix) -and ($vm.VMHost -notlike $exclideesxs)){
            $out += $vm.Name + ','
        }
    }

    write-host '<%<%', $out
    '''
    return powershell(script).split('<%<%')[1].strip().split(",")