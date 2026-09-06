param([Parameter(Mandatory=$true)][string]$Directory)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$mediaDirectory = (Resolve-Path -LiteralPath $Directory).Path
Get-ChildItem -LiteralPath $mediaDirectory -File | Where-Object { $_.Extension -in '.emf', '.wmf' } | ForEach-Object {
    $metafile = $null
    $bitmap = $null
    $graphics = $null
    try {
        $metafile = [System.Drawing.Image]::FromFile($_.FullName)
        # Keep formula previews sharp, with a bounded raster size.
        $factor = [Math]::Min(3.0, 6000.0 / [Math]::Max($metafile.Width, $metafile.Height))
        $bitmap = New-Object System.Drawing.Bitmap ([int][Math]::Ceiling($metafile.Width*$factor)),([int][Math]::Ceiling($metafile.Height*$factor))
        $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
        $graphics.Clear([System.Drawing.Color]::White)
        $graphics.DrawImage($metafile, 0, 0, $bitmap.Width, $bitmap.Height)
        $bitmap.Save($_.FullName + '.png', [System.Drawing.Imaging.ImageFormat]::Png)
    } finally {
        if ($graphics) { $graphics.Dispose() }
        if ($bitmap) { $bitmap.Dispose() }
        if ($metafile) { $metafile.Dispose() }
    }
}
