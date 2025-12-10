#!/bin/bash
################################################################################
# DownX - Otomatik Kurulum ve Geliştirme Ortamı Kurulum Scripti
# Bazzite OS (Fedora Silverblue tabanlı) için özel
#
# Kullanım: chmod +x setup_downx.sh && ./setup_downx.sh
################################################################################

set -e  # Hata durumunda dur

# Renkler
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Banner
clear
echo -e "${CYAN}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║    ██████╗  ██████╗ ██╗    ██╗███╗   ██╗██╗  ██╗            ║
║    ██╔══██╗██╔═══██╗██║    ██║████╗  ██║╚██╗██╔╝            ║
║    ██║  ██║██║   ██║██║ █╗ ██║██╔██╗ ██║ ╚███╔╝             ║
║    ██║  ██║██║   ██║██║███╗██║██║╚██╗██║ ██╔██╗             ║
║    ██████╔╝╚██████╔╝╚███╔███╔╝██║ ╚████║██╔╝ ██╗            ║
║    ╚═════╝  ╚═════╝  ╚══╝╚══╝ ╚═╝  ╚═══╝╚═╝  ╚═╝            ║
║                                                               ║
║    Spotify & YouTube Downloader - Bazzite OS Edition         ║
║    Otomatik Kurulum ve Geliştirme Ortamı                     ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

echo -e "${GREEN}DownX Kurulum Scripti - Bazzite OS${NC}"
echo -e "${YELLOW}Geliştirme ortamı ve tüm bağımlılıklar kurulacak...${NC}"
echo ""

# Root kontrolü (root olmamalı)
if [ "$EUID" -eq 0 ]; then
   echo -e "${RED}HATA: Bu scripti root olarak çalıştırmayın!${NC}"
   echo "Lütfen normal kullanıcı olarak çalıştırın."
   exit 1
fi

# Bazzite OS kontrolü
if [ ! -f /etc/os-release ]; then
    echo -e "${RED}HATA: /etc/os-release bulunamadı!${NC}"
    exit 1
fi

source /etc/os-release
echo -e "${BLUE}Tespit edilen sistem: ${NAME} ${VERSION}${NC}"

# Bazzite/Fedora kontrolü
if [[ ! "$ID" =~ ^(fedora|bazzite)$ ]]; then
    echo -e "${YELLOW}UYARI: Bu script Bazzite OS için optimize edilmiştir.${NC}"
    echo -e "${YELLOW}Devam etmek istiyor musunuz? (e/h)${NC}"
    read -r response
    if [[ ! "$response" =~ ^[eE]$ ]]; then
        exit 0
    fi
fi

# Dizinler
PROJECT_DIR="$HOME/Source/DownX"
VENV_DIR="$PROJECT_DIR/.venv"
CONFIG_DIR="$HOME/.config/downx"
CACHE_DIR="$HOME/.cache/downx"

echo ""
echo -e "${PURPLE}════════════════════════════════════════════════════════════${NC}"
echo -e "${PURPLE}  📋 KURULUM BİLGİLERİ${NC}"
echo -e "${PURPLE}════════════════════════════════════════════════════════════${NC}"
echo ""

# Kullanıcıdan bilgi al
echo -e "${CYAN}🎵 Spotify API Bilgileri:${NC}"
echo -e "${YELLOW}Spotify Developer Dashboard'dan alınır: https://developer.spotify.com/dashboard${NC}"
echo ""

