# Export Windows icons and the embedded RGBA texture from the approved PNG.
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$assetDirectory = Join-Path (Split-Path $PSScriptRoot -Parent) 'assets'
$source = [System.Drawing.Bitmap]::FromFile((Join-Path $assetDirectory 'cyrsassistant-logo-turquoise.png'))
$images = [System.Collections.Generic.List[byte[]]]::new()
$sizes = @(16, 24, 32, 48, 64, 128, 256)
try {
    foreach ($size in $sizes) {
        $bitmap = [System.Drawing.Bitmap]::new($size, $size, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
        try {
            $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
            try {
                $graphics.Clear([System.Drawing.Color]::Transparent)
                $graphics.CompositingMode = [System.Drawing.Drawing2D.CompositingMode]::SourceCopy
                $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
                $graphics.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
                $graphics.DrawImage($source, [System.Drawing.Rectangle]::new(0, 0, $size, $size))
            } finally { $graphics.Dispose() }
            $stream = [System.IO.MemoryStream]::new()
            try {
                $bitmap.Save($stream, [System.Drawing.Imaging.ImageFormat]::Png)
                $images.Add($stream.ToArray())
            } finally { $stream.Dispose() }
            if ($size -eq 256) {
                $pixels = [byte[]]::new($size * $size * 4)
                $locked = $bitmap.LockBits([System.Drawing.Rectangle]::new(0, 0, $size, $size), [System.Drawing.Imaging.ImageLockMode]::ReadOnly, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
                try {
                    for ($row = 0; $row -lt $size; $row++) {
                        [System.Runtime.InteropServices.Marshal]::Copy([IntPtr]::Add($locked.Scan0, $row * $locked.Stride), $pixels, $row * $size * 4, $size * 4)
                    }
                } finally { $bitmap.UnlockBits($locked) }
                for ($index = 0; $index -lt $pixels.Length; $index += 4) {
                    $blue = $pixels[$index]
                    $pixels[$index] = $pixels[$index + 2]
                    $pixels[$index + 2] = $blue
                }
                [System.IO.File]::WriteAllBytes((Join-Path $assetDirectory 'cyrsassistant-logo.rgba'), $pixels)
            }
        } finally { $bitmap.Dispose() }
    }
    $output = [System.IO.File]::Create((Join-Path $assetDirectory 'cyrsassistant-logo.ico'))
    $writer = [System.IO.BinaryWriter]::new($output)
    try {
        $writer.Write([uint16]0); $writer.Write([uint16]1); $writer.Write([uint16]$sizes.Count)
        $offset = 6 + 16 * $sizes.Count
        for ($index = 0; $index -lt $sizes.Count; $index++) {
            $dimension = if ($sizes[$index] -eq 256) { 0 } else { $sizes[$index] }
            $writer.Write([byte]$dimension); $writer.Write([byte]$dimension)
            $writer.Write([byte]0); $writer.Write([byte]0)
            $writer.Write([uint16]1); $writer.Write([uint16]32)
            $writer.Write([uint32]$images[$index].Length); $writer.Write([uint32]$offset)
            $offset += $images[$index].Length
        }
        foreach ($bytes in $images) { $writer.Write($bytes) }
    } finally { $writer.Dispose() }
} finally { $source.Dispose() }
Write-Output 'Exported logo: Windows ICO (16-256px) and RGBA texture (256px).'
