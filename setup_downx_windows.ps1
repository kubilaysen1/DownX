#Requires -RunAsAdministrator
################################################################################
# DownX Windows Installer
# Spotify & YouTube Downloader - Interactive Setup
# PowerShell 5.1+ Required
################################################################################

# Encoding
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# Renkler
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

function Write-Success { Write-ColorOutput Green "✓ $args" }
function Write-Error { Write-ColorOutput Red "✗ $args" }
function Write-Info { Write-ColorOutput Cyan "→ $args" }
function Write-Warning { Write-ColorOutput Yellow "⚠ $args" }

# Banner
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
Write-ColorOutput Magenta "║    Spotify & YouTube Downloader - Windows Edition            ║"
Write-ColorOutput Magenta "║    Otomatik Kurulum ve Geliştirme Ortamı                     ║"
Write-ColorOutput Magenta "║                                                               ║"
Write-ColorOutput Magenta "╚═══════════════════════════════════════════════════════════════╝"
Write-Host ""

# Admin kontrolü
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Error "Bu script yönetici (Administrator) olarak çalıştırılmalı!"
    Write-Info "Sağ tıklayıp 'Run as Administrator' seçin."
    pause
    exit 1
}

# Kurulum dizini
$INSTALL_DIR = "$env:USERPROFILE\DownX"
$VENV_PATH = "$INSTALL_DIR\.venv"
$CONFIG_DIR = "$env:APPDATA\DownX"
$DESKTOP_SHORTCUT = "$env:USERPROFILE\Desktop\DownX.lnk"
$START_MENU = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\DownX.lnk"

Write-Host ""
Write-ColorOutput Cyan "════════════════════════════════════════════════════════════"
Write-ColorOutput Cyan "  📋 KURULUM BİLGİLERİ"
Write-ColorOutput Cyan "════════════════════════════════════════════════════════════"
Write-Host ""

# ========================================
# KULLANICI GİRİŞLERİ
# ========================================

Write-ColorOutput Yellow "🎵 Spotify API Bilgileri:"
Write-Host "Spotify Developer Dashboard'dan alınır: https://developer.spotify.com/dashboard"
Write-Host ""

do {
    $SPOTIFY_CLIENT_ID = Read-Host "Spotify Client ID"
} while ($SPOTIFY_CLIENT_ID.Length -lt 20)
Write-Success "Client ID alındı"

do {
    $SecurePassword = Read-Host "Spotify Client Secret" -AsSecureString
    $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecurePassword)
    $SPOTIFY_CLIENT_SECRET = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
} while ($SPOTIFY_CLIENT_SECRET.Length -lt 20)
Write-Success "Client Secret alındı"
Write-Host ""

Write-ColorOutput Yellow "🎬 YouTube Cookies (Opsiyonel - Premium için):"
$USE_COOKIES = Read-Host "Cookies.txt dosyası eklemek ister misiniz? (E/H)"

$COOKIES_PATH = ""
if ($USE_COOKIES -match "^[Ee]$") {
    do {
        $COOKIES_PATH = Read-Host "Cookies.txt dosya yolu"
        if (Test-Path $COOKIES_PATH) {
            Write-Success "Cookies dosyası bulundu"
            break
        } else {
            Write-Warning "Dosya bulunamadı, tekrar deneyin"
        }
    } while ($true)
}
Write-Host ""

Write-ColorOutput Yellow "📁 İndirme Dizini:"
$DEFAULT_DOWNLOAD = "$env:USERPROFILE\Music\DownX"
$DOWNLOAD_DIR = Read-Host "İndirme dizini [$DEFAULT_DOWNLOAD]"
if ([string]::IsNullOrWhiteSpace($DOWNLOAD_DIR)) {
    $DOWNLOAD_DIR = $DEFAULT_DOWNLOAD
}
Write-Success "İndirme dizini: $DOWNLOAD_DIR"
Write-Host ""

Write-ColorOutput Yellow "⚙  Varsayılan İndirme Ayarları:"
Write-Host ""
Write-Host "Ses formatı:"
Write-Host "  1) M4A (Önerilen - Kaliteli, küçük boyut)"
Write-Host "  2) MP3 (Evrensel uyumluluk)"
Write-Host "  3) FLAC (Kayıpsız, büyük boyut)"
$FORMAT_CHOICE = Read-Host "Seçim [1]"
if ([string]::IsNullOrWhiteSpace($FORMAT_CHOICE)) { $FORMAT_CHOICE = "1" }

$AUDIO_FORMAT = switch ($FORMAT_CHOICE) {
    "1" { "m4a" }
    "2" { "mp3" }
    "3" { "flac" }
    default { "m4a" }
}
Write-Success "Ses formatı: $AUDIO_FORMAT"
Write-Host ""

