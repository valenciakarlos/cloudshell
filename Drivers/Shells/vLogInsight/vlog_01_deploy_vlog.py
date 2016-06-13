# service "vRealize Operations Manager"

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
import subprocess

with open(r'c:\ProgramData\QualiSystems\Shells.log', 'a') as f:
    f.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': ' + __file__.split('\\')[-1].replace('.py', '') + ': ' + str(os.environ) + '\r\n')

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


try:
    subprocess.check_output(
         'C:\Program Files\VMware\VMware OVF Tool\ovftool.exe --machineOutput --noSSLVerify --powerOn --allowExtraConfig --datastore=' + '"' + datastore + '"' + ' --acceptAllEulas --diskMode=' + thick_thin + ' --prop:vami.hostname.VMware_vCenter_Log_Insight="' + vm_name + '"' + ''' --prop:vami.gateway.VMware_vCenter_Log_Insight=''' + gateway + ''' --prop:vami.DNS.VMware_vCenter_Log_Insight=''' + dns_ip+ ''' --prop:vami.ip0.VMware_vCenter_Log_Insight=''' + vlogs_ip + ''' --prop:vami.netmask0.VMware_vCenter_Log_Insight=''' + vlogs_netmask + ' --net:'+'"'+'Network 1'+'"'+'=' + '"' +portgroup + '"'+''' --name="''' +vm_name +'" '+ova_path+''' "vi://''' + vcenter_user + ''':''' + '"' + vcenter_password + '"' + '''@''' + vcenter_ip + '''/''' + datacenter + '''/host/''' + cluster + '''/Resources"'''
    )
except subprocess.CalledProcessError as e:
    print '\r\n' + e.output
    exit(1)
