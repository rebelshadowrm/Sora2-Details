param(
    [int]$Hours = 12,
    [ValidateSet('Live', 'HealingResearch')][string]$CaptureProfile = 'Live',
    [string]$PythonPath = 'C:\Python313\python.exe',
    [string]$GameDirectory = 'C:\Games\Trails in the Sky 2nd Chapter'
)

$ErrorActionPreference = 'Stop'
if ($Hours -lt 2 -or $Hours -gt 12) { throw 'Hours must be 2..12.' }
if ($CaptureProfile -eq 'HealingResearch') {
    & (Join-Path $PSScriptRoot 'start_live_meter.ps1') -Seconds 1800 `
        -CaptureProfile $CaptureProfile -PythonPath $PythonPath -GameDirectory $GameDirectory
} else {
    & (Join-Path $PSScriptRoot 'start_live_meter.ps1') -Seconds ($Hours * 3600) `
        -CaptureProfile $CaptureProfile -PythonPath $PythonPath -GameDirectory $GameDirectory
}
