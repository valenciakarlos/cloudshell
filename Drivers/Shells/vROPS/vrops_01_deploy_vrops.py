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

datastore = attrs['vROPS Datastore']
thick_thin = attrs['vROPS Disk Format']
gateway = attrs['vROPS Gateway']
dns_ip = attrs['vROPS DNS Server IP']
vrops_ip = attrs['vROPS IP']
vrops_netmask = attrs['vROPS Netmask']
portgroup = attrs['vROPS Portgroup Name']
vm_name = attrs['vROPS VM Name']
ova_path = attrs['vROPS Local OVA Path']
vcenter_user = attrs['vCenter Administrator User']
vcenter_password = attrs['vCenter Administrator Password']
vcenter_ip = attrs['vCenter FQDN']
datacenter = attrs['vROPS Datacenter']
cluster = attrs['vROPS Cluster']
timezone = attrs['vROPS Timezone']


try:
    subprocess.check_output(
         'C:\Program Files\VMware\VMware OVF Tool\ovftool.exe --machineOutput --noSSLVerify --powerOn --allowExtraConfig --datastore="' + datastore + '"' + ' --acceptAllEulas --diskMode=' + thick_thin + ' --prop:vamitimezone="' + timezone + '"' + ' --prop:vami.gateway.vRealize_Operations_Manager_Appliance=' + gateway + ' --prop:vami.DNS.vRealize_Operations_Manager_Appliance=' + dns_ip +' --prop:vami.ip0.vRealize_Operations_Manager_Appliance=' + vrops_ip + ' --prop:vami.netmask0.vRealize_Operations_Manager_Appliance=' + vrops_netmask + ' --net:"Network 1"=' + '"' + portgroup + '"' + ' --name="''' + vm_name + '"' + ' "' + ova_path + '"' + ' "vi://' + vcenter_user + ':' + '"' + vcenter_password + '"' + '@' + vcenter_ip + '/' + datacenter + '/host/' +  cluster + '/Resources"'
    )
except subprocess.CalledProcessError as e:
    print '\r\n' + e.output
    exit(1)
