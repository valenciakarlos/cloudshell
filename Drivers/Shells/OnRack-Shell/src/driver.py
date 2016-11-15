import json
from quali_remote import qs_trace, qs_info
from time import sleep, time

import paramiko
import requests
import subprocess
from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.shell.core.driver_context import InitCommandContext, ResourceCommandContext, AutoLoadResource, \
    AutoLoadDetails, AutoLoadCommandContext
import cloudshell.api.cloudshell_api
from cloudshell.api.cloudshell_api import ResourceInfoDto, ResourceAttributesUpdateRequest, AttributeNameValue, PhysicalConnectionUpdateRequest


def ssh(host, user, password, command, context):
    qs_trace('ssh ' + host + ': ' + command, context)
    sshcl = paramiko.SSHClient()
    sshcl.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    sshcl.connect(host, username=user, password=password)
    stdin, stdout, stderr = sshcl.exec_command(command)
    stdin.close()
    a = []
    for line in stdout.read().splitlines():
        a.append(line + '\n')
    for line in stderr.read().splitlines():
        a.append(line + '\n')
    rv = '\n'.join(a)
    qs_trace('ssh result: ' + rv, context)
    return rv


def rest_json(method, url, bodydict, token, context):
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }
    if token:
        headers['Authentication-Token'] = token
    qs_trace('url=%s method=%s bodydict=%s token=%s' % (url, method, str(bodydict), str(token)), context)
    o = requests.request(method.upper(), url, data=(json.dumps(bodydict) if bodydict else None), headers=headers, verify=False)
    qs_trace('result=%s' % (str(o.text)), context)
    if o.status_code >= 400:
        raise Exception('REST query failed: %d %s: %s' % (o.status_code, str(o), str(o.text)))
    return json.loads(o.text)


