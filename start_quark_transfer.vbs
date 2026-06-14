Option Explicit

Dim shell, command, url, ready, i, request, exitCode

Set shell = CreateObject("WScript.Shell")

url = "http://127.0.0.1:8765/"
command = "schtasks.exe /Run /TN QuarkTransferAlwaysOn"
exitCode = shell.Run(command, 0, True)

If exitCode <> 0 Then
  command = "wsl.exe -d Ubuntu-24.04 -- bash /home/xuelong/projects/Tools/QuarkTransfer/run_home_service_forever.sh"
  shell.Run command, 0, False
  exitCode = 0
End If

If exitCode <> 0 Then
  MsgBox "Home directory QuarkTransfer failed to start." & vbCrLf & _
    "Check /home/xuelong/projects/Tools/QuarkTransfer/config/tracker.log", _
    vbCritical, "Quark Transfer"
  WScript.Quit exitCode
End If

ready = False
For i = 1 To 30
  On Error Resume Next
  Set request = CreateObject("MSXML2.XMLHTTP")
  request.Open "GET", url & "api/config", False
  request.Send
  If Err.Number = 0 Then
    If request.Status = 200 Then ready = True
  End If
  Err.Clear
  On Error GoTo 0
  If ready Then Exit For
  WScript.Sleep 300
Next

If Not ready Then
  MsgBox "QuarkTransfer did not respond on port 8765.", vbCritical, "Quark Transfer"
  WScript.Quit 1
End If

shell.Run url, 1, False
