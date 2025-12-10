#!/usr/bin/env python3
"""
DownX - Modern Video/Audio Downloader
Version: 2.1.0 - Ultra Dark Theme
"""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, GdkPixbuf, Pango

import os
import sys
import json
import shutil
import threading
import subprocess
import logging
import time
import hashlib
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
from typing import Optional, Dict, List, Any, Tuple
from queue import Queue, Empty
from dataclasses import dataclass, field
from enum import Enum

# Settings'ten güncel değişkenleri import et
from settings import (
    COOKIES_FILE, update_download_dir,
    GLOBAL_CONFIG, save_config, get_download_dir, load_config
)

# Diğer modülleri import et
from youtube_client import YouTubeClient
from downloader import Downloader
from search_tab import SearchTab
from settings_tab import SettingsTab
from downloads_tab import DownloadsTab
from tools_tab import ToolsTab
from spotify_client import SpotifyClient
from check_dependencies import run_dependency_check

# Resim yükleme kütüphaneleri
try:
    import requests
    from PIL import Image, ImageFilter, ImageEnhance
    IMAGING_AVAILABLE = True
except ImportError:
    print("⚠️ Görsel özellikler için 'requests' ve 'Pillow' kurulu olmalı")
    requests = None
    Image = None
    IMAGING_AVAILABLE = False


# ========== DEFAULT CSS - ESKİ GÜZEL RENKLER ==========
DEFAULT_CSS = """
* {
    color: #e8e8e8;
}

window {
    background: linear-gradient(135deg, #2b2d42 0%, #3d405b 50%, #2b2d42 100%);
    color: #ffffff;
}

box, scrolledwindow, viewport {
    background-color: transparent;
    color: #e8e8e8;
}

/* TreeView ve Liste arka planları */
treeview, list, listbox {
    background-color: rgba(43, 45, 66, 0.6);
    color: #e8e8e8;
}

treeview:selected, list:selected, row:selected {
    background-color: rgba(94, 158, 255, 0.3);
}

/* TextView beyaz alan düzeltme */
textview, textview text {
    background-color: rgba(43, 45, 66, 0.8);
    color: #e8e8e8;
}

/* Frame içerikleri */
frame > border {
    background-color: rgba(43, 45, 66, 0.4);
}

/* Scrollbar */
scrollbar {
    background-color: rgba(43, 45, 66, 0.3);
}

scrollbar slider {
    background-color: rgba(255, 255, 255, 0.2);
    border-radius: 10px;
}

scrollbar slider:hover {
    background-color: rgba(255, 255, 255, 0.3);
}

.titlebar {
    background: linear-gradient(180deg, #3d405b 0%, #2b2d42 100%);
    border-bottom: 1px solid rgba(255,255,255,0.15);
    min-height: 56px;
}

.titlebar-button {
    background: rgba(255,255,255,0.12);
    border: none;
    border-radius: 8px;
    padding: 8px 14px;
    min-width: 36px;
    min-height: 36px;
}

.titlebar-button:hover {
    background: rgba(255,255,255,0.2);
}

.tab-bar {
    background: linear-gradient(180deg, #3d405b 0%, #2b2d42 100%);
    border-bottom: 1px solid rgba(255,255,255,0.12);
    min-height: 50px;
    padding: 6px 0;
}

.tab-button {
    background: transparent;
    border: none;
    border-radius: 10px 10px 0 0;
    padding: 14px 26px;
    margin: 6px 3px 0 3px;
    color: #b8bcc8;
    font-size: 13px;
    font-weight: 500;
    min-width: 130px;
}

.tab-button:hover {
    background: rgba(255,255,255,0.08);
    color: #eaeaea;
}

.tab-button.tab-active {
    background: linear-gradient(180deg, #2b2d42 0%, #252736 100%);
    color: #ffffff;
    font-weight: 600;
    border: 1px solid rgba(255,255,255,0.15);
    border-bottom: none;
    box-shadow: 0 -3px 12px rgba(0,0,0,0.4);
}

.tab-button.tab-active:hover {
    background: linear-gradient(180deg, #2b2d42 0%, #252736 100%);
}

.tab-button image {
    opacity: 0.75;
}

.tab-button.tab-active image {
    opacity: 1;
}

entry {
    background-color: rgba(61, 64, 91, 0.5);
    color: #ffffff;
    border: 1px solid rgba(255,255,255,0.25);
    border-radius: 10px;
    padding: 10px 14px;
    min-height: 40px;
}

entry:focus {
    background-color: rgba(61, 64, 91, 0.7);
    border-color: #5e9eff;
    box-shadow: 0 0 0 3px rgba(94,158,255,0.25);
}

combobox, combobox > * {
    background-color: rgba(61, 64, 91, 0.5);
    color: #ffffff;
    border: 1px solid rgba(255,255,255,0.25);
}

combobox button {
    background-color: rgba(61, 64, 91, 0.5);
}

label {
    color: #e8e8e8;
}

button {
    background: linear-gradient(135deg, rgba(255,255,255,0.12), rgba(255,255,255,0.08));
    background-image: none;
    color: #ffffff;
    border: 1px solid rgba(255,255,255,0.20);
    border-radius: 8px;
    padding: 10px 18px;
}

button:hover {
    background: linear-gradient(135deg, rgba(255,255,255,0.18), rgba(255,255,255,0.12));
    border-color: rgba(255,255,255,0.35);
    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
}

.quick-action-btn {
    background: linear-gradient(135deg, rgba(94,158,255,0.15), rgba(94,158,255,0.10));
    background-image: none;
    color: #ffffff;
    border: 1px solid rgba(94,158,255,0.3);
    border-radius: 12px;
    padding: 14px 28px;
    min-height: 54px;
    box-shadow: 0 4px 12px rgba(94,158,255,0.15);
}

.quick-action-btn:hover {
    background: linear-gradient(135deg, rgba(94,158,255,0.25), rgba(94,158,255,0.18));
    border-color: #5e9eff;
    box-shadow: 0 6px 16px rgba(94,158,255,0.25);
}

switch {
    background-color: rgba(255,255,255,0.15);
}

switch:checked {
    background-color: #5e9eff;
}

.status-bar {
    background: linear-gradient(90deg, rgba(0,0,0,0.5), rgba(0,0,0,0.3));
    padding: 10px 18px;
    border-top: 1px solid rgba(255,255,255,0.12);
    min-height: 42px;
}

.loading-container {
    background: radial-gradient(ellipse at center, #2b2d42 0%, #1a1c2e 100%);
}

.notification {
    padding: 16px 20px;
    border-radius: 14px;
    margin: 8px;
    box-shadow: 0 6px 24px rgba(0,0,0,0.5);
    border: 1px solid rgba(255,255,255,0.15);
}

.notification.info {
    background: linear-gradient(135deg, rgba(94,158,255,0.96), rgba(74,138,235,0.96));
}

.notification.success {
    background: linear-gradient(135deg, rgba(34,197,94,0.96), rgba(22,163,74,0.96));
}

.notification.warning {
    background: linear-gradient(135deg, rgba(251,191,36,0.96), rgba(245,158,11,0.96));
    color: #1a1c2e;
}

.notification.error {
    background: linear-gradient(135deg, rgba(239,68,68,0.96), rgba(220,38,38,0.96));
}

progressbar {
    min-height: 22px;
    border-radius: 12px;
}

progressbar trough {
    background-color: rgba(255,255,255,0.12);
    border-radius: 12px;
}

progressbar progress {
    background: linear-gradient(90deg, #5e9eff, #7eb3ff, #5e9eff);
    background-size: 200% 100%;
    border-radius: 12px;
    box-shadow: 0 3px 12px rgba(94,158,255,0.5);
}

.search-box {
    background-color: rgba(61, 64, 91, 0.5);
    border-radius: 25px;
    padding: 10px 18px;
    border: 2px solid rgba(255,255,255,0.15);
    min-height: 42px;
}

.search-box:focus-within {
    background-color: rgba(61, 64, 91, 0.7);
    border-color: #5e9eff;
    box-shadow: 0 0 0 3px rgba(94,158,255,0.2);
}

/* Spinbutton arka planı */
spinbutton {
    background-color: rgba(61, 64, 91, 0.5);
    border: 1px solid rgba(255,255,255,0.25);
}

spinbutton entry {
    background-color: transparent;
}

/* CheckButton arka planı */
checkbutton {
    background-color: transparent;
}

checkbutton check {
    background-color: rgba(255,255,255,0.1);
    border: 1px solid rgba(255,255,255,0.3);
}

checkbutton:checked check {
    background-color: #5e9eff;
}
"""