class OnrackShellDriver (ResourceDriverInterface):
    
    def cleanup(self):
        """
        Destroy the driver session, this function is called everytime a driver instance is destroyed
        This is a good place to close any open sessions, finish writing to log files
        """
        pass

    def __init__(self):
        """
        ctor must be without arguments, it is created with reflection at run time
        """
        pass

    def initialize(self, context):
        """
        Initialize the driver session, this function is called everytime a new instance of the driver is created
        This is a good place to load and cache the driver configuration, initiate sessions etc.
        :param InitCommandContext context: the context the command runs on
        """
        pass

    #remote command
    def cancel_os_deployment(self, context, ports):
        """
        A simple example function
        :param ResourceCommandContext context: the context the command runs on
        """

        csapi = cloudshell.api.cloudshell_api.CloudShellAPISession(context.connectivity.server_address,
                                                                   port=context.connectivity.cloudshell_api_port,
                                                                   token_id=context.connectivity.admin_auth_token)
        onrack_ip = context.resource.address
        onrack_username = context.resource.attributes['User']
        onrack_password = csapi.DecryptPassword(context.resource.attributes['Password']).Value

        onrack_res_id = ports[0].split('/')[-1]

        token = rest_json('post', 'https://' + onrack_ip + '/login',
                          {'email': onrack_username, 'password': onrack_password},
                          '', context)['response']['user']['authentication_token']
        rest_json('delete', 'http://' + onrack_ip + ':8080/api/common/nodes/' + onrack_res_id + '/workflows/active', None, token, context)

    #remote command
    def deploy_os(self, context, ports, os_type):
        """
        A simple example function
        :param ResourceCommandContext context: the context the command runs on
        """

        # return 'xxx:' + str(context) + str(ports)
        #
        csapi = cloudshell.api.cloudshell_api.CloudShellAPISession(context.connectivity.server_address,
                                                                   port=context.connectivity.cloudshell_api_port,
                                                                   token_id=context.connectivity.admin_auth_token)

        # onrack = ['/'.join(r.Name.split('/')[0:-1]) for r in csapi.GetResourceDetails(context.resource.fullname).ChildResources if r.Name.endswith('/OnRack')][0]
        # od = csapi.GetResourceDetails(onrack)
        # onrack_ip = od.Address
        # onrack_username = [a.Value for a in od.ResourceAttributes if a.Name == 'OnRack Username'][0]
        # # onrack_password = csapi.DecryptPassword([a.Value for a in od.ResourceAttributes if a.Name == 'OnRack Password'][0]).Value
        # onrack_password = [a.Value for a in od.ResourceAttributes if a.Name == 'OnRack Password'][0]
        onrack_ip = context.resource.address
        # onrack_username = context.resource.attributes['OnRack Username']
        # onrack_password = context.resource.attributes['OnRack Password']
        onrack_username = context.resource.attributes['User']
        onrack_password = csapi.DecryptPassword(context.resource.attributes['Password']).Value


        # csapi.GetResourceDetails(context.resource.fullname).
        # onrack = ['/'.join(r.Name.split('/')[0:-1]) for r in csapi.GetResourceDetails(context.resource.fullname).ChildResources if r.Name.endswith('/OnRack')][0]
        onrack_res_id = ports[0].split('/')[-1]

        server_attrs = {}
        for r in csapi.GetResourceDetails(context.resource.fullname).ChildResources:
            if r.Address == onrack_res_id or r.Address.endswith('/' + onrack_res_id):
                server_resource_name = '/'.join(r.Connections[0].FullPath.split('/')[0:-1])
                d = csapi.GetResourceDetails(server_resource_name)

                for a in d.ResourceAttributes:
                    server_attrs[a.Name] = a.Value
                server_attrs['ResourceAddress'] = d.Address
                server_attrs['ResourceName'] = d.Name

        vcenter_attrs = {}
        for s in csapi.GetReservationDetails(context.remote_reservation.reservation_id).ReservationDescription.Services:
            if 'vCenter' in s.ServiceName:
                for a in s.Attributes:
                    vcenter_attrs[a.Name] = a.Value

        if len(vcenter_attrs) == 0:
            raise Exception('vCenter service not found in reservation')

        if server_attrs['Requires OS Deployment'].lower() in ['false', 'no']:
            qs_info('Skipping deployment for %s. To force redeploy, set Requires OS Deployment attribute to True on resource %s' % (server_attrs['ResourceName'], server_attrs['ResourceName']), context)
            return

        csapi.SetResourceLiveStatus(server_attrs['ResourceName'], 'Offline', '')
        # csapi.WriteMessageToReservationOutput(resid, 'Installing %s on %s...' % (os_type, attrs['ResourceName']))
        nic10 = vcenter_attrs['VDS1 Hosts VNICS']
        if not nic10:
            raise Exception('Attribute "VDS1 Hosts VNICS" was not set on vCenter service')
        if ',' in nic10:
            raise Exception('Only a single NIC is supported for attribute "VDS1 Hosts VNICS" on vCenter service - got "%s"' % nic10)

        nic172 = vcenter_attrs['PXE VNIC']
        if not nic172:
            raise Exception('Attribute "PXE VNIC" was not set on vCenter service')

        ip172 = server_attrs['ESX PXE Network IP']

        # token = rest_json('post', 'https://' + onrack_ip + '/login',
        #                   {'email': onrack_username, 'password': onrack_password},
        #                   '', context)['response']['user']['authentication_token']
        # ipmi_ip = rest_json('get', 'https://' + onrack_ip + '/redfish/v1/Systems/' + onrack_res_id, None, token, context)['Oem']['EMC']['VisionID_Ip']
        # needfix = False
        # bootseq = ssh(ipmi_ip, 'root', 'calvin', 'racadm get BIOS.BiosBootSettings.BootSeq', context)
        # bootseq = bootseq.split('BootSeq=')[1].split('\n')[0].strip()
        # got_nic = False
        # # needfix = False
        # for b in bootseq.split(','):
        #     if 'NIC' in b and 'Integrated' in b:
        #         got_nic = True
        #     if 'HardDisk' in b:
        #         if not got_nic:
        #             raise Exception('Bad boot order detected on %s (%s): %s' % (server_attrs['ResourceName'], onrack_res_id, bootseq))
        #             #needfix = True
        #             #break
        #if needfix:
        #    b2 = []
        #    for b in bootseq.split(','):
        #        if 'Integrated' in b:
        #            b2.append(b)
        #    for b in bootseq.split(','):
        #        if 'Integrated' not in b:
        #            b2.append(b)
        #    bootseq2 = ','.join(b2)
        #    qs_info('Attempting to fix boot order on %s (%s):\nBefore: %s\nNew: %s' % (server_attrs['ResourceName'], ipmi_ip, bootseq, bootseq2), context)
        #    ssh(ipmi_ip, 'root', 'calvin', 'racadm set BIOS.BiosBootSettings.BootSeq ' + bootseq2, context)
        #    jids = ssh(ipmi_ip, 'root', 'calvin', 'racadm jobqueue create BIOS.Setup.1-1 -r forced', context)
        #    # Commit JID = JID_782384188487
        #    # Reboot JID = RID_782384191517
        #    commit = jids.split('Commit JID =')[1].split('\n')[0].strip()##

        #    waited = 0
        #    while True:
        #        s = ssh(ipmi_ip, 'root', 'calvin', 'racadm jobqueue view -i ' + reboot, context)
        #        if 'Status=Reboot Completed' in s:
        #            break
        #        sleep(30)
        #        waited += 30
        #        if waited > 600:
        #            raise Exception('Reboot for BIOS boot order change did not succeed within 10 minutes. Status: %s' % s)
        #    waited = 0
        #    while True:
        #        s = ssh(ipmi_ip, 'root', 'calvin', 'racadm jobqueue view -i ' + commit, context)
        #        if 'Status=Completed' in s:
        #            break
        #        sleep(30)
        #        waited += 30
        #        if waited > 600:
        #            raise Exception('Commit for BIOS boot order change did not succeed within 10 minutes. Status: %s' % s)
        #    sleep(30)
        #    qs_info('Boot order fixed on %s, proceeding with OS install' % (server_attrs['ResourceName']), context)

        # except Exception as e:
        #     qs_info('Failed to check boot order: ' + str(e), context)

        tries = 0
        maxtries = int(context.resource.attributes['OS Deployment Attempts'])
        while tries < maxtries:
            tries += 1
            qs_info('Deploying %s on %s: Attempt #%d...' % (os_type, server_attrs['ResourceName'], tries), context)

            token = rest_json('post', 'https://' + onrack_ip + '/login',
                              {'email': onrack_username, 'password': onrack_password},
                              '', context)['response']['user']['authentication_token']

            # ip172 = rest_json('get', 'http://' + onrack_ip + ':8080/api/1.1/nodes/' + onrack_res_id + '/catalogs/ohai', None, None)['data']['ipaddress']
            # csapi.SetAttributeValue(attrs['ResourceName'], 'ESX PXE Network IP', ip172)

            try:
                # onrack_res_id = context.resource.attributes['OnRackID']
                x = rest_json('post', 'https://' + onrack_ip + '/rest/v1/ManagedSystems/Systems/' + onrack_res_id + '/OEM/OnRack/Actions/BootImage/ESXi', { # changed redfish to rest, added /ManagedSystems, added /ESXi
                    'domain': server_attrs['ESX Domain'],
                    'hostname': server_attrs['ResourceName'].split(' ')[-1],
                    'repo': 'http://' + server_attrs['ESX PXE Network Gateway'] + ':8080/esxi/6.0', #server_attrs['ESX Repo URL'],  # http://172.31.128.1:8080/esxi/6.0
                    'version': '6.0',
                    # 'version': attrs['ESX Version'],
                    # 'osName': 'ESXi', # removed osName
                    'networkDevices': [
                        {
                            'device': nic172,
                            'ipv4': {
                                'netmask': server_attrs['ESX PXE Network Netmask'],
                                'ipAddr': ip172,  # attrs['ESX PXE Network IP'], # context.resource.address,
                                'gateway': server_attrs['ESX PXE Network Gateway'],
                            }
                        }
                    ],
                    'switchDevices': [ # added switchDevices
                        {
                            'switchName': 'vSwitch0',
                            'uplinks': [nic172]
                        }
                    ],
                    # 'rootPassword': csapi.DecryptPassword(context.resource.attributes['ESX Root Password']).Value,
                    'rootPassword': server_attrs['ESX Root Password'],
                    'dnsServers': [
                        server_attrs['ESX DNS1'],
                        server_attrs['ESX DNS2'],
                    ]
                }, token, context)

                taskid = x['Id']
                state = 'no-state'
                waited = 0
                while True:
                    state = rest_json('get', 'https://' + onrack_ip + '/redfish/v1/TaskService/Tasks/' + taskid, None, token, context)['TaskState']
                    if state == 'Running':
                        waited += 1
                        if waited > 200:
                            break
                        sleep(10)
                    elif state in ['Completed', 'Exception', 'Killed']:
                        break

                if state != 'Completed':
                    try:
                        taskstatus = rest_json('get', 'http://' + onrack_ip + ':8080/api/common/workflows/' + taskid, None, None, context)
                        taskdump = 'task ' + taskstatus['instanceId'] + '\n'
                        taskdump += 'started ' + taskstatus['createdAt'] + '\n'
                        if 'target' in taskstatus['context']:
                            taskdump += 'target ' + taskstatus['context']['target'] + '\n'
                        if 'defaults' in taskstatus['definition']['options']:
                            taskdump += 'hostname ' + taskstatus['definition']['options']['defaults']['hostname'] + '\n'
                        for t, td in taskstatus['tasks'].iteritems():
                            # if td['state'] != 'succeeded':
                            taskdump += td['friendlyName'] + ': ' + td['state'] + '\n'
                        qs_trace(taskdump, context)
                        qs_trace(json.dumps(taskstatus), context)
                    except:
                        taskdump = '(also could not dump subtask report)'
                    raise Exception('OS deployment ended with status %s: %s' % (state, taskdump))
                qs_info('Sleeping 100 seconds', context)
                sleep(100)
                ping = subprocess.check_output(['ping', ip172], stderr=subprocess.STDOUT)
                # if 'host unreachable' in ping or '0% loss' not in ping:
                if 'TTL' not in ping:
                    raise Exception('Ping failed')

                qs_info('Ping succeeded', context)
                pw = server_attrs['ESX Root Password']
                ip10 = server_attrs['ResourceAddress']
                netmask10 = server_attrs['ESX Netmask']
                gateway10 = server_attrs['ESX Gateway']
                ssh(ip172, 'root', pw, 'esxcfg-vswitch -a vSwitch1', context)
                ssh(ip172, 'root', pw, 'esxcfg-vswitch vSwitch1 --link=' + nic10, context)
                ssh(ip172, 'root', pw, 'esxcfg-vswitch vSwitch1 --add-pg=' + nic10, context)
                ssh(ip172, 'root', pw, 'esxcfg-vmknic -a -i ' + ip10 + ' -n ' + netmask10 + ' ' + nic10, context)
                ssh(ip172, 'root', pw, 'esxcfg-route ' + gateway10, context)
                ssh(ip172, 'root', pw, 'esxcli system maintenanceMode set --enable false', context)
                ssh(ip172, 'root', pw, 'esxcli network  vswitch standard portgroup remove -v vSwitch0 -p "VM Network"', context)
                ssh(ip172, 'root', pw, 'esxcli network  vswitch standard portgroup add    -v vSwitch1 -p "VM Network"', context)

                csapi.SetResourceLiveStatus(server_attrs['ResourceName'], 'Online', '')
                csapi.SetAttributeValue(server_attrs['ResourceName'], 'Requires OS Deployment', 'False')
                qs_info('Finished installing %s on %s' % (os_type, server_attrs['ResourceName']), context)
                return
            except Exception as e:
                qs_info('Error installing %s on %s: %s' % (os_type, server_attrs['ResourceName'], str(e)), context)
                if 'in progress' in str(e).lower():
                    qs_info('Killing in-progress task on %s' % onrack_res_id)
                    # http://localhost:8080/api/common/nodes/$1/workflows/active
                    try:
                        rest_json('delete', 'http://' + onrack_ip + ':8080/api/common/nodes/' + onrack_res_id + '/workflows/active', None, '', context)
                    except Exception as e2:
                        qs_info('Failed to kill in-progress task on %s, sleeping 30 minutes to wait for task timeout. %s' % (onrack_res_id, str(e2)))
                        sleep(30*60)
                    sleep(60)
            sleep(30)
        raise Exception('Failed to install %s on %s in %d tries' % (os_type, server_attrs['ResourceName'], maxtries))
    
    
    def get_inventory(self, context):
        """
        Discovers the resource structure and attributes.
        :param AutoLoadCommandContext context: the context the command runs on
        :return Attribute and sub-resource information for the Shell resource you can return an AutoLoadDetails object
        :rtype: AutoLoadDetails
        """



        csapi = cloudshell.api.cloudshell_api.CloudShellAPISession(context.connectivity.server_address,
                                                                   port=context.connectivity.cloudshell_api_port,
                                                                   token_id=context.connectivity.admin_auth_token)

        onrack_ip = context.resource.address
        username = context.resource.attributes['User']
        password = csapi.DecryptPassword(context.resource.attributes['Password']).Value
        # password = context.resource.attributes['OnRack Password']

        token = rest_json('post', 'https://' + onrack_ip + '/login',
                          { 'email': username, 'password': password},
                          '', context)['response']['user']['authentication_token']

        systemlist = [x['@odata.id'].split('/')[-1]
                      for x in rest_json('get', 'https://' + onrack_ip + '/redfish/v1/Systems', None, token, context)['Members']]

        nodeid2eths = {}

        for node in rest_json('get', 'http://' + onrack_ip + ':8080/api/1.1/nodes', None, token, context):
            try:
                ohai = rest_json('get', 'http://' + onrack_ip + ':8080/api/1.1/nodes/' + node['id'] + '/catalogs/ohai', None, token, context)
                # ohai = json.loads('''{"node":"582a28eb5db8528c07d97c88","source":"ohai","data":{"languages":{"ruby":{"platform":"x86_64-linux","version":"1.9.3","release_date":"2013-11-22","target":"x86_64-pc-linux-gnu","target_cpu":"x86_64","target_vendor":"pc","target_os":"linux","host":"x86_64-pc-linux-gnu","host_cpu":"x86_64","host_os":"linux-gnu","host_vendor":"pc","bin_dir":"/usr/bin","ruby_bin":"/usr/bin/ruby1.9.1","gems_dir":"/var/lib/gems/1.9.1","gem_bin":"/usr/bin/gem1.9.1"},"python":{"version":"2.7.6","builddate":"Mar 22 2014, 22:59:56"},"perl":{"version":"5.18.2","archname":"x86_64-linux-gnu-thread-multi"}},"kernel":{"name":"Linux","release":"3.16.0-25-generic","version":"#33-Ubuntu SMP Fri Nov 7 01:53:40 UTC 2014","machine":"x86_64","modules":{"ipmi_si":{"size":"53386","refcount":"2"},"ipmi_devintf":{"size":"17572","refcount":"0"},"ipmi_poweroff":{"size":"14366","refcount":"0"},"ipmi_watchdog":{"size":"24912","refcount":"0"},"ipmi_msghandler":{"size":"45318","refcount":"4"},"ses":{"size":"17363","refcount":"0"},"enclosure":{"size":"15368","refcount":"1"},"igb":{"size":"187953","refcount":"0"},"hid_generic":{"size":"12559","refcount":"0"},"ixgbe":{"size":"246952","refcount":"0"},"i2c_algo_bit":{"size":"13413","refcount":"1"},"dca":{"size":"15130","refcount":"2"},"ahci":{"size":"29966","refcount":"0"},"usbhid":{"size":"52623","refcount":"0"},"ptp":{"size":"19395","refcount":"2"},"megaraid_sas":{"size":"100086","refcount":"0"},"hid":{"size":"110426","refcount":"2"},"libahci":{"size":"32424","refcount":"1"},"mdio":{"size":"13561","refcount":"1"},"pps_core":{"size":"19382","refcount":"1"},"overlayfs":{"size":"27916","refcount":"1"},"squashfs":{"size":"48362","refcount":"1"}},"os":"GNU/Linux"},"os":"linux","os_version":"3.16.0-25-generic","hostname":"monorail-micro","fqdn":"monorail-micro","domain":null,"network":{"interfaces":{"lo":{"mtu":"65536","encapsulation":"Loopback","state":"down"},"eth0":{"type":"eth","number":"0","mtu":"1500","flags":["BROADCAST","MULTICAST"],"encapsulation":"Ethernet","addresses":{"2C:60:0C:98:92:11":{"family":"lladdr"}},"state":"down"},"eth1":{"type":"eth","number":"1","mtu":"1500","flags":["BROADCAST","MULTICAST","UP","LOWER_UP"],"encapsulation":"Ethernet","addresses":{"90:E2:BA:82:BC:F8":{"family":"lladdr"},"172_31_128_2":{"family":"inet","prefixlen":"22","netmask":"255.255.252.0","broadcast":"172.31.131.255","scope":"Global"},"fe80::92e2:baff:fe82:bcf8":{"family":"inet6","prefixlen":"64","scope":"Link"}},"state":"up","arp":{"172_31_128_1":"00:50:56:99:c3:48"},"routes":[{"destination":"172.31.128.0/22","family":"inet","scope":"link","proto":"kernel","src":"172.31.128.2"},{"destination":"fe80::/64","family":"inet6","metric":"256","proto":"kernel"}]},"eth2":{"type":"eth","number":"2","mtu":"1500","flags":["BROADCAST","MULTICAST"],"encapsulation":"Ethernet","addresses":{"2C:60:0C:98:92:12":{"family":"lladdr"}},"state":"down"},"eth3":{"type":"eth","number":"3","mtu":"1500","flags":["BROADCAST","MULTICAST"],"encapsulation":"Ethernet","addresses":{"90:E2:BA:82:BC:F9":{"family":"lladdr"}},"state":"down"},"eth4":{"type":"eth","number":"4","mtu":"1500","flags":["BROADCAST","MULTICAST"],"encapsulation":"Ethernet","addresses":{"2C:60:0C:98:94:D3":{"family":"lladdr"}},"state":"down"},"eth5":{"type":"eth","number":"5","mtu":"1500","flags":["BROADCAST","MULTICAST"],"encapsulation":"Ethernet","addresses":{"2C:60:0C:98:94:D4":{"family":"lladdr"}},"state":"down"}},"listeners":{"tcp":{"22":{"address":"*","pid":1101,"name":"sshd"}}}},"counters":{"network":{"interfaces":{"lo":{"rx":{"bytes":"0","packets":"0","errors":"0","drop":"0","overrun":"0"},"tx":{"bytes":"0","packets":"0","errors":"0","drop":"0","carrier":"0","collisions":"0"}},"eth0":{"tx":{"queuelen":"1000","bytes":"0","packets":"0","errors":"0","drop":"0","carrier":"0","collisions":"0"},"rx":{"bytes":"0","packets":"0","errors":"0","drop":"0","overrun":"0"}},"eth1":{"tx":{"queuelen":"1000","bytes":"225624","packets":"2907","errors":"0","drop":"0","carrier":"0","collisions":"0"},"rx":{"bytes":"60990324","packets":"4077","errors":"0","drop":"0","overrun":"0"}},"eth2":{"tx":{"queuelen":"1000","bytes":"0","packets":"0","errors":"0","drop":"0","carrier":"0","collisions":"0"},"rx":{"bytes":"0","packets":"0","errors":"0","drop":"0","overrun":"0"}},"eth3":{"tx":{"queuelen":"1000","bytes":"0","packets":"0","errors":"0","drop":"0","carrier":"0","collisions":"0"},"rx":{"bytes":"0","packets":"0","errors":"0","drop":"0","overrun":"0"}},"eth4":{"tx":{"queuelen":"1000","bytes":"0","packets":"0","errors":"0","drop":"0","carrier":"0","collisions":"0"},"rx":{"bytes":"0","packets":"0","errors":"0","drop":"0","overrun":"0"}},"eth5":{"tx":{"queuelen":"1000","bytes":"0","packets":"0","errors":"0","drop":"0","carrier":"0","collisions":"0"},"rx":{"bytes":"0","packets":"0","errors":"0","drop":"0","overrun":"0"}}}}},"ipaddress":"172.31.128.2","macaddress":"90:E2:BA:82:BC:F8","ohai_time":1479141884.109528,"etc":{"passwd":{"root":{"dir":"/root","gid":0,"uid":0,"shell":"/bin/bash","gecos":"root"},"daemon":{"dir":"/usr/sbin","gid":1,"uid":1,"shell":"/usr/sbin/nologin","gecos":"daemon"},"bin":{"dir":"/bin","gid":2,"uid":2,"shell":"/usr/sbin/nologin","gecos":"bin"},"sys":{"dir":"/dev","gid":3,"uid":3,"shell":"/usr/sbin/nologin","gecos":"sys"},"sync":{"dir":"/bin","gid":65534,"uid":4,"shell":"/bin/sync","gecos":"sync"},"games":{"dir":"/usr/games","gid":60,"uid":5,"shell":"/usr/sbin/nologin","gecos":"games"},"man":{"dir":"/var/cache/man","gid":12,"uid":6,"shell":"/usr/sbin/nologin","gecos":"man"},"lp":{"dir":"/var/spool/lpd","gid":7,"uid":7,"shell":"/usr/sbin/nologin","gecos":"lp"},"mail":{"dir":"/var/mail","gid":8,"uid":8,"shell":"/usr/sbin/nologin","gecos":"mail"},"news":{"dir":"/var/spool/news","gid":9,"uid":9,"shell":"/usr/sbin/nologin","gecos":"news"},"uucp":{"dir":"/var/spool/uucp","gid":10,"uid":10,"shell":"/usr/sbin/nologin","gecos":"uucp"},"proxy":{"dir":"/bin","gid":13,"uid":13,"shell":"/usr/sbin/nologin","gecos":"proxy"},"www-data":{"dir":"/var/www","gid":33,"uid":33,"shell":"/usr/sbin/nologin","gecos":"www-data"},"backup":{"dir":"/var/backups","gid":34,"uid":34,"shell":"/usr/sbin/nologin","gecos":"backup"},"list":{"dir":"/var/list","gid":38,"uid":38,"shell":"/usr/sbin/nologin","gecos":"Mailing List Manager"},"irc":{"dir":"/var/run/ircd","gid":39,"uid":39,"shell":"/usr/sbin/nologin","gecos":"ircd"},"gnats":{"dir":"/var/lib/gnats","gid":41,"uid":41,"shell":"/usr/sbin/nologin","gecos":"Gnats Bug-Reporting System (admin)"},"nobody":{"dir":"/nonexistent","gid":65534,"uid":65534,"shell":"/usr/sbin/nologin","gecos":"nobody"},"libuuid":{"dir":"/var/lib/libuuid","gid":101,"uid":100,"shell":"","gecos":""},"monorail":{"dir":"/home/monorail","gid":999,"uid":999,"shell":"/bin/bash","gecos":""},"sshd":{"dir":"/var/run/sshd","gid":65534,"uid":101,"shell":"/usr/sbin/nologin","gecos":""},"_lldpd":{"dir":"/var/run/lldpd","gid":104,"uid":102,"shell":"/bin/false","gecos":""}},"group":{"root":{"gid":0,"members":[]},"daemon":{"gid":1,"members":[]},"bin":{"gid":2,"members":[]},"sys":{"gid":3,"members":[]},"adm":{"gid":4,"members":[]},"tty":{"gid":5,"members":[]},"disk":{"gid":6,"members":[]},"lp":{"gid":7,"members":[]},"mail":{"gid":8,"members":[]},"news":{"gid":9,"members":[]},"uucp":{"gid":10,"members":[]},"man":{"gid":12,"members":[]},"proxy":{"gid":13,"members":[]},"kmem":{"gid":15,"members":[]},"dialout":{"gid":20,"members":[]},"fax":{"gid":21,"members":[]},"voice":{"gid":22,"members":[]},"cdrom":{"gid":24,"members":[]},"floppy":{"gid":25,"members":[]},"tape":{"gid":26,"members":[]},"sudo":{"gid":27,"members":[]},"audio":{"gid":29,"members":[]},"dip":{"gid":30,"members":[]},"www-data":{"gid":33,"members":[]},"backup":{"gid":34,"members":[]},"operator":{"gid":37,"members":[]},"list":{"gid":38,"members":[]},"irc":{"gid":39,"members":[]},"src":{"gid":40,"members":[]},"gnats":{"gid":41,"members":[]},"shadow":{"gid":42,"members":[]},"utmp":{"gid":43,"members":[]},"video":{"gid":44,"members":[]},"sasl":{"gid":45,"members":[]},"plugdev":{"gid":46,"members":[]},"staff":{"gid":50,"members":[]},"games":{"gid":60,"members":[]},"users":{"gid":100,"members":[]},"nogroup":{"gid":65534,"members":[]},"libuuid":{"gid":101,"members":[]},"netdev":{"gid":102,"members":[]},"monorail":{"gid":999,"members":[]},"ssh":{"gid":103,"members":[]},"_lldpd":{"gid":104,"members":[]}}},"current_user":"root","dmi":{"dmidecode_version":"2.12","smbios_version":"2.8","structures":{"count":"76","size":"4695"},"table_location":"0x7BBBC000","bios":{"all_records":[{"record_id":"0x0000","size":"0","application_identifier":"BIOS Information","Vendor":"American Megatrends Inc.","Version":"S2B_3A17","Release Date":"11/07/2014","Address":"0xF0000","Runtime Size":"64 kB","ROM Size":"8192 kB","Characteristics":{"PCI is supported":null,"BIOS is upgradeable":null,"BIOS shadowing is allowed":null,"Boot from CD is supported":null,"Selectable boot is supported":null,"BIOS ROM is socketed":null,"EDD is supported":null,"Print screen service is supported (int 5h)":null,"8042 keyboard services are supported (int 9h)":null,"Serial services are supported (int 14h)":null,"Printer services are supported (int 17h)":null,"ACPI is supported":null,"USB legacy is supported":null,"BIOS boot specification is supported":null,"Targeted content distribution is supported":null,"UEFI is supported":null},"BIOS Revision":"5.6","Firmware Revision":"3.31"}],"vendor":"American Megatrends Inc.","version":"S2B_3A17","release_date":"11/07/2014","address":"0xF0000","runtime_size":"64 kB","rom_size":"8192 kB","bios_revision":"5.6","firmware_revision":"3.31"},"system":{"all_records":[{"record_id":"0x0001","size":"1","application_identifier":"System Information","Manufacturer":"Quanta Computer Inc","Product Name":"D51B-2U (dual 1G LoM)","Version":"To be filled by O.E.M.","Serial Number":"QTFCJ05260027","UUID":"51C208A2-7C18-1000-B48B-2C600C989213","Wake-up Type":"Other","SKU Number":"To be filled by O.E.M.","Family":"To be filled by O.E.M."}],"manufacturer":"Quanta Computer Inc","product_name":"D51B-2U (dual 1G LoM)","version":"To be filled by O.E.M.","serial_number":"QTFCJ05260027","uuid":"51C208A2-7C18-1000-B48B-2C600C989213","wake_up_type":"Other","sku_number":"To be filled by O.E.M.","family":"To be filled by O.E.M."},"base_board":{"all_records":[{"record_id":"0x0002","size":"2","application_identifier":"Base Board Information","Manufacturer":"Quanta Computer Inc","Product Name":"S2B-MB (dual 1G LoM)","Version":"31S2BMB0030","Serial Number":"QTF3J052100191","Asset Tag":" ","Features":{"Board is a hosting board":null,"Board is replaceable":null},"Location In Chassis":"To be filled by O.E.M.","Chassis Handle":"0x0003","Type":"Motherboard","Contained Object Handles":"0"}],"manufacturer":"Quanta Computer Inc","product_name":"S2B-MB (dual 1G LoM)","version":"31S2BMB0030","serial_number":"QTF3J052100191","asset_tag":" ","location_in_chassis":"To be filled by O.E.M.","chassis_handle":"0x0003","type":"Motherboard","contained_object_handles":"0"},"chassis":{"all_records":[{"record_id":"0x0003","size":"3","application_identifier":"Onboard Device","Manufacturer":"Quanta Computer Inc","Type":"SATA Controller","Lock":"Not Present","Version":"To be filled by O.E.M.","Serial Number":"QTFCJ05260027","Asset Tag":" ","Boot-up State":"Safe","Power Supply State":"Safe","Thermal State":"Safe","Security Status":"None","OEM Information":"0x00000000","Height":"Unspecified","Number Of Power Cords":"1","Contained Elements":{"<OUT OF SPEC> (0)":null},"SKU Number":"To be filled by O.E.M.","Internal Reference Designator":"Not Specified","Internal Connector Type":"None","External Reference Designator":"J2-REAR_VIDEO","External Connector Type":"Access Bus (USB)","Port Type":"USB","Designation":"Riser1_Slot1_x8","Current Usage":"Available","Length":"Long","Characteristics":{"3_3 V is provided":null},"Bus Address":"0001:00:11.4","Reference Designation":"sSATA_Controller","Status":"Enabled","Type Instance":"1"}],"manufacturer":"Quanta Computer Inc","type":"SATA Controller","lock":"Not Present","version":"To be filled by O.E.M.","serial_number":"QTFCJ05260027","asset_tag":" ","boot_up_state":"Safe","power_supply_state":"Safe","thermal_state":"Safe","security_status":"None","oem_information":"0x00000000","height":"Unspecified","number_of_power_cords":"1","sku_number":"To be filled by O.E.M.","internal_reference_designator":"Not Specified","internal_connector_type":"None","external_reference_designator":"J2-REAR_VIDEO","external_connector_type":"Access Bus (USB)","port_type":"USB","designation":"Riser1_Slot1_x8","current_usage":"Available","length":"Long","bus_address":"0001:00:11.4","reference_designation":"sSATA_Controller","status":"Enabled","type_instance":"1"},"oem_strings":{"all_records":[{"record_id":"0x0024","size":"11","application_identifier":"Cache Information","String 1":"To Be Filled By O.E.M.","Interface Type":"KCS (Keyboard Control Style)","Specification Version":"2.0","I2C Slave Address":"0x10","NV Storage Device":"Not Present","Base Address":"0x0000000000000CA2 (I/O)","Register Spacing":"Successive Byte Boundaries","Location":"Internal","Use":"System Memory","Error Correction Type":"Single-bit ECC","Maximum Capacity":"384 GB","Error Information Handle":"Not Provided","Number Of Devices":"6","Starting Address":"0x03000000000","Ending Address":"0x03FFFFFFFFF","Range Size":"64 GB","Physical Array Handle":"0x004E","Partition Width":"2","Array Handle":"0x004E","Total Width":"Unknown","Data Width":"Unknown","Size":"No Module Installed","Form Factor":"DIMM","Set":"None","Locator":"DIMM_H2","Bank Locator":"_Node1_Channel3_Dimm2","Type":"Other","Type Detail":"Synchronous","Speed":"Unknown","Manufacturer":"NO DIMM","Serial Number":"NO DIMM","Asset Tag":"NO DIMM","Part Number":"NO DIMM","Rank":"Unknown","Configured Clock Speed":"Unknown","Minimum voltage":" Unknown","Maximum voltage":" Unknown","Configured voltage":" Unknown","Socket Designation":"CPU Internal L3","Configuration":"Enabled, Not Socketed, Level 3","Operational Mode":"Write Back","Installed Size":"30720 kB","Maximum Size":"30720 kB","Supported SRAM Types":{"Unknown":null},"Installed SRAM Type":"Unknown","System Type":"Unified","Associativity":"20-way Set-associative"}],"string_1":"To Be Filled By O.E.M.","interface_type":"KCS (Keyboard Control Style)","specification_version":"2.0","i2c_slave_address":"0x10","nv_storage_device":"Not Present","base_address":"0x0000000000000CA2 (I/O)","register_spacing":"Successive Byte Boundaries","location":"Internal","use":"System Memory","error_correction_type":"Single-bit ECC","maximum_capacity":"384 GB","error_information_handle":"Not Provided","number_of_devices":"6","starting_address":"0x03000000000","ending_address":"0x03FFFFFFFFF","range_size":"64 GB","physical_array_handle":"0x004E","partition_width":"2","array_handle":"0x004E","total_width":"Unknown","data_width":"Unknown","size":"No Module Installed","form_factor":"DIMM","set":"None","locator":"DIMM_H2","bank_locator":"_Node1_Channel3_Dimm2","type":"Other","type_detail":"Synchronous","speed":"Unknown","manufacturer":"NO DIMM","serial_number":"NO DIMM","asset_tag":"NO DIMM","part_number":"NO DIMM","rank":"Unknown","configured_clock_speed":"Unknown","minimum_voltage":" Unknown","maximum_voltage":" Unknown","configured_voltage":" Unknown","socket_designation":"CPU Internal L3","configuration":"Enabled, Not Socketed, Level 3","operational_mode":"Write Back","installed_size":"30720 kB","maximum_size":"30720 kB","installed_sram_type":"Unknown","system_type":"Unified","associativity":"20-way Set-associative"},"processor":{"all_records":[{"record_id":"0x0059","size":"4","application_identifier":"Cache Information","Socket Designation":"CPU Internal L3","Type":"Central Processor","Family":"Xeon","Manufacturer":"Intel","ID":"F2 06 03 00 FF FB EB BF","Signature":"Type 0, Family 6, Model 63, Stepping 2","Flags":{"FPU (Floating-point unit on-chip)":null,"VME (Virtual mode extension)":null,"DE (Debugging extension)":null,"PSE (Page size extension)":null,"TSC (Time stamp counter)":null,"MSR (Model specific registers)":null,"PAE (Physical address extension)":null,"MCE (Machine check exception)":null,"CX8 (CMPXCHG8 instruction supported)":null,"APIC (On-chip APIC hardware supported)":null,"SEP (Fast system call)":null,"MTRR (Memory type range registers)":null,"PGE (Page global enable)":null,"MCA (Machine check architecture)":null,"CMOV (Conditional move instruction supported)":null,"PAT (Page attribute table)":null,"PSE-36 (36-bit page size extension)":null,"CLFSH (CLFLUSH instruction supported)":null,"DS (Debug store)":null,"ACPI (ACPI supported)":null,"MMX (MMX technology supported)":null,"FXSR (FXSAVE and FXSTOR instructions supported)":null,"SSE (Streaming SIMD extensions)":null,"SSE2 (Streaming SIMD extensions 2)":null,"SS (Self-snoop)":null,"HTT (Multi-threading)":null,"TM (Thermal monitor supported)":null,"PBE (Pending break enabled)":null},"Version":"Intel(R) Xeon(R) CPU E5-2680 v3 @ 2.50GHz","Voltage":"0.6 V","External Clock":"100 MHz","Max Speed":"2500 MHz","Current Speed":"2500 MHz","Status":"Populated, Enabled","Upgrade":"<OUT OF SPEC>","L1 Cache Handle":"0x0056","L2 Cache Handle":"0x0057","L3 Cache Handle":"0x0058","Serial Number":"Not Specified","Asset Tag":"Not Specified","Part Number":"Not Specified","Core Count":"12","Core Enabled":"12","Thread Count":"24","Characteristics":{"64-bit capable":null,"Multi-Core":null,"Hardware Thread":null,"Execute Protection":null,"Enhanced Virtualization":null,"Power/Performance Control":null},"Configuration":"Enabled, Not Socketed, Level 3","Operational Mode":"Write Back","Location":"Internal","Installed Size":"30720 kB","Maximum Size":"30720 kB","Supported SRAM Types":{"Unknown":null},"Installed SRAM Type":"Unknown","Speed":"Unknown","Error Correction Type":"Single-bit ECC","System Type":"Unified","Associativity":"20-way Set-associative"},{"record_id":"0x005D","size":"4","application_identifier":"End Of Table","Socket Designation":"SOCKET 1","Type":"Central Processor","Family":"Xeon","Manufacturer":"Intel","ID":"F2 06 03 00 FF FB EB BF","Signature":"Type 0, Family 6, Model 63, Stepping 2","Flags":{"FPU (Floating-point unit on-chip)":null,"VME (Virtual mode extension)":null,"DE (Debugging extension)":null,"PSE (Page size extension)":null,"TSC (Time stamp counter)":null,"MSR (Model specific registers)":null,"PAE (Physical address extension)":null,"MCE (Machine check exception)":null,"CX8 (CMPXCHG8 instruction supported)":null,"APIC (On-chip APIC hardware supported)":null,"SEP (Fast system call)":null,"MTRR (Memory type range registers)":null,"PGE (Page global enable)":null,"MCA (Machine check architecture)":null,"CMOV (Conditional move instruction supported)":null,"PAT (Page attribute table)":null,"PSE-36 (36-bit page size extension)":null,"CLFSH (CLFLUSH instruction supported)":null,"DS (Debug store)":null,"ACPI (ACPI supported)":null,"MMX (MMX technology supported)":null,"FXSR (FXSAVE and FXSTOR instructions supported)":null,"SSE (Streaming SIMD extensions)":null,"SSE2 (Streaming SIMD extensions 2)":null,"SS (Self-snoop)":null,"HTT (Multi-threading)":null,"TM (Thermal monitor supported)":null,"PBE (Pending break enabled)":null},"Version":"Intel(R) Xeon(R) CPU E5-2680 v3 @ 2.50GHz","Voltage":"0.6 V","External Clock":"100 MHz","Max Speed":"2500 MHz","Current Speed":"2500 MHz","Status":"Populated, Enabled","Upgrade":"<OUT OF SPEC>","L1 Cache Handle":"0x005A","L2 Cache Handle":"0x005B","L3 Cache Handle":"0x005C","Serial Number":"Not Specified","Asset Tag":"Not Specified","Part Number":"Not Specified","Core Count":"12","Core Enabled":"12","Thread Count":"24","Characteristics":{"64-bit capable":null,"Multi-Core":null,"Hardware Thread":null,"Execute Protection":null,"Enhanced Virtualization":null,"Power/Performance Control":null},"Language Description Format":"Long","Installable Languages":{"en|US|iso8859-1":null},"Currently Installed Language":"en|US|iso8859-1"}],"type":"Central Processor","family":"Xeon","manufacturer":"Intel","id":"F2 06 03 00 FF FB EB BF","signature":"Type 0, Family 6, Model 63, Stepping 2","version":"Intel(R) Xeon(R) CPU E5-2680 v3 @ 2.50GHz","voltage":"0.6 V","external_clock":"100 MHz","max_speed":"2500 MHz","current_speed":"2500 MHz","status":"Populated, Enabled","upgrade":"<OUT OF SPEC>","serial_number":"Not Specified","asset_tag":"Not Specified","part_number":"Not Specified","core_count":"12","core_enabled":"12","thread_count":"24","configuration":"Enabled, Not Socketed, Level 3","operational_mode":"Write Back","location":"Internal","installed_size":"30720 kB","maximum_size":"30720 kB","installed_sram_type":"Unknown","speed":"Unknown","error_correction_type":"Single-bit ECC","system_type":"Unified","associativity":"20-way Set-associative","language_description_format":"Long","currently_installed_language":"en|US|iso8859-1"}},"chef_packages":{"ohai":{"version":"6.14.0","ohai_root":"/usr/lib/ruby/vendor_ruby/ohai"}},"virtualization":{},"keys":{"ssh":{"host_dsa_public":"AAAAB3NzaC1kc3MAAACBALbaYXQP5QV+QCrWQL0oRaQinKM0siCkGWSoBIelpOAXsEbDgipMLbD6Klm672uJSG02inrekF3+b1OH2AnHfpFCHBn12iMeI7hkOyssT6tUIDJi6HEdilJpJhxnGP8b6JfsB5UHERHwC6dtrfwGdl3UIgfXRQW+AH0KShy/1F1TAAAAFQDA1mvd4t5+jE4P5Fz+Tw8uUyFg/wAAAIA5wtL9lc8nC/037+JmmfbwyQsj1UTv40UnM4wKfoBTceSgi6XGJvkrmx90giTmUJxD3OSDRvHiu+b7XWn7k0dJcuKKlqy31oxXntx8tqJZWeLXVtrDfGEyzn+UuQ+KoviNpaIUrpd/tO9iDQ1dlyIm8YNjilmj3tDT09l4w6jvGgAAAIAIfnePbDiV4fOp9B9U0d0ESesnntffb14ini2d+NtpnRDpvXhSdo/vvmPhJRT5DeDIdtlG33LV6WuTb5R0RrqxFHHpMRlfKCGchGGNnBxuxN/YZ4mXW1oLx/mvJr34wfKpbf2CJx4gA5Qbz8RYCLZZI++dmIM9wzdg9I/NbLELHQ==","host_rsa_public":"AAAAB3NzaC1yc2EAAAADAQABAAABAQDqwfPSmABwE0cCu7zwsf6+P6RMFRasOqahoD73rYetHR1EDgjgBE/4k3c1ZIYLN7jAU92jf58Jo2sriCWpv8/H4ICMjbwPSI9PvX/rSTnuWOh4boHvnHySg4j5cbvUN6wYhjnUlhWO5fTflmRgQgjqHmQZsIp8b0fm69v8pQ1quihsaT76TCZBcQ9MuU87SwYqIF7VIuhTpyIytg6vQ+qLuoRxV43d4llU+rMBdKja7JPW1VjaTHly4nTXyyc+O9CkkaxglN5Smb1RfCBHWsPXQS5F1RzmRAv9KniTbv3b7c/jQH+ZgHyctFeB2TMuxNn+LjLX4L2ReYjhhCvtCYS/"}},"command":{"ps":"ps -ef"},"lsb":{"id":"Ubuntu","release":"14.04","codename":"trusty","description":"Ubuntu 14.04 LTS"},"platform":"ubuntu","platform_version":"14.04","platform_family":"debian","filesystem":{"overlayfs":{"kb_size":"132017640","kb_used":"31004","kb_available":"131986636","percent_used":"1%","mount":"/","fs_type":"overlayfs","mount_options":["rw"]},"udev":{"kb_size":"132007408","kb_used":"4","kb_available":"132007404","percent_used":"1%","mount":"/dev","fs_type":"devtmpfs","mount_options":["rw","mode=0755"]},"tmpfs":{"kb_size":"26403528","kb_used":"1260","kb_available":"26402268","percent_used":"1%","mount":"/run","fs_type":"tmpfs","mount_options":["rw","noexec","nosuid","size=10%","mode=0755"]},"none":{"kb_size":"102400","kb_used":"0","kb_available":"102400","percent_used":"0%","mount":"/sys/fs/pstore","fs_type":"pstore","mount_options":["rw"]},"proc":{"mount":"/proc","fs_type":"proc","mount_options":["rw","noexec","nosuid","nodev"]},"sysfs":{"mount":"/sys","fs_type":"sysfs","mount_options":["rw","noexec","nosuid","nodev"]},"devpts":{"mount":"/dev/pts","fs_type":"devpts","mount_options":["rw","noexec","nosuid","gid=5","mode=0620"]},"/dev/loop0":{"fs_type":"squashfs"},"/dev/sda1":{"fs_type":"ext4","uuid":"5456e743-4f43-4c2e-bfcc-450333ad6fc7","label":"root"},"rootfs":{"mount":"/","fs_type":"rootfs","mount_options":["rw","size=132007392k","nr_inodes=33001848"]}},"memory":{"swap":{"cached":"0kB","total":"0kB","free":"0kB"},"total":"264035280kB","free":"262114008kB","buffers":"16148kB","cached":"118608kB","active":"90036kB","inactive":"78240kB","dirty":"0kB","writeback":"0kB","anon_pages":"32912kB","mapped":"17572kB","slab":"93944kB","slab_reclaimable":"24128kB","slab_unreclaim":"69816kB","page_tables":"5332kB","nfs_unstable":"0kB","bounce":"0kB","commit_limit":"132017640kB","committed_as":"336272kB","vmalloc_total":"34359738367kB","vmalloc_used":"691244kB","vmalloc_chunk":"34224833332kB"},"block_device":{"sda":{"size":"2343174144","removable":"0","model":"MRROMB","rev":"4.27","state":"running","timeout":"90","vendor":"LSI"},"sdb":{"size":"2343174144","removable":"0","model":"MRROMB","rev":"4.27","state":"running","timeout":"90","vendor":"LSI"},"sdc":{"size":"2343174144","removable":"0","model":"MRROMB","rev":"4.27","state":"running","timeout":"90","vendor":"LSI"},"sdd":{"size":"2343174144","removable":"0","model":"MRROMB","rev":"4.27","state":"running","timeout":"90","vendor":"LSI"},"sde":{"size":"2343174144","removable":"0","model":"MRROMB","rev":"4.27","state":"running","timeout":"90","vendor":"LSI"},"sdf":{"size":"2343174144","removable":"0","model":"MRROMB","rev":"4.27","state":"running","timeout":"90","vendor":"LSI"},"sdg":{"size":"2343174144","removable":"0","model":"MRROMB","rev":"4.27","state":"running","timeout":"90","vendor":"LSI"},"sdh":{"size":"2343174144","removable":"0","model":"MRROMB","rev":"4.27","state":"running","timeout":"90","vendor":"LSI"},"sdi":{"size":"2343174144","removable":"0","model":"MRROMB","rev":"4.27","state":"running","timeout":"90","vendor":"LSI"},"sdj":{"size":"2343174144","removable":"0","model":"MRROMB","rev":"4.27","state":"running","timeout":"90","vendor":"LSI"},"sdk":{"size":"2343174144","removable":"0","model":"MRROMB","rev":"4.27","state":"running","timeout":"90","vendor":"LSI"},"sdl":{"size":"2343174144","removable":"0","model":"MRROMB","rev":"4.27","state":"running","timeout":"90","vendor":"LSI"},"sdm":{"size":"2343174144","removable":"0","model":"MRROMB","rev":"4.27","state":"running","timeout":"90","vendor":"LSI"},"sdn":{"size":"2343174144","removable":"0","model":"MRROMB","rev":"4.27","state":"running","timeout":"90","vendor":"LSI"},"sdo":{"size":"2343174144","removable":"0","model":"MRROMB","rev":"4.27","state":"running","timeout":"90","vendor":"LSI"},"sdp":{"size":"2343174144","removable":"0","model":"MRROMB","rev":"4.27","state":"running","timeout":"90","vendor":"LSI"},"sdq":{"size":"2343174144","removable":"0","model":"MRROMB","rev":"4.27","state":"running","timeout":"90","vendor":"LSI"},"sdr":{"size":"2343174144","removable":"0","model":"MRROMB","rev":"4.27","state":"running","timeout":"90","vendor":"LSI"},"sds":{"size":"1561722880","removable":"0","model":"MRROMB","rev":"4.27","state":"running","timeout":"90","vendor":"LSI"},"sdt":{"size":"1561722880","removable":"0","model":"MRROMB","rev":"4.27","state":"running","timeout":"90","vendor":"LSI"},"sdu":{"size":"1561722880","removable":"0","model":"MRROMB","rev":"4.27","state":"running","timeout":"90","vendor":"LSI"},"sdv":{"size":"1561722880","removable":"0","model":"MRROMB","rev":"4.27","state":"running","timeout":"90","vendor":"LSI"},"sdw":{"size":"1561722880","removable":"0","model":"MRROMB","rev":"4.27","state":"running","timeout":"90","vendor":"LSI"},"sdx":{"size":"1561722880","removable":"0","model":"MRROMB","rev":"4.27","state":"running","timeout":"90","vendor":"LSI"},"sdy":{"size":"62533296","removable":"0","model":"SATADOM-SH TYPE","rev":"710","state":"running","timeout":"30","vendor":"ATA"},"ram0":{"size":"131072","removable":"0"},"ram1":{"size":"131072","removable":"0"},"ram2":{"size":"131072","removable":"0"},"ram3":{"size":"131072","removable":"0"},"ram4":{"size":"131072","removable":"0"},"ram5":{"size":"131072","removable":"0"},"ram6":{"size":"131072","removable":"0"},"ram7":{"size":"131072","removable":"0"},"ram8":{"size":"131072","removable":"0"},"ram9":{"size":"131072","removable":"0"},"loop0":{"size":"100504","removable":"0"},"loop1":{"size":"0","removable":"0"},"loop2":{"size":"0","removable":"0"},"loop3":{"size":"0","removable":"0"},"loop4":{"size":"0","removable":"0"},"loop5":{"size":"0","removable":"0"},"loop6":{"size":"0","removable":"0"},"loop7":{"size":"0","removable":"0"},"ram10":{"size":"131072","removable":"0"},"ram11":{"size":"131072","removable":"0"},"ram12":{"size":"131072","removable":"0"},"ram13":{"size":"131072","removable":"0"},"ram14":{"size":"131072","removable":"0"},"ram15":{"size":"131072","removable":"0"}},"uptime_seconds":24,"uptime":"24 seconds","idletime_seconds":1015,"idletime":"16 minutes 55 seconds","cpu":{"0":{"vendor_id":"GenuineIntel","family":"6","model":"63","model_name":"Intel(R) Xeon(R) CPU E5-2680 v3 @ 2.50GHz","stepping":"2","mhz":"1200.000","cache_size":"30720 KB","physical_id":"0","core_id":"0","cores":"12","flags":["fpu","vme","de","pse","tsc","msr","pae","mce","cx8","apic","sep","mtrr","pge","mca","cmov","pat","pse36","clflush","dts","acpi","mmx","fxsr","sse","sse2","ss","ht","tm","pbe","syscall","nx","pdpe1gb","rdtscp","lm","constant_tsc","arch_perfmon","pebs","bts","rep_good","nopl","xtopology","nonstop_tsc","aperfmperf","eagerfpu","pni","pclmulqdq","dtes64","monitor","ds_cpl","vmx","smx","est","tm2","ssse3","fma","cx16","xtpr","pdcm","pcid","dca","sse4_1","sse4_2","x2apic","movbe","popcnt","tsc_deadline_timer","aes","xsave","avx","f16c","rdrand","lahf_lm","abm","ida","arat","epb","xsaveopt","pln","pts","dtherm","tpr_shadow","vnmi","flexpriority","ept","vpid","fsgsbase","tsc_adjust","bmi1","avx2","smep","bmi2","erms","invpcid"]},"1":{"vendor_id":"GenuineIntel","family":"6","model":"63","model_name":"Intel(R) Xeon(R) CPU E5-2680 v3 @ 2.50GHz","stepping":"2","mhz":"1200.195","cache_size":"30720 KB","physical_id":"0","core_id":"1","cores":"12","flags":["fpu","vme","de","pse","tsc","msr","pae","mce","cx8","apic","sep","mtrr","pge","mca","cmov","pat","pse36","clflush","dts","acpi","mmx","fxsr","sse","sse2","ss","ht","tm","pbe","syscall","nx","pdpe1gb","rdtscp","lm","constant_tsc","arch_perfmon","pebs","bts","rep_good","nopl","xtopology","nonstop_tsc","aperfmperf","eagerfpu","pni","pclmulqdq","dtes64","monitor","ds_cpl","vmx","smx","est","tm2","ssse3","fma","cx16","xtpr","pdcm","pcid","dca","sse4_1","sse4_2","x2apic","movbe","popcnt","tsc_deadline_timer","aes","xsave","avx","f16c","rdrand","lahf_lm","abm","ida","arat","epb","xsaveopt","pln","pts","dtherm","tpr_shadow","vnmi","flexpriority","ept","vpid","fsgsbase","tsc_adjust","bmi1","avx2","smep","bmi2","erms","invpcid"]},"2":{"vendor_id":"GenuineIntel","family":"6","model":"63","model_name":"Intel(R) Xeon(R) CPU E5-2680 v3 @ 2.50GHz","stepping":"2","mhz":"1200.000","cache_size":"30720 KB","physical_id":"0","core_id":"2","cores":"12","flags":["fpu","vme","de","pse","tsc","msr","pae","mce","cx8","apic","sep","mtrr","pge","mca","cmov","pat","pse36","clflush","dts","acpi","mmx","fxsr","sse","sse2","ss","ht","tm","pbe","syscall","nx","pdpe1gb","rdtscp","lm","constant_tsc","arch_perfmon","pebs","bts","rep_good","nopl","xtopology","nonstop_tsc","aperfmperf","eagerfpu","pni","pclmulqdq","dtes64","monitor","ds_cpl","vmx","smx","est","tm2","ssse3","fma","cx16","xtpr","pdcm","pcid","dca","sse4_1","sse4_2","x2apic","movbe","popcnt","tsc_deadline_timer","aes","xsave","avx","f16c","rdrand","lahf_lm","abm","ida","arat","epb","xsaveopt","pln","pts","dtherm","tpr_shadow","vnmi","flexpriority","ept","vpid","fsgsbase","tsc_adjust","bmi1","avx2","smep","bmi2","erms","invpcid"]},"3":{"vendor_id":"GenuineIntel","family":"6","model":"63","model_name":"Intel(R) Xeon(R) CPU E5-2680 v3 @ 2.50GHz","stepping":"2","mhz":"1200.000","cache_size":"30720 KB","physical_id":"0","core_id":"3","cores":"12","flags":["fpu","vme","de","pse","tsc","msr","pae","mce","cx8","apic","sep","mtrr","pge","mca","cmov","pat","pse36","clflush","dts","acpi","mmx","fxsr","sse","sse2","ss","ht","tm","pbe","syscall","nx","pdpe1gb","rdtscp","lm","constant_tsc","arch_perfmon","pebs","bts","rep_good","nopl","xtopology","nonstop_tsc","aperfmperf","eagerfpu","pni","pclmulqdq","dtes64","monitor","ds_cpl","vmx","smx","est","tm2","ssse3","fma","cx16","xtpr","pdcm","pcid","dca","sse4_1","sse4_2","x2apic","movbe","popcnt","tsc_deadline_timer","aes","xsave","avx","f16c","rdrand","lahf_lm","abm","ida","arat","epb","xsaveopt","pln","pts","dtherm","tpr_shadow","vnmi","flexpriority","ept","vpid","fsgsbase","tsc_adjust","bmi1","avx2","smep","bmi2","erms","invpcid"]},"4":{"vendor_id":"GenuineIntel","family":"6","model":"63","model_name":"Intel(R) Xeon(R) CPU E5-2680 v3 @ 2.50GHz","stepping":"2","mhz":"1200.097","cache_size":"30720 KB","physical_id":"0","core_id":"4","cores":"12","flags":["fpu","vme","de","pse","tsc","msr","pae","mce","cx8","apic","sep","mtrr","pge","mca","cmov","pat","pse36","clflush","dts","acpi","mmx","fxsr","sse","sse2","ss","ht","tm","pbe","syscall","nx","pdpe1gb","rdtscp","lm","constant_tsc","arch_perfmon","pebs","bts","rep_good","nopl","xtopology","nonstop_tsc","aperfmperf","eagerfpu","pni","pclmulqdq","dtes64","monitor","ds_cpl","vmx","smx","est","tm2","ssse3","fma","cx16","xtpr","pdcm","pcid","dca","sse4_1","sse4_2","x2apic","movbe","popcnt","tsc_deadline_timer","aes","xsave","avx","f16c","rdrand","lahf_lm","abm","ida","arat","epb","xsaveopt","pln","pts","dtherm","tpr_shadow","vnmi","flexpriority","ept","vpid","fsgsbase","tsc_adjust","bmi1","avx2","smep","bmi2","erms","invpcid"]},"5":{"vendor_id":"GenuineIntel","family":"6","model":"63","model_name":"Intel(R) Xeon(R) CPU E5-2680 v3 @ 2.50GHz","stepping":"2","mhz":"1200.195","cache_size":"30720 KB","physical_id":"0","core_id":"5","cores":"12","flags":["fpu","vme","de","pse","tsc","msr","pae","mce","cx8","apic","sep","mtrr","pge","mca","cmov","pat","pse36","clflush","dts","acpi","mmx","fxsr","sse","sse2","ss","ht","tm","pbe","syscall","nx","pdpe1gb","rdtscp","lm","constant_tsc","arch_perfmon","pebs","bts","rep_good","nopl","xtopology","nonstop_tsc","aperfmperf","eagerfpu","pni","pclmulqdq","dtes64","monitor","ds_cpl","vmx","smx","est","tm2","ssse3","fma","cx16","xtpr","pdcm","pcid","dca","sse4_1","sse4_2","x2apic","movbe","popcnt","tsc_deadline_timer","aes","xsave","avx","f16c","rdrand","lahf_lm","abm","ida","arat","epb","xsaveopt","pln","pts","dtherm","tpr_shadow","vnmi","flexpriority","ept","vpid","fsgsbase","tsc_adjust","bmi1","avx2","smep","bmi2","erms","invpcid"]},"6":{"vendor_id":"GenuineIntel","family":"6","model":"63","model_name":"Intel(R) Xeon(R) CPU E5-2680 v3 @ 2.50GHz","stepping":"2","mhz":"1200.000","cache_size":"30720 KB","physical_id":"0","core_id":"8","cores":"12","flags":["fpu","vme","de","pse","tsc","msr","pae","mce","cx8","apic","sep","mtrr","pge","mca","cmov","pat","pse36","clflush","dts","acpi","mmx","fxsr","sse","sse2","ss","ht","tm","pbe","syscall","nx","pdpe1gb","rdtscp","lm","constant_tsc","arch_perfmon","pebs","bts","rep_good","nopl","xtopology","nonstop_tsc","aperfmperf","eagerfpu","pni","pclmulqdq","dtes64","monitor","ds_cpl","vmx","smx","est","tm2","ssse3","fma","cx16","xtpr","pdcm","pcid","dca","sse4_1","sse4_2","x2apic","movbe","popcnt","tsc_deadline_timer","aes","xsave","avx","f16c","rdrand","lahf_lm","abm","ida","arat","epb","xsaveopt","pln","pts","dtherm","tpr_shadow","vnmi","flexpriority","ept","vpid","fsgsbase","tsc_adjust","bmi1","avx2","smep","bmi2","erms","invpcid"]},"7":{"vendor_id":"GenuineIntel","family":"6","model":"63","model_name":"Intel(R) Xeon(R) CPU E5-2680 v3 @ 2.50GHz","stepping":"2","mhz":"1200.000","cache_size":"30720 KB","physical_id":"0","core_id":"9","cores":"12","flags":["fpu","vme","de","pse","tsc","msr","pae","mce","cx8","apic","sep","mtrr","pge","mca","cmov","pat","pse36","clflush","dts","acpi","mmx","fxsr","sse","sse2","ss","ht","tm","pbe","syscall","nx","pdpe1gb","rdtscp","lm","constant_tsc","arch_perfmon","pebs","bts","rep_good","nopl","xtopology","nonstop_tsc","aperfmperf","eagerfpu","pni","pclmulqdq","dtes64","monitor","ds_cpl","vmx","smx","est","tm2","ssse3","fma","cx16","xtpr","pdcm","pcid","dca","sse4_1","sse4_2","x2apic","movbe","popcnt","tsc_deadline_timer","aes","xsave","avx","f16c","rdrand","lahf_lm","abm","ida","arat","epb","xsaveopt","pln","pts","dtherm","tpr_shadow","vnmi","flexpriority","ept","vpid","fsgsbase","tsc_adjust","bmi1","avx2","smep","bmi2","erms","invpcid"]},"8":{"vendor_id":"GenuineIntel","family":"6","model":"63","model_name":"Intel(R) Xeon(R) CPU E5-2680 v3 @ 2.50GHz","stepping":"2","mhz":"1200.000","cache_size":"30720 KB","physical_id":"0","core_id":"10","cores":"12","flags":["fpu","vme","de","pse","tsc","msr","pae","mce","cx8","apic","sep","mtrr","pge","mca","cmov","pat","pse36","clflush","dts","acpi","mmx","fxsr","sse","sse2","ss","ht","tm","pbe","syscall","nx","pdpe1gb","rdtscp","lm","constant_tsc","arch_perfmon","pebs","bts","rep_good","nopl","xtopology","nonstop_tsc","aperfmperf","eagerfpu","pni","pclmulqdq","dtes64","monitor","ds_cpl","vmx","smx","est","tm2","ssse3","fma","cx16","xtpr","pdcm","pcid","dca","sse4_1","sse4_2","x2apic","movbe","popcnt","tsc_deadline_timer","aes","xsave","avx","f16c","rdrand","lahf_lm","abm","ida","arat","epb","xsaveopt","pln","pts","dtherm","tpr_shadow","vnmi","flexpriority","ept","vpid","fsgsbase","tsc_adjust","bmi1","avx2","smep","bmi2","erms","invpcid"]},"9":{"vendor_id":"GenuineIntel","family":"6","model":"63","model_name":"Intel(R) Xeon(R) CPU E5-2680 v3 @ 2.50GHz","stepping":"2","mhz":"1200.000","cache_size":"30720 KB","physical_id":"0","core_id":"11","cores":"12","flags":["fpu","vme","de","pse","tsc","msr","pae","mce","cx8","apic","sep","mtrr","pge","mca","cmov","pat","pse36","clflush","dts","acpi","mmx","fxsr","sse","sse2","ss","ht","tm","pbe","syscall","nx","pdpe1gb","rdtscp","lm","constant_tsc","arch_perfmon","pebs","bts","rep_good","nopl","xtopology","nonstop_tsc","aperfmperf","eagerfpu","pni","pclmulqdq","dtes64","monitor","ds_cpl","vmx","smx","est","tm2","ssse3","fma","cx16","xtpr","pdcm","pcid","dca","sse4_1","sse4_2","x2apic","movbe","popcnt","tsc_deadline_timer","aes","xsave","avx","f16c","rdrand","lahf_lm","abm","ida","arat","epb","xsaveopt","pln","pts","dtherm","tpr_shadow","vnmi","flexpriority","ept","vpid","fsgsbase","tsc_adjust","bmi1","avx2","smep","bmi2","erms","invpcid"]},"10":{"vendor_id":"GenuineIntel","family":"6","model":"63","model_name":"Intel(R) Xeon(R) CPU E5-2680 v3 @ 2.50GHz","stepping":"2","mhz":"1200.000","cache_size":"30720 KB","physical_id":"0","core_id":"12","cores":"12","flags":["fpu","vme","de","pse","tsc","msr","pae","mce","cx8","apic","sep","mtrr","pge","mca","cmov","pat","pse36","clflush","dts","acpi","mmx","fxsr","sse","sse2","ss","ht","tm","pbe","syscall","nx","pdpe1gb","rdtscp","lm","constant_tsc","arch_perfmon","pebs","bts","rep_good","nopl","xtopology","nonstop_tsc","aperfmperf","eagerfpu","pni","pclmulqdq","dtes64","monitor","ds_cpl","vmx","smx","est","tm2","ssse3","fma","cx16","xtpr","pdcm","pcid","dca","sse4_1","sse4_2","x2apic","movbe","popcnt","tsc_deadline_timer","aes","xsave","avx","f16c","rdrand","lahf_lm","abm","ida","arat","epb","xsaveopt","pln","pts","dtherm","tpr_shadow","vnmi","flexpriority","ept","vpid","fsgsbase","tsc_adjust","bmi1","avx2","smep","bmi2","erms","invpcid"]},"11":{"vendor_id":"GenuineIntel","family":"6","model":"63","model_name":"Intel(R) Xeon(R) CPU E5-2680 v3 @ 2.50GHz","stepping":"2","mhz":"1200.000","cache_size":"30720 KB","physical_id":"0","core_id":"13","cores":"12","flags":["fpu","vme","de","pse","tsc","msr","pae","mce","cx8","apic","sep","mtrr","pge","mca","cmov","pat","pse36","clflush","dts","acpi","mmx","fxsr","sse","sse2","ss","ht","tm","pbe","syscall","nx","pdpe1gb","rdtscp","lm","constant_tsc","arch_perfmon","pebs","bts","rep_good","nopl","xtopology","nonstop_tsc","aperfmperf","eagerfpu","pni","pclmulqdq","dtes64","monitor","ds_cpl","vmx","smx","est","tm2","ssse3","fma","cx16","xtpr","pdcm","pcid","dca","sse4_1","sse4_2","x2apic","movbe","popcnt","tsc_deadline_timer","aes","xsave","avx","f16c","rdrand","lahf_lm","abm","ida","arat","epb","xsaveopt","pln","pts","dtherm","tpr_shadow","vnmi","flexpriority","ept","vpid","fsgsbase","tsc_adjust","bmi1","avx2","smep","bmi2","erms","invpcid"]},"12":{"vendor_id":"GenuineIntel","family":"6","model":"63","model_name":"Intel(R) Xeon(R) CPU E5-2680 v3 @ 2.50GHz","stepping":"2","mhz":"1200.000","cache_size":"30720 KB","physical_id":"1","core_id":"0","cores":"12","flags":["fpu","vme","de","pse","tsc","msr","pae","mce","cx8","apic","sep","mtrr","pge","mca","cmov","pat","pse36","clflush","dts","acpi","mmx","fxsr","sse","sse2","ss","ht","tm","pbe","syscall","nx","pdpe1gb","rdtscp","lm","constant_tsc","arch_perfmon","pebs","bts","rep_good","nopl","xtopology","nonstop_tsc","aperfmperf","eagerfpu","pni","pclmulqdq","dtes64","monitor","ds_cpl","vmx","smx","est","tm2","ssse3","fma","cx16","xtpr","pdcm","pcid","dca","sse4_1","sse4_2","x2apic","movbe","popcnt","tsc_deadline_timer","aes","xsave","avx","f16c","rdrand","lahf_lm","abm","ida","arat","epb","xsaveopt","pln","pts","dtherm","tpr_shadow","vnmi","flexpriority","ept","vpid","fsgsbase","tsc_adjust","bmi1","avx2","smep","bmi2","erms","invpcid"]},"13":{"vendor_id":"GenuineIntel","family":"6","model":"63","model_name":"Intel(R) Xeon(R) CPU E5-2680 v3 @ 2.50GHz","stepping":"2","mhz":"1200.097","cache_size":"30720 KB","physical_id":"1","core_id":"1","cores":"12","flags":["fpu","vme","de","pse","tsc","msr","pae","mce","cx8","apic","sep","mtrr","pge","mca","cmov","pat","pse36","clflush","dts","acpi","mmx","fxsr","sse","sse2","ss","ht","tm","pbe","syscall","nx","pdpe1gb","rdtscp","lm","constant_tsc","arch_perfmon","pebs","bts","rep_good","nopl","xtopology","nonstop_tsc","aperfmperf","eagerfpu","pni","pclmulqdq","dtes64","monitor","ds_cpl","vmx","smx","est","tm2","ssse3","fma","cx16","xtpr","pdcm","pcid","dca","sse4_1","sse4_2","x2apic","movbe","popcnt","tsc_deadline_timer","aes","xsave","avx","f16c","rdrand","lahf_lm","abm","ida","arat","epb","xsaveopt","pln","pts","dtherm","tpr_shadow","vnmi","flexpriority","ept","vpid","fsgsbase","tsc_adjust","bmi1","avx2","smep","bmi2","erms","invpcid"]},"14":{"vendor_id":"GenuineIntel","family":"6","model":"63","model_name":"Intel(R) Xeon(R) CPU E5-2680 v3 @ 2.50GHz","stepping":"2","mhz":"1200.000","cache_size":"30720 KB","physical_id":"1","core_id":"2","cores":"12","flags":["fpu","vme","de","pse","tsc","msr","pae","mce","cx8","apic","sep","mtrr","pge","mca","cmov","pat","pse36","clflush","dts","acpi","mmx","fxsr","sse","sse2","ss","ht","tm","pbe","syscall","nx","pdpe1gb","rdtscp","lm","constant_tsc","arch_perfmon","pebs","bts","rep_good","nopl","xtopology","nonstop_tsc","aperfmperf","eagerfpu","pni","pclmulqdq","dtes64","monitor","ds_cpl","vmx","smx","est","tm2","ssse3","fma","cx16","xtpr","pdcm","pcid","dca","sse4_1","sse4_2","x2apic","movbe","popcnt","tsc_deadline_timer","aes","xsave","avx","f16c","rdrand","lahf_lm","abm","ida","arat","epb","xsaveopt","pln","pts","dtherm","tpr_shadow","vnmi","flexpriority","ept","vpid","fsgsbase","tsc_adjust","bmi1","avx2","smep","bmi2","erms","invpcid"]},"15":{"vendor_id":"GenuineIntel","family":"6","model":"63","model_name":"Intel(R) Xeon(R) CPU E5-2680 v3 @ 2.50GHz","stepping":"2","mhz":"1200.000","cache_size":"30720 KB","physical_id":"1","core_id":"3","cores":"12","flags":["fpu","vme","de","pse","tsc","msr","pae","mce","cx8","apic","sep","mtrr","pge","mca","cmov","pat","pse36","clflush","dts","acpi","mmx","fxsr","sse","sse2","ss","ht","tm","pbe","syscall","nx","pdpe1gb","rdtscp","lm","constant_tsc","arch_perfmon","pebs","bts","rep_good","nopl","xtopology","nonstop_tsc","aperfmperf","eagerfpu","pni","pclmulqdq","dtes64","monitor","ds_cpl","vmx","smx","est","tm2","ssse3","fma","cx16","xtpr","pdcm","pcid","dca","sse4_1","sse4_2","x2apic","movbe","popcnt","tsc_deadline_timer","aes","xsave","avx","f16c","rdrand","lahf_lm","abm","ida","arat","epb","xsaveopt","pln","pts","dtherm","tpr_shadow","vnmi","flexpriority","ept","vpid","fsgsbase","tsc_adjust","bmi1","avx2","smep","bmi2","erms","invpcid"]},"16":{"vendor_id":"GenuineIntel","family":"6","model":"63","model_name":"Intel(R) Xeon(R) CPU E5-2680 v3 @ 2.50GHz","stepping":"2","mhz":"1200.000","cache_size":"30720 KB","physical_id":"1","core_id":"4","cores":"12","flags":["fpu","vme","de","pse","tsc","msr","pae","mce","cx8","apic","sep","mtrr","pge","mca","cmov","pat","pse36","clflush","dts","acpi","mmx","fxsr","sse","sse2","ss","ht","tm","pbe","syscall","nx","pdpe1gb","rdtscp","lm","constant_tsc","arch_perfmon","pebs","bts","rep_good","nopl","xtopology","nonstop_tsc","aperfmperf","eagerfpu","pni","pclmulqdq","dtes64","monitor","ds_cpl","vmx","smx","est","tm2","ssse3","fma","cx16","xtpr","pdcm","pcid","dca","sse4_1","sse4_2","x2apic","movbe","popcnt","tsc_deadline_timer","aes","xsave","avx","f16c","rdrand","lahf_lm","abm","ida","arat","epb","xsaveopt","pln","pts","dtherm","tpr_shadow","vnmi","flexpriority","ept","vpid","fsgsbase","tsc_adjust","bmi1","avx2","smep","bmi2","erms","invpcid"]},"17":{"vendor_id":"GenuineIntel","family":"6","model":"63","model_name":"Intel(R) Xeon(R) CPU E5-2680 v3 @ 2.50GHz","stepping":"2","mhz":"1200.000","cache_size":"30720 KB","physical_id":"1","core_id":"5","cores":"12","flags":["fpu","vme","de","pse","tsc","msr","pae","mce","cx8","apic","sep","mtrr","pge","mca","cmov","pat","pse36","clflush","dts","acpi","mmx","fxsr","sse","sse2","ss","ht","tm","pbe","syscall","nx","pdpe1gb","rdtscp","lm","constant_tsc","arch_perfmon","pebs","bts","rep_good","nopl","xtopology","nonstop_tsc","aperfmperf","eagerfpu","pni","pclmulqdq","dtes64","monitor","ds_cpl","vmx","smx","est","tm2","ssse3","fma","cx16","xtpr","pdcm","pcid","dca","sse4_1","sse4_2","x2apic","movbe","popcnt","tsc_deadline_timer","aes","xsave","avx","f16c","rdrand","lahf_lm","abm","ida","arat","epb","xsaveopt","pln","pts","dtherm","tpr_shadow","vnmi","flexpriority","ept","vpid","fsgsbase","tsc_adjust","bmi1","avx2","smep","bmi2","erms","invpcid"]},"18":{"vendor_id":"GenuineIntel","family":"6","model":"63","model_name":"Intel(R) Xeon(R) CPU E5-2680 v3 @ 2.50GHz","stepping":"2","mhz":"1200.000","cache_size":"30720 KB","physical_id":"1","core_id":"8","cores":"12","flags":["fpu","vme","de","pse","tsc","msr","pae","mce","cx8","apic","sep","mtrr","pge","mca","cmov","pat","pse36","clflush","dts","acpi","mmx","fxsr","sse","sse2","ss","ht","tm","pbe","syscall","nx","pdpe1gb","rdtscp","lm","constant_tsc","arch_perfmon","pebs","bts","rep_good","nopl","xtopology","nonstop_tsc","aperfmperf","eagerfpu","pni","pclmulqdq","dtes64","monitor","ds_cpl","vmx","smx","est","tm2","ssse3","fma","cx16","xtpr","pdcm","pcid","dca","sse4_1","sse4_2","x2apic","movbe","popcnt","tsc_deadline_timer","aes","xsave","avx","f16c","rdrand","lahf_lm","abm","ida","arat","epb","xsaveopt","pln","pts","dtherm","tpr_shadow","vnmi","flexpriority","ept","vpid","fsgsbase","tsc_adjust","bmi1","avx2","smep","bmi2","erms","invpcid"]},"19":{"vendor_id":"GenuineIntel","family":"6","model":"63","model_name":"Intel(R) Xeon(R) CPU E5-2680 v3 @ 2.50GHz","stepping":"2","mhz":"1200.000","cache_size":"30720 KB","physical_id":"1","core_id":"9","cores":"12","flags":["fpu","vme","de","pse","tsc","msr","pae","mce","cx8","apic","sep","mtrr","pge","mca","cmov","pat","pse36","clflush","dts","acpi","mmx","fxsr","sse","sse2","ss","ht","tm","pbe","syscall","nx","pdpe1gb","rdtscp","lm","constant_tsc","arch_perfmon","pebs","bts","rep_good","nopl","xtopology","nonstop_tsc","aperfmperf","eagerfpu","pni","pclmulqdq","dtes64","monitor","ds_cpl","vmx","smx","est","tm2","ssse3","fma","cx16","xtpr","pdcm","pcid","dca","sse4_1","sse4_2","x2apic","movbe","popcnt","tsc_deadline_timer","aes","xsave","avx","f16c","rdrand","lahf_lm","abm","ida","arat","epb","xsaveopt","pln","pts","dtherm","tpr_shadow","vnmi","flexpriority","ept","vpid","fsgsbase","tsc_adjust","bmi1","avx2","smep","bmi2","erms","invpcid"]},"20":{"vendor_id":"GenuineIntel","family":"6","model":"63","model_name":"Intel(R) Xeon(R) CPU E5-2680 v3 @ 2.50GHz","stepping":"2","mhz":"1200.000","cache_size":"30720 KB","physical_id":"1","core_id":"10","cores":"12","flags":["fpu","vme","de","pse","tsc","msr","pae","mce","cx8","apic","sep","mtrr","pge","mca","cmov","pat","pse36","clflush","dts","acpi","mmx","fxsr","sse","sse2","ss","ht","tm","pbe","syscall","nx","pdpe1gb","rdtscp","lm","constant_tsc","arch_perfmon","pebs","bts","rep_good","nopl","xtopology","nonstop_tsc","aperfmperf","eagerfpu","pni","pclmulqdq","dtes64","monitor","ds_cpl","vmx","smx","est","tm2","ssse3","fma","cx16","xtpr","pdcm","pcid","dca","sse4_1","sse4_2","x2apic","movbe","popcnt","tsc_deadline_timer","aes","xsave","avx","f16c","rdrand","lahf_lm","abm","ida","arat","epb","xsaveopt","pln","pts","dtherm","tpr_shadow","vnmi","flexpriority","ept","vpid","fsgsbase","tsc_adjust","bmi1","avx2","smep","bmi2","erms","invpcid"]},"21":{"vendor_id":"GenuineIntel","family":"6","model":"63","model_name":"Intel(R) Xeon(R) CPU E5-2680 v3 @ 2.50GHz","stepping":"2","mhz":"1200.000","cache_size":"30720 KB","physical_id":"1","core_id":"11","cores":"12","flags":["fpu","vme","de","pse","tsc","msr","pae","mce","cx8","apic","sep","mtrr","pge","mca","cmov","pat","pse36","clflush","dts","acpi","mmx","fxsr","sse","sse2","ss","ht","tm","pbe","syscall","nx","pdpe1gb","rdtscp","lm","constant_tsc","arch_perfmon","pebs","bts","rep_good","nopl","xtopology","nonstop_tsc","aperfmperf","eagerfpu","pni","pclmulqdq","dtes64","monitor","ds_cpl","vmx","smx","est","tm2","ssse3","fma","cx16","xtpr","pdcm","pcid","dca","sse4_1","sse4_2","x2apic","movbe","popcnt","tsc_deadline_timer","aes","xsave","avx","f16c","rdrand","lahf_lm","abm","ida","arat","epb","xsaveopt","pln","pts","dtherm","tpr_shadow","vnmi","flexpriority","ept","vpid","fsgsbase","tsc_adjust","bmi1","avx2","smep","bmi2","erms","invpcid"]},"22":{"vendor_id":"GenuineIntel","family":"6","model":"63","model_name":"Intel(R) Xeon(R) CPU E5-2680 v3 @ 2.50GHz","stepping":"2","mhz":"1199.902","cache_size":"30720 KB","physical_id":"1","core_id":"12","cores":"12","flags":["fpu","vme","de","pse","tsc","msr","pae","mce","cx8","apic","sep","mtrr","pge","mca","cmov","pat","pse36","clflush","dts","acpi","mmx","fxsr","sse","sse2","ss","ht","tm","pbe","syscall","nx","pdpe1gb","rdtscp","lm","constant_tsc","arch_perfmon","pebs","bts","rep_good","nopl","xtopology","nonstop_tsc","aperfmperf","eagerfpu","pni","pclmulqdq","dtes64","monitor","ds_cpl","vmx","smx","est","tm2","ssse3","fma","cx16","xtpr","pdcm","pcid","dca","sse4_1","sse4_2","x2apic","movbe","popcnt","tsc_deadline_timer","aes","xsave","avx","f16c","rdrand","lahf_lm","abm","ida","arat","epb","xsaveopt","pln","pts","dtherm","tpr_shadow","vnmi","flexpriority","ept","vpid","fsgsbase","tsc_adjust","bmi1","avx2","smep","bmi2","erms","invpcid"]},"23":{"vendor_id":"GenuineIntel","family":"6","model":"63","model_name":"Intel(R) Xeon(R) CPU E5-2680 v3 @ 2.50GHz","stepping":"2","mhz":"1200.000","cache_size":"30720 KB","physical_id":"1","core_id":"13","cores":"12","flags":["fpu","vme","de","pse","tsc","msr","pae","mce","cx8","apic","sep","mtrr","pge","mca","cmov","pat","pse36","clflush","dts","acpi","mmx","fxsr","sse","sse2","ss","ht","tm","pbe","syscall","nx","pdpe1gb","rdtscp","lm","constant_tsc","arch_perfmon","pebs","bts","rep_good","nopl","xtopology","nonstop_tsc","aperfmperf","eagerfpu","pni","pclmulqdq","dtes64","monitor","ds_cpl","vmx","smx","est","tm2","ssse3","fma","cx16","xtpr","pdcm","pcid","dca","sse4_1","sse4_2","x2apic","movbe","popcnt","tsc_deadline_timer","aes","xsave","avx","f16c","rdrand","lahf_lm","abm","ida","arat","epb","xsaveopt","pln","pts","dtherm","tpr_shadow","vnmi","flexpriority","ept","vpid","fsgsbase","tsc_adjust","bmi1","avx2","smep","bmi2","erms","invpcid"]},"24":{"vendor_id":"GenuineIntel","family":"6","model":"63","model_name":"Intel(R) Xeon(R) CPU E5-2680 v3 @ 2.50GHz","stepping":"2","mhz":"1200.097","cache_size":"30720 KB","physical_id":"0","core_id":"0","cores":"12","flags":["fpu","vme","de","pse","tsc","msr","pae","mce","cx8","apic","sep","mtrr","pge","mca","cmov","pat","pse36","clflush","dts","acpi","mmx","fxsr","sse","sse2","ss","ht","tm","pbe","syscall","nx","pdpe1gb","rdtscp","lm","constant_tsc","arch_perfmon","pebs","bts","rep_good","nopl","xtopology","nonstop_tsc","aperfmperf","eagerfpu","pni","pclmulqdq","dtes64","monitor","ds_cpl","vmx","smx","est","tm2","ssse3","fma","cx16","xtpr","pdcm","pcid","dca","sse4_1","sse4_2","x2apic","movbe","popcnt","tsc_deadline_timer","aes","xsave","avx","f16c","rdrand","lahf_lm","abm","ida","arat","epb","xsaveopt","pln","pts","dtherm","tpr_shadow","vnmi","flexpriority","ept","vpid","fsgsbase","tsc_adjust","bmi1","avx2","smep","bmi2","erms","invpcid"]},"25":{"vendor_id":"GenuineIntel","family":"6","model":"63","model_name":"Intel(R) Xeon(R) CPU E5-2680 v3 @ 2.50GHz","stepping":"2","mhz":"1200.000","cache_size":"30720 KB","physical_id":"0","core_id":"1","cores":"12","flags":["fpu","vme","de","pse","tsc","msr","pae","mce","cx8","apic","sep","mtrr","pge","mca","cmov","pat","pse36","clflush","dts","acpi","mmx","fxsr","sse","sse2","ss","ht","tm","pbe","syscall","nx","pdpe1gb","rdtscp","lm","constant_tsc","arch_perfmon","pebs","bts","rep_good","nopl","xtopology","nonstop_tsc","aperfmperf","eagerfpu","pni","pclmulqdq","dtes64","monitor","ds_cpl","vmx","smx","est","tm2","ssse3","fma","cx16","xtpr","pdcm","pcid","dca","sse4_1","sse4_2","x2apic","movbe","popcnt","tsc_deadline_timer","aes","xsave","avx","f16c","rdrand","lahf_lm","abm","ida","arat","epb","xsaveopt","pln","pts","dtherm","tpr_shadow","vnmi","flexpriority","ept","vpid","fsgsbase","tsc_adjust","bmi1","avx2","smep","bmi2","erms","invpcid"]},"26":{"vendor_id":"GenuineIntel","family":"6","model":"63","model_name":"Intel(R) Xeon(R) CPU E5-2680 v3 @ 2.50GHz","stepping":"2","mhz":"1200.195","cache_size":"30720 KB","physical_id":"0","core_id":"2","cores":"12","flags":["fpu","vme","de","pse","tsc","msr","pae","mce","cx8","apic","sep","mtrr","pge","mca","cmov","pat","pse36","clflush","dts","acpi","mmx","fxsr","sse","sse2","ss","ht","tm","pbe","syscall","nx","pdpe1gb","rdtscp","lm","constant_tsc","arch_perfmon","pebs","bts","rep_good","nopl","xtopology","nonstop_tsc","aperfmperf","eagerfpu","pni","pclmulqdq","dtes64","monitor","ds_cpl","vmx","smx","est","tm2","ssse3","fma","cx16","xtpr","pdcm","pcid","dca","sse4_1","sse4_2","x2apic","movbe","popcnt","tsc_deadline_timer","aes","xsave","avx","f16c","rdrand","lahf_lm","abm","ida","arat","epb","xsaveopt","pln","pts","dtherm","tpr_shadow","vnmi","flexpriority","ept","vpid","fsgsbase","tsc_adjust","bmi1","avx2","smep","bmi2","erms","invpcid"]},"27":{"vendor_id":"GenuineIntel","family":"6","model":"63","model_name":"Intel(R) Xeon(R) CPU E5-2680 v3 @ 2.50GHz","stepping":"2","mhz":"1200.097","cache_size":"30720 KB","physical_id":"0","core_id":"3","cores":"12","flags":["fpu","vme","de","pse","tsc","msr","pae","mce","cx8","apic","sep","mtrr","pge","mca","cmov","pat","pse36","clflush","dts","acpi","mmx","fxsr","sse","sse2","ss","ht","tm","pbe","syscall","nx","pdpe1gb","rdtscp","lm","constant_tsc","arch_perfmon","pebs","bts","rep_good","nopl","xtopology","nonstop_tsc","aperfmperf","eagerfpu","pni","pclmulqdq","dtes64","monitor","ds_cpl","vmx","smx","est","tm2","ssse3","fma","cx16","xtpr","pdcm","pcid","dca","sse4_1","sse4_2","x2apic","movbe","popcnt","tsc_deadline_timer","aes","xsave","avx","f16c","rdrand","lahf_lm","abm","ida","arat","epb","xsaveopt","pln","pts","dtherm","tpr_shadow","vnmi","flexpriority","ept","vpid","fsgsbase","tsc_adjust","bmi1","avx2","smep","bmi2","erms","invpcid"]},"28":{"vendor_id":"GenuineIntel","family":"6","model":"63","model_name":"Intel(R) Xeon(R) CPU E5-2680 v3 @ 2.50GHz","stepping":"2","mhz":"1200.000","cache_size":"30720 KB","physical_id":"0","core_id":"4","cores":"12","flags":["fpu","vme","de","pse","tsc","msr","pae","mce","cx8","apic","sep","mtrr","pge","mca","cmov","pat","pse36","clflush","dts","acpi","mmx","fxsr","sse","sse2","ss","ht","tm","pbe","syscall","nx","pdpe1gb","rdtscp","lm","constant_tsc","arch_perfmon","pebs","bts","rep_good","nopl","xtopology","nonstop_tsc","aperfmperf","eagerfpu","pni","pclmulqdq","dtes64","monitor","ds_cpl","vmx","smx","est","tm2","ssse3","fma","cx16","xtpr","pdcm","pcid","dca","sse4_1","sse4_2","x2apic","movbe","popcnt","tsc_deadline_timer","aes","xsave","avx","f16c","rdrand","lahf_lm","abm","ida","arat","epb","xsaveopt","pln","pts","dtherm","tpr_shadow","vnmi","flexpriority","ept","vpid","fsgsbase","tsc_adjust","bmi1","avx2","smep","bmi2","erms","invpcid"]},"29":{"vendor_id":"GenuineIntel","family":"6","model":"63","model_name":"Intel(R) Xeon(R) CPU E5-2680 v3 @ 2.50GHz","stepping":"2","mhz":"1200.000","cache_size":"30720 KB","physical_id":"0","core_id":"5","cores":"12","flags":["fpu","vme","de","pse","tsc","msr","pae","mce","cx8","apic","sep","mtrr","pge","mca","cmov","pat","pse36","clflush","dts","acpi","mmx","fxsr","sse","sse2","ss","ht","tm","pbe","syscall","nx","pdpe1gb","rdtscp","lm","constant_tsc","arch_perfmon","pebs","bts","rep_good","nopl","xtopology","nonstop_tsc","aperfmperf","eagerfpu","pni","pclmulqdq","dtes64","monitor","ds_cpl","vmx","smx","est","tm2","ssse3","fma","cx16","xtpr","pdcm","pcid","dca","sse4_1","sse4_2","x2apic","movbe","popcnt","tsc_deadline_timer","aes","xsave","avx","f16c","rdrand","lahf_lm","abm","ida","arat","epb","xsaveopt","pln","pts","dtherm","tpr_shadow","vnmi","flexpriority","ept","vpid","fsgsbase","tsc_adjust","bmi1","avx2","smep","bmi2","erms","invpcid"]},"30":{"vendor_id":"GenuineIntel","family":"6","model":"63","model_name":"Intel(R) Xeon(R) CPU E5-2680 v3 @ 2.50GHz","stepping":"2","mhz":"1200.000","cache_size":"30720 KB","physical_id":"0","core_id":"8","cores":"12","flags":["fpu","vme","de","pse","tsc","msr","pae","mce","cx8","apic","sep","mtrr","pge","mca","cmov","pat","pse36","clflush","dts","acpi","mmx","fxsr","sse","sse2","ss","ht","tm","pbe","syscall","nx","pdpe1gb","rdtscp","lm","constant_tsc","arch_perfmon","pebs","bts","rep_good","nopl","xtopology","nonstop_tsc","aperfmperf","eagerfpu","pni","pclmulqdq","dtes64","monitor","ds_cpl","vmx","smx","est","tm2","ssse3","fma","cx16","xtpr","pdcm","pcid","dca","sse4_1","sse4_2","x2apic","movbe","popcnt","tsc_deadline_timer","aes","xsave","avx","f16c","rdrand","lahf_lm","abm","ida","arat","epb","xsaveopt","pln","pts","dtherm","tpr_shadow","vnmi","flexpriority","ept","vpid","fsgsbase","tsc_adjust","bmi1","avx2","smep","bmi2","erms","invpcid"]},"31":{"vendor_id":"GenuineIntel","family":"6","model":"63","model_name":"Intel(R) Xeon(R) CPU E5-2680 v3 @ 2.50GHz","stepping":"2","mhz":"1204.296","cache_size":"30720 KB","physical_id":"0","core_id":"9","cores":"12","flags":["fpu","vme","de","pse","tsc","msr","pae","mce","cx8","apic","sep","mtrr","pge","mca","cmov","pat","pse36","clflush","dts","acpi","mmx","fxsr","sse","sse2","ss","ht","tm","pbe","syscall","nx","pdpe1gb","rdtscp","lm","constant_tsc","arch_perfmon","pebs","bts","rep_good","nopl","xtopology","nonstop_tsc","aperfmperf","eagerfpu","pni","pclmulqdq","dtes64","monitor","ds_cpl","vmx","smx","est","tm2","ssse3","fma","cx16","xtpr","pdcm","pcid","dca","sse4_1","sse4_2","x2apic","movbe","popcnt","tsc_deadline_timer","aes","xsave","avx","f16c","rdrand","lahf_lm","abm","ida","arat","epb","xsaveopt","pln","pts","dtherm","tpr_shadow","vnmi","flexpriority","ept","vpid","fsgsbase","tsc_adjust","bmi1","avx2","smep","bmi2","erms","invpcid"]},"32":{"vendor_id":"GenuineIntel","family":"6","model":"63","model_name":"Intel(R) Xeon(R) CPU E5-2680 v3 @ 2.50GHz","stepping":"2","mhz":"1200.000","cache_size":"30720 KB","physical_id":"0","core_id":"10","cores":"12","flags":["fpu","vme","de","pse","tsc","msr","pae","mce","cx8","apic","sep","mtrr","pge","mca","cmov","pat","pse36","clflush","dts","acpi","mmx","fxsr","sse","sse2","ss","ht","tm","pbe","syscall","nx","pdpe1gb","rdtscp","lm","constant_tsc","arch_perfmon","pebs","bts","rep_good","nopl","xtopology","nonstop_tsc","aperfmperf","eagerfpu","pni","pclmulqdq","dtes64","monitor","ds_cpl","vmx","smx","est","tm2","ssse3","fma","cx16","xtpr","pdcm","pcid","dca","sse4_1","sse4_2","x2apic","movbe","popcnt","tsc_deadline_timer","aes","xsave","avx","f16c","rdrand","lahf_lm","abm","ida","arat","epb","xsaveopt","pln","pts","dtherm","tpr_shadow","vnmi","flexpriority","ept","vpid","fsgsbase","tsc_adjust","bmi1","avx2","smep","bmi2","erms","invpcid"]},"33":{"vendor_id":"GenuineIntel","family":"6","model":"63","model_name":"Intel(R) Xeon(R) CPU E5-2680 v3 @ 2.50GHz","stepping":"2","mhz":"1201.074","cache_size":"30720 KB","physical_id":"0","core_id":"11","cores":"12","flags":["fpu","vme","de","pse","tsc","msr","pae","mce","cx8","apic","sep","mtrr","pge","mca","cmov","pat","pse36","clflush","dts","acpi","mmx","fxsr","sse","sse2","ss","ht","tm","pbe","syscall","nx","pdpe1gb","rdtscp","lm","constant_tsc","arch_perfmon","pebs","bts","rep_good","nopl","xtopology","nonstop_tsc","aperfmperf","eagerfpu","pni","pclmulqdq","dtes64","monitor","ds_cpl","vmx","smx","est","tm2","ssse3","fma","cx16","xtpr","pdcm","pcid","dca","sse4_1","sse4_2","x2apic","movbe","popcnt","tsc_deadline_timer","aes","xsave","avx","f16c","rdrand","lahf_lm","abm","ida","arat","epb","xsaveopt","pln","pts","dtherm","tpr_shadow","vnmi","flexpriority","ept","vpid","fsgsbase","tsc_adjust","bmi1","avx2","smep","bmi2","erms","invpcid"]},"34":{"vendor_id":"GenuineIntel","family":"6","model":"63","model_name":"Intel(R) Xeon(R) CPU E5-2680 v3 @ 2.50GHz","stepping":"2","mhz":"1204.296","cache_size":"30720 KB","physical_id":"0","core_id":"12","cores":"12","flags":["fpu","vme","de","pse","tsc","msr","pae","mce","cx8","apic","sep","mtrr","pge","mca","cmov","pat","pse36","clflush","dts","acpi","mmx","fxsr","sse","sse2","ss","ht","tm","pbe","syscall","nx","pdpe1gb","rdtscp","lm","constant_tsc","arch_perfmon","pebs","bts","rep_good","nopl","xtopology","nonstop_tsc","aperfmperf","eagerfpu","pni","pclmulqdq","dtes64","monitor","ds_cpl","vmx","smx","est","tm2","ssse3","fma","cx16","xtpr","pdcm","pcid","dca","sse4_1","sse4_2","x2apic","movbe","popcnt","tsc_deadline_timer","aes","xsave","avx","f16c","rdrand","lahf_lm","abm","ida","arat","epb","xsaveopt","pln","pts","dtherm","tpr_shadow","vnmi","flexpriority","ept","vpid","fsgsbase","tsc_adjust","bmi1","avx2","smep","bmi2","erms","invpcid"]},"35":{"vendor_id":"GenuineIntel","family":"6","model":"63","model_name":"Intel(R) Xeon(R) CPU E5-2680 v3 @ 2.50GHz","stepping":"2","mhz":"1200.097","cache_size":"30720 KB","physical_id":"0","core_id":"13","cores":"12","flags":["fpu","vme","de","pse","tsc","msr","pae","mce","cx8","apic","sep","mtrr","pge","mca","cmov","pat","pse36","clflush","dts","acpi","mmx","fxsr","sse","sse2","ss","ht","tm","pbe","syscall","nx","pdpe1gb","rdtscp","lm","constant_tsc","arch_perfmon","pebs","bts","rep_good","nopl","xtopology","nonstop_tsc","aperfmperf","eagerfpu","pni","pclmulqdq","dtes64","monitor","ds_cpl","vmx","smx","est","tm2","ssse3","fma","cx16","xtpr","pdcm","pcid","dca","sse4_1","sse4_2","x2apic","movbe","popcnt","tsc_deadline_timer","aes","xsave","avx","f16c","rdrand","lahf_lm","abm","ida","arat","epb","xsaveopt","pln","pts","dtherm","tpr_shadow","vnmi","flexpriority","ept","vpid","fsgsbase","tsc_adjust","bmi1","avx2","smep","bmi2","erms","invpcid"]},"36":{"vendor_id":"GenuineIntel","family":"6","model":"63","model_name":"Intel(R) Xeon(R) CPU E5-2680 v3 @ 2.50GHz","stepping":"2","mhz":"1199.902","cache_size":"30720 KB","physical_id":"1","core_id":"0","cores":"12","flags":["fpu","vme","de","pse","tsc","msr","pae","mce","cx8","apic","sep","mtrr","pge","mca","cmov","pat","pse36","clflush","dts","acpi","mmx","fxsr","sse","sse2","ss","ht","tm","pbe","syscall","nx","pdpe1gb","rdtscp","lm","constant_tsc","arch_perfmon","pebs","bts","rep_good","nopl","xtopology","nonstop_tsc","aperfmperf","eagerfpu","pni","pclmulqdq","dtes64","monitor","ds_cpl","vmx","smx","est","tm2","ssse3","fma","cx16","xtpr","pdcm","pcid","dca","sse4_1","sse4_2","x2apic","movbe","popcnt","tsc_deadline_timer","aes","xsave","avx","f16c","rdrand","lahf_lm","abm","ida","arat","epb","xsaveopt","pln","pts","dtherm","tpr_shadow","vnmi","flexpriority","ept","vpid","fsgsbase","tsc_adjust","bmi1","avx2","smep","bmi2","erms","invpcid"]},"37":{"vendor_id":"GenuineIntel","family":"6","model":"63","model_name":"Intel(R) Xeon(R) CPU E5-2680 v3 @ 2.50GHz","stepping":"2","mhz":"1200.000","cache_size":"30720 KB","physical_id":"1","core_id":"1","cores":"12","flags":["fpu","vme","de","pse","tsc","msr","pae","mce","cx8","apic","sep","mtrr","pge","mca","cmov","pat","pse36","clflush","dts","acpi","mmx","fxsr","sse","sse2","ss","ht","tm","pbe","syscall","nx","pdpe1gb","rdtscp","lm","constant_tsc","arch_perfmon","pebs","bts","rep_good","nopl","xtopology","nonstop_tsc","aperfmperf","eagerfpu","pni","pclmulqdq","dtes64","monitor","ds_cpl","vmx","smx","est","tm2","ssse3","fma","cx16","xtpr","pdcm","pcid","dca","sse4_1","sse4_2","x2apic","movbe","popcnt","tsc_deadline_timer","aes","xsave","avx","f16c","rdrand","lahf_lm","abm","ida","arat","epb","xsaveopt","pln","pts","dtherm","tpr_shadow","vnmi","flexpriority","ept","vpid","fsgsbase","tsc_adjust","bmi1","avx2","smep","bmi2","erms","invpcid"]},"38":{"vendor_id":"GenuineIntel","family":"6","model":"63","model_name":"Intel(R) Xeon(R) CPU E5-2680 v3 @ 2.50GHz","stepping":"2","mhz":"1200.097","cache_size":"30720 KB","physical_id":"1","core_id":"2","cores":"12","flags":["fpu","vme","de","pse","tsc","msr","pae","mce","cx8","apic","sep","mtrr","pge","mca","cmov","pat","pse36","clflush","dts","acpi","mmx","fxsr","sse","sse2","ss","ht","tm","pbe","syscall","nx","pdpe1gb","rdtscp","lm","constant_tsc","arch_perfmon","pebs","bts","rep_good","nopl","xtopology","nonstop_tsc","aperfmperf","eagerfpu","pni","pclmulqdq","dtes64","monitor","ds_cpl","vmx","smx","est","tm2","ssse3","fma","cx16","xtpr","pdcm","pcid","dca","sse4_1","sse4_2","x2apic","movbe","popcnt","tsc_deadline_timer","aes","xsave","avx","f16c","rdrand","lahf_lm","abm","ida","arat","epb","xsaveopt","pln","pts","dtherm","tpr_shadow","vnmi","flexpriority","ept","vpid","fsgsbase","tsc_adjust","bmi1","avx2","smep","bmi2","erms","invpcid"]},"39":{"vendor_id":"GenuineIntel","family":"6","model":"63","model_name":"Intel(R) Xeon(R) CPU E5-2680 v3 @ 2.50GHz","stepping":"2","mhz":"1200.195","cache_size":"30720 KB","physical_id":"1","core_id":"3","cores":"12","flags":["fpu","vme","de","pse","tsc","msr","pae","mce","cx8","apic","sep","mtrr","pge","mca","cmov","pat","pse36","clflush","dts","acpi","mmx","fxsr","sse","sse2","ss","ht","tm","pbe","syscall","nx","pdpe1gb","rdtscp","lm","constant_tsc","arch_perfmon","pebs","bts","rep_good","nopl","xtopology","nonstop_tsc","aperfmperf","eagerfpu","pni","pclmulqdq","dtes64","monitor","ds_cpl","vmx","smx","est","tm2","ssse3","fma","cx16","xtpr","pdcm","pcid","dca","sse4_1","sse4_2","x2apic","movbe","popcnt","tsc_deadline_timer","aes","xsave","avx","f16c","rdrand","lahf_lm","abm","ida","arat","epb","xsaveopt","pln","pts","dtherm","tpr_shadow","vnmi","flexpriority","ept","vpid","fsgsbase","tsc_adjust","bmi1","avx2","smep","bmi2","erms","invpcid"]},"40":{"vendor_id":"GenuineIntel","family":"6","model":"63","model_name":"Intel(R) Xeon(R) CPU E5-2680 v3 @ 2.50GHz","stepping":"2","mhz":"1200.000","cache_size":"30720 KB","physical_id":"1","core_id":"4","cores":"12","flags":["fpu","vme","de","pse","tsc","msr","pae","mce","cx8","apic","sep","mtrr","pge","mca","cmov","pat","pse36","clflush","dts","acpi","mmx","fxsr","sse","sse2","ss","ht","tm","pbe","syscall","nx","pdpe1gb","rdtscp","lm","constant_tsc","arch_perfmon","pebs","bts","rep_good","nopl","xtopology","nonstop_tsc","aperfmperf","eagerfpu","pni","pclmulqdq","dtes64","monitor","ds_cpl","vmx","smx","est","tm2","ssse3","fma","cx16","xtpr","pdcm","pcid","dca","sse4_1","sse4_2","x2apic","movbe","popcnt","tsc_deadline_timer","aes","xsave","avx","f16c","rdrand","lahf_lm","abm","ida","arat","epb","xsaveopt","pln","pts","dtherm","tpr_shadow","vnmi","flexpriority","ept","vpid","fsgsbase","tsc_adjust","bmi1","avx2","smep","bmi2","erms","invpcid"]},"41":{"vendor_id":"GenuineIntel","family":"6","model":"63","model_name":"Intel(R) Xeon(R) CPU E5-2680 v3 @ 2.50GHz","stepping":"2","mhz":"1200.292","cache_size":"30720 KB","physical_id":"1","core_id":"5","cores":"12","flags":["fpu","vme","de","pse","tsc","msr","pae","mce","cx8","apic","sep","mtrr","pge","mca","cmov","pat","pse36","clflush","dts","acpi","mmx","fxsr","sse","sse2","ss","ht","tm","pbe","syscall","nx","pdpe1gb","rdtscp","lm","constant_tsc","arch_perfmon","pebs","bts","rep_good","nopl","xtopology","nonstop_tsc","aperfmperf","eagerfpu","pni","pclmulqdq","dtes64","monitor","ds_cpl","vmx","smx","est","tm2","ssse3","fma","cx16","xtpr","pdcm","pcid","dca","sse4_1","sse4_2","x2apic","movbe","popcnt","tsc_deadline_timer","aes","xsave","avx","f16c","rdrand","lahf_lm","abm","ida","arat","epb","xsaveopt","pln","pts","dtherm","tpr_shadow","vnmi","flexpriority","ept","vpid","fsgsbase","tsc_adjust","bmi1","avx2","smep","bmi2","erms","invpcid"]},"42":{"vendor_id":"GenuineIntel","family":"6","model":"63","model_name":"Intel(R) Xeon(R) CPU E5-2680 v3 @ 2.50GHz","stepping":"2","mhz":"1200.000","cache_size":"30720 KB","physical_id":"1","core_id":"8","cores":"12","flags":["fpu","vme","de","pse","tsc","msr","pae","mce","cx8","apic","sep","mtrr","pge","mca","cmov","pat","pse36","clflush","dts","acpi","mmx","fxsr","sse","sse2","ss","ht","tm","pbe","syscall","nx","pdpe1gb","rdtscp","lm","constant_tsc","arch_perfmon","pebs","bts","rep_good","nopl","xtopology","nonstop_tsc","aperfmperf","eagerfpu","pni","pclmulqdq","dtes64","monitor","ds_cpl","vmx","smx","est","tm2","ssse3","fma","cx16","xtpr","pdcm","pcid","dca","sse4_1","sse4_2","x2apic","movbe","popcnt","tsc_deadline_timer","aes","xsave","avx","f16c","rdrand","lahf_lm","abm","ida","arat","epb","xsaveopt","pln","pts","dtherm","tpr_shadow","vnmi","flexpriority","ept","vpid","fsgsbase","tsc_adjust","bmi1","avx2","smep","bmi2","erms","invpcid"]},"43":{"vendor_id":"GenuineIntel","family":"6","model":"63","model_name":"Intel(R) Xeon(R) CPU E5-2680 v3 @ 2.50GHz","stepping":"2","mhz":"1200.195","cache_size":"30720 KB","physical_id":"1","core_id":"9","cores":"12","flags":["fpu","vme","de","pse","tsc","msr","pae","mce","cx8","apic","sep","mtrr","pge","mca","cmov","pat","pse36","clflush","dts","acpi","mmx","fxsr","sse","sse2","ss","ht","tm","pbe","syscall","nx","pdpe1gb","rdtscp","lm","constant_tsc","arch_perfmon","pebs","bts","rep_good","nopl","xtopology","nonstop_tsc","aperfmperf","eagerfpu","pni","pclmulqdq","dtes64","monitor","ds_cpl","vmx","smx","est","tm2","ssse3","fma","cx16","xtpr","pdcm","pcid","dca","sse4_1","sse4_2","x2apic","movbe","popcnt","tsc_deadline_timer","aes","xsave","avx","f16c","rdrand","lahf_lm","abm","ida","arat","epb","xsaveopt","pln","pts","dtherm","tpr_shadow","vnmi","flexpriority","ept","vpid","fsgsbase","tsc_adjust","bmi1","avx2","smep","bmi2","erms","invpcid"]},"44":{"vendor_id":"GenuineIntel","family":"6","model":"63","model_name":"Intel(R) Xeon(R) CPU E5-2680 v3 @ 2.50GHz","stepping":"2","mhz":"1200.097","cache_size":"30720 KB","physical_id":"1","core_id":"10","cores":"12","flags":["fpu","vme","de","pse","tsc","msr","pae","mce","cx8","apic","sep","mtrr","pge","mca","cmov","pat","pse36","clflush","dts","acpi","mmx","fxsr","sse","sse2","ss","ht","tm","pbe","syscall","nx","pdpe1gb","rdtscp","lm","constant_tsc","arch_perfmon","pebs","bts","rep_good","nopl","xtopology","nonstop_tsc","aperfmperf","eagerfpu","pni","pclmulqdq","dtes64","monitor","ds_cpl","vmx","smx","est","tm2","ssse3","fma","cx16","xtpr","pdcm","pcid","dca","sse4_1","sse4_2","x2apic","movbe","popcnt","tsc_deadline_timer","aes","xsave","avx","f16c","rdrand","lahf_lm","abm","ida","arat","epb","xsaveopt","pln","pts","dtherm","tpr_shadow","vnmi","flexpriority","ept","vpid","fsgsbase","tsc_adjust","bmi1","avx2","smep","bmi2","erms","invpcid"]},"45":{"vendor_id":"GenuineIntel","family":"6","model":"63","model_name":"Intel(R) Xeon(R) CPU E5-2680 v3 @ 2.50GHz","stepping":"2","mhz":"1200.000","cache_size":"30720 KB","physical_id":"1","core_id":"11","cores":"12","flags":["fpu","vme","de","pse","tsc","msr","pae","mce","cx8","apic","sep","mtrr","pge","mca","cmov","pat","pse36","clflush","dts","acpi","mmx","fxsr","sse","sse2","ss","ht","tm","pbe","syscall","nx","pdpe1gb","rdtscp","lm","constant_tsc","arch_perfmon","pebs","bts","rep_good","nopl","xtopology","nonstop_tsc","aperfmperf","eagerfpu","pni","pclmulqdq","dtes64","monitor","ds_cpl","vmx","smx","est","tm2","ssse3","fma","cx16","xtpr","pdcm","pcid","dca","sse4_1","sse4_2","x2apic","movbe","popcnt","tsc_deadline_timer","aes","xsave","avx","f16c","rdrand","lahf_lm","abm","ida","arat","epb","xsaveopt","pln","pts","dtherm","tpr_shadow","vnmi","flexpriority","ept","vpid","fsgsbase","tsc_adjust","bmi1","avx2","smep","bmi2","erms","invpcid"]},"46":{"vendor_id":"GenuineIntel","family":"6","model":"63","model_name":"Intel(R) Xeon(R) CPU E5-2680 v3 @ 2.50GHz","stepping":"2","mhz":"1200.097","cache_size":"30720 KB","physical_id":"1","core_id":"12","cores":"12","flags":["fpu","vme","de","pse","tsc","msr","pae","mce","cx8","apic","sep","mtrr","pge","mca","cmov","pat","pse36","clflush","dts","acpi","mmx","fxsr","sse","sse2","ss","ht","tm","pbe","syscall","nx","pdpe1gb","rdtscp","lm","constant_tsc","arch_perfmon","pebs","bts","rep_good","nopl","xtopology","nonstop_tsc","aperfmperf","eagerfpu","pni","pclmulqdq","dtes64","monitor","ds_cpl","vmx","smx","est","tm2","ssse3","fma","cx16","xtpr","pdcm","pcid","dca","sse4_1","sse4_2","x2apic","movbe","popcnt","tsc_deadline_timer","aes","xsave","avx","f16c","rdrand","lahf_lm","abm","ida","arat","epb","xsaveopt","pln","pts","dtherm","tpr_shadow","vnmi","flexpriority","ept","vpid","fsgsbase","tsc_adjust","bmi1","avx2","smep","bmi2","erms","invpcid"]},"47":{"vendor_id":"GenuineIntel","family":"6","model":"63","model_name":"Intel(R) Xeon(R) CPU E5-2680 v3 @ 2.50GHz","stepping":"2","mhz":"1200.000","cache_size":"30720 KB","physical_id":"1","core_id":"13","cores":"12","flags":["fpu","vme","de","pse","tsc","msr","pae","mce","cx8","apic","sep","mtrr","pge","mca","cmov","pat","pse36","clflush","dts","acpi","mmx","fxsr","sse","sse2","ss","ht","tm","pbe","syscall","nx","pdpe1gb","rdtscp","lm","constant_tsc","arch_perfmon","pebs","bts","rep_good","nopl","xtopology","nonstop_tsc","aperfmperf","eagerfpu","pni","pclmulqdq","dtes64","monitor","ds_cpl","vmx","smx","est","tm2","ssse3","fma","cx16","xtpr","pdcm","pcid","dca","sse4_1","sse4_2","x2apic","movbe","popcnt","tsc_deadline_timer","aes","xsave","avx","f16c","rdrand","lahf_lm","abm","ida","arat","epb","xsaveopt","pln","pts","dtherm","tpr_shadow","vnmi","flexpriority","ept","vpid","fsgsbase","tsc_adjust","bmi1","avx2","smep","bmi2","erms","invpcid"]},"total":48,"real":2}},"createdAt":"2016-11-14T21:14:00.261Z","updatedAt":"2016-11-14T21:14:00.261Z","id":"582a2918abed2e8907545c29"}''')
                for ifname, ifdata in ohai['data']['network']['interfaces'].iteritems():
                    if ifdata.get('encapsulation', '') != 'Ethernet':
                        continue
                    if node['id'] not in nodeid2eths:
                        nodeid2eths[node['id']] = []
                    eth = {
                        'ResourceFamily': 'Port',
                        'ResourceModel': 'Resource Port',
                        'ResourceName': ifname,
                        'ResourceAddress': 'no-ohai-address',
                        'ResourceDescription': '',
                        'MTU': ifdata['mtu'],
                        'MAC Address': '',
                        'IPv4 Address': '',
                        'IPv6 Address': '',
                    }
                    nodeid2eths[node['id']].append(eth)
                    for addr, addrdata in ifdata['addresses'].iteritems():
                        if addrdata['family'] == 'lladdr':
                            eth['MAC Address'] = addr
                            eth['ResourceAddress'] = addr
                        elif addrdata['family'] == 'inet':
                            eth['IPv4 Address'] = addr.replace('_', '.')
                        elif addrdata['family'] == 'inet6':
                            eth['IPv6 Address'] = addr
            except:
                qs_trace('ohai failed for node ' + node['id'], context)

        currhosts = [{'a': 'b'}]
        if True:
            currhosts = []
        # for system in systemlist[0:1]:
        for system in systemlist:
            url = 'https://' + onrack_ip + "/redfish/v1/Systems/" + system
            out = rest_json('get', url, None, token, context)
            # out = json.loads('''{"SKU": "To be filled by O.E.M.", "BiosVersion": "S2B_3A17 5.6 11/07/2014", "PowerState": "Off", "Processors": {"@odata.type": "#ProcessorCollection.ProcessorCollection", "Oem": {}, "Members@odata.navigationLink": {"@odata.id": null}, "Members@odata.count": 2.0, "@odata.id": "/redfish/v1/Systems/582a28eb5db8528c07d97c88/Processors", "@odata.context": null, "Members": [{"@odata.id": "/redfish/v1/Systems/582a28eb5db8528c07d97c88/Processors/Socket0"}, {"@odata.id": "/redfish/v1/Systems/582a28eb5db8528c07d97c88/Processors/Socket1"}], "Description": null, "Name": "Processors Collection"}, "SerialNumber": null, "Boot": {"BootSourceOverrideTarget": null, "UefiTargetBootSourceOverride": null, "BootSourceOverrideEnabled": null}, "PartNumber": null, "ProcessorSummary": {"Status": {"HealthRollup": "OK", "State": null, "Health": "OK", "Oem": {"StatesAsserted": []}}, "Count": 2.0, "Model": "Intel(R) Xeon(R) CPU E5-2680 v3 @ 2.50GHz"}, "@odata.type": "#ComputerSystem.1.0.0.ComputerSystem", "Description": null, "HostName": null, "@odata.context": null, "SimpleStorage": {"@odata.type": "#SimpleStorageCollection.SimpleStorageCollection", "Oem": {}, "Members": [{"@odata.id": "/redfish/v1/Systems/582a28eb5db8528c07d97c88/SimpleStorage/0"}, {"@odata.id": "/redfish/v1/Systems/582a28eb5db8528c07d97c88/SimpleStorage/1"}], "Members@odata.count": 2.0, "@odata.id": "/redfish/v1/Systems/582a28eb5db8528c07d97c88/SimpleStorage", "@odata.context": null, "Members@odata.navigationLink": {"@odata.id": null}, "Name": "SimpleStorage Collection", "Description": null}, "Oem": {"EMC": {"VisionID_System": "QTF3J052100191", "VisionID_Chassis": "QTFCJ05260027", "VisionID_Ip": "10.10.111.11"}}, "Manufacturer": "Quanta Computer Inc", "Status": {"HealthRollup": null, "State": null, "Health": "Down", "Oem": {"StatesAsserted": null}}, "Name": "Quanta D51", "AssetTag": " ", "@odata.id": "/redfish/v1/Systems/582a28eb5db8528c07d97c88", "IndicatorLED": "Off", "LogServices": {"@odata.type": "#LogServiceCollection.LogServiceCollection", "Oem": {}, "Members@odata.count": 1.0, "@odata.id": "/redfish/v1/Systems/582a28eb5db8528c07d97c88/LogService", "@odata.context": null, "Members@odata.navigationLink": {"@odata.id": null}, "Description": null, "Name": "Log Service Collection", "Members": [{"@odata.id": "/redfish/v1/Systems/582a28eb5db8528c07d97c88/LogService/sel"}]}, "MemorySummary": {"Status": {"HealthRollup": null, "State": null, "Health": null, "Oem": {"StatesAsserted": []}}, "TotalSystemMemoryGiB": 256.0}, "Model": "D51B-2U (dual 1G LoM)", "EthernetInterfaces": {"@odata.type": null, "Description": null, "Members": [], "Members@odata.navigationLink": {"@odata.id": null}, "Members@odata.count": null, "@odata.id": null, "@odata.context": null, "Oem": {}, "Name": null}, "UUID": "51C208A2-7C18-1000-B48B-2C600C989213", "Links": {"PoweredBy": [{"@odata.id": "/redfish/v1/Chassis/582a28eb5db8528c07d97c88/Power"}], "Chassis@odata.count": 1.0, "Chassis@odata.navigationLink": {"@odata.id": null}, "ManagedBy@odata.count": 1.0, "PoweredBy@odata.count": 1.0, "ManagedBy@odata.navigationLink": {"@odata.id": null}, "ManagedBy": [{"@odata.id": "/redfish/v1/Managers/582a28eb5db8528c07d97c88"}], "Chassis": {"@odata.id": "/redfish/v1/Chassis/582a28eb5db8528c07d97c88"}, "CooledBy@odata.navigationLink": {"@odata.id": null}, "Oem": {}, "CooledBy@odata.count": 0.0, "CooledBy": [], "PoweredBy@odata.navigationLink": {"@odata.id": null}}, "SystemType": null, "Actions": {"#ComputerSystem.Reset": {"target": "/redfish/v1/Systems/582a28eb5db8528c07d97c88/Actions/ComputerSystem.Reset", "title": null}, "Oem": {"OnRack.BootImage": {"target": "/redfish/v1/Systems/582a28eb5db8528c07d97c88/OEM/OnRack/Actions/BootImage", "title": null}}}, "Id": "582a28eb5db8528c07d97c88"}''')
            if out['Oem']['EMC']['VisionID_System']:
                name = out['Name']
                model = out.get('Model', None)
                if model:
                    model = name + ' ' + model.strip()
                else:
                    model = name

                x = {
                    "OnRackID": out['Id'],
                    "ResourceName": out['Name'] + ' ' + out['Oem']['EMC']['VisionID_Chassis'],
                    "ResourceAddress": out['Id'],
                    "ResourceFamily": "Compute Server",
                    "ResourceModel": "ComputeShell",
                    "ResourceFolder": "Compute/" + context.resource.name,
                    "ResourceDescription": out['Oem']['EMC']['VisionID_System'],
                    "ResourceSubresources": nodeid2eths.get(system, []) + [{
                        'ResourceFamily': 'Power Port',
                        'ResourceModel': 'Generic Power Port',
                        'ResourceName': 'OnRack',
                        'ResourceDescription': '',
                        'ResourceAddress': 'NA',
                    }],
                    # "ResourceDescription": '\n'.join([s[2:]
                    #                                   for s in re.sub(r'[{}"\[\]]', '', json.dumps(out, indent=2, separators=('', ': '))).split('\n')
                    #                                   if s.strip()]).strip()[0:1999],
                    "Number of CPUs": str(out['ProcessorSummary']['Count']),
                    "Memory Size": str(out['MemorySummary']['TotalSystemMemoryGiB']),
                    "BIOS Version": str(out['BiosVersion']),
                    "Vendor": out['Manufacturer'],
                    "Serial Number": out['SerialNumber'] if out['SerialNumber'] else '',
                    "Model": model,
                    "VisionID IP": out['Oem']['EMC']['VisionID_Ip'],
                    "Location": context.resource.attributes['Location'],
                }
                currhosts.append(x)
                # qs_info('DEBUG JSON: ' + str(x), context)
            else:
                qs_info('Skipping system %s' % url, context)

        # currhosts = [
        #     # {"OnRackID": "or1", "ResourceName": "Host01", "ResourceAddress": "1", "ResourceFamily": "Compute Server", "ResourceModel": "ComputeShell", "ResourceFolder": "Compute", "ResourceDescription": "descr", "Number of CPUs": "4", "Memory Size": "64", "Vendor": "Dell", "Model": "R630", "Serial Number": "s1",  },
        #     {"OnRackID": "or2", "ResourceName": "Host02", "ResourceAddress": "2", "ResourceFamily": "Compute Server", "ResourceModel": "ComputeShell", "ResourceFolder": "Compute", "ResourceDescription": "descr", "Number of CPUs": "4", "Memory Size": "64", "Vendor": "Dell", "Model": "R630", "Serial Number": "s2",  },
        #     {"OnRackID": "or3", "ResourceName": "Host03", "ResourceAddress": "3", "ResourceFamily": "Compute Server", "ResourceModel": "ComputeShell", "ResourceFolder": "Compute", "ResourceDescription": "descr", "Number of CPUs": "4", "Memory Size": "64", "Vendor": "Dell", "Model": "R630", "Serial Number": "s3",  },
        #     # {"OnRackID": "or4", "ResourceName": "Host04", "ResourceAddress": "4", "ResourceFamily": "Compute Server", "ResourceModel": "ComputeShell", "ResourceFolder": "Compute", "ResourceDescription": "descr", "Number of CPUs": "4", "Memory Size": "64", "Vendor": "Dell", "Model": "R630", "Serial Number": "s4",  },
        #     # {"OnRackID": "or5", "ResourceName": "Host05", "ResourceAddress": "5", "ResourceFamily": "Compute Server", "ResourceModel": "ComputeShell", "ResourceFolder": "Compute", "ResourceDescription": "descr", "Number of CPUs": "4", "Memory Size": "64", "Vendor": "Dell", "Model": "R630", "Serial Number": "s5",  },
        #     # {"OnRackID": "or6", "ResourceName": "Host06", "ResourceAddress": "6", "ResourceFamily": "Compute Server", "ResourceModel": "ComputeShell", "ResourceFolder": "Compute", "ResourceDescription": "descr", "Number of CPUs": "4", "Memory Size": "64", "Vendor": "Dell", "Model": "R630", "Serial Number": "s6",  },
        #     {"OnRackID": "or7", "ResourceName": "Host07", "ResourceAddress": "7", "ResourceFamily": "Compute Server", "ResourceModel": "ComputeShell", "ResourceFolder": "Compute", "ResourceDescription": "descr", "Number of CPUs": "4", "Memory Size": "64", "Vendor": "Dell", "Model": "R630", "Serial Number": "s7",  },
        #     # {"OnRackID": "or8", "ResourceName": "Host08", "ResourceAddress": "8", "ResourceFamily": "Compute Server", "ResourceModel": "ComputeShell", "ResourceFolder": "Compute", "ResourceDescription": "descr", "Number of CPUs": "4", "Memory Size": "64", "Vendor": "Dell", "Model": "R630", "Serial Number": "s8",  },
        #     {"OnRackID": "or9", "ResourceName": "Host09", "ResourceAddress": "9", "ResourceFamily": "Compute Server", "ResourceModel": "ComputeShell", "ResourceFolder": "Compute", "ResourceDescription": "descr", "Number of CPUs": "4", "Memory Size": "64", "Vendor": "Dell", "Model": "R630", "Serial Number": "s9",  },
        #     {"OnRackID": "or10", "ResourceName": "Host10", "ResourceAddress": "10", "ResourceFamily": "Compute Server", "ResourceModel": "ComputeShell", "ResourceFolder": "Compute", "ResourceDescription": "descr", "Number of CPUs": "4", "Memory Size": "64", "Vendor": "Dell", "Model": "R630", "Serial Number": "s10",  },
        # ]
        guid2currhost = {}
        for host in currhosts:
            guid2currhost[host['OnRackID']] = host

        curr_guids = set([host['OnRackID'] for host in currhosts])

        me = csapi.GetResourceDetails(resourceFullPath=context.resource.fullname)

        rm_guids = set([r.UniqeIdentifier for r in me.ChildResources])

        guid2rmdetails = dict([(r.UniqeIdentifier, r) for r in me.ChildResources])

        to_delete_guids = rm_guids.difference(curr_guids)  # in rm but not in new
        to_create_guids = curr_guids.difference(rm_guids)  # in new but not in rm
        reinclude_guids = curr_guids.difference(to_create_guids)  # in rm and new

        if len(to_delete_guids) > 0:
            csapi.ExcludeResources([
                                       '/'.join(guid2rmdetails[a].Connections[0].FullPath.split('/')[0:-1])
                                       for a in to_delete_guids
                                       if len(guid2rmdetails[a].Connections) > 0])
            # todo if we delete the roots: delete onrack subresources

        if len(reinclude_guids) > 0:
            csapi.IncludeResources([
                                       '/'.join(guid2rmdetails[a].Connections[0].FullPath.split('/')[0:-1])
                                       for a in reinclude_guids
                                       if len(guid2rmdetails[a].Connections) > 0])

        if len(to_create_guids) > 0:
            for folder in set([host['ResourceFolder'] for host in currhosts]):
                csapi.CreateFolder(folder)

            for guid in to_create_guids:
                roots_rootsubs = [
                    ResourceInfoDto('Compute Server', 'ComputeShell', guid2currhost[guid]['ResourceName'],
                                    guid2currhost[guid]['ResourceAddress'], guid2currhost[guid]['ResourceFolder'], '',
                                    guid2currhost[guid]['ResourceDescription'])
                ]
                for sub in guid2currhost[guid]['ResourceSubresources']:
                    roots_rootsubs.append(ResourceInfoDto(sub['ResourceFamily'], sub['ResourceModel'], sub['ResourceName'],
                                                    sub['ResourceAddress'], '', guid2currhost[guid]['ResourceName'],
                                                    sub['ResourceDescription']))
                try:
                    csapi.CreateResources(roots_rootsubs)
                except:
                    pass
                # todo sync NICs (added / removed)

            # roots = [
            #     ResourceInfoDto('Compute Server', 'ComputeShell', guid2currhost[guid]['ResourceName'], guid2currhost[guid]['ResourceAddress'], guid2currhost[guid]['ResourceFolder'], '', guid2currhost[guid]['ResourceDescription'])
            #     for guid in to_create_guids
            #     ]
            #
            # rootsubs = []
            # for guid in to_create_guids:
            #     for sub in guid2currhost[guid]['ResourceSubresources']:
            #         rootsubs.append(ResourceInfoDto(sub['ResourceFamily'], sub['ResourceModel'], sub['ResourceName'], sub['ResourceAddress'], '', guid2currhost[guid]['ResourceName'], sub['ResourceDescription']))

            onracksubs = [
                ResourceInfoDto('OnRack Discoverable', 'OnRack Discovered Resource', guid2currhost[guid]['ResourceName'], guid2currhost[guid]['ResourceAddress'], '', context.resource.fullname, '')
                for guid in to_create_guids
                ]

            # csapi.CreateResources(roots + rootsubs + onracksubs)
            csapi.CreateResources(onracksubs)
            csapi.UpdatePhysicalConnections([
                                                PhysicalConnectionUpdateRequest(
                                                    guid2currhost[guid]['ResourceName'] + '/OnRack',
                                                    context.resource.fullname + '/' + guid2currhost[guid]['ResourceName'],
                                                    '1'
                                                )
                                                for guid in to_create_guids])
            # for guid in to_create_guids:
            #     csapi.UpdateResourceDriver(guid2currhost[guid]['ResourceName'], "ComputeShellDriver")

        if len(currhosts) > 0:
            # for host in currhosts:
            #     for name, value in host.iteritems():
            #         if 'Resource' not in name:
            #             csapi.SetAttributeValue(host['ResourceName'], name, value)
            #     for name in ['Serial Number', 'Model', 'OnRackID']:
            #         csapi.SetAttributeValue(context.resource.fullname + '/' + host['ResourceName'], name, host[name])
            roots = [
                ResourceAttributesUpdateRequest(host['ResourceName'],
                                                [
                                                    AttributeNameValue(name, value)
                                                    for name, value in host.iteritems()
                                                    if 'Resource' not in name])
                for host in currhosts
                ]
            rootsubs = []
            for host in currhosts:
                for sub in host['ResourceSubresources']:
                    if False:
                        sub = {'a': 'b'}
                    attrs = [
                        AttributeNameValue(name, value)
                        for name, value in sub.iteritems()
                        if 'Resource' not in name
                        ]
                    if len(attrs) > 0:
                        rootsubs.append(ResourceAttributesUpdateRequest(host['ResourceName'] + '/' + sub['ResourceName'], attrs))


            onracksubs = [
                ResourceAttributesUpdateRequest(context.resource.fullname + '/' + host['ResourceName'],
                                                [
                                                    AttributeNameValue('Model', host['Model']),
                                                    AttributeNameValue('Serial Number', host['Serial Number']),
                                                    AttributeNameValue('OnRackID', host['OnRackID']),
                                                ])
                for host in currhosts
                ]
            for x in roots + rootsubs + onracksubs:
                qs_trace(x.ResourceFullName, context)
                for av in x.AttributeNamesValues:
                    qs_trace('  ' + av.Name + ' = ' + av.Value, context)
            csapi.SetAttributesValues(roots + rootsubs + onracksubs)
            for host in currhosts:
                csapi.UpdateResourceDescription(host['ResourceName'], host['ResourceDescription'])
        
        return AutoLoadDetails([
            AutoLoadResource(model='Compute Server', 
                             name=host['ResourceName'], 
                             relative_address=host['ResourceAddress'], 
                             unique_identifier=host['OnRackID'])
            for host in currhosts
            ], [])

