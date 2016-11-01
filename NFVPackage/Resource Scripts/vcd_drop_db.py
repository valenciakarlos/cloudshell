# service "vCloud Director"

import os
import time
import subprocess
import sys

from quali_remote import quali_enter, quali_exit, qs_trace, qs_info

quali_enter(__file__)


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
    raise Exception('Could not drop vCD database: ' + out)

qs_info('vcloud db dropped')

quali_exit(__file__)
