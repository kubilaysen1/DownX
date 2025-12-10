"""
4KTube Free - Queue Manager
Spotify ve YouTube indirme kuyruğunu yönetir.
"""

import threading
import time
import os
import sys
import subprocess
import uuid
import glob
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

from gi.repository import GLib
from settings import GLOBAL_CONFIG, get_download_dir


def sanitize_filename(name):
    """Dosya/klasör adı için güvenli karakter"""
    if not name:
        return "Unknown"
    clean = re.sub(r'[<>:"/\\|?*]', '', str(name))
    clean = clean.strip('. ')
    return clean[:100] if clean else "Unknown"


class QueueManager:
    def __init__(self, main_window, spotify_client=None, youtube_client=None):
        self.main_window = main_window
        self.spotify_client = spotify_client
        self.youtube_client = youtube_client
        
        self.queue = []
        self.selected_indices = set()
        self.lock = threading.RLock()
        
        self.is_downloading = False
        self.stop_requested = False
        
        print(f"[QUEUE] Başlatıldı")

    # ========================================
    # BÖLÜM 1: KUYRUĞA EKLEME
    # ========================================
    
    def add_url_to_queue(self, url: str, is_playlist=False, clear_queue=True, batch_name=None):
        """URL'yi arka planda işle ve kuyruğa ekle"""
        if not url or not url.strip():
            return
        threading.Thread(
            target=self._add_url_worker,
            args=(url.strip(), is_playlist, clear_queue, batch_name),
            daemon=True
        ).start()

    def _add_url_worker(self, url, is_playlist, clear_queue, batch_name=None):
        """URL işleme worker thread"""
        print(f"\n[QUEUE] URL alındı: {url[:60]}...")
        
        is_spotify = "spotify.com" in url or "spotify.link" in url
        is_youtube = "youtube.com" in url or "youtu.be" in url
        
        new_items = []
        
        try:
            if is_spotify:
                new_items = self._parse_spotify_url(url)
            elif is_youtube:
                new_items = self._parse_youtube_url(url, batch_name=batch_name)
            
            if not new_items:
                print(f"[QUEUE] API'den veri alınamadı, ham URL ekleniyor")
                new_items.append({
                    "id": str(uuid.uuid4()),
                    "type": "spotify" if is_spotify else "youtube",
                    "url": url,
                    "title": "Bilinmeyen Parça",
                    "artist": "Bilinmeyen",
                    "album": "Tekli",
                    "status": "Beklemede",
                    "is_playlist": False
                })

            with self.lock:
                if clear_queue:
                    self.queue.clear()
                    self.selected_indices.clear()
                
                start_idx = len(self.queue)
                self.queue.extend(new_items)
                
                for i in range(start_idx, start_idx + len(new_items)):
                    self.selected_indices.add(i)
            
            print(f"[QUEUE] ✓ {len(new_items)} parça eklendi. Toplam kuyruk: {len(self.queue)}")
            self._update_ui()
            
        except Exception as e:
            print(f"[QUEUE] HATA: {e}")
            import traceback
            traceback.print_exc()

    def _parse_spotify_url(self, url):
        """Spotify URL'sinden parça listesi çıkar"""
        items = []
        
        if not self.spotify_client or not self.spotify_client.sp:
            print("[SPOTIFY] Client bağlı değil, ham URL kullanılacak")
            return items
        
        try:
            print("[SPOTIFY] API'den veri çekiliyor...")
            info = self.spotify_client.get_content_info(url)
            
            if not info:
                print("[SPOTIFY] API boş döndü")
                return items
            
            playlist_name = sanitize_filename(info.get('title', 'Spotify'))
            tracks = info.get('tracks', [])
            
            print(f"[SPOTIFY] '{playlist_name}' - {len(tracks)} parça bulundu")
            
            for i, track in enumerate(tracks):
                track_url = track.get('url', '')
                
                item = {
                    "id": str(uuid.uuid4()),
                    "type": "spotify",
                    "url": track_url if track_url else url,
                    "title": sanitize_filename(track.get('title', 'Bilinmeyen')),
                    "artist": sanitize_filename(track.get('artist', 'Bilinmeyen')),
                    "album": playlist_name,
                    "cover_url": track.get('cover_url', ''),
                    "year": track.get('year', ''),
                    "track_no": track.get('track_no', i + 1),
                    "status": "Beklemede",
                    "is_playlist": len(tracks) > 1
                }
                items.append(item)
                
        except Exception as e:
            print(f"[SPOTIFY] Parse hatası: {e}")
        
        return items

    def _parse_youtube_url(self, url, batch_name=None):
        """YouTube URL'sinden video listesi çıkar"""
        items = []
        
        # Playlist mi tekli video mu kontrol et
        is_playlist = "list=" in url or "/playlist" in url
        
        if is_playlist and self.youtube_client:
            # Playlist için youtube_client kullan
            try:
                print("[YOUTUBE] Playlist API'den veri çekiliyor...")
                tracks = self.youtube_client.get_playlist_tracks_meta(url)
                
                if tracks:
                    playlist_name = sanitize_filename(
                        tracks[0].get('playlist_title', 'YouTube Playlist')
                    )
                    
                    print(f"[YOUTUBE] '{playlist_name}' - {len(tracks)} video bulundu")
                    
                    for t in tracks:
                        items.append({
                            "id": str(uuid.uuid4()),
                            "type": "youtube",
                            "url": t.get('url', url),
                            "title": sanitize_filename(t.get('title', 'Video')),
                            "artist": sanitize_filename(t.get('channel', 'YouTube')),
                            "album": playlist_name,
                            "cover_url": t.get('thumbnail') or t.get('cover_url', ''),
                            "status": "Beklemede",
                            "is_playlist": True
                        })
                    return items
            except Exception as e:
                print(f"[YOUTUBE] Playlist parse hatası: {e}")
        
        # Tekli video için yt-dlp ile başlık çek
        try:
            import yt_dlp
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
                'skip_download': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if info:
                    title = info.get('title', 'YouTube Video')
                    channel = info.get('uploader', 'YouTube')
                    thumbnail = info.get('thumbnail', '')
                    
                    print(f"[YOUTUBE] Tekli video: {title[:50]}...")
                    
                    # Eğer batch_name varsa (TXT'den yüklendiyse) onu kullan
                    album_name = batch_name if batch_name else "Tekli"
                    
                    items.append({
                        "id": str(uuid.uuid4()),
                        "type": "youtube",
                        "url": url,
                        "title": sanitize_filename(title),
                        "artist": sanitize_filename(channel),
                        "album": sanitize_filename(album_name),
                        "cover_url": thumbnail,
                        "status": "Beklemede",
                        "is_playlist": bool(batch_name)  # TXT'den geliyorsa True
                    })
                    return items
                    
        except Exception as e:
            print(f"[YOUTUBE] Tekli video parse hatası: {e}")
        
        # Fallback: Başlık çekilemezse ham URL ekle
        album_name = batch_name if batch_name else "Tekli"
        
        items.append({
            "id": str(uuid.uuid4()),
            "type": "youtube",
            "url": url,
            "title": "Bilinmeyen Video",
            "artist": "YouTube",
            "album": sanitize_filename(album_name),
            "status": "Beklemede",
            "is_playlist": bool(batch_name)
        })
        
        return items

    # ========================================
    # BÖLÜM 2: İNDİRME KONTROLÜ
    # ========================================
    
    def start_downloads(self):
        """İndirmeleri başlat"""
        if self.is_downloading:
            print("[DOWNLOAD] Zaten indirme yapılıyor")
            return
        
        if not self.selected_indices:
            GLib.idle_add(self.main_window.status_label.set_text, "⚠️ Parça seçin!")
            return
        
        self.is_downloading = True
        self.stop_requested = False
        
        threading.Thread(target=self._download_worker, daemon=True).start()

    def stop_downloads(self):
        """İndirmeleri durdur"""
        print("[DOWNLOAD] Durdurma isteği alındı")
        self.stop_requested = True

    def _download_worker(self):
        """Ana indirme worker thread"""
        print(f"\n{'='*70}")
        print(f"[DOWNLOAD] İndirme başlatıldı")
        print(f"{'='*70}\n")
        
        try:
            max_concurrent = GLOBAL_CONFIG.get("max_concurrent_downloads", 3)
            
            with self.lock:
                selected_items = [
                    self.queue[i] for i in sorted(self.selected_indices)
                    if i < len(self.queue)
                ]
            
            if not selected_items:
                print("[DOWNLOAD] İndirilecek parça yok")
                return
            
            print(f"[DOWNLOAD] {len(selected_items)} parça indirilecek ({max_concurrent} eşzamanlı)")
            
            with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
                futures = {
                    executor.submit(self._download_single_item, item): item
                    for item in selected_items
                }
                
                for future in as_completed(futures):
                    if self.stop_requested:
                        print("[DOWNLOAD] Kullanıcı tarafından durduruldu")
                        executor.shutdown(wait=False, cancel_futures=True)
                        break
                    
                    item = futures[future]
                    try:
                        success = future.result(timeout=300)
                        if success:
                            print(f"[DOWNLOAD] ✓ {item.get('title', '?')}")
                        else:
                            print(f"[DOWNLOAD] ✗ {item.get('title', '?')}")
                    except Exception as e:
                        print(f"[DOWNLOAD] Exception: {item.get('title', '?')} - {e}")
            
            print(f"\n{'='*70}")
            print(f"[DOWNLOAD] İndirme tamamlandı")
            print(f"{'='*70}\n")
            
        except Exception as e:
            print(f"[DOWNLOAD] Kritik hata: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            self.is_downloading = False
            self._update_ui()

    def _download_single_item(self, item):
        """Tek item indir (Spotify veya YouTube)"""
        if self.stop_requested:
            return False
        
        try:
            # Dosya kontrolü
            skip_existing = GLOBAL_CONFIG.get("skip_existing", True)
            if skip_existing and self._check_file_exists(item):
                print(f"[SKIP] Mevcut: {item.get('title')}")
                item["status"] = "Atlandı (Mevcut)"
                self._update_ui()
                return True
            
            # İndirme
            item_type = item.get("type", "youtube")
            
            if item_type == "spotify":
                return self._download_spotify_track(item)
            else:
                return self._download_youtube_track(item)
                
        except Exception as e:
            print(f"[DOWNLOAD] Hata: {item.get('title')} - {e}")
            item["status"] = "Hata"
            self._update_ui()
            return False

    # ========================================
    # BÖLÜM 3: SPOTIFY İNDİRME (SpotDL)
    # ========================================
    
    def _download_spotify_track(self, item):
        """SpotDL ile Spotify parça indir"""
        try:
            # MODE KONTROLÜ - Spotify sadece ses indirir!
            mode = GLOBAL_CONFIG.get("mode", "audio")
            if mode != "audio":
                print(f"[SPOTDL] ⚠️ Spotify sadece ses indirebilir! Mode 'audio' olarak ayarlandı.")
                # Video istiyorsan YouTube kullan
            
            # 1. Hedef Klasör
            download_dir = get_download_dir()
            album_name = item.get("album", "Spotify")
            
            if item.get("is_playlist") and album_name and album_name not in ["Tekli", "Spotify"]:
                folder_name = sanitize_filename(album_name)
                target_dir = os.path.join(download_dir, folder_name)
            else:
                target_dir = download_dir
            
            os.makedirs(target_dir, exist_ok=True)
            
            # 2. URL Kontrolü
            url = item.get("url", "")
            if not url or ("spotify.com" not in url and "spotify:" not in url):
                print(f"[SPOTDL] ⛔ Geçersiz URL: {url}")
                GLib.idle_add(self._handle_worker_finish, False, "Geçersiz Link", item["id"])
                return False

            # 3. Format Ayarları (lowercase + None check)
            audio_format = GLOBAL_CONFIG.get("audio_format", "mp3")
            if audio_format is None:
                audio_format = "mp3"
            audio_format = audio_format.lower()
            
            # KRİTİK: SpotDL sadece mp3, flac, ogg, opus, m4a, wav destekler
            # AAC seçilmişse M4A'ya çevir
            if audio_format == "aac":
                audio_format = "m4a"
                print(f"[SPOTDL] Format AAC -> M4A'ya çevrildi (SpotDL uyumluluğu)")
            
            # SpotDL desteklemeyen formatlar
            if audio_format not in ["mp3", "flac", "ogg", "opus", "m4a", "wav"]:
                print(f"[SPOTDL] ⚠️ Desteklenmeyen format: {audio_format}, MP3 kullanılacak")
                audio_format = "mp3"
            
            # Bitrate Ayarı (SpotDL '128k' formatında ister)
            config_quality = GLOBAL_CONFIG.get("audio_quality", "192")
            if config_quality is None:
                config_quality = "192"
            # String'e çevir (integer olabilir)
            config_quality = str(config_quality)
            # Sadece sayı varsa 'k' ekle
            if config_quality.isdigit():
                config_quality = f"{config_quality}k"
            elif not config_quality.endswith("k"):
                config_quality += "k"
            
            # 4. Output Şablonu
            abs_target_dir = os.path.abspath(target_dir)
            output_template = os.path.join(abs_target_dir, "{artist} - {title}.{output-ext}")
            
            # 5. SpotDL Komutu
            cmd = [
                sys.executable, "-m", "spotdl", 
                "download",
                url,
                "--output", output_template,
                "--format", audio_format,
                "--bitrate", config_quality,
                "--overwrite", "skip" if GLOBAL_CONFIG.get("skip_existing", True) else "force",
                "--simple-tui"
            ]

            print(f"[SPOTDL] Komut: {cmd}")
            print(f"[SPOTDL] Format: {audio_format}, Bitrate: {config_quality}")

            # 6. Subprocess Başlat
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                encoding='utf-8',
                startupinfo=startupinfo
            )

            # 7. Çıktıyı Canlı Oku
            while True:
                line = process.stdout.readline()
                
                if not line and process.poll() is not None:
                    break
                
                if line:
                    clean = line.strip()
                    if "Downloading" in clean:
                        GLib.idle_add(self._update_queue_progress, item["id"], 50.0, "İndiriliyor...")
                    elif "Converting" in clean:
                        GLib.idle_add(self._update_queue_progress, item["id"], 90.0, "Dönüştürülüyor...")
                    elif "Found" in clean:
                        GLib.idle_add(self._update_queue_progress, item["id"], 10.0, "Bulundu...")
            
            stderr_out = process.stderr.read()
            
            # 8. Sonuç Analizi
            if process.returncode == 0:
                print(f"[SPOTDL] ✓ Tamamlandı: {item.get('title')}")
                GLib.idle_add(self._handle_worker_finish, True, "Tamamlandı", item["id"])
                return True
            else:
                print(f"[SPOTDL] Hata Kodu: {process.returncode}")
                if stderr_out: 
                    print(f"[SPOTDL] Hata: {stderr_out[:500]}")
                
                # Dosya inmiş mi kontrol et
                expected_partial = sanitize_filename(item.get('title', ''))[:10]
                if expected_partial:
                    search_pattern = os.path.join(target_dir, f"*{expected_partial}*.{audio_format}")
                    if glob.glob(search_pattern):
                        print("[SPOTDL] Dosya bulundu, başarılı sayılıyor")
                        GLib.idle_add(self._handle_worker_finish, True, "Tamamlandı", item["id"])
                        return True

                GLib.idle_add(self._handle_worker_finish, False, "Hata", item["id"])
                return False

        except Exception as e:
            print(f"[SPOTDL] Kritik Hata: {e}")
            import traceback
            traceback.print_exc()
            GLib.idle_add(self._handle_worker_finish, False, "Hata", item["id"])
            return False
            
    # ========================================
    # BÖLÜM 4: YOUTUBE İNDİRME
    # ========================================
    
    def _download_youtube_track(self, item):
        """Tek bir YouTube videosunu indir"""
        try:
            item["status"] = "İndiriliyor..."
            self._update_ui()
            
            from downloader import Downloader
            
            url = item.get("url", "")
            if not url:
                item["status"] = "Hata: URL yok"
                return False
            
            print(f"[YTDLP] İndiriliyor: {item.get('title')}")
            
            done = threading.Event()
            result = {"success": False}
            
            def on_progress(pct, msg):
                item["status"] = f"%{int(pct)}"
            
            def on_done(success, msg):
                result["success"] = success
                done.set()
            
            dl = Downloader(url, item, on_progress, on_done)
            dl.start()
            
            done.wait(timeout=300)
            
            if result["success"]:
                print(f"[YTDLP] ✓ OK: {item.get('title')}")
            else:
                print(f"[YTDLP] ✗ Hata: {item.get('title')}")
                
            return result["success"]
            
        except Exception as e:
            print(f"[YTDLP] Exception: {e}")
            item["status"] = "Hata"
            return False

    # ========================================
    # BÖLÜM 5: YARDIMCI METOTLAR
    # ========================================
    
    def _check_file_exists(self, item):
        """Dosya zaten var mı kontrol et"""
        try:
            title = item.get("title", "")
            artist = item.get("artist", "")
            
            if not title or title in ["Bilinmeyen", "Bilinmeyen Parça", "Unknown"]:
                return False
            if not artist or artist in ["Bilinmeyen", "Unknown"]:
                return False
            
            download_dir = get_download_dir()
            
            search_name = f"{artist} - {title}"
            
            for root, dirs, files in os.walk(download_dir):
                for f in files:
                    ext = os.path.splitext(f)[1].lower()
                    if ext not in ['.mp3', '.m4a', '.opus', '.flac', '.wav', '.ogg']:
                        continue
                    
                    fname = os.path.splitext(f)[0].lower()
                    if title.lower() in fname and artist.lower() in fname:
                        full_path = os.path.join(root, f)
                        print(f"[CHECK] Mevcut bulundu: {full_path}")
                        return True
            
            return False
        except Exception as e:
            print(f"[CHECK] Hata: {e}")
            return False

    def _get_item_by_id(self, item_id):
        """ID ile item bul"""
        with self.lock:
            for item in self.queue:
                if item.get("id") == item_id:
                    return item
        return None

    def _update_ui(self):
        """UI güncelle"""
        if hasattr(self.main_window, 'downloads_tab'):
            GLib.idle_add(self.main_window.downloads_tab.update_downloads_page_content)

    def _update_queue_progress(self, item_id, percent, message):
        """Progress güncelle"""
        item = self._get_item_by_id(item_id)
        if item:
            item["status"] = message
        self._update_ui()

    def _handle_worker_finish(self, success, message, item_id):
        """İndirme bittiğinde"""
        item = self._get_item_by_id(item_id)
        if item:
            item["status"] = "Tamamlandı" if success else "Hata"
        self._update_ui()