Write-Host "Ses kalitesi:"
Write-Host "  1) 320 kbps (En yüksek kalite)"
Write-Host "  2) 256 kbps (Yüksek kalite, küçük boyut)"
Write-Host "  3) 192 kbps (İyi kalite, minimum boyut)"
$QUALITY_CHOICE = Read-Host "Seçim [1]"
if ([string]::IsNullOrWhiteSpace($QUALITY_CHOICE)) { $QUALITY_CHOICE = "1" }

$AUDIO_QUALITY = switch ($QUALITY_CHOICE) {
    "1" { "320" }
    "2" { "256" }
    "3" { "192" }
    default { "320" }
}
Write-Success "Ses kalitesi: $AUDIO_QUALITY kbps"
Write-Host ""

$EMBED_METADATA = Read-Host "Metadata ve kapak resmi eklensin mi? (E/H) [E]"
if ([string]::IsNullOrWhiteSpace($EMBED_METADATA)) { $EMBED_METADATA = "E" }
$EMBED_METADATA = $EMBED_METADATA -match "^[Ee]$"
Write-Success "Metadata: $EMBED_METADATA"
Write-Host ""

# ========================================
# ÖZET
# ========================================

Write-Host ""
Write-ColorOutput Cyan "════════════════════════════════════════════════════════════"
Write-ColorOutput Cyan "  📊 KURULUM ÖZETİ"
Write-ColorOutput Cyan "════════════════════════════════════════════════════════════"
Write-Host ""
Write-Host "Spotify API:"
Write-Host "  Client ID: $($SPOTIFY_CLIENT_ID.Substring(0, 20))..."
Write-Host "  Client Secret: ****"
Write-Host ""
Write-Host "YouTube:"
if ($COOKIES_PATH) {
    Write-Host "  Cookies: $(Split-Path -Leaf $COOKIES_PATH)"
} else {
    Write-Host "  Cookies: Yok"
}
Write-Host ""
Write-Host "İndirme Ayarları:"
Write-Host "  Dizin: $DOWNLOAD_DIR"
Write-Host "  Format: $AUDIO_FORMAT"
Write-Host "  Kalite: $AUDIO_QUALITY kbps"
Write-Host "  Metadata: $EMBED_METADATA"
Write-Host ""
Write-Host "Kurulum Dizini: $INSTALL_DIR"
Write-Host ""

$CONFIRM = Read-Host "Kuruluma devam etmek istiyor musunuz? (E/H)"
if ($CONFIRM -notmatch "^[Ee]$") {
    Write-Warning "Kurulum iptal edildi"
    exit 0
}

# Log dosyası
$LOG_FILE = "$INSTALL_DIR\kurulum.log"

# ========================================
# KURULUM BAŞLANGIÇ
# ========================================

Write-Host ""
Write-ColorOutput Cyan "════════════════════════════════════════════════════════════"
Write-ColorOutput Cyan "  ADIM 1/7: Python Kontrolü"
Write-ColorOutput Cyan "════════════════════════════════════════════════════════════"

# Python var mı?
$PYTHON_CMD = $null
$pythonCommands = @("python", "python3", "py")

foreach ($cmd in $pythonCommands) {
    try {
        $version = & $cmd --version 2>&1
        if ($version -match "Python (\d+)\.(\d+)") {
            $major = [int]$matches[1]
            $minor = [int]$matches[2]
            if ($major -ge 3 -and $minor -ge 8) {
                $PYTHON_CMD = $cmd
                Write-Success "Python bulundu: $version"
                break
            }
        }
    } catch {}
}

if (-not $PYTHON_CMD) {
    Write-Error "Python 3.8+ bulunamadı!"
    Write-Info "Python'u indirin: https://www.python.org/downloads/"
    Write-Info "Kurulumda 'Add Python to PATH' seçeneğini işaretleyin!"
    pause
    exit 1
}

# ========================================
# ADIM 2: DIZINLER
# ========================================

Write-Host ""
Write-ColorOutput Cyan "════════════════════════════════════════════════════════════"
Write-ColorOutput Cyan "  ADIM 2/7: Dizinler Oluşturuluyor"
Write-ColorOutput Cyan "════════════════════════════════════════════════════════════"

New-Item -ItemType Directory -Force -Path $INSTALL_DIR | Out-Null
New-Item -ItemType Directory -Force -Path "$INSTALL_DIR\resources\icons" | Out-Null
New-Item -ItemType Directory -Force -Path $CONFIG_DIR | Out-Null
New-Item -ItemType Directory -Force -Path $DOWNLOAD_DIR | Out-Null

