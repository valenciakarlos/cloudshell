# service "NSX Manager"

# # demo
# import time
# time.sleep(3)
# print 'Executed ' + __file__.split('\\')[-1].replace('.py', '')
# exit()
# # /demo


import os
import json
import time
import sys
from vCenterCommon import deployVM
from quali_remote import quali_enter, quali_exit, qs_trace, qs_info

quali_enter(__file__)

# with open(r'c:\ProgramData\QualiSystems\Shells.log', 'a') as f:
#     f.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': ' + __file__.split('\\')[-1].replace('.py', '') + ': ' + str(os.environ) + '\r\n')

resource = json.loads(os.environ['RESOURCECONTEXT'])
resource_name = resource['name']
attrs = resource['attributes']

nsx_ip = attrs['NSX IP']
nsx_user = attrs['NSX Username']
nsx_password = attrs['NSX Password']

datastore = attrs['Datastore']
thick_thin = attrs['NSX Disk Format']
nsx_hostname = attrs['NSX Hostname']
netmask = attrs['NSX Netmask']
gateway = attrs['NSX Gateway IP']
dns_csv = attrs['NSX DNS Server IP']
ntp = attrs['NSX NTP Servers']
portgroup = attrs['NSX Portgroup Name']
name = attrs['NSX VM Name']
ova_path = attrs['Local NSX OVA Path']
nsx_domain = attrs['NSX Search Domain']
vcenter_user = attrs['vCenter Administrator Username']
vcenter_password = attrs['vCenter Administrator Password']
vcenter_ip = attrs['vCenter IP']
datacenter = attrs['Datacenter']
cluster = attrs['Cluster']

# STEPS # Quit if name already exists on vcenter_ip vcenter_user vcenter_password

command = ' --machineOutput --noSSLVerify --allowExtraConfig --powerOn --acceptAllEulas --datastore="' + datastore + "\" --diskMode=\"" + thick_thin +"\" --prop:vsm_hostname=\"" + nsx_hostname + "\" --prop:vsm_ip_0=" + nsx_ip + " --prop:vsm_netmask_0=" + netmask + " --prop:vsm_gateway_0=" + gateway + " --prop:vsm_dns1_0=" + dns_csv + " --prop:vsm_domain_0=" + nsx_domain +" --prop:vsm_ntp_0=" + ntp + " --prop:vsm_isSSHEnabled=True" + " --net:VSMgmt=\"" + portgroup + "\" --prop:vsm_cli_passwd_0=" + nsx_password + " --prop:vsm_cli_en_passwd_0=" + nsx_password + " --name=" + name +" " + ova_path + ' "vi://''' + vcenter_user + ''':''' + '"' + vcenter_password + '"' + '''@''' + vcenter_ip + '''/''' + datacenter + '''/host/''' + cluster + '/Resources"'
deployVM(command, name, vcenter_ip, vcenter_user, vcenter_password, False, True)

quali_exit(__file__)