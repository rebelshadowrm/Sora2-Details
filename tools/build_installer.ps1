param(
    [string]$Version = '0.2.0-preview.1',
    [string]$OutputDir,
    [string]$SignParams = $env:VPK_SIGN_PARAMS,
    [switch]$RequireSigning,
    [switch]$DisableDelta
)

$ErrorActionPreference = 'Stop'
if ($RequireSigning -and [string]::IsNullOrWhiteSpace($SignParams)) {
    throw 'RequireSigning needs SignParams (or VPK_SIGN_PARAMS) for the configured signing identity.'
}
if ($Version -notmatch '^(?<major>0|[1-9]\d*)\.(?<minor>0|[1-9]\d*)\.(?<patch>0|[1-9]\d*)(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$') {
    throw 'Use a semantic version such as 0.2.0-preview.1.'
}
$fileVersion = '{0}.{1}.{2}.0' -f $Matches.major, $Matches.minor, $Matches.patch
$versionMetadata = @(
    "-p:Version=$Version",
    "-p:AssemblyVersion=$fileVersion",
    "-p:FileVersion=$fileVersion",
    "-p:InformationalVersion=$Version",
    '-p:IncludeSourceRevisionInInformationalVersion=false'
)

$root = Split-Path $PSScriptRoot -Parent
$releaseRoot = Join-Path $root 'releases'
$output = if ($OutputDir) { [IO.Path]::GetFullPath($OutputDir) }
    else { Join-Path $releaseRoot 'velopack-preview' }
