from Versa_Common import *

from quali_remote import quali_enter, quali_exit, qs_trace, qs_info

quali_enter(__file__)


resource = json.loads(os.environ['RESOURCECONTEXT'])
resource_name = resource['name']
attrs = resource['attributes']

#General VM config
datastore = attrs['Versa Datastore']
thick_thin = attrs['Versa Disk Mode']
vcenter_user = attrs['vCenter Administrator User']
vcenter_password = attrs['vCenter Administrator Password']
vcenter_ip = attrs['vCenter IP']
datacenter = attrs['Versa Datacenter']
cluster = attrs['Versa Branch1 Cluster']


controller_ova_path = attrs['Versa Controller Path']

#Branch1 config
#eth 0
branch1_portgroup = attrs['Versa Branch1 NB Portgroup Name']
branch1_vmname = attrs['Versa Branch1 VM Name']
branch1_ip = attrs['Versa Branch1 NB IP']
branch1_dns = attrs['Versa Branch1 NB DNS']
branch1_mask = attrs['Versa Branch1 NB Mask']
branch1_gateway = attrs['Versa Branch1 NB Gateway']
branch1_eth = 'eth0'
#eth 1
branch1_1_portgroup = attrs['Versa Branch1 SDWAN Portgroup Name']
branch1_1_ip = ''
branch1_1_dns = ''
branch1_1_mask = ''
branch1_1_gateway = ''
branch1_1_eth = 'eth1'
#eth 2
branch1_2_portgroup = attrs['Versa Branch1 Traffic Portgroup Name']
branch1_2_ip = ''
branch1_2_dns = ''
branch1_2_mask = ''
branch1_2_gateway = ''
branch1_2_eth = 'eth2'

br1 = {
    branch1_eth: (branch1_ip, branch1_portgroup, branch1_mask, branch1_gateway, branch1_dns),
    branch1_1_eth: (branch1_1_ip, branch1_1_portgroup, branch1_1_mask, branch1_1_gateway, branch1_1_dns),
    branch1_2_eth: (branch1_2_ip, branch1_2_portgroup, branch1_2_mask, branch1_2_gateway, branch1_2_dns),
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
    # STEPS # Quit if branch1_vmname already exists on vcenter_ip vcenter_user vcenter_password

    session.add_dvPort_group(dv_switchsdwan, branch1_1_portgroup, int(vds1_num_ports), vds1_vlanmode, vds1_vlan_ids)
    session.add_dvPort_group(dv_switch, branch1_2_portgroup, int(vds1_num_ports), vds1_vlanmode, vds1_vlan_ids)
except:
    pass
#Deploy Branch1
command = ' --skipManifestCheck --noSSLVerify  --allowExtraConfig --datastore=' + '"' + datastore + '"' + ' --acceptAllEulas --diskMode=' + thick_thin + ' --net:"VM Network"="' + branch1_portgroup + '" --name="' + branch1_vmname + '" "' + controller_ova_path + '" "vi://' + vcenter_user + ':"' + vcenter_password + '"@' + vcenter_ip + '/' + datacenter + '/host/' + cluster + '/Resources"'
deployVM(command, branch1_vmname, vcenter_ip, vcenter_user, vcenter_password, False, True)
time.sleep(5)
vmPower(branch1_vmname, 'start', vcenter_ip, vcenter_user, vcenter_password)

loop = 10
script = '\'cat /etc/network/interfaces\''

time.sleep(30)
br1 = setAdapterMAC(branch1_vmname, br1, vcenter_ip, vcenter_user, vcenter_password)
while loop > 0:
    firstNFVEth(branch1_vmname, 'admin', 'versa123', br1, 20, 30, vcenter_ip, vcenter_user, vcenter_password)
    ans = invokeScript(script, branch1_vmname, 'admin', 'versa123', 20, 30, vcenter_ip, vcenter_user, vcenter_password)
    if 'EOF' in ans:
        loop = 0
    else:
        loop -= 1
addNFVAdapter(branch1_vmname, br1, vcenter_ip, vcenter_user, vcenter_password)
vmPower(branch1_vmname, 'restart', vcenter_ip, vcenter_user, vcenter_password)

quali_exit(__file__)