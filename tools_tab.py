#!/usr/bin/env python3
"""
DownX - Tools Tab (FULL VERSION)
Spotify metadata → YouTube eşleştirme
Gelişmiş kontrol ve TXT export
"""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Pango
import os
import threading
import subprocess
from pathlib import Path
import json
import re
from difflib import SequenceMatcher


class ToolsTab(Gtk.Box):
    """Araçlar sekmesi - Gelişmiş Spotify→YouTube matcher"""
    
    def __init__(self, parent_window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.parent = parent_window
        self.logger = parent_window.logger
        
        self.output_folder = None
        self.matched_songs = []
        self.missing_songs = []
        self.is_running = False
        
        # Ana container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        main_box.set_margin_top(12)
        main_box.set_margin_bottom(12)
        main_box.set_margin_start(20)
        main_box.set_margin_end(20)
        
        # Başlık
        header = self.create_header()
        main_box.pack_start(header, False, False, 0)
        
        # Grid Layout
        grid = Gtk.Grid()
        grid.set_row_spacing(8)
        grid.set_column_spacing(12)
        grid.set_column_homogeneous(True)
        
        # Sol: Matcher
        matcher_box = self.create_matcher_section()
        grid.attach(matcher_box, 0, 0, 1, 1)
        
        # Sağ: Sistem
        system_box = self.create_system_section()
        grid.attach(system_box, 1, 0, 1, 1)
        
        main_box.pack_start(grid, False, False, 0)
        
        # Progress bar
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_show_text(True)
        self.progress_bar.set_text("Hazır")
        main_box.pack_start(self.progress_bar, False, False, 0)
        
        # Log
        log_frame = self.create_log()
        main_box.pack_start(log_frame, True, True, 0)
        
        self.pack_start(main_box, True, True, 0)
        self.show_all()
    
    def create_header(self):
        """Başlık"""
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        
        title = Gtk.Label()
        title.set_markup("<span size='large' weight='bold'>🔄 Spotify → YouTube Matcher</span>")
        title.set_halign(Gtk.Align.START)
        header.pack_start(title, False, False, 0)
        
        header.pack_start(Gtk.Box(), True, True, 0)
        
        version = Gtk.Label()
        version.set_markup("<span size='small' alpha='60%'>v5.0 - Gelişmiş Eşleştirme</span>")
        header.pack_end(version, False, False, 0)
        
        return header
    
    def create_matcher_section(self):
        """Matcher bölümü"""
        frame = Gtk.Frame()
        frame.set_label("🎵 Eşleştirme")
        
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        box.set_margin_start(12)
        box.set_margin_end(12)
        
        # Açıklama
        desc = Gtk.Label()
        desc.set_markup(
            "<span size='small'>"
            "MP3 klasörü seç → Spotify metadata oku → YouTube'da ara\n"
            "Bulunamayan şarkılar TXT'ye kaydedilir"
            "</span>"
        )
        desc.set_line_wrap(True)
        desc.set_halign(Gtk.Align.START)
        box.pack_start(desc, False, False, 0)
        
        # Klasör seç
        self.folder_btn = Gtk.Button(label="📁 MP3 Klasörü Seç")
        self.folder_btn.set_size_request(-1, 35)
        self.folder_btn.connect("clicked", self.select_folder)
        box.pack_start(self.folder_btn, False, False, 0)
        
        # Seçenekler
        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        box.pack_start(sep, False, False, 4)
        
        opt_label = Gtk.Label()
        opt_label.set_markup("<b>Seçenekler:</b>")
        opt_label.set_halign(Gtk.Align.START)
        box.pack_start(opt_label, False, False, 0)
        
        # Minimum eşleşme skoru
        match_box = Gtk.Box(spacing=8)
        match_label = Gtk.Label(label="Min. Eşleşme:")
        match_box.pack_start(match_label, False, False, 0)
        
        self.match_spin = Gtk.SpinButton()
        self.match_spin.set_range(50, 100)
        self.match_spin.set_value(85)
        self.match_spin.set_increments(5, 10)
        self.match_spin.set_tooltip_text("Minimum %85 eşleşme önerilir")
        match_box.pack_start(self.match_spin, False, False, 0)
        
        match_pct = Gtk.Label(label="%")
        match_box.pack_start(match_pct, False, False, 0)
        box.pack_start(match_box, False, False, 0)
        
        # Auto-fix
        self.auto_fix_check = Gtk.CheckButton(label="Otomatik düzelt (artist - title)")
        self.auto_fix_check.set_active(True)
        self.auto_fix_check.set_tooltip_text("'ArtistName - SongTitle' formatını otomatik düzelt")
        box.pack_start(self.auto_fix_check, False, False, 0)
        
        # Başlat butonu
        self.start_btn = Gtk.Button(label="🚀 Eşleştirmeyi Başlat")
        self.start_btn.set_size_request(-1, 40)
        self.start_btn.get_style_context().add_class("suggested-action")
        self.start_btn.connect("clicked", self.start_matching)
        box.pack_start(self.start_btn, False, False, 0)
        
        # Durdur butonu
        self.stop_btn = Gtk.Button(label="⏹️ Durdur")
        self.stop_btn.set_size_request(-1, 35)
        self.stop_btn.set_sensitive(False)
        self.stop_btn.connect("clicked", self.stop_matching)
        box.pack_start(self.stop_btn, False, False, 0)
        
        # İstatistikler
        sep2 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        box.pack_start(sep2, False, False, 4)
        
        self.stats_label = Gtk.Label()
        self.stats_label.set_markup("<span size='small'><b>İstatistik:</b> Henüz yok</span>")
        self.stats_label.set_halign(Gtk.Align.START)
        box.pack_start(self.stats_label, False, False, 0)
        
        frame.add(box)
        return frame
    
    def create_system_section(self):
        """Sistem bilgisi"""
        frame = Gtk.Frame()
        frame.set_label("ℹ️ Sistem")
        
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        box.set_margin_start(12)
        box.set_margin_end(12)
        
        # Bağımlılıklar
        deps_label = Gtk.Label()
        deps_label.set_markup("<b>Bağımlılıklar:</b>")
        deps_label.set_halign(Gtk.Align.START)
        box.pack_start(deps_label, False, False, 0)
        
        deps = [
            ("mutagen", self.check_mutagen()),
            ("yt-dlp", self.check_ytdlp()),
            ("FFmpeg", self.check_ffmpeg())
        ]
        
        for name, status in deps:
            lbl = Gtk.Label()
            lbl.set_markup(f"<span size='small'>{name}: {status}</span>")
            lbl.set_halign(Gtk.Align.START)
            box.pack_start(lbl, False, False, 0)
        
        # Temizlik
        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        box.pack_start(sep, False, False, 4)
        
        clean_label = Gtk.Label()
        clean_label.set_markup("<b>Önbellek:</b>")
        clean_label.set_halign(Gtk.Align.START)
        box.pack_start(clean_label, False, False, 0)
        
        self.cache_label = Gtk.Label()
        self.update_cache_info()
        self.cache_label.set_halign(Gtk.Align.START)
        box.pack_start(self.cache_label, False, False, 0)
        
        clean_btn = Gtk.Button(label="🗑️ Önbelleği Temizle")
        clean_btn.set_size_request(-1, 32)
        clean_btn.connect("clicked", self.cleanup_cache)
        box.pack_start(clean_btn, False, False, 0)
        
        # Export
        sep2 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        box.pack_start(sep2, False, False, 4)
        
        export_label = Gtk.Label()
        export_label.set_markup("<b>Export:</b>")
        export_label.set_halign(Gtk.Align.START)
        box.pack_start(export_label, False, False, 0)
        
        self.export_missing_btn = Gtk.Button(label="💾 Eksikleri TXT'ye Kaydet")
        self.export_missing_btn.set_size_request(-1, 32)
        self.export_missing_btn.set_sensitive(False)
        self.export_missing_btn.connect("clicked", self.export_missing)
        box.pack_start(self.export_missing_btn, False, False, 0)
        
        self.export_all_btn = Gtk.Button(label="📋 Tüm Sonuçları Kaydet")
        self.export_all_btn.set_size_request(-1, 32)
        self.export_all_btn.set_sensitive(False)
        self.export_all_btn.connect("clicked", self.export_all)
        box.pack_start(self.export_all_btn, False, False, 0)
        
        frame.add(box)
        return frame
    
    def create_log(self):
        """Log görünümü"""
        frame = Gtk.Frame()
        frame.set_label("📋 İşlem Günlüğü")
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_size_request(-1, 200)
        
        self.log_view = Gtk.TextView()
        self.log_view.set_editable(False)
        self.log_view.set_cursor_visible(False)
        self.log_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.log_view.set_margin_top(6)
        self.log_view.set_margin_bottom(6)
        self.log_view.set_margin_start(8)
        self.log_view.set_margin_end(8)
        
        font_desc = Pango.FontDescription("monospace 9")
        self.log_view.modify_font(font_desc)
        
        self.log_buffer = self.log_view.get_buffer()
        
        scrolled.add(self.log_view)
        frame.add(scrolled)
        
        return frame
    
    # ==================== HELPER METHODS ====================
    
    def log_message(self, message: str):
        """Log mesajı ekle"""
        GLib.idle_add(self._append_log, message)
    
    def _append_log(self, message: str):
        """Log buffer'a ekle"""
        end_iter = self.log_buffer.get_end_iter()
        self.log_buffer.insert(end_iter, f"{message}\n")
        
        mark = self.log_buffer.create_mark(None, end_iter, False)
        self.log_view.scroll_to_mark(mark, 0.0, True, 0.0, 1.0)
        
        return False
    
    def update_progress(self, fraction, text=""):
        """Progress bar güncelle"""
        GLib.idle_add(self._set_progress, fraction, text)
    
    def _set_progress(self, fraction, text):
        self.progress_bar.set_fraction(fraction)
        if text:
            self.progress_bar.set_text(text)
        return False
    
    def update_stats(self, total, matched, missing):
        """İstatistik güncelle"""
        GLib.idle_add(self._set_stats, total, matched, missing)
    
    def _set_stats(self, total, matched, missing):
        self.stats_label.set_markup(
            f"<span size='small'><b>İstatistik:</b> "
            f"Toplam: {total} | "
            f"<span foreground='#10b981'>Eşleşti: {matched}</span> | "
            f"<span foreground='#ef4444'>Eksik: {missing}</span>"
            "</span>"
        )
        return False
    
    # ==================== EVENT HANDLERS ====================
    
    def select_folder(self, button):
        """Klasör seç"""
        dialog = Gtk.FileChooserDialog(
            title="MP3 Klasörü Seç",
            parent=self.parent,
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )
        
        if dialog.run() == Gtk.ResponseType.OK:
            self.output_folder = dialog.get_filename()
            self.folder_btn.set_label(f"📁 {Path(self.output_folder).name}")
            self.log_message(f"✅ Klasör seçildi: {self.output_folder}")
        
        dialog.destroy()
    
    def start_matching(self, button):
        """Eşleştirmeyi başlat"""
        if not self.output_folder:
            self.parent.show_notification("Klasör seçin!", "warning")
            return
        
        if self.is_running:
            return
        
        self.is_running = True
        self.start_btn.set_sensitive(False)
        self.stop_btn.set_sensitive(True)
        self.export_missing_btn.set_sensitive(False)
        self.export_all_btn.set_sensitive(False)
        
        self.matched_songs = []
        self.missing_songs = []
        
        self.log_message("🚀 Eşleştirme başlatıldı...")
        
        thread = threading.Thread(target=self._run_matching, daemon=True)
        thread.start()
    
    def stop_matching(self, button):
        """Eşleştirmeyi durdur"""
        self.is_running = False
        self.log_message("⏹️ Durdurma isteği gönderildi...")
    
    # ==================== MAIN MATCHING LOGIC ====================
    
    def _run_matching(self):
        """Ana eşleştirme işlemi"""
        try:
            # 1. MP3 dosyalarını bul
            self.log_message("📂 MP3 dosyaları taranıyor...")
            mp3_files = list(Path(self.output_folder).rglob("*.mp3"))
            
            if not mp3_files:
                self.log_message("❌ MP3 dosyası bulunamadı!")
                self._finish_matching()
                return
            
            total = len(mp3_files)
            self.log_message(f"✓ {total} MP3 dosyası bulundu")
            
            # 2. Her dosyayı işle
            for idx, mp3_file in enumerate(mp3_files, 1):
                if not self.is_running:
                    self.log_message("⏹️ Kullanıcı tarafından durduruldu")
                    break
                
                progress = idx / total
                self.update_progress(progress, f"{idx}/{total}")
                
                result = self._process_file(mp3_file)
                
                if result['matched']:
                    self.matched_songs.append(result)
                else:
                    self.missing_songs.append(result)
                
                # İstatistik güncelle
                self.update_stats(idx, len(self.matched_songs), len(self.missing_songs))
            
            # 3. Özet
            self._finish_matching()
            
        except Exception as e:
            self.log_message(f"❌ Kritik hata: {e}")
            import traceback
            traceback.print_exc()
            self._finish_matching()
    
    def _process_file(self, mp3_file: Path) -> dict:
        """Tek dosyayı işle"""
        try:
            # 1. Metadata oku
            metadata = self._read_metadata(mp3_file)
            
            if not metadata:
                self.log_message(f"⚠️ Metadata okunamadı: {mp3_file.name}")
                return {
                    'file': str(mp3_file),
                    'filename': mp3_file.name,
                    'artist': "Bilinmiyor",
                    'title': mp3_file.stem,
                    'matched': False,
                    'youtube_url': None,
                    'match_score': 0
                }
            
            artist = metadata.get('artist', 'Bilinmiyor')
            title = metadata.get('title', mp3_file.stem)
            
            # 2. YouTube'da ara
            self.log_message(f"🔍 Aranıyor: {artist} - {title}")
            
            youtube_result = self._search_youtube(artist, title)
            
            if youtube_result:
                # 3. Eşleşme skoru hesapla
                min_score = self.match_spin.get_value()
                score = self._calculate_match_score(
                    artist, title,
                    youtube_result['artist'], youtube_result['title']
                )
                
                matched = score >= min_score
                
                if matched:
                    self.log_message(f"  ✓ Bulundu (%{score:.0f}): {youtube_result['url']}")
                else:
                    self.log_message(f"  ✗ Eşleşme düşük (%{score:.0f})")
                
                return {
                    'file': str(mp3_file),
                    'filename': mp3_file.name,
                    'artist': artist,
                    'title': title,
                    'matched': matched,
                    'youtube_url': youtube_result['url'] if matched else None,
                    'youtube_title': youtube_result['title'],
                    'match_score': score
                }
            else:
                self.log_message(f"  ✗ YouTube'da bulunamadı")
                return {
                    'file': str(mp3_file),
                    'filename': mp3_file.name,
                    'artist': artist,
                    'title': title,
                    'matched': False,
                    'youtube_url': None,
                    'match_score': 0
                }
                
        except Exception as e:
            self.log_message(f"❌ Hata ({mp3_file.name}): {e}")
            return {
                'file': str(mp3_file),
                'filename': mp3_file.name,
                'artist': "Bilinmiyor",
                'title': mp3_file.stem,
                'matched': False,
                'youtube_url': None,
                'match_score': 0
            }
    
    def _read_metadata(self, mp3_file: Path) -> dict:
        """MP3 metadata oku"""
        try:
            from mutagen.mp3 import MP3
            from mutagen.id3 import ID3
            
            audio = MP3(mp3_file)
            
            # Otomatik düzelt aktifse dosya adından parse et
            if self.auto_fix_check.get_active() and ' - ' in mp3_file.stem:
                parts = mp3_file.stem.split(' - ', 1)
                fallback_artist = parts[0].strip()
                fallback_title = parts[1].strip()
            else:
                fallback_artist = "Bilinmiyor"
                fallback_title = mp3_file.stem
            
            # ID3 tags
            artist = str(audio.get('TPE1', fallback_artist))
            title = str(audio.get('TIT2', fallback_title))
            
            # Liste ise ilk elemanı al
            if isinstance(artist, list):
                artist = artist[0] if artist else fallback_artist
            if isinstance(title, list):
                title = title[0] if title else fallback_title
            
            return {
                'artist': artist.strip(),
                'title': title.strip()
            }
            
        except Exception as e:
            # Fallback: dosya adından parse et
            if self.auto_fix_check.get_active() and ' - ' in mp3_file.stem:
                parts = mp3_file.stem.split(' - ', 1)
                return {
                    'artist': parts[0].strip(),
                    'title': parts[1].strip()
                }
            return None
    
    def _search_youtube(self, artist: str, title: str) -> dict:
        """YouTube'da ara"""
        try:
            # YouTube client kullan (parent'tan)
            if not hasattr(self.parent, 'yt_client') or not self.parent.yt_client:
                return None
            
            query = f"{artist} {title}"
            results = self.parent.yt_client.search_videos(query, limit=1)
            
            if results:
                result = results[0]
                return {
                    'url': result['url'],
                    'title': result['title'],
                    'artist': result.get('channel', artist),
                }
            
            return None
            
        except Exception as e:
            return None
    
    def _calculate_match_score(self, artist1, title1, artist2, title2) -> float:
        """Eşleşme skoru hesapla (0-100)"""
        # Normalize
        artist1 = self._normalize_string(artist1)
        title1 = self._normalize_string(title1)
        artist2 = self._normalize_string(artist2)
        title2 = self._normalize_string(title2)
        
        # Artist benzerliği
        artist_score = SequenceMatcher(None, artist1, artist2).ratio()
        
        # Title benzerliği
        title_score = SequenceMatcher(None, title1, title2).ratio()
        
        # Ortalama (%30 artist, %70 title)
        final_score = (artist_score * 0.3 + title_score * 0.7) * 100
        
        return final_score
    
    def _normalize_string(self, s: str) -> str:
        """String normalize et"""
        # Küçük harf
        s = s.lower()
        
        # Özel karakterleri kaldır
        s = re.sub(r'[^a-z0-9\s]', '', s)
        
        # Fazla boşlukları temizle
        s = ' '.join(s.split())
        
        return s
    
    def _finish_matching(self):
        """Eşleştirme bitti"""
        GLib.idle_add(self._cleanup_ui)
        
        total = len(self.matched_songs) + len(self.missing_songs)
        matched = len(self.matched_songs)
        missing = len(self.missing_songs)
        
        self.log_message("\n" + "="*60)
        self.log_message("📊 SONUÇ:")
        self.log_message(f"  Toplam:    {total}")
        self.log_message(f"  ✓ Eşleşti: {matched} (%{matched/total*100:.1f})" if total > 0 else "")
        self.log_message(f"  ✗ Eksik:   {missing} (%{missing/total*100:.1f})" if total > 0 else "")
        self.log_message("="*60)
        
        if missing > 0:
            self.log_message(f"\n💡 {missing} eksik şarkı var. 'Eksikleri TXT'ye Kaydet' butonunu kullanabilirsin.")
        
        self.update_progress(1.0, "Tamamlandı")
        GLib.idle_add(self.parent.show_notification, f"Tamamlandı! {matched}/{total} eşleşti", "success")
    
    def _cleanup_ui(self):
        """UI temizle"""
        self.is_running = False
        self.start_btn.set_sensitive(True)
        self.stop_btn.set_sensitive(False)
        
        if self.missing_songs:
            self.export_missing_btn.set_sensitive(True)
        
        if self.matched_songs or self.missing_songs:
            self.export_all_btn.set_sensitive(True)
        
        return False
    
    # ==================== EXPORT ====================
    
    def export_missing(self, button):
        """Eksik şarkıları TXT'ye kaydet"""
        if not self.missing_songs:
            self.parent.show_notification("Eksik şarkı yok!", "info")
            return
        
        dialog = Gtk.FileChooserDialog(
            title="Eksikleri Kaydet",
            parent=self.parent,
            action=Gtk.FileChooserAction.SAVE
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE, Gtk.ResponseType.OK
        )
        dialog.set_current_name("bulunamayan_sarkılar.txt")
        
        if dialog.run() == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("# Bulunamayan Şarkılar\n")
                    f.write(f"# Toplam: {len(self.missing_songs)}\n\n")
                    
                    for song in self.missing_songs:
                        f.write(f"{song['artist']} - {song['title']}\n")
                
                self.log_message(f"💾 Eksikler kaydedildi: {filename}")
                self.parent.show_notification("Eksikler kaydedildi!", "success")
                
            except Exception as e:
                self.log_message(f"❌ Kayıt hatası: {e}")
                self.parent.show_notification(f"Hata: {e}", "error")
        
        dialog.destroy()
    
    def export_all(self, button):
        """Tüm sonuçları JSON olarak kaydet"""
        if not self.matched_songs and not self.missing_songs:
            self.parent.show_notification("Sonuç yok!", "info")
            return
        
        dialog = Gtk.FileChooserDialog(
            title="Tüm Sonuçları Kaydet",
            parent=self.parent,
            action=Gtk.FileChooserAction.SAVE
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE, Gtk.ResponseType.OK
        )
        dialog.set_current_name("eslestirme_sonuclari.json")
        
        if dialog.run() == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            
            try:
                data = {
                    'total': len(self.matched_songs) + len(self.missing_songs),
                    'matched': len(self.matched_songs),
                    'missing': len(self.missing_songs),
                    'matched_songs': self.matched_songs,
                    'missing_songs': self.missing_songs
                }
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                self.log_message(f"💾 Tüm sonuçlar kaydedildi: {filename}")
                self.parent.show_notification("Sonuçlar kaydedildi!", "success")
                
            except Exception as e:
                self.log_message(f"❌ Kayıt hatası: {e}")
                self.parent.show_notification(f"Hata: {e}", "error")
        
        dialog.destroy()
    
    # ==================== SYSTEM INFO ====================
    
    def check_mutagen(self):
        """Mutagen kontrolü"""
        try:
            import mutagen
            return f"<span foreground='#10b981'>✓ {mutagen.version_string}</span>"
        except:
            return "<span foreground='#ef4444'>✗ Yok</span>"
    
    def check_ytdlp(self):
        """yt-dlp kontrolü"""
        try:
            result = subprocess.run(
                ['yt-dlp', '--version'],
                capture_output=True,
                text=True,
                timeout=2
            )
            version = result.stdout.strip()[:10]
            return f"<span foreground='#10b981'>✓ {version}</span>"
        except:
            return "<span foreground='#ef4444'>✗ Yok</span>"
    
    def check_ffmpeg(self):
        """FFmpeg kontrolü"""
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                timeout=2
            )
            if result.returncode == 0:
                return "<span foreground='#10b981'>✓ Kurulu</span>"
            return "<span foreground='#ef4444'>✗ Yok</span>"
        except:
            return "<span foreground='#ef4444'>✗ Yok</span>"
    
    def update_cache_info(self):
        """Cache bilgisi"""
        try:
            cache_dir = Path.home() / ".cache" / "downx"
            if cache_dir.exists():
                size = sum(f.stat().st_size for f in cache_dir.rglob('*') if f.is_file())
                size_mb = size / (1024 * 1024)
                self.cache_label.set_markup(f"<span size='small'>Boyut: {size_mb:.1f} MB</span>")
            else:
                self.cache_label.set_markup("<span size='small'>Boyut: 0 MB</span>")
        except:
            self.cache_label.set_markup("<span size='small'>Boyut: ?</span>")
    
    def cleanup_cache(self, button):
        """Cache temizle"""
        try:
            cache_dir = Path.home() / ".cache" / "downx"
            if cache_dir.exists():
                import shutil
                shutil.rmtree(cache_dir)
                cache_dir.mkdir(parents=True, exist_ok=True)
                
                self.log_message("✅ Önbellek temizlendi")
                self.parent.show_notification("Temizlendi!", "success")
                self.update_cache_info()
            else:
                self.log_message("ℹ️ Önbellek zaten boş")
        except Exception as e:
            self.log_message(f"❌ {str(e)}")