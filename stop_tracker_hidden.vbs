Set shell = CreateObject("WScript.Shell")
root = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
cmd = "python """ & root & "\tracker_launcher.py"" stop --port 8765"
shell.Run cmd, 0, True
