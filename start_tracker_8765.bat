@echo off
cd /d "%~dp0"
echo Quark tracker is starting...
echo.
echo Tracker page:
echo http://127.0.0.1:8765/tracker
echo.
echo Keep this window open while using the tracker.
echo Press Ctrl+C to stop the service.
echo.
python "%~dp0server.py" --port 8765
pause
