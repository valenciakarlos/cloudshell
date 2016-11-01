# service "vRealize Operations Manager"

import os
import time
import json
from vCenterCommon import deleteVMs, vmPower
from quali_remote import quali_enter, quali_exit, qs_trace, qs_info

quali_enter(__file__)


resource = json.loads(os.environ['RESOURCECONTEXT'])
resource_name = resource['name']
attrs = resource['attributes']

vcenter_ip = attrs['vCenter FQDN']
vcenter_user = attrs['vCenter Administrator User']
vcenter_password = attrs['vCenter Administrator Password']

vm_name = attrs['vROPS VM Name']

vmPower(vm_name, 'stop', vcenter_ip, vcenter_user, vcenter_password)
deleteVMs(vm_name, vcenter_ip, vcenter_user, vcenter_password)

quali_exit(__file__)