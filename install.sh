#!/bin/bash
################################################################################
# DownX - Tek Komut Kurulum (Linux)
# curl -fsSL https://raw.githubusercontent.com/[username]/DownX/main/install.sh | bash
################################################################################

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
PURPLE='\033[0;35m'
NC='\033[0m'

echo -e "${PURPLE}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║    ██████╗  ██████╗ ██╗    ██╗███╗   ██╗██╗  ██╗            ║"
echo "║    ██╔══██╗██╔═══██╗██║    ██║████╗  ██║╚██╗██╔╝            ║"
echo "║    ██║  ██║██║   ██║██║ █╗ ██║██╔██╗ ██║ ╚███╔╝             ║"
echo "║    ██║  ██║██║   ██║██║███╗██║██║╚██╗██║ ██╔██╗             ║"
echo "║    ██████╔╝╚██████╔╝╚███╔███╔╝██║ ╚████║██╔╝ ██╗            ║"
echo "║    ╚═════╝  ╚═════╝  ╚══╝╚══╝ ╚═╝  ╚═══╝╚═╝  ╚═╝            ║"
echo "║                                                               ║"
echo "║    Tek Komut Kurulum - Linux                                 ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

# Dizin belirle
INSTALL_DIR="$HOME/Source/DownX"
TEMP_DIR="/tmp/downx-install-$$"

echo -e "${BLUE}[1/4] Hazırlanıyor...${NC}"

# Geçici dizin
mkdir -p "$TEMP_DIR"
cd "$TEMP_DIR"

# Git var mı?
if command -v git &> /dev/null; then
    echo -e "${GREEN}✓ Git bulundu${NC}"
    USE_GIT=true
else
    echo -e "${YELLOW}⚠ Git bulunamadı, wget kullanılacak${NC}"
    USE_GIT=false
fi

echo ""
echo -e "${BLUE}[2/4] DownX indiriliyor...${NC}"

if [ "$USE_GIT" = true ]; then
    # Git ile klonla
    git clone --depth 1 https://github.com/[username]/DownX.git "$INSTALL_DIR"
    echo -e "${GREEN}✓ Repo klonlandı${NC}"
else
    # Wget ile indir
    REPO_ZIP="https://github.com/[username]/DownX/archive/refs/heads/main.zip"
    wget -q "$REPO_ZIP" -O downx.zip
    unzip -q downx.zip
    mkdir -p "$INSTALL_DIR"
    mv DownX-main/* "$INSTALL_DIR/"
    echo -e "${GREEN}✓ Dosyalar indirildi${NC}"
fi

echo ""
echo -e "${BLUE}[3/4] Kurulum scripti çalıştırılıyor...${NC}"
echo ""

cd "$INSTALL_DIR"

# Kurulum scriptini belirle
if [ -f "setup_downx.sh" ]; then
    SETUP_SCRIPT="setup_downx.sh"
elif [ -f "setup_linux.sh" ]; then
    SETUP_SCRIPT="setup_linux.sh"
else
    echo -e "${RED}✗ Kurulum scripti bulunamadı!${NC}"
    exit 1
fi

chmod +x "$SETUP_SCRIPT"
./"$SETUP_SCRIPT"

echo ""
echo -e "${BLUE}[4/4] Temizlik...${NC}"
rm -rf "$TEMP_DIR"

echo ""
echo -e "${PURPLE}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  🎉 DownX Kurulumu Tamamlandı!                                ║${NC}"
echo -e "${PURPLE}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}Çalıştırmak için:${NC}"
echo "  cd $INSTALL_DIR"
echo "  ./run.sh"
echo ""
echo -e "${CYAN}Veya uygulama menüsünden:${NC}"
echo "  'DownX' ara ve başlat"
echo ""
echo -e "${PURPLE}Kolay gelsin! 🚀${NC}"
echo ""
