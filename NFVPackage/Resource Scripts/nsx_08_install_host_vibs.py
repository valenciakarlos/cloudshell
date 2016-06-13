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

nsx_datacenter_name = attrs['Datacenter']
compute_cluster_name = attrs['Compute Cluster']
mgmt_cluster_name = attrs['MGMT Cluster']
resource_pool_name = attrs['Controller Cluster']


datacenter_moref, nsx_cluster_moref, compute_cluster_moref, mgmt_cluster_moref = powershell('''
Add-PSSnapin VMware.VimAutomation.Core
Connect-VIServer ''' + vcenter_ip + ''' -User ''' + vcenter_user + ''' -Password ''' + vcenter_password + '''

$a1 = (get-datacenter | where { $_.Name -eq "''' + nsx_datacenter_name + '''" } | get-view).MoRef.Value

$cl = (get-cluster | where { $_.Name -eq "''' + resource_pool_name + '''" })
if(($cl | Measure).Count -eq 0) {
    $cl = (get-resourcepool | where { $_.Name -eq "''' + resource_pool_name + '''" })
}
$a2 = ($cl | get-view).MoRef.Value

$c2 = (get-cluster | where { $_.Name -eq "''' + mgmt_cluster_name + '''" })
if(($c2 | Measure).Count -eq 0) {
    $c2 = (get-resourcepool | where { $_.Name -eq "''' + mgmt_cluster_name + '''" })
}
$a3 = ($c2 | get-view).MoRef.Value

$c3 = (get-cluster | where { $_.Name -eq "''' + compute_cluster_name + '''" })
if(($c3 | Measure).Count -eq 0) {
    $c3 = (get-resourcepool | where { $_.Name -eq "''' + compute_cluster_name + '''" })
}
$a4 = ($c3 | get-view).MoRef.Value

write-host '<%<%', $a1, $a2, $a3, $a4
''').split('<%<%')[1].strip().split(' ')
try:
    for cluster_moref in {nsx_cluster_moref, compute_cluster_moref, mgmt_cluster_moref}:
        test = rest_api_query('''https://''' + nsx_ip + '''/api/2.0/nwfabric/configure''', nsx_user, nsx_password, 'post', '''
        <nwFabricFeatureConfig>
            <resourceConfig>
            <resourceId>''' + cluster_moref + '''</resourceId>
            </resourceConfig>
        </nwFabricFeatureConfig>
        ''')
        with open(r'c:\ProgramData\QualiSystems\Shellss.log', 'a') as f:
            f.write(test)
        try:
            nsx_wait_job(nsx_ip, nsx_user, nsx_password, test)
        except Exception, e:
            print e
        #time.sleep(30)
        try:
            bat('''
            cd ''' + qualiroot() + '''\\eamjava
    
            "C:\\Program Files\\Java\\jre7\\bin\\java.exe" -cp .;eam+vim25-wsdl.jar DisableVum ''' + vcenter_ip + ''' ''' + vcenter_user + ''' ''' + vcenter_password + ''' true
    
            ''')
        
            try:
                rest_api_query('''https://''' + nsx_ip + '''/api/2.0/nwfabric/resolveIssues/''' + cluster_moref, nsx_user, nsx_password, 'post', '')
            except:
                pass
        except:
            pass
    time.sleep(300)
except Exception, e:
    print e

# requests.get('https://' + vcenter_ip + '/eam/mob/', auth={vcenter_user, vcenter_password})

# time.sleep(30)
#
# for _ in range(1, 10):
#     try:
#         rest_api_query('''https://''' + nsx_ip + '''/api/2.0/nwfabric/resolveIssues/''' + cluster_moref, nsx_user, nsx_password, 'post', '')
#     except:
#         pass
#     time.sleep(60)
#     failed_hosts_csv = powershell('''
# Add-PSSnapin VMware.VimAutomation.Core
# Connect-VIServer ''' + vcenter_ip + ''' -User ''' + vcenter_user + ''' -Password ''' + vcenter_password + '''
#
# $cl = (get-cluster | where { $_.Name -eq "''' + resource_pool_name + '''" })
# if(($cl | Measure).Count -eq 0) {
#     $cl = (get-resourcepool | where { $_.Name -eq "''' + resource_pool_name + '''" })
# }
#
# $failed = ''
# foreach($h in ($cl | get-vmhost)) {
#     if((($h | get-esxcli).software.vib.list() | where { $_.Name -eq 'esx-vxlan' } | measure).Count -eq 0) {
#         $failed += $h.Name
#         $failed += ','
#     }
# }
#
# write-host '<%<%', $failed
# ''').split('<%<%')[1].strip()
#     if failed_hosts_csv == '':
#         break
#
