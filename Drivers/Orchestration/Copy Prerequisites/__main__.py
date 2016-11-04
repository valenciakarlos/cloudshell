import os
import subprocess
import time
import zipfile


tempdir = os.path.normpath(os.path.dirname(__file__) + '\\..\\temp')
os.makedirs(tempdir)

with zipfile.ZipFile(os.path.dirname(__file__), "r") as z:
    z.extractall(tempdir)

#extract the inner zip to site-packages
with zipfile.ZipFile((tempdir + "\\sitepack.zip"), "r") as z:
    z.extractall("C:\\Program Files (x86)\\QualiSystems\\TestShell\\ExecutionServer\\python\\2.7.10\\Lib\\site-packages\\")

print os.path.normpath(tempdir + "\\sitepack.zip") + " unzipped"
