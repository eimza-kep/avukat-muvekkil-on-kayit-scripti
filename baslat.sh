#!/usr/bin/env bash
cd "$(dirname "$0")"

echo "======================================================================"
echo "   ⚖️ Hukuk Bürosu Müvekkil Ön Görüşme Portalı - Başlatıcı"
echo "======================================================================"

if command -v python3 &>/dev/null; then
    (sleep 1 && (xdg-open http://localhost:8082/ 2>/dev/null || open http://localhost:8082/ 2>/dev/null)) &
    python3 server.py
elif command -v python &>/dev/null; then
    (sleep 1 && (xdg-open http://localhost:8082/ 2>/dev/null || open http://localhost:8082/ 2>/dev/null)) &
    python server.py
else
    echo "Python bulunamadı. Form doğrudan açılıyor..."
    xdg-open index.html 2>/dev/null || open index.html 2>/dev/null
fi
