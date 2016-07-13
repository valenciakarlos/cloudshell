# service "vCloud Director"

import json
import os
import time
import paramiko
import socket
import re
import subprocess

def exe(command_array):
    g = open(r'c:\ProgramData\QualiSystems\Shells.log', 'a')
    g.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': exe: ' + str(command_array) + '\r\n')
    g.close()
    rv = subprocess.check_output(command_array)
    if rv is not None:
        rv = rv.strip()
    g = open(r'c:\ProgramData\QualiSystems\Shells.log', 'a')
    g.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': exe result: ' + str(rv) + '\r\n')
    g.close()
    return str(rv)

with open(r'c:\ProgramData\QualiSystems\Shells.log', 'a') as f:
    f.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': ' + __file__.split('\\')[-1].replace('.py', '') + ': ' + str(os.environ) + '\r\n')

default_dir = "c:\\deploy\\vcd_autoit\\"
vcd_first_file_name = 'vcd_first_setup.exe'
vcd_attach_vc_file_name = 'vcd_attach_vcenter.exe'

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


def first():
    out = exe([default_dir + vcd_first_file_name, vcdLicense, adminName, adminPassword, '"' + contactName + '"', contactEmail, systemName, vcdIp])
    return out


def second():
    out = exe([default_dir + vcd_attach_vc_file_name, vcAddress, vcUsername, vcPassword, vcName, 'https://' + vcAddress + '/vsphere-client', vsmAddress, vsmUsername, vsmPassword, vcdIp, adminName, adminPassword])
    return out
ans = ''
error = True
for x in xrange(3):
    ans = first()
    if 'not found' not in ans.lower():
        print ans
        error = False
        break

if error:
    print "failed to run first setup on vCD " + '\n' + ans
    g = open(r'c:\ProgramData\QualiSystems\Shells.log', 'a')
    g.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': vCD Error: ' + str(ans) + '\r\n')
    exit(1)

time.sleep(5)
ans = ''
error = True
for n in xrange(3):
    ans = second()
    if 'not found' not in ans.lower():
        print ans
        error = False
        break

if error:
    print "failed to attach vCenter to vCD " + '\n' + ans
    g = open(r'c:\ProgramData\QualiSystems\Shells.log', 'a')
    g.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': vCD Error: ' + str(ans) + '\r\n')
    exit(1)