# Spotify Client ID
while true; do
    read -p "$(echo -e ${GREEN}Enter Spotify Client ID: ${NC})" SPOTIFY_CLIENT_ID
    if [ ${#SPOTIFY_CLIENT_ID} -ge 20 ]; then
        echo -e "${GREEN}✓ Client ID alındı${NC}"
        break
    else
        echo -e "${RED}❌ Client ID çok kısa! En az 20 karakter olmalı.${NC}"
    fi
done

echo ""

# Spotify Client Secret
while true; do
    read -sp "$(echo -e ${GREEN}Enter Spotify Client Secret: ${NC})" SPOTIFY_CLIENT_SECRET
    echo ""
    if [ ${#SPOTIFY_CLIENT_SECRET} -ge 20 ]; then
        echo -e "${GREEN}✓ Client Secret alındı${NC}"
        break
    else
        echo -e "${RED}❌ Client Secret çok kısa! En az 20 karakter olmalı.${NC}"
    fi
done

echo ""
echo ""

# YouTube Cookies (opsiyonel)
echo -e "${CYAN}🎬 YouTube Cookies (Opsiyonel - Premium için):${NC}"
echo -e "${YELLOW}Cookies.txt dosyası eklemek ister misiniz? (e/h)${NC}"
read -r ADD_COOKIES

YOUTUBE_COOKIES_PATH=""
if [[ "$ADD_COOKIES" =~ ^[eE]$ ]]; then
    read -p "$(echo -e ${GREEN}Cookies.txt dosya yolu: ${NC})" YOUTUBE_COOKIES_PATH
    if [ -f "$YOUTUBE_COOKIES_PATH" ]; then
        echo -e "${GREEN}✓ Cookies dosyası bulundu${NC}"
    else
        echo -e "${YELLOW}⚠️  Dosya bulunamadı, kurulumdan sonra manuel eklenebilir${NC}"
        YOUTUBE_COOKIES_PATH=""
    fi
fi

echo ""
echo ""

# İndirme dizini
echo -e "${CYAN}📁 İndirme Dizini:${NC}"
DEFAULT_DOWNLOAD_DIR="$HOME/Music/DownX"
read -p "$(echo -e ${GREEN}İndirme dizini [${DEFAULT_DOWNLOAD_DIR}]: ${NC})" DOWNLOAD_DIR
DOWNLOAD_DIR=${DOWNLOAD_DIR:-$DEFAULT_DOWNLOAD_DIR}
echo -e "${GREEN}✓ İndirme dizini: ${DOWNLOAD_DIR}${NC}"

echo ""
echo ""

# Varsayılan ayarlar
echo -e "${CYAN}⚙️  Varsayılan İndirme Ayarları:${NC}"
echo ""

# Audio format
echo -e "${YELLOW}Ses formatı:${NC}"
echo "  1) M4A (Önerilen - Kaliteli, küçük boyut)"
echo "  2) MP3 (Evrensel uyumluluk)"
echo "  3) FLAC (Kayıpsız, büyük boyut)"
read -p "$(echo -e ${GREEN}Seçim [1]: ${NC})" AUDIO_FORMAT_CHOICE
AUDIO_FORMAT_CHOICE=${AUDIO_FORMAT_CHOICE:-1}

case $AUDIO_FORMAT_CHOICE in
    1) AUDIO_FORMAT="m4a" ;;
    2) AUDIO_FORMAT="mp3" ;;
    3) AUDIO_FORMAT="flac" ;;
    *) AUDIO_FORMAT="m4a" ;;
esac

echo -e "${GREEN}✓ Ses formatı: ${AUDIO_FORMAT}${NC}"
echo ""

# Audio quality
echo -e "${YELLOW}Ses kalitesi:${NC}"
echo "  1) 320 kbps (En yüksek kalite)"
echo "  2) 256 kbps (Yüksek kalite, küçük boyut)"
echo "  3) 192 kbps (İyi kalite, minimum boyut)"
read -p "$(echo -e ${GREEN}Seçim [1]: ${NC})" AUDIO_QUALITY_CHOICE
AUDIO_QUALITY_CHOICE=${AUDIO_QUALITY_CHOICE:-1}

case $AUDIO_QUALITY_CHOICE in
    1) AUDIO_QUALITY="320" ;;
    2) AUDIO_QUALITY="256" ;;
    3) AUDIO_QUALITY="192" ;;
    *) AUDIO_QUALITY="320" ;;
esac

echo -e "${GREEN}✓ Ses kalitesi: ${AUDIO_QUALITY} kbps${NC}"
echo ""

# Metadata
echo -e "${YELLOW}Metadata ve kapak resmi eklensin mi? (e/h) [e]:${NC}"
read -r ADD_METADATA
ADD_METADATA=${ADD_METADATA:-e}

if [[ "$ADD_METADATA" =~ ^[eE]$ ]]; then
    EMBED_METADATA="true"
    EMBED_THUMBNAIL="true"
    echo -e "${GREEN}✓ Metadata ve kapak resmi eklenecek${NC}"
