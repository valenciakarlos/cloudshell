#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#
# Only edit the copy of this file at Common Scripts/steps.py !!!!!!!
#
# Other copies will be overwritten by create package.cmd!!!!
#
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
import json
import os
from threading import Thread
from time import sleep
import subprocess
import time

import requests
from cloudshell.helpers.scripts import cloudshell_scripts_helpers as helpers
from cloudshell.api.cloudshell_api import InputNameValue, CloudShellAPISession

from quali_remote import qs_info, qs_error


#
# import zipfile
#
#
# tempdir = os.path.normpath(os.path.dirname(__file__) + '\\..\\temp')
# os.makedirs(tempdir)
#
# with zipfile.ZipFile(os.path.dirname(__file__), "r") as z:
#     z.extractall(tempdir)
#
# #extract the inner zip to site-packages
# with zipfile.ZipFile((tempdir + "\\sitepack.zip"), "r") as z:
#     z.extractall("C:\\Program Files (x86)\\QualiSystems\\TestShell\\ExecutionServer\\python\\2.7.10\\Lib\\site-packages\\")
#
# print os.path.normpath(tempdir + "\\sitepack.zip") + " unzipped"


# copy {Project.LogPath} {strreplace(Project.LogPath,'.log','.' + currenttime2str('yyyy-MM-dd HH-mm-ss') + '.log')}
# {Project.LogPath} {currenttime2str}: Log file cleared


def inranges(n, rs):
    if not rs:
        return True
    for r in rs.split(','):
        r = r.strip()
        if not r:
            continue
        if r.lower() == 'all':
            return True
        if r.lower() == 'none':
            return False
        if '-' in r:
            start, end = r.split('-')
        else:
            start = r
            end = r
        if start == 'end':
            start = 1000000
        if end == 'end':
            end = 1000000
        start = int(start)
        end = int(end)
        if start <= n <= end:
            return True
    return False


class ServiceSleep:
    def __init__(self, service_model, seconds, message=''):
        """
        :param service_model: str
        :param seconds: int
        :param message: str
        """
        self.service_model = service_model
        self.seconds = seconds
        self.message = message

    def __repr__(self):
        return 'sleep,,,"%d seconds%s"' % (self.seconds, ' - ' + self.message if self.message else '')

    def execute(self, csapi, resid, resdetails, simulated):
        """
        :param csapi: CloudShellAPISession
        :param resid: str
        :param simulated: bool
        :return: str
        """
        rv = ''
        for svc in resdetails.Services:
            if self.service_model == svc.ServiceName:
                if self.message:
                    if not simulated:
                        qs_info('Sleeping %d seconds - %s ' % (self.seconds, self.message), filename='orchestration')
                    else:
                        rv += str(self) + '\n'
                if not simulated:
                    sleep(self.seconds)
        return rv


class ServicePrint:
    def __init__(self, service_model, message):
        """
        :param service_model: str
        :param message: str
        """
        self.service_model = service_model
        self.message = message

    def __repr__(self):
        return 'print,,,"%s"' % (self.message)

    def execute(self, csapi, resid, resdetails, simulated):
        """
        :param csapi: CloudShellAPISession
        :param resid: str
        :param simulated: bool
        :return: str
        """
        rv = ''
        for svc in resdetails.Services:
            if self.service_model == svc.ServiceName:
                if not simulated:
                    qs_info(self.message, filename='orchestration')
                    rv += self.message + '\n'
                else:
                    rv += 'found\n'
        return rv


class ResourcePrint:
    def __init__(self, resource_model, message):
        """
        :param resource_model: str
        :param message: str
        """
        self.resource_model = resource_model
        self.message = message

    def __repr__(self):
        return 'print,,,"%s"' % (self.message)

    def execute(self, csapi, resid, resdetails, simulated):
        """
        :param csapi: CloudShellAPISession
        :param resid: str
        :param simulated: bool
        :return: str
        """
        rv = ''
        for res in resdetails.Resources:
            if self.resource_model == res.ResourceModelName:
                if not simulated:
                    qs_info(self.message, filename='orchestration')
                    rv += self.message + '\n'
                else:
                    rv += 'found\n'
        return rv


