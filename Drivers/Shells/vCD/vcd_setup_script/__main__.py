#service ScaleIO
import os
import subprocess
import time
import json
import pkgutil
import zipfile
import shutil

def exe(command_array):
    return subprocess.check_output(command_array)

tempdir = os.path.dirname(__file__) + '\\..\\temp'
if not os.path.exists(tempdir):
    os.makedirs(tempdir)
	
with zipfile.ZipFile(os.path.dirname(__file__), "r") as z:
    z.extractall(tempdir)

if os.getenv('RESOURCECONTEXT',0)!=0:
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

#delete temp folder
shutil.rmtree(tempdir, ignore_errors=True)