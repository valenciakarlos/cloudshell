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
from NSX_Common import *
from quali_remote import quali_enter, quali_exit, qs_trace, qs_info

quali_enter(__file__)
# with open(r'c:\ProgramData\QualiSystems\Shells.log', 'a') as f:
#     f.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': ' + __file__.split('\\')[-1].replace('.py', '') + ': ' + str(os.environ) + '\r\n')

resource = json.loads(os.environ['RESOURCECONTEXT'])
resource_name = resource['name']
attrs = resource['attributes']

nsx_ip = attrs['NSX IP']
nsx_user = attrs['NSX Username']
nsx_password = attrs['NSX Password']

segment_id = attrs['Segment ID Number']
segment_name = attrs['Segment Name']
begin = attrs['Segment Range Start']
end = attrs['Segment Range End']

rest_api_query('''https://''' + nsx_ip + '''/api/2.0/vdn/config/segments''', nsx_user, nsx_password, 'post', '''
    <segmentRange>
        <id>''' + segment_id + '''</id>
        <name>''' + segment_name + '''</name>
        <begin>''' + begin + '''</begin>
        <end>''' + end + '''</end>
    </segmentRange>
''')

quali_exit(__file__)