param(
    [ValidateRange(2, 12)][int]$Hours = 12,
    [switch]$MeterOnly,
    [switch]$CaptureOnly,
    [string]$GameDirectory,
    [string]$PythonPath,
    [string]$DataDirectory
)

$ErrorActionPreference = 'Stop'
$DataDirectory = if ($DataDirectory) { [IO.Path]::GetFullPath($DataDirectory) }
    elseif ($env:SORA2_DETAILS_DATA_DIR) { [IO.Path]::GetFullPath($env:SORA2_DETAILS_DATA_DIR) }
    else { Join-Path $env:LOCALAPPDATA 'Sora2 Details' }
$env:SORA2_DETAILS_DATA_DIR = $DataDirectory

function Quote-WindowsArgument([string]$Value) {
    if ($Value.Length -gt 0 -and $Value -notmatch '[\s"]') { return $Value }
    $quoted = [System.Text.StringBuilder]::new()
    $null = $quoted.Append('"')
    $backslashes = 0
    foreach ($character in $Value.ToCharArray()) {
        if ($character -eq [char]92) { $backslashes++; continue }
        if ($character -eq [char]34) {
            $null = $quoted.Append(([string][char]92) * ($backslashes * 2 + 1)).Append('"')
            $backslashes = 0
            continue
        }
        $null = $quoted.Append(([string][char]92) * $backslashes).Append($character)
        $backslashes = 0
    }
    $null = $quoted.Append(([string][char]92) * ($backslashes * 2)).Append('"')
    return $quoted.ToString()
}

function Start-DesktopApplication([string]$Executable, [string]$WorkingDirectory, [string]$Arguments) {
    $startInfo = [Diagnostics.ProcessStartInfo]::new()
    $startInfo.FileName = $Executable
    $startInfo.WorkingDirectory = $WorkingDirectory
    $startInfo.Arguments = $Arguments
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $process = [Diagnostics.Process]::Start($startInfo)
    if ($null -eq $process) { throw 'Could not start Sora 2 Details.' }
    $process.Dispose()
}

$root = $PSScriptRoot
$desktopExe = Join-Path $root 'Sora2.Details.Desktop.exe'
if (-not (Test-Path -LiteralPath $desktopExe)) {
    $desktopExe = Join-Path $root 'app\Sora2.Details.Desktop.exe'
}
if (-not (Test-Path -LiteralPath $desktopExe)) {
    $desktopExe = Join-Path $root 'src\Sora2.Details.Desktop\bin\Release\net9.0-windows\Sora2.Details.Desktop.exe'
}
if (-not (Test-Path -LiteralPath $desktopExe)) {
    throw 'Desktop app is missing. Run tools\build_release.ps1 or build the solution in Release mode.'
}

$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$isAdministrator = [Security.Principal.WindowsPrincipal]::new($identity).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdministrator) {
    if ($CaptureOnly) {
        throw 'Capture-only mode is an app child operation. Start Sora 2 Details normally so it can request startup approval once.'
    }
}

if (-not $CaptureOnly) {
    if (Get-Process -Name 'Sora2.Details.Desktop' -ErrorAction SilentlyContinue) {
        Write-Output 'Sora 2 Details is already running. Use its tray and capture controls.'
        exit 0
    }
    $appArguments = @('--data-dir', $DataDirectory, '--capture-hours', [string]$Hours)
    if ($MeterOnly) { $appArguments += '--meter-only' }
    if ($GameDirectory) { $appArguments += @('--game-directory', $GameDirectory) }
    if ($PythonPath) { $appArguments += @('--python-path', $PythonPath) }
    $argumentLine = ($appArguments | ForEach-Object { Quote-WindowsArgument ([string]$_) }) -join ' '
    Start-DesktopApplication $desktopExe $root $argumentLine
    if ((Get-Process -Name sora_2nd -ErrorAction SilentlyContinue).Count -eq 0 -and -not $MeterOnly) {
        Write-Output 'Game is not running. Sora 2 Details will wait in the tray and notify you when Trails starts.'
    } else {
        Write-Output 'Opened Sora 2 Details. Startup approval is requested before the main meter becomes interactive.'
    }
    exit 0
}

if (-not $isAdministrator) {
    throw 'Capture-only mode requires the elevated Sora 2 Details process.'
}
$game = @(Get-Process -Name sora_2nd -ErrorAction SilentlyContinue)
if ($game.Count -eq 0) { throw 'Start the game before beginning live capture.' }
if ($game.Count -ne 1) { throw "Expected one sora_2nd process; found $($game.Count)." }

if (-not $GameDirectory) {
    try { $GameDirectory = Split-Path $game[0].MainModule.FileName -Parent } catch { }
    if (-not $GameDirectory) {
        $savedPath = Join-Path $env:LOCALAPPDATA 'Sora2 Details\game-directory.txt'
        if (Test-Path -LiteralPath $savedPath) {
            try {
                $savedDirectory = (Get-Content -LiteralPath $savedPath -Raw).Trim()
                if (Test-Path -LiteralPath (Join-Path $savedDirectory 'sora_2nd.exe')) {
                    $GameDirectory = $savedDirectory
                }
            } catch { }
        }
    }
    if (-not $GameDirectory) {
        $originalInstall = 'C:\Games\Trails in the Sky 2nd Chapter'
        if (Test-Path -LiteralPath (Join-Path $originalInstall 'sora_2nd.exe')) {
            $GameDirectory = $originalInstall
        } else {
            throw 'Could not locate sora_2nd.exe. Click Capture in the meter to choose it, or pass -GameDirectory.'
        }
    }
}

if (-not $PythonPath) {
    $candidates = @((Join-Path $root 'python\python.exe'), 'C:\Python313\python.exe') + @(
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
