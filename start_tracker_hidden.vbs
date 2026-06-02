Set shell = CreateObject("WScript.Shell")
root = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
cmd = "python """ & root & "\tracker_launcher.py"" start --port 8765"
shell.Run cmd, 0, False
WScript.Sleep 1200
shell.Run "http://127.0.0.1:8765/tracker", 1, False
