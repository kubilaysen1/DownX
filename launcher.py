#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
4KTube Free - Akıllı Başlatıcı (Smart Launcher)
Tüm Linux dağıtımlarında çalışır.
Eksik bağımlılıkları tespit edip yükler.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

# Renkli çıktı için ANSI kodları
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_banner():
    """Başlangıç banner'ı"""
    print(f"""
{Colors.CYAN}{Colors.BOLD}
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   ██╗  ██╗██╗  ██╗████████╗██╗   ██╗██████╗ ███████╗          ║
║   ██║  ██║██║ ██╔╝╚══██╔══╝██║   ██║██╔══██╗██╔════╝          ║
║   ███████║█████╔╝    ██║   ██║   ██║██████╔╝█████╗            ║
║   ╚════██║██╔═██╗    ██║   ██║   ██║██╔══██╗██╔══╝            ║
║        ██║██║  ██╗   ██║   ╚██████╔╝██████╔╝███████╗          ║
║        ╚═╝╚═╝  ╚═╝   ╚═╝    ╚═════╝ ╚═════╝ ╚══════╝          ║
║                                                               ║
║                    FREE - Premium Edition                     ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
{Colors.END}""")

def print_status(message, status="info"):
    """Duruma göre renkli mesaj yazdır"""
    icons = {
        "info": f"{Colors.BLUE}ℹ{Colors.END}",
        "success": f"{Colors.GREEN}✓{Colors.END}",
        "warning": f"{Colors.YELLOW}⚠{Colors.END}",
        "error": f"{Colors.RED}✗{Colors.END}",
        "check": f"{Colors.CYAN}→{Colors.END}",
    }
    icon = icons.get(status, icons["info"])
    print(f"  {icon} {message}")

def print_section(title):
    """Bölüm başlığı yazdır"""
    print(f"\n{Colors.BOLD}{Colors.MAGENTA}━━━ {title} ━━━{Colors.END}")

def detect_distro():
    """Linux dağıtımını tespit et"""
    distro_info = {
        "id": "unknown",
        "name": "Unknown Linux",
        "package_manager": None,
        "install_cmd": None,
        "sudo_needed": True
    }
    
    # /etc/os-release dosyasını oku
    os_release = Path("/etc/os-release")
    if os_release.exists():
        with open(os_release) as f:
            for line in f:
                if line.startswith("ID="):
                    distro_info["id"] = line.split("=")[1].strip().strip('"').lower()
                elif line.startswith("NAME="):
                    distro_info["name"] = line.split("=", 1)[1].strip().strip('"')
    
    # Paket yöneticisini belirle
    distro_id = distro_info["id"]
    
    # Fedora, RHEL, CentOS
    if distro_id in ["fedora", "rhel", "centos", "rocky", "almalinux"]:
        if shutil.which("dnf"):
            distro_info["package_manager"] = "dnf"
            distro_info["install_cmd"] = "sudo dnf install -y"
        elif shutil.which("yum"):
            distro_info["package_manager"] = "yum"
            distro_info["install_cmd"] = "sudo yum install -y"
    
    # Ubuntu, Debian, Linux Mint, Pop!_OS
    elif distro_id in ["ubuntu", "debian", "linuxmint", "pop", "elementary", "zorin", "kali"]:
        distro_info["package_manager"] = "apt"
        distro_info["install_cmd"] = "sudo apt install -y"
    
    # Arch Linux, Manjaro, EndeavourOS
    elif distro_id in ["arch", "manjaro", "endeavouros", "garuda", "artix"]:
        distro_info["package_manager"] = "pacman"
        distro_info["install_cmd"] = "sudo pacman -S --noconfirm"
    
    # openSUSE
    elif distro_id in ["opensuse", "opensuse-leap", "opensuse-tumbleweed", "suse"]:
        distro_info["package_manager"] = "zypper"
        distro_info["install_cmd"] = "sudo zypper install -y"
    
    # Gentoo
    elif distro_id == "gentoo":
        distro_info["package_manager"] = "emerge"
        distro_info["install_cmd"] = "sudo emerge"
    
    # Void Linux
    elif distro_id == "void":
        distro_info["package_manager"] = "xbps"
        distro_info["install_cmd"] = "sudo xbps-install -y"
    
    # NixOS
    elif distro_id == "nixos":
        distro_info["package_manager"] = "nix"
        distro_info["install_cmd"] = "nix-env -iA nixpkgs."
        distro_info["sudo_needed"] = False
    
    # Flatpak içinde mi?
    if os.path.exists("/.flatpak-info"):
        distro_info["is_flatpak"] = True
    
    # Silverblue/Kinoite (immutable)
    if distro_id == "fedora" and os.path.exists("/run/ostree-booted"):
        distro_info["is_immutable"] = True
        distro_info["install_cmd"] = "rpm-ostree install"
    
    return distro_info

