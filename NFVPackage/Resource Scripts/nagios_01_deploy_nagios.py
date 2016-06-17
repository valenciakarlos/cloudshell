# service "Nagios"

import json
import os
import time
import sys
from vCenterCommon import deployVM

with open(r'c:\ProgramData\QualiSystems\Shells.log', 'a') as f:
    f.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': ' + __file__.split('\\')[-1].replace('.py', '') + ': ' + str(os.environ) + '\r\n')

resource = json.loads(os.environ['RESOURCECONTEXT'])
resource_name = resource['name']
attrs = resource['attributes']
datastore = attrs['Nagios Datastore']
thick_thin = attrs['Nagios Disk Format']
nagios_ip = attrs['Nagios IP']
netmask = attrs['Nagios Netmask']
gateway = attrs['Nagios Gateway']
dns1 = attrs['Nagios DNS1']
dns2 = attrs['Nagios DNS2']
search_domains = attrs['Nagios Search Domains']
hostname = attrs['Nagios Hostname']
rootpass = attrs['Nagios Root Password']
portgroup = attrs['Nagios Portgroup Name']
vm_name = attrs['Nagios VM Name']
ova_path = '"'+attrs['Nagios Local OVA Path']+'"'
vcenter_user = attrs['vCenter Administrator User']
vcenter_password = attrs['vCenter Administrator Password']
vcenter_ip = attrs['vCenter IP']
datacenter = attrs['Nagios Datacenter']
cluster = attrs['Nagios Cluster']

try:
    command = ' --machineOutput --noSSLVerify --powerOn --allowExtraConfig --datastore=' + '"' + datastore + '"' + ' --acceptAllEulas --diskMode=' + thick_thin + ' --prop:DNS1=' + dns1 + ' --prop:DNS2=' + dns2 + ' --prop:Gateway=' + gateway + ' --prop:Hostname="' + hostname + '"  --prop:IP=' + nagios_ip + ' --prop:Netmask=' + netmask + ' --prop:Root_Password="' + rootpass + '" --prop:Search_Domains="' + search_domains + '" --net:"Anetwork"="' + portgroup +  '" --name="' + vm_name + '" ' + ova_path + ' "vi://' + vcenter_user + ':"' + vcenter_password + '"@' + vcenter_ip + '/' + datacenter + '/host/' + cluster + '/Resources"'
    deployVM(command, vm_name, vcenter_ip, vcenter_user, vcenter_password, False)
except Exception, e:
    print e
    sys.exit(1)
