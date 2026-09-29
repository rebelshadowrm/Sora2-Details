param(
    [Parameter(Mandatory = $true)][int]$TargetPid,
    [int]$Minutes = 30,
    [string]$PythonPath = 'C:\Python313\python.exe'
)

$ErrorActionPreference = 'Stop'
if ($Minutes -lt 1 -or $Minutes -gt 1500) { throw 'Minutes must be 1..1500.' }
$server = Join-Path $PSScriptRoot 'elevated_probe_session.py'
$dataDir = if ($env:SORA2_DETAILS_DATA_DIR) { $env:SORA2_DETAILS_DATA_DIR } else { Join-Path $env:LOCALAPPDATA 'Sora2 Details' }
$sessionDir = Join-Path $dataDir 'probe-session'
$readyPath = Join-Path $sessionDir 'ready.json'
if (Test-Path -LiteralPath $readyPath) {
    $ready = Get-Content -LiteralPath $readyPath -Raw | ConvertFrom-Json
    if (-not $ready.stopped -and $ready.serverPid) {
        $existing = Get-Process -Id $ready.serverPid -ErrorAction SilentlyContinue
        if ($existing) {
            if ($ready.targetPid -ne $TargetPid) {
                throw "Probe session PID $($ready.serverPid) targets game PID $($ready.targetPid), not $TargetPid. Stop that session before starting another."
            }
            $expiresAt = [DateTimeOffset]::MinValue
            if ($ready.expiresAt) {
                $expiresAt = [DateTimeOffset]::Parse($ready.expiresAt)
            }
            if ($expiresAt -le [DateTimeOffset]::UtcNow) {
                throw "Probe session PID $($ready.serverPid) has expired and is still stopping. Retry after it exits."
            }
            Write-Output "Probe session already running (PID $($ready.serverPid)); expires $($ready.expiresAt)."
            exit 0
        }
    }
}
$arguments = '"' + $server + '" --session-dir "' + $sessionDir +
    '" serve --pid ' + $TargetPid + ' --minutes ' + $Minutes
$captureHost = Join-Path (Split-Path $PSScriptRoot -Parent) 'Sora2.Details.CaptureHost.exe'
$useCaptureHost = Test-Path -LiteralPath $captureHost
if ($useCaptureHost) {
    # A final dot preserves drive roots and avoids a backslash before the closing quote.
    $hostDataDir = Join-Path ([IO.Path]::GetFullPath($dataDir)) '.'
    $arguments = "$TargetPid $Minutes `"$hostDataDir`""
    $elevationExe = $captureHost
} else {
    # Research checkouts and the legacy external-Python ZIP retain their launcher.
    $elevationExe = $PythonPath
}
try {
    $process = Start-Process -FilePath $elevationExe -ArgumentList $arguments `
        -Verb RunAs -WindowStyle Hidden -PassThru
} catch {
    if ($_.Exception.NativeErrorCode -eq 1223) {
        throw 'Capture permission was declined. Saved encounters remain available; click Capture to try again.'
    }
    throw
}
for ($attempt = 0; $attempt -lt 100; $attempt++) {
    Start-Sleep -Milliseconds 100
    if (Test-Path -LiteralPath $readyPath) {
        $ready = Get-Content -LiteralPath $readyPath -Raw | ConvertFrom-Json
        $launcherPid = if ($useCaptureHost) { $ready.hostPid } else { $ready.serverPid }
        if ($launcherPid -eq $process.Id -and -not $ready.stopped) {
            Write-Output "Probe session ready (PID $($ready.serverPid)); expires $($ready.expiresAt)."
            exit 0
        }
    }
    if ($process.HasExited) { throw "Elevated probe session exited with code $($process.ExitCode)." }
}
throw 'Elevated probe session did not become ready within ten seconds.'
