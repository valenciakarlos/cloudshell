from quali_remote import *
import time
import paramiko
import re
import json
import os

with open(r'c:\ProgramData\QualiSystems\Shells.log', 'a') as f:
    f.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': ' + __file__.split('\\')[-1].replace('.py', '') + ': ' + str(os.environ) + '\r\n')


resource = json.loads(os.environ['RESOURCECONTEXT'])
resource_name = resource['name']
attrs = resource['attributes']

provider_name = attrs['Versa Provider Name']
br1_name = attrs['Versa Branch1 VM Name']
br2_name = attrs['Versa Branch2 VM Name']
br1_ip = attrs['Versa Branch1 NB IP']
br2_ip = attrs['Versa Branch2 NB IP']
br1_sdwan_ip = attrs['Versa Branch1 SDWAN IP']
br1_sdwan_subnet = attrs['Versa Branch1 SDWAN Subnet']
br2_sdwan_ip = attrs['Versa Branch2 SDWAN IP']
br2_sdwan_subnet = attrs['Versa Branch2 SDWAN Subnet']
br1_chas = attrs['Versa Branch1 Serial']
br2_chas = attrs['Versa Branch2 Serial']
site_name = 'Controller'
controller_sb_gw = attrs['Versa Controller SDWAN IP']
ipsec_key = attrs['Versa Branch PreStaging IPSec Key']
br1_ipsec_id = attrs['Versa Branch1 PreStaging IPSec ID']
br2_ipsec_id = attrs['Versa Branch2 PreStaging IPSec ID']
provider_ipsec_id = attrs['Versa Provider PreStaging IPSec ID']


def do_command(ssh1, command):
    if command:
        g = open(r'c:\ProgramData\QualiSystems\Shells.log', 'a')
        g.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': ssh : ' + command + '\r\n')
        g.close()
        stdin, stdout, stderr = ssh1.exec_command(command)
        stdin.close()
        a = []
        for line in stdout.read().splitlines():
            a.append(line + '\n')
        for line in stderr.read().splitlines():
            a.append(line + '\n')
        rv = '\n'.join(a)
        g = open(r'c:\ProgramData\QualiSystems\Shells.log', 'a')
        g.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': ssh result: ' + rv + '\r\n')
        g.close()
        return rv

def do_command_and_wait(chan, command, expect):
    g = open(r'c:\ProgramData\QualiSystems\Shells.log', 'a')
    g.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': ssh : ' + command + ' : wait for : ' + expect + '\r\n')
    g.close()
    # Ssh and wait for the password prompt.
    chan.send(command + '\n')

    buff = ''
    #while buff.find(expect) < 0:
    while not re.search(expect, buff, 0):
        resp = chan.recv(9999)
        buff += resp
        print resp
    g = open(r'c:\ProgramData\QualiSystems\Shells.log', 'a')
    g.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': replay : ' + buff + ' : wait for : ' + expect + '\r\n')
    time.sleep(1)
    return buff



