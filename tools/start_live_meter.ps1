param(
    [int]$Seconds = 1800,
    [string]$PythonPath,
    [string]$GameDirectory = 'C:\Games\Trails in the Sky 2nd Chapter'
)

$ErrorActionPreference = 'Stop'
if ($Seconds -lt 60 -or $Seconds -gt 43200) { throw 'Seconds must be 60..43200.' }
$root = Split-Path $PSScriptRoot -Parent
if (-not $PythonPath) {
    $candidates = @((Join-Path $root 'python\python.exe'), 'C:\Python313\python.exe') + @(
        Get-Command python.exe -All -ErrorAction SilentlyContinue | ForEach-Object { $_.Source }
    )
    foreach ($candidate in $candidates | Select-Object -Unique) {
        if (-not (Test-Path -LiteralPath $candidate)) { continue }
        try {
            $result = & $candidate -c 'import sys; print(int(sys.version_info >= (3, 11) and sys.maxsize > 2**32))' 2>$null
            if ($LASTEXITCODE -eq 0 -and $result -eq '1') { $PythonPath = $candidate; break }
        } catch { }
    }
}
if (-not $PythonPath) { throw 'Live capture needs 64-bit Python 3.11 or newer. Pass -PythonPath or use the bundled runtime.' }
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
$desktopExe = Join-Path $root 'Sora2.Details.Desktop.exe'
if (-not (Test-Path -LiteralPath $desktopExe)) {
    $desktopExe = Join-Path $root 'app\Sora2.Details.Desktop.exe'
}
if (-not (Test-Path -LiteralPath $desktopExe)) {
    $desktopExe = Join-Path $root 'src\Sora2.Details.Desktop\bin\Release\net9.0-windows\Sora2.Details.Desktop.exe'
}
if (-not (Test-Path -LiteralPath $desktopExe)) {
    throw 'Build the solution in Release mode before starting the live meter.'
}
$games = @(Get-Process -Name sora_2nd -ErrorAction SilentlyContinue)
if ($games.Count -ne 1) { throw "Expected one running sora_2nd process; found $($games.Count)." }

$dataDir = if ($env:SORA2_DETAILS_DATA_DIR) { $env:SORA2_DETAILS_DATA_DIR } else { Join-Path $env:LOCALAPPDATA 'Sora2 Details' }
$liveDir = Join-Path $dataDir 'live'
New-Item -ItemType Directory -Path $liveDir -Force | Out-Null
$currentPath = Join-Path $liveDir 'current.json'
if (Test-Path -LiteralPath $currentPath) {
    $current = Get-Content -LiteralPath $currentPath -Raw | ConvertFrom-Json
    $helperPids = @($current.bridgePid, $current.serverPid, $current.hostPid) |
        Where-Object { $_ -and (Get-Process -Id $_ -ErrorAction SilentlyContinue) }
    if ($helperPids.Count -gt 0) {
        throw "A live capture helper is still running (PID $($helperPids -join ', ')). Use tools/stop_live_meter.ps1 first."
    }
    Remove-Item -LiteralPath $currentPath -Force
}

$minutes = [int][Math]::Ceiling($Seconds / 60.0) + 3
$captureAction = if ($Seconds -gt 3600) { 'session_capture' } else { 'live_capture' }
$sessionDir = Join-Path $dataDir 'probe-session'
$readyPath = Join-Path $sessionDir 'ready.json'
$server = Join-Path $PSScriptRoot 'elevated_probe_session.py'

function Start-CaptureAttempt {
    try {
        & (Join-Path $PSScriptRoot 'start_probe_session.ps1') -TargetPid $games[0].Id `
            -Minutes $minutes -PythonPath $PythonPath -ErrorAction Stop | Out-Null
    } catch {
        throw
    }

    try {
        $sessionReady = Get-Content -LiteralPath $readyPath -Raw | ConvertFrom-Json
        $requestOutput = & $PythonPath $server send $captureAction --seconds $Seconds --no-wait
        if ($LASTEXITCODE -ne 0) { throw "Could not queue live capture: $requestOutput" }
        if (($requestOutput -join "`n") -match 'Request ([0-9a-f]+) queued') {
            $attemptRequestId = $Matches[1]
        } else { throw "Could not read live capture request ID: $requestOutput" }

        $attemptTrace = Join-Path $liveDir "probe-session-$attemptRequestId.jsonl"
        $attemptStopFile = Join-Path $liveDir "stop-$attemptRequestId"
        @{
            requestId = $attemptRequestId
            targetPid = $games[0].Id
            bridgePid = 0
            desktopPid = $PID
            serverPid = $sessionReady.serverPid
            hostPid = $sessionReady.hostPid
            sessionId = $sessionReady.sessionId
            pythonPath = $PythonPath
            trace = $attemptTrace
            stopFile = $attemptStopFile
        } | ConvertTo-Json | Set-Content -LiteralPath $currentPath -Encoding UTF8
        $resultPath = Join-Path $sessionDir "results\$attemptRequestId.json"
        for ($attempt = 0; $attempt -lt 100; $attempt++) {
            if (Test-Path -LiteralPath $attemptTrace) {
                $traceText = Get-Content -LiteralPath $attemptTrace -Raw
                if ($traceText -match '"kind": "armed"') {
                    return [pscustomobject]@{ Armed = $true; SessionStarted = $true;
                        RequestId = $attemptRequestId; Trace = $attemptTrace;
                        SessionId = $sessionReady.sessionId; ServerPid = $sessionReady.serverPid;
                        HostPid = $sessionReady.hostPid }
                }
            } else { $traceText = '' }

            if (Test-Path -LiteralPath $resultPath) {
                $result = Get-Content -LiteralPath $resultPath -Raw | ConvertFrom-Json
                if (-not $result.ok) {
                    if ($result.output -and (Test-Path -LiteralPath $result.output)) {
                        $traceText += "`n" + (Get-Content -LiteralPath $result.output -Raw)
                    }
                    throw "Probe failed before arming. Inspect $attemptTrace`n$traceText"
                }
            }
            Start-Sleep -Milliseconds 100
        }
        throw "Probe did not arm within ten seconds. Inspect $attemptTrace"
    } catch {
        if ($attemptStopFile) {
            try { Set-Content -LiteralPath $attemptStopFile -Value 'stop' -Encoding ASCII } catch { }
        }
        & $PythonPath $server send stop --no-wait 2>$null | Out-Null
        throw
    }
}

