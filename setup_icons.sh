#!/bin/bash
################################################################################
# DownX İkon Kurulum Scripti
# Mor renkli ikonları projeye kurar
################################################################################

set -e

# Renkler
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
PURPLE='\033[0;35m'
NC='\033[0m'

echo -e "${PURPLE}════════════════════════════════════════════════════════════${NC}"
echo -e "${PURPLE}  🎨 DownX İkon Kurulum${NC}"
echo -e "${PURPLE}════════════════════════════════════════════════════════════${NC}"
echo ""

# Proje dizini
PROJECT_DIR="$HOME/Source/DownX"

if [ ! -d "$PROJECT_DIR" ]; then
    echo -e "${RED}HATA: $PROJECT_DIR bulunamadı!${NC}"
    echo "Önce setup_downx.sh'yi çalıştırın."
    exit 1
fi

cd "$PROJECT_DIR"

# Resources dizini
mkdir -p resources/icons

echo -e "${BLUE}İkon dosyaları aranıyor...${NC}"

# Script dizini
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# İkon dosyaları
ICON_FILES=(
    "downx_icon_purple.png:icon.png"
    "downx_icon_512.png:icon_512.png"
    "downx_icon_256.png:icon_256.png"
    "downx_icon_128.png:icon_128.png"
    "downx_icon_64.png:icon_64.png"
    "downx_icon_48.png:icon_48.png"
    "downx_icon_32.png:icon_32.png"
    "downx_icon_16.png:icon_16.png"
)

FOUND=0
TOTAL=${#ICON_FILES[@]}

for file_pair in "${ICON_FILES[@]}"; do
    IFS=':' read -r source dest <<< "$file_pair"

    # Script dizininde ara
    if [ -f "$SCRIPT_DIR/$source" ]; then
        cp "$SCRIPT_DIR/$source" "resources/icons/$dest"
        echo -e "${GREEN}✓ $dest kopyalandı${NC}"
        ((FOUND++))
    # Downloads'ta ara
    elif [ -f "$HOME/Downloads/$source" ]; then
        cp "$HOME/Downloads/$source" "resources/icons/$dest"
        echo -e "${GREEN}✓ $dest kopyalandı (Downloads)${NC}"
        ((FOUND++))
    # Manuel path
    elif [ -f "$source" ]; then
        cp "$source" "resources/icons/$dest"
        echo -e "${GREEN}✓ $dest kopyalandı${NC}"
        ((FOUND++))
    else
        echo -e "${YELLOW}⚠️  $source bulunamadı${NC}"
    fi
done

# Logo (128x128)
if [ -f "resources/icons/icon_128.png" ]; then
    cp resources/icons/icon_128.png resources/logo.png
    echo -e "${GREEN}✓ logo.png oluşturuldu${NC}"
fi

echo ""
echo -e "${BLUE}Sonuç: $FOUND/$TOTAL ikon kuruldu${NC}"

if [ $FOUND -eq 0 ]; then
    echo ""
    echo -e "${RED}HATA: Hiç ikon bulunamadı!${NC}"
    echo ""
    echo -e "${YELLOW}İkonları şu klasöre kopyalayın:${NC}"
    echo "  $SCRIPT_DIR/"
    echo ""
    echo -e "${YELLOW}Veya şu komutu çalıştırın:${NC}"
    echo "  cp /path/to/downx_icon_*.png $SCRIPT_DIR/"
    echo ""
    exit 1
fi

# Desktop entry güncelle
DESKTOP_FILE="$HOME/.local/share/applications/downx.desktop"

if [ -f "$DESKTOP_FILE" ]; then
    echo ""
    echo -e "${BLUE}Desktop entry güncelleniyor...${NC}"

    # Icon satırını güncelle
    sed -i "s|^Icon=.*|Icon=$PROJECT_DIR/resources/icons/icon.png|" "$DESKTOP_FILE"

    echo -e "${GREEN}✓ Desktop entry güncellendi${NC}"

    # Cache güncelle
    if command -v update-desktop-database &> /dev/null; then
        update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
        echo -e "${GREEN}✓ Desktop database güncellendi${NC}"
    fi

    # KDE için
    if command -v kbuildsycoca5 &> /dev/null; then
        kbuildsycoca5 2>/dev/null || true
        echo -e "${GREEN}✓ KDE cache güncellendi${NC}"
    fi
fi

echo ""
echo -e "${PURPLE}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}🎉 İkon kurulumu tamamlandı!${NC}"
echo -e "${PURPLE}════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}Kurulu İkonlar:${NC}"
ls -lh resources/icons/ | grep -v "^total" | awk '{print "  " $9 " (" $5 ")"}'
echo ""
echo -e "${BLUE}Test:${NC}"
echo "  1. Uygulama menüsünü aç"
echo "  2. 'DownX' ara"
echo "  3. Mor ikonu göreceksin! 💜"
echo ""
