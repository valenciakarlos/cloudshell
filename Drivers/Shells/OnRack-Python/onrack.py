import time
import json
import zipfile
import os
import requests
from quali_remote import rest_api_query
from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.shell.core.context import InitCommandContext, ResourceCommandContext
from cloudshell.api.cloudshell_api import CloudShellAPISession as cs_api
from quali_utils.quali_packaging import PackageEditor


class OnRack(ResourceDriverInterface):
    def populate_resources(self, context):
        """
        :param ResourceCommandContext context: the context the command runs on
        """
        self.reservationid = context.reservation.reservation_id
        self._cs_session(context=context)
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
                models_to_create[resources_to_create[res]['Attrs']['Model Name']] = 'Compute'  # TODO For Network, need better logic

        pack_loc = self._create_qualli_package(families_to_create, models_to_create, resources_to_create, self.address)
        self._import_package(pack_loc)

    def deploy_esxs(self, context):
        """
        :param ResourceCommandContext context: the context the command runs on
        """

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
        self._cs_session(context=context)
        self.address = context.resource.address
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
        self._logger("Response is: " + out)
        out = json.loads(out)
        auth_token = out['response']['user']['authentication_token']
        return auth_token

    def _list_all_systems(self, address, api_token):
        url = 'https://' + address + '/rest/v1/ManagedSystems/Systems'
        token_header = {'Authentication-Token': api_token}
        try:
            out = rest_api_query(url=url, user='', password='', method='get', body='', is_body_json=False,
                                 return_xml=True, header=token_header)
        except Exception, e:
            self._logger("Got Error while trying to get all OnRack Systems: " + str(e))
            self._WriteMessage("Got Error while trying to get all OnRack Systems: " + str(e))
            raise Exception("Got Error while trying to get all OnRack Systems: " + str(e))
        out = json.loads(out)
        members = out['Links']['Members']
        system_list = []
        for member in members:
            system_list.append(member['href'])
        return system_list

    def _list_all_nodes(self, address):
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
        return node_dict

    def _get_system_info(self, address, api_token, system_url):
        url = 'https://' + address + '/' + system_url
        token_header = {'Authentication-Token': api_token}
        try:
            out = rest_api_query(url=url, user='', password='', method='get', body='', is_body_json=False,
                                 return_xml=True, header=token_header)
        except Exception, e:
            self._logger("Got Error while trying to get all OnRack Systems: " + str(e))
            self._WriteMessage("Got Error while trying to get all OnRack Systems: " + str(e))
            raise Exception("Got Error while trying to get all OnRack Systems: " + str(e))

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
        return system_info, id

    def _create_qualli_package(self, families, models, resources, onrack_ip):
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
            folder = 'OnRackImport'
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
        return zip_location

    def _import_package(self, pack_path):
        r = requests.put('http://localhost:9000/Api/Auth/Login',
                         {"username": "admin", "password": "admin", "domain": "Global"})
        authcode = "Basic " + r._content[1:-1]
        fileobj = open(pack_path, 'rb')
        r = requests.post('http://localhost:9000/API/Package/ImportPackage', headers={"Authorization": authcode},
                        files={"file": fileobj})
        fileobj.close()

a = OnRack()
# print a._get_onrack_api_token('10.10.111.90', 'admin', 'admin123')
list = a._list_all_systems('10.10.111.90', a._get_onrack_api_token('10.10.111.90', 'admin', 'admin123'))
dict = a._list_all_nodes('10.10.111.90')

families_to_create = ['Compute']  # TODO Add Network Family
models_to_create = {}
resources_to_create = {}
for system in list:
    sys_info, id = a._get_system_info('10.10.111.90', a._get_onrack_api_token('10.10.111.90', 'admin', 'admin123'),
                                      system)
    if sys_info:
        resources_to_create[sys_info['Hostname']] = dict[id]
        resources_to_create[sys_info['Hostname']]['Attrs'] = sys_info

for res in resources_to_create:
    if resources_to_create[res]['Attrs']['Model Name'] not in models_to_create:
        models_to_create[resources_to_create[res]['Attrs']['Model Name']] = 'Compute'  # TODO For Network, need better logic
a._create_qualli_package(families_to_create, models_to_create, resources_to_create, '10.10.111.90')

pass