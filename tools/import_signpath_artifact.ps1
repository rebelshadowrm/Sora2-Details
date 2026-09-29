param(
    [Parameter(Mandatory = $true)] [string]$Version,
    [Parameter(Mandatory = $true)] [string]$SignedDirectory,
    [string]$ReleaseDirectory = (Join-Path $PSScriptRoot '..\releases\velopack-preview')
)

$ErrorActionPreference = 'Stop'
$signedRoot = [IO.Path]::GetFullPath($SignedDirectory)
$releaseRoot = [IO.Path]::GetFullPath($ReleaseDirectory)
if (-not (Test-Path -LiteralPath $signedRoot -PathType Container)) {
    throw "Signed artifact directory not found: $signedRoot"
}
if (-not (Test-Path -LiteralPath $releaseRoot -PathType Container)) {
    throw "Release directory not found: $releaseRoot"
}

$files = @(
    'Sora2.Details-win-x64-preview-Setup.exe',
    'Sora2.Details-win-x64-preview-Portable.zip',
    "Sora2.Details-$Version-win-x64-preview-full.nupkg"
)
foreach ($name in $files) {
    $matches = @(Get-ChildItem -LiteralPath $signedRoot -Filter $name -File -Recurse)
    if ($matches.Count -ne 1) {
        throw "Expected exactly one signed $name under $signedRoot; found $($matches.Count)."
    }
    Copy-Item -LiteralPath $matches[0].FullName -Destination (Join-Path $releaseRoot $name) -Force
}

$versionMatch = [regex]::Match($Version, '^(?<major>0|[1-9]\d*)\.(?<minor>0|[1-9]\d*)\.(?<patch>0|[1-9]\d*)')
if (-not $versionMatch.Success) { throw "Invalid semantic version: $Version" }
$expectedFileVersion = '{0}.{1}.{2}.0' -f $versionMatch.Groups['major'].Value,
    $versionMatch.Groups['minor'].Value, $versionMatch.Groups['patch'].Value
$fullName = "Sora2.Details-$Version-win-x64-preview-full.nupkg"
$fullPath = Join-Path $releaseRoot $fullName
$hashes = @{
    SHA1 = (Get-FileHash -LiteralPath $fullPath -Algorithm SHA1).Hash.ToUpperInvariant()
    SHA256 = (Get-FileHash -LiteralPath $fullPath -Algorithm SHA256).Hash.ToUpperInvariant()
    Size = (Get-Item -LiteralPath $fullPath).Length
}

$feedPath = Join-Path $releaseRoot 'releases.win-x64-preview.json'
$feed = Get-Content -LiteralPath $feedPath -Raw | ConvertFrom-Json
$assets = @($feed.Assets | Where-Object { $_.FileName -eq $fullName -and $_.Version -eq $Version -and $_.Type -eq 'Full' })
if ($assets.Count -ne 1) {
    throw "Expected exactly one full-package feed entry for $Version; found $($assets.Count)."
}
$assets[0].SHA1 = $hashes.SHA1
$assets[0].SHA256 = $hashes.SHA256
$assets[0].Size = $hashes.Size
[IO.File]::WriteAllText($feedPath, ($feed | ConvertTo-Json -Depth 100), [Text.UTF8Encoding]::new($false))

$releasesPath = Join-Path $releaseRoot 'RELEASES-win-x64-preview'
$lines = [IO.File]::ReadAllLines($releasesPath)
$updatedLines = 0
for ($index = 0; $index -lt $lines.Length; $index++) {
    $columns = $lines[$index] -split '\s+', 3
    if ($columns.Count -eq 3 -and $columns[1] -eq $fullName) {
        $lines[$index] = '{0} {1} {2}' -f $hashes.SHA1, $fullName, $hashes.Size
        $updatedLines++
    }
}
if ($updatedLines -ne 1) {
    throw "Expected exactly one RELEASES entry for $fullName; found $updatedLines."
}
[IO.File]::WriteAllLines($releasesPath, $lines, [Text.UTF8Encoding]::new($false))

Write-Output "Imported signed release files for $Version and refreshed package hashes ($expectedFileVersion)."
