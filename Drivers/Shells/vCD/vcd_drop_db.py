# service "vCloud Director"

import os
import time
import subprocess
import sys

with open(r'c:\ProgramData\QualiSystems\Shells.log', 'a') as f:
    f.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': ' + __file__.split('\\')[-1].replace('.py', '') + ': ' + str(os.environ) + '\r\n')


sqlscript = '''
USE [master]
GO

IF  EXISTS (SELECT name FROM sys.databases WHERE name = N'vcloud')
DROP DATABASE [vcloud]
GO

'''

with open(r'c:\deploy\drop_sql_sb.sql', 'w') as file_:
    file_.write(sqlscript)

db_instance = ".\qualisystems2008"
out = subprocess.check_output('sqlcmd -S .\\qualisystems2008 -i c:\\deploy\\drop_sql_sb.sql', stderr=subprocess.STDOUT)
if 'Cannot drop database' in out:
    print out
    sys.exit(1)
else:
    print 'vcloud db dropped'



