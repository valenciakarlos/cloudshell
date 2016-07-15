#include-once
; ------------------------------------------------------------------------------
;
; AutoIt Version: 3.0
; Language:       English
; Description:    Functions that assist with Image Search
;                 Require that the ImageSearchDLL.dll be loadable
;
; ------------------------------------------------------------------------------

$destination = @WorkingDir & "\ImageSearchDLL_x64.dll"
FileInstall("ImageSearchDLL_x64.dll", $destination)
$destination = @WorkingDir & "\msvcr110d.dll"
FileInstall("msvcr110d.dll", $destination)


;===============================================================================
;
; Description:      Find the position of an image on the desktop
; Syntax:           _ImageSearchArea, _ImageSearch
; Parameter(s):
;                   $findImage - the image to locate on the desktop
;                   $tolerance - 0 for no tolerance (0-255). Needed when colors of
;                                image differ from desktop. e.g GIF
;                   $resultPosition - Set where the returned x,y location of the image is.
;                                     1 for centre of image, 0 for top left of image
;                   $x $y - Return the x and y location of the image
;
; Return Value(s):  On Success - Returns 1
;                   On Failure - Returns 0
;
; Note: Use _ImageSearch to search the entire desktop, _ImageSearchArea to specify
;       a desktop region to search
;
;===============================================================================
Func _ImageSearch($findImage,$resultPosition, ByRef $x, ByRef $y,$tolerance)
   return _ImageSearchArea($findImage,$resultPosition,0,0,@DesktopWidth,@DesktopHeight,$x,$y,$tolerance)
EndFunc

Func _ImageSearchArea($findImage,$resultPosition,$x1,$y1,$right,$bottom, ByRef $x, ByRef $y, $tolerance)
	If $tolerance>0 Then $findImage = "*" & $tolerance & " " & $findImage

	If @AutoItX64 Then
		 $result = DllCall("ImageSearchDLL_x64.dll","str","ImageSearch","int",$x1,"int",$y1,"int",$right,"int",$bottom,"str",$findImage)
	  Else
		 $result = DllCall("ImageSearchDLL.dll","str","ImageSearch","int",$x1,"int",$y1,"int",$right,"int",$bottom,"str",$findImage)
   EndIf

    If $result = "0" Then Return 0

   $array = StringSplit($result[0],"|")
   If(UBound($array) >= 4) Then
	  $x=Int(Number($array[2]))
	  $y=Int(Number($array[3]))
	  If $resultPosition=1 Then
		 $x=$x + Int(Number($array[4])/2)
		 $y=$y + Int(Number($array[5])/2)
	  Endif
	  Return 1
   EndIf
EndFunc

;===============================================================================
;
; Description:      Wait for a specified number of seconds for an image to appear
;
; Syntax:           _WaitForImageSearch, _WaitForImagesSearch
; Parameter(s):
;					$waitSecs  - seconds to try and find the image
;                   $findImage - the image to locate on the desktop
;                   $tolerance - 0 for no tolerance (0-255). Needed when colors of
;                                image differ from desktop. e.g GIF
;                   $resultPosition - Set where the returned x,y location of the image is.
;                                     1 for centre of image, 0 for top left of image
;                   $x $y - Return the x and y location of the image
;
; Return Value(s):  On Success - Returns 1
;                   On Failure - Returns 0
;
;
;===============================================================================
Func _WaitForImageSearch($findImage,$waitSecs,$resultPosition, ByRef $x, ByRef $y,$tolerance)
	$waitSecs = $waitSecs * 1000
	$startTime=TimerInit()
	While TimerDiff($startTime) < $waitSecs
		sleep(100)
		$result=_ImageSearch($findImage,$resultPosition,$x, $y,$tolerance)
		if $result > 0 Then
			return 1
		EndIf
	WEnd
	return 0
EndFunc

;===============================================================================
;
; Description:      Wait for a specified number of seconds for any of a set of
;                   images to appear
;
; Syntax:           _WaitForImagesSearch
; Parameter(s):
;					$waitSecs  - seconds to try and find the image
;                   $findImage - the ARRAY of images to locate on the desktop
;                              - ARRAY[0] is set to the number of images to loop through
;								 ARRAY[1] is the first image
;                   $tolerance - 0 for no tolerance (0-255). Needed when colors of
;                                image differ from desktop. e.g GIF
;                   $resultPosition - Set where the returned x,y location of the image is.
;                                     1 for centre of image, 0 for top left of image
;                   $x $y - Return the x and y location of the image
;
; Return Value(s):  On Success - Returns the index of the successful find
;                   On Failure - Returns 0
;
;
;===============================================================================
Func _WaitForImagesSearch($findImage,$waitSecs,$resultPosition, ByRef $x, ByRef $y,$tolerance)
	$waitSecs = $waitSecs * 1000
	$startTime=TimerInit()
	While TimerDiff($startTime) < $waitSecs
		for $i = 1 to $findImage[0]
		    sleep(100)
		    $result=_ImageSearch($findImage[$i],$resultPosition,$x, $y,$tolerance)
		    if $result > 0 Then
			    return $i
		    EndIf
		Next
	WEnd
	return 0
EndFunc
