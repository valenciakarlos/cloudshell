from quali_remote import *
import os
import json
import time
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
wan_local_ip = attrs['Versa Controller SDWAN IP']
ipsec_network = attrs['Versa BGP Client NW']
next_hop = attrs['Versa Controller LAN IP']
branch_ipsec_range = attrs['Versa Branch IPSec Range']
branch_ipsec_netmask = attrs['Versa Branch IPSec Netmask']
prov_mgmt_ike = attrs['Versa Provider MGMT IKE']
tnt_mgmt_ike = attrs['Versa TNT MGMT IKE']
br1_prestaging_ipsec_id = attrs['Versa Branch1 PreStaging IPSec ID']
br2_prestaging_ipsec_id = attrs['Versa Branch2 PreStaging IPSec ID']
provider_prestaging_ipsec_id = attrs['Versa Provider PreStaging IPSec ID']
prestaging_key = attrs['Versa Branch PreStaging IPSec Key']
br1_staging_ipsec_id = attrs['Versa Branch1 Staging IPSec ID']
br2_staging_ipsec_id = attrs['Versa Branch2 Staging IPSec ID']
provider_staging_ipsec_id = attrs['Versa Provider Staging IPSec ID']
staging_key = attrs['Versa Branch Staging IPSec Key']
br1_poststaging_ipsec_id = attrs['Versa Branch1 PostStaging IPSec ID']
br2_poststaging_ipsec_id = attrs['Versa Branch2 PostStaging IPSec ID']
provider_poststaging_ipsec_id = attrs['Versa Provider PostStaging IPSec ID']
poststaging_key = attrs['Versa Branch PostStaging IPSec Key']


# Add Static Route to IPSec
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/nms/routing-options/static''', versa_username, versa_password, 'post', '{"route":{"destination-prefix":"' + ipsec_network + '","next-hop-address":"' + next_hop + '","outgoing-interface":"eth1"}}', is_body_json=True, return_xml=True)
except Exception as e:
    print e

#Staging IPSec Profile
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/device/''' + versa_controller_name + '''/config/orgs/org-services/''' + versa_provider_org + '''/ipsec''', versa_username, versa_password, 'post', '{"vpn-profile":{"name":"Staging-IPSec","vpn-type":"controller-staging-sdwan","tunnel-initiate":"automatic","routing-instance":"Global-VR","tunnel-routing-instance":"Prov-Mgmt-VR","tunnel-interface":"tvi-0/3.0","remote-auth-type":"psk","local-auth-info":{"auth-type":"psk","id-type":"email","key":"' + prestaging_key + '","id-string":"' + provider_prestaging_ipsec_id + '"},"psk-auth-clients":{"remote-client":[{"id-type":"email","remote-id":"' + br1_prestaging_ipsec_id + '","key":"' + prestaging_key + '"},{"id-type":"email","remote-id":"' + br2_prestaging_ipsec_id + '","key":"' + prestaging_key + '"}]},"ipsec":{"life":{"duration":28800}},"ike":{"group":"mod1","lifetime":"28800","dpd-timeout":"30"},"local":{"inet":"' + wan_local_ip + '"},"address-pools":{"address-range":"' + branch_ipsec_range + '","netmask":"' + branch_ipsec_netmask + '","accessible-subnets":[{"subnet":"' + ipsec_network + '"}]}}}', is_body_json=True, return_xml=True)
except Exception as e:
    print e


#Provider IPSec Profile
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/device/''' + versa_controller_name + '''/config/orgs/org-services/''' + versa_provider_org + '''/ipsec''', versa_username, versa_password, 'post', '{"vpn-profile":{"name":"Provider-IPSec","vpn-type":"controller-sdwan","tunnel-initiate":"automatic","routing-instance":"Prov-Mgmt-VR","tunnel-interface":"tvi-0/2.0","remote-auth-type":"psk","local-auth-info":{"auth-type":"psk","id-type":"email","key":"' + staging_key + '","id-string":"' + provider_staging_ipsec_id + '"},"psk-auth-clients":{"remote-client":[{"id-type":"email","remote-id":"' + br1_staging_ipsec_id + '","key":"' + staging_key + '"},{"id-type":"email","remote-id":"' + br2_staging_ipsec_id + '","key":"' + staging_key + '"}]},"ipsec":{"life":{"duration":28800}},"ike":{"group":"mod1","lifetime":"28800","dpd-timeout":"30"},"local":{"inet":"' + prov_mgmt_ike + '"}}}', is_body_json=True, return_xml=True)
except Exception as e:
    print e

#PostStagging IPSec Profile
try:
    rest_api_query('''http://''' + versa_dir_ip + ''':9182/api/config/devices/device/''' + versa_controller_name + '''/config/orgs/org-services/''' + versa_customer_org + '''/ipsec''', versa_username, versa_password, 'post', '{"vpn-profile":{"name":"PostStaging-IPSec","vpn-type":"controller-sdwan","tunnel-initiate":"automatic","routing-instance":"Cust-Mgmt-VR","tunnel-interface":"tvi-0/6.0","remote-auth-type":"psk","local-auth-info":{"auth-type":"psk","id-type":"email","key":"' + poststaging_key + '","id-string":"' + provider_poststaging_ipsec_id + '"},"psk-auth-clients":{"remote-client":[{"id-type":"email","remote-id":"' + br1_poststaging_ipsec_id + '","key":"' + poststaging_key + '"},{"id-type":"email","remote-id":"' + br2_poststaging_ipsec_id + '","key":"' + poststaging_key + '"}]},"ipsec":{"life":{"duration":28800}},"ike":{"group":"mod1","lifetime":"28800","dpd-timeout":"30"},"local":{"inet":"' + tnt_mgmt_ike + '"}}}', is_body_json=True, return_xml=True)
except Exception as e:
    print e

quali_exit(__file__)