class ResourceLiveStatus:
    def __init__(self, resource_model, status, message=''):
        """
        :param status: str
        """
        self.resource_model = resource_model
        self.status = status
        self.message = message

    def __repr__(self):
        return 'resource live status,"%s","%s","%s"' % (self.resource_model, self.status, self.message)

    def execute(self, csapi, resid, resdetails, simulated):
        """
        :param csapi: CloudShellAPISession
        :param resid: str
        :param simulated: bool
        :return: str
        """
        rv = ''
        for res in csapi.GetReservationDetails(resid).ReservationDescription.Resources:
            if self.resource_model == res.ResourceModelName:
                if not simulated:
                    csapi.SetResourceLiveStatus(resid, res.Name, self.status, self.message)
                    rv += '%s %s\n' % (self.status, self.message)
                else:
                    rv += 'found\n'
        return rv


class ServiceLiveStatus:
    def __init__(self, service_model, status, message=''):
        """
        :param status: str
        """
        self.status = status
        self.service_model = service_model
        self.message = message

    def __repr__(self):
        return 'service live status,"%s","%s","%s"' % (self.service_model, self.status, self.message)

    def execute(self, csapi, resid, resdetails, simulated):
        """
        :param csapi: CloudShellAPISession
        :param resid: str
        :param simulated: bool
        :return: str
        """
        rv = ''
        for svc in resdetails.Services:
            if self.service_model == svc.ServiceName:
                if not simulated:
                    csapi.SetServiceLiveStatus(resid, self.service_model, self.status, self.message)
                    rv += '%s %s\n' % (self.status, self.message)
                else:
                    rv += 'found\n'
        return rv


class EnvironmentCommand:
    def __init__(self, command, input_dict=None, input_generator=None):
        """
        :param command: str
        :param input_dict: dict[str, str]
        :param input_generator: (CloudShellAPISession, str)->dict[str, str]
        """
        self.command = command
        self.input_dict = input_dict if input_dict else {}
        self.input_generator = input_generator

    def __repr__(self):
        return 'command,ENVIRONMENT,"%s","%s"' % (self.command, 'dynamic' if self.input_generator else str(self.input_dict))

    def execute(self, csapi, resid, resdetails, simulated):
        """
        :param csapi: CloudShellAPISession
        :param resid: str
        :param simulated: bool
        :return: str
        """
        rv = ''
        if self.input_generator:
            inp = self.input_generator(csapi, resid)
        else:
            inp = self.input_dict
        if not simulated:
            rv += csapi.ExecuteEnvironmentCommand(resid, self.command, [InputNameValue(attr, value) for attr, value in inp.iteritems()], printOutput=False).Output + '\n'
        else:
            rv += 'found\n'
        return rv


class ServiceCommand:
    def __init__(self, service_model, command, input_dict=None, input_generator=None):
        """
        :param service_model: str
        :param command: str
        :param input_dict: dict[str, str]
        :param input_generator: (CloudShellAPISession, str)->dict[str, str]
        """
        self.service_model = service_model
        self.command = command
        self.input_dict = input_dict if input_dict else {}
        self.input_generator = input_generator

    def __repr__(self):
        return 'service command,"%s","%s","%s"' % (self.service_model, self.command, 'dynamic' if self.input_generator else str(self.input_dict))

    def execute(self, csapi, resid, resdetails, simulated):
        """
        :param csapi: CloudShellAPISession
        :param resid: str
        :param simulated: bool
        :return: str
        """
        rv = ''
        for svc in resdetails.Services:
            if self.service_model == svc.ServiceName:
                if self.input_generator:
                    inp = self.input_generator(csapi, resid)
                else:
                    inp = self.input_dict
                if not simulated:
                    rv += csapi.ExecuteCommand(resid, svc.Alias, 'Service', self.command, [InputNameValue(attr, value) for attr, value in inp.iteritems()], printOutput=False).Output + '\n'
                else:
                    rv += 'found\n'
        return rv


