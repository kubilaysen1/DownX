#Requires -Version 5.1
################################################################################
# DownX - Tek Komut Kurulum (Windows)
# irm https://raw.githubusercontent.com/[username]/DownX/main/install.ps1 | iex
################################################################################

$ErrorActionPreference = "Stop"

function Write-ColorOutput($Color, $Message) {
    Write-Host $Message -ForegroundColor $Color
}

Clear-Host
Write-Host ""
Write-ColorOutput Magenta "╔═══════════════════════════════════════════════════════════════╗"
Write-ColorOutput Magenta "║                                                               ║"
Write-ColorOutput Magenta "║    ██████╗  ██████╗ ██╗    ██╗███╗   ██╗██╗  ██╗            ║"
Write-ColorOutput Magenta "║    ██╔══██╗██╔═══██╗██║    ██║████╗  ██║╚██╗██╔╝            ║"
Write-ColorOutput Magenta "║    ██║  ██║██║   ██║██║ █╗ ██║██╔██╗ ██║ ╚███╔╝             ║"
Write-ColorOutput Magenta "║    ██║  ██║██║   ██║██║███╗██║██║╚██╗██║ ██╔██╗             ║"
Write-ColorOutput Magenta "║    ██████╔╝╚██████╔╝╚███╔███╔╝██║ ╚████║██╔╝ ██╗            ║"
Write-ColorOutput Magenta "║    ╚═════╝  ╚═════╝  ╚══╝╚══╝ ╚═╝  ╚═══╝╚═╝  ╚═╝            ║"
Write-ColorOutput Magenta "║                                                               ║"
Write-ColorOutput Magenta "║    Tek Komut Kurulum - Windows                                ║"
Write-ColorOutput Magenta "║                                                               ║"
Write-ColorOutput Magenta "╚═══════════════════════════════════════════════════════════════╝"
Write-Host ""

$INSTALL_DIR = "$env:USERPROFILE\DownX"
$TEMP_DIR = "$env:TEMP\downx-install-$(Get-Random)"

Write-ColorOutput Cyan "[1/4] Hazırlanıyor..."

# Geçici dizin
New-Item -ItemType Directory -Force -Path $TEMP_DIR | Out-Null
Set-Location $TEMP_DIR

# Git var mı?
$USE_GIT = $false
try {
    $null = git --version
    Write-ColorOutput Green "✓ Git bulundu"
    $USE_GIT = $true
} catch {
    Write-ColorOutput Yellow "⚠ Git bulunamadı, Invoke-WebRequest kullanılacak"
}

Write-Host ""
Write-ColorOutput Cyan "[2/4] DownX indiriliyor..."

if ($USE_GIT) {
    # Git ile klonla
    git clone --depth 1 https://github.com/[username]/DownX.git $INSTALL_DIR
    Write-ColorOutput Green "✓ Repo klonlandı"
} else {
    # Wget ile indir
    $REPO_ZIP = "https://github.com/[username]/DownX/archive/refs/heads/main.zip"
    Invoke-WebRequest -Uri $REPO_ZIP -OutFile "downx.zip"
    Expand-Archive -Path "downx.zip" -DestinationPath "."
    New-Item -ItemType Directory -Force -Path $INSTALL_DIR | Out-Null
    Copy-Item -Path "DownX-main\*" -Destination $INSTALL_DIR -Recurse -Force
    Write-ColorOutput Green "✓ Dosyalar indirildi"
}

Write-Host ""
Write-ColorOutput Cyan "[3/4] Kurulum scripti çalıştırılıyor..."
Write-Host ""

Set-Location $INSTALL_DIR

# Kurulum scriptini belirle
$SETUP_SCRIPT = $null
if (Test-Path "setup_windows.ps1") {
    $SETUP_SCRIPT = "setup_windows.ps1"
} elseif (Test-Path "setup_windows.bat") {
    $SETUP_SCRIPT = "setup_windows.bat"
}

if ($SETUP_SCRIPT) {
    if ($SETUP_SCRIPT -like "*.ps1") {
        & ".\$SETUP_SCRIPT"
    } else {
        & ".\$SETUP_SCRIPT"
    }
} else {
    Write-ColorOutput Red "✗ Kurulum scripti bulunamadı!"
    exit 1
}

Write-Host ""
Write-ColorOutput Cyan "[4/4] Temizlik..."
Remove-Item -Path $TEMP_DIR -Recurse -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-ColorOutput Magenta "╔═══════════════════════════════════════════════════════════════╗"
Write-ColorOutput Green "║  🎉 DownX Kurulumu Tamamlandı!                                ║"
Write-ColorOutput Magenta "╚═══════════════════════════════════════════════════════════════╝"
Write-Host ""
Write-ColorOutput Cyan "Çalıştırmak için:"
Write-Host "  Masaüstünde 'DownX' kısayoluna çift tıklayın"
Write-Host "  Veya: $INSTALL_DIR\run.bat"
Write-Host ""
Write-ColorOutput Magenta "Kolay gelsin! 🚀"
Write-Host ""
