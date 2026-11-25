# OuzFX – Kdenlive effects & transitions pack installer for Windows
# Usage (PowerShell):  .\install.ps1 [-Profile 1080p|4k|vertical] [-Uninstall]
param(
    [ValidateSet("1080p", "4k", "vertical")][string]$Profile = "1080p",
    [switch]$Uninstall
)
$ErrorActionPreference = "Stop"
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$Pack = Join-Path $Here "pack"
# Kdenlive on Windows: effects/compositions in %AppData%\kdenlive (Roaming),
# lumas in %LocalAppData%\kdenlive\lumas (that is where Kdenlive scans for them).
$Roaming = Join-Path $env:APPDATA "kdenlive"
$Local = Join-Path $env:LOCALAPPDATA "kdenlive"
$Dirs = @{
    "effect-templates" = Join-Path $Roaming "effect-templates"
    "transitions"      = Join-Path $Roaming "transitions"
    "lumasHD"          = Join-Path $Local "lumas\HD\ouzfx"
    "lumasV"           = Join-Path $Local "lumas\VERTICAL\ouzfx"
    "overlays"         = Join-Path $Roaming "ouzfx\overlays"
    "sfx"              = Join-Path $Roaming "ouzfx\sfx"
    "library"          = Join-Path $Roaming "library\OuzFX SFX"
    "highlights"       = Join-Path $Roaming "ouzfx\highlights"
    "libraryHL"        = Join-Path $Roaming "library\OuzFX Highlights"
    "titles"           = Join-Path $Roaming "titles"
}
$HlSize = if ($Profile -eq "4k") { "2160" } else { "1080" }

if ($Uninstall) {
    Remove-Item (Join-Path $Dirs["effect-templates"] "ouzfx_*.xml") -ErrorAction SilentlyContinue
    Remove-Item (Join-Path $Dirs["transitions"] "ouzfx_*.xml") -ErrorAction SilentlyContinue
    Remove-Item $Dirs["lumasHD"], $Dirs["lumasV"], (Join-Path $Roaming "ouzfx"), $Dirs["library"], $Dirs["libraryHL"] -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item (Join-Path $Dirs["titles"] "ouzfx_*.kdenlivetitle") -ErrorAction SilentlyContinue
    Write-Host "Removed OuzFX. Restart Kdenlive."
    exit 0
}

foreach ($d in $Dirs.Values) { New-Item -ItemType Directory -Force -Path $d | Out-Null }
Copy-Item (Join-Path $Pack "$Profile\effect-templates\*.xml") $Dirs["effect-templates"] -Force
$LumaRoot = (Join-Path $Local "lumas") -replace '\\', '/'
Get-ChildItem (Join-Path $Pack "$Profile\transitions\*.xml") | ForEach-Object {
    (Get-Content $_.FullName -Raw -Encoding UTF8).Replace("@LUMADIR@", $LumaRoot) |
        Set-Content -Path (Join-Path $Dirs["transitions"] $_.Name) -Encoding UTF8
}
Copy-Item (Join-Path $Pack "lumas\HD\ouzfx\*.png") $Dirs["lumasHD"] -Force
Copy-Item (Join-Path $Pack "lumas\VERTICAL\ouzfx\*.png") $Dirs["lumasV"] -Force
if (Test-Path (Join-Path $Here "overlays")) { Copy-Item (Join-Path $Here "overlays\*") $Dirs["overlays"] -Force }
if (Test-Path (Join-Path $Here "sfx")) {
    Get-ChildItem (Join-Path $Here "sfx") -Directory | ForEach-Object {
        foreach ($root in @($Dirs["sfx"], $Dirs["library"])) {
            $t = Join-Path $root $_.Name
            New-Item -ItemType Directory -Force -Path $t | Out-Null
            Copy-Item (Join-Path $_.FullName "*.wav") $t -Force
        }
    }
    Write-Host "Sound effects: $($Dirs["sfx"]) (also in Kdenlive's Library panel > OuzFX SFX)"
}
$HlSrc = Join-Path $Here "highlights\$HlSize"
if (Test-Path $HlSrc) {
    Get-ChildItem $HlSrc -Directory | ForEach-Object {
        foreach ($root in @($Dirs["highlights"], $Dirs["libraryHL"])) {
            $t = Join-Path $root $_.Name
            New-Item -ItemType Directory -Force -Path $t | Out-Null
            Copy-Item (Join-Path $_.FullName "*.webm") $t -Force
        }
    }
    Write-Host "Highlights: $($Dirs["highlights"]) (also in Kdenlive's Library panel > OuzFX Highlights)"
}
$TiSrc = Join-Path $Here "titles\$Profile"
if (Test-Path $TiSrc) {
    Copy-Item (Join-Path $TiSrc "*.kdenlivetitle") $Dirs["titles"] -Force
    Write-Host "Label title templates: $($Dirs["titles"]) (Project > Add Template Title)"
}
# brand fonts (OFL) - per-user install, no admin rights needed
$FontSrc = Join-Path $Here "fonts"
if (Test-Path $FontSrc) {
    $UserFonts = Join-Path $env:LOCALAPPDATA "Microsoft\Windows\Fonts"
    New-Item -ItemType Directory -Force -Path $UserFonts | Out-Null
    $Reg = "HKCU:\Software\Microsoft\Windows NT\CurrentVersion\Fonts"
    Get-ChildItem (Join-Path $FontSrc "*.ttf") | ForEach-Object {
        $dst = Join-Path $UserFonts $_.Name
        Copy-Item $_.FullName $dst -Force
        New-ItemProperty -Path $Reg -Name "$($_.BaseName) (TrueType)" -Value $dst -PropertyType String -Force | Out-Null
    }
    Write-Host "Brand fonts installed for the current user (restart Kdenlive to pick them up)."
}
Write-Host "Installed OuzFX ($Profile). Restart Kdenlive and search 'OuzFX' in Effects / Compositions."
