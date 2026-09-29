param(
    [Parameter(Mandatory = $true)] [string]$Version,
    [string]$ReleaseDirectory = (Join-Path $PSScriptRoot '..\releases\velopack-preview'),
    [Parameter(Mandatory = $true)] [string]$DestinationDirectory
)

$ErrorActionPreference = 'Stop'
if ($Version -notmatch '^(?<major>0|[1-9]\d*)\.(?<minor>0|[1-9]\d*)\.(?<patch>0|[1-9]\d*)(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$') {
    throw "Invalid semantic version: $Version"
}

$source = [IO.Path]::GetFullPath($ReleaseDirectory)
$destination = [IO.Path]::GetFullPath($DestinationDirectory)
if (-not (Test-Path -LiteralPath $source -PathType Container)) {
    throw "Release directory not found: $source"
}
if (Test-Path -LiteralPath $destination) {
    throw "SignPath artifact destination already exists: $destination"
}

$files = @(
    'Sora2.Details-win-x64-preview-Setup.exe',
    'Sora2.Details-win-x64-preview-Portable.zip',
    "Sora2.Details-$Version-win-x64-preview-full.nupkg"
)
New-Item -ItemType Directory -Path $destination | Out-Null
foreach ($name in $files) {
    $sourcePath = Join-Path $source $name
    if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) {
        throw "Expected release artifact is missing: $sourcePath"
    }
    Copy-Item -LiteralPath $sourcePath -Destination $destination
}

Get-ChildItem -LiteralPath $destination -File | Sort-Object Name | Select-Object Name, Length
