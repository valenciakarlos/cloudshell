# service "Versa"

from Versa_Common import *
import sys
import time
import os

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
cluster = attrs['Versa Cluster']

#Director config
vm_name = attrs['Versa Director VM Name']
ova_path = attrs['Versa Director Path']

#Northbound - user facing
versa_nb_ip = attrs['Versa Director NB IP']
versa_nb_dns = attrs['Versa Director NB DNS']
versa_nb_mask = attrs['Versa Director NB Mask']
versa_nb_gateway = attrs['Versa Director NB Gateway']
versa_nb_portgroup = attrs['Versa Director NB Portgroup Name']
versa_nb_eth = 'eth0'
#Southbound - Controller facing
versa_sb_ip = attrs['Versa Director SB IP']
versa_sb_dns = attrs['Versa SB DNS']
versa_sb_mask = attrs['Versa SB Netmask']
versa_sb_gateway = attrs['Versa Controller LAN IP']
versa_sb_portgroup = attrs['Versa Director SB Portgroup Name']
versa_sb_eth = 'eth1'

controller_ip = attrs['Versa Controller LAN IP']
controller_mask = attrs['Versa SB Netmask']
controller_network = attrs['Versa SB Network']
versa = {
    versa_nb_eth: (versa_nb_ip, versa_nb_portgroup, versa_nb_mask, versa_nb_gateway, versa_nb_dns),
    versa_sb_eth: (versa_sb_ip, versa_sb_portgroup, versa_sb_mask, versa_sb_gateway, versa_sb_dns),
}

dv_switch = str(attrs['Versa SB VDS'])
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
    # STEPS # Quit if vm_name already exists on vcenter_ip vcenter_user vcenter_password

    session.add_dvPort_group(dv_switch, versa_sb_portgroup, int(vds1_num_ports), vds1_vlanmode, vds1_vlan_ids)

except:
    pass


#Deploy Director
command = ' --skipManifestCheck --noSSLVerify  --allowExtraConfig --datastore=' + '"' + datastore + '"' + ' --acceptAllEulas --diskMode=' + thick_thin + ' --net:"VM Network"="' + versa_sb_portgroup + '" --name="' + vm_name + '" ' + ova_path + ' "vi://' + vcenter_user + ':"' + vcenter_password + '"@' + vcenter_ip + '/' + datacenter + '/host/' + cluster + '/Resources"'
deployVM(command, vm_name, vcenter_ip, vcenter_user, vcenter_password, False)

time.sleep(5)
vmPower(vm_name, 'start', vcenter_ip, vcenter_user, vcenter_password)
addAdapter(vm_name, versa, vcenter_ip, vcenter_user, vcenter_password)
versa = setAdapterMAC(vm_name, versa, vcenter_ip, vcenter_user, vcenter_password)
chmod = '''\"echo \'versa123\' | sudo -S chmod 777 /etc/network/interfaces\"'''
networking = firstEth(versa)
networking += addEth(versa)
networking += addRoute(versa_nb_gateway, controller_ip, controller_mask, controller_network)
networking += '\' > /etc/network/interfaces"'
invokeScript(chmod, vm_name, 'versa', 'versa123', 20, 30, vcenter_ip, vcenter_user, vcenter_password)
invokeScript(networking, vm_name, 'versa', 'versa123', 20, 30, vcenter_ip, vcenter_user, vcenter_password)
vmPower(vm_name, 'restart', vcenter_ip, vcenter_user, vcenter_password)

quali_exit(__file__)