Option Explicit

Dim shell, fso, root, python, server, command, url, ready, i, request

Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

root = fso.GetParentFolderName(WScript.ScriptFullName)
python = shell.ExpandEnvironmentStrings("%USERPROFILE%") & "\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
server = root & "\server.py"
url = "http://127.0.0.1:8765/"

If Not fso.FileExists(python) Then
  MsgBox "Python runtime was not found: " & python, vbCritical, "Quark Transfer"
  WScript.Quit 1
End If

If Not fso.FileExists(server) Then
  MsgBox "server.py was not found: " & server, vbCritical, "Quark Transfer"
  WScript.Quit 1
End If

command = """" & python & """ """ & server & """ --host 127.0.0.1 --port 8765"
shell.Run command, 0, False

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

shell.Run url, 1, False
