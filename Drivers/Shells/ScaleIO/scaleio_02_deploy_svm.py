# service "ScaleIO"

from vCenterCommon import deployVM, changeVMadapter, vmPower
from qualipy.api.cloudshell_api import CloudShellAPISession
from SIOCommon import *
from quali_remote import powershell, notify_user
import datetime
import os
import json
# a = True
# while a:
#     time.sleep(10)
with open(r'c:\ProgramData\QualiSystems\Shells.log', 'a') as f:
    f.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': ' + __file__.split('\\')[-1].replace('.py', '') + ': ' + str(os.environ) + '\r\n')

starttime = datetime.datetime.now()

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
gateway_esx = attrs['Host for ScaleIO Gateway']
esx_excludes = attrs['Exclude ESXs From SDC Role']
esx_password = attrs['ESX Root Password']

# SIO Deployment Info
thick_thin = attrs['ScaleIO SVM DiskType']
vm_name = attrs['ScaleIO SVM Name PreFix']
sio_svm_cluster = attrs['ScaleIO Cluster']
sio_mgmt_portgroup = attrs['Management Network Label']
sio_data1_portgroup = attrs['Data Network Label']
sio_data2_portgroup = attrs['Data2 Network Label']


# Path Info
ova_path = attrs['OVA Full Path']


# IP Info
mgmt_netmask = attrs['MGMT Subnet']
data1_netmask = attrs['Data Subnet']
data2_netmask = attrs['Data2 Subnet']
mgmt_gw = attrs['MGMT Gateway']

svm1_mgmt_ip = attrs['Primary MDM Management IP']
svm2_mgmt_ip = attrs['Secondary MDM Management IP']
svm3_mgmt_ip = attrs['Tie Breaker Management IP']
svm4_mgmt_ip = attrs['Gateway Management IP']

svm1_data1_ip = attrs['Primary MDM Data IP']
svm2_data1_ip = attrs['Secondary MDM Data IP']
svm3_data1_ip = attrs['Tie Breaker Data IP']
svm4_data1_ip = attrs['Gateway Data IP']

svm1_data2_ip = attrs['Primary MDM Data2 IP']
svm2_data2_ip = attrs['Secondary MDM Data2 IP']
svm3_data2_ip = attrs['Tie Breaker Data2 IP']
svm4_data2_ip = attrs['Gateway Data2 IP']

# svm1_data2_ip = '10.10.109.1'
# svm2_data2_ip = '10.10.109.2'
# svm3_data2_ip = '10.10.109.3'
# svm4_data2_ip = '10.10.109.4'

# sds1_mgmt_ip = attrs['SDS1 MGMT IP']
# sds2_mgmt_ip = attrs['SDS2 MGMT IP']
# sds3_mgmt_ip = attrs['SDS3 MGMT IP']
# sds4_mgmt_ip = attrs['SDS4 MGMT IP']
#
# sds1_data1_ip = attrs['SDS1 Data IP']
# sds2_data1_ip = attrs['SDS2 Data IP']
# sds3_data1_ip = attrs['SDS3 Data IP']
# sds4_data1_ip = attrs['SDS4 Data IP']
#
# sds1_data2_ip = '' #'192.168.73.250'
# sds2_data2_ip = '' #'192.168.73.251'
# sds3_data2_ip = '' #'192.168.73.252'
# sds4_data2_ip = '' #'192.168.73.253'

siodic = {
    'Primary': [svm1_mgmt_ip, svm1_data1_ip, svm1_data2_ip],
    'Secondary': [svm2_mgmt_ip, svm2_data1_ip, svm2_data2_ip],
    'TieBreaker': [svm3_mgmt_ip, svm3_data1_ip, svm3_data2_ip],
}

sdsippool = {
    # 'SDS-1': [sds1_mgmt_ip, sds1_data1_ip, sds1_data2_ip],
    # 'SDS-2': [sds2_mgmt_ip, sds2_data1_ip, sds2_data2_ip],
    # 'SDS-3': [sds3_mgmt_ip, sds3_data1_ip, sds3_data2_ip],
    # 'SDS-4': [sds4_mgmt_ip, sds4_data1_ip, sds4_data2_ip],

}
sdsmgmt = attrs['SDS Management IPs CSV'].split(',')
sdsdata = attrs['SDS Data IPs CSV'].split(',')
sdsdata2 = attrs['SDS Data2 IPs CSV'].split(',')

