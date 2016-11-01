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
from quali_remote import powershell
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

vcenter_ip = attrs['vCenter IP']
vcenter_user = attrs['vCenter Administrator Username']
vcenter_password = attrs['vCenter Administrator Password']
datacenter_name = attrs['Datacenter']

#NSX Cluster
nsx_cluster = attrs['Controller Cluster']
edge_vds_name = attrs['Edge Distributed vSwitch Name']
edge_vlan = attrs['Edge VLAN']
edge_mtu = attrs['Edge MTU']
edge_ip_pool_name = attrs['Edge IP Pool Name']

#VIO Compute Cluster
compute_cluster_name = attrs['Compute Cluster']
compute_ip_pool_name = attrs['Compute IP Pool Name']
compute_vds_name = attrs['Compute Distributed vSwitch Name']
compute_vlan = attrs['Compute VLAN']
compute_mtu = attrs['Compute MTU']

#VIO MGMT Cluster
mgmt_cluster_name = attrs['MGMT Cluster']
mgmt_ip_pool_name = attrs['MGMT IP Pool Name']
mgmt_vds_name = attrs['MGMT Distributed vSwitch Name']
mgmt_vlan = attrs['MGMT VLAN']
mgmt_mtu = attrs['MGMT MTU']

datacenter_moref, edge_vds_moref, nsx_cluster_moref, compute_vds_moref, compute_cluster_moref, mgmt_vds_moref, mgmt_cluster_moref = powershell('''
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

$a2 = (get-vdswitch | where { $_.Name -eq "''' + edge_vds_name + '''" } | get-view).MoRef.Value
$cl = (get-cluster | where { $_.Name -eq "''' + nsx_cluster + '''" })
if(($cl | Measure).Count -eq 0) {
    $cl = (get-resourcepool | where { $_.Name -eq "''' + nsx_cluster + '''" })
}
$a3 = ($cl | get-view).MoRef.Value

$a4 = (get-vdswitch | where { $_.Name -eq "''' + compute_vds_name + '''" } | get-view).MoRef.Value
$c2 = (get-cluster | where { $_.Name -eq "''' + compute_cluster_name + '''" })
if(($c2 | Measure).Count -eq 0) {
    $c2 = (get-resourcepool | where { $_.Name -eq "''' + compute_cluster_name + '''" })
}
$a5 = ($c2 | get-view).MoRef.Value

$a6 = (get-vdswitch | where { $_.Name -eq "''' + mgmt_vds_name + '''" } | get-view).MoRef.Value
$c3 = (get-cluster | where { $_.Name -eq "''' + mgmt_cluster_name + '''" })
if(($c3 | Measure).Count -eq 0) {
    $c3 = (get-resourcepool | where { $_.Name -eq "''' + mgmt_cluster_name + '''" })
}
$a7 = ($c3 | get-view).MoRef.Value

write-host '<%<%', $a1, $a2, $a3, $a4, $a5, $a6, $a7
''').split('<%<%')[1].strip().split(' ')

# if datacenter_moref:
#     scope = datacenter_moref
# else:
scope = 'globalroot-0'

edge_ip_pool_moref = ''
pools = json.loads(rest_api_query('''https://''' + nsx_ip + '''/api/2.0/services/ipam/pools/scope/''' + scope, nsx_user, nsx_password, 'get', ''))
for p in pools['ipAddressPools']:
    if p['name'].lower() == edge_ip_pool_name.lower():
        edge_ip_pool_moref = p['objectId']
        break
if not edge_ip_pool_moref:
    raise Exception('IP pool named "' + edge_ip_pool_name + '" not found')

