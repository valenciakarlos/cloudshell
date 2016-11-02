import json
import subprocess
import tempfile
import uuid
import os
import paramiko
import time

import traceback
import sys

import requests

from cloudshell.core.logger.qs_logger import get_qs_logger
from cloudshell.helpers.scripts import cloudshell_scripts_helpers as helpers
from cloudshell.api.cloudshell_api import CloudShellAPISession


def qs_log(severity, message, context=None):
    # with open(r'c:\ProgramData\QualiSystems\Shells.log', 'a') as f:
    #     f.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': ' + __file__.split('\\')[-1].replace('.pyc', '').replace('.py', '') +
    #             ': ' + message + '\r\n')

    # with open(r'c:\ProgramData\QualiSystems\LoggingDebug.log', 'a') as f:
    #     f.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': qs_log called')

    if context:
        try:
            resid = context.reservation.reservation_id
        except:
            try:
                resid = context.remote_reservation.reservation_id
            except:
                resid = 'no-reservation'

        # try:
        #     resource = context.remote_endpoints[0].fullname + '_via_' + context.resource.fullname
        # except:
        #     try:
        #         resource = context.resource.fullname
        #     except:
        #         resource = 'no-resource'
        # resource = resource.replace('/', '-').replace(':', '-')
        #
        try:
            csapi = CloudShellAPISession(context.connectivity.server_address,
                                                                       port=context.connectivity.cloudshell_api_port,
                                                                       token_id=context.connectivity.admin_auth_token)
        except:
            csapi = None

    else:
        csapi = helpers.get_api_session()
        try:
            resid = helpers.get_reservation_context_details().id
        except:
            resid = 'no-reservation'

        # try:
        #     resource = helpers.get_resource_context_details().fullname
        # except:
        #     resource = 'no-resource'
        # resource = resource.replace('/', '-').replace(':', '-')

    logger = get_qs_logger(log_group=resid, log_category='NFV', log_file_prefix='nfv')
    with open(r'c:\ProgramData\QualiSystems\LoggingDebug.log', 'a') as f:
        f.write(logger.name + ' ' + time.strftime('%Y-%m-%d %H:%M:%S') + ': ' + str(resid) + ' ' + str(message)[0:50] + '...\n')

    if severity in ['info']:
        logger.info(message)

    if severity in ['trace']:
        logger.debug(message)

    if severity in ['error']:
        logger.error(message)

    if severity in ['info', 'error']:
        if resid != 'no-reservation' and csapi:
            csapi.WriteMessageToReservationOutput(resid, message)


def qs_trace(message, context=None):
    qs_log('trace', message, context)


def qs_info(message, context=None):
    qs_log('info', message, context)


def qs_error(message, context=None):
    qs_log('error', message, context)


def myexcepthook(exctype, value, tb):
    x = []
    if issubclass(exctype, Exception):
        x.append("Exception type: " + str(exctype))
        x.append("Value called: " + str(value))
        x.append("Stacktrace: ")
        for trace in traceback.format_tb(tb):
            x.append(trace)
        qs_error('\r\n'.join(x))
    sys.__excepthook__(exctype, value, traceback)


sys.excepthook = myexcepthook

exclude_env_vars = {'TMP', 'COMPUTERNAME', 'USERDOMAIN', 'PSMODULEPATH', 'COMMONPROGRAMFILES', 'PROCESSOR_IDENTIFIER',
                    'PROGRAMFILES', 'PROCESSOR_REVISION', 'SYSTEMROOT', 'PATH', 'PROGRAMFILES(X86)', 'COMSPEC',
                    'STUDIOINSTALLDIR', 'TEMP', 'COMMONPROGRAMFILES(X86)', 'PROCESSOR_ARCHITECTURE', 'ALLUSERSPROFILE',
                    'LOCALAPPDATA', 'HOMEPATH', 'RESERVATIONCONTEXT', 'PROGRAMW6432', 'USERNAME', 'LOGONSERVER',
                    'PROMPT', 'SESSIONNAME', 'PROGRAMDATA', 'USERDOMAIN_ROAMINGPROFILE', 'PATHEXT', 'CLIENTNAME',
                    'FP_NO_HOST_CHECK', 'WINDIR', 'APPDATA', 'HOMEDRIVE', 'SYSTEMDRIVE', 'NUMBER_OF_PROCESSORS',
                    'PROCESSOR_LEVEL', 'PROCESSOR_ARCHITEW6432', 'COMMONPROGRAMW6432', 'OS', 'PUBLIC', 'USERPROFILE'}


