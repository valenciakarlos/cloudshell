; Auto-Fill ScaleIO Plugin Deployment Wizard
; Pre-Conditions for execution:
;	(1) English in language bar.
;	(2) Firefox browser in Full Screen mode.
#AutoIt3Wrapper_UseX64=Y

#include "plugin_functions_lib.au3"
#include <MsgBoxConstants.au3>

$destination = @WorkingDir & "\attach.bmp"
FileInstall("attach.bmp", $destination)
$destination = @WorkingDir & "\url.bmp"
FileInstall("url.bmp", $destination)

AutoItSetOption('MouseCoordMode', 1)

;example: 10.10.111.232 administrator@vsphere.local Welcome1! vCenter6-nfv http://10.10.111.232/vsphere-client 10.10.111.33 admin Welcome1! 10.10.111.34 administrator dangerous

$start_step = 1
$end_step = 5
Global $step_name = ""
; input file handling variables
Global $skip = False
Global $window_name = "VMware vCloud Director"


$vchostname = $CmdLine[1]
$vc_username = $CmdLine[2]
$vc_password = $CmdLine[3]
$vc_name = $CmdLine[4]
$vc_webclient = $CmdLine[5]
$nsx_address = $CmdLine[6]
$nsx_username = $CmdLine[7]
$nsx_password = $CmdLine[8]
$vcd_address = $CmdLine[9]
$admin_username = $CmdLine[10]
$admin_password = $CmdLine[11]

Func step1()
	$step_name = " Login"
	Send($admin_username)
	Send("{TAB 1}")
	Send($admin_password)
	Send("{TAB 1}")
	Send("{SPACE}")
	wsleep(2000)
	Send("{SPACE}")
EndFunc   ;==>step1

Func step2()
	$step_name = " Attach vCenter"
	click_image("attach.bmp")

    wsleep(20000)
EndFunc   ;==>step2

Func step3()
	$step_name = " Name this vCenter"
    wSleep(5000)
	Send("{TAB 2}")
	Send($vchostname,1)
	Send("{TAB 2}")
	Send($vc_username,1)
	Send("{TAB 1}")
	Send($vc_password,1)
	Send("{TAB 1}")
	Send($vc_name,1)
	Send("{TAB 2}")
	Send($vc_webclient,1)
	click_image("url.bmp")
	wsleep(10000)
    Send("{TAB 1}")
	Send("{SPACE}")

EndFunc   ;==>step3

Func step4()
	$step_name = " Connect to vShield Manager"
	wSleep(10000)
	Send("{TAB 5}")
	Send($nsx_address,1)
	Send("{TAB 1}")
	Send($nsx_username,1)
	Send("{TAB 1}")
	Send($nsx_password,1)
    Send("{TAB 2}")
	Send("{SPACE}")
	wsleep(2000)

EndFunc   ;==>step4

Func step5()
	$step_name = " Ready to Complete"
	Send("{SPACE}")
    wSleep(10000)

EndFunc   ;==>step5


Func fill_step($step_num, $wait = 1000)
	wSleep($wait)
	Switch $step_num
		Case 1
			step1()
		Case 2
			step2()
		Case 3
			step3()
		Case 4
			step4()
		Case 5
			step5()

		Case Else
			MsgBox(4, "unexpected step?", "wrong step encountered: " & $step_num & " Continue?")
	EndSwitch
	log_write("[fill_step] " & $step_name & " ==> completed" & @CRLF)
EndFunc   ;==>fill_step

Func wizard_autofill()

    If get_window_by_title($window_name)=0 Then
		log_write("Firefox window '" & $window_name & "' not found" & @CRLF)
	Else
		For $cur_step = $start_step To $end_step Step 1
			log_write('>' & '[wizard_autofill] current step is: ' & $cur_step & @CRLF)
			fill_step($cur_step)
		Next
	EndIf

EndFunc   ;==>wizard_autofill

ShellExecute("taskkill.exe","/IM firefox.* /F")
wsleep(2000)
ShellExecute("C:\Program Files\Mozilla Firefox\firefox.exe",  "https://" & $CmdLine[9] & "/cloud")
wsleep(10000)
wizard_autofill()
wsleep(10000)
ShellExecute("taskkill.exe","/IM firefox.* /F")
