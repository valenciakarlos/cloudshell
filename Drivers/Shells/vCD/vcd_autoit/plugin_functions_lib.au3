#include <MsgBoxConstants.au3>
#include <GUIConstants.au3>
#include <Array.au3>
#include <File.au3>
#include <String.au3>
#include <FileConstants.au3>
#include <ImageSearch64.au3>

; General Settings
HotKeySet("{F10}", "Quit")
AutoItSetOption('MouseCoordMode', 0)
AutoItSetOption("TrayIconDebug", 1);0-off
$SLEEP_TIME = 500
Global $WIN_WAIT_TIME = 6

; Logging
$log_file = "c:\autoit.log"
$hFile = FileOpen($log_file, 2)

; Input File handling Variables
Global $CSVFILE = "";"C:\temp\mgmt_ips_conf_10.76.61.14-16.csv";"C:\temp\test2.csv";
Global $skip = False ;skip first line in file?
Global $file_parsing_error = "csv file parsing error in: " & $CSVFILE
Global $Dchar = "," ;delimiter of csv file
;Global $csv_arr = _ParseCSV($CSVFILE,$Dchar,$file_parsing_error,$skip)

Func finish($msg = "Finish tasks on program completion..")
   log_write("[Finish] " & $msg,True)
   ;ConsoleWrite($msg)
   FileClose($hFile) ; Close the filehandle to release the file.
   Exit
EndFunc   ;==>Quit

Func Quit()
   finish('>' & "[Quit] Quiting by user requet.." & @CRLF)
	;ConsoleWrite('>' & "[Quit] Quiting by user requet.." & @CRLF)
	;FileClose($hFile) ; Close the filehandle to release the file.
	;Exit
 EndFunc   ;==>Quit

Func cleanup_pressed_keys()
	Sleep(10)
	Send("{CTRLDOWN}")
	Sleep(10)
	Send("{CTRLUP}")

	Sleep(10)
	Send("{SHIFTDOWN}")
	Sleep(10)
	Send("{SHIFTUP}")

	Sleep(10)
	;Send("{ALTDOWN}")
	Sleep(10)
	;Send("{ALTUP}")
	Sleep(10)
	;Send("{LWINDOWN}")
	Sleep(10)
	Send("{LWINUP}")
	;Sleep(10)
	;Send("{ALTUP}")
EndFunc

Func wait_for_pixel_color($x, $y, $color, $timeout = 3000)
	; Example Call: $isColor = wait_for_pixel_color(472, 492, 16777214)
	$check_interval = 500
	$elapsed_time = 0
	$is_identical_color = False
	MouseClick("primary", $x, $y, 1)
	ConsoleWrite('>' & "[wait_for_pixel_color] " & " x: " & $x & " y: " & $y & " $color: " & $color & " $timeout: " & $timeout & @CRLF)
	While $elapsed_time < $timeout
		$iColor = PixelGetColor($x, $y)
		ConsoleWrite('>' & "[wait_for_pixel_color] " & " sampled color is: " & $iColor & " required color is: " & $color & @CRLF)
		If $iColor = $color Then
			$is_identical_color = True
			ExitLoop
		EndIf
		Sleep($check_interval)
		$elapsed_time += $check_interval
	WEnd
	Return $is_identical_color
EndFunc   ;==>wait_for_pixel_color

Func search_color_in_range($x_start, $x_end, $y, $color, $interval = 2)
	; Example Call: $isColor = search_color_in_range(472, 500, 490, 16777215)
	ConsoleWrite('>' & "[search_color_in_range] " & " $x_start: " & $x_start & " $x_end: " & $x_end & " $y: " & $y & " search color: " & $color & @CRLF)
	$isFound = False
	MouseMove($x_start, $y, 0);MouseClick("primary", $x_start, $y, 1)
	$cur_x = $x_start
	While $cur_x <= $x_end
		MouseMove($cur_x, $y, 0);MouseClick("primary", $cur_x, $y, 1)
		$iColor = PixelGetColor($cur_x, $y)
		ConsoleWrite('>' & "[search_color_in_range] " & " $cur_x: " & $cur_x & " sampled color: " & $iColor & @CRLF)
		If $iColor = $color Then
			$isFound = True
			ExitLoop
		EndIf
		$cur_x += $interval
	WEnd
	Return $isFound
EndFunc   ;==>search_color_in_range

