param(
    [int]$Seconds = 1800,
    [string]$PythonPath = 'C:\Python313\python.exe'
)

$ErrorActionPreference = 'Stop'
if ($Seconds -lt 60 -or $Seconds -gt 3600) { throw 'Seconds must be 60..3600.' }
$root = Split-Path $PSScriptRoot -Parent
$games = @(Get-Process -Name sora_2nd -ErrorAction SilentlyContinue)
if ($games.Count -ne 1) { throw "Expected one running sora_2nd process; found $($games.Count)." }

$minutes = [int][Math]::Ceiling($Seconds / 60.0) + 3
& (Join-Path $PSScriptRoot 'start_probe_session.ps1') -TargetPid $games[0].Id `
    -Minutes $minutes -PythonPath $PythonPath

$request = & $PythonPath (Join-Path $PSScriptRoot 'elevated_probe_session.py') `
    send critical_long_capture --seconds $Seconds --no-wait
if ($LASTEXITCODE -ne 0) { throw "Could not queue critical capture: $request" }
if (($request -join "`n") -match 'Request ([0-9a-f]+) queued') {
    $requestId = $Matches[1]
} else { throw "Could not read critical capture request ID: $request" }

$trace = Join-Path $root ".research-deps\live\probe-session-$requestId.jsonl"
$stopFile = Join-Path $root ".research-deps\live\stop-$requestId"
$armed = $false
for ($attempt = 0; $attempt -lt 100; $attempt++) {
    Start-Sleep -Milliseconds 100
    if (Test-Path -LiteralPath $trace) {
        $head = Get-Content -LiteralPath $trace -TotalCount 5
        if ($head -match '"kind": "armed"') { $armed = $true; break }
    }
}
if (-not $armed) { throw "Probe did not arm within ten seconds. Inspect $trace" }

Write-Output "Critical research capture armed for $Seconds seconds (game PID $($games[0].Id))."
Write-Output "Trace: $trace"
Write-Output "To stop early: New-Item -ItemType File -Path '$stopFile' -Force"
