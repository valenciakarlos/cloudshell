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
cms_uuid = attrs['Versa CMS UUID']
versa_provider_org = attrs['Versa Provider Name']
versa_customer_org = attrs['Versa Customer Name']
analytics_ip = attrs['Versa Analytics NB IP']
lef_src_ip = attrs['Versa LEF SRC IP']
lef_dst_ip = attrs['Versa LEF DST IP']
analytics_log_port = attrs['Versa Analytics Logs Port']


#Add analytics
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/nms/provider/analytics-connector''', versa_username, versa_password, 'patch', '{"analytics-connector":{"name":"Versa-Analytics","username":"Administrator","password":"versa123","connector-type":"versa-analytics","collector-ipaddress":"' + analytics_ip + '","collector-port":"8080"}}', is_body_json=True, return_xml=True)
except Exception as e:
    print e



#Add Provider template
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/device/''' + versa_controller_name + '''/config/orgs/org-services/''' + versa_provider_org + '''/lef/templates''', versa_username, versa_password, 'post', '<template><name>template-ipfix</name><type>ipfix</type></template>', is_body_json=False, return_xml=True)
except Exception as e:
    print e


#Add Provider collector
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/device/''' + versa_controller_name + '''/config/orgs/org-services/''' + versa_provider_org + '''/lef/collectors''', versa_username, versa_password, 'post', '{"collector":{"name":"Collector1","template":"template-ipfix","transport":"tcp","destination-port":"' + analytics_log_port + '","destination-address":"' + lef_dst_ip + '","source-address":"' + lef_src_ip + '","transmit-rate":"10000","pending-queue-limit":"2048","template-resend-interval":"60","routing-instance":"Prov-Mgmt-VR"}}', is_body_json=True, return_xml=True)
except Exception as e:
    print e


#Add Provider LEF Profile
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/device/''' + versa_controller_name + '''/config/orgs/org-services/''' + versa_provider_org + '''/lef/profiles''', versa_username, versa_password, 'post', '{"profile":{"name":"LEF-Prof1","collector":"Collector1"}}', is_body_json=True, return_xml=True)
except Exception as e:
    print e

#Add Provider Default LEF Profile
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/device/''' + versa_controller_name + '''/config/orgs/org-services/''' + versa_provider_org + '''/lef/default-profile''', versa_username, versa_password, 'put', '{"default-profile":"LEF-Prof1"}', is_body_json=True, return_xml=True)
except Exception as e:
    print e



#####################

#Add Customer template
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/device/''' + versa_controller_name + '''/config/orgs/org-services/''' + versa_customer_org + '''/lef/templates''', versa_username, versa_password, 'post', '<template><name>template-ipfix</name><type>ipfix</type></template>', is_body_json=False, return_xml=True)
except Exception as e:
    print e


#Add Customer collector
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/device/''' + versa_controller_name + '''/config/orgs/org-services/''' + versa_customer_org + '''/lef/collectors''', versa_username, versa_password, 'post', '{"collector":{"name":"Collector1","template":"template-ipfix","transport":"tcp","destination-port":"' + analytics_log_port + '","destination-address":"' + lef_dst_ip +'","source-address":"' + lef_src_ip + '","transmit-rate":"10000","pending-queue-limit":"2048","template-resend-interval":"60","routing-instance":"Prov-Mgmt-VR"}}', is_body_json=True, return_xml=True)
except Exception as e:
    print e


#Add Customer LEF Profile
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/device/''' + versa_controller_name + '''/config/orgs/org-services/''' + versa_customer_org + '''/lef/profiles''', versa_username, versa_password, 'post', '{"profile":{"name":"LEF-Prof1","collector":"Collector1"}}', is_body_json=True, return_xml=True)
except Exception as e:
    print e

#Add Customer Default LEF Profile
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/device/''' + versa_controller_name + '''/config/orgs/org-services/''' + versa_customer_org + '''/lef/default-profile''', versa_username, versa_password, 'put', '{"default-profile":"LEF-Prof1"}', is_body_json=True, return_xml=True)
except Exception as e:
    print e


quali_exit(__file__)