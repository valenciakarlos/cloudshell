# service "vCloud Director"

import json
import os
import time
import subprocess
import zipfile
import shutil
import sys

from quali_remote import quali_enter, quali_exit, qs_trace, qs_info

quali_enter(__file__)


def exe(command_array):
    qs_trace('exe: ' + str(command_array))
    rv = subprocess.check_output(command_array)
    if rv is not None:
        rv = rv.strip()
    qs_trace('exe result: ' + str(rv))
    return str(rv)


default_dir = "c:\\deploy\\vcd_autoit\\"
vcd_first_file_name = 'vcd_first_setup.exe'
vcd_attach_vc_file_name = 'vcd_attach_vcenter.exe'

if not os.path.exists(default_dir):
    os.makedirs(default_dir)

with zipfile.ZipFile(os.path.dirname(__file__), "r") as z:
    z.extractall(default_dir)

resource = json.loads(os.environ['RESOURCECONTEXT'])
resource_name = resource['name']
attrs = resource['attributes']
# take all inputs from the attributes
vcAddress = attrs['vCenter IP']
vcUsername = attrs['vCenter Administrator User']
vcPassword = attrs['vCenter Administrator Password']
vcName = attrs['vCD Attached vCenter Name']
searchDomain = attrs['vCD Management Search Domains']
systemName = attrs['vCD Hostname']
contactName = attrs['vCD Contact Name']
contactEmail = attrs['vCD Contact Email']
adminName = attrs['vCD Administrator User']
adminPassword = attrs['vCD Administrator Password']
vcdLicense = attrs['vCD License Key']
vsmAddress = attrs['vShield Manager Address']
vsmUsername = attrs['vShield Manager Username']
vsmPassword = attrs['vShield Manager Password']
vcdIp = attrs['vCD Management IP']

contactName.replace(' ', '###')
def first():
    out = exe([default_dir + vcd_first_file_name, vcdLicense, adminName, adminPassword, contactName, contactEmail, systemName, vcdIp])
    return out


def second():
    out = exe([default_dir + vcd_attach_vc_file_name, vcAddress, vcUsername, vcPassword, vcName, 'https://' + vcAddress + '/vsphere-client', vsmAddress, vsmUsername, vsmPassword, vcdIp, adminName, adminPassword])
    return out

ans = ''
error = True
for x in xrange(3):
    ans = first()
    if 'not found' not in ans.lower():
        error = False
        break
    else:
        time.sleep(30)

if error:
    shutil.rmtree(default_dir, ignore_errors=True)
    raise Exception("failed to run first setup on vCD " + '\n' + ans)

time.sleep(5)
ans = ''
error = True
for n in xrange(3):
    ans = second()
    if 'not found' not in ans.lower():
        error = False
        break
    else:
        time.sleep(30)

if error:
    shutil.rmtree(default_dir, ignore_errors=True)
    raise Exception("failed to attach vCenter to vCD " + '\n' + ans)

shutil.rmtree(default_dir, ignore_errors=True)

quali_exit(__file__)