def get_system_packages(distro):
    """Dağıtıma göre gerekli sistem paketlerini döndür"""
    pkg_manager = distro["package_manager"]
    
    packages = {
        "dnf": {
            "gtk": "gtk3",
            "pygobject": "python3-gobject",
            "gobject-devel": "gobject-introspection-devel",
            "cairo": "python3-cairo",
            "ffmpeg": "ffmpeg",
            "pip": "python3-pip",
        },
        "apt": {
            "gtk": "gir1.2-gtk-3.0",
            "pygobject": "python3-gi",
            "gobject-devel": "libgirepository1.0-dev",
            "cairo": "python3-gi-cairo",
            "ffmpeg": "ffmpeg",
            "pip": "python3-pip",
        },
        "pacman": {
            "gtk": "gtk3",
            "pygobject": "python-gobject",
            "gobject-devel": "gobject-introspection",
            "cairo": "python-cairo",
            "ffmpeg": "ffmpeg",
            "pip": "python-pip",
        },
        "zypper": {
            "gtk": "gtk3",
            "pygobject": "python3-gobject",
            "gobject-devel": "gobject-introspection-devel",
            "cairo": "python3-cairo",
            "ffmpeg": "ffmpeg",
            "pip": "python3-pip",
        },
    }
    
    return packages.get(pkg_manager, packages["apt"])

def check_python_version():
    """Python sürümünü kontrol et"""
    print_section("Python Kontrolü")
    
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_status(f"Python {version_str} - En az 3.8 gerekli!", "error")
        return False
    
    print_status(f"Python {version_str} ✓", "success")
    return True

def check_gtk():
    """GTK ve PyGObject kontrolü"""
    print_section("GTK/PyGObject Kontrolü")
    
    try:
        import gi
        gi.require_version("Gtk", "3.0")
        from gi.repository import Gtk
        print_status("GTK 3.0 ✓", "success")
        print_status(f"PyGObject ✓", "success")
        return True
    except ImportError as e:
        print_status(f"GTK/PyGObject bulunamadı: {e}", "error")
        return False
    except ValueError as e:
        print_status(f"GTK sürüm hatası: {e}", "error")
        return False

def check_ffmpeg():
    """FFmpeg kontrolü"""
    if shutil.which("ffmpeg"):
        try:
            result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
            version_line = result.stdout.split("\n")[0]
            print_status(f"FFmpeg ✓ ({version_line.split(' ')[2] if len(version_line.split(' ')) > 2 else 'OK'})", "success")
            return True
        except:
            pass
    
    print_status("FFmpeg bulunamadı!", "error")
    return False

def check_pip_packages():
    """Pip paketlerini kontrol et"""
    print_section("Python Paket Kontrolü")
    
    required_packages = {
        "yt-dlp": "yt_dlp",
        "spotdl": "spotdl",
        "spotipy": "spotipy",
        "requests": "requests",
        "Pillow": "PIL",
        "mutagen": "mutagen",
    }
    
    missing = []
    installed = []
    
    for package_name, import_name in required_packages.items():
        try:
            __import__(import_name)
            installed.append(package_name)
        except ImportError:
            missing.append(package_name)
    
    for pkg in installed:
        print_status(f"{pkg} ✓", "success")
    
    for pkg in missing:
        print_status(f"{pkg} eksik!", "warning")
    
    return missing

