import json
import re
from time import sleep, strftime

import requests
import subprocess
from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.shell.core.driver_context import InitCommandContext, ResourceCommandContext, AutoLoadResource, \
    AutoLoadAttribute, AutoLoadDetails, CancellationContext, AutoLoadCommandContext
import cloudshell.api.cloudshell_api
from cloudshell.api.cloudshell_api import ResourceInfoDto, ResourceAttributesUpdateRequest, AttributeNameValue, PhysicalConnectionUpdateRequest
import random, string
from cloudshell.core.logger.qs_logger import get_qs_logger


def log(message):
    for _ in range(10):
        try:
            with open(r'c:\programdata\qualisystems\onrack.log', 'a') as f:
                f.write(strftime('%Y-%m-%d %H:%M:%S') + ': ' + message + '\r\n')
            return
        except:
            sleep(random.randint(5))


def rest_json(method, url, bodydict, token):
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }
    if token:
        headers['Authentication-Token'] = token
    log('url=%s method=%s bodydict=%s token=%s' % (url, method, str(bodydict), str(token)))
    o = requests.request(method.upper(), url, data=(json.dumps(bodydict) if bodydict else ''), headers=headers, verify=False)
    log('result=%s' % (str(o.text)))
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
        self.logger = get_qs_logger("resources", "QS", "onrack")
        pass

    def initialize(self, context):
        """
        Initialize the driver session, this function is called everytime a new instance of the driver is created
        This is a good place to load and cache the driver configuration, initiate sessions etc.
        :param InitCommandContext context: the context the command runs on
        """
        pass

    #remote command
    def deploy_os(self, context, ports, os_type):
        """
        A simple example function
        :param ResourceCommandContext context: the context the command runs on
        """

        csapi = cloudshell.api.cloudshell_api.CloudShellAPISession(context.connectivity.server_address,
                                                                   port=context.connectivity.cloudshell_api_port,
                                                                   token_id=context.connectivity.admin_auth_token)

        onrack = ['/'.join(r.Name.split('/')[0:-1]) for r in csapi.GetResourceDetails(context.resource.fullname).ChildResources if r.Name.endswith('/OnRack')][0]
        od = csapi.GetResourceDetails(onrack)
        onrack_ip = od.Address
        onrack_username = [a.Value for a in od.ResourceAttributes if a.Name == 'OnRack Username'][0]
        # onrack_password = csapi.DecryptPassword([a.Value for a in od.ResourceAttributes if a.Name == 'OnRack Password'][0]).Value
        onrack_password = [a.Value for a in od.ResourceAttributes if a.Name == 'OnRack Password'][0]

        tries = 0
        while tries < 5:
            token = rest_json('post', 'https://' + onrack_ip + '/login', {'email': onrack_username, 'password': onrack_password}, '')['response']['user']['authentication_token']

            onrack_res_id = context.resource.attributes['OnRackID']
            taskid = rest_json('post', 'https://' + onrack_ip + '/redfish/v1/Systems/' + onrack_res_id + '/OEM/OnRack/Actions/BootImage', {
                'domain': context.resource.attributes['ESX Domain'],
                'hostname': context.resource.fullname,
                'repo': context.resource.attributes['ESX Repo URL'],
                'version': context.resource.attributes['ESX Version'],
                'osName': 'ESXi',
                'networkDevices': [
                    {
                        'device': 'vmnic0',
                        'ipv4': {
                            'netmask': context.resource.attributes['ESX Netmask'],
                            'ipAddr': context.resource.address,
                            'gateway': context.resource.attributes['ESX Gateway'],
                        }
                    }
                ],
                # 'rootPassword': csapi.DecryptPassword(context.resource.attributes['ESX Root Password']).Value,
                'rootPassword': context.resource.attributes['ESX Root Password'],
                'dnsServers': [
                    context.resource.attributes['ESX DNS1'],
                    context.resource.attributes['ESX DNS2'],
                ]
            }, token)['Id']

            state = 'no-state'
            waited = 0
            while True:
                state = rest_json('get', 'https://' + onrack_ip + '/redfish/v1/TaskService/Tasks/' + taskid, None, token)['TaskState']
                if state == 'Running':
                    waited += 1
                    if waited > 60:
                        break
                    sleep(10)
                elif state in ['Completed', 'Exception', 'Killed']:
                    break

            if state == 'Completed':
                sleep(100)
                ping = subprocess.check_output(['ping', '-n', '1', context.resource.address], stderr=subprocess.STDOUT)
                if 'host unreachable' not in ping and '0% loss' in ping:
                    return

            tries += 1

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
        username = context.resource.attributes['OnRack Username']
        # password = csapi.DecryptPassword(context.resource.attributes['OnRack Password']).Value
        password = context.resource.attributes['OnRack Password']

        token = rest_json('post', 'https://' + onrack_ip + '/login', { 'email': username, 'password': password }, '')['response']['user']['authentication_token']

        systemlist = [x['@odata.id'].split('/')[-1]
                      for x in rest_json('get', 'https://' + onrack_ip + '/redfish/v1/Systems', None, token)['Members']]

        nodeid2eths = {}

        for node in rest_json('get', 'http://' + onrack_ip + ':8080/api/1.1/nodes', None, token):
            for ifname, ifdata in rest_json('get', 'http://' + onrack_ip + ':8080/api/1.1/nodes/' + node['id'] + '/catalogs/ohai', None, token)['data']['network']['interfaces'].iteritems():
                if ifdata.get('encapsulation', '') != 'Ethernet':
                    continue
                if node['id'] not in nodeid2eths:
                    nodeid2eths['id'] = []
                eth = {
                    'ResourceFamily': 'Port',
                    'ResourceModel': 'Resource Port',
                    'ResourceName': ifname,
                    'ResourceAddress': 'no-ohai-address',
                    'MTU': ifdata['mtu'],
                }
                nodeid2eths['id'].append(eth)
                for addr, addrdata in ifdata['addresses'].iteritems():
                    if addrdata['family'] == 'lladdr':
                        eth['MAC Address'] = addr
                        eth['ResourceAddress'] = addr
                    elif addrdata['family'] == 'inet':
                        eth['IPv4 Address'] = addr
                    elif addrdata['family'] == 'inet6':
                        eth['IPv6 Address'] = addr

        currhosts = [{'a': 'b'}]
        if True:
            currhosts = []
        for system in systemlist:
            url = 'https://' + onrack_ip + "/redfish/v1/Systems/" + system
            out = rest_json('get', url, None, token)
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
                    "ResourceAddress": out['SerialNumber'],
                    "ResourceFamily": "Compute Server",
                    "ResourceModel": "ComputeShell",
                    "ResourceFolder": "Compute",
                    "ResourceDescription": out['Oem']['EMC']['VisionID_System'],
                    "ResourceSubresources": nodeid2eths.get(system, []) + [{
                        'ResourceFamily': 'Power Port',
                        'ResourceModel': 'Generic Power Port',
                        'ResourceName': 'OnRack',
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
                log('Skipping system %s' % url)

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
                        rootsubs.append(ResourceAttributesUpdateRequest(sub['ResourceName'], attrs))


            onracksubs = [
                ResourceAttributesUpdateRequest(context.resource.fullname + '/' + host['ResourceName'],
                                                [
                                                    AttributeNameValue('Model', host['Model']),
                                                    AttributeNameValue('Serial Number', host['Serial Number']),
                                                    AttributeNameValue('OnRackID', host['OnRackID']),
                                                ])
                for host in currhosts
                ]
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