class ResourceCommand:
    def __init__(self, resource_model, command, input_dict=None, input_generator=None):
        """
        :param resource_model: str
        :param command: str
        :param input_dict: dict[str, str]
        :param input_generator: (CloudShellAPISession, str)->dict[str, str]
        """
        self.resource_model = resource_model
        self.command = command
        self.input_dict = input_dict if input_dict else {}
        self.input_generator = input_generator

    def __repr__(self):
        return 'resource command,"%s","%s","%s"' % (self.resource_model, self.command, 'dynamic' if self.input_generator else str(self.input_dict))

    def execute(self, csapi, resid, resdetails, simulated):
        """
        :param csapi: CloudShellAPISession
        :param resid: str
        :param simulated: bool
        :return: str
        """
        es = []
        threads = []
        rvs = []
        for res in csapi.GetReservationDetails(resid).ReservationDescription.Resources:
            if self.resource_model == res.ResourceModelName:
                if self.input_generator:
                    inp = self.input_generator(csapi, resid)
                else:
                    inp = self.input_dict
                if not simulated:
                    def t(csapi1, rvs1, es1, resid1, name1, kind1, command1, args1):
                        try:
                            trv = csapi1.ExecuteCommand(resid1, name1, kind1, command1, args1, printOutput=False)
                            rvs1.append(trv)
                        except Exception as e:
                            es1.append(e)
                    th = Thread(target=t, args=(csapi, rvs, es, resid, res.Name, 'Resource', self.command, [InputNameValue(attr, value) for attr, value in inp.iteritems()]))
                    threads.append(th)
                    th.start()
                else:
                    rvs.append('found')
        for th in threads:
            th.join()
        return '\n'.join(rvs + es)


class ResourceRemoteCommand:
    def __init__(self, resource_model, command, tag, input_list=None, input_generator=None):
        """
        :param resource_model: str
        :param command: str
        :param tag: str
        :param input_list: list[str]
        :param input_generator: (CloudShellAPISession, str)->list[str]
        """
        self.resource_model = resource_model
        self.command = command
        self.tag = tag
        self.input_list = input_list if input_list else []
        self.input_generator = input_generator

    def __repr__(self):
        return 'resource remote command,"%s","%s","%s"' % (self.resource_model, self.command, 'dynamic' if self.input_generator else str(self.input_list))

    def execute(self, csapi, resid, resdetails, simulated):
        """
        :param csapi: CloudShellAPISession
        :param resid: str
        :param simulated: bool
        :return: str
        """
        rvs = []
        es = []
        threads = []
        for res in csapi.GetReservationDetails(resid).ReservationDescription.Resources:
            if self.resource_model == res.ResourceModelName:
                if self.input_generator:
                    inp = self.input_generator(csapi, resid)
                else:
                    inp = self.input_list
                if not simulated:
                    def t(csapi1, rvs1, es1, resid1, name1, command1, tag1, inp1):
                        try:
                            trv = csapi1.ExecuteResourceConnectedCommand(resid1, name1, command1, tag1, inp1, [], printOutput=False).Output
                            rvs1.append(trv)
                        except Exception as e:
                            es1.append(e)
                    th = Thread(target=t, args=(csapi, rvs, es, resid, res.Name, self.command, self.tag, inp))
                    threads.append(th)
                    th.start()
                else:
                    rvs.append('found')
        for th in threads:
            th.join()
        if len(es) > 0:
            raise Exception('One or more errors executing %s: %s' % (str(self), '\n'.join([str(x) for x in es])))
        return '\n'.join(rvs)


class ResourceEnqueuedCommand:
    def __init__(self, resource_model, command, input_list=None, input_generator=None):
        """
        :param resource_model: str
        :param command: str
        :param input_list: list[str]
        :param input_generator: (CloudShellAPISession, str)->list[str]
        """
        self.resource_model = resource_model
        self.command = command
        self.input_list = input_list if input_list else []
        self.input_generator = input_generator

    def __repr__(self):
        return 'enqueue resource command,"%s","%s","%s"' % (self.resource_model, self.command, 'dynamic' if self.input_generator else str(self.input_list))

    def execute(self, csapi, resid, resdetails, simulated):
        """
        :param csapi: CloudShellAPISession
        :param resid: str
        :param simulated: bool
        :return: str
        """
        rv = ''
        for res in csapi.GetReservationDetails(resid).ReservationDescription.Resources:
            if self.resource_model == res.ResourceModelName:
                if self.input_generator:
                    inp = self.input_generator(csapi, resid)
                else:
                    inp = self.input_list
                if not simulated:
                    rv += csapi.EnqueueResourceCommand(resid, res.Name, self.command, inp, printOutput=False) + '\n'
                else:
                    rv += 'found\n'
        return rv