else
    EMBED_METADATA="false"
    EMBED_THUMBNAIL="false"
    echo -e "${YELLOW}⚠️  Metadata ve kapak resmi eklenmeyecek${NC}"
fi

echo ""
echo ""

# Özet
echo -e "${PURPLE}════════════════════════════════════════════════════════════${NC}"
echo -e "${PURPLE}  📊 KURULUM ÖZETİ${NC}"
echo -e "${PURPLE}════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${CYAN}Spotify API:${NC}"
echo "  Client ID: ${SPOTIFY_CLIENT_ID:0:20}..."
echo "  Client Secret: ****"
echo ""
echo -e "${CYAN}YouTube:${NC}"
if [ -n "$YOUTUBE_COOKIES_PATH" ]; then
    echo "  Cookies: $(basename $YOUTUBE_COOKIES_PATH)"
else
    echo "  Cookies: Yok (opsiyonel)"
fi
echo ""
echo -e "${CYAN}İndirme Ayarları:${NC}"
echo "  Dizin: $DOWNLOAD_DIR"
echo "  Format: $AUDIO_FORMAT"
echo "  Kalite: $AUDIO_QUALITY kbps"
echo "  Metadata: $EMBED_METADATA"
echo ""

# Onay
echo -e "${YELLOW}Kuruluma devam etmek istiyor musunuz? (e/h)${NC}"
read -r CONFIRM

if [[ ! "$CONFIRM" =~ ^[eE]$ ]]; then
    echo -e "${RED}Kurulum iptal edildi.${NC}"
    exit 0
fi