; TBD Func ConsoleWrite_concat_with_spaces($list)

Func serial_mouse_click($x, $y, $delta, $times)
	ConsoleWrite('>' & '[serial_mouse_click] ' & " x: " & $x & " y: " & $y & " delta: " & $delta & " times: " & $times & @CRLF)
	$i = 1
	While $i <= $times
		MouseClick("primary", $x, $y, 1)
		Sleep(500)
		;Local $iColor = PixelGetColor($x, $y)
		ConsoleWrite('>' & '[serial_mouse_click] [ ' & $x & ',' & $y & ']' & @CRLF)
		;dbg_check_proceed()
		;if $iColor <> $grayed_out_color Then
		;	$i = $i + 1
		;	ContinueLoop
		;EndIf
		$i = $i + 1
		$y = $y + $delta
	WEnd
EndFunc   ;==>serial_mouse_click

Func serial_click_and_send($x, $y, $delta, $times, $array, $col_num)
	log_write('>' & '[serial_click_and_send] ' & " x: " & $x & " y: " & $y & " delta: " & $delta & " times: " & $times & @CRLF)
	$i = 2
	$times = $times + $i - 1
	While $i <= $times
		MouseClick("primary", $x, $y, 1)
		$cur_val = $array[$i][$col_num]
		send_with_sleep("^a" & $cur_val, 50)
		log_write('>' & '[serial_click_and_send] [ ' & $x & ',' & $y & '] array[' & $i & '][' & $col_num & '] ==>' & $cur_val & @CRLF)
		$i = $i + 1
		$y = $y + $delta
	WEnd
EndFunc   ;==>serial_click_and_send


Func dbg_check_proceed()
	; ******* DEBUGGING proceed or abort Condition **************
	Sleep(4000)
	$verify = MsgBox(4, "Proceed?", "Yes or No?")
	If $verify = $IDNO Then
		Exit
	EndIf
EndFunc   ;==>dbg_check_proceed

Func click_button($x, $y)
	log_write("[click_button] (" & $x & "," & $y & ")" & @CRLF)
	$aPos = calc_absolute_position($x, $y)
	;log_write("[click_button] click_button($aPos[0], $aPos[1])" & @CRLF)
	log_write("[click_button] ==> (" & $aPos[0] & "," & $aPos[1] & ")" & @CRLF)
	;MouseMove( $aPos[0], $aPos[1])
	MouseClick("primary", $aPos[0], $aPos[1], 1)
EndFunc   ;==>click_button

Func click_next_button()
   log_write("[click_next_button] click_next_button()" & @CRLF)

   if click_image("nextbtn.png")=0 Then
	  click_image("nextbtn.bmp")
   EndIf

EndFunc   ;==>click_next_button

Func click_image($image)
   $x1 = 0
   $y1 = 0
   wSleep()
   $image_retries = 10
   $retry_delay = 2000
   $found = "0"
   For $i = $image_retries To 0 Step -1
	  $result = _ImageSearch($image,1,$x1,$y1,50)
	  If $result=1 Then
		 MouseClick("primary",$x1,$y1+2,1)
		 $found = "1"
		 Return 1
	  Else
		 wsleep($retry_delay)
	  EndIf
   Next
   if $found = "0" Then
	  log_write("[click_image] image '" & $image & "' not found")
	  return 0
   EndIf
EndFunc

Func point_image($image)
   $x1 = 0
   $y1 = 0
   wSleep()
   $result = _ImageSearch($image,1,$x1,$y1,50)
   If $result=1 Then
	  MouseClick("right",$x1,$y1+2,1)
	  Return 1
   Else
	  log_write("[click_image] image '" & $image & "' not found")
	  Return 0
   EndIf
EndFunc

Func log_write($msg,$withDate=False)
   ConsoleWrite('>' & $msg & @CRLF)
   If $withDate = True Then
	  _FileWriteLog($hFile, @CRLF & $msg)
   Else
	  FileWriteLine($hFile, @CRLF & $msg)
   EndIf
EndFunc   ;==>log_write

Func send_with_sleep($input, $time = $SLEEP_TIME) ; Send input after sleep
	wSleep($time)
	log_write("[send_with_sleep] " & $input)
	Send($input)
	cleanup_pressed_keys()
EndFunc   ;==>send_with_sleep

