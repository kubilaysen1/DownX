#!/usr/bin/env python3
"""
4KTube Free - Settings Tab (PERFECT & STABLE)
Modern, güzel, GTK uyarısız, segfault-free tasarım
"""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import os
from pathlib import Path
from settings import GLOBAL_CONFIG, save_config, update_download_dir


class SettingsTab(Gtk.Box):
    """Modern ve Güvenli Ayarlar Sekmesi"""
    
    def __init__(self, parent_window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.parent = parent_window
        self.logger = parent_window.logger
        
        # Config temizliği
        self.cleanup_old_config()
        
        # ScrolledWindow (güvenli)
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        # Ana container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Modern başlık
        header = self.create_modern_header()
        main_box.pack_start(header, False, False, 0)
        
        # Preset bar
        preset_bar = self.create_preset_bar()
        main_box.pack_start(preset_bar, False, False, 0)
        
        # Content area
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        content.set_margin_top(20)
        content.set_margin_bottom(20)
        content.set_margin_start(30)
        content.set_margin_end(30)
        
        # Temel Ayarlar
        basic_section = self.create_basic_section()
        content.pack_start(basic_section, False, False, 0)
        
        # Kalite Ayarları
        quality_section = self.create_quality_section()
        content.pack_start(quality_section, False, False, 0)
        
        # Gelişmiş (Expander ile)
        advanced_expander = self.create_advanced_expander()
        content.pack_start(advanced_expander, False, False, 0)
        
        main_box.pack_start(content, True, True, 0)
        
        # Alt butonlar
        button_box = self.create_action_buttons()
        main_box.pack_start(button_box, False, False, 0)
        
        scroll.add(main_box)
        self.pack_start(scroll, True, True, 0)
        
        # UI'ı config'den yükle
        GLib.idle_add(self.update_ui_from_config)
        
        self.show_all()
    
    def cleanup_old_config(self):
        """Eski config temizliği"""
        changed = False
        
        if 'mode' in GLOBAL_CONFIG and 'download_mode' not in GLOBAL_CONFIG:
            GLOBAL_CONFIG['download_mode'] = GLOBAL_CONFIG['mode']
            del GLOBAL_CONFIG['mode']
            changed = True
        
        if 'download_mode' not in GLOBAL_CONFIG:
            GLOBAL_CONFIG['download_mode'] = 'audio'
            changed = True
        
        if changed:
            save_config()
            self.logger.info("✅ Config güncellendi")
    
    def create_modern_header(self):
        """Modern başlık"""
        header_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        inner_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        inner_box.set_margin_top(20)
        inner_box.set_margin_bottom(20)
        inner_box.set_margin_start(30)
        inner_box.set_margin_end(30)
        
        # Sol: Başlık
        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        
        title = Gtk.Label()
        title.set_markup("<span size='xx-large' weight='bold'>⚙️ Ayarlar</span>")
        title.set_halign(Gtk.Align.START)
        title_box.pack_start(title, False, False, 0)
        
        subtitle = Gtk.Label()
        subtitle.set_markup("<span size='small' alpha='70%'>İndirme tercihlerini özelleştir</span>")
        subtitle.set_halign(Gtk.Align.START)
        title_box.pack_start(subtitle, False, False, 0)
        
        inner_box.pack_start(title_box, True, True, 0)
        
        # Sağ: Profil göstergesi
        self.profile_label = Gtk.Label()
        self.profile_label.set_markup("<span size='large' weight='bold'>⚡ Standart</span>")
        self.profile_label.set_halign(Gtk.Align.END)
        self.profile_label.set_valign(Gtk.Align.CENTER)
        inner_box.pack_end(self.profile_label, False, False, 0)
        
        header_box.pack_start(inner_box, False, False, 0)
        
        # Separator
        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        header_box.pack_start(sep, False, False, 0)
        
        return header_box
    
    def create_preset_bar(self):
        """Hızlı profil butonları - GTK uyarısız"""
        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        bar.set_margin_top(16)
        bar.set_margin_bottom(8)
        bar.set_margin_start(30)
        bar.set_margin_end(30)
        
        label = Gtk.Label()
        label.set_markup("<span weight='bold'>Hızlı Profiller:</span>")
        bar.pack_start(label, False, False, 0)
        
        # Hızlı - Buton boyutu düzeltildi
        fast_btn = Gtk.Button(label="🚀 Hızlı (128kbps)")
        fast_btn.set_size_request(150, 45)  # 30 → 45 (GTK uyarısını önler)
        fast_btn.set_tooltip_text("Hızlı indirme, düşük kalite")
        fast_btn.connect("clicked", self.on_preset_fast)
        bar.pack_start(fast_btn, False, False, 0)
        
        # Standart
        std_btn = Gtk.Button(label="⚡ Standart (192kbps)")
        std_btn.set_size_request(150, 45)
        std_btn.set_tooltip_text("Dengeli kalite/hız (önerilen)")
        std_btn.connect("clicked", self.on_preset_standard)
        bar.pack_start(std_btn, False, False, 0)
        
        # Kaliteli
        hq_btn = Gtk.Button(label="💎 Kaliteli (320kbps)")
        hq_btn.set_size_request(150, 45)
        hq_btn.set_tooltip_text("En iyi kalite")
        hq_btn.connect("clicked", self.on_preset_hq)
        bar.pack_start(hq_btn, False, False, 0)
        
        return bar
    
    def create_basic_section(self):
        """Temel ayarlar"""
        frame = self.create_frame("🏠 Temel Ayarlar")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(16)
        box.set_margin_end(16)
        
        # İndirme modu
        mode_label = Gtk.Label()
        mode_label.set_markup("<b>📥 İndirme Modu:</b>")
        mode_label.set_halign(Gtk.Align.START)
        box.pack_start(mode_label, False, False, 0)
        
        self.download_mode_combo = Gtk.ComboBoxText()
        self.download_mode_combo.append("audio", "🎵 Sadece Müzik (MP3)")
        self.download_mode_combo.append("video+audio", "🎬 Video + Ses (MP4)")
        self.download_mode_combo.append("video", "🎬 Sadece Video")
        self.download_mode_combo.set_active_id(GLOBAL_CONFIG.get('download_mode', 'audio'))
        self.download_mode_combo.set_size_request(-1, 45)  # 40 → 45
        box.pack_start(self.download_mode_combo, False, False, 0)
        
        # Klasör
        folder_label = Gtk.Label()
        folder_label.set_markup("<b>📁 İndirme Klasörü:</b>")
        folder_label.set_halign(Gtk.Align.START)
        box.pack_start(folder_label, False, False, 0)
        
        folder_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        
        self.folder_entry = Gtk.Entry()
        self.folder_entry.set_text(str(GLOBAL_CONFIG.get('download_path', Path.home() / 'Music')))
        self.folder_entry.set_size_request(-1, 45)  # 40 → 45
        folder_box.pack_start(self.folder_entry, True, True, 0)
        
        browse_btn = Gtk.Button(label="📂 Gözat")
        browse_btn.set_size_request(120, 45)  # 100x40 → 120x45
        browse_btn.connect("clicked", self.select_download_folder)
        folder_box.pack_start(browse_btn, False, False, 0)
        
        box.pack_start(folder_box, False, False, 0)
        
        # Eşzamanlı
        concurrent_label = Gtk.Label()
        concurrent_label.set_markup("<b>⚡ Eşzamanlı İndirme:</b>")
        concurrent_label.set_halign(Gtk.Align.START)
        box.pack_start(concurrent_label, False, False, 0)
        
        concurrent_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        
        self.concurrent_spin = Gtk.SpinButton()
        self.concurrent_spin.set_range(1, 10)
        self.concurrent_spin.set_increments(1, 1)
        self.concurrent_spin.set_value(GLOBAL_CONFIG.get('max_concurrent_downloads', 3))
        self.concurrent_spin.set_size_request(120, 45)  # 100x40 → 120x45
        concurrent_box.pack_start(self.concurrent_spin, False, False, 0)
        
        tip = Gtk.Label()
        tip.set_markup("<span size='small' alpha='70%'>dosya (3-5 arası önerilir)</span>")
        concurrent_box.pack_start(tip, False, False, 0)
        
        box.pack_start(concurrent_box, False, False, 0)
        
        # Checkboxlar
        self.skip_existing_check = Gtk.CheckButton(label="✓ Var olan dosyaları atla")
        self.skip_existing_check.set_active(GLOBAL_CONFIG.get('skip_existing', True))
        box.pack_start(self.skip_existing_check, False, False, 0)
        
        self.embed_metadata_check = Gtk.CheckButton(label="✓ Metadata ekle (şarkı bilgileri)")
        self.embed_metadata_check.set_active(GLOBAL_CONFIG.get('embed_metadata', True))
        box.pack_start(self.embed_metadata_check, False, False, 0)
        
        self.embed_thumbnail_check = Gtk.CheckButton(label="✓ Kapak resmi ekle")
        self.embed_thumbnail_check.set_active(GLOBAL_CONFIG.get('embed_thumbnail', True))
        box.pack_start(self.embed_thumbnail_check, False, False, 0)
        
        frame.add(box)
        return frame
    
    def create_quality_section(self):
        """Kalite ayarları"""
        frame = self.create_frame("⚡ Kalite Ayarları")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(16)
        box.set_margin_end(16)
        
        # 2 sütun grid
        grid = Gtk.Grid()
        grid.set_row_spacing(12)
        grid.set_column_spacing(20)
        grid.set_column_homogeneous(True)
        
        # Sol: Ses kalitesi
        audio_label = Gtk.Label()
        audio_label.set_markup("<b>🎵 Ses Kalitesi:</b>")
        audio_label.set_halign(Gtk.Align.START)
        grid.attach(audio_label, 0, 0, 1, 1)
        
        self.audio_quality_combo = Gtk.ComboBoxText()
        self.audio_quality_combo.append("320", "320 kbps - En İyi 💎")
        self.audio_quality_combo.append("256", "256 kbps - Çok İyi")
        self.audio_quality_combo.append("192", "192 kbps - İyi ⚡")
        self.audio_quality_combo.append("128", "128 kbps - Normal 📱")
        self.audio_quality_combo.append("96", "96 kbps - Düşük")
        
        current_aq = str(GLOBAL_CONFIG.get('audio_quality', '192')).replace('k', '')
        self.audio_quality_combo.set_active_id(current_aq)
        self.audio_quality_combo.set_size_request(-1, 45)  # 40 → 45
        grid.attach(self.audio_quality_combo, 0, 1, 1, 1)
        
        # Sağ: Video kalitesi
        video_label = Gtk.Label()
        video_label.set_markup("<b>🎬 Video Kalitesi:</b>")
        video_label.set_halign(Gtk.Align.START)
        grid.attach(video_label, 1, 0, 1, 1)
        
        self.video_quality_combo = Gtk.ComboBoxText()
        self.video_quality_combo.append("2160p", "4K (2160p) 🌟")
        self.video_quality_combo.append("1080p", "1080p - Full HD ⚡")
        self.video_quality_combo.append("720p", "720p - HD")
        self.video_quality_combo.append("480p", "480p - SD 📱")
        self.video_quality_combo.append("360p", "360p - Düşük")
        
        current_vq = GLOBAL_CONFIG.get('video_quality', '1080p')
        self.video_quality_combo.set_active_id(current_vq)
        self.video_quality_combo.set_size_request(-1, 45)  # 40 → 45
        grid.attach(self.video_quality_combo, 1, 1, 1, 1)
        
        box.pack_start(grid, False, False, 0)
        
        # İpucu
        tip = Gtk.Label()
        tip.set_markup("<span size='small' alpha='70%'>💡 192kbps ve 1080p çoğu kullanıcı için idealdir</span>")
        tip.set_halign(Gtk.Align.START)
        box.pack_start(tip, False, False, 0)
        
        frame.add(box)
        return frame
    
    def create_advanced_expander(self):
        """Gelişmiş ayarlar (expander ile)"""
        expander = Gtk.Expander(label="🔧 Gelişmiş Ayarlar")
        expander.set_margin_top(8)
        
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(16)
        box.set_margin_end(16)
        
        # Uyarı
        warning = Gtk.Label()
        warning.set_markup("<span size='small'>⚠️ <b>Dikkat:</b> Bu ayarları sadece biliyorsanız değiştirin</span>")
        warning.set_halign(Gtk.Align.START)
        box.pack_start(warning, False, False, 0)
        
        # Grid
        grid = Gtk.Grid()
        grid.set_row_spacing(12)
        grid.set_column_spacing(20)
        grid.set_column_homogeneous(True)
        
        # Sol: Audio format
        audio_fmt_label = Gtk.Label()
        audio_fmt_label.set_markup("<b>🎵 Ses Format:</b>")
        audio_fmt_label.set_halign(Gtk.Align.START)
        grid.attach(audio_fmt_label, 0, 0, 1, 1)
        
        self.audio_format_combo = Gtk.ComboBoxText()
        self.audio_format_combo.append("mp3", "MP3 (Önerilen) 🏆")
        self.audio_format_combo.append("m4a", "M4A / AAC")
        self.audio_format_combo.append("opus", "OPUS (Küçük)")
        self.audio_format_combo.append("flac", "FLAC (Kayıpsız) 💎")
        self.audio_format_combo.append("ogg", "OGG Vorbis")
        
        current_af = GLOBAL_CONFIG.get('audio_format', 'mp3')
        self.audio_format_combo.set_active_id(current_af)
        self.audio_format_combo.set_size_request(-1, 45)  # 40 → 45
        grid.attach(self.audio_format_combo, 0, 1, 1, 1)
        
        # Sağ: Video format
        video_fmt_label = Gtk.Label()
        video_fmt_label.set_markup("<b>🎬 Video Format:</b>")
        video_fmt_label.set_halign(Gtk.Align.START)
        grid.attach(video_fmt_label, 1, 0, 1, 1)
        
        self.video_format_combo = Gtk.ComboBoxText()
        self.video_format_combo.append("mp4", "MP4 (Önerilen) 🏆")
        self.video_format_combo.append("mkv", "MKV (Yüksek Kalite)")
        self.video_format_combo.append("webm", "WEBM (Web)")
        
        current_vf = GLOBAL_CONFIG.get('video_format', 'mp4')
        self.video_format_combo.set_active_id(current_vf)
        self.video_format_combo.set_size_request(-1, 45)  # 40 → 45
        grid.attach(self.video_format_combo, 1, 1, 1, 1)
        
        # Codec
        codec_label = Gtk.Label()
        codec_label.set_markup("<b>⚙️ Video Codec:</b>")
        codec_label.set_halign(Gtk.Align.START)
        grid.attach(codec_label, 0, 2, 1, 1)
        
        self.video_codec_combo = Gtk.ComboBoxText()
        self.video_codec_combo.append("h264", "H.264 (Standart) 🏆")
        self.video_codec_combo.append("h265", "H.265 / HEVC")
        self.video_codec_combo.append("vp9", "VP9 (Web)")
        self.video_codec_combo.append("copy", "Kopyala (Hızlı)")
        
        current_codec = GLOBAL_CONFIG.get('video_codec', 'h264')
        self.video_codec_combo.set_active_id(current_codec)
        self.video_codec_combo.set_size_request(-1, 45)  # 40 → 45
        grid.attach(self.video_codec_combo, 0, 3, 1, 1)
        
        box.pack_start(grid, False, False, 0)
        
        expander.add(box)
        return expander
    
    def create_frame(self, title):
        """Frame oluştur"""
        frame = Gtk.Frame()
        frame.set_label(title)
        frame.set_shadow_type(Gtk.ShadowType.OUT)
        return frame
    
    def create_action_buttons(self):
        """Alt butonlar - GTK uyarısız"""
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        box.set_margin_top(16)
        box.set_margin_bottom(16)
        box.set_margin_start(30)
        box.set_margin_end(30)
        
        box.pack_start(Gtk.Box(), True, True, 0)
        
        reset_btn = Gtk.Button(label="🔄 Varsayılan")
        reset_btn.set_size_request(150, 45)  # 150x40 → 150x45
        reset_btn.connect("clicked", self.on_reset_clicked)
        box.pack_start(reset_btn, False, False, 0)
        
        save_btn = Gtk.Button(label="💾 Kaydet")
        save_btn.set_size_request(150, 45)  # 150x40 → 150x45
        save_btn.get_style_context().add_class("suggested-action")
        save_btn.connect("clicked", self.on_save_clicked)
        box.pack_start(save_btn, False, False, 0)
        
        return box
    
    # ==================== EVENT HANDLERS ====================
    
    def on_preset_fast(self, btn):
        """Hızlı profil"""
        self.audio_quality_combo.set_active_id("128")
        self.video_quality_combo.set_active_id("720p")
        self.concurrent_spin.set_value(5)
        self.profile_label.set_markup("<span size='large' weight='bold'>🚀 Hızlı</span>")
    
    def on_preset_standard(self, btn):
        """Standart profil"""
        self.audio_quality_combo.set_active_id("192")
        self.video_quality_combo.set_active_id("1080p")
        self.concurrent_spin.set_value(3)
        self.profile_label.set_markup("<span size='large' weight='bold'>⚡ Standart</span>")
    
    def on_preset_hq(self, btn):
        """Kaliteli profil"""
        self.audio_quality_combo.set_active_id("320")
        self.video_quality_combo.set_active_id("1080p")
        self.concurrent_spin.set_value(2)
        self.profile_label.set_markup("<span size='large' weight='bold'>💎 Kaliteli</span>")
    
    def select_download_folder(self, btn):
        """Klasör seç"""
        dialog = Gtk.FileChooserDialog(
            title="İndirme Klasörü Seç",
            parent=self.parent,
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            folder = dialog.get_filename()
            self.folder_entry.set_text(folder)
        
        dialog.destroy()
    
    def on_save_clicked(self, btn):
        """Kaydet"""
        try:
            updates = {
                'download_mode': self.download_mode_combo.get_active_id(),
                'download_path': self.folder_entry.get_text(),
                'max_concurrent_downloads': int(self.concurrent_spin.get_value()),
                'skip_existing': self.skip_existing_check.get_active(),
                'embed_metadata': self.embed_metadata_check.get_active(),
                'embed_thumbnail': self.embed_thumbnail_check.get_active(),
                'audio_quality': self.audio_quality_combo.get_active_id(),
                'video_quality': self.video_quality_combo.get_active_id(),
                'audio_format': self.audio_format_combo.get_active_id(),
                'video_format': self.video_format_combo.get_active_id(),
                'video_codec': self.video_codec_combo.get_active_id(),
            }
            
            save_config(updates)
            update_download_dir(updates['download_path'])
            
            if hasattr(self.parent, 'status_label'):
                GLib.idle_add(self.parent.status_label.set_text, "✅ Ayarlar kaydedildi!")
            
            self.logger.info("Ayarlar kaydedildi")
            
        except Exception as e:
            self.logger.error(f"Kaydetme hatası: {e}")
    
    def on_reset_clicked(self, btn):
        """Varsayılana dön"""
        dialog = Gtk.MessageDialog(
            transient_for=self.parent,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Varsayılan ayarlara dönülsün mü?"
        )
        
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES:
            from settings import DEFAULT_CONFIG
            save_config(DEFAULT_CONFIG.copy())
            self.update_ui_from_config()
    
    def update_ui_from_config(self):
        """Config'den UI'ı güncelle"""
        try:
            self.download_mode_combo.set_active_id(GLOBAL_CONFIG.get('download_mode', 'audio'))
            self.folder_entry.set_text(str(GLOBAL_CONFIG.get('download_path', Path.home() / 'Music')))
            self.concurrent_spin.set_value(GLOBAL_CONFIG.get('max_concurrent_downloads', 3))
            self.skip_existing_check.set_active(GLOBAL_CONFIG.get('skip_existing', True))
            self.embed_metadata_check.set_active(GLOBAL_CONFIG.get('embed_metadata', True))
            self.embed_thumbnail_check.set_active(GLOBAL_CONFIG.get('embed_thumbnail', True))
            
            audio_q = str(GLOBAL_CONFIG.get('audio_quality', '192')).replace('k', '')
            self.audio_quality_combo.set_active_id(audio_q)
            
            self.video_quality_combo.set_active_id(GLOBAL_CONFIG.get('video_quality', '1080p'))
            self.audio_format_combo.set_active_id(GLOBAL_CONFIG.get('audio_format', 'mp3'))
            self.video_format_combo.set_active_id(GLOBAL_CONFIG.get('video_format', 'mp4'))
            self.video_codec_combo.set_active_id(GLOBAL_CONFIG.get('video_codec', 'h264'))
        except Exception as e:
            self.logger.error(f"UI güncelleme hatası: {e}")