# service "NSX Manager"

# # demo
# import time
# time.sleep(3)
# print 'Executed ' + __file__.split('\\')[-1].replace('.py', '')
# exit()
# # /demo


import os
import json
import time
import sys
from vCenterCommon import deployVM

with open(r'c:\ProgramData\QualiSystems\Shells.log', 'a') as f:
    f.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': ' + __file__.split('\\')[-1].replace('.py', '') + ': ' + str(os.environ) + '\r\n')

resource = json.loads(os.environ['RESOURCECONTEXT'])
resource_name = resource['name']
attrs = resource['attributes']

datastore = attrs['vRA Datastore']
thick_thin = attrs['vRA Disk Format']
root_password = attrs['vRA Root Password']
hostname = attrs['vRA Hostname']
gateway = attrs['vRA Gateway IP']
netmask = attrs['vRA Netmask']
domain = attrs['vRA Domain']
searchpath = attrs['vRA DNS Search Path']
dns = attrs['vRA DNS Server IP']
ip = attrs['vRA IP']
portgroup = attrs['vRA Portgroup Name']
name = attrs['vRA VM Name']
ova_path = attrs['Local vRA OVA Path']

vcenter_user = attrs['vCenter Administrator Username']
vcenter_password = attrs['vCenter Administrator Password']
vcenter_ip = attrs['vCenter IP']
datacenter = attrs['Datacenter']
cluster = attrs['Cluster']

try:
    command = ' '.join([
        '--machineOutput',
        '--noSSLVerify',
        '--allowExtraConfig',
        '--powerOn',
        '--acceptAllEulas',
        '--datastore="' + datastore + '"',
        '--diskMode=' + thick_thin,
        '--prop:varoot-password="' + root_password + '"',
        '--prop:va-ssh-enabled=True',
        '--prop:vami.hostname=' + hostname,
        '--prop:vami.gateway=' + gateway,
        '--prop:vami.domain=' + domain,
        '--prop:vami.searchpath=' + searchpath,
        '--prop:vami.DNS=' + dns,
        '--prop:vami.ip0=' + ip,
        '--prop:vami.netmask0=" ' + netmask + '"',
        '"--net:Network 1=' + portgroup + '"',
        '--name="' + name + '"',
        '"' + ova_path + '"',
        '"vi://''' + vcenter_user.replace('@', '%40') + ''':''' + '"' + vcenter_password + '"' + '''@''' + vcenter_ip + '''/''' + datacenter + '''/host/''' + cluster + '/Resources"'
    ])
    deployVM(command, name, vcenter_ip, vcenter_user, vcenter_password, False)
except Exception as e:
    print '\r\n' + str(e)
    sys.exit(1)
