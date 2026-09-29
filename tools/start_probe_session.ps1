param(
    [Parameter(Mandatory = $true)][int]$TargetPid,
    [int]$Minutes = 30,
    [string]$PythonPath = 'C:\Python313\python.exe',
    [switch]$TryUnprivileged
)

$ErrorActionPreference = 'Stop'
if ($Minutes -lt 1 -or $Minutes -gt 1500) { throw 'Minutes must be 1..1500.' }
$server = Join-Path $PSScriptRoot 'elevated_probe_session.py'
$dataDir = if ($env:SORA2_DETAILS_DATA_DIR) { $env:SORA2_DETAILS_DATA_DIR } else { Join-Path $env:LOCALAPPDATA 'Sora2 Details' }
$sessionDir = Join-Path $dataDir 'probe-session'
$readyPath = Join-Path $sessionDir 'ready.json'
$startupErrorPath = Join-Path $sessionDir 'startup-error.json'
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$isAdministrator = [Security.Principal.WindowsPrincipal]::new($identity).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator)
if ($TryUnprivileged -and $isAdministrator) {
    throw 'Run -TryUnprivileged from a standard-user shell. An elevated process cannot lower its token.'
}
if (-not $TryUnprivileged -and -not $isAdministrator) {
    throw 'The production app starts elevated before capture. For standard-user diagnostics only, run this script with -TryUnprivileged from a standard-user shell.'
}
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
            return
        }
    }
}
$null = New-Item -ItemType Directory -Path $sessionDir -Force
Remove-Item -LiteralPath $startupErrorPath -Force -ErrorAction SilentlyContinue
$captureHost = Join-Path (Split-Path $PSScriptRoot -Parent) 'Sora2.Details.CaptureHost.exe'
if ($TryUnprivileged) {
    $useCaptureHost = $false
    $elevationExe = $PythonPath
    $arguments = '"' + $server + '" --session-dir "' + $sessionDir +
        '" serve --pid ' + $TargetPid + ' --minutes ' + $Minutes
} else {
    $useCaptureHost = Test-Path -LiteralPath $captureHost
    if ($useCaptureHost) {
        # A final dot preserves drive roots and avoids a backslash before the closing quote.
        $hostDataDir = Join-Path ([IO.Path]::GetFullPath($dataDir)) '.'
        $arguments = "$TargetPid $Minutes `"$hostDataDir`""
        $elevationExe = $captureHost
    } else {
        # Research checkouts and the legacy external-Python ZIP retain their launcher.
        $elevationExe = $PythonPath
        $arguments = '"' + $server + '" --session-dir "' + $sessionDir +
            '" serve --pid ' + $TargetPid + ' --minutes ' + $Minutes
    }
}
$startInfo = [Diagnostics.ProcessStartInfo]::new()
$startInfo.FileName = $elevationExe
$startInfo.Arguments = $arguments
$startInfo.WorkingDirectory = Split-Path -Parent $server
$startInfo.UseShellExecute = $false
$startInfo.CreateNoWindow = $true
$startInfo.WindowStyle = [Diagnostics.ProcessWindowStyle]::Hidden
# CreateProcess with no alternate token makes the host and Python child inherit
# the app's already-approved token. No child capture process asks for UAC.
$process = [Diagnostics.Process]::Start($startInfo)
if ($null -eq $process) { throw 'Could not start the probe session process.' }
for ($attempt = 0; $attempt -lt 100; $attempt++) {
    Start-Sleep -Milliseconds 100
    if (Test-Path -LiteralPath $readyPath) {
        $ready = Get-Content -LiteralPath $readyPath -Raw | ConvertFrom-Json
        $launcherPid = if ($useCaptureHost) { $ready.hostPid } else { $ready.serverPid }
        if ($launcherPid -eq $process.Id -and -not $ready.stopped) {
            Remove-Item -LiteralPath $startupErrorPath -Force -ErrorAction SilentlyContinue
            Write-Output "Probe session ready (PID $($ready.serverPid)); expires $($ready.expiresAt)."
            return
        }
    }
    if ($process.HasExited) {
        $detail = ''
        if (Test-Path -LiteralPath $startupErrorPath) {
            try {
                $startupError = Get-Content -LiteralPath $startupErrorPath -Raw | ConvertFrom-Json
                $detail = " $($startupError.error)"
            } catch { }
        }
        Remove-Item -LiteralPath $startupErrorPath -Force -ErrorAction SilentlyContinue
        throw "Probe session exited with code $($process.ExitCode).$detail"
    }
}
try { & $PythonPath $server send stop --no-wait 2>$null | Out-Null } catch { }
for ($attempt = 0; $attempt -lt 50 -and -not $process.HasExited; $attempt++) {
    Start-Sleep -Milliseconds 100
}
if (-not $process.HasExited) {
    try {
        $taskkill = Join-Path $env:SystemRoot 'System32\taskkill.exe'
        $null = Start-Process -FilePath $taskkill -ArgumentList @('/PID', $process.Id.ToString(), '/T', '/F') `
            -WindowStyle Hidden -Wait -PassThru
    } catch {
        throw "Probe session did not become ready within ten seconds, and its helper process tree could not be stopped: $($_.Exception.Message)"
    }
}
if (-not $process.WaitForExit(5000)) {
    throw 'Probe session did not become ready within ten seconds, and helper shutdown could not be confirmed.'
}
throw 'Probe session did not become ready within ten seconds. The helper process tree was stopped.'
