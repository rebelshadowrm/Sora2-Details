param([switch]$NoBuild)

$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$exe = Join-Path $root 'src\Sora2.Details.Desktop\bin\Release\net9.0-windows\Sora2.Details.Desktop.exe'
$priorDataDirectory = $env:SORA2_DETAILS_DATA_DIR
$priorResearchReplay = $env:SORA2_DETAILS_RESEARCH_REPLAY
try {
    $env:SORA2_DETAILS_DATA_DIR = Join-Path $root '.research-deps\local-meter-test'
    $env:SORA2_DETAILS_RESEARCH_REPLAY = Join-Path $root 'samples\command-battles.json'

    if (-not $NoBuild) {
        & dotnet build (Join-Path $root 'Sora2.Details.sln') -c Release
        if ($LASTEXITCODE -ne 0) { throw 'Local meter build failed.' }
    }
    if (-not (Test-Path -LiteralPath $exe)) { throw "Meter executable not found: $exe" }
    New-Item -ItemType Directory -Path $env:SORA2_DETAILS_DATA_DIR -Force | Out-Null
    Write-Output "Launching isolated sample meter. Test settings: $env:SORA2_DETAILS_DATA_DIR"
    Write-Output 'Live capture is disabled in this test window. Close it when finished.'
    & $exe
}
finally {
    if ($null -eq $priorDataDirectory) { Remove-Item Env:\SORA2_DETAILS_DATA_DIR -ErrorAction SilentlyContinue }
    else { $env:SORA2_DETAILS_DATA_DIR = $priorDataDirectory }
    if ($null -eq $priorResearchReplay) { Remove-Item Env:\SORA2_DETAILS_RESEARCH_REPLAY -ErrorAction SilentlyContinue }
    else { $env:SORA2_DETAILS_RESEARCH_REPLAY = $priorResearchReplay }
}
