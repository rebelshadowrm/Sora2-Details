@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start-Sora2Details.ps1" -MeterOnly
exit /b %errorlevel%
