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
}

if ($Uninstall) {
    Remove-Item (Join-Path $Dirs["effect-templates"] "ouzfx_*.xml") -ErrorAction SilentlyContinue
    Remove-Item (Join-Path $Dirs["transitions"] "ouzfx_*.xml") -ErrorAction SilentlyContinue
    Remove-Item $Dirs["lumasHD"], $Dirs["lumasV"], (Join-Path $Roaming "ouzfx") -Recurse -Force -ErrorAction SilentlyContinue
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
Write-Host "Installed OuzFX ($Profile). Restart Kdenlive and search 'OuzFX' in Effects / Compositions."
