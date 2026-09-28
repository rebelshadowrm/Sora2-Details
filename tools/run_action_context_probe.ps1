param(
    [Parameter(Mandatory = $true)][int]$TargetPid,
    [Parameter(Mandatory = $true)][string]$OutputPath,
    [int]$Seconds = 300,
    [string]$PythonPath = 'C:\Python313\python.exe'
)

$ErrorActionPreference = 'Stop'
$probe = Join-Path $PSScriptRoot 'lifecycle_probe.py'
$hash = 'D8B2911D1576216BDC22D070550E4F531E105DE7ED2981885849669F4ACF8AAF'
try {
    & $PythonPath $probe $TargetPid `
        --expected-sha256 $hash `
        --rva BattleCommandBegin=0x1175B8 `
        --rva EffectEntry=0xE4A60 `
        --inspect-effect-entry EffectEntry `
        --rva HpSet=0xF8EB3 `
        --inspect-hp-set HpSet `
        --rva BattleEnd=0xBA659 `
        --seconds $Seconds --max-hits 5000 2>&1 |
        Out-File -LiteralPath $OutputPath -Encoding UTF8
    if ($LASTEXITCODE -ne 0) {
        "Probe exited with code $LASTEXITCODE" | Add-Content -LiteralPath $OutputPath
    }
} catch {
    $_ | Out-File -LiteralPath $OutputPath -Encoding UTF8
}
