# -*- coding: utf-8 -*-
"""
test_avukat.py
--------------
Hukuk Bürosu Müvekkil Ön Kayıt, UDF Ayrıştırıcı ve UYAP Vekaletname Test Süiti.
"""

import os
import sys
import sqlite3
import unittest
import xml.etree.ElementTree as ET

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from server import init_db, DB_FILE
from scripts.udf_parser import (
    parse_udf_bytes,
    create_sample_udf_bytes,
    generate_vekaletname_text,
    generate_uyap_vekalet_xml
)

class TestAvukatPortal(unittest.TestCase):
    def setUp(self):
        init_db()
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("DELETE FROM intakes WHERE intake_code LIKE 'DOSYA-2026-TEST%'")
            conn.commit()

    def test_database_initialization(self):
        self.assertTrue(os.path.exists(DB_FILE), "hukuk_dosyalar.db olusturulamadi.")
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='intakes'")
            table = cursor.fetchone()
            self.assertIsNotNone(table, "'intakes' tablosu bulunamadi.")

            cursor.execute("PRAGMA table_info(intakes)")
            cols = [col[1] for col in cursor.fetchall()]
            for expected in ["udf_filename", "udf_document_type", "udf_content", "udf_summary"]:
                self.assertIn(expected, cols, f"Eksik sütun: {expected}")

    def test_intake_insertion_and_conflict_query(self):
        intake_code = "DOSYA-2026-TEST01"
        client_name = "Canan Yildiz"
        opponent_name = "Baris Insaat A.S."

        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO intakes (
                    intake_code, client_type, full_name, id_number, phone,
                    email, city, legal_category, opponent_name, opponent_vkn,
                    existing_case, case_summary, evidences, consultation_type,
                    preferred_time, udf_filename, udf_document_type
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                intake_code,
                "Bireysel",
                client_name,
                "11122233344",
                "05329998877",
                "canan@test.com",
                "Izmir",
                "İş Hukuku",
                opponent_name,
                "9876543210",
                "Hayır",
                "Kidem tazminati odenmedi.",
                "[\"Banka Dekontu\"]",
                "Yüz Yüze",
                "Salı öğleden sonra",
                "dava_dilekcesi.udf",
                "DAVA DİLEKÇESİ"
            ))
            conn.commit()

            # Conflict check sorgulaması
            cursor.execute("SELECT * FROM intakes WHERE opponent_name LIKE ?", (f"%{opponent_name}%",))
            row = cursor.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row[1], intake_code)
            self.assertEqual(row[3], client_name)
            self.assertEqual(row[8], "İş Hukuku")
            self.assertEqual(row[9], opponent_name)

    def test_udf_parser(self):
        sample_court_text = """T.C. İSTANBUL 4. İŞ MAHKEMESİNE
DAVACI : Canan Yıldız
VEKİLİ : Av. Hakan Yılmaz
DAVALI : Barış İnşaat A.Ş.
DAVA KONUSU : Fazla mesai ve kıdem tazminatı talepli dava dilekçesidir.
AÇIKLAMALAR : Müvekkil davalı işyerinde 5 yıl çalışmış olup hak edişleri ödenmemiştir."""

        udf_bytes = create_sample_udf_bytes(sample_court_text)
        self.assertGreater(len(udf_bytes), 0)

        parsed = parse_udf_bytes(udf_bytes)
        self.assertTrue(parsed["success"])
        self.assertTrue(parsed["is_zip"])
        self.assertEqual(parsed["document_type"], "DAVA DİLEKÇESİ")
        self.assertIn("Canan Yıldız", parsed["full_text"])
        self.assertIn("Barış İnşaat", parsed["summary"])
        self.assertGreater(parsed["word_count"], 10)

    def test_vekaletname_generator(self):
        client = {
            "full_name": "Mehmet Kaya",
            "id_number": "12345678901",
            "city": "Ankara",
            "phone": "05551234567",
            "intake_code": "DOSYA-2026-9999",
            "legal_category": "Ticaret Hukuku"
        }
        lawyer = {
            "name": "Av. Ahmet Yılmaz",
            "baro": "Ankara Barosu",
            "sicil": "45678",
            "address": "Söğütözü No:5"
        }

        # Metin şablonu kontrolü
        txt = generate_vekaletname_text(client, lawyer)
        self.assertIn("GENEL DAVA VEKALETNAMESİ TASLAĞI", txt)
        self.assertIn("Mehmet Kaya", txt)
        self.assertIn("Av. Ahmet Yılmaz", txt)
        self.assertIn("Ahzu kabza", txt)
        self.assertIn("ARABULUCULUK", txt)
        self.assertIn("tevkil", txt)

        # UYAP XML şablonu kontrolü
        xml_str = generate_uyap_vekalet_xml(client, lawyer)
        self.assertIn("UyapVekaletname", xml_str)
        self.assertIn("Mehmet Kaya", xml_str)
        self.assertIn("Ankara Barosu", xml_str)

        # XML geçerlilik doğrulaması
        root = ET.fromstring(xml_str)
        self.assertEqual(root.tag, "UyapVekaletname")

if __name__ == "__main__":
    print("=" * 60)
    print("  HUKUK BÜROSU MÜVEKKİL ÖN KAYIT VE UDF TEST SÜİTİ")
    print("=" * 60)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAvukatPortal)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.wasSuccessful():
        print("\n✅ TÜM TESTLER BAŞARIYLA GEÇTİ!")
        sys.exit(0)
    else:
        print("\n❌ TEST BAŞARISIZ!")
        sys.exit(1)
