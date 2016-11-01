# service "NSX Controller"

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
from quali_remote import powershell
from NSX_Common import *
from quali_remote import quali_enter, quali_exit

quali_enter(__file__)
# with open(r'c:\ProgramData\QualiSystems\Shells.log', 'a') as f:
#     f.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': ' + __file__.split('\\')[-1].replace('.py', '') + ': ' + str(os.environ) + '\r\n')


resource = json.loads(os.environ['RESOURCECONTEXT'])
resource_name = resource['name']
attrs = resource['attributes']

nsx_ip = attrs['NSX IP']
nsx_user = attrs['NSX Username']
nsx_password = attrs['NSX Password']

vcenter_ip = attrs['vCenter IP']
vcenter_user = attrs['vCenter Administrator Username']
vcenter_password = attrs['vCenter Administrator Password']

nsx_controllers_ip_pool_name = attrs['MGMT IP Pool Name']

controller_name = attrs['Controller Name']
description = attrs['Controller Description']
datacenter_name = attrs['Datacenter']
resource_pool_name = attrs['Controller Cluster']
datastore_name = attrs['Controller Datastore']
deployment_size_small_medium_large = attrs['Deployment Size']
portgroup_name = attrs['Controller Portgroup Name']
new_controller_admin_password = attrs['Controller Admin Password']

datacenter_moref, resource_pool_moref, datastore_moref, portgroup_moref = powershell('''
Add-PSSnapin VMware.VimAutomation.Core -ErrorAction SilentlyContinue
Try {
    import-module VMware.VimAutomation.VDS -ErrorAction SilentlyContinue
}
Catch {
}
try {
	Add-PSSnapin VMware.VimAutomation.VDS -ErrorAction SilentlyContinue
}
catch {
}
Connect-VIServer ''' + vcenter_ip + ''' -User ''' + vcenter_user + ''' -Password ''' + vcenter_password + '''

$a1 = (get-datacenter | where { $_.Name -eq "''' + datacenter_name + '''" } | get-view).MoRef.Value

$cl = (get-cluster | where { $_.Name -eq "''' + resource_pool_name + '''" })
if(($cl | Measure).Count -eq 0) {
    $cl = (get-resourcepool | where { $_.Name -eq "''' + resource_pool_name + '''" })
}
$a2 = ($cl | get-view).MoRef.Value

$a3 = (get-datastore | where { $_.Name -eq "''' + datastore_name + '''" } | get-view).MoRef.Value
$a4 = (Get-VDPortgroup | where { $_.Name -eq "''' + portgroup_name + '''" } | get-view).MoRef.Value

write-host '<%<%', $a1, $a2, $a3, $a4
''').split('<%<%')[1].strip().split(' ')

# if datacenter_moref:
# scope = datacenter_moref
# else:
scope = 'globalroot-0'

ip_pool_moref = ''
o = rest_api_query('''https://''' + nsx_ip + '''/api/2.0/services/ipam/pools/scope/''' + scope, nsx_user, nsx_password, 'get', '')
pools = json.loads(o)
f = open(r'c:\ProgramData\QualiSystems\Shells.log', 'a')
f.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': ' + __file__.split('\\')[-1].replace('.py', '') + ': o=' + str(o) + 'pools=' + str(pools) + '\r\n')
f.close()

for p in pools['ipAddressPools']:
    if p['name'].lower() == nsx_controllers_ip_pool_name.lower():
        ip_pool_moref = p['objectId']
        break
if not ip_pool_moref:
    raise Exception('IP pool named "' + nsx_controllers_ip_pool_name + '" not found')

# STEPS # Query for existing controller and quit if found

jobid = rest_api_query('''https://''' + nsx_ip + '''/api/2.0/vdn/controller''', nsx_user, nsx_password, 'post', '''
<controllerSpec>
    <name>''' + controller_name + '''</name>
    <description>''' + description + '''</description>
    <ipPoolId>''' + ip_pool_moref + '''</ipPoolId>
    <resourcePoolId>''' + resource_pool_moref + '''</resourcePoolId>
    <datastoreId>''' + datastore_moref + '''</datastoreId>
    <deployType>''' + deployment_size_small_medium_large + '''</deployType>
    <networkId>''' + portgroup_moref + '''</networkId>
    <password>''' + new_controller_admin_password + '''</password>
</controllerSpec>
''')

jobid = jobid.strip()
time.sleep(30)
#time.sleep(600)
nsx_wait_job(nsx_ip, nsx_user, nsx_password, jobid)

quali_exit(__file__)