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


def myexcepthook(exctype, value, tb):
    x = []
    if issubclass(exctype, Exception):
        x.append("Exception type: " + str(exctype))
        x.append("Value called: " + str(value))
        x.append("Stacktrace: ")
        for trace in traceback.format_tb(tb):
            x.append(trace)
        h = open(r'c:\ProgramData\QualiSystems\Shells.log', 'a')
        h.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': ' + ('\r\n'.join(x)) + '\r\n')
        h.close()
    sys.__excepthook__(exctype, value, traceback)

sys.excepthook = myexcepthook


excudeenv = set(['TMP', 'COMPUTERNAME',
                    'USERDOMAIN', 'PSMODULEPATH',
                    'COMMONPROGRAMFILES', 'PROCESSOR_IDENTIFIER',
                    'PROGRAMFILES', 'PROCESSOR_REVISION',
                    'SYSTEMROOT', 'PATH',
                    'PROGRAMFILES(X86)', 'COMSPEC',
                    'STUDIOINSTALLDIR', 'TEMP',
                    'COMMONPROGRAMFILES(X86)', 'PROCESSOR_ARCHITECTURE',
                    'ALLUSERSPROFILE', 'LOCALAPPDATA',
                    'HOMEPATH', 'RESERVATIONCONTEXT',
                 'PROGRAMW6432', 'USERNAME',
                 'LOGONSERVER', 'PROMPT',
                    'SESSIONNAME', 'PROGRAMDATA',
                    'USERDOMAIN_ROAMINGPROFILE', 'PATHEXT',
                    'CLIENTNAME', 'FP_NO_HOST_CHECK',
                    'WINDIR', 'APPDATA',
                    'HOMEDRIVE', 'SYSTEMDRIVE',
                    'NUMBER_OF_PROCESSORS', 'PROCESSOR_LEVEL',
                    'PROCESSOR_ARCHITEW6432', 'COMMONPROGRAMW6432',
                    'OS', 'PUBLIC', 'USERPROFILE', ])


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
        if k not in excudeenv:
            env2[k] = env1[k]

    g = open(r'c:\ProgramData\QualiSystems\ehc.log', 'a')
    g.write('\n**************************************************************************************\n\n' +
            time.strftime('%Y-%m-%d %H:%M:%S') +
            ': Function start\n\n' + fn.split('\\')[-1].replace('.py', '') + '\n' +
            dictpp(env2, '    ') +
            '\n**************************************************************************************\n' +
            '\n')
    g.close()
    g = open(r'c:\ProgramData\QualiSystems\ehc_brief.log', 'a')
    g.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': Function start: ' + json.loads(os.environ['RESOURCECONTEXT'])['name'] +
            ' - ' + fn.split('\\')[-1].replace('.py', '') + '\n\n')
    g.close()


def quali_exit(fn):
    global start_time
    g = open(r'c:\ProgramData\QualiSystems\ehc.log', 'a')
    g.write('\n**************************************************************************************\n' +
            time.strftime('%Y-%m-%d %H:%M:%S') +
            ': Function ' + fn.split('\\')[-1].replace('.py', '') + ' completed (' + str(time.time() - start_time) + ')\n' +
            '**************************************************************************************\n')
    g.close()
    g = open(r'c:\ProgramData\QualiSystems\ehc_brief.log', 'a')
    g.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': Function end: ' + json.loads(os.environ['RESOURCECONTEXT'])['name'] +
            ' - ' + fn.split('\\')[-1].replace('.py', '') + ' (' + str(time.time() - start_time) + ')\n\n')
    g.close()

def qualiroot():
    return r'c:\quali'


def pspath():
    return qualiroot() + '\\psexec.exe'


def exe(command_array):
    g = open(r'c:\ProgramData\QualiSystems\Shells.log', 'a')
    g.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': exe: ' + str(command_array) + '\r\n')
    g.close()
    rv = subprocess.check_output(command_array, stderr=subprocess.STDOUT)
    if rv is not None:
        rv = rv.strip()

    g = open(r'c:\ProgramData\QualiSystems\Shells.log', 'a')
    g.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': exe result: ' + str(rv) + '\r\n')
    g.close()
    return rv


def bat(script_text):
    g = open(r'c:\ProgramData\QualiSystems\Shells.log', 'a')
    g.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': bat: ' + script_text + '\r\n')
    g.close()

    f = tempfile.NamedTemporaryFile(suffix='.cmd', delete=False)
    f.write(script_text)
    f.close()
    rv = subprocess.check_output([r'c:\windows\system32\cmd.exe', '/c', f.name], stderr=subprocess.STDOUT).strip()
    if rv is not None:
        rv = rv.strip()

    g = open(r'c:\ProgramData\QualiSystems\Shells.log', 'a')
    g.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': bat result: ' + str(rv) + '\r\n')
    g.close()
    return rv


def powershell(script_text):
    g = open(r'c:\ProgramData\QualiSystems\Shells.log', 'a')
    g.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': powershell: ' + script_text + '\r\n')
    g.close()

    f = tempfile.NamedTemporaryFile(suffix='.ps1', delete=False)
    f.write(script_text)
    f.close()
    rv = subprocess.check_output([r'c:\windows\syswow64\WindowsPowerShell\v1.0\powershell.exe', '-ExecutionPolicy', 'Bypass', '-File', f.name], stderr=subprocess.STDOUT)
    if rv is not None:
        rv = rv.strip()

    g = open(r'c:\ProgramData\QualiSystems\Shells.log', 'a')
    g.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': powershell result: ' + str(rv) + '\r\n')
    g.close()

    return rv