Write-Success "Dizinler oluşturuldu"

# ========================================
# ADIM 3: VIRTUAL ENVIRONMENT
# ========================================

Write-Host ""
Write-ColorOutput Cyan "════════════════════════════════════════════════════════════"
Write-ColorOutput Cyan "  ADIM 3/7: Virtual Environment"
Write-ColorOutput Cyan "════════════════════════════════════════════════════════════"

if (Test-Path $VENV_PATH) {
    Write-Info "Virtual environment zaten mevcut"
} else {
    Write-Info "Virtual environment oluşturuluyor..."
    & $PYTHON_CMD -m venv $VENV_PATH
    Write-Success "Virtual environment oluşturuldu"
}

# venv aktivasyonu
$VENV_PYTHON = "$VENV_PATH\Scripts\python.exe"
$VENV_PIP = "$VENV_PATH\Scripts\pip.exe"

# pip güncelle
Write-Info "pip güncelleniyor..."
& $VENV_PIP install --upgrade pip setuptools wheel | Out-Null
Write-Success "pip güncellendi"

# ========================================
# ADIM 4: PYTHON PAKETLERI
# ========================================

Write-Host ""
Write-ColorOutput Cyan "════════════════════════════════════════════════════════════"
Write-ColorOutput Cyan "  ADIM 4/7: Python Paketleri (Bu biraz zaman alabilir)"
Write-ColorOutput Cyan "════════════════════════════════════════════════════════════"

$packages = @(
    "requests",
    "urllib3",
    "Pillow",
    "mutagen",
    "yt-dlp",
    "spotdl",
    "spotipy",
    "PyQt6",
    "pylint",
    "black",
    "mypy",
    "pytest"
)

foreach ($pkg in $packages) {
    Write-Info "Kuruluyor: $pkg"
    & $VENV_PIP install $pkg 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Success "$pkg kuruldu"
    } else {
        Write-Warning "$pkg kurulamadı (isteğe bağlı olabilir)"
    }
}

# ========================================
# ADIM 5: CONFIG DOSYALARI
# ========================================

Write-Host ""
Write-ColorOutput Cyan "════════════════════════════════════════════════════════════"
Write-ColorOutput Cyan "  ADIM 5/7: Config Dosyaları"
Write-ColorOutput Cyan "════════════════════════════════════════════════════════════"

# config.json
$CONFIG_JSON = @{
    download_dir = $DOWNLOAD_DIR
    audio_format = $AUDIO_FORMAT
    audio_quality = $AUDIO_QUALITY
    embed_metadata = $EMBED_METADATA
    embed_thumbnail = $EMBED_METADATA
    concurrent_downloads = 3
    skip_existing = $true
    theme = "dark"
    language = "tr"
} | ConvertTo-Json

Set-Content -Path "$CONFIG_DIR\config.json" -Value $CONFIG_JSON -Encoding UTF8
Write-Success "config.json oluşturuldu"

# spotify_credentials.json
$SPOTIFY_JSON = @{
    client_id = $SPOTIFY_CLIENT_ID
    client_secret = $SPOTIFY_CLIENT_SECRET
} | ConvertTo-Json

Set-Content -Path "$CONFIG_DIR\spotify_credentials.json" -Value $SPOTIFY_JSON -Encoding UTF8
Write-Success "Spotify credentials kaydedildi"

# cookies.txt
if ($COOKIES_PATH) {
    Copy-Item $COOKIES_PATH "$CONFIG_DIR\cookies.txt"
    Write-Success "YouTube cookies kopyalandı"
}

# ========================================
# ADIM 6: İKONLAR
# ========================================

Write-Host ""
Write-ColorOutput Cyan "════════════════════════════════════════════════════════════"
Write-ColorOutput Cyan "  ADIM 6/7: İkonlar"
Write-ColorOutput Cyan "════════════════════════════════════════════════════════════"

# İkon script dizininde mi?
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$ICON_FOUND = $false

$icon_files = @(
    "downx_icon_purple.png",
    "downx_icon_128.png",
    "downx_icon_64.png",
    "downx_icon_48.png",
    "downx_icon_32.png"
)

foreach ($icon in $icon_files) {
    $source = Join-Path $SCRIPT_DIR $icon
    if (Test-Path $source) {
        Copy-Item $source "$INSTALL_DIR\resources\icons\" -Force
        $ICON_FOUND = $true
    }
}