# İndirme durumu enum'u
class DownloadStatus(Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


# İndirme veri sınıfı
@dataclass
class DownloadItem:
    """İndirme öğesi veri sınıfı"""
    id: str
    url: str
    title: str = "Bilinmeyen Video"
    channel: str = "Bilinmeyen Kanal"
    duration: str = "00:00"
    quality: str = "best"
    format: str = "mp4"
    thumbnail_url: Optional[str] = None
    thumbnail_pixbuf: Optional[GdkPixbuf.Pixbuf] = None
    file_size: int = 0
    downloaded_size: int = 0
    progress: float = 0.0
    speed: str = "0 KB/s"
    eta: str = "Hesaplanıyor..."
    status: DownloadStatus = DownloadStatus.PENDING
    error_message: Optional[str] = None
    file_path: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class NotificationManager:
    """Bildirim yöneticisi"""

    def __init__(self, parent_window):
        self.parent = parent_window
        self.notifications = []
        self.notification_box = None
        self.setup_notification_area()

    def setup_notification_area(self):
        """Bildirim alanını oluştur"""
        self.notification_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.notification_box.set_halign(Gtk.Align.END)
        self.notification_box.set_valign(Gtk.Align.START)
        self.notification_box.set_margin_top(60)
        self.notification_box.set_margin_end(20)

    def show(self, message: str, notification_type: str = "info", duration: int = 3000):
        """Bildirim göster"""
        notification = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        notification.get_style_context().add_class("notification")
        notification.get_style_context().add_class(notification_type)
        notification.set_size_request(300, -1)

        icon_names = {
            "info": "dialog-information-symbolic",
            "success": "emblem-ok-symbolic",
            "warning": "dialog-warning-symbolic",
            "error": "dialog-error-symbolic"
        }
        icon = Gtk.Image.new_from_icon_name(
            icon_names.get(notification_type, "dialog-information-symbolic"),
            Gtk.IconSize.BUTTON
        )
        notification.pack_start(icon, False, False, 0)

        label = Gtk.Label(label=message)
        label.set_line_wrap(True)
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        label.set_max_width_chars(40)
        notification.pack_start(label, True, True, 0)

        close_btn = Gtk.Button()
        close_btn.set_relief(Gtk.ReliefStyle.NONE)
        close_icon = Gtk.Image.new_from_icon_name("window-close-symbolic", Gtk.IconSize.SMALL_TOOLBAR)
        close_btn.add(close_icon)
        close_btn.connect("clicked", lambda b: self.remove_notification(notification))
        notification.pack_end(close_btn, False, False, 0)

        self.notification_box.pack_start(notification, False, False, 0)
        self.notifications.append(notification)
        notification.show_all()

        if duration > 0:
            GLib.timeout_add(duration, lambda: self.remove_notification(notification))

        return notification

    def remove_notification(self, notification):
        """Bildirimi kaldır"""
        if notification in self.notifications:
            self.notifications.remove(notification)
            notification.destroy()
        return False


class ThumbnailCache:
    """Thumbnail önbellek yöneticisi"""

    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or Path.home() / ".cache" / "downx" / "thumbnails"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.memory_cache = {}
        self.max_memory_cache = 50
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_cache_path(self, url: str) -> Path:
        """URL için önbellek dosya yolunu oluştur"""
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return self.cache_dir / f"{url_hash}.jpg"

    def get(self, url: str) -> Optional[GdkPixbuf.Pixbuf]:
        """Önbellekten thumbnail al"""
        if url in self.memory_cache:
            return self.memory_cache[url]

        cache_path = self.get_cache_path(url)
        if cache_path.exists():
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                    str(cache_path), 120, 68, True
                )
                self._add_to_memory_cache(url, pixbuf)
                return pixbuf
            except Exception as e:
                self.logger.warning(f"Önbellek yükleme hatası: {e}")
                cache_path.unlink()

        return None

    def set(self, url: str, pixbuf: GdkPixbuf.Pixbuf):
        """Thumbnail'i önbelleğe kaydet"""
        cache_path = self.get_cache_path(url)
        try:
            pixbuf.savev(str(cache_path), "jpeg", ["quality"], ["85"])
            self._add_to_memory_cache(url, pixbuf)
        except Exception as e:
            self.logger.warning(f"Önbellek kaydetme hatası: {e}")

    def _add_to_memory_cache(self, url: str, pixbuf: GdkPixbuf.Pixbuf):
        """Bellek önbelleğine ekle"""
        if len(self.memory_cache) >= self.max_memory_cache:
            first_key = next(iter(self.memory_cache))
            del self.memory_cache[first_key]

        self.memory_cache[url] = pixbuf

    def clear(self):
        """Önbelleği temizle"""
        self.memory_cache.clear()
        for file in self.cache_dir.glob("*.jpg"):
            file.unlink()
        self.logger.info("Thumbnail önbelleği temizlendi")


