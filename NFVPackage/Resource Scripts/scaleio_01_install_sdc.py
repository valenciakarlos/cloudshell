# service "ScaleIO"

from SIOCommon import getSIOesxs, configureSDC, installSDC
from vCenterCommon import rebootESX
import time
import os
import json

with open(r'c:\ProgramData\QualiSystems\Shells.log', 'a') as f:
    f.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': ' + __file__.split('\\')[-1].replace('.py', '') + ': ' + str(os.environ) + '\r\n')

resource = json.loads(os.environ['RESOURCECONTEXT'])
resource_name = resource['name']
attrs = resource['attributes']

# vCenter Info
vcenter_ip = attrs['vCenter IP']
vcenter_user = attrs['vCenter Username']
vcenter_password = attrs['vCenter Password']
datacenter = attrs['Datacenter']
esx_excludes = attrs['Exclude ESXs From SDC Role']
esx_password = attrs['ESX Root Password']

# Path Info
sdcpath = attrs['SDC Path']

# SIO Info
sio_svm_cluster = attrs['ScaleIO Cluster']
# IP Info

svm1_mgmt_ip = attrs['Primary MDM Management IP']
svm2_mgmt_ip = attrs['Secondary MDM Management IP']

svm1_data1_ip = attrs['Primary MDM Data IP']
svm2_data1_ip = attrs['Secondary MDM Data IP']

svm1_data2_ip = ''  
svm2_data2_ip = ''  

sds1_mgmt_ip = ''  
sds2_mgmt_ip = ''  
sds3_mgmt_ip = ''  
sds4_mgmt_ip = ''  

sds1_data1_ip = ''  
sds2_data1_ip = ''  
sds3_data1_ip = ''  
sds4_data1_ip = ''  

sds1_data2_ip = ''  
sds2_data2_ip = ''  
sds3_data2_ip = ''  
sds4_data2_ip = ''  


esxs = getSIOesxs(vcenter_ip, vcenter_user, vcenter_password, datacenter, esx_excludes, sio_svm_cluster)
esxs.pop()
esx_list = ''
ipstring = ''
for ip in [svm1_data1_ip, svm2_data1_ip, svm1_data2_ip, svm2_data2_ip]:
    if ip != '':
        ipstring += ip + ','
ipstring = ipstring[:-1]

try:
    for esx in esxs:
        esx_name = esx.split(",")[0]
        installSDC(esx_name, sdcpath, esx_password)
        esx_list += esx_name + ','
    # Reboot ESXs and wait for them (up-to 10 minutes)
    rebootESX(esx_list[:-1], vcenter_ip, vcenter_user, vcenter_password)
    for esx in esxs:
        esx_name = esx.split(",")[0]
        configureSDC(esx_name, esx_password, ipstring)
    rebootESX(esx_list[:-1], vcenter_ip, vcenter_user, vcenter_password)

except Exception, e:
    print e
    with open(r'c:\ProgramData\QualiSystems\Shells.log', 'a') as f:
        f.write(time.strftime('%Y-%m-%d %H:%M:%S') + ' Got Error: ' + e + '\r\n')
    exit(1)