if ($ICON_FOUND) {
    # icon.png ve logo.png oluştur
    if (Test-Path "$INSTALL_DIR\resources\icons\downx_icon_purple.png") {
        Copy-Item "$INSTALL_DIR\resources\icons\downx_icon_purple.png" "$INSTALL_DIR\resources\icons\icon.png"
    }
    if (Test-Path "$INSTALL_DIR\resources\icons\downx_icon_128.png") {
        Copy-Item "$INSTALL_DIR\resources\icons\downx_icon_128.png" "$INSTALL_DIR\resources\logo.png"
    }
    Write-Success "İkonlar kopyalandı"
} else {
    Write-Warning "İkonlar bulunamadı (opsiyonel)"
}

# ========================================
# ADIM 7: SHORTCUTS
# ========================================

Write-Host ""
Write-ColorOutput Cyan "════════════════════════════════════════════════════════════"
Write-ColorOutput Cyan "  ADIM 7/7: Kısayollar"
Write-ColorOutput Cyan "════════════════════════════════════════════════════════════"

# run.bat
$RUN_BAT = @"
@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat
python gui.py
pause
"@
Set-Content -Path "$INSTALL_DIR\run.bat" -Value $RUN_BAT -Encoding ASCII
Write-Success "run.bat oluşturuldu"

# Desktop shortcut
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($DESKTOP_SHORTCUT)
$Shortcut.TargetPath = "$INSTALL_DIR\run.bat"
$Shortcut.WorkingDirectory = $INSTALL_DIR
$Shortcut.WindowStyle = 1
if (Test-Path "$INSTALL_DIR\resources\icons\icon.ico") {
    $Shortcut.IconLocation = "$INSTALL_DIR\resources\icons\icon.ico"
} elseif (Test-Path "$INSTALL_DIR\resources\icons\icon.png") {
    $Shortcut.IconLocation = "$INSTALL_DIR\resources\icons\icon.png"
}
$Shortcut.Save()
Write-Success "Masaüstü kısayolu oluşturuldu"

# Start Menu shortcut
$Shortcut = $WshShell.CreateShortcut($START_MENU)
$Shortcut.TargetPath = "$INSTALL_DIR\run.bat"
$Shortcut.WorkingDirectory = $INSTALL_DIR
$Shortcut.WindowStyle = 1
if (Test-Path "$INSTALL_DIR\resources\icons\icon.ico") {
    $Shortcut.IconLocation = "$INSTALL_DIR\resources\icons\icon.ico"
} elseif (Test-Path "$INSTALL_DIR\resources\icons\icon.png") {
    $Shortcut.IconLocation = "$INSTALL_DIR\resources\icons\icon.png"
}
$Shortcut.Save()
Write-Success "Başlat menüsü kısayolu oluşturuldu"

# ========================================
# TAMAMLANDI
# ========================================

Write-Host ""
Write-ColorOutput Magenta "╔═══════════════════════════════════════════════════════════╗"
Write-ColorOutput Green "║  🎉 KURULUM BAŞARILI!                                     ║"
Write-ColorOutput Magenta "╚═══════════════════════════════════════════════════════════╝"
Write-Host ""

Write-ColorOutput Cyan "⚙  KURULUM AYARLARI:"
Write-Host "• Spotify API: ✓ Yapılandırıldı"
if ($COOKIES_PATH) {
    Write-Host "• YouTube Cookies: ✓ Eklendi"
}
Write-Host "• Format: $AUDIO_FORMAT ($AUDIO_QUALITY kbps)"
Write-Host "• Metadata: $EMBED_METADATA"
Write-Host "• Dizin: $DOWNLOAD_DIR"
Write-Host ""

Write-ColorOutput Cyan "📦 SONRAKI ADIMLAR:"
Write-Host ""
Write-Host "1. Masaüstü kısayolundan:"
Write-Host "   → 'DownX' ikonuna çift tıkla"
Write-Host ""
Write-Host "2. Veya terminal'den:"
Write-Host "   cd $INSTALL_DIR"
Write-Host "   .\run.bat"
Write-Host ""
Write-Host "3. Python dosyalarını kopyalayın:"
Write-Host "   gui.py, settings.py, downloader.py, vb."
Write-Host "   → $INSTALL_DIR dizinine"
Write-Host ""

Write-ColorOutput Yellow "⚠  ÖNEMLİ:"
Write-Host "• Uygulama Python dosyalarını manuel kopyalamalısınız"
Write-Host "• gui.py ve diğer .py dosyalarını $INSTALL_DIR içine atın"
Write-Host ""

Write-Host "Log dosyası: $LOG_FILE"
Write-Host ""
Write-ColorOutput Magenta "═══════════════════════════════════════════════════════════"
Write-Host "Kolay gelsin! 🚀"
Write-ColorOutput Magenta "═══════════════════════════════════════════════════════════"
Write-Host ""

pause
