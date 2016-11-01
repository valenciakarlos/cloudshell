from quali_remote import *
import os
import json
import time
from xml.dom.minidom import parseString

from quali_remote import quali_enter, quali_exit, qs_trace, qs_info

quali_enter(__file__)

resource = json.loads(os.environ['RESOURCECONTEXT'])
resource_name = resource['name']
attrs = resource['attributes']

versa_dir_ip = attrs['Versa Director NB IP']
versa_username = attrs['Versa Username']
versa_password = attrs['Versa Password']
versa_controller_name = attrs['Versa Controller Name']
versa_provider_org = attrs['Versa Provider Name']
versa_customer_org = attrs['Versa Customer Name']
dg_email = attrs['Versa DeviceGroup Email']
dg_phone = attrs['Versa DeviceGroup Phone']
br1_name = attrs['Versa Branch1 VM Name']
br2_name = attrs['Versa Branch2 VM Name']
br1_chas = attrs['Versa Branch1 Serial']
br2_chas = attrs['Versa Branch2 Serial']


#Add Branch1 to Inventory
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/nms/assets''', versa_username, versa_password, 'post', '{"asset":{"serial-no":"' + br1_chas + '","name":"' + br1_name + '","status":"shipped","organization":"' + versa_customer_org + '"}}', is_body_json=True, return_xml=True)
except Exception as e:
    print e


#Add Branch2 to Inventory
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/nms/assets''', versa_username, versa_password, 'post', '{"asset":{"serial-no":"' + br2_chas + '","name":"' + br2_name + '","status":"shipped","organization":"' + versa_customer_org + '"}}', is_body_json=True, return_xml=True)
except Exception as e:
    print e


#Add Device Group
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices''', versa_username, versa_password, 'post', '{"device-group":{"name":"Cust-Branches","dg:organization":"' + versa_customer_org + '","dg:e-mail":"' + dg_email + '","dg:phone":"' + dg_phone + '","dg:serial-number":["' + br1_chas + '","' + br2_chas + '"]}}', is_body_json=True, return_xml=True)
except Exception as e:
    print e


#Add Stagging Template #1
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/vnms/template''', versa_username, versa_password, 'post', '{"versanms.templateData":{"name":"Branches-Staging","templateType":"sdwan-staging","device-group":["Cust-Branches"],"providerTenant":"' + versa_provider_org + '"}}', is_body_json=True, return_xml=True)
except Exception as e:
    print e


#Add Stagging Template #2
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/nms/devicegroup-template-mapping/Branches-Staging''', versa_username, versa_password, 'put', '{"devicegroup-template-mapping":{"template":"Branches-Staging","device-group":["Cust-Branches"]}}', is_body_json=True, return_xml=True)
except Exception as e:
    print e


#Add Stagging Template #3
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/vnms/template/organizations''', versa_username, versa_password, 'post', '{"versanms.templates":{"template":[{"name":"Branches-Staging"}]}}', is_body_json=True, return_xml=True)
except Exception as e:
    print e


#Add PostStagging Template #1
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/vnms/template''', versa_username, versa_password, 'post', '{"versanms.templateData":{"name":"Branches-PostStaging","templateType":"sdwan-post-staging","organization":["' + versa_customer_org + '"],"device-group":["Cust-Branches"],"providerTenant":"' + versa_provider_org + '"}}', is_body_json=True, return_xml=True)
except Exception as e:
    print e


#Add PostStagging Template #2
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/nms/devicegroup-template-mapping/Branches-PostStaging''', versa_username, versa_password, 'put', '{"devicegroup-template-mapping":{"template":"Branches-PostStaging","device-group":["Cust-Branches"]}}', is_body_json=True, return_xml=True)
except Exception as e:
    print e


#Add PostStagging Template #3
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/vnms/template/organizations''', versa_username, versa_password, 'post', '{"versanms.templates":{"template":[{"name":"Branches-PostStaging"},{"name":"Branches-Staging"}]}}', is_body_json=True, return_xml=True)
except Exception as e:
    print e


quali_exit(__file__)