class ResourceAutoloadCommand:
    def __init__(self, resource_model):
        """
        :param resource_model: str
        """
        self.resource_model = resource_model

    def __repr__(self):
        return 'resource autoload command,"%s",,' % (self.resource_model)

    def execute(self, csapi, resid, resdetails, simulated):
        """
        :param csapi: CloudShellAPISession
        :param resid: str
        :param simulated: bool
        :return: str
        """
        rv = ''
        for res in csapi.GetReservationDetails(resid).ReservationDescription.Resources:
            if self.resource_model == res.ResourceModelName:
                if not simulated:
                    rv += csapi.Autoload(res.Name) + '\n'
                else:
                    rv += 'found\n'
        return rv


def go(printmode, include_ranges='', exclude_ranges=''):
    if not include_ranges:
        include_ranges = 'all'
    if not exclude_ranges:
        exclude_ranges = 'none'
    # print 'include=' + include_ranges
    # print 'exclude=' + exclude_ranges
    # print 'go'
    csapi = helpers.get_api_session()
    # print 'got api'
    resid = helpers.get_reservation_context_details().id
    # print 'resid=' + resid

    sitemans = [r for r in csapi.GetReservationDetails(resid).ReservationDescription.Resources if r.ResourceModelName == 'SiteManagerShell']
    if len(sitemans) == 0:
        raise Exception('You must add a Site Network Manager resource to the reservation')
    siteman_details = sitemans[0]
    site_manager_attrs = dict([(a.Name, a.Value) for a in csapi.GetResourceDetails(siteman_details.Name).ResourceAttributes])

    site_manager_attrs['Interface Names For Migration'] = 'aaua'
    site_manager_attrs['Default VLAN'] = '4'
    site_manager_attrs['Management VLAN'] = '5'

    steps = [
        # EnvironmentCommand('copy_prereq'),
        # EnvironmentCommand('copy_inputs'),

        # ResourceLiveStatus('OnRack', 'Offline'),
        # ResourceAutoloadCommand('OnRack'),
        # ResourceLiveStatus('OnRack', 'Online'),
        ResourcePrint('SiteManagerShell', 'Starting deployment'),
        # todo add alias and description
        ResourceRemoteCommand('ComputeShell', 'deploy_os', 'remote_onrack', ['ESXi']),

        # ResourceCommand('Brocade NOS Switch', 'set_access_vlan', {
        #     'InterfaceNames': site_manager_attrs['Interface Names For Migration'],
        #     'VLAN_ID': site_manager_attrs['Management VLAN']
        # }),

        ServiceLiveStatus('vCenter', 'Offline'),
        ServiceCommand('vCenter', 'vcenter_01_deploy_vcenter'),
        ServiceSleep('vCenter', 60, 'Waiting for vCenter to start...'),
        ServiceCommand('vCenter', 'vcenter_02_create_infrastructure'),
        ServiceCommand('vCenter', 'vcenter_03_create_vds'),
        ServiceLiveStatus('vCenter', 'Online'),

        # ResourceCommand('Brocade NOS Switch', 'set_access_vlan', {
        #     'InterfaceNames': site_manager_attrs['Interface Names For Migration'],
        #     'VLAN_ID': site_manager_attrs['Default VLAN']
        # }),

        ServiceLiveStatus('ScaleIO', 'Offline'),
        ServiceCommand('ScaleIO', 'scaleio_01_install_sdc'),
        ServiceCommand('ScaleIO', 'scaleio_02_deploy_svm'),
        ServiceCommand('ScaleIO', 'scaleio_03_configure_svm'),
        ServiceLiveStatus('ScaleIO', 'Online'),

        ServiceSleep('NSX Manager', 300, 'Waiting for hosts to stabilize after ScaleIO installation...'),
        ServiceLiveStatus('NSX Manager', 'Offline'),
        ServiceCommand('NSX Manager', 'nsx_01_deploy_nsx'),
        ServiceSleep('NSX Manager', 200, 'Waiting for NSX to start...'),
        ServiceCommand('NSX Manager', 'nsx_02_set_sso'),
        ServiceCommand('NSX Manager', 'nsx_03_set_vcenter'),
        ServiceCommand('NSX Manager', 'nsx_04_add_nsx_admin'),
        # ServiceCommand('NSX Manager', 'nsx_05_create_ip_pools'),
        # ServiceCommand('NSX Manager', 'nsx_06_deploy_controller'),
        # ServiceCommand('NSX Manager', 'nsx_07_create_vxlan_segment'),
        # ServiceCommand('NSX Manager', 'nsx_08_install_host_vibs'),
        # ServiceCommand('NSX Manager', 'nsx_09_configure_host_vteps'),
        # ServiceCommand('NSX Manager', 'nsx_10_create_transport_zone'),
        # ServiceCommand('NSX Manager', 'nsx_11_create_logical_switch'),
        ServiceLiveStatus('NSX Manager', 'Online'),

        ServiceLiveStatus('vCloud Director', 'Offline'),
        ServiceCommand('vCloud Director', 'vcd_01_deploy_vcd'),
        ServiceCommand('vCloud Director', 'vcd_02_create_sql_db'),
        ServiceSleep('vCloud Director', 65, 'Waiting for vCD to power on...'),
        ServiceCommand('vCloud Director', 'vcd_03_create_certificates'),
        ServiceCommand('vCloud Director', 'vcd_04_install_and_configure'),
        ServiceCommand('vCloud Director', 'vcd_05_setup'),
        ServiceLiveStatus('vCloud Director', 'Online'),

        ServiceLiveStatus('vRealize Operations Manager', 'Offline'),
        ServiceCommand('vRealize Operations Manager', 'vrops_01_deploy_vrops'),
        # ServiceSleep('vRealize Operations Manager', 600, 'Waiting for vROPS VM to respond...'),
        # ServiceCommand('vRealize Operations Manager', 'vrops_02_startup_wizard'),
        # ServiceCommand('vRealize Operations Manager', 'vrops_03_start_service'),
        # ServiceCommand('vRealize Operations Manager', 'vrops_04_license'),
        # ServiceCommand('vRealize Operations Manager', 'vrops_05_vcenter_registration'),
        ServiceLiveStatus('vRealize Operations Manager', 'Online'),

        ServiceLiveStatus('vRealize Log Insight', 'Offline'),
        ServiceCommand('vRealize Log Insight', 'vlog_01_deploy_vlog'),
        # ServiceSleep('vRealize Log Insight', 600, 'Waiting for Log Insight VM to respond...'),
        # ServiceCommand('vRealize Log Insight', 'vlog_03_apply_pak_patch'),
        # ServiceCommand('vRealize Log Insight', 'vlog_04_vcenter_registration'),
        # ServiceCommand('vRealize Log Insight', 'vlog_05_vrops_registration'),
        ServiceLiveStatus('vRealize Log Insight', 'Online'),


        ServiceLiveStatus('vRealize Automation', 'Offline'),
        ServiceCommand('vRealize Automation', 'vra_01_deploy_vra'),
        # todo vRealize other steps commented
        ServiceLiveStatus('vRealize Automation', 'Online'),

        ServiceLiveStatus('Nagios Monitoring', 'Offline'),
        ServiceCommand('Nagios Monitoring', 'nagios_01_deploy_nagios'),
        ServiceSleep('Nagios Monitoring', 100, 'Waiting for Nagios to start...'),
        ServiceCommand('Nagios Monitoring', 'nagios_02_configure_nagios'),
        ServicePrint('Nagios Monitoring', 'Successfully configured Nagios'),
        ServiceCommand('Nagios Registration', 'RegisterResources', lambda api, resid: {
            'ResourceNames': ','.join([r.Name
                                       for r in api.GetReservationDetails(resid).ReservationDescription.Resources
                                       if r.ResourceModel == 'Compute Server'])
        }),
        ServicePrint('Nagios Registration', 'Successfully registered ESX hosts'),

        ResourceEnqueuedCommand('NagiosServer', 'Start'),

        ServiceCommand('Nagios Monitoring', 'Enable'),
        ServiceLiveStatus('Nagios Monitoring', 'Online'),

        ServiceLiveStatus('Versa Director', 'Offline'),
        ServiceCommand('Versa Director', 'versa_01_deploy_director'),
        ServiceCommand('Versa Director', 'versa_02_deploy_analytics'),
        ServiceCommand('Versa Director', 'versa_03_deploy_controller'),
        ServiceCommand('Versa Director', 'versa_04_deploy_branch1'),
        ServiceCommand('Versa Director', 'versa_05_deploy_branch2'),
        ServiceSleep('Versa Director', 100, 'Waiting for Versa to finish rebooting...'),
        ServiceCommand('Versa Director', 'versa_06_post_deployment_configurations'),
        ServiceSleep('Versa Director', 5),
        ServiceCommand('Versa Director', 'versa_07_organization_administration'),
        ServiceSleep('Versa Director', 5),
        ServiceCommand('Versa Director', 'versa_08_create_controller'),
        ServiceSleep('Versa Director', 45),
        ServiceCommand('Versa Director', 'versa_09_controller_administration'),
        ServiceSleep('Versa Director', 5),
        ServiceCommand('Versa Director', 'versa_10_organization_configurations'),
        ServiceSleep('Versa Director', 5),
        ServiceCommand('Versa Director', 'versa_11_create_analytics'),
        ServiceSleep('Versa Director', 5),
        ServiceCommand('Versa Director', 'versa_12_ipsec_profiles'),
        ServiceSleep('Versa Director', 5),
        ServiceCommand('Versa Director', 'versa_13_bracnh_administration'),
        ServiceSleep('Versa Director', 5),
        ServiceCommand('Versa Director', 'versa_14_template_configurations_1'),
        ServiceSleep('Versa Director', 5),
        ServiceCommand('Versa Director', 'versa_15_template_configurations_2'),
        ServiceSleep('Versa Director', 5),
        ServiceCommand('Versa Director', 'versa_16_branches_startup_configurations'),
        ServiceSleep('Versa Director', 20, 'Finished Versa configurations, waiting for Versa Director to configure the Branches...'),
        ServiceLiveStatus('Versa Director', 'Online'),

    ]

    csv = ''

    # print 'getting details'
    resdetails = csapi.GetReservationDetails(resid).ReservationDescription
    csapi.WriteMessageToReservationOutput(resid, 'Log folder: c:\\ProgramData\\QualiSystems\\Logs\\%s' % resid)
    # csapi.WriteMessageToReservationOutput(resid, 'Log folder: file://c:/ProgramData/QualiSystems/Logs/%s' % resid)
    haderror = False
    for i, step in enumerate(steps):
        if inranges(i, include_ranges) and not inranges(i, exclude_ranges):
            # print 'included'
            if not printmode and not isinstance(step, ResourcePrint) and not isinstance(step, ServicePrint):
                qs_info('Starting step #%d: %s' % (i, str(step)), filename='orchestration')
            try:
                result = step.execute(csapi, resid, resdetails, printmode)
                if result:
                    if printmode:
                        csv += '%d,%s\n' % (i, str(step))
            except Exception as e:
                qs_error('Error on step #%d: %s' % (i, str(e)))
                haderror = True
                break
            if not printmode and not isinstance(step, ResourcePrint) and not isinstance(step, ServicePrint):
                qs_info('Finished step #%d: %s' % (i, str(step)), filename='orchestration')
    if haderror:
        print 'Orchestration failed at step %d. Check the Output window for details.' % i
        exit(1)
    if printmode:
        con_details = helpers.get_connectivity_context_details()
        env_details = helpers.get_reservation_context_details()
        token1 = json.loads(os.environ['QUALICONNECTIVITYCONTEXT'])['adminAuthToken']
        # pw = con_details.admin_pass
        # pw = 'admin'
        # pw = csapi.DecryptPassword(con_details.admin_pass).Value
        token2 = requests.put('http://%s:%d/API/Auth/Login' % (con_details.server_address, 9000),
                              headers={'Content-Type': 'application/x-www-form-urlencoded'},
                              # data='username=%s&password=%s&domain=%s' % (con_details.admin_user, pw, env_details.domain)).content
                              data='token=%s&domain=%s' % (token1, env_details.domain)).content

        if token2.startswith('"') and token2.endswith('"'):
            token2 = token2[1:-1]

        # print os.environ
        # print token2
        # print con_details.admin_user
        # print pw
        # print env_details.domain
        print csv
        j = requests.post('http://%s:%s/Api/Package/AttachFileToReservation' % (con_details.server_address, 9000),
                          headers={
                              'Authorization': 'Basic ' + token2,
                          },
                          files={
                              'QualiPackage': ('QualiPackage', csv),
                              'reservationId': ('reservationId', env_details.id),
                              'saveFileAs': ('saveFileAs', 'steps.csv'),
                              'overwriteIfExists': ('overwriteIfExists', 'True'),
                          })
        print j.status_code
        print j.text
        print 'steps.csv has been attached to the reservation.\n\nReload the page and click the paperclip icon to download the file.'
