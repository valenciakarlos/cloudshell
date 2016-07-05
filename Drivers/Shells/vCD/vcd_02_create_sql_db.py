# service "vCloud Director"

import json
import os
import time
import subprocess
import sys

with open(r'c:\ProgramData\QualiSystems\Shells.log', 'a') as f:
    f.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': ' + __file__.split('\\')[-1].replace('.py', '') + ': ' + str(os.environ) + '\r\n')

resource = json.loads(os.environ['RESOURCECONTEXT'])
resource_name = resource['name']
attrs = resource['attributes']
db_folder = attrs['vCD DB Folder']

sqlscript = '''
USE [master]
GO
CREATE DATABASE [vcloud] ON PRIMARY
(NAME = N'vcloud', FILENAME = N'{folder}\\vcloud.mdf', SIZE = 100MB, FILEGROWTH = 10% )
LOG ON
(NAME = N'vcdb_log', FILENAME = N'{folder}\\vcloud.ldf', SIZE = 1MB, FILEGROWTH = 10%)
COLLATE Latin1_General_CS_AS
GO

USE [vcloud]
GO
ALTER DATABASE [vcloud] SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
ALTER DATABASE [vcloud] SET ALLOW_SNAPSHOT_ISOLATION ON;
ALTER DATABASE [vcloud] SET READ_COMMITTED_SNAPSHOT ON WITH NO_WAIT;
ALTER DATABASE [vcloud] SET MULTI_USER;
GO

USE [vcloud]
GO
CREATE LOGIN [vcloud] WITH PASSWORD = 'vcloudpass', DEFAULT_DATABASE =[vcloud], 
DEFAULT_LANGUAGE =[us_english], CHECK_POLICY=OFF
GO
CREATE USER [vcloud] for LOGIN [vcloud]
GO

USE [vcloud]
GO
sp_addrolemember [db_owner], [vcloud]
GO

'''.format(folder=db_folder)

# Add "NT AUTHORITY\NETWORK SERVICE" to Folder Permission. (Both c:\Deploy && db_folder)
def change_permission(folder):
    from quali_remote import powershell
    script = '''
    $folder = \'''' + folder + '''\'
    $perm = ((Get-Item $folder).GetAccessControl('Access')).Access
    $found = ''
    foreach($_ in $perm){
        if($_.IdentityReference -like '*network service*'){
            #$_
            $found = $_
            }
        }
    if (-Not $found){
        $Ar = New-Object System.Security.AccessControl.FileSystemAccessRule('NT AUTHORITY\NETWORK SERVICE', 'Fullcontrol', 'ContainerInherit,ObjectInherit', 'None', 'Allow')
        $rule = (Get-Item $folder).GetAccessControl('Access')
        $rule.SetAccessRule($Ar)
        Set-Acl -Path $folder -AclObject $rule
    }'''
    powershell(script)

change_permission(db_folder)
if not db_folder == r'c:\deploy':
    change_permission('c:\deploy')


#write sql file
try:
    with open(r'c:\deploy\vcd.sql', 'w') as f:
        f.write(sqlscript)
except Exception as e:
    print e
    with open(r'c:\ProgramData\QualiSystems\Shells.log', 'a') as f:
        f.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': vcd write to file error: ' + str(e) + '\r\n')
    sys.exit(1)


db_instance = ".\qualisystems2008"
dbexist = subprocess.check_output('sqlcmd -S ' + db_instance + ' -Q "select name from master.sys.databases where name=\"vcloud\""')

if "vcloud" in dbexist:
    print 'vcloud db already exists, for new deployments run the "drop db" first'
    sys.exit(1)
else:
    out = subprocess.check_output('sqlcmd -S ' + db_instance + ' -i c:\\deploy\\vcd.sql')
    if "does not exist" in out:
        with open(r'c:\ProgramData\QualiSystems\Shells.log', 'a') as f:
            f.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': ' + __file__.split('\\')[-1].replace('.py', '') + ': ' + out + '\r\n')
        print out
        sys.exit(1)
    else:
        print 'vcloud db created'


