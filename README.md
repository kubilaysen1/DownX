# 🎵 4KTube Free - Premium Edition

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
- 🌐 **Çoklu Platform** - Tüm Linux dağıtımlarında çalışır

## 🚀 Hızlı Kurulum

### Otomatik Kurulum (Önerilen)

```bash
# Repoyu klonla veya dosyaları indir
cd 4kTubeFree

# Kurulum scriptini çalıştır
chmod +x install.sh
./install.sh
```

### Manuel Kurulum

#### 1. Sistem Paketleri

**Fedora/RHEL:**
```bash
sudo dnf install gtk3 python3-gobject python3-cairo python3-pip ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt install gir1.2-gtk-3.0 python3-gi python3-gi-cairo python3-pip ffmpeg
```

**Arch Linux:**
```bash
sudo pacman -S gtk3 python-gobject python-cairo python-pip ffmpeg
```

#### 2. Python Paketleri

```bash
# Virtual environment oluştur (önerilir)
python3 -m venv .venv --system-site-packages
source .venv/bin/activate

# Bağımlılıkları yükle
pip install -r requirements.txt
```

#### 3. Çalıştır

```bash
python gui.py
```

## 📁 Dosya Yapısı

```
4kTubeFree/
├── gui.py              # Ana uygulama
├── launcher.py         # Akıllı başlatıcı (bağımlılık kontrolü)
├── install.sh          # Kurulum scripti
├── requirements.txt    # Python bağımlılıkları
├── settings.py         # Ayar yönetimi
├── search_tab.py       # Arama sekmesi
├── downloads_tab.py    # İndirmeler sekmesi
├── settings_tab.py     # Ayarlar sekmesi
├── queue_manager.py    # İndirme kuyruğu
├── downloader.py       # YouTube indirici
├── youtube_client.py   # YouTube API
├── spotify_client.py   # Spotify API
└── cookies.txt         # (Opsiyonel) YouTube cookies
```

## ⚙️ Ayarlar

### Spotify API Kurulumu

1. [Spotify Developer Dashboard](https://developer.spotify.com/dashboard) adresine gidin
2. Yeni bir uygulama oluşturun
3. Client ID ve Client Secret'ı alın
4. Ayarlar sekmesinden girin

### YouTube Cookies (Opsiyonel)

Premium içerikler veya yaş sınırlı videolar için:

1. Tarayıcınıza "Get cookies.txt" eklentisini yükleyin
2. YouTube'a giriş yapın
3. Cookies'i dışa aktarın
4. Ayarlar sekmesinden yükleyin

## 🎨 Desteklenen Formatlar

| Format | Açıklama |
|--------|----------|
| MP3    | En yaygın, her yerde çalışır |
| M4A    | AAC, daha iyi kalite |
| OPUS   | En iyi sıkıştırma |
| FLAC   | Kayıpsız, büyük dosya |
| WAV    | Sıkıştırmasız |

## ⌨️ Klavye Kısayolları

| Kısayol | İşlev |
|---------|-------|
| `Ctrl+Q` | Uygulamadan çık |
| `Ctrl+F` | Arama kutusuna odaklan |
| `Ctrl+D` | İndirilenler sekmesi |
| `Ctrl+S` | Ayarlar sekmesi |
| `Ctrl+B` | Sidebar aç/kapat |
| `F11` | Tam ekran |
| `ESC` | Aramayı temizle |

## 🐛 Sorun Giderme

### GTK Hatası
```
Gtk-Message: Failed to load module "colorreload-gtk-module"
```
Bu uyarı zararsızdır, görmezden gelebilirsiniz.

### PyGObject Import Hatası
```bash
# Fedora Silverblue için
rpm-ostree install python3-gobject gtk3-devel

# Veya venv'i sistem paketleriyle oluşturun
python3 -m venv .venv --system-site-packages
```

### FFmpeg Bulunamadı
```bash
# Fedora
sudo dnf install ffmpeg

# Ubuntu
sudo apt install ffmpeg
```

## 📝 Lisans

Bu proje ücretsiz olarak sunulmaktadır. Kişisel kullanım için serbesttir.

## 🤝 Katkıda Bulunma

Pull request'ler kabul edilir! Büyük değişiklikler için önce bir issue açın.

---

**4KTube Free** ile müzik keyfinizi çıkarın! 🎶
