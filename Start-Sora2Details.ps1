param(
    [ValidateRange(2, 12)][int]$Hours = 12,
    [switch]$MeterOnly,
    [string]$GameDirectory = 'C:\Games\Trails in the Sky 2nd Chapter',
    [string]$PythonPath
)

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$desktopExe = Join-Path $root 'app\Sora2.Details.Desktop.exe'
if (-not (Test-Path -LiteralPath $desktopExe)) {
    $desktopExe = Join-Path $root 'src\Sora2.Details.Desktop\bin\Release\net9.0-windows\Sora2.Details.Desktop.exe'
}
if (-not (Test-Path -LiteralPath $desktopExe)) {
    throw 'Desktop app is missing. Run tools\build_release.ps1 or build the solution in Release mode.'
}

$game = @(Get-Process -Name sora_2nd -ErrorAction SilentlyContinue)
if ($MeterOnly -or $game.Count -eq 0) {
    if (-not (Get-Process -Name 'Sora2.Details.Desktop' -ErrorAction SilentlyContinue)) {
        Start-Process -FilePath $desktopExe -WorkingDirectory $root | Out-Null
    }
    if ($game.Count -eq 0 -and -not $MeterOnly) {
        Write-Output 'Game is not running. Opened the meter with saved encounters; run this launcher again after starting the game for live capture.'
    } else {
        Write-Output 'Meter opened without live capture.'
    }
    exit 0
}
if ($game.Count -ne 1) { throw "Expected one sora_2nd process; found $($game.Count)." }

if (-not $PythonPath) {
    $candidates = @('C:\Python313\python.exe') + @(
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
if (-not $PythonPath) {
    throw 'Live capture needs 64-bit Python 3.11 or newer. Install Python or pass -PythonPath. Use -MeterOnly to open saved fights.'
}
$versionCheck = & $PythonPath -c 'import sys; print(int(sys.version_info >= (3, 11) and sys.maxsize > 2**32))'
if ($LASTEXITCODE -ne 0 -or $versionCheck -ne '1') {
    throw "Live capture needs 64-bit Python 3.11 or newer: $PythonPath"
}

& (Join-Path $root 'tools\start_session_logger.ps1') -Hours $Hours `
    -PythonPath $PythonPath -GameDirectory $GameDirectory
