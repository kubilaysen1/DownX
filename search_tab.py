import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango
import os
import sys
import threading
import re
import subprocess
import requests
import time
from pathlib import Path

# Settings
try:
    from settings import GLOBAL_CONFIG, get_download_dir
except ImportError:
    GLOBAL_CONFIG = {"download_path": str(Path.home() / "Downloads")}
    DOWNLOAD_DIR = Path.home() / "Downloads"

# Imports
try:
    from queue_manager import QueueManager
except ImportError:
    QueueManager = None

try:
    from spotify_client import SpotifyClient
except ImportError:
    SpotifyClient = None

try:
    from gi.repository import GdkPixbuf
except ImportError:
    GdkPixbuf = None

class SearchTab(Gtk.Box):
    def __init__(self, main_window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        self.main_window = main_window
        self.executor = getattr(main_window, 'executor', None)
        self.yt_client = getattr(main_window, 'yt_client', None)
        
        # Önce Spotify client oluştur
        try:
            self.spotify_client = SpotifyClient() if SpotifyClient else None
            if self.spotify_client and self.spotify_client.sp:
                print("✅ [SEARCH] Spotify Client bağlandı")
            else:
                print("⚠️ [SEARCH] Spotify Client bağlanamadı")
        except Exception as e:
            self.spotify_client = None
            print(f"⚠️ [SEARCH] Spotify Client hatası: {e}")
        
        # Sonra QueueManager'ı spotify ve youtube client ile oluştur
        if QueueManager:
            self.queue_manager = QueueManager(
                main_window, 
                spotify_client=self.spotify_client,
                youtube_client=self.yt_client
            )
            print("✅ [SEARCH] QueueManager başlatıldı")
        else:
            self.queue_manager = None
            print("⚠️ [SEARCH] QueueManager yüklenemedi!")

        self.current_search_query = ""

        # UI
        self.main_scroll = Gtk.ScrolledWindow()
        self.main_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.main_scroll.set_kinetic_scrolling(True)
        self.pack_start(self.main_scroll, True, True, 0)

        self.main_content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=25)
        self.main_content.set_margin_top(30)
        self.main_content.set_margin_start(30)
        self.main_content.set_margin_end(30)
        self.main_content.set_margin_bottom(30)
        self.main_scroll.add(self.main_content)

        self.create_search_section()
        self.create_quick_actions_section()
        self.create_results_section()
        
        self.check_spotdl_startup()
        self.show_all()

    def check_spotdl_startup(self):
        def _chk():
            try:
                subprocess.run([sys.executable, "-m", "spotdl", "--version"], 
                             capture_output=True, check=True)
                GLib.idle_add(lambda: self.main_window.status_label.set_text("✅ SpotDL Hazır"))
            except:
                GLib.idle_add(lambda: self.main_window.status_label.set_text("⚠️ SpotDL Bulunamadı"))
        threading.Thread(target=_chk, daemon=True).start()

    # ============= ARAMA ARAYÜZÜ =============
    def create_search_section(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        
        header_box = Gtk.Box(spacing=12)
        icon = Gtk.Image.new_from_icon_name("system-search-symbolic", Gtk.IconSize.LARGE_TOOLBAR)
        lbl = Gtk.Label()
        lbl.set_markup("<span size='x-large' weight='bold'>Arama ve İndirme</span>")
        header_box.pack_start(icon, False, False, 0)
        header_box.pack_start(lbl, False, False, 0)
        vbox.pack_start(header_box, False, False, 0)

        input_box = Gtk.Box(spacing=10)
        
        self.search_entry = Gtk.Entry()
        self.search_entry.set_placeholder_text("YouTube / Spotify linki veya şarkı adı...")
        # DÜZELTME BURADA: set_height_request yerine set_size_request
        self.search_entry.set_size_request(-1, 45) 
        self.search_entry.connect("activate", self.on_search_clicked)
        self.search_entry.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY, "edit-clear")
        self.search_entry.connect("icon-press", lambda e, p, v: self.search_entry.set_text(""))
        input_box.pack_start(self.search_entry, True, True, 0)

        search_btn = Gtk.Button()
        search_btn.get_style_context().add_class("suggested-action")
        search_btn.set_size_request(100, 45)
        search_btn.connect("clicked", self.on_search_clicked)
        
        btn_box = Gtk.Box(spacing=5)
        btn_box.set_halign(Gtk.Align.CENTER)
        btn_icon = Gtk.Image.new_from_icon_name("edit-find-symbolic", Gtk.IconSize.BUTTON)
        btn_lbl = Gtk.Label(label="ARA")
        btn_lbl.set_markup("<b>ARA</b>")
        btn_box.pack_start(btn_icon, False, False, 0)
        btn_box.pack_start(btn_lbl, False, False, 0)
        search_btn.add(btn_box)
        
        input_box.pack_start(search_btn, False, False, 0)
        vbox.pack_start(input_box, False, False, 0)
        
        info_lbl = Gtk.Label()
        info_lbl.set_markup("<span size='small' foreground='#888888'>Spotify playlistleri otomatik olarak ayrı klasöre indirilir.</span>")
        info_lbl.set_xalign(0)
        vbox.pack_start(info_lbl, False, False, 0)

        self.main_content.pack_start(vbox, False, False, 0)

    # ============= HIZLI İŞLEMLER =============
    def create_quick_actions_section(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        
        header = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        lbl = Gtk.Label()
        lbl.set_markup("<b>Hızlı İşlemler</b>")
        lbl.set_xalign(0)
        header.pack_start(lbl, False, False, 0)
        header.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 0)
        vbox.pack_start(header, False, False, 0)

        grid = Gtk.Grid()
        grid.set_column_spacing(20)
        grid.set_row_spacing(10)
        grid.set_column_homogeneous(True)

        def mk_btn(label, icon_name, callback):
            b = Gtk.Button()
            b.set_size_request(-1, 50) # Yükseklik ayarı
            b.connect("clicked", callback)
            b.get_style_context().add_class("quick-action-btn")  # CSS class
            
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            box.set_halign(Gtk.Align.CENTER)
            img = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.BUTTON)
            lbl = Gtk.Label(label=label)
            
            box.pack_start(img, False, False, 0)
            box.pack_start(lbl, False, False, 0)
            b.add(box)
            return b

        btn1 = mk_btn("TXT Yükle", "text-x-generic", self.on_toplu_liste_clicked)
        btn2 = mk_btn("Yapıştır", "edit-paste", self.paste_clipboard)

        grid.attach(btn1, 0, 0, 1, 1)
        grid.attach(btn2, 1, 0, 1, 1)

        vbox.pack_start(grid, False, False, 0)
        self.main_content.pack_start(vbox, False, False, 0)

    # ============= SONUÇ ALANI =============
    def create_results_section(self):
        self.result_content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        self.main_content.pack_start(self.result_content_box, True, True, 0)
        self.show_placeholder()

    def show_placeholder(self):
        self.clear_results()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)
        box.set_margin_top(60)
        
        icon = Gtk.Image.new_from_icon_name("edit-find-symbolic", Gtk.IconSize.DIALOG)
        icon.set_pixel_size(96) 
        icon.set_opacity(0.3)
        
        lbl = Gtk.Label()
        lbl.set_markup("<span size='large' foreground='gray'>Arama yapmak veya link eklemek için yukarıyı kullanın.</span>")
        
        box.pack_start(icon, False, False, 0)
        box.pack_start(lbl, False, False, 0)
        self.result_content_box.pack_start(box, True, True, 0)
        self.result_content_box.show_all()

    def clear_results(self):
        for child in self.result_content_box.get_children():
            self.result_content_box.remove(child)

    # ============= İŞLEM MANTIĞI =============
    def on_search_clicked(self, widget):
        query = self.search_entry.get_text().strip()
        if not query: return

        self.clear_results()
        self.show_loading("Analiz ediliyor...")

        is_spotify = "http://googleusercontent.com/spotify.com/" in query or "spotify.link" in query or "open.spotify.com" in query
        is_youtube = "youtube.com" in query or "youtu.be" in query

        if (is_spotify or is_youtube) and self.queue_manager:
            is_playlist = "list=" in query or "/playlist/" in query or "/album/" in query
            self.queue_manager.add_url_to_queue(query, is_playlist=is_playlist)
            
            msg = (
                "✅ <b>Link Kuyruğa Alındı!</b>\n\n"
                "İndirmeyi başlatmak için sol menüden\n"
                "<b>'İndirilenler'</b> sekmesine gidin."
            )
            self.display_message(msg, False)
            return

        if self.executor and self.yt_client:
            self.executor.submit(self.run_search_thread, query)
        else:
            self.display_message("YouTube istemcisi hazır değil.", True)

    def run_search_thread(self, query):
        try:
            results = self.yt_client.search_videos(query, 15)
            GLib.idle_add(self.display_results, results)
        except Exception as e:
            GLib.idle_add(self.display_message, f"Arama Hatası: {e}", True)

    def display_results(self, results):
        self.clear_results()
        if not results:
            self.display_message("Sonuç bulunamadı.", True)
            return

        list_box = Gtk.ListBox()
        list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        list_box.set_spacing(10)
        
        for vid in results:
            row = Gtk.ListBoxRow()
            row.add(self.create_video_card(vid))
            list_box.add(row)
            
        self.result_content_box.pack_start(list_box, True, True, 0)
        self.result_content_box.show_all()

    def create_video_card(self, data):
        frame = Gtk.Frame()
        frame.set_shadow_type(Gtk.ShadowType.ETCHED_OUT)
        frame.set_name("video-card") 
        
        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
        main_box.set_margin_top(10)
        main_box.set_margin_bottom(10)
        main_box.set_margin_start(10)
        main_box.set_margin_end(10)
        
        img = Gtk.Image()
        img.set_size_request(140, 80)
        img.set_from_icon_name("video-x-generic", Gtk.IconSize.DIALOG)
        main_box.pack_start(img, False, False, 0)
        
        if GdkPixbuf and data.get('thumbnail') and requests:
            self.executor.submit(self.load_img, img, data['thumbnail'])

        v = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        v.set_valign(Gtk.Align.CENTER)
        
        title = Gtk.Label()
        title.set_markup(f"<span size='medium' weight='bold'>{data.get('title', 'Video')}</span>")
        title.set_xalign(0)
        title.set_line_wrap(True)
        title.set_max_width_chars(60)
        
        meta_text = f"<span foreground='#777777'>{data.get('channel', '')} • {data.get('duration', '')}</span>"
        meta = Gtk.Label()
        meta.set_markup(meta_text)
        meta.set_xalign(0)
        
        v.pack_start(title, False, False, 0)
        v.pack_start(meta, False, False, 0)
        main_box.pack_start(v, True, True, 0)
        
        btn = Gtk.Button()
        btn.set_valign(Gtk.Align.CENTER)
        
        b_box = Gtk.Box(spacing=5)
        b_icon = Gtk.Image.new_from_icon_name("list-add-symbolic", Gtk.IconSize.BUTTON)
        b_lbl = Gtk.Label(label="Sıraya Ekle")
        b_box.pack_start(b_icon, False, False, 0)
        b_box.pack_start(b_lbl, False, False, 0)
        btn.add(b_box)
        
        btn.connect("clicked", lambda b: self.download_single(data))
        main_box.pack_end(btn, False, False, 0)
        
        frame.add(main_box)
        return frame

    def download_single(self, data):
        if self.queue_manager:
            self.queue_manager.add_url_to_queue(data['url'])
            self.main_window.show_notification(f"{data['title']} kuyruğa eklendi", "success")
        elif hasattr(self.main_window, 'download_manager'):
            self.main_window.download_manager.add_download(data['url'])

    def load_img(self, img, url):
        try:
            r = requests.get(url, timeout=5)
            loader = GdkPixbuf.PixbufLoader()
            loader.write(r.content)
            loader.close()
            pix = loader.get_pixbuf().scale_simple(140, 80, GdkPixbuf.InterpType.BILINEAR)
            GLib.idle_add(img.set_from_pixbuf, pix)
        except: pass

    def show_loading(self, text):
        self.clear_results()
        
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)
        
        spinner = Gtk.Spinner()
        spinner.set_size_request(32, 32)
        spinner.start()
        
        lbl = Gtk.Label(label=text)
        
        box.pack_start(spinner, False, False, 0)
        box.pack_start(lbl, False, False, 0)
        
        self.result_content_box.pack_start(box, True, True, 50)
        self.result_content_box.show_all()

    def display_message(self, text, is_error):
        self.clear_results()
        icon_name = "dialog-error" if is_error else "emblem-default"
        img = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.DIALOG)
        img.set_pixel_size(64)
        
        lbl = Gtk.Label()
        lbl.set_justify(Gtk.Justification.CENTER)
        lbl.set_markup(f"<span size='large'>{text}</span>")
        
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        box.set_valign(Gtk.Align.CENTER)
        box.set_margin_top(40)
        
        box.pack_start(img, False, False, 0)
        box.pack_start(lbl, False, False, 0)
        
        self.result_content_box.pack_start(box, True, True, 20)
        self.result_content_box.show_all()

    def paste_clipboard(self, btn):
        cb = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        txt = cb.wait_for_text()
        if txt:
            self.search_entry.set_text(txt.strip())
            self.on_search_clicked(None)

    def on_toplu_liste_clicked(self, btn):
        dialog = Gtk.FileChooserDialog(
            title="Playlist Dosyası Seç (.txt)",
            parent=self.main_window,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        
        filter_text = Gtk.FileFilter()
        filter_text.set_name("Metin Dosyaları")
        filter_text.add_mime_type("text/plain")
        dialog.add_filter(filter_text)

        if dialog.run() == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            threading.Thread(target=self.load_from_txt, args=(filename,), daemon=True).start()
        
        dialog.destroy()

    def load_from_txt(self, filename):
        """TXT dosyasından linkleri yükle - TAMAMEN ARKA PLANDA"""
        # Hemen loading göster
        GLib.idle_add(self.show_loading, "Dosya okunuyor...")
        
        # Tüm işlemi arka plana at
        threading.Thread(target=self._load_txt_background, args=(filename,), daemon=True).start()
    
    def _load_txt_background(self, filename):
        """TXT yükleme - arka plan thread'i"""
        try:
            # TXT dosya adını al (klasör için)
            import os
            txt_basename = os.path.splitext(os.path.basename(filename))[0]
            
            # Dosyayı oku
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    raw_lines = f.readlines()
            except UnicodeDecodeError:
                with open(filename, 'r', encoding='cp1254') as f:
                    raw_lines = f.readlines()

            # Linkleri çıkar
            unique_links = set() 
            valid_links = []
            url_pattern = re.compile(r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)')

            for line in raw_lines:
                line = line.strip()
                if not line or line.startswith("#"): 
                    continue
                match = url_pattern.search(line)
                if match:
                    clean = match.group(0)
                    if clean not in unique_links:
                        unique_links.add(clean)
                        valid_links.append(clean)
            
            if not valid_links:
                GLib.idle_add(self.display_message, "Geçerli link bulunamadı.", True)
                return

            if not self.queue_manager:
                GLib.idle_add(self.display_message, "Queue Manager başlatılamadı!", True)
                return

            total = len(valid_links)
            GLib.idle_add(self.main_window.status_label.set_text, f"📂 {total} link bulundu, ekleniyor...")

            # Linkleri SIRALI ama HIZLI ekle
            added = 0
            for i, url in enumerate(valid_links, 1):
                # Her 10 linkte bir UI güncelle (daha az güncelleme = daha hızlı)
                if i % 10 == 0:
                    GLib.idle_add(self.main_window.status_label.set_text, f"Ekleniyor ({i}/{total})...")
                
                is_spotify = "open.spotify.com" in url or "spotify.link" in url
                is_pl = "list=" in url or "/playlist/" in url or "/album/" in url or is_spotify

                # TXT adını da gönder (klasör için)
                self.queue_manager.add_url_to_queue(
                    url, 
                    is_playlist=is_pl, 
                    clear_queue=False,
                    batch_name=txt_basename  # ← YENİ: TXT dosya adı
                )
                added += 1
                
                # Çok kısa bekleme (rate limit için)
                time.sleep(0.2)

            # Tamamlandı mesajı
            final_msg = (
                f"✅ <b>{added} Link Kuyruğa Eklendi</b>\n\n"
                "İşlemleri başlatmak için:\n"
                "1. Sol menüden <b>'İndirilenler'</b> sekmesine gidin.\n"
                "2. Listeyi kontrol edin.\n"
                "3. <b>'İndirmeyi Başlat'</b> butonuna basın."
            )
            GLib.idle_add(self.display_message, final_msg, False)
            GLib.idle_add(self.main_window.status_label.set_text, f"✅ {added} link eklendi")

        except Exception as e:
            GLib.idle_add(self.display_message, f"Hata: {str(e)}", True)