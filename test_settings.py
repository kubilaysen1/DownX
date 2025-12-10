#!/usr/bin/env python3
"""
Ayar Sistemi Test Scripti
"""
import sys
import os

# Outputs klasörünü path'e ekle
sys.path.insert(0, '/mnt/user-data/outputs')

print("=" * 60)
print("AYAR SİSTEMİ TEST")
print("=" * 60)

# 1. Settings'i import et
print("\n1. Settings modülü yükleniyor...")
from settings import GLOBAL_CONFIG, save_config, load_config

print(f"   İlk durum:")
print(f"   - Format: {GLOBAL_CONFIG.get('audio_format')}")
print(f"   - Kalite: {GLOBAL_CONFIG.get('audio_quality')}")

# 2. M4A'ya değiştir
print("\n2. M4A'ya değiştiriliyor...")
save_config({
    'audio_format': 'm4a',
    'audio_quality': '256k'
})

# 3. Config'i yeniden yükle
print("\n3. Config yeniden yükleniyor...")
load_config()

print(f"   Güncel durum:")
print(f"   - Format: {GLOBAL_CONFIG.get('audio_format')}")
print(f"   - Kalite: {GLOBAL_CONFIG.get('audio_quality')}")

# 4. Simüle edilmiş indirme
print("\n4. İndirme simülasyonu...")
print(f"   Downloader şu ayarları kullanacak:")
print(f"   - audio_format = GLOBAL_CONFIG.get('audio_format') = '{GLOBAL_CONFIG.get('audio_format')}'")
print(f"   - audio_quality = GLOBAL_CONFIG.get('audio_quality') = '{GLOBAL_CONFIG.get('audio_quality')}'")

if GLOBAL_CONFIG.get('audio_format') == 'm4a':
    print(f"\n   ✅ BAŞARILI! M4A kullanılacak!")
else:
    print(f"\n   ❌ HATA! Hala MP3 kullanılıyor!")

print("\n" + "=" * 60)
print("Config dosyası içeriği:")
print("=" * 60)

config_file = os.path.expanduser("~/.config/4ktube/config.json")
if os.path.exists(config_file):
    with open(config_file, 'r') as f:
        print(f.read())
else:
    print("❌ Config dosyası bulunamadı!")

print("=" * 60)
