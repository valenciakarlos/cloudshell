"c:\Program Files\7-Zip\7z.exe" x -y -o"c:\program files (x86)\qualisystems\testshell\executionserver\python\2.7.10\lib\site-packages" "Python site packages.zip"

@echo off

if defined QSPASSWORD goto skippass

powershell -Command $pword = read-host "Enter CloudShell admin password to import packages" -AsSecureString ; $BSTR=[System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($pword) ; [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR) > .tmp.txt & set /p QSPASSWORD=<.tmp.txt & del .tmp.txt

:skippass


"c:\program files (x86)\qualisystems\testshell\executionserver\python\2.7.10\python.exe" worker.py

@echo Installation complete
@pause