$captureAttempt = Start-CaptureAttempt
if (-not $captureAttempt.Armed) { throw "Probe did not arm. Inspect $($captureAttempt.Trace)" }
$requestId = $captureAttempt.RequestId
$trace = $captureAttempt.Trace
$stopFile = Join-Path $liveDir "stop-$requestId"
@{
    requestId = $requestId
    targetPid = $games[0].Id
    bridgePid = 0
    desktopPid = $PID
    serverPid = $captureAttempt.ServerPid
    hostPid = $captureAttempt.HostPid
    sessionId = $captureAttempt.SessionId
    pythonPath = $PythonPath
    trace = $trace
    stopFile = $stopFile
} | ConvertTo-Json | Set-Content -LiteralPath $currentPath -Encoding UTF8

# The server processes this after the bounded capture returns or its stop file is seen.
& $PythonPath $server send stop --no-wait | Out-Null

$bridge = Join-Path $PSScriptRoot 'live_capture_bridge.py'
$arguments = '"' + $bridge + '" "' + $trace + '" --table-pac "' + $tablePac +
    '" --script-pac "' + $scriptPac + '" --follow --max-wait-seconds ' + ($Seconds + 60)
$bridgeStart = [Diagnostics.ProcessStartInfo]::new()
$bridgeStart.FileName = $PythonPath
$bridgeStart.Arguments = $arguments
$bridgeStart.WorkingDirectory = $root
$bridgeStart.UseShellExecute = $false
$bridgeStart.CreateNoWindow = $true
$bridgeStart.WindowStyle = [Diagnostics.ProcessWindowStyle]::Hidden
$bridgeProcess = [Diagnostics.Process]::Start($bridgeStart)
if ($null -eq $bridgeProcess) { throw 'Could not start the live-capture bridge.' }

@{
    requestId = $requestId
    targetPid = $games[0].Id
    bridgePid = $bridgeProcess.Id
    desktopPid = $PID
    serverPid = $captureAttempt.ServerPid
    hostPid = $captureAttempt.HostPid
    sessionId = $captureAttempt.SessionId
    pythonPath = $PythonPath
    trace = $trace
    stopFile = $stopFile
} | ConvertTo-Json | Set-Content -LiteralPath $currentPath -Encoding UTF8

Remove-Item Env:\SORA2_DETAILS_RESEARCH_REPLAY -ErrorAction SilentlyContinue
$runningDesktop = @(Get-Process -Name 'Sora2.Details.Desktop' -ErrorAction SilentlyContinue)
$desktopProcess = if ($runningDesktop.Count -eq 1) {
    $runningDesktop[0]
} else {
    $desktopStart = [Diagnostics.ProcessStartInfo]::new()
    $desktopStart.FileName = $desktopExe
    $desktopStart.Arguments = '--data-dir "' + $dataDir + '"'
    $desktopStart.WorkingDirectory = $root
    $desktopStart.UseShellExecute = $false
    $desktopProcess = [Diagnostics.Process]::Start($desktopStart)
    if ($null -eq $desktopProcess) { throw 'Could not start Sora 2 Details.' }
}

@{
    requestId = $requestId
    targetPid = $games[0].Id
    bridgePid = $bridgeProcess.Id
    desktopPid = $desktopProcess.Id
    serverPid = $captureAttempt.ServerPid
    hostPid = $captureAttempt.HostPid
    sessionId = $captureAttempt.SessionId
    pythonPath = $PythonPath
    trace = $trace
    stopFile = $stopFile
} | ConvertTo-Json | Set-Content -LiteralPath $currentPath -Encoding UTF8
Write-Output "LIVE / PARTIAL capture armed for $Seconds seconds (game PID $($games[0].Id))."
Write-Output "Trace: $trace"
Write-Output 'To detach early: .\tools\stop_live_meter.ps1'
