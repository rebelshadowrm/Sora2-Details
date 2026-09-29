# Reproducible code-drawn meter icon; no game artwork or external image dependencies.
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$output = Join-Path $PSScriptRoot '..\src\Sora2.Details.Desktop\assets\sora2-details.ico'
$images = @()
foreach ($size in @(16, 32, 48, 256)) {
    $bitmap = New-Object Drawing.Bitmap($size, $size)
    $graphics = [Drawing.Graphics]::FromImage($bitmap)
    $graphics.Clear([Drawing.Color]::FromArgb(255, 22, 29, 43))
    $brush = New-Object Drawing.SolidBrush([Drawing.Color]::FromArgb(255, 79, 195, 247))
    foreach ($bar in @(@(3, 3, 10, 2), @(3, 7, 7, 2), @(3, 11, 4, 2))) {
        $graphics.FillRectangle($brush, [single]($bar[0]*$size/16), [single]($bar[1]*$size/16),
            [single]($bar[2]*$size/16), [single]($bar[3]*$size/16))
    }
    $stream = New-Object IO.MemoryStream
    $bitmap.Save($stream, [Drawing.Imaging.ImageFormat]::Png)
    $images += ,@($size, $stream.ToArray())
    $stream.Dispose(); $brush.Dispose(); $graphics.Dispose(); $bitmap.Dispose()
}
$file = [IO.File]::Create($output)
$writer = New-Object IO.BinaryWriter($file)
try {
    $writer.Write([uint16]0); $writer.Write([uint16]1); $writer.Write([uint16]$images.Count)
    $offset = 6 + 16 * $images.Count
    foreach ($entry in $images) {
        $dimension = if ($entry[0] -eq 256) { 0 } else { $entry[0] }
        $writer.Write([byte]$dimension); $writer.Write([byte]$dimension)
        $writer.Write([uint16]0); $writer.Write([uint16]1); $writer.Write([uint16]32)
        $writer.Write([uint32]$entry[1].Length); $writer.Write([uint32]$offset)
        $offset += $entry[1].Length
    }
    foreach ($entry in $images) { $writer.Write([byte[]]$entry[1]) }
} finally { $writer.Dispose(); $file.Dispose() }
