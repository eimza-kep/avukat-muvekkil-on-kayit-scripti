# -*- coding: utf-8 -*-
"""
server.py
---------
Avukat & Hukuk Bürosu Müvekkil Ön Kayıt ve Çıkar Çatışması Portalı.
SQLite ile güvenli yerel dosya kabul kaydı tutar.
"""

import os
import sys
import json
import sqlite3
import random
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PORT = 8082
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hukuk_dosyalar.db")

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS intakes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                intake_code TEXT UNIQUE,
                client_type TEXT,
                full_name TEXT,
                id_number TEXT,
                phone TEXT,
                email TEXT,
                city TEXT,
                legal_category TEXT,
                opponent_name TEXT,
                opponent_vkn TEXT,
                existing_case TEXT,
                case_summary TEXT,
                evidences TEXT,
                consultation_type TEXT,
                preferred_time TEXT,
                status TEXT DEFAULT 'Ön İncelemede',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

class LegalHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "healthy", "service": "avukat-portal"}).encode("utf-8"))
            return

        if parsed.path == "/api/dosya-listesi":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()

            with sqlite3.connect(DB_FILE) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM intakes ORDER BY created_at DESC")
                rows = [dict(r) for r in cursor.fetchall()]
                for r in rows:
                    if r.get("evidences"):
                        try:
                            r["evidences"] = json.loads(r["evidences"])
                        except Exception:
                            pass
                self.wfile.write(json.dumps(rows, ensure_ascii=False).encode("utf-8"))
            return

        super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/on-kayit":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            try:
                data = json.loads(body)
            except Exception:
                data = {}

            intake_code = f"DOSYA-2026-{random.randint(1000, 9999)}"
            evidences_json = json.dumps(data.get("evidences", []), ensure_ascii=False)

            with sqlite3.connect(DB_FILE) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO intakes (
                        intake_code, client_type, full_name, id_number, phone,
                        email, city, legal_category, opponent_name, opponent_vkn,
                        existing_case, case_summary, evidences, consultation_type,
                        preferred_time
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    intake_code,
                    data.get("client_type", ""),
                    data.get("full_name", ""),
                    data.get("id_number", ""),
                    data.get("phone", ""),
                    data.get("email", ""),
                    data.get("city", ""),
                    data.get("legal_category", ""),
                    data.get("opponent_name", ""),
                    data.get("opponent_vkn", ""),
                    data.get("existing_case", ""),
                    data.get("case_summary", ""),
                    evidences_json,
                    data.get("consultation_type", ""),
                    data.get("preferred_time", "")
                ))
                conn.commit()

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            resp = {
                "success": True,
                "intake_code": intake_code,
                "message": "Ön görüşme kaydınız başarıyla alındı."
            }
            self.wfile.write(json.dumps(resp, ensure_ascii=False).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()

def run_server(port=PORT):
    init_db()
    server_address = ("", port)
    httpd = HTTPServer(server_address, LegalHandler)
    print(f"⚖️ Hukuk Bürosu Portalı aktif: http://localhost:{port}")
    print(f"📋 Admin Paneli: http://localhost:{port}/admin.html")
    httpd.serve_forever()

if __name__ == "__main__":
    init_db()
    run_server()
