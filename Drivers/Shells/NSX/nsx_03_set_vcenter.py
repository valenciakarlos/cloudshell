# service "NSX Manager"

#
# # demo
# import time
# time.sleep(3)
# print 'Executed ' + __file__.split('\\')[-1].replace('.py', '')
# exit()
# # /demo

from quali_remote import *
import os
import json
import time
from NSX_Common import *
with open(r'c:\ProgramData\QualiSystems\Shells.log', 'a') as f:
    f.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': ' + __file__.split('\\')[-1].replace('.py', '') + ': ' + str(os.environ) + '\r\n')

resource = json.loads(os.environ['RESOURCECONTEXT'])
resource_name = resource['name']
attrs = resource['attributes']

nsx_ip = attrs['NSX IP']
nsx_user = attrs['NSX Username']
nsx_password = attrs['NSX Password']

vcenter_ip = attrs['vCenter IP']
vcenter_upn = attrs['vCenter Administrator Username']
vcenter_password = attrs['vCenter Administrator Password']


rest_api_query_with_retry('''https://''' + nsx_ip + '''/api/2.0/services/vcconfig''', nsx_user, nsx_password, 'put', '''
<vcInfo>
    <ipAddress>''' + vcenter_ip + '''</ipAddress>
    <userName>''' + vcenter_upn + '''</userName>
    <password>''' + vcenter_password + '''</password>
    {0}
    <assignRoleToUser>true</assignRoleToUser>
    <pluginDownloadServer></pluginDownloadServer>
    <pluginDownloadPort></pluginDownloadPort>
</vcInfo>
''')