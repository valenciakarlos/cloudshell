# service "NSX Manager"

#
# # demo
# import time
# time.sleep(3)
# print 'Executed ' + __file__.split('\\')[-1].replace('.py', '')
# exit()
# # /demo

from NSX_Common import rest_api_query_with_retry
import json
import time
import os

with open(r'c:\ProgramData\QualiSystems\Shells.log', 'a') as f:
    f.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': ' + __file__.split('\\')[-1].replace('.py', '') + ': ' + str(os.environ) + '\r\n')

resource = json.loads(os.environ['RESOURCECONTEXT'])
resource_name = resource['name']
attrs = resource['attributes']

nsx_ip = attrs['NSX IP']
nsx_user = attrs['NSX Username']
nsx_password = attrs['NSX Password']

sso_fqdn = attrs['vCenter IP']
sso_user = attrs['NSX SSO Username']
sso_password = attrs['NSX SSO Password']

if sso_fqdn:
    rest_api_query_with_retry('''https://''' + nsx_ip + '''/api/2.0/services/ssoconfig''', nsx_user, nsx_password, 'post', '''
    <ssoConfig>
        <ssoLookupServiceUrl>https://''' + sso_fqdn + ''':7444/lookupservice/sdk</ssoLookupServiceUrl>
        <ssoAdminUsername>''' + sso_user + '''</ssoAdminUsername>
        <ssoAdminUserpassword>''' + sso_password + '''</ssoAdminUserpassword>
        {0}
    </ssoConfig>
    ''')
