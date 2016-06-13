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

ent_admin_group = attrs['Enterprise Admin Group']


rest_api_query('''https://''' + nsx_ip + '''/api/2.0/services/usermgmt/role/''' + ent_admin_group + '''?isGroup=true''', nsx_user, nsx_password, 'post', '''
<accessControlEntry>
    <role>enterprise_admin</role>
</accessControlEntry>
''')