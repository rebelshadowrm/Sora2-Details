param(
    [Parameter(Mandatory = $true)][int]$TargetPid,
    [Parameter(Mandatory = $true)][string]$OutputPath,
    [string]$SourceContext,
    [string]$TargetContext,
    [string]$ExtraStatus,
    [string]$PythonPath = 'C:\Python313\python.exe'
)

$ErrorActionPreference = 'Stop'
$probe = Join-Path $PSScriptRoot 'read_status_identity.py'
try {
    $probeArgs = @($probe, $TargetPid,
        '0x16c50ee5588', '0x16c50ee45c8', '0x16c50ee4b08', '0x16c50ee52e8')
    if ($SourceContext) { $probeArgs += @('--context', $SourceContext) }
    if ($TargetContext) { $probeArgs += @('--context', $TargetContext) }
    if ($ExtraStatus) { $probeArgs += @('--extra-status', $ExtraStatus) }
    & $PythonPath @probeArgs 2>&1 |
        Out-File -LiteralPath $OutputPath -Encoding UTF8
    if ($LASTEXITCODE -ne 0) {
        "Probe exited with code $LASTEXITCODE" | Add-Content -LiteralPath $OutputPath
    }
} catch {
    $_ | Out-File -LiteralPath $OutputPath -Encoding UTF8
}
