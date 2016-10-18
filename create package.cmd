rem goto :skipdll
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

   
rem copy compiled drivers
copy "drivers\shells\onrack.compilation\onrack.dll" "nfvpackage\resource drivers\OnRack Driver.dll" /y
copy "Drivers\Orchestration\nfv environment driver.Compilation\nfv environment driver.dll" "nfvpackage\topology drivers\NFV Environment Driver.dll" /y

rem create vcd script
cd "drivers\shells\vcd\vcd_autoit"
"C:\Program Files (x86)\AutoIt3\Aut2Exe\Aut2exe_x64.exe" /in vcd_first_setup.au3 /out vcd_first_setup.exe /comp 4 /x64 /pack
"C:\Program Files (x86)\AutoIt3\Aut2Exe\Aut2exe_x64.exe" /in vcd_attach_vcenter.au3 /out vcd_attach_vcenter.exe /comp 4 /x64 /pack
:while3
    if exist "vcd_first_setup.exe" (
        if exist "vcd_attach_vcenter.exe" (
			timeout 3 >nul
		) else (
			timeout /t 3 /nobreak > NUL
			goto :while3
		)
    ) else (
        timeout /t 3 /nobreak > NUL
        goto :while3
    )

cd ..\..\..\..\
copy "drivers\shells\vcd\vcd_autoit\*.exe" "drivers\shells\vcd\vcd_setup_script"
rem copy "drivers\shells\vcd\vcd_autoit\*.bmp" "drivers\shells\vcd\vcd_setup_script"
rem copy "drivers\shells\vcd\vcd_autoit\*.dll" "drivers\shells\vcd\vcd_setup_script"
cd "drivers\shells\vcd\vcd_setup_script"
del ..\"vcd_05_setup.zip" /q
"c:\Program Files\7-Zip\7z.exe" a ..\"vcd_05_setup.zip" *
del *.exe /q
rem del *.bmp /q
rem del *.dll /q
cd ..\..\..\..\


:skipdll


rem create environment site-package deploy script
cd "drivers\site-packages"
"c:\Program Files\7-Zip\7z.exe" a "..\orchestration\copy prerequisites\sitepack.zip" *
cd ..\..\
cd "drivers\orchestration\copy prerequisites"
"c:\Program Files\7-Zip\7z.exe" a "..\..\..\nfvpackage\topology scripts\copy_prereq.zip" *
del *.zip
cd ..\..\..\

copy "drivers\orchestration\Common Scripts\steps.py" "drivers\orchestration\Generate Orchestration Steps File\"
cd "drivers\orchestration\Generate Orchestration Steps File\"
"c:\Program Files\7-Zip\7z.exe" a "..\..\..\nfvpackage\topology scripts\generate_orchestration_steps_file.zip" *
cd ..\..\..\

copy "drivers\orchestration\Common Scripts\steps.py" "drivers\orchestration\Run Orchestration Steps\"
cd "drivers\orchestration\Run Orchestration Steps\"
"c:\Program Files\7-Zip\7z.exe" a "..\..\..\nfvpackage\topology scripts\run_orchestration_steps.zip" *
cd ..\..\..\

rem rem copy "drivers\orchestration\NFV Environment Scripts\steps.py" "nfvpackage\topology scripts\" /y
rem rem copy "drivers\orchestration\NFV Environment Scripts\setup.py" "nfvpackage\topology scripts\" /y
rem copy "drivers\orchestration\NFV Environment Scripts\copy_inputs.py" "nfvpackage\topology scripts\" /y

rem goto :skipshells

rem rem copy "nfvpackage\Configuration\shellconfig-base.xml" "nfvpackage\Configuration\shellconfig.xml"
rem copy "nfvpackage\Datamodel\datamodel-base.xml"       "nfvpackage\Datamodel\datamodel.xml"
rem copy "shellconfig-base.xml" "nfvpackage\Configuration\shellconfig.xml"
rem rem copy "datamodel-base.xml"       "nfvpackage\Datamodel\datamodel.xml"

cd drivers\shells\OnRack-Shell
shellfoundry pack
cd dist
copy onrack-shell.zip ..\..\..\..\
rem "c:\Program Files\7-Zip\7z.exe" x -y onrack-shell.zip
rem copy "Resource Drivers - Python\OnrackShellDriver.zip"         "..\..\..\..\nfvpackage\Resource Drivers - Python\" /y
cd ..
cd ..\..\..\
rem python xmlmerge.py "nfvpackage\DataModel\datamodel.xml"        "drivers\shells\OnRack-Shell\dist\DataModel\datamodel.xml"
rem python xmlmerge.py "nfvpackage\Configuration\shellconfig.xml"  "drivers\shells\OnRack-Shell\dist\Configuration\shellconfig.xml"
rem rem copy "drivers\shells\OnRack-Shell\dist\DataModel\datamodel.xml" "nfvpackage\DataModel\datamodel-onrack.xml"
rem rem copy "drivers\shells\OnRack-Shell\dist\Configuration\shellconfig.xml" "nfvpackage\Configuration\shellconfig-onrack.xml"

cd drivers\shells\SiteManager-Shell
shellfoundry pack
cd dist
copy site_manager_shell.zip ..\..\..\..\
rem "c:\Program Files\7-Zip\7z.exe" x -y site_manager_shell.zip
rem copy "Resource Drivers - Python\SiteManagerShellDriver.zip"    "..\..\..\..\nfvpackage\Resource Drivers - Python\" /y
cd ..
cd ..\..\..\
rem python xmlmerge.py "nfvpackage\DataModel\datamodel.xml"        "drivers\shells\SiteManager-Shell\dist\DataModel\datamodel.xml"
rem python xmlmerge.py "nfvpackage\Configuration\shellconfig.xml"  "drivers\shells\SiteManager-Shell\dist\Configuration\shellconfig.xml"
rem rem copy "drivers\shells\SiteManager-Shell\dist\DataModel\datamodel.xml" "nfvpackage\DataModel\datamodel-sitemanager.xml"
rem rem copy "drivers\shells\SiteManager-Shell\dist\Configuration\shellconfig.xml" "nfvpackage\Configuration\shellconfig-sitemanager.xml"

cd drivers\shells\Compute-Shell
shellfoundry pack
cd dist
copy compute-shell ..\..\..\..\
rem "c:\Program Files\7-Zip\7z.exe" x -y compute-shell.zip
rem copy "Resource Drivers - Python\ComputeShellDriver.zip"         "..\..\..\..\nfvpackage\Resource Drivers - Python\" /y
cd ..
cd ..\..\..\
rem python xmlmerge.py "nfvpackage\DataModel\datamodel.xml"         "drivers\shells\Compute-Shell\dist\DataModel\datamodel.xml"
rem python xmlmerge.py "nfvpackage\Configuration\shellconfig.xml"   "drivers\shells\Compute-Shell\dist\Configuration\shellconfig.xml"
rem rem copy "drivers\shells\Compute-Shell\dist\DataModel\datamodel.xml" "nfvpackage\DataModel\datamodel-compute.xml"
rem rem copy "drivers\shells\Compute-Shell\dist\Configuration\shellconfig.xml" "nfvpackage\Configuration\shellconfig-compute.xml"


:skipshells

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
del ..\"NFV Build Environment.zip"
"c:\Program Files\7-Zip\7z.exe" a ..\"NFV Build Environment.zip" *
cd ..\


rem create site-package zip
rem cd drivers\site-packages
rem "c:\Program Files\7-Zip\7z.exe" a ..\..\"Python site packages.zip" *
rem cd ..\..\
