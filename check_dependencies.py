import os
import requests
import shutil
import subprocess
import zipfile
import stat
import re
import threading
from gi.repository import GLib

# --- AYARLAR ---
YTDLP_URL = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
FFMPEG_ZIP_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
APP_DIR = os.path.dirname(os.path.abspath(__file__)) 

# İkili dosyaların isimleri
YTDLP_NAME = "yt-dlp.exe" if os.name == 'nt' else "yt-dlp"
FFMPEG_NAME = "ffmpeg.exe" if os.name == 'nt' else "ffmpeg"

YTDLP_PATH = os.path.join(APP_DIR, YTDLP_NAME)
FFMPEG_PATH = os.path.join(APP_DIR, FFMPEG_NAME)

def download_file(url, target_path, status_callback):
    """URL'den dosyayı indirir (Sadece Windows için çalışır)."""
    filename = os.path.basename(target_path)
    status_callback(f"İndiriliyor: {filename}...")
    try:
        if os.name != 'nt':
            # Linux'ta harici exe indirmeyi atla, sistemden almalıyız
            status_callback(f"⚠️ Linux/Diğer sistem: {filename} sistem PATH'inden bekleniyor.")
            return False 

        for attempt in range(3):
            with requests.get(url, stream=True, timeout=10) as r:
                r.raise_for_status()
                with open(target_path, 'wb') as f:
                    shutil.copyfileobj(r.raw, f)
            
            os.chmod(target_path, os.stat(target_path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            status_callback(f"-> {filename} başarıyla indirildi.")
            return True
    except Exception as e:
        status_callback(f"❌ İndirme Hatası ({filename}): {e}")
        return False

def is_command_available(name):
    """Komutun PATH'te mevcut olup olmadığını kontrol eder (Linux için)."""
    return shutil.which(name) is not None

def check_and_download_ffmpeg(status_callback):
    """FFmpeg'i kontrol eder ve indirir/ayıklar."""
    if os.name == 'nt':
        # Windows için otomatik indir (Yukarıdaki download_file içindeki logic)
        if os.path.exists(FFMPEG_PATH):
            status_callback("✅ FFmpeg.exe mevcut.")
            return True

        status_callback("⚠️ FFmpeg eksik. İndiriliyor...")
        temp_zip = os.path.join(APP_DIR, "ffmpeg_temp.zip")
        
        if not download_file(FFMPEG_ZIP_URL, temp_zip, status_callback):
            return False

        try:
            status_callback("Zip arşivinden çıkarılıyor...")
            with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                for member in zip_ref.namelist():
                    if member.endswith('bin/ffmpeg.exe'):
                        with zip_ref.open(member) as source, open(FFMPEG_PATH, "wb") as target:
                            shutil.copyfileobj(source, target)
                        break
            os.remove(temp_zip)
            os.chmod(FFMPEG_PATH, os.stat(FFMPEG_PATH).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            status_callback("✅ FFmpeg başarıyla kuruldu.")
            return True
        except Exception as e:
            status_callback(f"❌ FFmpeg ayıklama hatası: {e}")
            if os.path.exists(temp_zip): os.remove(temp_zip)
            return False
    else:
        # Linux için PATH kontrolü
        if is_command_available('ffmpeg'):
            status_callback("✅ FFmpeg sistemde mevcut.")
            return True
        else:
            status_callback("❌ FFmpeg sistemde eksik. Lütfen kurun (örn: sudo dnf install ffmpeg).")
            return False

def check_and_download_ytdlp(status_callback):
    """yt-dlp'yi kontrol eder ve indirir."""
    if os.name == 'nt':
        # Windows için otomatik indir
        if os.path.exists(YTDLP_PATH):
            status_callback("✅ yt-dlp.exe mevcut.")
            return True
        return download_file(YTDLP_URL, YTDLP_PATH, status_callback)
    else:
        # Linux için PATH kontrolü
        if is_command_available('yt-dlp'):
            status_callback("✅ yt-dlp sistemde mevcut.")
            return True
        else:
            status_callback("❌ yt-dlp sistemde eksik. Lütfen kurun (örn: pip install yt-dlp).")
            return False

def run_dependency_check(finished_callback, status_callback):
    """Tüm bağımlılıkları arka planda kontrol eder ve tamamlandığında UI'ı günceller."""
    
    # UI'a durumu ana thread'den göndermek için GLib kullan
    def ui_status(msg):
        GLib.idle_add(status_callback, msg)

    ui_status("--- Harici Bağımlılık Kontrolü Başladı ---")
    
    ytdlp_ok = check_and_download_ytdlp(ui_status)
    ffmpeg_ok = check_and_download_ffmpeg(ui_status)
    
    if ytdlp_ok and ffmpeg_ok:
        ui_status("🎉 Tüm bağımlılıklar hazır.")
        GLib.idle_add(finished_callback, True)
    else:
        ui_status("❌ HATA: Kritik bağımlılıklar eksik kaldı. Uygulama düzgün çalışmayabilir.")
        GLib.idle_add(finished_callback, True) # Başarısız olsa bile UI'ı aç, durumu göster