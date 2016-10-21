

from Versa_Common import *

with open(r'c:\ProgramData\QualiSystems\Shells.log', 'a') as f:
    f.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': ' + __file__.split('\\')[-1].replace('.py', '') + ': ' + str(os.environ) + '\r\n')


resource = json.loads(os.environ['RESOURCECONTEXT'])
resource_name = resource['name']
attrs = resource['attributes']

# General VM config
datastore = attrs['Versa Datastore']
thick_thin = attrs['Versa Disk Mode']
vcenter_user = attrs['vCenter Administrator User']
vcenter_password = attrs['vCenter Administrator Password']
vcenter_ip = attrs['vCenter IP']
datacenter = attrs['Versa Datacenter']
cluster = attrs['Versa Branch2 Cluster']


controller_ova_path = attrs['Versa Controller Path']

# Branch2 config
# eth 0
branch2_vmname = attrs['Versa Branch2 VM Name']
branch2_portgroup = attrs['Versa Branch2 NB Portgroup Name']
branch2_ip = attrs['Versa Branch2 NB IP']
branch2_dns = attrs['Versa Branch2 NB DNS']
branch2_mask = attrs['Versa Branch2 NB Mask']
branch2_gateway = attrs['Versa Branch2 NB Gateway']
branch2_eth = 'eth0'
# eth 1
branch2_1_portgroup = attrs['Versa Branch2 SDWAN Portgroup Name']
branch2_1_ip = ''
branch2_1_dns = ''
branch2_1_mask = ''
branch2_1_gateway = ''
branch2_1_eth = 'eth1'
# eth 2
branch2_2_portgroup = attrs['Versa Branch2 Traffic Portgroup Name']
branch2_2_ip = ''
branch2_2_dns = ''
branch2_2_mask = ''
branch2_2_gateway = ''
branch2_2_eth = 'eth2'

br2 = {
    branch2_eth: (branch2_ip, branch2_portgroup, branch2_mask, branch2_gateway, branch2_dns),
    branch2_1_eth: (branch2_1_ip, branch2_1_portgroup, branch2_1_mask, branch2_1_gateway, branch2_1_dns),
    branch2_2_eth: (branch2_2_ip, branch2_2_portgroup, branch2_2_mask, branch2_2_gateway, branch2_2_dns),
}
dv_switch = str(attrs['Versa Traffic VDS'])
dv_switchsdwan = str(attrs['Versa SDWAN VDS'])
vds1_num_ports = '128'
vds1_vlanmode = 'none'
vds1_vlan_ids = '0'

try:
    vcenterparams = {
        'IP': vcenter_ip,
        'user': vcenter_user,
        'password': vcenter_password}

    # Set VC session
    session = Vcenter(vcenterparams)
    # STEPS # Quit if branch2_vmname already exists on vcenter_ip vcenter_user vcenter_password
    session.add_dvPort_group(dv_switchsdwan, branch2_1_portgroup, int(vds1_num_ports), vds1_vlanmode, vds1_vlan_ids)
    session.add_dvPort_group(dv_switch, branch2_2_portgroup, int(vds1_num_ports), vds1_vlanmode, vds1_vlan_ids)
except:
    pass
# Deploy Branch2
try:
    command = ' --skipManifestCheck --noSSLVerify  --allowExtraConfig --datastore=' + '"' + datastore + '"' + ' --acceptAllEulas --diskMode=' + thick_thin + ' --net:"VM Network"="' + branch2_portgroup + '" --name="' + branch2_vmname + '" "' + controller_ova_path + '" "vi://' + vcenter_user + ':"' + vcenter_password + '"@' + vcenter_ip + '/' + datacenter + '/host/' + cluster + '/Resources"'
    deployVM(command, branch2_vmname, vcenter_ip, vcenter_user, vcenter_password, False)
    time.sleep(5)
    vmPower(branch2_vmname, 'start', vcenter_ip, vcenter_user, vcenter_password)
except Exception, e:
    print '\r\n' + str(e)
    sys.exit(1)

loop = 10
script = '\'cat /etc/network/interfaces\''
time.sleep(30)
try:
    br2 = setAdapterMAC(branch2_vmname, br2, vcenter_ip, vcenter_user, vcenter_password)
    while loop > 0:
        firstNFVEth(branch2_vmname, 'admin', 'versa123', br2, 20, 30, vcenter_ip, vcenter_user, vcenter_password)
        ans = invokeScript(script, branch2_vmname, 'admin', 'versa123', 20, 30, vcenter_ip, vcenter_user, vcenter_password)
        if 'EOF' in ans:
            loop = 0
        else:
            loop -= 1
    addNFVAdapter(branch2_vmname, br2, vcenter_ip, vcenter_user, vcenter_password)
    vmPower(branch2_vmname, 'restart', vcenter_ip, vcenter_user, vcenter_password)
except Exception, e:
    print e