def install_system_packages(distro, packages_to_install):
    """Sistem paketlerini yükle"""
    if not distro["install_cmd"]:
        print_status("Paket yöneticisi tespit edilemedi!", "error")
        return False
    
    print_section("Sistem Paketleri Yükleniyor")
    
    # Paket adlarını al
    sys_packages = get_system_packages(distro)
    install_list = []
    
    for pkg in packages_to_install:
        if pkg in sys_packages:
            install_list.append(sys_packages[pkg])
    
    if not install_list:
        print_status("Yüklenecek paket yok", "info")
        return True
    
    cmd = f"{distro['install_cmd']} {' '.join(install_list)}"
    print_status(f"Komut: {cmd}", "check")
    
    try:
        result = subprocess.run(cmd, shell=True)
        if result.returncode == 0:
            print_status("Sistem paketleri yüklendi!", "success")
            return True
        else:
            print_status("Yükleme başarısız!", "error")
            return False
    except Exception as e:
        print_status(f"Hata: {e}", "error")
        return False

def install_pip_packages(packages):
    """Pip paketlerini yükle"""
    if not packages:
        return True
    
    print_section("Python Paketleri Yükleniyor")
    
    # pip'in güncel olduğundan emin ol
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip", "-q"])
    
    for pkg in packages:
        print_status(f"Yükleniyor: {pkg}...", "check")
        try:
            # --break-system-packages bazı sistemlerde gerekli
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", pkg, "--break-system-packages", "-q"],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                # --break-system-packages olmadan dene
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", pkg, "-q"],
                    capture_output=True,
                    text=True
                )
            
            if result.returncode == 0:
                print_status(f"{pkg} yüklendi ✓", "success")
            else:
                print_status(f"{pkg} yüklenemedi: {result.stderr[:50]}", "error")
        except Exception as e:
            print_status(f"{pkg} yüklenemedi: {e}", "error")
    
    return True

def setup_venv():
    """Virtual environment oluştur (önerilir)"""
    venv_path = Path(__file__).parent / ".venv"
    
    if venv_path.exists():
        return venv_path
    
    print_section("Virtual Environment")
    print_status("Yeni venv oluşturuluyor...", "check")
    
    try:
        subprocess.run([sys.executable, "-m", "venv", str(venv_path), "--system-site-packages"])
        print_status(f"venv oluşturuldu: {venv_path}", "success")
        return venv_path
    except Exception as e:
        print_status(f"venv oluşturulamadı: {e}", "warning")
        return None

def ask_user(question):
    """Kullanıcıya evet/hayır sorusu sor"""
    while True:
        response = input(f"\n{Colors.YELLOW}? {question} [E/h]: {Colors.END}").strip().lower()
        if response in ["", "e", "evet", "y", "yes"]:
            return True
        elif response in ["h", "hayır", "n", "no"]:
            return False
        print("  Lütfen 'E' (Evet) veya 'H' (Hayır) yazın.")

def create_desktop_entry():
    """Masaüstü kısayolu oluştur"""
    app_dir = Path(__file__).parent.resolve()
    desktop_dir = Path.home() / ".local" / "share" / "applications"
    desktop_dir.mkdir(parents=True, exist_ok=True)
    
    desktop_content = f"""[Desktop Entry]
Name=4KTube Free
Comment=YouTube ve Spotify'dan müzik indirin
Exec={sys.executable} {app_dir}/gui.py
Icon=multimedia-video-player
Terminal=false
Type=Application
Categories=AudioVideo;Audio;Video;Network;
Keywords=youtube;spotify;download;music;video;
"""
    
    desktop_file = desktop_dir / "4ktube-free.desktop"
    desktop_file.write_text(desktop_content)
    os.chmod(desktop_file, 0o755)
    
    print_status(f"Masaüstü kısayolu: {desktop_file}", "success")

