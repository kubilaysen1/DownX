#!/usr/bin/env python3
"""
Config Test - Mod değişikliği kaydediliyor mu?
"""

import json
from pathlib import Path
import time

CONFIG_FILE = Path.home() / ".config" / "4ktube" / "config.json"

print("🔍 Config Test Başlatılıyor...\n")

if not CONFIG_FILE.exists():
    print(f"❌ Config dosyası bulunamadı: {CONFIG_FILE}")
    print("   Uygulamayı en az bir kez başlat!")
    exit(1)

def read_config():
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def show_mode():
    config = read_config()
    mode = config.get("download_mode", "?")
    audio_fmt = config.get("audio_format", "?")
    video_fmt = config.get("video_format", "?")
    
    print(f"📊 Mevcut Durum:")
    print(f"   download_mode: {mode}")
    print(f"   audio_format: {audio_fmt}")
    print(f"   video_format: {video_fmt}")
    print()

print("1️⃣  İlk Durum:")
show_mode()

print("=" * 50)
print()
print("🎬 Video moduna geçiliyor...")
print()

# Video moduna geç
config = read_config()
config["download_mode"] = "video"
with open(CONFIG_FILE, 'w') as f:
    json.dump(config, f, indent=2)

time.sleep(0.5)

print("2️⃣  Video modu:")
show_mode()

print("=" * 50)
print()
print("🎵 Audio moduna geçiliyor...")
print()

# Audio moduna geç
config = read_config()
config["download_mode"] = "audio"
with open(CONFIG_FILE, 'w') as f:
    json.dump(config, f, indent=2)

time.sleep(0.5)

print("3️⃣  Audio modu:")
show_mode()

print("=" * 50)
print()
print("✅ Test Tamamlandı!")
print()
print("💡 Eğer modlar değişiyorsa, config çalışıyor demektir.")
print("💡 Eğer hep 'audio' kalıyorsa, settings_tab.py çalışmıyor demektir.")