class DownloadManager:
    """İndirme yöneticisi"""

    def __init__(self, parent_window, max_concurrent: int = 3):
        self.parent = parent_window
        self.max_concurrent = max_concurrent
        self.downloads: Dict[str, DownloadItem] = {}
        self.download_queue: Queue = Queue()
        self.active_downloads: Dict[str, threading.Thread] = {}
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.is_downloading = False

        self.stats = {
            "total_downloads": 0,
            "completed_downloads": 0,
            "failed_downloads": 0,
            "total_bytes_downloaded": 0,
            "session_start": datetime.now()
        }

        self.queue_processor = threading.Thread(target=self._process_queue, daemon=True)
        self.queue_processor.start()

    def add_download(self, url: str, quality: str = "best", format: str = "mp4") -> str:
        """İndirme kuyruğuna ekle"""
        download_id = hashlib.md5(f"{url}{datetime.now()}".encode()).hexdigest()[:12]

        download_item = DownloadItem(
            id=download_id,
            url=url,
            quality=quality,
            format=format,
            start_time=datetime.now()
        )

        self.downloads[download_id] = download_item
        self.download_queue.put(download_id)
        self.stats["total_downloads"] += 1

        self.logger.info(f"İndirme kuyruğuna eklendi: {url}")

        return download_id

    def _process_queue(self):
        """Kuyruk işleyici"""
        while True:
            try:
                if len(self.active_downloads) >= self.max_concurrent:
                    time.sleep(1)
                    continue

                download_id = self.download_queue.get(timeout=1)

                if download_id in self.downloads:
                    download_item = self.downloads[download_id]

                    if download_item.status == DownloadStatus.PENDING:
                        self._start_download(download_id)

            except Empty:
                continue
            except Exception as e:
                self.logger.error(f"Kuyruk işleme hatası: {e}")

    def _start_download(self, download_id: str):
        """İndirmeyi başlat"""
        download_item = self.downloads.get(download_id)
        if not download_item:
            return

        download_item.status = DownloadStatus.DOWNLOADING

        future = self.executor.submit(self._download_worker, download_id)
        self.active_downloads[download_id] = future

        future.add_done_callback(lambda f: self._download_complete(download_id, f))

    def _download_worker(self, download_id: str):
        """İndirme işçi thread'i"""
        download_item = self.downloads.get(download_id)
        if not download_item:
            return

        try:
            self.parent.yt_client.extract_info(download_item.url)

            download_item.status = DownloadStatus.COMPLETED
            download_item.end_time = datetime.now()
            self.stats["completed_downloads"] += 1

        except Exception as e:
            download_item.status = DownloadStatus.FAILED
            download_item.error_message = str(e)
            self.stats["failed_downloads"] += 1
            self.logger.error(f"İndirme hatası ({download_id}): {e}")

    def _download_complete(self, download_id: str, future):
        """İndirme tamamlandığında"""
        if download_id in self.active_downloads:
            del self.active_downloads[download_id]

        GLib.idle_add(self.parent.update_download_ui, download_id)

    def pause_download(self, download_id: str):
        """İndirmeyi duraklat"""
        if download_id in self.downloads:
            self.downloads[download_id].status = DownloadStatus.PAUSED

    def resume_download(self, download_id: str):
        """İndirmeyi devam ettir"""
        if download_id in self.downloads:
            download_item = self.downloads[download_id]
            if download_item.status == DownloadStatus.PAUSED:
                download_item.status = DownloadStatus.PENDING
                self.download_queue.put(download_id)

    def cancel_download(self, download_id: str):
        """İndirmeyi iptal et"""
        if download_id in self.downloads:
            self.downloads[download_id].status = DownloadStatus.CANCELLED

    def get_statistics(self) -> Dict[str, Any]:
        """İstatistikleri döndür"""
        uptime = datetime.now() - self.stats["session_start"]
        return {
            **self.stats,
            "active_downloads": len(self.active_downloads),
            "queued_downloads": self.download_queue.qsize(),
            "uptime": str(uptime).split('.')[0]
        }

    def shutdown(self):
        """Yöneticiyi kapat"""
        self.executor.shutdown(wait=False)