def setCommand(br_name, sdwan_ip, sdwan_subnet, prov_name, br_serial, cont_gw, ip_key, ip_id, prov_id, site='Controller'):
    script = '''cli
conf
set interfaces vni-0/0 unit 0 family inet address ''' + sdwan_ip + sdwan_subnet + '''
set interfaces tvi-0/3 type ipsec
set interfaces tvi-0/3 unit 0 family
set networks WAN-Network-1 interfaces [ vni-0/0.0 ]
set orgs org ''' + prov_name + ''' type exclusive
set orgs org ''' + prov_name + ''' available-routing-instances [ grt-vrf mgmt ]
set orgs org ''' + prov_name + ''' traffic-identification using [ tvi-0/3.0 ]
set orgs org ''' + prov_name + ''' traffic-identification using-networks [ WAN-Network-1 ]
set orgs org ''' + prov_name + ''' available-service-node-groups [ default-sng ]
set orgs org ''' + prov_name + ''' sd-wan site
set orgs org ''' + prov_name + ''' sd-wan site site-type branch-prestaging
set orgs org ''' + prov_name + ''' sd-wan site global-tenant-id 1
set orgs org ''' + prov_name + ''' sd-wan site site-name ''' + br_name + '''
set orgs org ''' + prov_name + ''' sd-wan site chassis-id ''' + br_serial + '''
set orgs org ''' + prov_name + ''' sd-wan site site-type branch-prestaging
set orgs org ''' + prov_name + ''' sd-wan site management-routing-instance mgmt
set orgs org ''' + prov_name + ''' sd-wan site wan-interfaces vni-0/0.0 circuit-name internet1
set orgs org ''' + prov_name + ''' sd-wan controllers controller1 site-name ''' + site + '''
set orgs org ''' + prov_name + ''' sd-wan controllers controller1 site-id 1
set orgs org ''' + prov_name + ''' sd-wan controllers controller1 transport-addresses addr1 ip-address ''' + cont_gw + '''
set orgs org ''' + prov_name + ''' sd-wan controllers controller1 transport-addresses addr1 routing-instance grt-vrf
set orgs org-services ''' + prov_name + ''' ipsec vpn-profile branch vpn-type branch-prestaging-sdwan
set orgs org-services ''' + prov_name + ''' ipsec vpn-profile branch local-auth-info
set orgs org-services ''' + prov_name + ''' ipsec vpn-profile branch local-auth-info auth-type psk
set orgs org-services ''' + prov_name + ''' ipsec vpn-profile branch local-auth-info id-type email
set orgs org-services ''' + prov_name + ''' ipsec vpn-profile branch local-auth-info key ''' + ip_key + '''
set orgs org-services ''' + prov_name + ''' ipsec vpn-profile branch local-auth-info id-string ''' + ip_id + '''
set orgs org-services ''' + prov_name + ''' ipsec vpn-profile branch local
set orgs org-services ''' + prov_name + ''' ipsec vpn-profile branch local inet ''' + sdwan_ip + '''
set orgs org-services ''' + prov_name + ''' ipsec vpn-profile branch routing-instance grt-vrf
set orgs org-services ''' + prov_name + ''' ipsec vpn-profile branch tunnel-routing-instance mgmt
set orgs org-services ''' + prov_name + ''' ipsec vpn-profile branch tunnel-initiate automatic
set orgs org-services ''' + prov_name + ''' ipsec vpn-profile branch ipsec life duration 25000
set orgs org-services ''' + prov_name + ''' ipsec vpn-profile branch ike group mod1
set orgs org-services ''' + prov_name + ''' ipsec vpn-profile branch ike lifetime 27000
set orgs org-services ''' + prov_name + ''' ipsec vpn-profile branch ike dpd-timeout 10
set orgs org-services ''' + prov_name + ''' ipsec vpn-profile branch peer-auth-info
set orgs org-services ''' + prov_name + ''' ipsec vpn-profile branch peer-auth-info auth-type psk
set orgs org-services ''' + prov_name + ''' ipsec vpn-profile branch peer-auth-info id-type email
set orgs org-services ''' + prov_name + ''' ipsec vpn-profile branch peer-auth-info key ''' + ip_key + '''
set orgs org-services ''' + prov_name + ''' ipsec vpn-profile branch peer-auth-info id-string ''' + prov_id + '''
set orgs org-services ''' + prov_name + ''' ipsec vpn-profile branch peer
set orgs org-services ''' + prov_name + ''' ipsec vpn-profile branch peer inet ''' + cont_gw + '''
set orgs org-services ''' + prov_name + ''' ipsec vpn-profile branch tunnel-interface tvi-0/3.0
set routing-instances grt-vrf instance-type virtual-router
set routing-instances grt-vrf networks [ WAN-Network-1 ]
set routing-instances grt-vrf routing-options static route 0.0.0.0/0 ''' + cont_gw + ''' none
set routing-instances mgmt instance-type virtual-router
set routing-instances mgmt interfaces [ tvi-0/3.0 ]
set service-node-groups default-sng id 0
set service-node-groups default-sng type internal
set service-node-groups default-sng services [ ipsec sdwan ]
set system vnf-manager vnf-mgmt-interfaces [ tvi-0/3.0 ]
set system identification name ''' + br_name + '''
set system services ssh enabled
commit

'''
    return script

#get script
br1 = setCommand(br1_name, br1_sdwan_ip, br1_sdwan_subnet, provider_name, br1_chas, controller_sb_gw, ipsec_key, br1_ipsec_id, provider_ipsec_id)
br2 = setCommand(br2_name, br2_sdwan_ip, br2_sdwan_subnet, provider_name, br2_chas, controller_sb_gw, ipsec_key, br2_ipsec_id, provider_ipsec_id)

#do Branch1
br1ssh = paramiko.SSHClient()
br1ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy()) #allow auto-accepting new hosts
br1ssh.connect(br1_ip, username='admin', password='versa123')
br1chan = br1ssh.invoke_shell()
for s in br1.splitlines():
    do_command_and_wait(br1chan, s, expect=r' ')

#do Branch2
br2ssh = paramiko.SSHClient()
br2ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy()) #allow auto-accepting new hosts
br2ssh.connect(br2_ip, username='admin', password='versa123')
br2chan = br2ssh.invoke_shell()
for s in br2.splitlines():
    do_command_and_wait(br2chan, s, expect=r' ')