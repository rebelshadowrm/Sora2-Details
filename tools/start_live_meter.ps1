param(
    [int]$Seconds = 1800,
    [string]$PythonPath = 'C:\Python313\python.exe',
    [string]$GameDirectory = 'C:\Games\Trails in the Sky 2nd Chapter'
)

$ErrorActionPreference = 'Stop'
if ($Seconds -lt 60 -or $Seconds -gt 43200) { throw 'Seconds must be 60..43200.' }
$root = Split-Path $PSScriptRoot -Parent
$gameExe = Join-Path $GameDirectory 'sora_2nd.exe'
$expectedHash = 'D8B2911D1576216BDC22D070550E4F531E105DE7ED2981885849669F4ACF8AAF'
$actualHash = (Get-FileHash -LiteralPath $gameExe -Algorithm SHA256).Hash
if ($actualHash -ne $expectedHash) { throw "Unsupported game executable SHA-256: $actualHash" }
$tablePac = Join-Path $GameDirectory 'pac\steam\table_en.pac'
$scriptPac = Join-Path $GameDirectory 'pac\steam\script_en.pac'
& $PythonPath (Join-Path $PSScriptRoot 'status_name_index.py') $tablePac Emeronecider | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'The English status table does not match the validated lookup payload.' }
& $PythonPath (Join-Path $PSScriptRoot 'name_table_index.py') $tablePac 0 2 4 5 6 | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'The English actor-name table does not match the validated lookup payload.' }
& $PythonPath (Join-Path $PSScriptRoot 'enemy_ai_skill_index.py') $scriptPac mon5031 | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'The English enemy AI script archive does not match the validated build.' }
$desktopExe = Join-Path $root 'app\Sora2.Details.Desktop.exe'
if (-not (Test-Path -LiteralPath $desktopExe)) {
    $desktopExe = Join-Path $root 'src\Sora2.Details.Desktop\bin\Release\net9.0-windows\Sora2.Details.Desktop.exe'
}
if (-not (Test-Path -LiteralPath $desktopExe)) {
    throw 'Build the solution in Release mode before starting the live meter.'
}
$games = @(Get-Process -Name sora_2nd -ErrorAction SilentlyContinue)
if ($games.Count -ne 1) { throw "Expected one running sora_2nd process; found $($games.Count)." }

$liveDir = Join-Path $root '.research-deps\live'
New-Item -ItemType Directory -Path $liveDir -Force | Out-Null
$currentPath = Join-Path $liveDir 'current.json'
if (Test-Path -LiteralPath $currentPath) {
    $current = Get-Content -LiteralPath $currentPath -Raw | ConvertFrom-Json
    if ($current.bridgePid -and (Get-Process -Id $current.bridgePid -ErrorAction SilentlyContinue)) {
        throw 'A live bridge is already running. Use tools/stop_live_meter.ps1 first.'
    }
}

$minutes = [int][Math]::Ceiling($Seconds / 60.0) + 3
& (Join-Path $PSScriptRoot 'start_probe_session.ps1') -TargetPid $games[0].Id `
    -Minutes $minutes -PythonPath $PythonPath

$captureAction = if ($Seconds -gt 3600) { 'session_capture' } else { 'live_capture' }
$request = & $PythonPath (Join-Path $PSScriptRoot 'elevated_probe_session.py') `
    send $captureAction --seconds $Seconds --no-wait
if ($LASTEXITCODE -ne 0) { throw "Could not queue live capture: $request" }
if (($request -join "`n") -match 'Request ([0-9a-f]+) queued') {
    $requestId = $Matches[1]
} else { throw "Could not read live capture request ID: $request" }
$trace = Join-Path $liveDir "probe-session-$requestId.jsonl"
$stopFile = Join-Path $liveDir "stop-$requestId"
$armed = $false
for ($attempt = 0; $attempt -lt 100; $attempt++) {
    Start-Sleep -Milliseconds 100
    if (Test-Path -LiteralPath $trace) {
        $head = Get-Content -LiteralPath $trace -TotalCount 5
        if ($head -match '"kind": "armed"') { $armed = $true; break }
    }
}
if (-not $armed) { throw "Probe did not arm within ten seconds. Inspect $trace" }

$bridge = Join-Path $PSScriptRoot 'live_capture_bridge.py'
$arguments = '"' + $bridge + '" "' + $trace + '" --table-pac "' + $tablePac +
    '" --script-pac "' + $scriptPac + '" --follow --max-wait-seconds ' + ($Seconds + 60)
$bridgeProcess = Start-Process -FilePath $PythonPath -ArgumentList $arguments `
    -WorkingDirectory $root -WindowStyle Hidden -PassThru

Remove-Item Env:\SORA2_DETAILS_RESEARCH_REPLAY -ErrorAction SilentlyContinue
$runningDesktop = @(Get-Process -Name 'Sora2.Details.Desktop' -ErrorAction SilentlyContinue)
$desktopProcess = if ($runningDesktop.Count -eq 1) {
    $runningDesktop[0]
} else {
    Start-Process -FilePath $desktopExe -WorkingDirectory $root -PassThru
}

@{
    requestId = $requestId
    targetPid = $games[0].Id
    bridgePid = $bridgeProcess.Id
    desktopPid = $desktopProcess.Id
    trace = $trace
    stopFile = $stopFile
} | ConvertTo-Json | Set-Content -LiteralPath $currentPath -Encoding UTF8

# The helper processes this once the bounded capture ends or is stopped.
& $PythonPath (Join-Path $PSScriptRoot 'elevated_probe_session.py') send stop --no-wait | Out-Null
Write-Output "LIVE / PARTIAL capture armed for $Seconds seconds (game PID $($games[0].Id))."
Write-Output "Trace: $trace"
Write-Output 'To detach early: .\tools\stop_live_meter.ps1'
