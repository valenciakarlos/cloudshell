# service "vCenter"

import os
import json
import subprocess
import time
import sys
from quali_remote import powershell

with open(r'c:\ProgramData\QualiSystems\Shells.log', 'a') as f:
    f.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': ' + __file__.split('\\')[-1].replace('.py', '') + ': ' + str(os.environ) + '\r\n')

resource = json.loads(os.environ['RESOURCECONTEXT'])
resource_name = resource['name']
attrs = resource['attributes']


vcenter_iso = attrs['vCenter ISO location']
vcenter_portgroup = attrs['vCenter Portgroup Name']
vcenter_size = attrs['vCenter Deployment Size']
vcenter_vm_name = attrs['vCenter VM Name']
vcenter_diskformat = attrs['vCenter Disk Format']
vcenter_esx_ip = attrs['vCenter ESXi IP']
vcenter_esx_username = attrs['vCenter ESXi Username']
vcenter_esx_password = attrs['vCenter ESXi Password']
vcenter_datastore = attrs['vCenter Datastore']
vcenter_hostname = attrs['vCenter Hostname']
vcenter_dns1 = attrs['vCenter DNS1']
#vcenter_dns2 = attrs['vCenter DNS2']  #for 6.0.1
vcenter_gateway = attrs['vCenter Gateway']
vcenter_ip = attrs['vCenter IP']
vcenter_prefix = attrs['vCenter Prefix']
vcenter_password = attrs['vCenter Administrator Password']
vcenter_sso_password = attrs['vCenter SSO Password']
vcenter_sso_domain = attrs['vCenter SSO Domain']
vcenter_sso_site = attrs['vCenter SSO Site Name']
vcenter_ntp_server = attrs['vCenter NTP Server']




if vcenter_diskformat.lower() == 'thin':
    vcenter_diskformat = 'true'
else:
    vcenter_diskformat = 'false'


# exit maintenance mode and create datastores before deploying
powershell('''
Add-PSSnapin VMware.VimAutomation.Core
Connect-VIServer ''' + vcenter_esx_ip + ''' -User ''' + vcenter_esx_username + ''' -Password ''' + vcenter_esx_password + '''

Get-VMHost | Set-VMHost -State Connected

$VMHost = Get-VMHost
$storMgr = Get-View $VMHost.ExtensionData.ConfigManager.DatastoreSystem

$i = 2
$storMgr.QueryAvailableDisksForVmfs($null) | %{
  New-Datastore -name "'''+vcenter_datastore+'''" -vmfs -path $_.CanonicalName
  #$i = $i+1
  break
}

''')

# extract iso file
subprocess.check_output(
    r'"C:\Program Files\7-Zip\7z.exe" x "' + vcenter_iso + '" -o"c:\deploy\\vcsa" -aoa', shell=True
)

###
#json 6.0.1
###

#json = '''{
#"__version": "1.1",
#"target.vcsa": {
#    "appliance": {
#        "deployment.network": "''' + vcenter_portgroup + '''",
#        "deployment.option": "''' + vcenter_size + '''",
#        "name": "''' + vcenter_vm_name + '''",
#        "thin.disk.mode": ''' + vcenter_diskformat + '''
#    },
#    "esx": {
#        "hostname": "''' + vcenter_esx_ip + '''",
#        "username": "''' + vcenter_esx_username + '''",
#        "password": "''' + vcenter_esx_password + '''",
#        "datastore": "''' + vcenter_datastore + '''"
#    },
#
#    "network": {
#        "hostname": "''' + vcenter_hostname + '''",
#        "dns.servers": [
#            "''' + vcenter_dns1 + '''",
#            "''' + vcenter_dns2 + '''"
#        ],
#        "gateway": "''' + vcenter_gateway + '''",
#        "ip": "''' + vcenter_ip + '''",
#        "ip.family": "ipv4",
#        "mode": "static",
#        "prefix": "''' + vcenter_prefix + '''"
#    },
#    "os": {
#        "password": "''' + vcenter_password + '''",
#        "ssh.enable": true
#    },
#    "sso": {
#        "password": "''' + vcenter_sso_password + '''",
#        "domain-name": "''' + vcenter_sso_domain + '''",
#        "site-name": "''' + vcenter_sso_site + '''"
#    }
#}
#}'''



###
#json 6.0.0
###

json = '''{
    "__comments":
    [
        "QualiSystems deploy script for VCSA 6.0.0"
    ],
 
    "deployment":
    {
        "esx.hostname":"''' + vcenter_esx_ip +'''",
        "esx.datastore":"''' + vcenter_datastore + '''",
        "esx.username":"''' + vcenter_esx_username + '''",
        "esx.password":"''' + vcenter_esx_password + '''",
        "deployment.option":"''' + vcenter_size + '''",
        "deployment.network":"''' + vcenter_portgroup + '''",
        "appliance.name":"''' + vcenter_vm_name + '''",
        "appliance.thin.disk.mode":''' + vcenter_diskformat + '''
    },
 
    "vcsa":
    {
 
        "system":
        {
            "root.password":"''' + vcenter_password + '''",
            "ssh.enable":true,
            "ntp.servers":"''' + vcenter_ntp_server + '''"
        },
 
        "sso":
        {
            "password":"''' + vcenter_sso_password + '''",
            "domain-name":"''' + vcenter_sso_domain + '''",
            "site-name":"''' + vcenter_sso_site + '''"
        },
 
        "networking":
        {
            "ip.family":"ipv4",
            "mode":"static",
            "ip":"''' + vcenter_ip + '''",
            "prefix":"''' + vcenter_prefix + '''",
            "gateway":"''' + vcenter_gateway + '''",
            "dns.servers":"''' + vcenter_dns1 + '''",
            "system.name":"''' + vcenter_hostname + '''"
        }
    }
}'''


with open(r'c:\deploy\vcsaparams.json', 'w') as j:
    j.write(json)


# deploy 
try:
    subprocess.check_output(r'c:\deploy\vcsa\vcsa-cli-installer\win32\vcsa-deploy.exe --no-esx-ssl-verify c:\deploy\vcsaparams.json', shell=True)
except Exception as e:
    print e
    with open(r'c:\ProgramData\QualiSystems\Shells.log', 'a') as f:
        f.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': vcenter deploy error: ' + str(e) + '\r\n')
    sys.exit(1)

