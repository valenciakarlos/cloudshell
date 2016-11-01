# service "Versa Director"

import os
import time
import json
from vCenterCommon import deleteVMs, vmPower
from quali_remote import quali_enter, quali_exit, qs_trace, qs_info

quali_enter(__file__)

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

quali_exit(__file__)