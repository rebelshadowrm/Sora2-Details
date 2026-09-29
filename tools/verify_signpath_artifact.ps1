param(
    [Parameter(Mandatory = $true)] [string]$Version,
    [Parameter(Mandatory = $true)] [string]$ArtifactDirectory
)

$ErrorActionPreference = 'Stop'
$artifactRoot = [IO.Path]::GetFullPath($ArtifactDirectory)
if (-not (Test-Path -LiteralPath $artifactRoot -PathType Container)) {
    throw "SignPath output directory not found: $artifactRoot"
}
$versionMatch = [regex]::Match($Version, '^(?<major>0|[1-9]\d*)\.(?<minor>0|[1-9]\d*)\.(?<patch>0|[1-9]\d*)')
if (-not $versionMatch.Success) { throw "Invalid semantic version: $Version" }
$expectedFileVersion = '{0}.{1}.{2}.0' -f $versionMatch.Groups['major'].Value,
    $versionMatch.Groups['minor'].Value, $versionMatch.Groups['patch'].Value

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
$scratch = Join-Path $env:RUNNER_TEMP ('signpath-verify-' + [Guid]::NewGuid().ToString('N'))
$scratchFull = [IO.Path]::GetFullPath($scratch).TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
$runnerTempFull = [IO.Path]::GetFullPath($env:RUNNER_TEMP).TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
if (-not $scratchFull.StartsWith($runnerTempFull, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Signature verification staging path escaped RUNNER_TEMP.'
}
New-Item -ItemType Directory -Path $scratch | Out-Null
$executables = [Collections.Generic.List[string]]::new()

function Expand-ArchiveExecutables([string]$ArchivePath, [string]$Destination, [int]$Depth = 0) {
    if ($Depth -gt 5) { throw "Nested archive limit exceeded at $ArchivePath" }
    $destinationFull = [IO.Path]::GetFullPath($Destination).TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
    New-Item -ItemType Directory -Path $destinationFull -Force | Out-Null
    $archive = [IO.Compression.ZipFile]::OpenRead($ArchivePath)
    try {
        foreach ($entry in $archive.Entries) {
            if ([string]::IsNullOrEmpty($entry.Name)) { continue }
            $outputPath = [IO.Path]::GetFullPath((Join-Path $destinationFull $entry.FullName))
            if (-not $outputPath.StartsWith($destinationFull, [StringComparison]::OrdinalIgnoreCase)) {
                throw "Archive entry escaped its extraction directory: $($entry.FullName)"
            }
            $extension = [IO.Path]::GetExtension($entry.Name)
            if ($extension -notin @('.exe', '.zip', '.nupkg')) { continue }
            New-Item -ItemType Directory -Path (Split-Path -Parent $outputPath) -Force | Out-Null
            $sourceStream = $entry.Open()
            try {
                $targetStream = [IO.File]::Create($outputPath)
                try { $sourceStream.CopyTo($targetStream) }
                finally { $targetStream.Dispose() }
            } finally { $sourceStream.Dispose() }
            if ($extension -eq '.exe') {
                $executables.Add($outputPath)
            } else {
                Expand-ArchiveExecutables $outputPath (Join-Path $destination ( [IO.Path]::GetFileNameWithoutExtension($entry.Name))) ($Depth + 1)
            }
        }
    } finally { $archive.Dispose() }
}

function Assert-SignPathSignature([string]$Path) {
    $signature = Get-AuthenticodeSignature -LiteralPath $Path
    if ($signature.Status -ne [Management.Automation.SignatureStatus]::Valid) {
        throw "Authenticode signature is missing or invalid for $Path (status: $($signature.Status))."
    }
    $signerName = $signature.SignerCertificate.GetNameInfo(
        [Security.Cryptography.X509Certificates.X509NameType]::SimpleName, $false)
    if ($signerName -notmatch 'SignPath Foundation') {
        throw "Unexpected Authenticode signer '$signerName' for $Path."
    }
}

try {
    $setups = @(Get-ChildItem -LiteralPath $artifactRoot -Filter '*-Setup.exe' -File -Recurse)
    if ($setups.Count -ne 1) { throw "Expected one signed Setup.exe; found $($setups.Count)." }
    Assert-SignPathSignature $setups[0].FullName

    $archives = @(Get-ChildItem -LiteralPath $artifactRoot -File -Recurse | Where-Object {
        $_.Extension -in @('.zip', '.nupkg')
    })
    foreach ($archive in $archives) {
        Expand-ArchiveExecutables $archive.FullName (Join-Path $scratch ([Guid]::NewGuid().ToString('N')))
    }

    foreach ($name in @('Sora2.Details.Desktop.exe', 'Sora2.Details.CaptureHost.exe')) {
        $matches = @($executables | Where-Object { [IO.Path]::GetFileName($_) -ieq $name })
        if ($matches.Count -lt 1) { throw "No packaged copy of $name was found for signature verification." }
        foreach ($path in $matches) {
            Assert-SignPathSignature $path
            $versionInfo = [Diagnostics.FileVersionInfo]::GetVersionInfo($path)
            if ($versionInfo.ProductName -ne 'Sora 2 Details' -or
                $versionInfo.FileVersion -ne $expectedFileVersion -or
                $versionInfo.ProductVersion -ne $Version) {
                throw "Unexpected version metadata in signed ${name}: product '$($versionInfo.ProductName)', " +
                    "file '$($versionInfo.FileVersion)', product version '$($versionInfo.ProductVersion)'."
            }
        }
    }
    Write-Output "Verified SignPath Authenticode signatures and $Version metadata for the installer and project executables."
} finally {
    if (Test-Path -LiteralPath $scratchFull.TrimEnd([IO.Path]::DirectorySeparatorChar)) {
        Remove-Item -LiteralPath $scratchFull.TrimEnd([IO.Path]::DirectorySeparatorChar) -Recurse -Force
    }
}
