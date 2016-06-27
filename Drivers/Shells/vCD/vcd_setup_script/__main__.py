# service "vCloud Director"
import os
import subprocess
import json
import zipfile
import shutil
import time

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

tempdir = os.path.dirname(__file__) + '\\..\\temp'
if not os.path.exists(tempdir):
    os.makedirs(tempdir)

with zipfile.ZipFile(os.path.dirname(__file__), "r") as z:
    z.extractall(tempdir)

if os.getenv('RESOURCECONTEXT', 0) != 0:
    resource = json.loads(os.environ['RESOURCECONTEXT'])
    resource_name = resource['name']
    attrs = resource['attributes']

    #take all inputs from the attributes
    vcAddress = attrs['vCenter IP']
    vcUsername = attrs['vCenter Administrator User']
    vcPassword = attrs['vCenter Administrator Password']
    vcName = attrs['vCD Attached vCenter Name'] #
    searchDomain = attrs['vCD Management Search Domains']
    systemName = attrs['vCD Hostname']
    contactName = attrs['vCD Contact Name'] #
    contactEmail = attrs['vCD Contact Email'] #
    adminName = attrs['vCD Administrator User'] #
    adminPassword = attrs['vCD Administrator Password'] #
    vcdLicense = attrs['vCD License Key'] #
    vsmAddress = attrs['vShield Manager Address'] #
    vsmUsername = attrs['vShield Manager Username'] #
    vsmPassword = attrs['vShield Manager Password'] #

else: #debug
    vcAddress = "10.10.111.32"
    vcUsername = "administrator@vsphere.local"
    vcPassword = "Welcome1!"
    vcName = "vcenter6"
    searchDomain = "lss.emc.com"
    systemName = "scln153"
    contactName = "aaabbb"
    contactEmail = "aaabbb@work.com"
    adminName = "administrator"
    adminPassword = "dangerous"
    vcdLicense = "00000-00000-00000-00000-00000"
    vsmAddress = "10.10.111.233"
    vsmUsername = "admin"
    vsmPassword = "Welcome1!"


output = exe([tempdir + '\\vcd_setup.exe','vcAddress='+vcAddress,'vcUsername="'+vcUsername+'"','vcPassword="'+vcPassword+'"','vcName="'+vcName+'"','searchDomain="'+searchDomain+'"','systemName="'+systemName+'"','contactName="'+contactName+'"','contactEmail="'+contactEmail+'"','adminName="'+adminName+'"','adminPassword="'+adminPassword+'"','vcdLicense="'+vcdLicense+'"','vsmAddress="'+vsmAddress+'"','vsmUsername="'+vsmUsername+'"','vsmPassword="'+vsmPassword+'"'])
print(output)

# delete temp folder
shutil.rmtree(tempdir, ignore_errors=True)