Func send_now($input="") ; Send input with no sleep
	log_write("[send_now] " & $input)
	Send($input)
EndFunc   ;==>send_with_sleep

Func wSleep($time = 500) ; sleep wraping
	ConsoleWrite('>' & '[wSleep] sleeping for: ' & $time & '...' & @CRLF)
	Sleep($time)
EndFunc   ;==>wSleep


; _ParseCSV Usage:
;$CSVFILE = "C:\temp\test2.csv"
;$skip = False
;$error = "parsing error!"
;$Dchar = ","
;$myArr = _ParseCSV($CSVFILE,$Dchar,$error,$skip)

Func _ParseCSV($f, $Dchar, $error, $skip)
	log_write("[_ParseCSV] input params: " & " file: " & $f & " delimeter: " & $Dchar & " msg: " & $error & " skip: " & $skip)

	Local $array[500][500]
	Local $line = ""

	$i = 0
	$file = FileOpen($f, 0)
	If $file = -1 Then
		MsgBox(0, "Error", $error)
		Return False
	EndIf

	;skip 1st line
	If $skip Then $line = FileReadLine($file)

	While 1
		$i = $i + 1
		Local $line = FileReadLine($file)
		If @error = -1 Then ExitLoop
		$row_array = StringSplit($line, $Dchar)
		If $i == 1 Then $row_size = UBound($row_array)
		If $row_size <> UBound($row_array) Then MsgBox(0, "Error", "Row: " & $i & " has different size ")
		$row_size = UBound($row_array)
		$array = _arrayAdd_2d($array, $i, $row_array, $row_size)

	WEnd
	FileClose($file)
	$array[0][0] = $i - 1 ;stores number of lines
	$array[0][1] = $row_size - 1 ; stores number of data in a row (data corresponding to index 0 is the number of data in a row actually that's way the -1)
	Return $array

EndFunc   ;==>_ParseCSV


Func _arrayAdd_2d($array, $inwhich, $row_array, $row_size)
	For $i = 1 To $row_size - 1 Step 1
		$array[$inwhich][$i] = $row_array[$i]
	Next
	Return $array
EndFunc   ;==>_arrayAdd_2d

Func get_window_by_title($title)
	log_write("[get_window_by_title] Activating Window with Title: " & $title)
	WinWait($title, "", $WIN_WAIT_TIME)
	WinActivate($title)
	Local $hWnd = WinWaitActive($title, "", $WIN_WAIT_TIME)
	Local $sText = ""
	$active_title = WinGetTitle("[ACTIVE]")
	log_write("[get_window_by_title] Active Window's Title is: " & $active_title)
	Local $iPosition = StringInStr($active_title, $title)
	Return $iPosition
EndFunc   ;==>get_window_by_title

Func prompt($msg)
	log_write("[prompt] " & $msg)
	MsgBox(0, "Watch Out", $msg);, timeout = 25)
EndFunc   ;==>prompt

Func calc_window_position($winTitle)
	; Retrieve the position as well as height and width of the active window.
	Local $winPos = WinGetPos($winTitle)
	; Display the array values returned by WinGetPos.
	log_write("[calc_window_position] width: " & $winPos[2] & " Hight: " & $winPos[3])
	Return $winPos ; retrun array with window values.
EndFunc   ;==>calc_window_position

Func calc_absolute_position($x, $y, $winTitle = "[ACTIVE]") ; ( 52%,64% )
	Local $aPos[2];
	Local $winPos = calc_window_position($winTitle)
	$width = $winPos[2]
	$height = $winPos[3]
	$aPos[0] = $width * $x / 100 ; abs x
	$aPos[1] = $height * $y / 100 ; abs y
	; Retrieve the position as well as height and width of the active window.
	Local $winPos = WinGetPos($winTitle)
	; Display the array values returned by WinGetPos.
	log_write("[calc_absolute_position] abs width: " & $aPos[0] & " abs Hight: " & $aPos[1])
	Return $aPos ; retrun array with absolute values coordinates of x & y.
EndFunc   ;==>calc_absolute_position

Func get_abs_x_coord($x_percent, $winTitle = "[ACTIVE]")
	Local $winPos = calc_window_position($winTitle)
	Local $abs_x = $winPos[2] * $x_percent / 100
	log_write("[get_abs_x_coord] abs x coord: " & $abs_x)
	Return $abs_x
EndFunc