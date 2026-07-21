Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Add-Type -AssemblyName System.Drawing

$flutterRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$brandingRoot = Join-Path $flutterRoot 'assets\branding'
$legacyRoot = Join-Path $brandingRoot 'legacy_launcher'
New-Item -ItemType Directory -Force $legacyRoot | Out-Null

$legacyAndroid = Join-Path $legacyRoot 'android_flutter_launcher.png'
$androidSource = Join-Path $flutterRoot 'android\app\src\main\res\mipmap-xxxhdpi\ic_launcher.png'
if (-not (Test-Path $legacyAndroid)) {
    Copy-Item -LiteralPath $androidSource -Destination $legacyAndroid
}

$legacyIos = Join-Path $legacyRoot 'ios_flutter_launcher.png'
$iosSource = Join-Path $flutterRoot 'ios\Runner\Assets.xcassets\AppIcon.appiconset\Icon-App-1024x1024@1x.png'
if (-not (Test-Path $legacyIos)) {
    Copy-Item -LiteralPath $iosSource -Destination $legacyIos
}

$legacyWeb = Join-Path $legacyRoot 'web_flutter_launcher.png'
$webSource = Join-Path $flutterRoot 'web\icons\Icon-512.png'
if (-not (Test-Path $legacyWeb)) {
    Copy-Item -LiteralPath $webSource -Destination $legacyWeb
}

function New-SignSyncIcon {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][int]$Size
    )

    $directory = Split-Path -Parent $Path
    New-Item -ItemType Directory -Force $directory | Out-Null

    $bitmap = [System.Drawing.Bitmap]::new($Size, $Size)
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    try {
        $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
        $graphics.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
        $graphics.Clear([System.Drawing.ColorTranslator]::FromHtml('#13263F'))

        $scale = $Size / 512.0
        $connection = [System.Drawing.Drawing2D.GraphicsPath]::new()
        try {
            $connection.StartFigure()
            $connection.AddBezier(
                [System.Drawing.PointF]::new(144 * $scale, 160 * $scale),
                [System.Drawing.PointF]::new(208 * $scale, 96 * $scale),
                [System.Drawing.PointF]::new(336 * $scale, 112 * $scale),
                [System.Drawing.PointF]::new(360 * $scale, 176 * $scale)
            )
            $connection.AddBezier(
                [System.Drawing.PointF]::new(360 * $scale, 176 * $scale),
                [System.Drawing.PointF]::new(384 * $scale, 240 * $scale),
                [System.Drawing.PointF]::new(288 * $scale, 248 * $scale),
                [System.Drawing.PointF]::new(232 * $scale, 272 * $scale)
            )
            $connection.AddBezier(
                [System.Drawing.PointF]::new(232 * $scale, 272 * $scale),
                [System.Drawing.PointF]::new(160 * $scale, 304 * $scale),
                [System.Drawing.PointF]::new(136 * $scale, 360 * $scale),
                [System.Drawing.PointF]::new(184 * $scale, 400 * $scale)
            )
            $connection.AddBezier(
                [System.Drawing.PointF]::new(184 * $scale, 400 * $scale),
                [System.Drawing.PointF]::new(232 * $scale, 440 * $scale),
                [System.Drawing.PointF]::new(336 * $scale, 408 * $scale),
                [System.Drawing.PointF]::new(368 * $scale, 352 * $scale)
            )
            $connectionPen = [System.Drawing.Pen]::new(
                [System.Drawing.ColorTranslator]::FromHtml('#59D4CC'),
                [Math]::Max(2, 48 * $scale)
            )
            try {
                $connectionPen.StartCap = [System.Drawing.Drawing2D.LineCap]::Round
                $connectionPen.EndCap = [System.Drawing.Drawing2D.LineCap]::Round
                $connectionPen.LineJoin = [System.Drawing.Drawing2D.LineJoin]::Round
                $graphics.DrawPath($connectionPen, $connection)
            }
            finally {
                $connectionPen.Dispose()
            }
        }
        finally {
            $connection.Dispose()
        }

        $textPen = [System.Drawing.Pen]::new(
            [System.Drawing.Color]::White,
            [Math]::Max(1.5, 20 * $scale)
        )
        try {
            $textPen.StartCap = [System.Drawing.Drawing2D.LineCap]::Round
            $textPen.EndCap = [System.Drawing.Drawing2D.LineCap]::Round
            $graphics.DrawLine($textPen, 280 * $scale, 312 * $scale, 368 * $scale, 312 * $scale)
            $graphics.DrawLine($textPen, 296 * $scale, 352 * $scale, 344 * $scale, 352 * $scale)
        }
        finally {
            $textPen.Dispose()
        }

        $bitmap.Save($Path, [System.Drawing.Imaging.ImageFormat]::Png)
    }
    finally {
        $graphics.Dispose()
        $bitmap.Dispose()
    }
}

