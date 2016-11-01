# service "vCloud Director"

import os
import time
import json
from vCenterCommon import deleteVMs, vmPower
import subprocess
import sys
from quali_remote import quali_enter, quali_exit, qs_trace, qs_info

quali_enter(__file__)


resource = json.loads(os.environ['RESOURCECONTEXT'])
resource_name = resource['name']
attrs = resource['attributes']

vcenter_ip = attrs['vCenter IP']
vcenter_user = attrs['vCenter Administrator User']
vcenter_password = attrs['vCenter Administrator Password']

vm_name = attrs['vCD VM Name']

vmPower(vm_name, 'stop', vcenter_ip, vcenter_user, vcenter_password)
deleteVMs(vm_name, vcenter_ip, vcenter_user, vcenter_password)

time.sleep(40)

sqlscript = '''
USE [master]
GO

IF  EXISTS (SELECT name FROM sys.databases WHERE name = N'vcloud')
DROP DATABASE [vcloud]
GO

'''

with open(r'c:\deploy\drop_sql_sb.sql', 'w') as file_:
    file_.write(sqlscript)

db_instance = ".\qualisystems2008"
out = subprocess.check_output('sqlcmd -S .\\qualisystems2008 -i c:\\deploy\\drop_sql_sb.sql', stderr=subprocess.STDOUT)
if 'Cannot drop database' in out:
    raise Exception('Could not uninstall vCD: ' + out)

qs_info('vcloud uninstalled')

quali_exit(__file__)