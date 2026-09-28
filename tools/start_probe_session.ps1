param(
    [Parameter(Mandatory = $true)][int]$TargetPid,
    [int]$Minutes = 30,
    [string]$PythonPath = 'C:\Python313\python.exe'
)

$ErrorActionPreference = 'Stop'
if ($Minutes -lt 1 -or $Minutes -gt 1500) { throw 'Minutes must be 1..1500.' }
$server = Join-Path $PSScriptRoot 'elevated_probe_session.py'
$sessionDir = Join-Path (Split-Path $PSScriptRoot -Parent) '.research-deps\probe-session'
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
$process = Start-Process -FilePath $PythonPath -ArgumentList $arguments `
    -Verb RunAs -WindowStyle Hidden -PassThru
for ($attempt = 0; $attempt -lt 100; $attempt++) {
    Start-Sleep -Milliseconds 100
    if (Test-Path -LiteralPath $readyPath) {
        $ready = Get-Content -LiteralPath $readyPath -Raw | ConvertFrom-Json
        if ($ready.serverPid -eq $process.Id -and -not $ready.stopped) {
            Write-Output "Probe session ready (PID $($process.Id)); expires $($ready.expiresAt)."
            exit 0
        }
    }
    if ($process.HasExited) { throw "Elevated probe session exited with code $($process.ExitCode)." }
}
throw 'Elevated probe session did not become ready within ten seconds.'