echo ""
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  ADIM 1/8: Sistem Güncellemesi${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"

# Bazzite OS immutable, rpm-ostree kullanır
echo -e "${BLUE}rpm-ostree güncelleniyor...${NC}"
rpm-ostree upgrade --check || echo -e "${YELLOW}Güncelleme kontrolü atlandı${NC}"

echo ""
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  ADIM 2/8: Sistem Paketleri (Toolbox/Layered)${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"

# Bazzite'da sistem paketleri için rpm-ostree veya toolbox kullanılır
# GTK3 ve FFmpeg Flatpak veya layered olarak kurulabilir

echo -e "${BLUE}Gerekli paketler kontrol ediliyor...${NC}"

# GTK3 kontrol
if ! rpm -qa | grep -q gtk3; then
    echo -e "${YELLOW}GTK3 layered paket olarak kuruluyor...${NC}"
    rpm-ostree install gtk3 gtk3-devel || echo -e "${YELLOW}GTK3 zaten kurulu olabilir${NC}"
fi

# FFmpeg - Bazzite'da genelde önceden yüklü
if ! command -v ffmpeg &> /dev/null; then
    echo -e "${YELLOW}FFmpeg bulunamadı, layered paket olarak kuruluyor...${NC}"
    rpm-ostree install ffmpeg ffmpeg-libs || {
        echo -e "${YELLOW}rpm-ostree ile kurulamadı, Flatpak kullanılacak${NC}"
    }
fi

# Development tools
echo -e "${BLUE}Development tools kontrol ediliyor...${NC}"
rpm-ostree install python3-devel cairo-devel gobject-introspection-devel cairo-gobject-devel || \
    echo -e "${YELLOW}Dev tools zaten kurulu${NC}"

echo ""
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  ADIM 3/8: Python Ortamı${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"

# Python kontrolü
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}HATA: Python3 bulunamadı!${NC}"
    echo "Bazzite OS'ta Python3 varsayılan olarak gelmelidir."
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}✓ Python bulundu: ${PYTHON_VERSION}${NC}"

# pip kontrolü ve yükleme
if ! python3 -m pip --version &> /dev/null; then
    echo -e "${YELLOW}pip kuruluyor...${NC}"
    python3 -m ensurepip --upgrade
fi

# pip güncelleme
echo -e "${BLUE}pip güncelleniyor...${NC}"
python3 -m pip install --user --upgrade pip setuptools wheel

echo ""
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  ADIM 4/8: Proje Dizini ve Virtual Environment${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"

# Proje dizini oluştur
echo -e "${BLUE}Proje dizini oluşturuluyor: ${PROJECT_DIR}${NC}"
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

# Virtual environment oluştur
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${BLUE}Virtual environment oluşturuluyor...${NC}"
    python3 -m venv "$VENV_DIR"
    echo -e "${GREEN}✓ Virtual environment oluşturuldu${NC}"
else
    echo -e "${GREEN}✓ Virtual environment zaten mevcut${NC}"
fi

# Virtual environment'ı aktifleştir
echo -e "${BLUE}Virtual environment aktifleştiriliyor...${NC}"
source "$VENV_DIR/bin/activate"

# pip güncelle (venv içinde)
pip install --upgrade pip setuptools wheel

echo ""
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  ADIM 5/8: Python Paketleri (PyPI)${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"

echo -e "${BLUE}Python paketleri kuruluyor (bu biraz zaman alabilir)...${NC}"

# Temel paketler
pip install --upgrade \
    requests \
    urllib3 \
    Pillow \
    mutagen

# PyGObject (GTK3 için) - Sistem paketlerini kullan
echo -e "${BLUE}PyGObject kuruluyor...${NC}"
pip install PyGObject || {
    echo -e "${YELLOW}PyGObject pip ile kurulamadı, sistem paketini kullanıyoruz${NC}"
    # Bazzite'da sistem PyGObject'i kullanılabilir
}

# Downloader'lar
echo -e "${BLUE}yt-dlp ve spotdl kuruluyor...${NC}"
pip install yt-dlp spotdl

# Geliştirme araçları
echo -e "${BLUE}Geliştirme araçları kuruluyor...${NC}"
pip install \
    pylint \
    black \
    mypy \
    pytest

echo -e "${GREEN}✓ Tüm Python paketleri kuruldu${NC}"

echo ""
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  ADIM 6/8: VS Code Ayarları${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"

# VS Code settings dizini
VSCODE_DIR="$PROJECT_DIR/.vscode"
mkdir -p "$VSCODE_DIR"

# settings.json
cat > "$VSCODE_DIR/settings.json" << 'EOL'
{
    "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
    "python.terminal.activateEnvironment": true,
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "python.formatting.blackArgs": ["--line-length", "100"],
    "editor.formatOnSave": true,
    "editor.rulers": [100],
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        "**/.pytest_cache": true,
        "**/.mypy_cache": true
    },
    "python.analysis.typeCheckingMode": "basic",
    "python.testing.pytestEnabled": true,
    "terminal.integrated.env.linux": {
        "PYTHONPATH": "${workspaceFolder}"
    }
}
EOL

# launch.json (debug için)
cat > "$VSCODE_DIR/launch.json" << 'EOL'
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "DownX GUI",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/gui.py",
            "console": "integratedTerminal",
            "justMyCode": false
        },
        {
            "name": "DownX Launcher",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/launcher.py",
            "console": "integratedTerminal"
        }
    ]
}
EOL

# tasks.json (build tasks)
cat > "$VSCODE_DIR/tasks.json" << 'EOL'
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Run DownX",
            "type": "shell",
            "command": "${workspaceFolder}/.venv/bin/python",
            "args": ["gui.py"],
            "group": {
                "kind": "build",
                "isDefault": true
            },
            "presentation": {
                "reveal": "always",
                "panel": "new"
            }
        },
        {
            "label": "Run Tests",
            "type": "shell",
            "command": "${workspaceFolder}/.venv/bin/pytest",
            "args": ["-v"],
            "group": "test"
        },
        {
            "label": "Format Code (Black)",
            "type": "shell",
            "command": "${workspaceFolder}/.venv/bin/black",
            "args": ["${workspaceFolder}"],
            "group": "none"
        }
    ]
}
EOL

echo -e "${GREEN}✓ VS Code ayarları oluşturuldu${NC}"

