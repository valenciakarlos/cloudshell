rem copy compiled drivers
copy drivers\shells\onrack.compilation\onrack.dll "nfvpackage\resource drivers\OnRack Driver.dll"
copy drivers\orchestration\nfv environment driver.compilation\onrack.dll "nfvpackage\topology drivers\NFV Environment Driver.dll"

rem create vcd script
copy drivers\shells\vcd\vcd_setup.compilation\vcd_setup.exe "drivers\shells\vcd\vcd_setup_script"
cd drivers\shells\vcd\vcd_setup_script
"c:\Program Files\7-Zip\7z.exe" a ..\"vcd_05_setup.zip" *
cd ..\..\..\..\


rem copy script files
copy drivers\shells\brocade\*.py "nfvpackage\resource scripts"
copy drivers\shells\nagios\*.py "nfvpackage\resource scripts"
copy drivers\shells\nsx\*.py "nfvpackage\resource scripts"
copy drivers\shells\scaleio\*.py "nfvpackage\resource scripts"
copy drivers\shells\vcd\*.py "nfvpackage\resource scripts"
copy drivers\shells\vcd\*.zip "nfvpackage\resource scripts"
copy drivers\shells\vcenter\*.py "nfvpackage\resource scripts"
copy drivers\shells\versa\*.py "nfvpackage\resource scripts"
copy drivers\shells\vcd\*.py "nfvpackage\resource scripts"
copy drivers\shells\vloginsight\*.py "nfvpackage\resource scripts"
copy drivers\shells\vrops\*.py "nfvpackage\resource scripts"


rem create package
cd nfvpackage
"c:\Program Files\7-Zip\7z.exe" a ..\"NFV Build Environment.zip" *
cd ..\


rem create site-package zip
cd drivers\site-packages
"c:\Program Files\7-Zip\7z.exe" a ..\..\"site-packages.zip" *
cd ..\..\