def upload_file(remote_ip, remote_domain, remote_user, remote_password, remote_drive_letter, remote_path_under_drive, local_file_path):
    return powershell('''
        $qualidrive=[guid]::NewGuid().Guid

        $pw=(ConvertTo-SecureString -String "''' + remote_password + '''" -AsPlainText -Force)

        $credential=(New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList "''' + remote_domain + '''\\''' + remote_user + '''", $pw)

        New-PSDrive -name $qualidrive -PSProvider FileSystem -root \\\\''' + remote_ip + '''\\''' + remote_drive_letter + '''`$ -credential $credential

        copy "''' + local_file_path + '''" "${qualidrive}:\\''' + remote_path_under_drive + '''"

        Remove-PSDrive -name $qualidrive -Force
    ''')


def upload_data(remote_ip, remote_domain, remote_user, remote_password, remote_drive_letter, remote_path_under_drive, data):
    f = tempfile.NamedTemporaryFile(suffix='.txt', delete=False, )
    f.write(data.replace('\r\n', '\n').replace('\n', '\r\n'))
    f.close()
    g = open(r'c:\ProgramData\QualiSystems\Shells.log', 'a')
    g.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': upload data: ' + data + '\r\n')
    g.close()
    return upload_file(remote_ip, remote_domain, remote_user, remote_password, remote_drive_letter, remote_path_under_drive, f.name)


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

    g = open(r'c:\ProgramData\QualiSystems\Shells.log', 'a')
    g.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': psexec: ' + ' '.join(ia) + '\r\n')
    g.close()

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
        g = open(r'c:\ProgramData\QualiSystems\Shells.log', 'a')
        g.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': bat result: ' + str(rv) + '\r\n')
        g.close()
        return rv
    except Exception as e:
        g = open(r'c:\ProgramData\QualiSystems\Shells.log', 'a')
        g.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': psexec failed: ' + str(e) + '\r\n')
        g.close()
        raise e


def psexec_bat_no_upload(remote_ip, remote_domain, remote_user, remote_password, bat_array, interactive=False):
    return psexec(remote_ip, remote_domain, remote_user, remote_password, bat_array, interactive=interactive)


def psexec_bat(remote_ip, remote_domain, remote_user, remote_password, remote_drive_letter, bat_text, interactive=False):
    bat_name = str(uuid.uuid4()) + '.bat'
    upload_data(remote_ip, remote_domain, remote_user, remote_password, remote_drive_letter, bat_name, bat_text)
    return psexec(remote_ip, remote_domain, remote_user, remote_password, [
        'cmd', '/c', remote_drive_letter + ':\\' + bat_name], interactive=interactive)


def psexec_ps1(remote_ip, remote_domain, remote_user, remote_password, remote_drive_letter, ps1_text, interactive=False):
    ps1_name = str(uuid.uuid4()) + '.ps1'
    upload_data(remote_ip, remote_domain, remote_user, remote_password, remote_drive_letter, ps1_name, ps1_text)
    return psexec(remote_ip, remote_domain, remote_user, remote_password, [
        'powershell', '-ExecutionPolicy', 'Bypass', '-File', remote_drive_letter + ':\\' + ps1_name], interactive=interactive)


def download_file(remote_ip, remote_domain, remote_user, remote_password, remote_drive_letter, http_user, http_password, url, dest_file_path_in_drive):
    psexec_ps1(remote_ip, remote_domain, remote_user, remote_password, remote_drive_letter, '''
[System.Net.ServicePointManager]::ServerCertificateValidationCallback={`$true};
`$w=New-Object System.Net.WebClient;
`$w.Headers['Authorization']='Basic '+[System.Convert]::ToBase64String([System.Text.Encoding]::ASCII.GetBytes("'''+http_user+''':'''+http_password+'''"));
`$w.DownloadFile("''' + url + '''", "'''+remote_drive_letter + ''':\\''' + dest_file_path_in_drive+'''")
''')


def ssh(host, user, password, command):
    g = open(r'c:\ProgramData\QualiSystems\Shells.log', 'a')
    g.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': ssh ' + host + ': ' + command + '\r\n')
    g.close()
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
    g = open(r'c:\ProgramData\QualiSystems\Shells.log', 'a')
    g.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': ssh result: ' + rv + '\r\n')
    g.close()
    return rv


def ssh_upload(host, username, password, local_file, dest_file):
    g = open(r'c:\ProgramData\QualiSystems\Shells.log', 'a')
    g.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': ssh upload ' + host + ': ' + local_file + ' -> ' + dest_file + '\r\n')
    g.close()
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





def rest_api_query(url, user, password, method, body, is_body_json=False, return_xml=False):
    from requests.packages.urllib3.exceptions import InsecureRequestWarning
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    with open(r'c:\ProgramData\QualiSystems\Shells.log', 'a') as f:
        f.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': ' + __file__.split('\\')[-1].replace('.py', '') +
                ': ' + url + ': ' + body + '\r\n')
    h = {}
    if return_xml:
        h['Accept'] = 'application/xml'
    else:
        h['Accept'] = 'application/json'
    if is_body_json:
        h['Content-Type'] = 'application/json'
    else:
        h['Content-Type'] = 'application/xml'
    if body:
        if not is_body_json and '<?xml' not in body:
            body = '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>\n' + body.strip()
        a = requests.request(method.upper(), url=url, auth=(user, password), verify=False, data=body, timeout=600, headers=h)
    else:
        a = requests.request(method.upper(), url=url, auth=(user, password), verify=False, timeout=600, headers=h)
    with open(r'c:\ProgramData\QualiSystems\Shells.log', 'a') as f:
        f.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': ' + __file__.split('\\')[-1].replace('.py', '') +
                ': ' + str(a.status_code) + ' ' + a.text + '\r\n')
    if 200 <= a.status_code < 400:
        return a.text
    raise Exception('Error: ' + str(a.status_code) + ': ' + a.text)



