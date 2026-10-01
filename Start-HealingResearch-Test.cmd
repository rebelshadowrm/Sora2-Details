@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start-Sora2Details.ps1" -CaptureProfile HealingResearch
if errorlevel 1 (
    echo.
    pause
    exit /b 1
)
exit /b 0
