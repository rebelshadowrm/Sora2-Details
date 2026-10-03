param(
    [Parameter(Mandatory = $true)][int]$TargetPid,
    [Parameter(Mandatory = $true)][string]$GameDirectory,
    [string]$PythonPath
)
$ErrorActionPreference = 'Stop'
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
if (-not [Security.Principal.WindowsPrincipal]::new($identity).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Start action recording from the elevated desktop session; this helper does not request another elevation.'
}
$root = Split-Path $PSScriptRoot -Parent
if (-not $PythonPath) {
    foreach ($candidate in @((Join-Path $root 'python\python.exe'), 'C:\Python313\python.exe')) {
        if (Test-Path -LiteralPath $candidate) { $PythonPath = $candidate; break }
    }
}
if (-not $PythonPath) { throw 'Action recording requires the bundled Python runtime or -PythonPath.' }
$game = Get-Process -Id $TargetPid
if ($game.ProcessName -ne 'sora_2nd' -or
    [IO.Path]::GetFullPath($game.Path) -ne [IO.Path]::GetFullPath((Join-Path $GameDirectory 'sora_2nd.exe'))) {
    throw 'The selected game location does not match the running game.'
}
if ((Get-FileHash -LiteralPath $game.Path -Algorithm SHA256).Hash -ne
    'D8B2911D1576216BDC22D070550E4F531E105DE7ED2981885849669F4ACF8AAF') {
    throw 'This executable is not supported by the action-stream probe.'
}
$table = Join-Path $GameDirectory 'pac\steam\table_en.pac'
& $PythonPath -B -c 'import sys; from pathlib import Path; sys.path.insert(0,sys.argv[1]); from reconcile_action_stream import DescriptorLookup; from name_table_index import read_rows; DescriptorLookup(Path(sys.argv[2])); read_rows(Path(sys.argv[2]))' $PSScriptRoot $table
if ($LASTEXITCODE -ne 0) { throw 'The English lookup tables did not pass their fingerprint checks.' }
$dataDir = if ($env:SORA2_DETAILS_DATA_DIR) { $env:SORA2_DETAILS_DATA_DIR }
    else { Join-Path $env:LOCALAPPDATA 'Sora2 Details' }
$currentPath = Join-Path $dataDir 'live\current.json'
if (Test-Path -LiteralPath $currentPath) {
    $current = Get-Content -LiteralPath $currentPath -Raw | ConvertFrom-Json
    foreach ($helperId in @($current.serverPid, $current.hostPid, $current.bridgePid)) {
        if ($helperId -and (Get-Process -Id $helperId -ErrorAction SilentlyContinue)) {
            throw 'Stop the existing capture before starting action recording.'
        }
    }
    if (-not (Test-Path -LiteralPath $current.trace) -or
        -not (Get-Content -LiteralPath $current.trace -Tail 20 | Select-String '"kind": "detached"')) {
        throw 'The previous capture has no verified detach. Use Stop capture first.'
    }
}
$batchId = [Guid]::NewGuid().ToString('N')
$directory = Join-Path $dataDir 'research\action-stream'
$null = New-Item -ItemType Directory -Path $directory -Force
$stop = Join-Path $directory "stop-$batchId"
$trace = Join-Path $directory "action-stream-$batchId.jsonl"
$arguments = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
    ('"' + (Join-Path $PSScriptRoot 'run_action_stream_probe.ps1') + '"'),
    '-TargetPid', $TargetPid, '-CaptureFocus', 'Transcript', '-RegisterSession', '-BatchId', $batchId,
    '-PythonPath', ('"' + $PythonPath + '"'), '-GameDirectory', ('"' + $GameDirectory + '"'))
$launcher = Start-Process powershell.exe -ArgumentList $arguments -WindowStyle Hidden -PassThru `
    -WorkingDirectory $PSScriptRoot -RedirectStandardOutput (Join-Path $directory "launcher-$batchId.stdout.log") `
    -RedirectStandardError (Join-Path $directory "launcher-$batchId.stderr.log")
# This is an arming wait, never a capture duration. The owner remains alive after we return.
$deadline = [DateTime]::UtcNow.AddSeconds(30)
while ([DateTime]::UtcNow -lt $deadline) {
    if ($env:SORA2_DETAILS_CAPTURE_START_CANCEL_FILE -and
        (Test-Path -LiteralPath $env:SORA2_DETAILS_CAPTURE_START_CANCEL_FILE)) {
        [IO.File]::WriteAllText($stop, 'stop'); throw 'Action recording startup was canceled; detach requested.'
    }
    if ($launcher.HasExited) { throw "Action recording failed to arm. See launcher-$batchId.stderr.log." }
    if (Test-Path -LiteralPath $trace) {
        $header = Get-Content -LiteralPath $trace -TotalCount 12 | Out-String
        if ($header.Contains('"kind": "armed"')) {
            $manifest = Get-Content -LiteralPath $currentPath -Raw | ConvertFrom-Json
            if ($manifest.requestId -eq $batchId -and $manifest.serverPid -eq $launcher.Id -and
                (Get-Process -Id $manifest.bridgePid -ErrorAction SilentlyContinue)) {
                # The bridge starts before the probe. Its first snapshot can precede
                # the armed marker, so a living bridge alone is not viewer readiness.
                if (Test-Path -LiteralPath $manifest.ledgerPath) {
                    $ledger = Get-Content -LiteralPath $manifest.ledgerPath -Raw | ConvertFrom-Json
                    if ($ledger.tracePath -eq $trace -and
                        ($ledger.observations | Where-Object { $_.raw.kind -eq 'armed' })) {
                        Write-Output "Recording action stream; manual stop only. Ledger: $($manifest.ledgerPath)"
                        exit 0
                    }
                }
            }
        }
    }
    Start-Sleep -Milliseconds 100
}
[IO.File]::WriteAllText($stop, 'stop')
throw 'Action recording did not arm within 30 seconds; detach requested. Use Stop capture to verify cleanup.'
