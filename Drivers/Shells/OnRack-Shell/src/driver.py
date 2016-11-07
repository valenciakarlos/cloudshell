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
        maxtries = int(context.resource.attributes['OS Deployment Attempts Limit'])
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

        # See below some example code demonstrating how to return the resource structure
        # and attributes. In real life, of course, if the actual values are not static,
        # this code would be preceded by some SNMP/other calls to get the actual resource information
        # Add sub resources details
        # sub_resources = [AutoLoadResource(model='OnRack Discovered Resource', name='Brocade1', relative_address='1'),
        #                  AutoLoadResource(model='OnRack Discovered Resource', name='Host1', relative_address='2'),
        #                  AutoLoadResource(model='OnRack Discovered Resource', name='Host2', relative_address='3'),
        #                  AutoLoadResource(model='OnRack Discovered Resource', name='Host3', relative_address='4'),
        #                  AutoLoadResource(model='OnRack Discovered Resource', name='Host4', relative_address='5'),
        #                  AutoLoadResource(model='OnRack Discovered Resource', name='Host5', relative_address='6'),
        #                  AutoLoadResource(model='OnRack Discovered Resource', name='Host6', relative_address='7'),
        #                  AutoLoadResource(model='OnRack Discovered Resource', name='Host7', relative_address='8'),
        #                  AutoLoadResource(model='OnRack Discovered Resource', name='Host8', relative_address='9'),
        #                  AutoLoadResource(model='OnRack Discovered Resource', name='Host9', relative_address='10')]
        # attributes = [AutoLoadAttribute('1', 'Serial Number', 'JAE053002JD'),
        #               AutoLoadAttribute('1', 'Model', 'BROCADE123'),
        #               AutoLoadAttribute('2', 'Serial Number', 'JAE053002JD2'),
        #               AutoLoadAttribute('2', 'Model', 'DELL SERVER 630'),
        #               AutoLoadAttribute('3', 'Serial Number', 'JAE053002JD3'),
        #               AutoLoadAttribute('3', 'Model', 'DELL SERVER 630'),
        #               AutoLoadAttribute('4', 'Serial Number', 'JAE053002JD4'),
        #               AutoLoadAttribute('4', 'Model', 'DELL SERVER 630'),
        #               AutoLoadAttribute('5', 'Serial Number', 'JAE053002JD5'),
        #               AutoLoadAttribute('5', 'Model', 'DELL SERVER 630'),
        #               AutoLoadAttribute('6', 'Serial Number', 'JAE053002JD6'),
        #               AutoLoadAttribute('6', 'Model', 'DELL SERVER 630'),
        #               AutoLoadAttribute('7', 'Serial Number', 'JAE053002JD7'),
        #               AutoLoadAttribute('7', 'Model', 'DELL SERVER 630'),
        #               AutoLoadAttribute('8', 'Serial Number', 'JAE053002JD8'),
        #               AutoLoadAttribute('8', 'Model', 'DELL SERVER 630'),
        #               AutoLoadAttribute('9', 'Serial Number', 'JAE053002JD9'),
        #               AutoLoadAttribute('9', 'Model', 'DELL SERVER 630'),
        #               AutoLoadAttribute('10', 'Serial Number', 'JAE053002JD10'),
        #               AutoLoadAttribute('10', 'Model', 'DELL SERVER 630')
        # ]

        # https: // localhost / redfish / v1 / OEM / OnRack / Switch / 57eb83a0be0e14b207416eef | python - mjson.tool
        # {
        #     "@odata.context": null,
        #     "@odata.id": "/redfish/v1/OEM/OnRack/Switch/57eb83a0be0e14b207416eef",
        #     "@odata.type": "#Switch.1.0.0.Switch",
        #     "Description": "Brocade Communications Systems, Inc. ICX7250-48, IronWare Version 08.0.30T211 Compiled on Mar 20 2015 at 11:57:13 labeled as SPS08030",
        #     "FWRevision": null,
        #     "HWRevision": null,
        #     "Id": "57eb83a0be0e14b207416eef",
        #     "ManufactureName": null,
        #     "Model": null,
        #     "Name": "ICX7250-48 Switch",

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
                for ifname, ifdata in rest_json('get', 'http://' + onrack_ip + ':8080/api/1.1/nodes/' + node['id'] + '/catalogs/ohai', None, token, context)['data']['network']['interfaces'].iteritems():
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
        for system in systemlist:
            url = 'https://' + onrack_ip + "/redfish/v1/Systems/" + system
            out = rest_json('get', url, None, token, context)
            if out['Oem']['EMC']['VisionID_System']:
                name = out['Name']
                model = out.get('Model', None)
                if model:
                    model = name + ' ' + model.strip()
                else:
                    model = name

                currhosts.append({
                    "OnRackID": out['Id'],
                    "ResourceName": out['Name'] + ' ' + out['Oem']['EMC']['VisionID_Chassis'],
                    "ResourceAddress": out['Id'],
                    "ResourceFamily": "Compute Server",
                    "ResourceModel": "ComputeShell",
                    "ResourceFolder": "Compute",
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
                    "Serial Number": out['SerialNumber'],
                    "Model": model,
                    "VisionID IP": out['Oem']['EMC']['VisionID_Ip'],
                    "Location": context.resource.attributes['Location'],
                })
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

            roots = [
                ResourceInfoDto('Compute Server', 'ComputeShell', guid2currhost[guid]['ResourceName'], guid2currhost[guid]['ResourceAddress'], guid2currhost[guid]['ResourceFolder'], '', guid2currhost[guid]['ResourceDescription'])
                for guid in to_create_guids
                ]

            rootsubs = []
            for guid in to_create_guids:
                for sub in guid2currhost[guid]['ResourceSubresources']:
                    rootsubs.append(ResourceInfoDto(sub['ResourceFamily'], sub['ResourceModel'], sub['ResourceName'], sub['ResourceAddress'], '', guid2currhost[guid]['ResourceName'], sub['ResourceDescription']))

            onracksubs = [
                ResourceInfoDto('OnRack Discoverable', 'OnRack Discovered Resource', guid2currhost[guid]['ResourceName'], guid2currhost[guid]['ResourceAddress'], '', context.resource.fullname, '')
                for guid in to_create_guids
                ]

            csapi.CreateResources(roots + rootsubs + onracksubs)
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

