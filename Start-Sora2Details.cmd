@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start-Sora2Details.ps1" %*
if errorlevel 1 pause
