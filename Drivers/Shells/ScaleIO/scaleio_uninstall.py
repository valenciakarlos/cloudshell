# service "ScaleIO"

import os
import time
import json
from vCenterCommon import deleteVMs, vmPower
from SIOCommon import getSIOesxs
from quali_remote import powershell

with open(r'c:\ProgramData\QualiSystems\Shells.log', 'a') as f:
    f.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': ' + __file__.split('\\')[-1].replace('.py', '') + ': ' + str(os.environ) + '\r\n')


resource = json.loads(os.environ['RESOURCECONTEXT'])
resource_name = resource['name']
attrs = resource['attributes']

vcenter_ip = attrs['vCenter IP']
vcenter_user = attrs['vCenter Administrator User']
vcenter_password = attrs['vCenter Administrator Password']


#delete scale io datastore
sio_storage_name = attrs['Unified Datastore']
datacenter = attrs['Datacenter']
esx_excludes = attrs['Exclude ESXs From SDC Role']
sio_svm_cluster = attrs['ScaleIO Cluster']
esxs = getSIOesxs(vcenter_ip, vcenter_user, vcenter_password, datacenter, esx_excludes, sio_svm_cluster)
esxs.pop()
esx_for_Storage = esxs[0].split(",")[0]
script = '''Add-PSSnapin VMware.VimAutomation.Core\n
        Connect-VIServer -Server ''' + vcenter_ip + ''' -User ''' + vcenter_user + ''' -Password ''' + vcenter_password + ''' -WarningAction SilentlyContinue\n
        Remove-Datastore -Datastore ''' + sio_storage_name + ''' -VMHost ''' + esx_for_Storage + ''' -Confirm:$false
        '''
powershell(script)


#delete vms
vm_name_prefix = attrs['ScaleIO SVM Name PreFix'] + '*'
vmPower(vm_name_prefix, 'stop', vcenter_ip, vcenter_user, vcenter_password)
deleteVMs(vm_name_prefix, vcenter_ip, vcenter_user, vcenter_password)