$androidIcons = @{
    'android\app\src\main\res\mipmap-mdpi\ic_launcher.png' = 48
    'android\app\src\main\res\mipmap-hdpi\ic_launcher.png' = 72
    'android\app\src\main\res\mipmap-xhdpi\ic_launcher.png' = 96
    'android\app\src\main\res\mipmap-xxhdpi\ic_launcher.png' = 144
    'android\app\src\main\res\mipmap-xxxhdpi\ic_launcher.png' = 192
}

$iosIcons = @{
    'ios\Runner\Assets.xcassets\AppIcon.appiconset\Icon-App-20x20@1x.png' = 20
    'ios\Runner\Assets.xcassets\AppIcon.appiconset\Icon-App-20x20@2x.png' = 40
    'ios\Runner\Assets.xcassets\AppIcon.appiconset\Icon-App-20x20@3x.png' = 60
    'ios\Runner\Assets.xcassets\AppIcon.appiconset\Icon-App-29x29@1x.png' = 29
    'ios\Runner\Assets.xcassets\AppIcon.appiconset\Icon-App-29x29@2x.png' = 58
    'ios\Runner\Assets.xcassets\AppIcon.appiconset\Icon-App-29x29@3x.png' = 87
    'ios\Runner\Assets.xcassets\AppIcon.appiconset\Icon-App-40x40@1x.png' = 40
    'ios\Runner\Assets.xcassets\AppIcon.appiconset\Icon-App-40x40@2x.png' = 80
    'ios\Runner\Assets.xcassets\AppIcon.appiconset\Icon-App-40x40@3x.png' = 120
    'ios\Runner\Assets.xcassets\AppIcon.appiconset\Icon-App-60x60@2x.png' = 120
    'ios\Runner\Assets.xcassets\AppIcon.appiconset\Icon-App-60x60@3x.png' = 180
    'ios\Runner\Assets.xcassets\AppIcon.appiconset\Icon-App-76x76@1x.png' = 76
    'ios\Runner\Assets.xcassets\AppIcon.appiconset\Icon-App-76x76@2x.png' = 152
    'ios\Runner\Assets.xcassets\AppIcon.appiconset\Icon-App-83.5x83.5@2x.png' = 167
    'ios\Runner\Assets.xcassets\AppIcon.appiconset\Icon-App-1024x1024@1x.png' = 1024
}

$webIcons = @{
    'web\favicon.png' = 32
    'web\icons\Icon-192.png' = 192
    'web\icons\Icon-512.png' = 512
    'web\icons\Icon-maskable-192.png' = 192
    'web\icons\Icon-maskable-512.png' = 512
}

foreach ($entry in @($androidIcons, $iosIcons, $webIcons)) {
    foreach ($icon in $entry.GetEnumerator()) {
        New-SignSyncIcon -Path (Join-Path $flutterRoot $icon.Key) -Size $icon.Value
    }
}

Write-Host 'SignSync launcher assets generated successfully.'
