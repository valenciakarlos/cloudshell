# service "vCloud Director"

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
datastore = attrs['Datastore']
thick_thin = attrs['Disk Format']
vcd_ip = attrs['vCD Management IP']
netmask = attrs['vCD Management Netmask']
gateway = attrs['vCD Management Gateway']
dns1 = attrs['vCD Management DNS1']
dns2 = attrs['vCD Management DNS2']
search_domains = attrs['vCD Management Search Domains']
vcd_ip2 = attrs['vCD VM IP']
netmask2 = attrs['vCD VM Netmask']
gateway2 = attrs['vCD VM Gateway']
hostname = attrs['vCD Hostname']
rootpass = attrs['vCD Root Password']

portgroup = attrs['vCD Management Portgroup Name']
portgroup2 = attrs['vCD VM Portgroup Name']
vm_name = attrs['vCD VM Name']
ova_path = '"'+attrs['vCD Local OVA Path']+'"'

vcenter_user = attrs['vCenter Administrator User']
vcenter_password = attrs['vCenter Administrator Password']
vcenter_ip = attrs['vCenter IP']
datacenter = attrs['Datacenter']
cluster = attrs['vCD Cluster']

command = ' --machineOutput --noSSLVerify --powerOn --allowExtraConfig --datastore=' + '"' + datastore + '"' + ' --acceptAllEulas --diskMode=' + thick_thin + ' --prop:DNS1=' + dns1 + ' --prop:DNS2=' + dns2 + ' --prop:Gateway=' + gateway + ' --prop:Gateway2=' + gateway2 + ' --prop:Hostname="' + hostname + '"  --prop:IP=' + vcd_ip + ' --prop:IP2=' + vcd_ip2 + ' --prop:Netmask=' + netmask + ' --prop:Netmask2=' + netmask2 + ' --prop:Root_Password="' + rootpass + '" --prop:Search_Domains="' + search_domains + '" --net:"mgmtportgrp"="' + portgroup + '" --net:"cmpPortGroup"="' + portgroup2 + '" --name="' + vm_name + '" ' + ova_path + ' "vi://' + vcenter_user + ':"' + vcenter_password + '"@' + vcenter_ip + '/' + datacenter + '/host/' + cluster + '/Resources"'
deployVM(command, vm_name, vcenter_ip, vcenter_user, vcenter_password, False, True)

quali_exit(__file__)