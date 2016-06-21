# service "Versa Director"

import os
import time
import json
from vCenterCommon import deleteVMs, vmPower

with open(r'c:\ProgramData\QualiSystems\Shells.log', 'a') as f:
    f.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': ' + __file__.split('\\')[-1].replace('.py', '') + ': ' + str(os.environ) + '\r\n')


resource = json.loads(os.environ['RESOURCECONTEXT'])
resource_name = resource['name']
attrs = resource['attributes']

vcenter_ip = attrs['vCenter IP']
vcenter_user = attrs['vCenter Administrator User']
vcenter_password = attrs['vCenter Administrator Password']


#remove all vms
vm_name = attrs['Versa Director VM Name']
vmPower(vm_name, 'stop', vcenter_ip, vcenter_user, vcenter_password)
deleteVMs(vm_name, vcenter_ip, vcenter_user, vcenter_password)

vm_name = attrs['Versa Analytics VM Name']
vmPower(vm_name, 'stop', vcenter_ip, vcenter_user, vcenter_password)
deleteVMs(vm_name, vcenter_ip, vcenter_user, vcenter_password)

vm_name = attrs['Versa Controller VM Name']
vmPower(vm_name, 'stop', vcenter_ip, vcenter_user, vcenter_password)
deleteVMs(vm_name, vcenter_ip, vcenter_user, vcenter_password)

vm_name = attrs['Versa Branch1 VM Name']
vmPower(vm_name, 'stop', vcenter_ip, vcenter_user, vcenter_password)
deleteVMs(vm_name, vcenter_ip, vcenter_user, vcenter_password)

vm_name = attrs['Versa Branch2 VM Name']
vmPower(vm_name, 'stop', vcenter_ip, vcenter_user, vcenter_password)
deleteVMs(vm_name, vcenter_ip, vcenter_user, vcenter_password)

#delete versa vds
