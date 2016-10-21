from quali_remote import *
from uuid import uuid4
import os
import time
import json


with open(r'c:\ProgramData\QualiSystems\Shells.log', 'a') as f:
    f.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': ' + __file__.split('\\')[-1].replace('.py', '') + ': ' + str(os.environ) + '\r\n')


resource = json.loads(os.environ['RESOURCECONTEXT'])
resource_name = resource['name']
attrs = resource['attributes']

versa_dir_ip = attrs['Versa Director NB IP']
versa_username = attrs['Versa Username']
versa_password = attrs['Versa Password']
cms_uuid = attrs['Versa CMS UUID']
versa_provider_org = attrs['Versa Provider Name']
versa_customer_org = attrs['Versa Customer Name']

customer_uuid = uuid4()
provider_uuid = uuid4()

# STEPS # Use separate try-catch for each creation
try:
    #Create Provider Org
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/nms/provider/organizations''', versa_username, versa_password, 'post', '''<organization><uuid>''' + str(provider_uuid) + '''</uuid><name>''' + versa_provider_org + '''</name><parent-org>none</parent-org><subscription-plan>Default-All-Services-Plan</subscription-plan><cms-orgs><uuid>''' + cms_uuid + '''</uuid><name>SDWAN-CMS-ORG</name><cms-connector>local</cms-connector></cms-orgs></organization>''')
    #Create Customer Org
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/nms/provider/organizations''', versa_username, versa_password, 'post', '''<organization><uuid>''' + str(customer_uuid) + '''</uuid><name>''' + versa_customer_org + '''</name><parent-org>''' + versa_provider_org + '''</parent-org><subscription-plan>Default-All-Services-Plan</subscription-plan><cms-orgs><uuid>''' + cms_uuid + '''</uuid><name>SDWAN-CMS-ORG</name><cms-connector>local</cms-connector></cms-orgs></organization>''')

except Exception as e:
    print e