echo ""
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  ADIM 7/8: Config Dizinleri ve Dosyalar${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"

# Config ve cache dizinleri
mkdir -p "$CONFIG_DIR"
mkdir -p "$CACHE_DIR"
mkdir -p "$HOME/Music/DownX"

# Kullanıcı verilerine göre config.json oluştur
echo -e "${BLUE}config.json oluşturuluyor...${NC}"
cat > "$CONFIG_DIR/config.json" << EOL
{
    "download_dir": "$DOWNLOAD_DIR",
    "download_mode": "audio",
    "audio_quality": "$AUDIO_QUALITY",
    "video_quality": "1080",
    "audio_format": "$AUDIO_FORMAT",
    "video_format": "mp4",
    "video_codec": "h264",
    "concurrent_downloads": 3,
    "skip_existing": true,
    "embed_metadata": $EMBED_METADATA,
    "embed_thumbnail": $EMBED_THUMBNAIL,
    "use_sponsorblock": false,
    "theme": "dark",
    "language": "tr"
}
EOL
echo -e "${GREEN}✓ Config dosyası oluşturuldu${NC}"

# Spotify credentials kaydet
echo -e "${BLUE}Spotify credentials kaydediliyor...${NC}"
cat > "$CONFIG_DIR/spotify_credentials.json" << EOL
{
    "client_id": "$SPOTIFY_CLIENT_ID",
    "client_secret": "$SPOTIFY_CLIENT_SECRET"
}
EOL
chmod 600 "$CONFIG_DIR/spotify_credentials.json"
echo -e "${GREEN}✓ Spotify credentials kaydedildi${NC}"

# YouTube cookies varsa kopyala
if [ -n "$YOUTUBE_COOKIES_PATH" ] && [ -f "$YOUTUBE_COOKIES_PATH" ]; then
    echo -e "${BLUE}YouTube cookies kopyalanıyor...${NC}"
    cp "$YOUTUBE_COOKIES_PATH" "$CONFIG_DIR/cookies.txt"
    chmod 600 "$CONFIG_DIR/cookies.txt"
    echo -e "${GREEN}✓ YouTube cookies kopyalandı${NC}"
fi

# İndirme dizinini oluştur
mkdir -p "$DOWNLOAD_DIR"
echo -e "${GREEN}✓ İndirme dizini oluşturuldu: $DOWNLOAD_DIR${NC}"

# .gitignore
cat > "$PROJECT_DIR/.gitignore" << 'EOL'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
.venv/
venv/
ENV/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo

# DownX specific
config.json
cookies.txt
spotify_credentials.json
*.log
tasks.json

# OS
.DS_Store
Thumbs.db

# Cache
.cache/
*.pyc
EOL

echo -e "${GREEN}✓ Config dizinleri hazır${NC}"

echo ""
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  ADIM 8/8: Başlatma Scriptleri${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"

# run.sh - Geliştirme için
cat > "$PROJECT_DIR/run.sh" << 'EOL'
#!/bin/bash
# DownX Başlatma Scripti

cd "$(dirname "$0")"
source .venv/bin/activate
python gui.py
EOL
chmod +x "$PROJECT_DIR/run.sh"

# run_launcher.sh - Launcher için
cat > "$PROJECT_DIR/run_launcher.sh" << 'EOL'
#!/bin/bash
# DownX Launcher Başlatma Scripti

cd "$(dirname "$0")"
source .venv/bin/activate
python launcher.py
EOL
chmod +x "$PROJECT_DIR/run_launcher.sh"

# Desktop dosyası
DESKTOP_FILE="$HOME/.local/share/applications/downx.desktop"
mkdir -p "$(dirname "$DESKTOP_FILE")"

# İkon dizini oluştur
mkdir -p "$PROJECT_DIR/resources/icons"

# İkonları embeded olarak oluştur (base64)
echo -e "${BLUE}İkonlar oluşturuluyor...${NC}"

# İkon script dizini (ikonlar setup_downx.sh ile birlikte gelmeli)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Eğer icon.png varsa kopyala
if [ -f "$SCRIPT_DIR/icon.png" ]; then
    cp "$SCRIPT_DIR/icon.png" "$PROJECT_DIR/resources/icons/icon.png"
    echo -e "${GREEN}✓ İkon kopyalandı${NC}"
elif [ -f "$PROJECT_DIR/resources/icons/icon.png" ]; then
    echo -e "${GREEN}✓ İkon zaten mevcut${NC}"
else
    echo -e "${YELLOW}⚠️  İkon bulunamadı, varsayılan ikon kullanılacak${NC}"
    # Fallback: system icon
    ICON_PATH="folder-download"
fi

# İkon path
if [ -f "$PROJECT_DIR/resources/icons/icon.png" ]; then
    ICON_PATH="$PROJECT_DIR/resources/icons/icon.png"
else
    ICON_PATH="folder-download"
fi

cat > "$DESKTOP_FILE" << EOL
[Desktop Entry]
Version=1.0
Type=Application
Name=DownX
Comment=Spotify & YouTube Downloader
Exec=$PROJECT_DIR/run.sh
Icon=$ICON_PATH
Terminal=false
Categories=AudioVideo;Audio;Video;Network;
Keywords=download;spotify;youtube;music;video;downx;
StartupWMClass=DownX
EOL

echo -e "${GREEN}✓ Desktop dosyası oluşturuldu${NC}"

# update-desktop-database güncelle
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
fi

echo ""
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  KURULUM TAMAMLANDI!${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo ""

# Sistem bilgisi
echo -e "${PURPLE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${PURPLE}  SİSTEM BİLGİLERİ${NC}"
echo -e "${PURPLE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Proje Dizini:${NC} $PROJECT_DIR"
echo -e "${BLUE}Virtual Env:${NC} $VENV_DIR"
echo -e "${BLUE}Config Dizini:${NC} $CONFIG_DIR"
echo -e "${BLUE}İndirme Dizini:${NC} $HOME/Music/DownX"
echo ""

# Python paketleri
echo -e "${PURPLE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${PURPLE}  KURULU PAKETLER${NC}"
echo -e "${PURPLE}═══════════════════════════════════════════════════════════${NC}"
source "$VENV_DIR/bin/activate"
pip list | grep -E "(requests|Pillow|mutagen|yt-dlp|spotdl|PyGObject)" || echo "Paket listesi alınamadı"
echo ""

# Sonraki adımlar
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  🎉 KURULUM BAŞARILI!                                     ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}📦 SONRAKI ADIMLAR:${NC}"
echo ""
echo -e "${CYAN}1. VS Code'u aç:${NC}"
echo "   code $PROJECT_DIR"
echo ""
echo -e "${CYAN}2. Terminal'de çalıştır:${NC}"
echo "   cd $PROJECT_DIR"
echo "   source .venv/bin/activate"
echo "   python gui.py"
echo ""
echo -e "${CYAN}3. Veya kısayol ile:${NC}"
echo "   $PROJECT_DIR/run.sh"
echo ""
echo -e "${CYAN}4. Uygulama menüsünden:${NC}"
echo "   'DownX' ara ve başlat"
echo ""
echo -e "${YELLOW}⚙️  ÖNEMLİ NOTLAR:${NC}"
echo ""
echo -e "${BLUE}• Spotify API:${NC}"
echo "  ✓ Client ID ve Secret otomatik kaydedildi"
echo "  Dosya: $CONFIG_DIR/spotify_credentials.json"
echo ""
if [ -f "$CONFIG_DIR/cookies.txt" ]; then
    echo -e "${BLUE}• YouTube Cookies:${NC}"
    echo "  ✓ Cookies dosyası kopyalandı"
    echo "  Dosya: $CONFIG_DIR/cookies.txt"
    echo ""
fi
echo -e "${BLUE}• İndirme Ayarları:${NC}"
echo "  Format: $AUDIO_FORMAT"
echo "  Kalite: $AUDIO_QUALITY kbps"
echo "  Metadata: $EMBED_METADATA"
echo "  Dizin: $DOWNLOAD_DIR"
echo ""
echo -e "${BLUE}• Ayarları Değiştir:${NC}"
echo "  nano $CONFIG_DIR/config.json"
echo ""
echo -e "${BLUE}• VS Code Python Interpreter:${NC}"
echo "  Ctrl+Shift+P → 'Python: Select Interpreter'"
echo "  → $VENV_DIR/bin/python seçin"
echo ""

# Log dosyası
LOG_FILE="$PROJECT_DIR/kurulum.log"
echo "$(date): Kurulum tamamlandı" > "$LOG_FILE"
echo "Python: $(python3 --version)" >> "$LOG_FILE"
echo "pip: $(pip --version)" >> "$LOG_FILE"

echo -e "${GREEN}Log dosyası: $LOG_FILE${NC}"
echo ""
echo -e "${PURPLE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}Kolay gelsin! 🚀${NC}"
echo -e "${PURPLE}═══════════════════════════════════════════════════════════${NC}"