def dictpp(o, tabs):
    if isinstance(o, str) or isinstance(o, unicode):
        if o and o[0] == '{':
            try:
                o = json.loads(o)
            except:
                pass
    if isinstance(o, dict):
        rv = '\n'
        for k in sorted(list(o.keys())):
            rv += tabs + '    ' + k + ' = ' + dictpp(o[k], tabs + '    ') + '\n'
        return rv
    else:
        return str(o)


def quali_enter(fn):
    global start_time
    start_time = time.time()
    env1 = os.environ
    env2 = {}
    for k in os.environ:
        if k not in exclude_env_vars:
            env2[k] = env1[k]

    qs_trace('**************************************************************************************')
    qs_trace('Function start')
    qs_trace(fn.split('\\')[-1].replace('.pyc', '').replace('.py', ''))
    qs_trace(dictpp(env2, '    '))
    qs_trace('**************************************************************************************')


def quali_exit(fn):
    global start_time
    qs_trace('**************************************************************************************')
    qs_trace('Function completed (' + str(time.time() - start_time))
    qs_trace(fn.split('\\')[-1].replace('.pyc', '').replace('.py', ''))
    qs_trace('**************************************************************************************')


def qualiroot():
    return r'c:\quali'


def pspath():
    return qualiroot() + '\\psexec.exe'


def exe(command_array):
    qs_trace('exe: ' + str(command_array))
    rv = subprocess.check_output(command_array, stderr=subprocess.STDOUT)
    if rv is not None:
        rv = rv.strip()

    qs_trace('exe result: ' + str(rv))
    return rv


def bat(script_text):
    qs_trace('bat: ' + str(script_text))

    f = tempfile.NamedTemporaryFile(suffix='.cmd', delete=False)
    f.write(script_text)
    f.close()
    rv = subprocess.check_output([r'c:\windows\system32\cmd.exe', '/c', f.name], stderr=subprocess.STDOUT).strip()
    if rv is not None:
        rv = rv.strip()

    qs_trace('bat result: ' + str(rv))
    return rv


def powershell(script_text):
    qs_trace(' powershell: ' + script_text)

    f = tempfile.NamedTemporaryFile(suffix='.ps1', delete=False)
    f.write(script_text)
    f.close()
    rv = subprocess.check_output(
        [r'c:\windows\syswow64\WindowsPowerShell\v1.0\powershell.exe', '-ExecutionPolicy', 'Bypass', '-File', f.name],
        stderr=subprocess.STDOUT)
    if rv is not None:
        rv = rv.strip()

    qs_trace('powershell result: ' + str(rv))
    return rv


def upload_file(remote_ip, remote_domain, remote_user, remote_password, remote_drive_letter, remote_path_under_drive,
                local_file_path):
    return powershell('''
        $qualidrive=[guid]::NewGuid().Guid
        $pw=(ConvertTo-SecureString -String "''' + remote_password + '''" -AsPlainText -Force)
        $credential=(New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList "''' + remote_domain + '''\\''' + remote_user + '''", $pw)
        New-PSDrive -name $qualidrive -PSProvider FileSystem -root \\\\''' + remote_ip + '''\\''' + remote_drive_letter + '''`$ -credential $credential
        copy "''' + local_file_path + '''" "${qualidrive}:\\''' + remote_path_under_drive + '''"
        Remove-PSDrive -name $qualidrive -Force
    ''')


def upload_data(remote_ip, remote_domain, remote_user, remote_password, remote_drive_letter, remote_path_under_drive,
                data):
    f = tempfile.NamedTemporaryFile(suffix='.txt', delete=False, )
    f.write(data.replace('\r\n', '\n').replace('\n', '\r\n'))
    f.close()
    qs_trace('upload data: ' + data)
    return upload_file(remote_ip, remote_domain, remote_user, remote_password, remote_drive_letter,
                       remote_path_under_drive, f.name)


def psexec(remote_ip, remote_domain, remote_user, remote_password, command_array, interactive=False):
    #     return powershell('''
    # $pw=(ConvertTo-SecureString -String "''' + remote_password + '''" -AsPlainText -Force)
    # $credential=(New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList "''' + remote_domain + '''\\''' + remote_user + '''", $pw)
    # Invoke-Command { & ''' + (' '.join(command_array)) + ''' } -ComputerName ''' + remote_ip + ''' -credential $credential
    # ''')

    ia = [
             pspath(),
             '\\\\' + remote_ip,
             '-u',
             remote_domain + '\\' + remote_user,
             '-p',
             remote_password,
             '-h'
         ] + (['-i', '0'] if interactive else []) + command_array

    qs_trace(': psexec: ' + ' '.join(ia))

    # stde = tempfile.NamedTemporaryFile(suffix='.txt', delete=False)
    # stdo = tempfile.NamedTemporaryFile(suffix='.txt', delete=False)
    # stdef = stde.name
    # stdof = stdo.name
    # p = subprocess.Popen(ia)
    # , stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    # o, e = p.communicate()
    # stde.close()
    # stdo.close()

    # rv = str(o) + '\r\n' + str(e) + '\r\n'
    # rv = powershell('& ' + (' '.join(ia)))

    # rv = '\r\n'.join(open(o)) + '\r\n\r\n' + '\r\n'.join(open(e))
    # h = open(stdef, 'r')
    # rv += '\r\n'.join(list(h.read() + '\r\n'
    # h.close()
    # h = open(stdof, 'r')
    # rv += h.read() + '\r\n'
    # h.close()
    #
    try:
        rv = subprocess.check_output(ia, stderr=subprocess.STDOUT)
        qs_trace(': bat result: ' + str(rv))
        return rv
    except Exception as e:
        qs_error('psexec failed: ' + str(e))
        raise e


