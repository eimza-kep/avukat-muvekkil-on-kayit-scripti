# -*- coding: utf-8 -*-
"""
server.py
---------
Avukat & Hukuk Bürosu Müvekkil Ön Kayıt, Çıkar Çatışması ve UDF Belge Portalı.
SQLite ile güvenli yerel dosya kabul kaydı tutar, UYAP UDF evraklarını ayrıştırır
ve UYAP Avukat Portalı vekaletname şablonları üretir.
"""

import os
import sys
import json
import sqlite3
import random
import base64
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from scripts.udf_parser import (
    parse_udf_bytes,
    generate_vekaletname_text,
    generate_uyap_vekalet_xml
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PORT = int(os.environ.get("PORT", 8082))
DB_FILE = os.environ.get("DATABASE_PATH", os.path.join(BASE_DIR, "hukuk_dosyalar.db"))

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
                udf_filename TEXT,
                udf_document_type TEXT,
                udf_content TEXT,
                udf_summary TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Migration: Add columns if table already exists
        cursor.execute("PRAGMA table_info(intakes)")
        cols = [c[1] for c in cursor.fetchall()]
        new_cols = {
            "udf_filename": "TEXT",
            "udf_document_type": "TEXT",
            "udf_content": "TEXT",
            "udf_summary": "TEXT"
        }
        for cname, ctype in new_cols.items():
            if cname not in cols:
                try:
                    cursor.execute(f"ALTER TABLE intakes ADD COLUMN {cname} {ctype}")
                except Exception:
                    pass
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
            self.handle_get_dosya_listesi()
            return

        if parsed.path == "/api/vekaletname-taslagi":
            self.handle_get_vekaletname_taslagi(parsed)
            return

        if parsed.path == "/api/export-vekalet-xml":
            self.handle_export_vekalet_xml(parsed)
            return

        super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/on-kayit":
            self.handle_create_on_kayit()
            return

        if parsed.path == "/api/upload-udf":
            self.handle_upload_udf()
            return

        if parsed.path == "/api/parse-udf":
            self.handle_parse_udf()
            return

        self.send_response(404)
        self.end_headers()

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def handle_get_dosya_listesi(self):
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
            self.send_json(rows)

    def handle_get_vekaletname_taslagi(self, parsed):
        qs = parse_qs(parsed.query)
        code = qs.get("code", [""])[0]
        if not code:
            self.send_json({"error": "Dosya kodu gereklidir."}, status=400)
            return

        with sqlite3.connect(DB_FILE) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM intakes WHERE intake_code = ?", (code,))
            row = cursor.fetchone()

        if not row:
            self.send_json({"error": "Dosya bulunamadı."}, status=404)
            return

        client_data = dict(row)
        txt = generate_vekaletname_text(client_data)
        xml = generate_uyap_vekalet_xml(client_data)

        self.send_json({
            "success": True,
            "intake_code": code,
            "vekaletname_text": txt,
            "uyap_xml": xml
        })

    def handle_export_vekalet_xml(self, parsed):
        qs = parse_qs(parsed.query)
        code = qs.get("code", [""])[0]
        with sqlite3.connect(DB_FILE) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM intakes WHERE intake_code = ?", (code,))
            row = cursor.fetchone()

        if not row:
            self.send_json({"error": "Dosya bulunamadı."}, status=404)
            return

        client_data = dict(row)
        xml = generate_uyap_vekalet_xml(client_data).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/xml; charset=utf-8")
        self.send_header("Content-Disposition", f'attachment; filename="vekalet_{code}.xml"')
        self.send_header("Content-Length", str(len(xml)))
        self.end_headers()
        self.wfile.write(xml)

    def handle_create_on_kayit(self):
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
                    preferred_time, udf_filename, udf_document_type, udf_content, udf_summary
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                data.get("preferred_time", ""),
                data.get("udf_filename", ""),
                data.get("udf_document_type", ""),
                data.get("udf_content", ""),
                data.get("udf_summary", "")
            ))
            conn.commit()

        # Otomatik vekaletname taslağı oluştur
        client_data = dict(data)
        client_data["intake_code"] = intake_code
        vekalet_text = generate_vekaletname_text(client_data)

        resp = {
            "success": True,
            "intake_code": intake_code,
            "message": "Ön görüşme kaydınız başarıyla alındı.",
            "vekaletname_text": vekalet_text
        }
        self.send_json(resp)

    def handle_upload_udf(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        try:
            data = json.loads(body.decode("utf-8"))
            intake_code = data.get("intake_code")
            filename = data.get("filename", "evrak.udf")
            b64_content = data.get("content_base64", "")
            raw_bytes = base64.b64decode(b64_content) if b64_content else b""

            parsed = parse_udf_bytes(raw_bytes)

            if intake_code:
                with sqlite3.connect(DB_FILE) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE intakes
                        SET udf_filename = ?, udf_document_type = ?, udf_content = ?, udf_summary = ?
                        WHERE intake_code = ?
                    """, (
                        filename,
                        parsed.get("document_type", ""),
                        parsed.get("full_text", ""),
                        parsed.get("summary", ""),
                        intake_code
                    ))
                    conn.commit()

            self.send_json({
                "success": True,
                "parsed": parsed
            })
        except Exception as e:
            self.send_json({"error": str(e)}, status=400)

    def handle_parse_udf(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        try:
            # Hem multipart/json hem de raw byte kabul et
            if body.startswith(b"{"):
                data = json.loads(body.decode("utf-8"))
                b64 = data.get("content_base64", "")
                raw_bytes = base64.b64decode(b64) if b64 else b""
            else:
                raw_bytes = body

            parsed = parse_udf_bytes(raw_bytes)
            self.send_json(parsed)
        except Exception as e:
            self.send_json({"error": str(e)}, status=400)

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
