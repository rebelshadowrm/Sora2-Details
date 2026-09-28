@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Stop-Sora2Details.ps1" %*
if errorlevel 1 pause
