param([string]$Version = '0.1.0-preview.1')

$ErrorActionPreference = 'Stop'
if ($Version -notmatch '^[0-9A-Za-z][0-9A-Za-z._-]*$') {
    throw 'Version may contain only letters, digits, dots, underscores, and hyphens.'
}
$root = Split-Path $PSScriptRoot -Parent
$releaseRoot = Join-Path $root 'releases'
New-Item -ItemType Directory -Path $releaseRoot -Force | Out-Null
$stage = Join-Path $releaseRoot ('.stage-' + [Guid]::NewGuid().ToString('N'))
$stageFull = [IO.Path]::GetFullPath($stage)
$releaseFull = [IO.Path]::GetFullPath($releaseRoot).TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
if (-not $stageFull.StartsWith($releaseFull, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Release staging path escaped the release directory.'
}
$app = Join-Path $stage 'app'
$tools = Join-Path $stage 'tools'
$docs = Join-Path $stage 'docs'
$archive = Join-Path $releaseRoot "Sora2-Details-$Version-win-x64.zip"

try {
    New-Item -ItemType Directory -Path $app, $tools, $docs -Force | Out-Null
    & dotnet build (Join-Path $root 'Sora2.Details.sln') -c Release
    if ($LASTEXITCODE -ne 0) { throw 'Release build failed.' }
    & dotnet run --project (Join-Path $root 'tests\Sora2.Details.Checks') -c Release --no-build
    if ($LASTEXITCODE -ne 0) { throw 'Replay and projection checks failed.' }
    & dotnet publish (Join-Path $root 'src\Sora2.Details.Desktop\Sora2.Details.Desktop.csproj') `
        -c Release -r win-x64 --self-contained true `
        -p:PublishSingleFile=true -p:IncludeNativeLibrariesForSelfExtract=true -o $app
    if ($LASTEXITCODE -ne 0) { throw 'Desktop publish failed.' }

    Get-ChildItem -LiteralPath (Join-Path $root 'tools') -File |
        Where-Object { $_.Extension -in '.py', '.ps1' } |
        ForEach-Object { Copy-Item -LiteralPath $_.FullName -Destination $tools }
    Get-ChildItem -LiteralPath (Join-Path $root 'docs') -File |
        ForEach-Object { Copy-Item -LiteralPath $_.FullName -Destination $docs }
    foreach ($name in @('Start-Sora2Details.ps1', 'Start-Sora2Details.cmd',
                       'Stop-Sora2Details.ps1', 'Stop-Sora2Details.cmd',
                       'README.md', 'RELEASE-NOTES.md')) {
        Copy-Item -LiteralPath (Join-Path $root $name) -Destination $stage
    }
    $commit = (& git -C $root rev-parse --short HEAD 2>$null)
    if ($LASTEXITCODE -ne 0) { $commit = $null }
    @{
        version = $Version
        platform = 'win-x64'
        desktop = 'self-contained .NET 9 WPF'
        liveCapture = 'partial, read-only; requires 64-bit Python 3.11+ and the validated game build'
        supportedGameSha256 = 'D8B2911D1576216BDC22D070550E4F531E105DE7ED2981885849669F4ACF8AAF'
        commit = $commit
    } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $stage 'release.json') -Encoding UTF8

    Compress-Archive -Path (Join-Path $stage '*') -DestinationPath $archive -CompressionLevel Optimal -Force
    $hash = (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant()
    Set-Content -LiteralPath "$archive.sha256" -Value "$hash  $(Split-Path $archive -Leaf)" -Encoding ASCII
    Write-Output "Release: $archive"
    Write-Output "SHA-256: $hash"
} finally {
    if (Test-Path -LiteralPath $stageFull) {
        Remove-Item -LiteralPath $stageFull -Recurse -Force
    }
}