nsx_wait_job(nsx_ip, nsx_user, nsx_password, rest_api_query('''https://''' + nsx_ip + '''/api/2.0/nwfabric/configure''', nsx_user, nsx_password, 'post', '''
<nwFabricFeatureConfig>
    <featureId>com.vmware.vshield.vsm.vxlan</featureId>
    <resourceConfig>
        <resourceId>''' + nsx_cluster_moref + '''</resourceId>
        <configSpec class="clusterMappingSpec">
        <switch><objectId>''' + edge_vds_moref + '''</objectId></switch>
        <vlanId>''' + edge_vlan + '''</vlanId>
        <vmknicCount>1</vmknicCount>
        <ipPoolId>''' + edge_ip_pool_moref + '''</ipPoolId>
        </configSpec>
    </resourceConfig>
    <resourceConfig>
        <resourceId>''' + edge_vds_moref + '''</resourceId>
        <configSpec class="vdsContext">
        <switch><objectId>''' + edge_vds_moref + '''</objectId></switch>
        <mtu>''' + edge_mtu + '''</mtu>
        <teaming>FAILOVER_ORDER</teaming>
        </configSpec>
    </resourceConfig>
</nwFabricFeatureConfig>
'''))

compute_ip_pool_moref = ''
pools = json.loads(rest_api_query('''https://''' + nsx_ip + '''/api/2.0/services/ipam/pools/scope/''' + scope, nsx_user, nsx_password, 'get', ''))
for p in pools['ipAddressPools']:
    if p['name'].lower() == compute_ip_pool_name.lower():
        compute_ip_pool_moref = p['objectId']
        break
if not compute_ip_pool_moref:
    raise Exception('IP pool named "' + compute_ip_pool_name + '" not found')

nsx_wait_job(nsx_ip, nsx_user, nsx_password, rest_api_query('''https://''' + nsx_ip + '''/api/2.0/nwfabric/configure''', nsx_user, nsx_password, 'post', '''
<nwFabricFeatureConfig>
    <featureId>com.vmware.vshield.vsm.vxlan</featureId>
    <resourceConfig>
        <resourceId>''' + compute_cluster_moref + '''</resourceId>
        <configSpec class="clusterMappingSpec">
        <switch><objectId>''' + compute_vds_moref + '''</objectId></switch>
        <vlanId>''' + compute_vlan + '''</vlanId>
        <vmknicCount>1</vmknicCount>
        <ipPoolId>''' + compute_ip_pool_moref + '''</ipPoolId>
        </configSpec>
    </resourceConfig>
    <resourceConfig>
        <resourceId>''' + compute_vds_moref + '''</resourceId>
        <configSpec class="vdsContext">
        <switch><objectId>''' + compute_vds_moref + '''</objectId></switch>
        <mtu>''' + compute_mtu + '''</mtu>
        <teaming>FAILOVER_ORDER</teaming>
        </configSpec>
    </resourceConfig>
</nwFabricFeatureConfig>
'''))

mgmt_ip_pool_moref = ''
pools = json.loads(rest_api_query('''https://''' + nsx_ip + '''/api/2.0/services/ipam/pools/scope/''' + scope, nsx_user, nsx_password, 'get', ''))
for p in pools['ipAddressPools']:
    if p['name'].lower() == mgmt_ip_pool_name.lower():
        mgmt_ip_pool_moref = p['objectId']
        break
if not mgmt_ip_pool_moref:
    raise Exception('IP pool named "' + mgmt_ip_pool_name + '" not found')

nsx_wait_job(nsx_ip, nsx_user, nsx_password, rest_api_query('''https://''' + nsx_ip + '''/api/2.0/nwfabric/configure''', nsx_user, nsx_password, 'post', '''
<nwFabricFeatureConfig>
    <featureId>com.vmware.vshield.vsm.vxlan</featureId>
    <resourceConfig>
        <resourceId>''' + mgmt_cluster_moref + '''</resourceId>
        <configSpec class="clusterMappingSpec">
        <switch><objectId>''' + mgmt_vds_moref + '''</objectId></switch>
        <vlanId>''' + mgmt_vlan + '''</vlanId>
        <vmknicCount>1</vmknicCount>
        <ipPoolId>''' + mgmt_ip_pool_moref + '''</ipPoolId>
        </configSpec>
    </resourceConfig>
    <resourceConfig>
        <resourceId>''' + mgmt_vds_moref + '''</resourceId>
        <configSpec class="vdsContext">
        <switch><objectId>''' + mgmt_vds_moref + '''</objectId></switch>
        <mtu>''' + mgmt_mtu + '''</mtu>
        <teaming>FAILOVER_ORDER</teaming>
        </configSpec>
    </resourceConfig>
</nwFabricFeatureConfig>
'''))

quali_exit(__file__)