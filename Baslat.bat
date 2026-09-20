@echo off
chcp 65001 >nul
title Avukat Müvekkil Ön Kayıt Scripti - Kolay Başlatıcı
cd /d "%~dp0"

echo ======================================================================
echo    ⚖️ Hukuk Bürosu Müvekkil Ön Görüşme Portalı - Başlatıcı
echo ======================================================================
echo.

where python >nul 2>nul
if %errorlevel% equ 0 (
    start http://localhost:8082/
    python server.py
    goto :end
)

if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    start http://localhost:8082/
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" server.py
    goto :end
)

echo [BİLGİ] Python bulunamadı. Form doğrudan tarayıcınızda açılıyor...
timeout /t 1 >nul
start "" "%~dp0index.html"

:end
