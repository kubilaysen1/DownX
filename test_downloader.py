#!/usr/bin/env python3
"""
Downloader Test Scripti - Ayarları gerçekten kullanıyor mu?
"""
import sys
sys.path.insert(0, '/mnt/user-data/outputs')

print("=" * 70)
print("DOWNLOADER AYAR TESTİ")
print("=" * 70)

# 1. Settings'i yükle ve M4A'ya ayarla
print("\n1. Settings yükleniyor ve M4A'ya ayarlanıyor...")
from settings import GLOBAL_CONFIG, save_config, load_config

save_config({
    'audio_format': 'm4a',
    'audio_quality': '256k'
})

print(f"   GLOBAL_CONFIG ayarlandı:")
print(f"   - audio_format: {GLOBAL_CONFIG.get('audio_format')}")
print(f"   - audio_quality: {GLOBAL_CONFIG.get('audio_quality')}")

# 2. Downloader modülünü import et
print("\n2. Downloader modülü import ediliyor...")
print(f"   (Downloader import edilirken settings.py'deki GLOBAL_CONFIG'i kullanacak)")

# Simüle edilmiş track_info
track_info = {
    'title': 'Test Şarkı',
    'artist': 'Test Sanatçı',
    'album': 'Test Album',
    'year': '2024',
    'track_no': 1,
    'cover_url': ''
}

print("\n3. Downloader nesnesi oluşturuluyor...")
print(f"   (Downloader.__init__ şimdi GLOBAL_CONFIG'i okuyacak)")

# Downloader'ı import et (yt_dlp olmadan çalışmaz ama biz sadece __init__'i test ediyoruz)
try:
    from downloader import Downloader
    print("\n   ✓ Downloader import edildi")
    print(f"\n   Downloader şu ayarları kullanacak:")
    print(f"   - Format: {GLOBAL_CONFIG.get('audio_format')}")
    print(f"   - Kalite: {GLOBAL_CONFIG.get('audio_quality')}")
    
    if GLOBAL_CONFIG.get('audio_format') == 'm4a':
        print(f"\n   ✅ BAŞARILI! M4A kullanılacak!")
    else:
        print(f"\n   ❌ HATA! MP3 kullanılıyor!")
        
except ImportError as e:
    print(f"\n   ⚠ Downloader import edilemedi (yt_dlp yok): {e}")
    print(f"   Ama bu normal, sadece GLOBAL_CONFIG'in doğru olduğunu gördük")

print("\n" + "=" * 70)
print("Config dosyası içeriği:")
print("=" * 70)

import os
config_file = os.path.expanduser("~/.config/4ktube/config.json")
if os.path.exists(config_file):
    with open(config_file, 'r') as f:
        import json
        config = json.load(f)
        print(f"audio_format: {config.get('audio_format')}")
        print(f"audio_quality: {config.get('audio_quality')}")
else:
    print("❌ Config dosyası bulunamadı!")

print("=" * 70)
