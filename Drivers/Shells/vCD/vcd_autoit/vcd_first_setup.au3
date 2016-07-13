; Auto-Fill ScaleIO Plugin Deployment Wizard
; Pre-Conditions for execution:
;	(1) English in language bar.
;	(2) Chrome browser in Full Screen mode.
#AutoIt3Wrapper_UseX64=Y

#include "plugin_functions_lib.au3"
#include <MsgBoxConstants.au3>

# 81486-5Z752-J8H7R-0X9R4-9MZ74 administrator dangerous MyName me@work.com vcd 10.10.111.34
AutoItSetOption('MouseCoordMode', 1)

$start_step = 1
$end_step = 6
Global $step_name = ""

; input file handling variables
Global $skip = False
#Global $window_name = "VMware vCloud Director - Mozilla Firefox"
Global $window_name = "VMware vCloud Director"

#Local $license_key = "81486-5Z752-J8H7R-0X9R4-9MZ74"
#Local $admin_username = ""
#Local $admin_password = ""
#Local $full_name = ""
#Local $email = ""
#Local $system_name = ""

$license_key = $CmdLine[1]
$admin_username = $CmdLine[2]
$admin_password = $CmdLine[3]
$full_name = $CmdLine[4]
$email = $CmdLine[5]
$system_name = $CmdLine[6]
$vcd_address = $CmdLine[7]


Func step1()
	$step_name = " Welcome"
	#click_next_button()
	Send("{TAB 2}")
	Send("{SPACE}")
EndFunc   ;==>step1

Func step2()
	$step_name = " Confirm License Agreement"
	wsleep(1000)
	click_image("agree_4.bmp")
	#click_next_button()
	Send("{TAB 5}")
	Send("{SPACE}")
EndFunc   ;==>step2

Func step3()
	$step_name = " Licensing"
	Send("{TAB 4}")
	Send($license_key,1)
    wsleep(2000)
	#click_next_button()
	Send("{TAB 6}")
	Send("{SPACE}")
EndFunc   ;==>step3

Func step4()
	$step_name = " Create Admin Account"
	Send("{TAB 5}")
	wSleep(500)
	Send($admin_username,1)
	Send("{TAB 1}")
	Send($admin_password,1)
	Send("{TAB 1}")
	Send($admin_password,1)
	Send("{TAB 1}")
	Send($full_name,1)
	Send("{TAB 1}")
	Send($email,1)
    Send("{TAB 2}")
	Send("{SPACE}")
	#click_next_button()
EndFunc   ;==>step4

Func step5()
	$step_name = " System Settings"
	Send("{TAB 6}")
	Send($system_name,1)
	wsleep(2000)
	Send("{TAB 3}")
	Send("{SPACE}")
	#click_next_button()
EndFunc   ;==>step5

Func step6()
	$step_name = " Ready to Complete"
	Send("{TAB 8}")
	Send("{SPACE}")
	#click_image("finishbtn.png")
    wSleep(30000)

EndFunc   ;==>step6


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
		Case 6
			step6()
		Case Else
			MsgBox(4, "unexpected step?", "wrong step encountered: " & $step_num & " Continue?")
	EndSwitch
	log_write("[fill_step] " & $step_name & " ==> completed" & @CRLF)
EndFunc   ;==>fill_step

Func wizard_autofill()

    get_window_by_title($window_name)

	For $cur_step = $start_step To $end_step Step 1
		ConsoleWrite('>' & '[wizard_autofill] current step is: ' & $cur_step & @CRLF)
		fill_step($cur_step)
	Next

EndFunc   ;==>wizard_autofill
#wsleep(10000)
ShellExecute("C:\Program Files\Mozilla Firefox\firefox.exe",  "https://" & $CmdLine[7] & "/cloud")
wsleep(10000)
wizard_autofill()
wsleep(50000)
WinClose($window_name)