for i in range(len(sdsmgmt)):
    sdsippool['SDS-%d' % (i+1)] = [sdsmgmt[i], sdsdata[i], sdsdata2[i]]



#connect to api
api = CloudShellAPISession(connectivity_details["serverAddress"], reservation_details["ownerUser"], reservation_details["ownerPass"], reservation_details["domain"])
reservationId = reservation_details["id"]


script = '''Add-PSSnapin VMware.VimAutomation.Core\n
        Connect-VIServer -Server ''' + vcenter_ip + ''' -User ''' + vcenter_user + ''' -Password ''' + vcenter_password + ''' -WarningAction SilentlyContinue \n
$store = (Get-Datastore -VMhost "''' + gateway_esx + '''" | Where-Object {$_.Name -like 'datastore*'}).Name\n
$cluster = (Get-Cluster -VMHost "''' + gateway_esx + '''").Name\n
Write-Host "<%<%", $store','$cluster'''
gatewayesx = powershell(script).split('<%<%')[1].strip().split(',')


esxs = getSIOesxs(vcenter_ip, vcenter_user, vcenter_password, datacenter, esx_excludes, sio_svm_cluster)
esxs.pop()

# If Total amount of ESXs in the system are less then 3
while len(esxs) < 3:
    esxs.append('NOESX,,')

mdm_number = 0
sds_number = 1
_sdclist = []
for esx in esxs:
    esx_name = esx.split(",")[0]
    esx_role = esx.split(",")[1]
    esx_storage = esx.split(",")[2]
    esx_cluster = esx.split(",")[3]
    # If There's less then 3 Total ESX, assign the first ESX info to all missing
    if esx_name == "NOESX":
        esx_name = esxs[0].split(",")[0]
        esx_role = 'MDM'
        esx_storage = esxs[0].split(",")[2]
    if esx_role == "MDM":
        print esx_name + " is MDM"
        svm = list(siodic.items()[mdm_number])
        info = svm[1]
        info += [esx_name]
        info += [esx_storage]
        info += [esx_cluster]
        svm[1] = info
        siodic.items()[mdm_number] = tuple(svm)
        mdm_number += 1
    else:
        print esx_name + " is SDC"
    _sdclist += [esx_name]

for esx in esxs:
    esx_name = esx.split(",")[0]
    esx_role = esx.split(",")[1]
    esx_storage = esx.split(",")[2]
    esx_cluster = esx.split(",")[3]
    if esx_role == "SDS":
        print esx_name + " is SDS"
        sds_name = 'SDS-' + str(sds_number)
        sdsparams = [sdsippool[sds_name][0], sdsippool[sds_name][1], sdsippool[sds_name][2], esx_name, esx_storage,
                     esx_cluster]
        siodic[sds_name] = sdsparams
        sds_number += 1
# Remove duplicate ESXs (if there's any)
sdclist = []
for i in _sdclist:
    if i not in sdclist:
        sdclist.append(i)


# Deploy SVM
for name in siodic:
    _vm_name = vm_name + '-' + name
    command = '--skipManifestCheck --noSSLVerify  --allowExtraConfig --datastore=' + '"' + siodic[name][4] + '"' + ' --acceptAllEulas --diskMode=' + thick_thin + ' --net:"VM Network"="' + sio_mgmt_portgroup + '" --name="' + _vm_name + '" ' + ova_path + ' "vi://' + vcenter_user + ':"' + vcenter_password + '"@' + vcenter_ip + '/' + datacenter + '/host/' + siodic[name][5] + '/' + siodic[name][3] + '"'
    notify_user(api, reservationId, "Deploying " + _vm_name)
    deployVM(command, _vm_name, vcenter_ip, vcenter_user, vcenter_password, False, True)

# Deploy Gateway
_vm_name = vm_name + "-Gateway"
command = '--skipManifestCheck --noSSLVerify  --allowExtraConfig --datastore=' + '"' + gatewayesx[0] + '"' + ' --acceptAllEulas --diskMode=' + thick_thin + ' --net:"VM Network"="' + sio_mgmt_portgroup + '" --name="' + _vm_name + '" ' + ova_path + ' "vi://' + vcenter_user + ':"' + vcenter_password + '"@' + vcenter_ip + '/' + datacenter + '/host/' + gatewayesx[1] + '/' + gateway_esx + '"'
notify_user(api, reservationId, "Deploying " + _vm_name)
deployVM(command, _vm_name, vcenter_ip, vcenter_user, vcenter_password, False, True)