def psexec_bat_no_upload(remote_ip, remote_domain, remote_user, remote_password, bat_array, interactive=False):
    return psexec(remote_ip, remote_domain, remote_user, remote_password, bat_array, interactive=interactive)


def psexec_bat(remote_ip, remote_domain, remote_user, remote_password, remote_drive_letter, bat_text,
               interactive=False):
    bat_name = str(uuid.uuid4()) + '.bat'
    upload_data(remote_ip, remote_domain, remote_user, remote_password, remote_drive_letter, bat_name, bat_text)
    return psexec(remote_ip, remote_domain, remote_user, remote_password, [
        'cmd', '/c', remote_drive_letter + ':\\' + bat_name], interactive=interactive)


def psexec_ps1(remote_ip, remote_domain, remote_user, remote_password, remote_drive_letter, ps1_text,
               interactive=False):
    ps1_name = str(uuid.uuid4()) + '.ps1'
    upload_data(remote_ip, remote_domain, remote_user, remote_password, remote_drive_letter, ps1_name, ps1_text)
    return psexec(remote_ip, remote_domain, remote_user, remote_password, [
        'powershell', '-ExecutionPolicy', 'Bypass', '-File', remote_drive_letter + ':\\' + ps1_name],
                  interactive=interactive)


def download_file(remote_ip, remote_domain, remote_user, remote_password, remote_drive_letter, http_user, http_password,
                  url, dest_file_path_in_drive):
    psexec_ps1(remote_ip, remote_domain, remote_user, remote_password, remote_drive_letter, '''
[System.Net.ServicePointManager]::ServerCertificateValidationCallback={`$true};
`$w=New-Object System.Net.WebClient;
`$w.Headers['Authorization']='Basic '+[System.Convert]::ToBase64String([System.Text.Encoding]::ASCII.GetBytes("''' + http_user + ''':''' + http_password + '''"));
`$w.DownloadFile("''' + url + '''", "''' + remote_drive_letter + ''':\\''' + dest_file_path_in_drive + '''")
''')


def ssh(host, user, password, command):
    qs_trace('ssh ' + host + ': ' + command)
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
    qs_trace('ssh result: ' + rv)
    return rv


def ssh_upload(host, username, password, local_file, dest_file):
    qs_trace('ssh upload ' + host + ': ' + local_file + ' -> ' + dest_file)
    s = paramiko.SSHClient()
    s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    s.connect(host, username=username, password=password)
    sftp = s.open_sftp()
    sftp.put(local_file, dest_file)
    s.close()


def ssh_download(host, username, password, source_file, local_file):
    s = paramiko.SSHClient()
    s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    s.connect(host, username=username, password=password)
    sftp = s.open_sftp()
    sftp.get(source_file, local_file)
    s.close()


def rest_api_query(url, user, password, method, body, is_body_json=False, return_xml=False, header=None):
    from requests.packages.urllib3.exceptions import InsecureRequestWarning
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    qs_trace(url + ': ' + body)
    h = {}
    if return_xml:
        h['Accept'] = 'application/xml'
    else:
        h['Accept'] = 'application/json'
    if is_body_json:
        h['Content-Type'] = 'application/json'
    else:
        h['Content-Type'] = 'application/xml'
    if header:
        for head in header:
            h[head] = header[head]
    if body:
        if not is_body_json and '<?xml' not in body:
            body = '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>\n' + body.strip()
        a = requests.request(method.upper(), url=url, auth=(user, password), verify=False, data=body, timeout=600,
                             headers=h)
    else:
        a = requests.request(method.upper(), url=url, auth=(user, password), verify=False, timeout=600, headers=h)
    qs_trace(str(a.status_code) + ' ' + a.text)
    if 200 <= a.status_code < 400:
        return a.text
    raise Exception('Error: ' + str(a.status_code) + ': ' + a.text)


def notify_user(api, reservationid, message):
    qs_trace(message)
    api.WriteMessageToReservationOutput(reservationid, message)


