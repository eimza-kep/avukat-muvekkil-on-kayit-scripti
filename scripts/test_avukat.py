# -*- coding: utf-8 -*-
"""
test_avukat.py
--------------
Hukuk Bürosu Müvekkil Ön Kayıt ve Çıkar Çatışması Portalı test süiti.
"""

import os
import sys
import sqlite3
import unittest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from server import init_db, DB_FILE

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
                    preferred_time
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                "Salı öğleden sonra"
            ))
            conn.commit()

            # Conflict check simülasyonu: Karşı taraf adıyla sorgulama
            cursor.execute("SELECT * FROM intakes WHERE opponent_name LIKE ?", (f"%{opponent_name}%",))
            row = cursor.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row[1], intake_code)
            self.assertEqual(row[3], client_name)
            self.assertEqual(row[8], "İş Hukuku")
            self.assertEqual(row[9], opponent_name)

if __name__ == "__main__":
    print("=" * 60)
    print("  HUKUK BÜROSU MÜVEKKİL ÖN KAYIT TEST SÜİTİ")
    print("=" * 60)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAvukatPortal)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.wasSuccessful():
        print("\n✅ TÜM TESTLER BAŞARIYLA GEÇTİ!")
        sys.exit(0)
    else:
        print("\n❌ TEST BAŞARISIZ!")
        sys.exit(1)