def main():
    """Ana başlatıcı fonksiyonu"""
    print_banner()
    
    # Dağıtımı tespit et
    distro = detect_distro()
    print_section("Sistem Bilgisi")
    print_status(f"Dağıtım: {distro['name']}", "info")
    print_status(f"Paket Yöneticisi: {distro['package_manager'] or 'Bilinmiyor'}", "info")
    
    if distro.get("is_immutable"):
        print_status("Immutable sistem (Silverblue/Kinoite)", "warning")
    
    all_ok = True
    missing_system = []
    missing_pip = []
    
    # Python kontrolü
    if not check_python_version():
        print(f"\n{Colors.RED}Python 3.8+ gerekli. Lütfen yükleyin.{Colors.END}")
        sys.exit(1)
    
    # GTK kontrolü
    if not check_gtk():
        missing_system.extend(["gtk", "pygobject", "cairo"])
        all_ok = False
    
    # FFmpeg kontrolü
    if not check_ffmpeg():
        missing_system.append("ffmpeg")
        all_ok = False
    
    # Pip paketleri kontrolü
    missing_pip = check_pip_packages()
    if missing_pip:
        all_ok = False
    
    # Eksik paketleri yükle
    if not all_ok:
        print_section("Eksik Bağımlılıklar")
        
        if missing_system:
            print_status(f"Eksik sistem paketleri: {', '.join(missing_system)}", "warning")
        if missing_pip:
            print_status(f"Eksik Python paketleri: {', '.join(missing_pip)}", "warning")
        
        if ask_user("Eksik paketleri yüklemek ister misiniz?"):
            # Sistem paketleri
            if missing_system and distro["package_manager"]:
                install_system_packages(distro, missing_system)
            
            # Pip paketleri
            if missing_pip:
                install_pip_packages(missing_pip)
            
            # Tekrar kontrol et
            print_section("Yeniden Kontrol")
            all_ok = check_gtk() and check_ffmpeg() and not check_pip_packages()
        else:
            print_status("Yükleme iptal edildi.", "warning")
    
    # Masaüstü kısayolu
    desktop_file = Path.home() / ".local" / "share" / "applications" / "4ktube-free.desktop"
    if not desktop_file.exists():
        if ask_user("Masaüstü kısayolu oluşturulsun mu?"):
            create_desktop_entry()
    
    # Uygulamayı başlat
    if all_ok:
        print_section("Uygulama Başlatılıyor")
        print_status("4KTube Free açılıyor...", "success")
        print()
        
        # gui.py'yi çalıştır
        app_dir = Path(__file__).parent
        gui_path = app_dir / "gui.py"
        
        if gui_path.exists():
            os.chdir(app_dir)
            os.execv(sys.executable, [sys.executable, str(gui_path)])
        else:
            print_status(f"gui.py bulunamadı: {gui_path}", "error")
            sys.exit(1)
    else:
        print(f"\n{Colors.RED}Bazı bağımlılıklar eksik. Lütfen manuel olarak yükleyin.{Colors.END}")
        print(f"\n{Colors.YELLOW}Manuel kurulum komutları:{Colors.END}")
        
        if distro["package_manager"] == "dnf":
            print("  sudo dnf install gtk3 python3-gobject python3-cairo ffmpeg python3-pip")
        elif distro["package_manager"] == "apt":
            print("  sudo apt install gir1.2-gtk-3.0 python3-gi python3-gi-cairo ffmpeg python3-pip")
        elif distro["package_manager"] == "pacman":
            print("  sudo pacman -S gtk3 python-gobject python-cairo ffmpeg python-pip")
        
        print(f"\n  pip install yt-dlp spotdl spotipy requests Pillow mutagen")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}İptal edildi.{Colors.END}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}Beklenmeyen hata: {e}{Colors.END}")
        sys.exit(1)