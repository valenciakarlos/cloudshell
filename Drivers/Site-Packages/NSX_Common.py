
from quali_remote import *


def nsx_wait(nsx_ip, user, password):
    while True:
        r = requests.get('''https://''' + nsx_ip + '''/api/2.0/vdn/controller''', auth=(user, password), verify=False, headers={'accept': 'application/json'})
        if r.status_code == 200:
            return
        time.sleep(20)


def nsx_get_job_status(nsx_ip, nsx_user, nsx_password, job_moref):
    x = rest_api_query('https://' + nsx_ip + '/api/2.0/services/taskservice/job/' + job_moref, nsx_user, nsx_password, 'get', '')
    f = open(r'c:\ProgramData\QualiSystems\Shells.log', 'a')
    f.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': ' + __file__.split('\\')[-1].replace('.py', '') + ': Job status ' + job_moref + ': ' + x + '\n')
    f.close()
    return x


def nsx_wait_job(nsx_ip, nsx_user, nsx_password, job_moref):
    while True:
        s = nsx_get_job_status(nsx_ip, nsx_user, nsx_password, job_moref)
        so = json.loads(s)
        so = so['jobInstances'][0]
        if so['status'] == 'COMPLETED':
            return
        if so['status'] == 'FAILED':
            ee = ''
            for ti in so['taskInstances']:
                ee += ti['name'] + ': ' + ti['status'] + ': ' + ti['statusMessage'] + '; '
            raise 'Task failure: ' + ee
        print 'Status ' + so['status'] + ', sleeping 5 seconds...'
        time.sleep(5)


def rest_api_query_with_retry(url, user, password, method, body, is_body_json=False):
    from requests.packages.urllib3.exceptions import InsecureRequestWarning
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    s = ''
    a = '832837'
    h = {'accept': 'application/json'}
    if is_body_json:
        h['Content-Type'] = 'application/json'
    else:
        h['Content-Type'] = 'application/xml'
    if not is_body_json and '<?xml' not in body:
        body = '''<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
''' + body.strip()
    for _ in [1, 2]:
        d = body.format(s)
        f = open(r'c:\ProgramData\QualiSystems\Shells.log', 'a')
        f.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': ' + __file__.split('\\')[-1].replace('.py', '') + ': ' + url + ': ' + str(h) + ': ' + d + '\n')
        a = requests.request(method.upper(), url=url, auth=(user, password), verify=False, data=d, timeout=600, headers=h)
        f = open(r'c:\ProgramData\QualiSystems\Shells.log', 'a')
        f.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': ' + __file__.split('\\')[-1].replace('.py', '') + ': ' + str(a.status_code) + ' ' + a.text + '\n')
        f.close()
        if 200 <= a.status_code < 400:
            return a.text
        s = '<certificateThumbprint>' + json.loads(a.text)['details'] + '</certificateThumbprint>'
    raise Exception('Error: ' + str(a.status_code) + ': ' + a.text)
