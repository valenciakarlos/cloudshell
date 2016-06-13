# service "NSX Manager"

#
# # demo
# import time
# time.sleep(3)
# print 'Executed ' + __file__.split('\\')[-1].replace('.py', '')
# exit()
# # /demo

from quali_remote import *
from NSX_Common import *
import os
import json
import time
with open(r'c:\ProgramData\QualiSystems\Shells.log', 'a') as f:
    f.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': ' + __file__.split('\\')[-1].replace('.py', '') + ': ' + str(os.environ) + '\r\n')

resource = json.loads(os.environ['RESOURCECONTEXT'])
resource_name = resource['name']
attrs = resource['attributes']

nsx_ip = attrs['NSX IP']
nsx_user = attrs['NSX Username']
nsx_password = attrs['NSX Password']

transport_zone_name = attrs['Transport Zone Name']
name = attrs['Logical Switch Name']
description = attrs['Logical Switch Description']

transport_zone_id = ''
j = json.loads(rest_api_query('''https://''' + nsx_ip + '''/api/2.0/vdn/scopes''', nsx_user, nsx_password, 'get', ''))
for s in j['allScopes']:
    if s['name'] == transport_zone_name:
        transport_zone_id = s['objectId']
        break

if not transport_zone_id:
    raise Exception('Transport zone "'+transport_zone_name+'" not found')

rest_api_query('''https://''' + nsx_ip + '''/api/2.0/vdn/scopes/''' + transport_zone_id + '''/virtualwires''', nsx_user, nsx_password, 'post', '''
<virtualWireCreateSpec>
	<name>''' + name + '''</name>
	<description>''' + description + '''</description>
	<tenantId>virtual wire tenant</tenantId>
	<guestVlanAllowed>true</guestVlanAllowed>
</virtualWireCreateSpec>
''')