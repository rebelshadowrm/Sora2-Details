$ErrorActionPreference = 'Stop'
$dataDir = if ($env:SORA2_DETAILS_DATA_DIR) { $env:SORA2_DETAILS_DATA_DIR } else { Join-Path $env:LOCALAPPDATA 'Sora2 Details' }
$currentPath = Join-Path $dataDir 'live\current.json'
if (-not (Test-Path -LiteralPath $currentPath)) { throw 'No live meter session record found.' }
$current = Get-Content -LiteralPath $currentPath -Raw | ConvertFrom-Json
if (-not $current.stopFile) { throw 'Live session record has no stop file.' }
Set-Content -LiteralPath $current.stopFile -Value 'stop' -Encoding ASCII
Write-Output 'Clean detach requested; the probe and bridge should stop within a few seconds.'
