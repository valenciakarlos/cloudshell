# service "vRealize Log Insight"

#
# # demo
# import time
# time.sleep(3)
# print 'Executed ' + __file__.split('\\')[-1].replace('.py', '')
# exit()
# # /demo

import json
import os
import time
import sys
from vCenterCommon import deployVM
from quali_remote import quali_enter, quali_exit, qs_trace, qs_info

quali_enter(__file__)

resource = json.loads(os.environ['RESOURCECONTEXT'])
resource_name = resource['name']
attrs = resource['attributes']
datastore = attrs['Log Insight Datastore']
thick_thin = attrs['Log Insight Disk Format']
gateway = attrs['Log Insight Gateway']
dns_ip = attrs['Log Insight DNS Server IP']
vlogs_ip = attrs['Log Insight IP']
vlogs_netmask = attrs['Log Insight Netmask']
portgroup = attrs['Log Insight Portgroup Name']
vm_name = attrs['Log Insight VM Name']
ova_path = '"'+attrs['Log Insight Local OVA Path']+'"'
vcenter_user = attrs['vCenter Administrator User']
vcenter_password = attrs['vCenter Administrator Password']
vcenter_ip = attrs['vCenter FQDN']
datacenter = attrs['Log Insight Datacenter']
cluster = attrs['Log Insight Cluster']

# STEPS # Quit if vm_name already exists on vcenter_ip vcenter_user vcenter_password
command = ' --machineOutput --noSSLVerify --powerOn --allowExtraConfig --datastore=' + '"' + datastore + '"' + ' --acceptAllEulas --diskMode=' + thick_thin + ' --prop:vami.hostname.VMware_vCenter_Log_Insight="' + vm_name + '"' + ''' --prop:vami.gateway.VMware_vCenter_Log_Insight=''' + gateway + ''' --prop:vami.DNS.VMware_vCenter_Log_Insight=''' + dns_ip + ''' --prop:vami.ip0.VMware_vCenter_Log_Insight=''' + vlogs_ip + ''' --prop:vami.netmask0.VMware_vCenter_Log_Insight=''' + vlogs_netmask + ' --net:' + '"'+'Network 1'+'"'+'=' + '"' + portgroup + '"' + ''' --name="''' +vm_name + '" ' + ova_path + ''' "vi://''' + vcenter_user + ''':''' + '"' + vcenter_password + '"' + '''@''' + vcenter_ip + '''/''' + datacenter + '''/host/''' + cluster + '''/Resources"'''
deployVM(command, vm_name, vcenter_ip, vcenter_user, vcenter_password, False, True)

quali_exit(__file__)