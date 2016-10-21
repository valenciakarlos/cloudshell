# service "ScaleIO"


from SIOCommon import getSIOesxs, configureSDC, installSDC
from qualipy.api.cloudshell_api import CloudShellAPISession
from vCenterCommon import rebootESX
from quali_remote import notify_user
import time
import os
import json

# a = True
# while a:
#     time.sleep(10)
with open(r'c:\ProgramData\QualiSystems\Shells.log', 'a') as f:
    f.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': ' + __file__.split('\\')[-1].replace('.py', '') + ': ' + str(os.environ) + '\r\n')

resource = json.loads(os.environ['RESOURCECONTEXT'])
reservation_details = json.loads(os.environ['RESERVATIONCONTEXT'])
connectivity_details = json.loads(os.environ['QUALICONNECTIVITYCONTEXT'])
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

#connect to api
api = CloudShellAPISession(connectivity_details["serverAddress"], reservation_details["ownerUser"], reservation_details["ownerPass"], reservation_details["domain"])
reservationId = reservation_details["id"]

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
        notify_user(api, reservationId, "Installing SDC on " + esx_name)
        installSDC(esx_name, sdcpath, esx_password)
        esx_list += esx_name + ','
    # Reboot ESXs and wait for them (up-to 10 minutes)
    notify_user(api, reservationId, "Rebooting ESX hosts after installation, might take up to 20 minutes")
    rebootESX(esx_list[:-1], vcenter_ip, vcenter_user, vcenter_password)
    notify_user(api, reservationId, "Reboot complete")
    for esx in esxs:
        esx_name = esx.split(",")[0]
        notify_user(api, reservationId, "Configure SDC on " + esx_name)
        configureSDC(esx_name, esx_password, ipstring)
    # After configuring the SDC another reboot to the ESX is required
    notify_user(api, reservationId, "Rebooting ESX hosts after configuration, might take up to 20 minutes")
    rebootESX(esx_list[:-1], vcenter_ip, vcenter_user, vcenter_password)
    notify_user(api, reservationId, "Reboot complete")
    
except Exception, e:
    print e
    with open(r'c:\ProgramData\QualiSystems\Shells.log', 'a') as f:
        f.write(time.strftime('%Y-%m-%d %H:%M:%S') + ' Got Error: ' + str(e) + '\r\n')
    exit(1)
