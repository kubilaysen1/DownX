# 💜 DownX - Premium Edition

YouTube ve Spotify'dan yüksek kaliteli müzik indirme uygulaması.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![GTK](https://img.shields.io/badge/GTK-3.0-green.svg)
![License](https://img.shields.io/badge/License-Free-brightgreen.svg)

## ✨ Özellikler

- 🎬 **YouTube İndirme** - Video ve ses dosyaları
- 🎧 **Spotify İndirme** - Şarkılar, albümler, playlistler
- 📋 **Toplu İndirme** - TXT dosyasından liste yükleme
- 🎨 **Modern Arayüz** - GTK3 tabanlı güzel tasarım
- ⚙️ **Özelleştirilebilir** - Format, kalite, dosya adlandırma
- 🔄 **İlerleme Takibi** - Gerçek zamanlı indirme durumu
- 🌐 **Çoklu Platform** - Tüm Linux dağıtımlarında ve Windows'ta çalışır

## 🚀 Hızlı Kurulum

### Otomatik Kurulum (Önerilen)

```bash
# Repoyu klonla veya dosyaları indir
cd DownX

# Kurulum scriptini çalıştır
chmod +x install.sh
./install.sh
Manuel Kurulum1. Sistem PaketleriFedora/RHEL:Bashsudo dnf install gtk3 python3-gobject python3-cairo python3-pip ffmpeg
Ubuntu/Debian:Bashsudo apt install gir1.2-gtk-3.0 python3-gi python3-gi-cairo python3-pip ffmpeg
Arch Linux:Bashsudo pacman -S gtk3 python-gobject python-cairo python-pip ffmpeg
2. Python PaketleriBash# Virtual environment oluştur (önerilir)
python3 -m venv .venv --system-site-packages
source .venv/bin/activate

# Bağımlılıkları yükle
pip install -r requirements.txt
3. ÇalıştırBashpython gui.py
📁 Dosya YapısıDownX/
├── gui.py             # Ana uygulama
├── launcher.py        # Akıllı başlatıcı (bağımlılık kontrolü)
├── install.sh         # Kurulum scripti
├── requirements.txt   # Python bağımlılıkları
├── settings.py        # Ayar yönetimi
├── search_tab.py      # Arama sekmesi
├── downloads_tab.py   # İndirmeler sekmesi
├── settings_tab.py    # Ayarlar sekmesi
├── queue_manager.py   # İndirme kuyruğu
├── downloader.py      # YouTube indirici
├── youtube_client.py  # YouTube API
├── spotify_client.py  # Spotify API
└── cookies.txt        # (Opsiyonel) YouTube cookies
⚙️ AyarlarSpotify API Kurulumu[şüpheli bağlantı kaldırıldı] adresine gidinYeni bir uygulama oluşturunClient ID ve Client Secret'ı alınAyarlar sekmesinden girinYouTube Cookies (Opsiyonel)Premium içerikler veya yaş sınırlı videolar için:Tarayıcınıza "Get cookies.txt" eklentisini yükleyinYouTube'a giriş yapınCookies'i dışa aktarınAyarlar sekmesinden yükleyin🎨 Desteklenen FormatlarFormatAçıklamaMP3En yaygın, her yerde çalışırM4AAAC, daha iyi kaliteOPUSEn iyi sıkıştırmaFLACKayıpsız, büyük dosyaWAVSıkıştırmasız⌨️ Klavye KısayollarıKısayolİşlevCtrl+QUygulamadan çıkCtrl+FArama kutusuna odaklanCtrl+Dİndirilenler sekmesiCtrl+SAyarlar sekmesiCtrl+BSidebar aç/kapatF11Tam ekranESCAramayı temizle🐛 Sorun GidermeGTK HatasıGtk-Message: Failed to load module "colorreload-gtk-module"
Bu uyarı zararsızdır, görmezden gelebilirsiniz.PyGObject Import HatasıBash# Fedora Silverblue için
rpm-ostree install python3-gobject gtk3-devel

# Veya venv'i sistem paketleriyle oluşturun
python3 -m venv .venv --system-site-packages
FFmpeg BulunamadıBash# Fedora
sudo dnf install ffmpeg

# Ubuntu
sudo apt install ffmpeg
📝 LisansBu proje ücretsiz olarak sunulmaktadır. Kişisel kullanım için serbesttir.🤝 Katkıda BulunmaPull request'ler kabul edilir! Büyük değişiklikler için önce bir issue açın.DownX ile müzik keyfinizi çıkarın! 🎶
