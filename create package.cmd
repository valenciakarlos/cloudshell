rem compile drivers
del "drivers\shells\onrack.compilation\onrack.dll"
"C:\Program Files (x86)\QualiSystems\CloudShell\Authoring\QsDriverStudio.exe" "drivers\shells\onrack\onrack.tsdrvproj" compile
:while1
    if exist "drivers\shells\onrack.compilation\onrack.dll" (
        timeout 7 >nul
    ) else (
        timeout /t 3 /nobreak > NUL
        goto :while1
    )
    
del "drivers\orchestration\nfv environment driver.compilation\nfv environment driver.dll" 
"C:\Program Files (x86)\QualiSystems\CloudShell\Authoring\QsDriverStudio.exe" "drivers\orchestration\nfv environment driver\nfv environment driver.tsdrvproj" compile
:while2
    if exist "drivers\orchestration\nfv environment driver.compilation\nfv environment driver.dll" (
        timeout 7 >nul
    ) else (
        timeout /t 3 /nobreak > NUL
        goto :while2
    )

del "drivers\shells\vcd\vcd_setup.compilation\vcd_setup.exe"
"C:\Program Files (x86)\QualiSystems\CloudShell\Authoring\QsDriverStudio.exe" "drivers\shells\vcd\vcd_setup\vcd_setup.tsdrvproj" compile
:while3
    if exist "drivers\shells\vcd\vcd_setup.compilation\vcd_setup.exe" (
        timeout 7 >nul
    ) else (
        timeout /t 3 /nobreak > NUL
        goto :while3
    )
    
rem copy compiled drivers
copy "drivers\shells\onrack.compilation\onrack.dll" "nfvpackage\resource drivers\OnRack Driver.dll" /y
copy "Drivers\Orchestration\nfv environment driver.Compilation\nfv environment driver.dll" "nfvpackage\topology drivers\NFV Environment Driver.dll" /y

rem create vcd script
copy drivers\shells\vcd\vcd_setup.compilation\vcd_setup.exe "drivers\shells\vcd\vcd_setup_script" /y
cd drivers\shells\vcd\vcd_setup_script
"c:\Program Files\7-Zip\7z.exe" a ..\"vcd_05_setup.zip" *
cd ..\..\..\..\


rem copy script files
copy drivers\shells\brocade\*.py "nfvpackage\resource scripts" /y
copy drivers\shells\nagios\*.py "nfvpackage\resource scripts" /y
copy drivers\shells\nsx\*.py "nfvpackage\resource scripts" /y
copy drivers\shells\scaleio\*.py "nfvpackage\resource scripts" /y
copy drivers\shells\vcd\*.py "nfvpackage\resource scripts" /y
copy drivers\shells\vcd\*.zip "nfvpackage\resource scripts" /y
copy drivers\shells\vcenter\*.py "nfvpackage\resource scripts" /y
copy drivers\shells\versa\*.py "nfvpackage\resource scripts" /y
copy drivers\shells\vcd\*.py "nfvpackage\resource scripts" /y
copy drivers\shells\vloginsight\*.py "nfvpackage\resource scripts" /y
copy drivers\shells\vrops\*.py "nfvpackage\resource scripts" /y


rem create package
cd nfvpackage
"c:\Program Files\7-Zip\7z.exe" a ..\"NFV Build Environment.zip" *
cd ..\


rem create site-package zip
cd drivers\site-packages
"c:\Program Files\7-Zip\7z.exe" a ..\..\"Python site packages.zip" *
cd ..\..\