$downloadDir = Join-Path $root '.research-deps\downloads'
$pythonZip = Join-Path $downloadDir 'python-3.13.15-embed-amd64.zip'
$pythonHash = 'D1F04D990AEE1253D8569E8E5104E30FA9F5FA830899F14843448872D936A2CF'
$stage = Join-Path $releaseRoot ('.installer-stage-' + [Guid]::NewGuid().ToString('N'))
$stageFull = [IO.Path]::GetFullPath($stage)
$releaseFull = [IO.Path]::GetFullPath($releaseRoot).TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
if (-not $stageFull.StartsWith($releaseFull, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Installer staging path escaped the release directory.'
}

try {
    New-Item -ItemType Directory -Path $stage, $output, $downloadDir -Force | Out-Null
    if (-not (Test-Path -LiteralPath $pythonZip)) {
        Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.13.15/python-3.13.15-embed-amd64.zip' -OutFile $pythonZip
    }
    if ((Get-FileHash -LiteralPath $pythonZip -Algorithm SHA256).Hash -ne $pythonHash) {
        throw 'Bundled Python download failed its pinned SHA-256 check.'
    }

    & dotnet build (Join-Path $root 'Sora2.Details.sln') -c Release @versionMetadata
    if ($LASTEXITCODE -ne 0) { throw 'Release build failed.' }
    & dotnet run --project (Join-Path $root 'tests\Sora2.Details.Checks') -c Release --no-build
    if ($LASTEXITCODE -ne 0) { throw 'Replay and projection checks failed.' }
    & dotnet publish (Join-Path $root 'src\Sora2.Details.Desktop\Sora2.Details.Desktop.csproj') `
        -c Release -r win-x64 --self-contained true `
        -p:PublishSingleFile=true -p:IncludeNativeLibrariesForSelfExtract=true @versionMetadata -o $stage
    if ($LASTEXITCODE -ne 0) { throw 'Desktop publish failed.' }
    & dotnet publish (Join-Path $root 'src\Sora2.Details.CaptureHost\Sora2.Details.CaptureHost.csproj') `
        -c Release -r win-x64 --self-contained true -p:PublishTrimmed=true `
        -p:PublishSingleFile=true -p:IncludeNativeLibrariesForSelfExtract=true @versionMetadata -o $stage
    if ($LASTEXITCODE -ne 0) { throw 'Capture host publish failed.' }

    foreach ($executableName in @('Sora2.Details.Desktop.exe', 'Sora2.Details.CaptureHost.exe')) {
        $executablePath = Join-Path $stage $executableName
        $versionInfo = [Diagnostics.FileVersionInfo]::GetVersionInfo($executablePath)
        if ($versionInfo.ProductName -ne 'Sora 2 Details' -or
            $versionInfo.FileVersion -ne $fileVersion -or
            $versionInfo.ProductVersion -ne $Version) {
            throw "Unexpected product/file/informational version metadata in $executableName. " +
                "Expected product 'Sora 2 Details', file $fileVersion, product version $Version; " +
                "found product '$($versionInfo.ProductName)', file '$($versionInfo.FileVersion)', " +
                "product version '$($versionInfo.ProductVersion)'."
        }
    }

    $tools = Join-Path $stage 'tools'
    $python = Join-Path $stage 'python'
    $assets = Join-Path $stage 'assets'
    New-Item -ItemType Directory -Path $tools, $python, $assets -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $root 'src\Sora2.Details.Desktop\assets\sora2-details.ico') `
        -Destination $assets
    # Only the session launcher and its direct Python dependencies belong in an installed build.
    # The source checkout and the legacy ZIP builder retain the research tools.
    $runtimeTools = @(
        'start_session_logger.ps1', 'start_live_meter.ps1', 'start_probe_session.ps1',
        'stop_live_meter.ps1', 'elevated_probe_session.py', 'lifecycle_probe.py',
        'live_capture_bridge.py', 'status_name_index.py', 'name_table_index.py',
        'enemy_ai_skill_index.py', 'skill_table_index.py', 'match_enemy_status.py'
    )
    foreach ($name in $runtimeTools) {
        Copy-Item -LiteralPath (Join-Path $root "tools\$name") -Destination $tools
    }
    foreach ($name in @('Start-Sora2Details.ps1', 'Start-Sora2Details.cmd',
                       'Stop-Sora2Details.ps1', 'Stop-Sora2Details.cmd', 'README.md',
                       'RELEASE-NOTES.md', 'CODE-SIGNING-POLICY.md', 'LICENSE')) {
        Copy-Item -LiteralPath (Join-Path $root $name) -Destination $stage
    }
    Expand-Archive -LiteralPath $pythonZip -DestinationPath $python
    $pth = Join-Path $python 'python313._pth'
    if (-not (Test-Path -LiteralPath $pth)) { throw 'Embedded Python path file was not found.' }
    Add-Content -LiteralPath $pth -Value '..\tools' -Encoding ASCII
    foreach ($script in @('elevated_probe_session.py', 'live_capture_bridge.py')) {
        & (Join-Path $python 'python.exe') -B (Join-Path $tools $script) --help | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "Embedded Python could not run $script." }
    }
    & (Join-Path $python 'python.exe') -B (Join-Path $root 'tools\test_elevated_probe_session.py')
    if ($LASTEXITCODE -ne 0) { throw 'Packaged probe readiness checks failed.' }
    foreach ($check in @(
        @{ Arguments = '--check-package'; ExitCode = 0 },
        @{ Arguments = '0 30 C:\Data'; ExitCode = 3 },
        @{ Arguments = '1 1501 C:\Data'; ExitCode = 3 },
        @{ Arguments = '1 30 relative-path'; ExitCode = 3 },
        @{ Arguments = '--arbitrary-command'; ExitCode = 3 }
    )) {
        $hostCheck = Start-Process -FilePath (Join-Path $stage 'Sora2.Details.CaptureHost.exe') `
            -ArgumentList $check.Arguments -WindowStyle Hidden -Wait -PassThru
        if ($hostCheck.ExitCode -ne $check.ExitCode) {
            throw "Packaged capture host check failed: $($check.Arguments) (exit $($hostCheck.ExitCode))."
        }
    }

    $signArguments = @()
    if (-not [string]::IsNullOrWhiteSpace($SignParams)) {
        $signArguments = @('--signParams', $SignParams)
    } else {
        Write-Warning 'Unsigned preview: Windows may display Unknown publisher and SmartScreen warnings.'
    }
    $deltaArguments = if ($DisableDelta) { @('--delta', 'None') } else { @() }
    & dotnet vpk pack --packId Sora2.Details --packVersion $Version --packDir $stage `
        --mainExe Sora2.Details.Desktop.exe --packTitle 'Sora 2 Details' `
        --packAuthors 'Sora 2 Details contributors' --runtime win-x64 `
        --channel win-x64-preview --outputDir $output `
        --icon (Join-Path $root 'src\Sora2.Details.Desktop\assets\sora2-details.ico') `
        --releaseNotes (Join-Path $root 'RELEASE-NOTES.md') @signArguments @deltaArguments
    if ($LASTEXITCODE -ne 0) { throw 'Velopack packaging failed.' }

    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $portablePath = Join-Path $output 'Sora2.Details-win-x64-preview-Portable.zip'
    $portableForUninstallCheck = [IO.Compression.ZipFile]::OpenRead($portablePath)
    try {
        $updateEntry = $portableForUninstallCheck.GetEntry('Update.exe')
        if ($null -eq $updateEntry) { throw 'Portable package has no Velopack Update.exe.' }
        $updatePath = Join-Path $stage 'verify-Update.exe'
        [IO.Compression.ZipFileExtensions]::ExtractToFile($updateEntry, $updatePath, $true)
        $updateHelp = (& $updatePath --help 2>&1 | Out-String)
        if ($LASTEXITCODE -ne 0 -or $updateHelp -notmatch 'Update\.exe uninstall') {
            throw 'Packaged Velopack updater does not expose its Windows uninstall command.'
        }
    } finally { $portableForUninstallCheck.Dispose() }

    if ($RequireSigning) {
        # Inspect delivered bytes: Velopack may sign a working copy of packDir.
        $portable = [IO.Compression.ZipFile]::OpenRead(
            $portablePath)
        $signedFiles = @((Join-Path $output 'Sora2.Details-win-x64-preview-Setup.exe'))
        try {
            foreach ($entryName in @('current/Sora2.Details.Desktop.exe',
                'current/Sora2.Details.CaptureHost.exe', 'Update.exe')) {
                $entry = $portable.GetEntry($entryName)
                if ($null -eq $entry) { throw "Missing packaged executable: $entryName" }
                $verifyPath = Join-Path $stage ('verify-' + [IO.Path]::GetFileName($entryName))
                [IO.Compression.ZipFileExtensions]::ExtractToFile($entry, $verifyPath, $true)
                $signedFiles += $verifyPath
            }
        } finally { $portable.Dispose() }
        foreach ($signedFile in $signedFiles) {
            if ((Get-AuthenticodeSignature -LiteralPath $signedFile).Status -ne 'Valid') {
                throw "Missing or invalid Authenticode signature: $signedFile"
            }
        }
    }

    Get-ChildItem -LiteralPath $output -File | Sort-Object Name | Select-Object Name, Length
} finally {
    if (Test-Path -LiteralPath $stageFull) {
        Remove-Item -LiteralPath $stageFull -Recurse -Force
    }
}
