# service "vCloud Director"

import json
import os
import time
import subprocess

with open(r'c:\ProgramData\QualiSystems\Shells.log', 'a') as f:
    f.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': ' + __file__.split('\\')[-1].replace('.py', '') + ': ' + str(os.environ) + '\r\n')

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

try:
    subprocess.check_output(
        'C:\Program Files\VMware\VMware OVF Tool\ovftool.exe --machineOutput --noSSLVerify --powerOn --allowExtraConfig --datastore=' + '"' + datastore + '"' + ' --acceptAllEulas --diskMode=' + thick_thin + ' --prop:DNS1=' + dns1 + ' --prop:DNS2=' + dns2 + ' --prop:Gateway=' + gateway + ' --prop:Gateway2=' + gateway2 + ' --prop:Hostname="' + hostname + '"  --prop:IP=' + vcd_ip + ' --prop:IP2=' + vcd_ip2 + ' --prop:Netmask=' + netmask + ' --prop:Netmask2=' + netmask2 + ' --prop:Root_Password="' + rootpass + '" --prop:Search_Domains="' + search_domains + '" --net:"Management Network"="' + portgroup + '" --net:"VM Network"="' + portgroup2 + '" --name="' +vm_name + '" ' + ova_path + ' "vi://' + vcenter_user + ':"' + vcenter_password + '"@' + vcenter_ip + '/' + datacenter + '/host/' + cluster + '/Resources"'
    )
except subprocess.CalledProcessError as e:
    print '\r\n' + e.output
    sys.exit(1)

'''
<Property oe:key="DNS1" oe:value="10.254.66.23"/>
         <Property oe:key="DNS2" oe:value="10.254.66.24"/>
         <Property oe:key="Gateway" oe:value="10.10.111.1"/>
         <Property oe:key="Gateway2" oe:value="11.111.11.1"/>
         <Property oe:key="Hostname" oe:value="vcd-centos"/>
         <Property oe:key="IP" oe:value="10.10.111.152"/>
         <Property oe:key="IP2" oe:value="11.11.11.11"/>
         <Property oe:key="Netmask" oe:value="255.255.255.0"/>
         <Property oe:key="Netmask2" oe:value="255.255.255.0"/>
         <Property oe:key="Root_Password" oe:value=""/>
         <Property oe:key="Search_Domains" oe:value="lss.emc.com"/>
		 
ovftool --machineOutput --noSSLVerify --allowExtraConfig --powerOn --datastore="datastore204" --acceptAllEulas --diskMode=thin --prop:DNS1=10.254.66.23 --prop:DNS2=10.254.66.24 --prop:Gateway=10.10.111.1 --prop:Gateway2=11.11.11.1 --prop:Hostname="vcd-centos2" --prop:IP=10.10.111.152 --prop:IP2=11.11.11.11 --prop:Netmask=255.255.255.0 --prop:Netmask2=255.255.255.0 --prop:Root_Password="dangerous2" --prop:Search_Domains="lcc.emc.com" --net:"Management Network"="Management Network" --net:"VM Network"="VM Network" --name="vcd2" c:\deploy\vcd-centos.ova vi:"//administrator@vsphere.local:"Sc@t$g045"@10.10.111.232/vmworlddemo2/host/SIO/Resources" \
                                
ovftool.exe --machineOutput --noSSLVerify --powerOn --allowExtraConfig --datastore="datastore204" --acceptAllEulas --diskMode=thin --prop:hostname="vcd2-vm" --prop:DNS1=10.254.66.23 --prop:DNS2=10.254.66.24 --prop:Gateway=10.10.111.1 --prop:Gateway2=11.11.11.11 --prop:Hostname="vcd2"  --prop:IP=10.10.111.152 --prop:IP2=11.11.11.12 --prop:Netmask=255.255.255.0 --prop:Netmask2=255.255.255.0 --prop:Root_Password="dangerous2" --prop:Search_Domains="lss.emc.com" --net:"Management Network"="Management Network" --net:"VM Network"="VM Network" --name="vcd2-vm" "c:\deploy\vcd-centos.ova" "vi://Sc@t$g045:"administrator@vsphere.local"@10.10.111.232/vmworlddemo2/host/SIO/Resources"
								'''