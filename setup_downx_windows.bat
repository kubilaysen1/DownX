@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: Admin kontrolü
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo.
    echo [HATA] Bu script yönetici olarak çalıştırılmalı!
    echo Sağ tıklayıp "Yönetici olarak çalıştır" seçin.
    echo.
    pause
    exit /b 1
)

cls
echo.
echo ═══════════════════════════════════════════════════════════════
echo    ██████╗  ██████╗ ██╗    ██╗███╗   ██╗██╗  ██╗
echo    ██╔══██╗██╔═══██╗██║    ██║████╗  ██║╚██╗██╔╝
echo    ██║  ██║██║   ██║██║ █╗ ██║██╔██╗ ██║ ╚███╔╝
echo    ██║  ██║██║   ██║██║███╗██║██║╚██╗██║ ██╔██╗
echo    ██████╔╝╚██████╔╝╚███╔███╔╝██║ ╚████║██╔╝ ██╗
echo    ╚═════╝  ╚═════╝  ╚══╝╚══╝ ╚═╝  ╚═══╝╚═╝  ╚═╝
echo.
echo    DownX - Windows Basit Kurulum
echo    Spotify ^& YouTube Downloader
echo.
echo ═══════════════════════════════════════════════════════════════
echo.

:: Dizinler
set "INSTALL_DIR=%USERPROFILE%\DownX"
set "CONFIG_DIR=%APPDATA%\DownX"

echo [1/5] Python Kontrolü
echo.

:: Python var mı?
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [HATA] Python bulunamadı!
    echo.
    echo Python 3.8+ indirin: https://www.python.org/downloads/
    echo Kurulumda "Add Python to PATH" işaretleyin!
    echo.
    pause
    exit /b 1
)

python --version
echo [OK] Python bulundu
echo.

echo [2/5] Dizinler Oluşturuluyor
echo.

if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
if not exist "%INSTALL_DIR%\resources\icons" mkdir "%INSTALL_DIR%\resources\icons"
if not exist "%CONFIG_DIR%" mkdir "%CONFIG_DIR%"
if not exist "%USERPROFILE%\Music\DownX" mkdir "%USERPROFILE%\Music\DownX"

echo [OK] Dizinler oluşturuldu
echo.

echo [3/5] Virtual Environment
echo.

if exist "%INSTALL_DIR%\.venv" (
    echo [OK] Virtual environment zaten mevcut
) else (
    echo Virtual environment oluşturuluyor...
    python -m venv "%INSTALL_DIR%\.venv"
    echo [OK] Virtual environment oluşturuldu
)
echo.

echo [4/5] Python Paketleri (Zaman alabilir)
echo.

call "%INSTALL_DIR%\.venv\Scripts\activate.bat"

echo pip güncelleniyor...
python -m pip install --upgrade pip >nul 2>&1

echo Paketler kuruluyor...
pip install requests urllib3 Pillow mutagen yt-dlp spotdl spotipy PyQt6 >nul 2>&1

if %errorLevel% equ 0 (
    echo [OK] Paketler kuruldu
) else (
    echo [UYARI] Bazı paketler kurulamadı
)
echo.

echo [5/5] Başlatma Dosyası
echo.

:: run.bat
(
echo @echo off
echo cd /d "%%~dp0"
echo call .venv\Scripts\activate.bat
echo python gui.py
echo pause
) > "%INSTALL_DIR%\run.bat"

echo [OK] run.bat oluşturuldu
echo.

echo ═══════════════════════════════════════════════════════════════
echo   KURULUM TAMAMLANDI!
echo ═══════════════════════════════════════════════════════════════
echo.
echo Kurulum Dizini: %INSTALL_DIR%
echo Config Dizini: %CONFIG_DIR%
echo.
echo SONRAKI ADIMLAR:
echo.
echo 1. Python dosyalarını kopyalayın:
echo    gui.py, settings.py, downloader.py vb.
echo    → %INSTALL_DIR%
echo.
echo 2. İkonları kopyalayın:
echo    downx_icon_*.png
echo    → %INSTALL_DIR%\resources\icons\
echo.
echo 3. Çalıştırın:
echo    %INSTALL_DIR%\run.bat
echo.
pause
