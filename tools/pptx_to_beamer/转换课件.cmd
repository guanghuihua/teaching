@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0convert.ps1" %*
if errorlevel 1 echo Conversion failed. See the message above.
pause
