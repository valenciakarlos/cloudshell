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
from quali_remote import powershell
with open(r'c:\ProgramData\QualiSystems\Shells.log', 'a') as f:
    f.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': ' + __file__.split('\\')[-1].replace('.py', '') + ': ' + str(os.environ) + '\r\n')


resource = json.loads(os.environ['RESOURCECONTEXT'])
resource_name = resource['name']
attrs = resource['attributes']

nsx_ip = attrs['NSX IP']
nsx_user = attrs['NSX Username']
nsx_password = attrs['NSX Password']

vcenter_ip = attrs['vCenter IP']
vcenter_user = attrs['vCenter Administrator Username']
vcenter_password = attrs['vCenter Administrator Password']


mgmt_ip_pool_name = attrs['MGMT IP Pool Name']
mgmt_ip_pool_netmask_bits = attrs['MGMT IP Pool Netmask Bits']
mgmt_ip_pool_gateway = attrs['MGMT IP Pool Gateway']
mgmt_ip_pool_dns_suffix = attrs['MGMT IP Pool DNS Suffix']
mgmt_ip_pool_dns_server1 = attrs['MGMT IP Pool DNS Server1']
mgmt_ip_pool_dns_server2 = attrs['MGMT IP Pool DNS Server2']
mgmt_ip_pool_start_ip = attrs['MGMT IP Pool Start IP']
mgmt_ip_pool_end_ip = attrs['MGMT IP Pool End IP']

compute_ip_pool_name = attrs['Compute IP Pool Name']
compute_ip_pool_netmask_bits = attrs['Compute IP Pool Netmask Bits']
compute_ip_pool_gateway = attrs['Compute IP Pool Gateway']
compute_ip_pool_dns_suffix = attrs['Compute IP Pool DNS Suffix']
compute_ip_pool_dns_server1 = attrs['Compute IP Pool DNS Server1']
compute_ip_pool_dns_server2 = attrs['Compute IP Pool DNS Server2']
compute_ip_pool_start_ip = attrs['Compute IP Pool Start IP']
compute_ip_pool_end_ip = attrs['Compute IP Pool End IP']

edge_ip_pool_name = attrs['Edge IP Pool Name']
edge_ip_pool_netmask_bits = attrs['Edge IP Pool Netmask Bits']
edge_ip_pool_gateway = attrs['Edge IP Pool Gateway']
edge_ip_pool_dns_suffix = attrs['Edge IP Pool DNS Suffix']
edge_ip_pool_dns_server1 = attrs['Edge IP Pool DNS Server1']
edge_ip_pool_dns_server2 = attrs['Edge IP Pool DNS Server2']
edge_ip_pool_start_ip = attrs['Edge IP Pool Start IP']
edge_ip_pool_end_ip = attrs['Edge IP Pool End IP']

# call twice for controllers and vteps pools

#datacenter_moref = powershell('''
#Add-PSSnapin VMware.VimAutomation.Core
#Connect-VIServer ''' + vcenter_ip + ''' -User ''' + vcenter_user + ''' -Password ''' + vcenter_password + '''
#
#$a1 = (get-datacenter | where { $_.Name -eq "''' + datacenter_name + '''" } | get-view).MoRef.Value
#
#write-host '<%<%', $a1
#''').split('<%<%')[1].strip()


# if datacenter_moref:
#     scope = datacenter_moref
# else:
scope = 'globalroot-0'

controller_ip_pool_moref = rest_api_query('''https://''' + nsx_ip + '''/api/2.0/services/ipam/pools/scope/''' + scope, nsx_user, nsx_password, 'post', '''
<ipamAddressPool>
    <name>''' + mgmt_ip_pool_name + '''</name>
    <prefixLength>''' + mgmt_ip_pool_netmask_bits + '''</prefixLength>
    <gateway>''' + mgmt_ip_pool_gateway + '''</gateway>
    <dnsSuffix>''' + mgmt_ip_pool_dns_suffix + '''</dnsSuffix>
    <dnsServer1>''' + mgmt_ip_pool_dns_server1 + '''</dnsServer1>
    <dnsServer2>''' + mgmt_ip_pool_dns_server2 + '''</dnsServer2>
    <ipRanges>
        <ipRangeDto>
            <startAddress>''' + mgmt_ip_pool_start_ip + '''</startAddress>
            <endAddress>''' + mgmt_ip_pool_end_ip + '''</endAddress>
        </ipRangeDto>
    </ipRanges>
</ipamAddressPool>
''')

compute_ip_pool_moref = rest_api_query('''https://''' + nsx_ip + '''/api/2.0/services/ipam/pools/scope/''' + scope, nsx_user, nsx_password, 'post', '''
<ipamAddressPool>
    <name>''' + compute_ip_pool_name + '''</name>
    <prefixLength>''' + compute_ip_pool_netmask_bits + '''</prefixLength>
    <gateway>''' + compute_ip_pool_gateway + '''</gateway>
    <dnsSuffix>''' + compute_ip_pool_dns_suffix + '''</dnsSuffix>
    <dnsServer1>''' + compute_ip_pool_dns_server1 + '''</dnsServer1>
    <dnsServer2>''' + compute_ip_pool_dns_server2 + '''</dnsServer2>
    <ipRanges>
        <ipRangeDto>
            <startAddress>''' + compute_ip_pool_start_ip + '''</startAddress>
            <endAddress>''' + compute_ip_pool_end_ip + '''</endAddress>
        </ipRangeDto>
    </ipRanges>
</ipamAddressPool>
''')

edge_ip_pool_moref = rest_api_query('''https://''' + nsx_ip + '''/api/2.0/services/ipam/pools/scope/''' + scope, nsx_user, nsx_password, 'post', '''
<ipamAddressPool>
    <name>''' + edge_ip_pool_name + '''</name>
    <prefixLength>''' + edge_ip_pool_netmask_bits + '''</prefixLength>
    <gateway>''' + edge_ip_pool_gateway + '''</gateway>
    <dnsSuffix>''' + edge_ip_pool_dns_suffix + '''</dnsSuffix>
    <dnsServer1>''' + edge_ip_pool_dns_server1 + '''</dnsServer1>
    <dnsServer2>''' + edge_ip_pool_dns_server2 + '''</dnsServer2>
    <ipRanges>
        <ipRangeDto>
            <startAddress>''' + edge_ip_pool_start_ip + '''</startAddress>
            <endAddress>''' + edge_ip_pool_end_ip + '''</endAddress>
        </ipRangeDto>
    </ipRanges>
</ipamAddressPool>
''')
