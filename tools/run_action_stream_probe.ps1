param(
    [Parameter(Mandatory = $true)][int]$TargetPid,
    [ValidateSet('Conditions', 'ConditionInsert', 'ConditionRemove', 'ConditionAttempt', 'ConditionLifecycle', 'Queue', 'Setup', 'Launch', 'Stages', 'Transcript')][string]$CaptureFocus = 'Conditions',
    [string]$PythonPath = 'C:\Python313\python.exe',
    [string]$GameDirectory = 'C:\Games\Trails in the Sky 2nd Chapter',
    [string]$BatchId,
    [switch]$RegisterSession
)

$ErrorActionPreference = 'Stop'
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
if (-not [Security.Principal.WindowsPrincipal]::new($identity).IsInRole(
        [Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Run this research probe from an elevated session. It does not request elevation itself.'
}
$dataDir = if ($env:SORA2_DETAILS_DATA_DIR) { $env:SORA2_DETAILS_DATA_DIR }
    else { Join-Path $env:LOCALAPPDATA 'Sora2 Details' }
$currentPath = Join-Path $dataDir 'live\current.json'
if (Test-Path -LiteralPath $currentPath) {
    $current = Get-Content -LiteralPath $currentPath -Raw | ConvertFrom-Json
    foreach ($helperId in @($current.serverPid, $current.hostPid, $current.bridgePid)) {
        if ($helperId -and (Get-Process -Id $helperId -ErrorAction SilentlyContinue)) {
            throw 'Stop the current capture before attaching this separate raw research probe.'
        }
    }
}
$researchDir = Join-Path $dataDir 'research\action-stream'
$null = New-Item -ItemType Directory -Path $researchDir -Force
if ($BatchId -and $BatchId -notmatch '^[a-f0-9]{32}$') { throw 'BatchId must be a lowercase GUID without separators.' }
if (-not $BatchId) { $BatchId = [Guid]::NewGuid().ToString('N') }
$batchId = $BatchId
if ($RegisterSession -and $CaptureFocus -ne 'Transcript') { throw 'Only Transcript can register an application session.' }
$outputPath = Join-Path $researchDir "action-stream-$batchId.jsonl"
$stopPath = Join-Path $researchDir "stop-$batchId"
$probe = Join-Path $PSScriptRoot 'lifecycle_probe.py'
Write-Output "Raw research trace: $outputPath"
Write-Output "Stop sentinel: $stopPath"
Write-Output 'Capture remains armed until explicitly stopped; no duration or hit-count cutoff.'
Write-Output "Research focus: $CaptureFocus"
# Candidate stages only. Transcript starts a separate lossless research projection.
$probeArgs = @('-B', $probe, [string]$TargetPid,
    '--expected-sha256', 'D8B2911D1576216BDC22D070550E4F531E105DE7ED2981885849669F4ACF8AAF',
    '--until-stop-file', '--stop-file', $stopPath)
if ($CaptureFocus -ne 'ConditionLifecycle') {
    $probeArgs += @('--rva', 'EffectDispatchEntry=0xDBE40', '--inspect-effect-dispatch', 'EffectDispatchEntry')
}
if ($CaptureFocus -eq 'ConditionLifecycle') {
    $probeArgs += @('--rva', 'ConditionRequestEntry=0x7F750', '--inspect-condition-request', 'ConditionRequestEntry',
        '--rva', 'ConditionRequestReturnSite=0x7FDE7', '--inspect-condition-return', 'ConditionRequestReturnSite',
        '--rva', 'ConditionRemoveEntry=0x80730', '--inspect-condition-return', 'ConditionRemoveEntry',
        '--rva', 'ConditionRemoveReturnSite=0x80780', '--inspect-condition-return', 'ConditionRemoveReturnSite')
} elseif ($CaptureFocus -eq 'Transcript') {
    $probeArgs += @('--rva', 'ActorStateDispatchCall=0x7A68B', '--inspect-actor-state-dispatch', 'ActorStateDispatchCall',
        '--first-state-update-only', 'ActorStateDispatchCall',
        '--rva', 'ResourceSetEntry=0xF8DB0', '--inspect-resource-set', 'ResourceSetEntry',
        '--write-pointer-rva', 'BattleModeWrite=0xC5D768,0x2D30')
} elseif ($CaptureFocus -eq 'ConditionAttempt') {
    $probeArgs += @('--rva', 'ConditionRequestEntry=0x7F750', '--inspect-condition-request', 'ConditionRequestEntry',
        '--rva', 'ConditionRequestReturnSite=0x7FDE7', '--inspect-condition-return', 'ConditionRequestReturnSite',
        '--rva', 'ConditionInsertReturnSite=0x7FD63', '--inspect-condition-return', 'ConditionInsertReturnSite')
} elseif ($CaptureFocus -eq 'ConditionRemove') {
    $probeArgs += @('--rva', 'ConditionInsertReturnSite=0x7FD63', '--inspect-condition-return', 'ConditionInsertReturnSite',
        '--rva', 'ConditionRemoveEntry=0x80730', '--inspect-condition-return', 'ConditionRemoveEntry',
        '--rva', 'ConditionRemoveReturnSite=0x80780', '--inspect-condition-return', 'ConditionRemoveReturnSite')
} elseif ($CaptureFocus -eq 'ConditionInsert') {
    $probeArgs += @('--rva', 'ConditionRequestEntry=0x7F750', '--inspect-condition-request', 'ConditionRequestEntry',
        '--rva', 'ConditionInsertReturnSite=0x7FD63', '--inspect-condition-return', 'ConditionInsertReturnSite',
        '--rva', 'ResourceSetEntry=0xF8DB0', '--inspect-resource-set', 'ResourceSetEntry')
} elseif ($CaptureFocus -eq 'Stages') {
    $probeArgs += @('--rva', 'ActorStateDispatchCall=0x7A68B', '--inspect-actor-state-dispatch', 'ActorStateDispatchCall',
        '--first-state-update-only', 'ActorStateDispatchCall',
        '--rva', 'AnimationLaunchAccepted=0x21558F', '--inspect-animation-accepted', 'AnimationLaunchAccepted',
        '--rva', 'ResourceSetEntry=0xF8DB0', '--inspect-resource-set', 'ResourceSetEntry')
} elseif ($CaptureFocus -eq 'Launch') {
    $probeArgs += @('--rva', 'AnimationLaunchEntry=0x215320', '--inspect-animation-request', 'AnimationLaunchEntry',
        '--rva', 'AnimationLaunchAccepted=0x21558F', '--inspect-animation-accepted', 'AnimationLaunchAccepted',
        '--rva', 'ResourceSetEntry=0xF8DB0', '--inspect-resource-set', 'ResourceSetEntry')
} elseif ($CaptureFocus -eq 'Setup') {
    $probeArgs += @('--rva', 'ActionSetupEntry=0x68F80', '--inspect-action-setup', 'ActionSetupEntry')
} else {
    $probeArgs += @('--rva', 'ConditionReturnSite=0xDE962', '--inspect-condition-return', 'ConditionReturnSite')
}
if ($CaptureFocus -in @('Launch', 'Stages', 'Transcript', 'ConditionInsert', 'ConditionRemove', 'ConditionAttempt', 'ConditionLifecycle')) {
    # All four slots are already assigned above; pending descriptors are inline
    # in both launch snapshots rather than a separate store/resume breakpoint.
} elseif ($CaptureFocus -in @('Queue', 'Setup')) {
    $probeArgs += @('--rva', 'DescriptorStoreSite=0x68E20', '--inspect-queue-store', 'DescriptorStoreSite',
        '--rva', 'DescriptorResumeSite=0x69111', '--inspect-queue-resume', 'DescriptorResumeSite')
} else {
    $probeArgs += @('--rva', 'CommandStageEntry=0x1179A0', '--inspect-action-state', 'CommandStageEntry',
        '--rva', 'ConditionRequestEntry=0x7F750', '--inspect-condition-request', 'ConditionRequestEntry')
}
$transcriptBridge = $null
if ($CaptureFocus -eq 'Transcript') {
    $ledgerPath = Join-Path $researchDir "ledger-$batchId.json"
    $bridgePath = Join-Path $PSScriptRoot 'action_transcript_bridge.py'
    $tablePath = Join-Path $GameDirectory 'pac\steam\table_en.pac'
    $bridgeArguments = @('-B', ('"' + $bridgePath + '"'), ('"' + $outputPath + '"'),
        '--output', ('"' + $ledgerPath + '"'), '--skill-pac', ('"' + $tablePath + '"'), '--watch')
    $transcriptBridge = Start-Process -FilePath $PythonPath -ArgumentList $bridgeArguments -WindowStyle Hidden -PassThru `
        -RedirectStandardError (Join-Path $researchDir "bridge-$batchId.stderr.log")
    # Retain the process handle before a short-lived bridge exits. Windows PowerShell's
    # Start-Process object can otherwise lose ExitCode even after WaitForExit succeeds.
    $null = $transcriptBridge.Handle
    Write-Output "Research transcript: $ledgerPath"
}
try {
    if ($RegisterSession) {
        $null = New-Item -ItemType Directory -Path (Split-Path $currentPath) -Force
        $manifest = @{
            trace = $outputPath; stopFile = $stopPath; ledgerPath = $ledgerPath
            serverPid = $PID; bridgePid = $transcriptBridge.Id; hostPid = 0
            targetPid = $TargetPid; requestId = $batchId; captureProfile = 'Transcript'
        } | ConvertTo-Json
        $temporaryManifest = "$currentPath.$batchId.tmp"
        [IO.File]::WriteAllText($temporaryManifest, $manifest, [Text.UTF8Encoding]::new($false))
        Move-Item -LiteralPath $temporaryManifest -Destination $currentPath -Force
    }
    & $PythonPath @probeArgs 2>&1 |
        Out-File -LiteralPath $outputPath -Encoding UTF8
    if ($LASTEXITCODE -ne 0) { throw "Research probe failed; preserved trace: $outputPath" }
    if ($transcriptBridge) {
        if (-not $transcriptBridge.WaitForExit(10000)) { throw 'Research projection did not finish after probe detach.' }
        if ($transcriptBridge.ExitCode -ne 0) { throw 'Research projection failed; inspect its preserved stderr log.' }
    }
} catch {
    if ($RegisterSession) {
        $results = Join-Path $dataDir 'probe-session\results'
        $null = New-Item -ItemType Directory -Path $results -Force
        @{ ok = $false; error = $_.Exception.Message } | ConvertTo-Json |
            Set-Content -LiteralPath (Join-Path $results "$batchId.json") -Encoding UTF8
    }
    throw
} finally {
    if ($transcriptBridge -and -not $transcriptBridge.HasExited) { $transcriptBridge.Kill() }
}
Write-Output "Research probe finished; inspect armed/disarmed/detached markers in $outputPath."