# Add Gateway to the dictionary
siodic['Gateway'] = [svm4_mgmt_ip, '', '', gatewayesx[1], gatewayesx[0]]
#  siodic['Gateway'] = [svm4_mgmt_ip, svm4_data1_ip, svm4_data2_ip, gatewayesx[1], gatewayesx[0]]

# Add UUID attribute to the VMs
notify_user(api, reservationId, "Power on VMs")
for name in siodic:
    _vm_name = vm_name + '-' + name
    script = '''Add-PSSnapin VMware.VimAutomation.Core\n
    Connect-VIServer -Server ''' + vcenter_ip + ''' -User ''' + vcenter_user + ''' -Password ''' + vcenter_password + ''' -WarningAction SilentlyContinue\n
    $v = Get-VM -Name ''' + _vm_name + '''
    New-AdvancedSetting -Entity $v -Name disk.EnableUUID -Value TRUE -Confirm:$false -Force:$true
    '''
    powershell(script)
    vmPower(_vm_name, 'start', vcenter_ip, vcenter_user, vcenter_password)

time.sleep(60)
notify_user(api, reservationId, "Configure VMs network")
for name in siodic:
    _vm_name = vm_name + '-' + name
    # Reconfigure VM NICs for Data network
    changeVMadapter(_vm_name, ("2", "3"), (sio_data1_portgroup, sio_data2_portgroup), vcenter_ip, vcenter_user, vcenter_password)
    # Configure SVM ETHs
    if siodic[name][0] != '':
        configureSIOnetwork('eth0', siodic[name][0], mgmt_netmask, _vm_name, vcenter_ip, vcenter_user, vcenter_password)
    if siodic[name][1] != '':
        configureSIOnetwork('eth1', siodic[name][1], data1_netmask, _vm_name, vcenter_ip, vcenter_user, vcenter_password)
    if siodic[name][2] != '':
        configureSIOnetwork('eth2', siodic[name][2], data2_netmask, _vm_name, vcenter_ip, vcenter_user, vcenter_password)
    # Configure Routes
    configureSIORoute('eth0', mgmt_gw, _vm_name, vcenter_ip, vcenter_user, vcenter_password)
    restartService('network', 'restart', _vm_name, vcenter_ip, vcenter_user, vcenter_password)

# Add RDM to SVMs
notify_user(api, reservationId, "Add RDM to SVMs")
diskdic = {}
for name in siodic:
    _vm_name = vm_name + '-' + name
    # Skip Gateway SVM
    if not "Gateway" in _vm_name:
        disks = getESXfreedisks(siodic[name][3], vcenter_ip, vcenter_user, vcenter_password).split('<%<%')[1].strip()
        # Check if the ESX have any free disks
        if disks != None:
            for disk in disks.split(";"):
                diskesx = disk.split(",")[0]
                diskname = disk.split(",")[1]
                diskssd = disk.split(",")[2]
                disksize = disk.split(",")[3]
                # Remove Disks with less than 100GB of space form the list
                if float(disksize) >= 100:
                    if _vm_name in diskdic:
                        diskdic[_vm_name] = diskdic[_vm_name] + [diskname, diskssd, disksize]
                    else:
                        diskdic[_vm_name] = [diskname, diskssd, disksize]


for vm in diskdic:
    for n in xrange(len(diskdic[vm])/3):
        print "VM name is: " + vm + " Disk " + diskdic[vm][n*3] + " Size: " + diskdic[vm][(n*3)+2]
        createRDMdisk(vm, diskdic[vm][n*3], vcenter_ip, vcenter_user, vcenter_password)


# Add AutoStart to the ESXs and SVMs
svms = ''
for svm in siodic:
    _vm_name = vm_name + '-' + svm
    svms += _vm_name + ','

configureAutomaticstart(svms[:-1], datacenter, vcenter_ip, vcenter_user, vcenter_password)


endtime = datetime.datetime.now()
print "Total Deployment time: " + str(endtime - starttime)
