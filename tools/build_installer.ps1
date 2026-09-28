param(
    [string]$Version = '0.2.0-preview.1',
    [string]$OutputDir
)

$ErrorActionPreference = 'Stop'
if ($Version -notmatch '^\d+\.\d+\.\d+(-[0-9A-Za-z.-]+)?$') {
    throw 'Use a semantic version such as 0.2.0-preview.1.'
}

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

    & dotnet build (Join-Path $root 'Sora2.Details.sln') -c Release
    if ($LASTEXITCODE -ne 0) { throw 'Release build failed.' }
    & dotnet run --project (Join-Path $root 'tests\Sora2.Details.Checks') -c Release --no-build
    if ($LASTEXITCODE -ne 0) { throw 'Replay and projection checks failed.' }
    & dotnet publish (Join-Path $root 'src\Sora2.Details.Desktop\Sora2.Details.Desktop.csproj') `
        -c Release -r win-x64 --self-contained true `
        -p:PublishSingleFile=true -p:IncludeNativeLibrariesForSelfExtract=true -o $stage
    if ($LASTEXITCODE -ne 0) { throw 'Desktop publish failed.' }

    $tools = Join-Path $stage 'tools'
    $python = Join-Path $stage 'python'
    New-Item -ItemType Directory -Path $tools, $python -Force | Out-Null
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
                       'Stop-Sora2Details.ps1', 'Stop-Sora2Details.cmd', 'README.md', 'RELEASE-NOTES.md')) {
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

    & dotnet vpk pack --packId Sora2.Details --packVersion $Version --packDir $stage `
        --mainExe Sora2.Details.Desktop.exe --packTitle 'Sora 2 Details' `
        --packAuthors 'Sora 2 Details contributors' --runtime win-x64 `
        --channel win-x64-preview --outputDir $output `
        --releaseNotes (Join-Path $root 'RELEASE-NOTES.md')
    if ($LASTEXITCODE -ne 0) { throw 'Velopack packaging failed.' }

    Get-ChildItem -LiteralPath $output -File | Sort-Object Name | Select-Object Name, Length
} finally {
    if (Test-Path -LiteralPath $stageFull) {
        Remove-Item -LiteralPath $stageFull -Recurse -Force
    }
}
