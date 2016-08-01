import time
import json
import zipfile
import os
import requests
from quali_remote import rest_api_query, powershell
from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.shell.core.context import InitCommandContext, ResourceCommandContext
from cloudshell.api.cloudshell_api import CloudShellAPISession as cs_api
from quali_utils.quali_packaging import PackageEditor


class OnRack(ResourceDriverInterface):
    def populate_resources(self, context):
        """
        :param ResourceCommandContext context: the context the command runs on
        """
        self._logger("Starting to Populate OnRack Resources")
        self.reservationid = context.reservation.reservation_id
        self._cs_session(context=context)
        self._WriteMessage("starting to Populate OnRack Resources")
        folder = "OnRackImport"
        token = self._get_onrack_api_token(self.address, self.user, self.password)
        systemlist = self._list_all_systems(self.address, token)
        nodelist = self._list_all_nodes(self.address)
        resources_to_create = {}
        for system in systemlist:
            sys_info, id = self._get_system_info(self.address, token, system)
            if sys_info:
                resources_to_create[sys_info['Hostname']] = nodelist[id]
                resources_to_create[sys_info['Hostname']]['Attrs'] = sys_info

        families_to_create = ['Compute']  # TODO Add Network Family
        models_to_create = {}
        if resources_to_create == {}:
            message = "No Usable Resources Found, check the logs for more information"
            self._logger(message + '\r\n' + "System List: " + str(systemlist) + '\r\n' + "Node List: " + str(nodelist))
            self._WriteMessage(message)
            raise Exception(message)

        for res in resources_to_create:
            if resources_to_create[res]['Attrs']['Model Name'] not in models_to_create:
                models_to_create[
                    resources_to_create[res]['Attrs']['Model Name']] = 'Compute'  # TODO For Network, need better logic

        pack_loc = self._create_quali_package(families_to_create, models_to_create, resources_to_create, self.address,
                                              folder)
        self._import_package(pack_loc)
        resource_to_add = []
        for res in resources_to_create:
            resource_to_add.append(resources_to_create[res]['Attrs']['System'])
        self._add_resource_to_reservation(resources_to_create, folder)
        self._WriteMessage("OnRack Populate Resources Finished")
        self._logger("OnRack Populate Resources Finished")

    def deploy_esxs(self, context):
        """
        :param ResourceCommandContext context: the context the command runs on
        """
        self._logger("Starting to Deploy ESXis on OnRack Resources")
        self.reservationid = context.reservation.reservation_id
        self._cs_session(context=context)
        self._WriteMessage("Starting to Deploy ESXis on OnRack Resources")
        folder = "OnRackImport"
        token = self._get_onrack_api_token(self.address, self.user, self.password)
        systemlist = self._list_all_systems(self.address, token)
        nodelist = self._list_all_nodes(self.address)
        resources_to_create = {}
        for system in systemlist:
            sys_info, id = self._get_system_info(self.address, token, system)
            if sys_info:
                resources_to_create[sys_info['Hostname']] = nodelist[id]
                resources_to_create[sys_info['Hostname']]['Attrs'] = sys_info
        esx_info_matrix = context.resource.attributes['DeployTable']
        esx_gateway = context.resource.attributes['ESX Gateway']
        esx_dns1 = context.resource.attributes['ESX DNS1']
        esx_dns2 = context.resource.attributes['ESX DNS2']
        esx_root_password = context.resource.attributes['ESX Root Password']
        esx_domain = context.resource.attributes['ESX Domain']

        deploy_dict = {}
        found_mac = []
        length = 0
        for esx in esx_info_matrix.split(';'):
            mac = esx.split(',')[0]
            if (mac != 'MAC') and (mac != ''):
                length += 1
                hostname = esx.split(',')[1]
                ip = esx.split(',')[2]
                for resource in resources_to_create:
                    for eth in resources_to_create[resource]:
                        if type(resources_to_create[resource][eth]) is dict:
                            continue

                        if str(resources_to_create[resource][eth]) == str(mac):
                            deploy_dict[hostname] = [mac, ip, esx_root_password, esx_dns1, esx_dns2, esx_gateway,
                                                     esx_domain, resources_to_create[resource]['Attrs']['OnRackID'],
                                                     resources_to_create[resource]['Attrs']['System']]
                            found_mac.append(mac)
                            break
        self._logger("Deploy ESX Dict: " + str(deploy_dict))
        unsolved = ''
        if len(found_mac) != length:
            for esx in esx_info_matrix.split(';'):
                mac = esx.split(',')[0]
                if (mac != 'MAC') and (mac != ''):
                    hostname = esx.split(',')[1]
                    if mac not in found_mac:
                        unsolved += "Was not able to find Hardware for: " + hostname + " MAC: " + mac + '\n'

        if unsolved:
            message = str(unsolved)
            self._logger(message)
            self._WriteMessage(message)
        duplicate_deploy = deploy_dict
        num_retries = 3
        for x in xrange(num_retries):  # Number of retires
            task_ids = {}
            for esx in deploy_dict:
                task_id = self._deploy_image(onrack_address=self.address, api_token=token,
                                             onrack_res_id=deploy_dict[esx][7], esx_ip=deploy_dict[esx][1],
                                             esx_dns1=deploy_dict[esx][3], esx_dns2=deploy_dict[esx][4],
                                             esx_gateway=deploy_dict[esx][5], esx_domain=deploy_dict[esx][6],
                                             esx_hostname=esx, esx_password=deploy_dict[esx][2])
                task_ids[task_id] = esx
                deploy_dict[esx].append(task_id)
                self._set_resource_livestatus(deploy_dict[esx][8], 'Installing', 'Installing ESX', folder)
                # OnRack VooDoo if commands being sent too fast.
                time.sleep(1)
            self._logger("Task IDs for Deployment: " + str(task_ids))
            deployed, esx_states = self._wait_fo_tasks_to_complete(task_ids, 100, 15)
            if deployed:
                esx_list = []
                for esx in duplicate_deploy:
                    self._set_resource_livestatus(duplicate_deploy[esx][8], 'Completed successfully', 'ESX Installed',
                                                  folder)
                    self._update_esx_resource(duplicate_deploy[esx][8], esx, duplicate_deploy[esx][1], folder)
                    esx_list.append(esx)

                message = "Successfully deployed all ESXis: " + str(esx_list)
                self._WriteMessage(message)
                self._logger(message + " on retry number: " + str(x))
                ping_retires = 60
                pingable = []
                for x in xrange(3):
                    for esx in deploy_dict:
                        ip_addr = deploy_dict[esx][1]
                        if esx not in pingable:
                            if self._ping_check(ip_addr, ping_retires):
                                pingable.append(esx)
                                self._set_resource_livestatus(deploy_dict[esx][8], 'Online', 'ESX host available',
                                                              folder)
                            else:
                                self._set_resource_livestatus(deploy_dict[esx][8],  'Offline', 'ESX host not available',
                                                              folder)

                if len(pingable) != len(deploy_dict):
                    message = "ESXs Failed to reply to ping check, please check the logs or manually adjust the IP " \
                              "addresses."
                    self._WriteMessage(message)
                    self._logger(message + " ESX that replayed: " + str(pingable))
                    raise Exception(message)
                exit(0)
            else:
                for esx_state in esx_states:
                    if esx_states[esx_state] == 'Completed':
                        for esx in deploy_dict:
                            if esx_state == deploy_dict[esx][9]:
                                deploy_dict.pop(esx)
                                break

        message = "Failed to deployed all ESXis after " + str(num_retries) + " retries"
        self._WriteMessage(message)
        self._logger(message)
        raise Exception(message)

    def _logger(self, message, path=r'c:\ProgramData\QualiSystems\OnRack.log'):
        try:
            time.strptime(message[:19], '%Y-%m-%d %H:%M:%S')
        except ValueError:
            message = time.strftime('%Y-%m-%d %H:%M:%S') + ' ' + message

        if not (message.endswith('\r\n')) or not (message.endswith('\n')):
            message += '\r\n'
        mode = 'a'
        with open(path, mode=mode) as f:
            f.write(message)
        f.close()

    def cleanup(self):
        pass

    def __init__(self):
        pass

    def _cs_session(self, context):
        self.cs_api = cs_api
        self.admin_token = context.connectivity.admin_auth_token
        self.server_address = context.connectivity.server_address
        self.session = self.cs_api(self.server_address, token_id=self.admin_token, domain='Global')
        self._logger("Connected to Cloudshell API")

    def initialize(self, context):
        """
        Initialize the driver session, this function is called every-time a new instance of the driver is created
        This is a good place to load and cache the driver configuration, initiate sessions etc.
        :param InitCommandContext context: the context the command runs on
        """
        # self._cs_session(context=context)
        # self.address = context.resource.address
        self.address = context.resource.attributes["OnRack Address"]
        self.attrs = context.resource.attributes
        self.user = context.resource.attributes["OnRack Username"]
        self.password = context.resource.attributes["OnRack Password"]
        # self.password = self.session.DecryptPassword(self.encrypted).Value
        self.name = context.resource.name

    def _WriteMessage(self, message):
        self.session.WriteMessageToReservationOutput(self.reservationid, message)

    def _get_onrack_api_token(self, address, email, password):
        data = '''
        {"email": "''' + email + '''",
         "password": "''' + password + '''"
        }
        '''
        url = 'https://' + address + '/login'
        try:
            out = rest_api_query(url=url, user='', password='', method='post', body=data, is_body_json=True,
                                 return_xml=True)
        except Exception, e:
            self._logger("Got Error while trying to get API token: " + str(e))
            self._WriteMessage("Got Error while trying to get API token: " + str(e))
            raise Exception("Got Error while trying to get API token: " + str(e))
        self._logger("Response From Getting OnRack API Token is: " + out)
        out = json.loads(out)
        auth_token = out['response']['user']['authentication_token']
        return auth_token

    def _list_all_systems(self, address, api_token):
        self._logger("Getting all OnRack Registered Systems...")
        url = 'https://' + address + '/redfish/v1/Systems'
        token_header = {'Authentication-Token': api_token}
        try:
            out = rest_api_query(url=url, user='', password='', method='get', body='', is_body_json=False,
                                 return_xml=True, header=token_header)
        except Exception, e:
            self._logger("Got Error while trying to get all OnRack Systems: " + str(e))
            self._WriteMessage("Got Error while trying to get all OnRack Systems: " + str(e))
            raise Exception("Got Error while trying to get all OnRack Systems: " + str(e))
        out = json.loads(out)
        members = out['Members']
        system_list = []
        for member in members:
            system_list.append(member['@odata.id'])
        self._logger("All OnRack Registered Systems: " + str(system_list))
        return system_list

    def _list_all_nodes(self, address):
        self._logger("Getting All OnRack Nodes....")
        url = 'http://' + address + ':8080/api/1.1/nodes'
        try:
            out = rest_api_query(url=url, user='', password='', method='get', body='', is_body_json=False,
                                 return_xml=True)
        except Exception, e:
            self._logger("Got Error while trying to get all OnRack Nodes: " + str(e))
            self._WriteMessage("Got Error while trying to get all OnRack Nodes: " + str(e))
            raise Exception("Got Error while trying to get all OnRack Nodes: " + str(e))
        out = json.loads(out)
        node_dict = {}
        for node in out:
            if node['type'] == 'compute':
                node_dict[node['id']] = {}
                num = 0
                for id in node['identifiers']:
                    node_dict[node['id']]["eth" + str(num)] = id
                    num += 1
        self._logger("All OnRack Nodes: " + str(node_dict))
        return node_dict

    def _get_system_info(self, address, api_token, system_url):
        # 'new' RESP API /redfish/v1/System/{ID} doesnt have full details as the below
        url = 'https://' + address + '/' + system_url
        token_header = {'Authentication-Token': api_token}
        try:
            out = rest_api_query(url=url, user='', password='', method='get', body='', is_body_json=False,
                                 return_xml=True, header=token_header)
        except Exception, e:
            self._logger("Got Error while trying to get OnRack System: " + str(e))
            self._WriteMessage("Got Error while trying to get OnRack System: " + str(e))
            raise Exception("Got Error while trying to get OnRack System: " + str(e))

        out = json.loads(out)
        id = out['Id']
        if out['Oem'] == {}:
            return None, id
        system_info = {
            'Hostname': out['Oem']['EMC']['VisionID_Chassis'],
            'OnRackID': out['Id'],
            'Serial Number': out['SerialNumber'],
            'Model Name': out['Model'],
            'IP Address': out['Oem']['EMC']['VisionID_Ip'],
            'System': out['Oem']['EMC']['VisionID_System'],
            'Name': out['Name'],
        }
        self._logger("OnRack System Info: " + str(system_info))
        return system_info, id

    def _create_quali_package(self, families, models, resources, onrack_ip, folder):
        self._logger("Creating Package for Import")
        zip_location = 'c:\\deploy\\OnRackImport.zip'
        pack = PackageEditor()
        pack.create(zip_location)
        pack.load(zip_location)
        for family in families:
            pack.add_family(family_name=family, description='Created via OnRack', categories='', connectable=False,
                            admin_only=False, shared_by_default=False, service_family=False, searchable=True)
        for model in models:
            pack.add_model_to_family(family_name=models[model], model_name=model, description='Created via OnRack')
        attributes = []
        for resource in resources:
            for att in resources[resource]['Attrs']:
                if att not in ['Hostname', 'IP Address', 'Name', 'System']:
                    pack.add_or_update_attribute(attribute_name=att, default_value='', description='Created via onRack',
                                                 attribute_type='String', lookup_values='',
                                                 rules=['Configuration', 'Setting'])
                    if att not in attributes:
                        attributes.append(att)
        pack.add_or_update_attribute(attribute_name='OnRackIP', default_value='',
                                     description='Created via onRack', attribute_type='String', lookup_values='',
                                     rules=['Configuration', 'Setting'])
        attributes.append('OnRackIP')

        for family in families:
            for att in attributes:
                pack.attach_attribute_to_family(family_name=family, attribute_name=att, user_input=False,
                                                allowed_values='')

        zip_hack = zipfile.ZipFile(zip_location, 'a')
        for resource in resources:
            res_name = resources[resource]['Attrs']['System']
            res_model = resources[resource]['Attrs']['Model Name']
            res_add = resources[resource]['Attrs']['IP Address']
            res_attrs = resources[resource]['Attrs']
            xml = '<?xml version="1.0" encoding="utf-8"?> \n'
            xml += '''<ResourceInfo xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" Name="''' + res_name + '''"  Address="''' + \
                   res_add + '''" ModelName="''' + res_model + '" FolderFullPath="' + folder + \
                   '''" xmlns="http://schemas.qualisystems.com/ResourceManagement/ResourceSchema.xsd"> \n'''
            xml += '<Attributes> \n'
            for att in attributes:
                if att == 'OnRackIP':
                    xml += '<Attribute Name="' + att + '" Value="' + onrack_ip + '" /> \n'
                else:
                    xml += '<Attribute Name="' + att + '" Value="' + res_attrs[att] + '" /> \n'
            xml += ' </Attributes> \n'
            xml += '</ResourceInfo>'

            with open('''c:\\deploy\\''' + res_name + '.xml', 'w') as file_:
                file_.write(xml)
                file_.close()
            zip_hack.write('''c:\\deploy\\''' + res_name + '.xml', "Resources/" + res_name + '.xml')
            os.remove('''c:\\deploy\\''' + res_name + '.xml')
        self._logger("Package Created And Can Be Found At: " + zip_location)
        return zip_location

    def _import_package(self, pack_path):
        self._logger("Starting to Import Package From: " + pack_path)
        r = requests.put('http://localhost:9000/Api/Auth/Login',
                         {"username": "admin", "password": "admin", "domain": "Global"})
        authcode = "Basic " + r._content[1:-1]
        fileobj = open(pack_path, 'rb')
        r = requests.post('http://localhost:9000/API/Package/ImportPackage', headers={"Authorization": authcode},
                          files={"file": fileobj})
        fileobj.close()
        self._logger("Finishing Importing Package")

    def _add_resource_to_reservation(self, resources, folder=None):
        num = 1
        for resource in resources:
            res_name = resources[resource]['Attrs']['System']
            if folder:
                res_name = folder + '/' + res_name
            self.session.AddResourcesToReservation(reservationId=self.reservationid, resourcesFullPath=[res_name],
                                                   shared=False)
            self._logger("Added Resource \"" + res_name + "\" To Reservation " + self.reservationid)
            self._set_resource_position(res_name, 100, 110 * num)
            num += 1

    def _set_resource_position(self, resource, x, y):
        self.session.SetReservationResourcePosition(self.reservationid, resource, int(x), int(y))
        self._logger("Setting Resource Position To: " + str(x) + '/' + str(y) + " For Resource: " + resource)

    def _deploy_image(self, onrack_address, api_token, onrack_res_id, esx_ip, esx_dns1, esx_dns2, esx_gateway, esx_domain,
                      esx_hostname, esx_password, image_type='ESXi'):
        deploy_request = '''
{
	"domain": "''' + esx_domain + '''",
	"hostname": "''' + esx_hostname + '''",
    "repo": "http://172.31.128.1:8080/esxi/6.0",
    "version": "6.0",
    "osName": "''' + image_type + '''",
    "networkDevices": [
        {
            "device": "eth0",
            "ipv4": {
                "netmask": "255.255.255.0",
				"ipAddr": "''' + esx_ip + '''",
				"gateway": "''' + esx_gateway + '''"
            }
        }
    ],
	"rootPassword": "''' + esx_password + '''",
    "dnsServers": [
		"''' + esx_dns1 + '''",
        "''' + esx_dns2 + '''"
    ]
}'''
        self._logger("Deploy Request: " + deploy_request)
        url = 'https://' + onrack_address + '/redfish/v1/Systems/' + onrack_res_id + '/OEM/OnRack/Actions/BootImage'
        token_header = {'Authentication-Token': api_token}
        try:
            out = rest_api_query(url=url, user='', password='', method='post', body=deploy_request, is_body_json=True,
                                 return_xml=True, header=token_header)
        except Exception, e:
            message = "Got Error while trying to deploy from OnRack: " + str(e)
            self._logger(message)
            self._WriteMessage(message)
            raise Exception(message)
        self._logger("Deploy response: " + out)
        out = json.loads(out)
        task_id = out['Id']
        return task_id

    def _check_onrack_job_status(self, onrack_address, api_token, job_id):
        url = 'https://' + onrack_address + '/redfish/v1/TaskService/Tasks/' + job_id
        token_header = {'Authentication-Token': api_token}
        try:
            out = rest_api_query(url=url, user='', password='', method='get', body='', is_body_json=True,
                                 return_xml=True, header=token_header)
        except Exception, e:
            message = "Got Error while trying to get job status from onrack: " + str(e)
            self._logger(message)
            self._WriteMessage(message)
            raise Exception(message)
        self._logger("Job Status response: " + out)
        out = json.loads(out)
        task_state = out['TaskState']
        return task_state

    def _wait_fo_tasks_to_complete(self, task_ids, retires, retry_delay):
        completed = {}
        for x in xrange(retires):
            for job in task_ids:
                if job not in completed:
                    token = self._get_onrack_api_token(self.address, self.user, self.password)
                    state = self._check_onrack_job_status(self.address, token, job)
                    if state == 'Completed':
                        completed[job] = state
                        message = "Successfully Deploy ESX: \"" + task_ids[job] + "\""
                        self._logger(message)
                        # self._WriteMessage(message)
                    elif state == 'Running':
                        message = "Deploy is still running for: \"" + task_ids[job] + "\""
                        self._logger(message)
                    elif (state == 'Exception') or (state == 'Killed'):
                        completed[job] = state
                        message = "Failed to Deploy ESX, \"" + task_ids[job] + "\"" + " Job ID: " + job
                        self._logger(message + " Completed Dict: " + str(completed))
                        self._WriteMessage(message)
            if len(completed) == len(task_ids):
                for task in completed:
                    if completed[task] != 'Completed':
                        return False, completed
                return True, completed
            else:
                time.sleep(retry_delay)
        return False, completed

    def _set_resource_livestatus(self, resource, status, add_info, folder=None):
        if folder:
            resource = folder + "/" + resource
        self._logger("setting Resource " + resource + " Livestatus To: " + status)
        self.session.SetResourceLiveStatus(resourceFullName=resource, liveStatusName=status, additionalInfo=add_info)

    def _update_esx_resource(self, old_resource, new_name, new_address, folder=None):
        if folder:
            old_resource = folder + "/" + old_resource
            # new_name = folder + "/" + new_name
        self._logger("Updating Resource: \"" + old_resource + "\" To new name: \"" + new_name +
                     "\"  And new address: \"" + new_address + "\"")
        self.session.UpdateResourceAddress(old_resource, new_address)
        self.session.RenameResource(old_resource, new_name)

    def _ping_check(self, address, ping_count):
        self._logger("Checking ping for: " + address)
        script = 'ping ' + address + " -n " + str(ping_count)
        out = powershell(script)
        if '100% loss' not in out:
            return True
        else:
            return False


# a = OnRack()
# # print a._get_onrack_api_token('10.10.111.90', 'admin', 'admin123')
# list = a._list_all_systems('10.10.111.90', a._get_onrack_api_token('10.10.111.90', 'admin', 'admin123'))
# dict = a._list_all_nodes('10.10.111.90')
#
# families_to_create = ['Compute']  # TODO Add Network Family
# models_to_create = {}
# resources_to_create = {}
# for system in list:
#     sys_info, id = a._get_system_info('10.10.111.90', a._get_onrack_api_token('10.10.111.90', 'admin', 'admin123'),
#                                       system)
#     if sys_info:
#         resources_to_create[sys_info['Hostname']] = dict[id]
#         resources_to_create[sys_info['Hostname']]['Attrs'] = sys_info
#
# for res in resources_to_create:
#     if resources_to_create[res]['Attrs']['Model Name'] not in models_to_create:
#         models_to_create[
#             resources_to_create[res]['Attrs']['Model Name']] = 'Compute'  # TODO For Network, need better logic
# a._create_qualli_package(families_to_create, models_to_create, resources_to_create, '10.10.111.90')

pass