class MainWindow(Gtk.Window):
    """Ana pencere sınıfı - Ultra Dark Theme v2.1"""

    def __init__(self, application=None, config=None):
        super().__init__(title="DownX")

        self.application = application
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)

        # Pencere özellikleri
        self.set_default_size(1300, 800)
        self.set_border_width(0)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.is_fullscreen = False

        # Minimum pencere boyutu
        self.set_size_request(900, 600)

        # İkonları ayarla
        self._load_window_icon()

        # Thread havuzu
        self.executor = ThreadPoolExecutor(max_workers=5)

        # YouTube client
        self.yt_client = None

        # Yöneticiler
        self.notification_manager = NotificationManager(self)
        self.thumbnail_cache = ThumbnailCache()
        self.download_manager = DownloadManager(self, max_concurrent=3)

        # Aktif indirmeler
        self.active_downloads = {}

        # Tema ayarları
        self._setup_theme()

        # CSS yükle
        self._load_custom_css()

        # Klavye kısayolları
        self._setup_keyboard_shortcuts()

        # Ana stack
        self.main_stack = Gtk.Stack()
        self.main_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.main_stack.set_transition_duration(200)
        self.add(self.main_stack)

        # Loading sayfası
        self.loading_page = self._create_loading_page()
        self.main_stack.add_named(self.loading_page, "loading")

        # Ana içerik overlay
        self.main_overlay = Gtk.Overlay()
        self.main_stack.add_named(self.main_overlay, "main")

        # Ana içerik kutusu
        self.main_content_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.main_overlay.add(self.main_content_box)

        # Bildirim alanını overlay'e ekle
        self.main_overlay.add_overlay(self.notification_manager.notification_box)

        # Başlangıçta loading göster
        self.main_stack.set_visible_child_name("loading")

        # Tümünü göster
        self.show_all()

        # Bağımlılık kontrolünü başlat
        self.start_dependency_check()

    def _load_window_icon(self) -> None:
        """Pencere ikonunu yükler (mor DownX logosu)."""
        icon_paths = [
            # Proje içi resources dizini (öncelikli)
            Path(__file__).parent / "resources" / "logo.png",
            Path(__file__).parent / "resources" / "icons" / "icon_128.png",
            Path(__file__).parent / "resources" / "icons" / "icon.png",
            # Ana dizin
            Path(__file__).parent / "logo.png",
            Path(__file__).parent / "icon.png",
            # Home dizini (kurulum sonrası)
            Path.home() / "Source" / "DownX" / "resources" / "logo.png",
            Path.home() / "Source" / "DownX" / "resources" / "icons" / "icon_128.png",
        ]

        icon_loaded = False
        for icon_path in icon_paths:
            if icon_path.exists():
                try:
                    self.set_icon_from_file(str(icon_path))
                    self.logger.info(f"✓ Pencere ikonu yüklendi: {icon_path}")
                    icon_loaded = True
                    break
                except Exception as e:
                    self.logger.warning(f"İkon yükleme hatası ({icon_path}): {e}")

        if not icon_loaded:
            # Fallback: sistem ikonu
            self.set_icon_name("multimedia-video-player")
            self.logger.info("Varsayılan sistem ikonu kullanılıyor")

    def _setup_theme(self):
        """Tema ayarlarını yap - ZORLA KOYU TEMA"""
        settings = Gtk.Settings.get_default()

        # Koyu temayı zorla
        settings.set_property("gtk-application-prefer-dark-theme", True)
        settings.set_property("gtk-enable-animations", True)

        # GTK tema adını da ayarla (eğer varsa)
        try:
            settings.set_property("gtk-theme-name", "Adwaita-dark")
        except:
            pass

        # Ekstra: Pencere rengini zorla
        try:
            screen = self.get_screen()
            provider = Gtk.CssProvider()
            provider.load_from_data(b"""
                window {
                    background-color: #0a0a0a;
                    color: #ffffff;
                }
            """)
            Gtk.StyleContext.add_provider_for_screen(
                screen,
                provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
        except:
            pass

    def _load_custom_css(self):
        """Özel CSS dosyasını yükle"""
        css_provider = Gtk.CssProvider()

        css_paths = [
            Path("assets/style.css"),
            Path("assets/style-premium.css"),
            Path(__file__).parent / "assets" / "style.css"
        ]

        css_loaded = False
        for css_path in css_paths:
            if css_path.exists():
                try:
                    css_provider.load_from_path(str(css_path))
                    css_loaded = True
                    self.logger.info(f"CSS yüklendi: {css_path}")
                    break
                except Exception as e:
                    self.logger.warning(f"CSS yükleme hatası: {e}")

        if not css_loaded:
            css_provider.load_from_data(self._get_default_css().encode())

        # CSS priority'yi maksimuma çıkar (GTK theme'i override et)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_USER
        )

    def _get_default_css(self) -> str:
        """Varsayılan CSS"""
        return DEFAULT_CSS

    def _setup_keyboard_shortcuts(self):
        """Klavye kısayollarını ayarla"""
        accel_group = Gtk.AccelGroup()
        self.add_accel_group(accel_group)

        shortcuts = [
            ("F11", self.toggle_fullscreen),
            ("<Control>f", self.focus_search),
            ("<Control>d", self.show_downloads),
            ("<Control>s", self.show_settings),
            ("Escape", self.escape_action),
            ("<Control>q", self.quit_app),
        ]

        for accel, callback in shortcuts:
            key, mod = Gtk.accelerator_parse(accel)
            accel_group.connect(key, mod, Gtk.AccelFlags.VISIBLE,
                               lambda *args, cb=callback: cb() or True)

    def quit_app(self):
        """Uygulamadan çık"""
        self.cleanup()
        if self.application:
            self.application.quit()
        else:
            Gtk.main_quit()

    def _create_loading_page(self):
        """Gelişmiş loading sayfası oluştur"""
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        container.get_style_context().add_class("loading-container")

        center_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=30)
        center_box.set_halign(Gtk.Align.CENTER)
        center_box.set_valign(Gtk.Align.CENTER)

        # Logo
        logo_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
        logo_box.set_halign(Gtk.Align.CENTER)

        logo = Gtk.Image()
        # Önce kendi ikonumuzu dene (128x128 loading için ideal)
        icon_path = Path(__file__).parent / "resources" / "icons" / "icon_128.png"
        if not icon_path.exists():
            icon_path = Path.home() / "Source" / "DownX" / "resources" / "icons" / "icon_128.png"

        if icon_path.exists():
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(str(icon_path), 80, 80, True)
                logo.set_from_pixbuf(pixbuf)
            except:
                logo.set_from_icon_name("multimedia-video-player", Gtk.IconSize.INVALID)
                logo.set_pixel_size(80)
        else:
            logo.set_from_icon_name("multimedia-video-player", Gtk.IconSize.INVALID)
            logo.set_pixel_size(80)

        logo_box.pack_start(logo, False, False, 0)

        app_name = Gtk.Label()
        app_name.set_markup("<span size='xx-large' weight='bold'>DownX</span>")
        logo_box.pack_start(app_name, False, False, 0)

        center_box.pack_start(logo_box, False, False, 0)

        # Spinner
        spinner_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)

        spinner = Gtk.Spinner()
        spinner.set_size_request(60, 60)
        spinner.start()
        spinner_box.pack_start(spinner, False, False, 0)

        self.loading_status_label = Gtk.Label()
        self.loading_status_label.set_markup("<span size='large'>Bağımlılıklar kontrol ediliyor...</span>")
        spinner_box.pack_start(self.loading_status_label, False, False, 0)

        self.loading_detail_label = Gtk.Label()
        self.loading_detail_label.set_markup("<span size='small' alpha='70%'>Lütfen bekleyin</span>")
        spinner_box.pack_start(self.loading_detail_label, False, False, 0)

        center_box.pack_start(spinner_box, False, False, 0)

        # Progress bar
        self.loading_progress = Gtk.ProgressBar()
        self.loading_progress.set_size_request(400, -1)
        self.loading_progress.set_show_text(False)
        center_box.pack_start(self.loading_progress, False, False, 0)

        container.pack_start(center_box, True, True, 0)

        # Alt bilgi
        info_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        info_box.set_halign(Gtk.Align.CENTER)
        info_box.set_margin_bottom(20)

        version_label = Gtk.Label()
        version_label.set_markup("<span size='small' alpha='50%'>Version 2.1.0 | Ultra Dark Theme</span>")
        info_box.pack_start(version_label, False, False, 0)

        container.pack_end(info_box, False, False, 0)

        return container

    def start_dependency_check(self):
        """Gelişmiş bağımlılık kontrolü"""
        self.loading_progress.set_fraction(0.0)

        def update_progress(step, total, message):
            GLib.idle_add(self._update_loading_ui, step, total, message)

        def on_complete(success):
            if success:
                GLib.idle_add(self._dependency_check_success)
            else:
                GLib.idle_add(self._dependency_check_failed)

        check_thread = threading.Thread(
            target=self._run_dependency_check,
            args=(update_progress, on_complete),
            daemon=True
        )
        check_thread.start()

    def _update_loading_ui(self, step, total, message):
        """Loading UI güncelle"""
        fraction = step / total if total > 0 else 0
        self.loading_progress.set_fraction(fraction)
        self.loading_status_label.set_markup(f"<span size='large'>{message}</span>")

        details = [
            "Sistem gereksinimleri kontrol ediliyor...",
            "Python paketleri yükleniyor...",
            "yt-dlp güncelleniyor...",
            "FFmpeg kontrol ediliyor...",
            "Önbellek temizleniyor...",
            "Ayarlar yükleniyor...",
            "Arayüz hazırlanıyor..."
        ]

        if step < len(details):
            self.loading_detail_label.set_markup(
                f"<span size='small' alpha='70%'>{details[step]}</span>"
            )

    def _run_dependency_check(self, progress_callback, complete_callback):
        """Bağımlılık kontrolü çalıştır"""
        try:
            steps = [
                ("Sistem kontrolleri", self._check_system),
                ("Python paketleri", self._check_python_packages),
                ("yt-dlp", self._check_ytdlp),
                ("FFmpeg", self._check_ffmpeg),
                ("Önbellek", self._clean_cache),
                ("Ayarlar", self._load_settings),
                ("Son hazırlıklar", self._final_preparations)
            ]

            total = len(steps)

            for i, (name, checker) in enumerate(steps):
                progress_callback(i, total, name)
                time.sleep(0.3)

                success = checker()
                if not success:
                    complete_callback(False)
                    return

            progress_callback(total, total, "Tamamlandı!")
            time.sleep(0.3)
            complete_callback(True)

        except Exception as e:
            self.logger.error(f"Bağımlılık kontrol hatası: {e}")
            complete_callback(False)

    def _check_system(self) -> bool:
        try:
            import platform
            self.logger.info(f"Sistem: {platform.system()} {platform.release()}")
            return True
        except:
            return False

    def _check_python_packages(self) -> bool:
        required = ['gi', 'requests', 'PIL']
        for package in required:
            try:
                __import__(package)
            except ImportError:
                self.logger.warning(f"Eksik paket: {package}")
                return False
        return True

    def _check_ytdlp(self) -> bool:
        try:
            result = subprocess.run(
                ['yt-dlp', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            self.logger.info(f"yt-dlp version: {result.stdout.strip()}")
            return result.returncode == 0
        except:
            return False

    def _check_ffmpeg(self) -> bool:
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False

    def _clean_cache(self) -> bool:
        try:
            cache_dir = Path.home() / ".cache" / "downx"
            if cache_dir.exists():
                cutoff = time.time() - (7 * 24 * 60 * 60)
                for file in cache_dir.rglob("*"):
                    if file.is_file() and file.stat().st_mtime < cutoff:
                        file.unlink()
            return True
        except:
            return True

    def _load_settings(self) -> bool:
        try:
            return True
        except:
            return True

    def _final_preparations(self) -> bool:
        try:
            self.yt_client = YouTubeClient()
            return True
        except:
            return False

    def _dependency_check_success(self):
        """Bağımlılık kontrolü başarılı"""
        self.logger.info("✅ Bağımlılık kontrolü başarılı")

        self.load_main_ui()
        self.main_stack.set_visible_child_name("main")
        self.show_notification("DownX'ye hoş geldiniz!", "success")

    def _dependency_check_failed(self):
        """Bağımlılık kontrolü başarısız"""
        self.logger.error("❌ Bağımlılık kontrolü başarısız")

        self.loading_status_label.set_markup(
            "<span size='large' color='#ef4444'>Kritik Hata!</span>"
        )
        self.loading_detail_label.set_markup(
            "<span size='small'>Bağımlılıklar yüklenemedi. Lütfen kurulum talimatlarını kontrol edin.</span>"
        )

        retry_btn = Gtk.Button(label="🔄 Yeniden Dene")
        retry_btn.set_size_request(180, 45)
        retry_btn.get_style_context().add_class("suggested-action")
        retry_btn.connect("clicked", lambda b: self.start_dependency_check())

        parent = self.loading_detail_label.get_parent()
        parent.pack_start(retry_btn, False, False, 20)
        retry_btn.show()

    def load_main_ui(self):
        """Ana kullanıcı arayüzünü yükle"""
        main_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.main_content_box.pack_start(main_container, True, True, 0)

        # 1. TITLEBAR
        titlebar = self.create_modern_titlebar()
        main_container.pack_start(titlebar, False, False, 0)

        # 2. TAB BAR
        tab_bar = self.create_chrome_tabs()
        main_container.pack_start(tab_bar, False, False, 0)

        # 3. CONTENT AREA
        content_area = self.create_content_area()
        main_container.pack_start(content_area, True, True, 0)

        # Sayfaları yükle
        self.load_pages()

        # İlk sekmeyi aktif et
        self.on_tab_click(self.tab_buttons["Ana Sayfa"], "Ana Sayfa")

        self.main_content_box.show_all()

    def create_modern_titlebar(self):
        """Minimal titlebar - Logo + Butonlar"""
        titlebar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        titlebar.get_style_context().add_class("titlebar")
        titlebar.set_margin_start(12)
        titlebar.set_margin_end(12)
        titlebar.set_margin_top(8)
        titlebar.set_margin_bottom(8)

        # Logo + Title
        logo_box = Gtk.Box(spacing=10)

        logo = Gtk.Image()
        # Önce kendi ikonumuzu dene
        icon_path = Path(__file__).parent / "resources" / "icons" / "icon_48.png"
        if not icon_path.exists():
            icon_path = Path(__file__).parent / "resources" / "icons" / "icon_64.png"
        if not icon_path.exists():
            icon_path = Path.home() / "Source" / "DownX" / "resources" / "icons" / "icon_48.png"

        if icon_path.exists():
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(str(icon_path), 32, 32, True)
                logo.set_from_pixbuf(pixbuf)
            except:
                logo.set_from_icon_name("multimedia-video-player", Gtk.IconSize.LARGE_TOOLBAR)
        else:
            logo.set_from_icon_name("multimedia-video-player", Gtk.IconSize.LARGE_TOOLBAR)

        logo_box.pack_start(logo, False, False, 0)

        title_label = Gtk.Label()
        title_label.set_markup("<b><span size='large'>DownX</span></b>")
        logo_box.pack_start(title_label, False, False, 0)

        titlebar.pack_start(logo_box, False, False, 0)

        # Spacer
        titlebar.pack_start(Gtk.Box(), True, True, 0)

        # Sağ butonlar
        button_box = Gtk.Box(spacing=6)

        # Tema butonu
        theme_btn = Gtk.Button()
        theme_btn.set_relief(Gtk.ReliefStyle.NONE)
        theme_btn.get_style_context().add_class("titlebar-button")
        theme_icon = Gtk.Image.new_from_icon_name("weather-clear-night-symbolic", Gtk.IconSize.BUTTON)
        theme_btn.add(theme_icon)
        theme_btn.set_tooltip_text("Tema değiştir")
        theme_btn.connect("clicked", self.toggle_theme)
        button_box.pack_start(theme_btn, False, False, 0)

        # Ayarlar hızlı erişim
        settings_quick_btn = Gtk.Button()
        settings_quick_btn.set_relief(Gtk.ReliefStyle.NONE)
        settings_quick_btn.get_style_context().add_class("titlebar-button")
        settings_quick_icon = Gtk.Image.new_from_icon_name("emblem-system-symbolic", Gtk.IconSize.BUTTON)
        settings_quick_btn.add(settings_quick_icon)
        settings_quick_btn.set_tooltip_text("Ayarlar")
        settings_quick_btn.connect("clicked", lambda b: self.on_tab_click(self.tab_buttons["Ayarlar"], "Ayarlar"))
        button_box.pack_start(settings_quick_btn, False, False, 0)

        titlebar.pack_end(button_box, False, False, 0)

        return titlebar

    def create_chrome_tabs(self):
        """Chrome-tarzı sekme çubuğu - BÜYÜK"""
        tab_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        tab_bar.get_style_context().add_class("tab-bar")
        tab_bar.set_margin_start(8)
        tab_bar.set_margin_end(8)

        self.tab_buttons = {}
        self.active_tab_button = None

        # Sekmeler
        tabs = [
            ("go-home-symbolic", "Ana Sayfa", "Ana sayfa ve arama"),
            ("folder-download-symbolic", "İndirilenler", "İndirme yöneticisi"),
            ("preferences-other-symbolic", "Araçlar", "Ekstra araçlar"),
            ("emblem-system-symbolic", "Ayarlar", "Uygulama ayarları"),
        ]

        for icon, label, tooltip in tabs:
            btn = self.create_tab_button(icon, label, tooltip)
            tab_bar.pack_start(btn, False, False, 0)
            self.tab_buttons[label] = btn

        # Sağda boşluk
        tab_bar.pack_start(Gtk.Box(), True, True, 0)

        return tab_bar

    def create_tab_button(self, icon, label, tooltip):
        """Chrome-style tek bir sekme butonu"""
        btn = Gtk.Button()
        btn.set_relief(Gtk.ReliefStyle.NONE)
        btn.get_style_context().add_class("tab-button")
        btn.set_tooltip_text(tooltip)

        box = Gtk.Box(spacing=8)
        box.set_halign(Gtk.Align.CENTER)

        # İkon - Normal boyut
        img = Gtk.Image.new_from_icon_name(icon, Gtk.IconSize.MENU)
        box.pack_start(img, False, False, 0)

        # Label - Normal
        lbl = Gtk.Label(label=label)
        box.pack_start(lbl, False, False, 0)

        btn.add(box)
        btn.connect("clicked", self.on_tab_click, label)

        return btn

    def on_tab_click(self, button, name):
        """Sekmeye tıklama"""
        if self.active_tab_button == button:
            return

        if self.active_tab_button:
            self.active_tab_button.get_style_context().remove_class("tab-active")

        button.get_style_context().add_class("tab-active")
        self.active_tab_button = button

        self.content_stack.set_visible_child_name(name)
        self.update_status(name)

        if name == "İndirilenler" and hasattr(self, 'downloads_tab'):
            GLib.idle_add(self.downloads_tab.update_downloads_page_content)

    def create_content_area(self):
        """İçerik alanını oluştur"""
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        # Content stack
        self.content_stack = Gtk.Stack()
        self.content_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.content_stack.set_transition_duration(50)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.add(self.content_stack)

        content_box.pack_start(scrolled, True, True, 0)

        # Status bar
        self.status_bar = self.create_status_bar()
        content_box.pack_end(self.status_bar, False, False, 0)

        return content_box

    def create_status_bar(self):
        """Alt durum çubuğu"""
        status = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        status.get_style_context().add_class("status-bar")

        # Sol taraf
        status_left = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        self.status_icon = Gtk.Image.new_from_icon_name("emblem-ok-symbolic", Gtk.IconSize.MENU)
        status_left.pack_start(self.status_icon, False, False, 0)

        self.status_label = Gtk.Label(label="Hazır")
        status_left.pack_start(self.status_label, False, False, 0)

        status.pack_start(status_left, False, False, 0)

        # Orta - progress
        self.global_progress = Gtk.ProgressBar()
        self.global_progress.set_size_request(200, -1)
        self.global_progress.set_visible(False)
        status.pack_start(self.global_progress, False, False, 0)

        # Sağ taraf
        stats_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)

        self.active_downloads_label = Gtk.Label()
        self.active_downloads_label.set_markup("<span size='small'>İndirmeler: 0</span>")
        stats_box.pack_start(self.active_downloads_label, False, False, 0)

        self.speed_label = Gtk.Label()
        self.speed_label.set_markup("<span size='small'>0 KB/s</span>")
        stats_box.pack_start(self.speed_label, False, False, 0)

        self.time_label = Gtk.Label()
        stats_box.pack_start(self.time_label, False, False, 0)

        status.pack_end(stats_box, False, False, 0)

        GLib.timeout_add_seconds(1, self.update_time)

        return status

    def load_pages(self):
        """Tüm sayfaları yükle"""
        # Ana sayfa / Arama
        self.search_tab = SearchTab(self)
        self.content_stack.add_named(self.search_tab, "Ana Sayfa")

        # İndirilenler
        self.downloads_tab = DownloadsTab(self)
        self.content_stack.add_named(self.downloads_tab, "İndirilenler")

        # Araçlar
        try:
            self.tools_tab = ToolsTab(self)
            self.content_stack.add_named(self.tools_tab, "Araçlar")
        except Exception as e:
            self.logger.warning(f"Tools tab yüklenemedi: {e}")

        # Ayarlar
        self.settings_tab = SettingsTab(self)
        self.content_stack.add_named(self.settings_tab, "Ayarlar")

    def add_url_to_download(self, url: str):
        """URL'yi indirme listesine ekle"""
        self.download_manager.add_download(url)
        self.show_notification("İndirme kuyruğuna eklendi", "success")

    def update_download_ui(self, download_id: str):
        """İndirme UI güncelleme"""
        if hasattr(self, 'downloads_tab'):
            self.downloads_tab.update_download_item(download_id)

    def update_status(self, message: str, icon: str = "emblem-ok-symbolic"):
        """Durum çubuğunu güncelle"""
        self.status_icon.set_from_icon_name(icon, Gtk.IconSize.MENU)
        self.status_label.set_text(message)

    def update_time(self):
        """Saat güncelleme"""
        now = datetime.now()
        self.time_label.set_text(now.strftime("%H:%M:%S"))

        stats = self.download_manager.get_statistics()
        self.active_downloads_label.set_markup(
            f"<span size='small'>İndirmeler: {stats['active_downloads']}</span>"
        )

        return True

    def show_notification(self, message: str, notification_type: str = "info"):
        """Bildirim göster"""
        self.notification_manager.show(message, notification_type)

    def toggle_fullscreen(self):
        """Tam ekran modunu değiştir"""
        if self.is_fullscreen:
            self.unfullscreen()
            self.is_fullscreen = False
            self.show_notification("Tam ekran modundan çıkıldı", "info")
        else:
            self.fullscreen()
            self.is_fullscreen = True
            self.show_notification("Tam ekran moduna geçildi", "info")

    def toggle_theme(self, button=None):
        """Tema değiştir"""
        settings = Gtk.Settings.get_default()
        dark_theme = settings.get_property("gtk-application-prefer-dark-theme")
        settings.set_property("gtk-application-prefer-dark-theme", not dark_theme)

        theme_name = "Açık" if dark_theme else "Koyu"
        self.show_notification(f"{theme_name} tema aktif", "info")

    def focus_search(self):
        """Ana sayfaya git"""
        self.on_tab_click(self.tab_buttons["Ana Sayfa"], "Ana Sayfa")

    def show_downloads(self):
        """İndirilenler sayfasını göster"""
        self.on_tab_click(self.tab_buttons["İndirilenler"], "İndirilenler")

    def show_settings(self):
        """Ayarlar sayfasını göster"""
        self.on_tab_click(self.tab_buttons["Ayarlar"], "Ayarlar")

    def escape_action(self):
        """ESC tuşu işlevi"""
        if self.is_fullscreen:
            self.toggle_fullscreen()

    def do_delete_event(self, event):
        """Pencere kapatılırken"""
        active = len(self.download_manager.active_downloads)
        if active > 0:
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.QUESTION,
                buttons=Gtk.ButtonsType.YES_NO,
                text="Aktif indirmeler var!"
            )
            dialog.format_secondary_text(
                f"{active} aktif indirme devam ediyor.\n"
                "Yine de çıkmak istiyor musunuz?"
            )

            response = dialog.run()
            dialog.destroy()

            if response != Gtk.ResponseType.YES:
                return True

        self.cleanup()
        return False

    def cleanup(self):
        """Temizlik işlemleri"""
        try:
            self.executor.shutdown(wait=False)
            self.download_manager.shutdown()
            self.logger.info("Temizlik işlemleri tamamlandı")
        except Exception as e:
            self.logger.error(f"Temizlik hatası: {e}")

        if not self.application:
            Gtk.main_quit()


# Ana çalıştırma
if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    win = MainWindow()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()

    Gtk.main()
