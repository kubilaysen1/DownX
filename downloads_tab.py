"""
Downloads Tab - ULTRA HAFİFLETİLMİŞ VERSİYON
- Sanal liste (sadece görünen satırlar)
- Minimum UI güncellemesi
- Batch güncelleme (her 500ms)
- CSS yok (native GTK)
"""
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango
import os
import subprocess 
import time

try:
    from settings import get_download_dir, GLOBAL_CONFIG
except ImportError:
    def get_download_dir(): return os.path.expanduser("~/Downloads")
    GLOBAL_CONFIG = {}

DOWNLOAD_DIR = get_download_dir()


class DownloadsTab(Gtk.Box):
    """Ultra Hafif İndirme Yönetimi"""
    
    def __init__(self, main_window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.main_window = main_window
        self.queue_manager = None
        self.row_cache = {}  # Widget cache
        self._pending_updates = set()  # Bekleyen güncellemeler
        self._last_full_update = 0
        self._update_timer = None
        
        self._setup_ui()
        self._refresh_queue_manager_ref()
        self.show_all()
        
        # Batch güncelleme timer
        GLib.timeout_add(500, self._batch_update_timer)

    def _setup_ui(self):
        """Minimal UI"""
        # Header
        header = Gtk.Box(spacing=8)
        header.set_margin_start(12)
        header.set_margin_end(12)
        header.set_margin_top(8)
        header.set_margin_bottom(8)
        
        title = Gtk.Label(label="📥 İndirmeler")
        title.set_markup("<b>📥 İndirmeler</b>")
        header.pack_start(title, False, False, 0)
        
        # İstatistikler
        self.stat_label = Gtk.Label()
        self.stat_label.set_markup("<span foreground='#888'>Kuyruk: 0 | Aktif: 0 | Bitti: 0</span>")
        header.pack_start(self.stat_label, False, False, 8)
        
        # Klasör aç
        folder_btn = Gtk.Button(label="📂 Klasör")
        folder_btn.connect("clicked", self._open_folder)
        header.pack_end(folder_btn, False, False, 0)
        
        self.pack_start(header, False, False, 0)
        
        # Kontroller (tek satır)
        controls = Gtk.Box(spacing=8)
        controls.set_margin_start(12)
        controls.set_margin_end(12)
        controls.set_margin_bottom(8)
        
        self.btn_start = Gtk.Button(label="▶️ Başlat")
        self.btn_start.connect("clicked", self._on_start)
        controls.pack_start(self.btn_start, False, False, 0)
        
        self.btn_stop = Gtk.Button(label="⏹️ Durdur")
        self.btn_stop.connect("clicked", self._on_stop)
        self.btn_stop.set_sensitive(False)
        controls.pack_start(self.btn_stop, False, False, 0)
        
        btn_clear = Gtk.Button(label="🧹 Temizle")
        btn_clear.connect("clicked", self._on_clear)
        controls.pack_start(btn_clear, False, False, 0)
        
        self.pack_start(controls, False, False, 0)
        
        # TreeView (en hızlı)
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)
        
        # Model: [id, #, başlık, sanatçı, durum, durum_icon, checked]
        self.store = Gtk.ListStore(str, int, str, str, str, str, bool)
        
        self.treeview = Gtk.TreeView(model=self.store)
        self.treeview.set_headers_visible(True)
        self.treeview.set_enable_search(False)
        self.treeview.set_fixed_height_mode(True)  # HIZLANDIRMA
        
        # Checkbox column
        renderer_toggle = Gtk.CellRendererToggle()
        renderer_toggle.connect("toggled", self._on_toggle)
        col_check = Gtk.TreeViewColumn("✓", renderer_toggle)
        col_check.add_attribute(renderer_toggle, "active", 6)  # Yeni: checked state
        col_check.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
        col_check.set_fixed_width(30)
        self.treeview.append_column(col_check)
        
        # # column
        renderer = Gtk.CellRendererText()
        col_num = Gtk.TreeViewColumn("#", renderer, text=1)
        col_num.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
        col_num.set_fixed_width(50)
        self.treeview.append_column(col_num)
        
        # Başlık column
        renderer = Gtk.CellRendererText()
        renderer.set_property("ellipsize", Pango.EllipsizeMode.END)
        col_title = Gtk.TreeViewColumn("Başlık", renderer, text=2)
        col_title.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
        col_title.set_fixed_width(400)
        col_title.set_expand(True)
        self.treeview.append_column(col_title)
        
        # Sanatçı column
        renderer = Gtk.CellRendererText()
        renderer.set_property("ellipsize", Pango.EllipsizeMode.END)
        renderer.set_property("foreground", "#888")
        col_artist = Gtk.TreeViewColumn("Sanatçı", renderer, text=3)
        col_artist.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
        col_artist.set_fixed_width(200)
        self.treeview.append_column(col_artist)
        
        # Durum column
        renderer = Gtk.CellRendererText()
        col_status = Gtk.TreeViewColumn("Durum", renderer, markup=5)
        col_status.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
        col_status.set_fixed_width(150)
        self.treeview.append_column(col_status)
        
        scroll.add(self.treeview)
        self.pack_start(scroll, True, True, 0)

    def _refresh_queue_manager_ref(self):
        """Queue manager referansı"""
        if not self.queue_manager:
            self.queue_manager = getattr(self.main_window, 'queue_manager', None)
            if not self.queue_manager and hasattr(self.main_window, 'search_tab'):
                self.queue_manager = getattr(self.main_window.search_tab, 'queue_manager', None)

    # ==================== GÜNCELLEME ====================
    
    def update_downloads_page_content(self):
        """TAM SAYFA GÜNCELLEMESİ - Sadece gerektiğinde"""
        now = time.time()
        # En az 1 saniyede bir tam güncelleme
        if now - self._last_full_update < 1.0:
            return
        
        self._last_full_update = now
        self._refresh_queue_manager_ref()
        
        # Store'u temizle
        self.store.clear()
        self.row_cache.clear()
        
        stats = {"queue": 0, "active": 0, "done": 0}
        
        if self.queue_manager and self.queue_manager.queue:
            # Sadece ilk 200 satır (çok büyük listelerde)
            max_items = 200
            items = list(self.queue_manager.queue)[:max_items]
            
            for idx, item in enumerate(items):
                item_id = item.get("id", str(idx))
                status = item.get("status", "Beklemede")
                
                # İstatistik
                if "İndiriliyor" in status or "Dönüştürülüyor" in status:
                    stats["active"] += 1
                elif status == "Tamamlandı":
                    stats["done"] += 1
                else:
                    stats["queue"] += 1
                
                # Durum ikonu
                status_markup = self._get_status_markup(status)
                
                # Checkbox durumu
                is_selected = idx in self.queue_manager.selected_indices if self.queue_manager else False
                
                # Row ekle
                tree_iter = self.store.append([
                    item_id,
                    idx + 1,
                    item.get("title", "?")[:60],
                    item.get("artist", "")[:40],
                    status,
                    status_markup,
                    is_selected  # Checkbox state
                ])
                
                self.row_cache[item_id] = tree_iter
            
            # Fazla item varsa
            total = len(self.queue_manager.queue)
            if total > max_items:
                self.store.append([
                    "",
                    0,
                    f"... ve {total - max_items} parça daha (Toplam: {total})",
                    "",
                    "",
                    "",
                    False
                ])
            
            # Butonlar
            running = self.queue_manager.is_downloading
            self.btn_start.set_sensitive(not running)
            self.btn_stop.set_sensitive(running)
        else:
            # Boş durum
            self.store.append([
                "",
                0,
                "Kuyruk boş - Link eklemek için Ara sekmesini kullan",
                "",
                "",
                "<span foreground='#888'>◷</span>",
                False
            ])
            self.btn_start.set_sensitive(False)
            self.btn_stop.set_sensitive(False)
        
        # İstatistik güncelle
        self.stat_label.set_markup(
            f"<span foreground='#3b82f6'>Kuyruk: {stats['queue']}</span> | "
            f"<span foreground='#f59e0b'>Aktif: {stats['active']}</span> | "
            f"<span foreground='#10b981'>Bitti: {stats['done']}</span>"
        )

    def _get_status_markup(self, status):
        """Durum markup"""
        if status == "Tamamlandı":
            return "<span foreground='#10b981'>✓ Tamamlandı</span>"
        elif "İndiriliyor" in status:
            return "<span foreground='#3b82f6'>⬇ İndiriliyor</span>"
        elif "Dönüştürülüyor" in status:
            return "<span foreground='#f59e0b'>⚙ Dönüştürülüyor</span>"
        elif "Hata" in status:
            return f"<span foreground='#ef4444'>✕ {status}</span>"
        elif "Kuyrukta" in status or "Beklemede" in status:
            return "<span foreground='#8b5cf6'>◷ Beklemede</span>"
        else:
            return f"<span foreground='#888'>{status}</span>"

    # ==================== HAFİF TEK SATIR GÜNCELLEMESİ ====================
    
    def update_download_status(self, item_id, message):
        """Tek satır güncelle (HIZLI)"""
        # Sadece pending'e ekle, batch'te işle
        self._pending_updates.add(item_id)

    def update_download_progress(self, item_id, percent, message=""):
        """Progress güncelle"""
        self._pending_updates.add(item_id)

    def _batch_update_timer(self):
        """500ms'de bir toplu güncelleme"""
        if not self._pending_updates:
            return True  # Timer devam etsin
        
        # Pending güncellemeleri işle
        to_update = list(self._pending_updates)
        self._pending_updates.clear()
        
        for item_id in to_update:
            if item_id in self.row_cache:
                tree_iter = self.row_cache[item_id]
                
                # Queue'dan item bul
                if self.queue_manager:
                    item = next((i for i in self.queue_manager.queue if i.get("id") == item_id), None)
                    if item:
                        status = item.get("status", "")
                        status_markup = self._get_status_markup(status)
                        
                        # Sadece durum sütununu güncelle
                        self.store.set_value(tree_iter, 4, status)
                        self.store.set_value(tree_iter, 5, status_markup)
        
        return True  # Timer devam etsin

    # ==================== OLAYLAR ====================
    
    def _on_start(self, btn):
        if self.queue_manager:
            self.queue_manager.start_downloads()
            GLib.timeout_add(100, self.update_downloads_page_content)

    def _on_stop(self, btn):
        if self.queue_manager:
            self.queue_manager.stop_downloads()
            GLib.timeout_add(100, self.update_downloads_page_content)

    def _on_clear(self, btn):
        """Tamamlananları temizle"""
        if not self.queue_manager:
            return
        
        with self.queue_manager.lock:
            # Sadece bekleyenleri tut
            self.queue_manager.queue = [
                i for i in self.queue_manager.queue 
                if i.get("status") not in ["Tamamlandı", "Hata", "Atlandı (Mevcut)"]
                and "Hata" not in i.get("status", "")
            ]
            self.queue_manager.selected_indices.clear()
            for i in range(len(self.queue_manager.queue)):
                self.queue_manager.selected_indices.add(i)
        
        self.update_downloads_page_content()

    def clear_all(self):
        """TÜMÜNÜ temizle"""
        if not self.queue_manager:
            return
        
        with self.queue_manager.lock:
            self.queue_manager.queue.clear()
            self.queue_manager.selected_indices.clear()
        
        self.update_downloads_page_content()

    def _on_toggle(self, widget, path):
        """Checkbox toggle"""
        tree_iter = self.store.get_iter(path)
        idx = self.store.get_value(tree_iter, 1) - 1  # Numara - 1
        
        if idx >= 0 and self.queue_manager:
            current = self.store.get_value(tree_iter, 6)
            new_value = not current
            
            self.store.set_value(tree_iter, 6, new_value)
            
            with self.queue_manager.lock:
                if new_value:
                    self.queue_manager.selected_indices.add(idx)
                else:
                    self.queue_manager.selected_indices.discard(idx)

    def _open_folder(self, btn):
        """Klasör aç"""
        try:
            subprocess.Popen(['xdg-open', get_download_dir()])
        except:
            pass

    # ==================== UYUMLULUK ====================
    
    def update_download_item(self, download_id):
        """Tek item güncelle"""
        self._pending_updates.add(download_id)

    def update_recent_files(self):
        """Yok artık"""
        pass