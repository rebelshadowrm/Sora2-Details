param(
    [Parameter(Mandatory = $true)][int]$TargetPid,
    [Parameter(Mandatory = $true)][int]$CurrentHp,
    [Parameter(Mandatory = $true)][int]$MaxHp,
    [Parameter(Mandatory = $true)][string]$PythonPath,
    [Parameter(Mandatory = $true)][string]$OutputPath,
    [string[]]$ReadAddresses,
    [string]$WatchAddress,
    [int]$WatchSeconds = 60
)

$ErrorActionPreference = 'Stop'
try {
    $probe = Join-Path $PSScriptRoot 'hp_memory_probe.py'
    if ($WatchAddress) {
        & $PythonPath $probe $TargetPid $CurrentHp $MaxHp --watch $WatchAddress --seconds $WatchSeconds 2>&1 |
            Out-File -LiteralPath $OutputPath -Encoding UTF8
        return
    } elseif ($ReadAddresses) {
        $result = & $PythonPath $probe $TargetPid $CurrentHp $MaxHp --read $ReadAddresses 2>&1
    } else {
        $result = & $PythonPath $probe $TargetPid $CurrentHp $MaxHp --limit 100 2>&1
    }
    $result | Out-File -LiteralPath $OutputPath -Encoding UTF8
    if ($LASTEXITCODE -ne 0) {
        "Probe exited with code $LASTEXITCODE" | Add-Content -LiteralPath $OutputPath
    }
} catch {
    $_ | Out-File -LiteralPath $OutputPath -Encoding UTF8
}
