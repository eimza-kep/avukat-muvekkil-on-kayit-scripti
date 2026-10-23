# -*- coding: utf-8 -*-
"""
scripts/udf_parser.py
---------------------
UYAP Doküman Editörü (.udf) Dosya Ayrıştırıcı ve
UYAP Avukat Portalı Vekaletname Şablon Üretici Modülü.
"""

import io
import re
import zipfile
import sqlite3
from datetime import datetime
import xml.etree.ElementTree as ET

DOC_TYPES = [
    ("DAVA DİLEKÇESİ", ["dava dilekçesi", "davacı vekili", "dava konusu"]),
    ("CEVAP DİLEKÇESİ", ["cevap dilekçesi", "davalı vekili", "cevaplarımızın sunulması"]),
    ("TENSİP ZAPTI", ["tensip zaptı", "tensip tutanağı", "ön inceleme duruşması"]),
    ("GEREKÇELİ KARAR", ["gerekçeli karar", "hüküm fıkrası", "karar no"]),
    ("BİLİRKİŞİ RAPORU", ["bilirkişi raporu", "hesap bilirkişisi", "kök rapor"]),
    ("İCRA TAKİP TALEBİ / ÖDEME EMRİ", ["takip talebi", "ödeme emri", "icra emri", "örnek no"])
]

def clean_xml_tags(text):
    """XML/HTML etiketlerini temizler ve fazla boşlukları düzenler."""
    if not text:
        return ""
    # XML tags removal
    no_tags = re.sub(r"<[^>]+>", " ", text)
    # Entities decoding
    no_tags = no_tags.replace("&nbsp;", " ").replace("&amp;", "&").replace("&quot;", '"').replace("&lt;", "<").replace("&gt;", ">")
    # Collapse whitespace while preserving paragraphs
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in no_tags.splitlines()]
    return "\n".join([line for line in lines if line])

def parse_udf_bytes(raw_bytes):
    """
    UYAP .udf dosyasının bayt verisini ayrıştırır.
    İçerideki content.xml dosyasını bulup metne dönüştürür.
    """
    if not raw_bytes:
        raise ValueError("UDF dosya içeriği boş.")

    extracted_text = ""
    is_zip = False

    # 1. Deneme: ZIP formatında content.xml ara
    try:
        with zipfile.ZipFile(io.BytesIO(raw_bytes)) as z:
            is_zip = True
            target_file = None
            for name in z.namelist():
                if name.lower().endswith("content.xml") or name.lower() == "content.xml":
                    target_file = name
                    break
            
            if not target_file and len(z.namelist()) > 0:
                # İlk xml dosyasını al
                for name in z.namelist():
                    if name.lower().endswith(".xml"):
                        target_file = name
                        break

            if target_file:
                xml_data = z.read(target_file)
                # UTF-8 veya ISO-8859-9 dene
                try:
                    xml_str = xml_data.decode("utf-8")
                except UnicodeDecodeError:
                    xml_str = xml_data.decode("iso-8859-9", errors="replace")

                try:
                    root = ET.fromstring(xml_str)
                    texts = [elem.text for elem in root.iter() if elem.text]
                    extracted_text = "\n".join(texts)
                except Exception:
                    extracted_text = clean_xml_tags(xml_str)
    except zipfile.BadZipFile:
        is_zip = False

    # 2. Deneme: Düz XML metin dosyası
    if not extracted_text:
        try:
            content_str = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            content_str = raw_bytes.decode("iso-8859-9", errors="replace")

        try:
            root = ET.fromstring(content_str)
            texts = [elem.text for elem in root.iter() if elem.text]
            extracted_text = "\n".join(texts)
        except Exception:
            extracted_text = clean_xml_tags(content_str)

    cleaned_text = clean_xml_tags(extracted_text)
    if not cleaned_text:
        cleaned_text = "UDF belgesi metin içermiyor veya şifrelenmiş."

    # Evrak Türü Tespiti
    lower_text = cleaned_text.lower()
    doc_type = "UYAP Adliye Belgesi"
    for name, keywords in DOC_TYPES:
        if any(kw in lower_text for kw in keywords):
            doc_type = name
            break

    words = cleaned_text.split()
    word_count = len(words)
    char_count = len(cleaned_text)

    # Özet oluştur (İlk 3 paragraf veya 400 karakter)
    summary_preview = cleaned_text[:500] + ("..." if len(cleaned_text) > 500 else "")

    return {
        "success": True,
        "is_zip": is_zip,
        "document_type": doc_type,
        "word_count": word_count,
        "char_count": char_count,
        "summary": summary_preview,
        "full_text": cleaned_text
    }

def create_sample_udf_bytes(sample_text):
    """
    Test amaçlı standart UYAP UDF (ZIP tabanlı content.xml) dosyası üretir.
    """
    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<template version="1.0">
  <content>{sample_text}</content>
</template>"""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("content.xml", xml_content.encode("utf-8"))
    return buf.getvalue()

def generate_vekaletname_text(client, lawyer=None):
    """
    TBB ve Noterlik standartlarında Ahzu Kabz ve Özel Yetkileri içeren
    Genel Dava Vekaletnamesi Taslağı metni üretir.
    """
    c_name = client.get("full_name", "Belirtilmedi")
    c_id = client.get("id_number", "Belirtilmedi")
    c_city = client.get("city", "İstanbul")
    c_phone = client.get("phone", "")
    intake = client.get("intake_code", "DOSYA-2026")

    l_name = (lawyer or {}).get("name", "Av. Hakan Yılmaz")
    l_baro = (lawyer or {}).get("baro", "İstanbul Barosu")
    l_sicil = (lawyer or {}).get("sicil", "12345")
    l_addr = (lawyer or {}).get("address", "Adalet Sarayı Karşısı No:10")

    return f"""GENEL DAVA VEKALETNAMESİ TASLAĞI
(T.C. Noterlikleri ve UYAP Avukat Portalı İçin Hazırlanmıştır)

VEKİL EDEN (MÜVEKKİL):
Adı Soyadı / Unvan : {c_name}
TCKN / VKN         : {c_id}
İkametgah / Adres  : {c_city}
İletişim Telefon   : {c_phone}
Büro Dosya Kodu    : {intake}

VEKİL TAYİN EDİLEN:
Avukat             : {l_name} ({l_baro} - Sicil No: {l_sicil})
Adres              : {l_addr}

VEKALETNAME YETKİ KAPSAMI:
Leh ve aleyhime açılmış veya açılacak bilumum dava ve takiplerden dolayı T.C. Mahkemelerinin, meclislerinin, icra dairelerinin ve resmi makamlarının her derecesinde beni temsile; hak ve menfaatlerimi müdafaaya; dava açmaya, icra takibi yapmaya, icra takiplerinde haciz koydurmaya ve kaldırmaya;

ÖZEL YETKİLER (HMK m. 74 ve İlgili Mevzuat Uyarınca):
Ahzu kabza (hükmolunan parayı ve hakları tahsil etmeye, tesellüm etmeye), sulh olmaya, ibra etmeye, davadan ve kanun yollarından feragate, feragati kabule, karşı tarafı ibraya, kabul ve ikrarda bulunmaya, 6325 sayılı Kanun uyarınca dava şartı veya ihtiyari ARABULUCULUK süreçlerinde beni tam yetkiyle temsile ve son tutanakları imzalamaya, hakem tayinine, konkordato ve uzlaşma teklifinde bulunmaya, ihtiyati tedbir ve ihtiyati haciz talep etmeye, vekaleti kısmen veya tamamen başkalarına devir ve teşrike (tevkil yetkisi) ve azle mezun ve yetkili olmak üzere vekil tayin ettim.

Vekil Eden (Müvekkil):
{c_name}
İmza:
"""

def generate_uyap_vekalet_xml(client, lawyer=None):
    """
    UYAP Avukat Portalı vekaletname veri aktarım XML şeması üretir.
    """
    root = ET.Element("UyapVekaletname", versiyon="1.0", tip="GenelDavaVekaletnamesi")

    # Dosya Bilgisi
    dosya = ET.SubElement(root, "DosyaBilgisi")
    ET.SubElement(dosya, "BuroDosyaKodu").text = client.get("intake_code", "")
    ET.SubElement(dosya, "HukukiAlan").text = client.get("legal_category", "")

    # Vekil Eden
    vekil_eden = ET.SubElement(root, "VekilEden")
    ET.SubElement(vekil_eden, "AdSoyadUnvan").text = client.get("full_name", "")
    ET.SubElement(vekil_eden, "KimlikNo").text = client.get("id_number", "")
    ET.SubElement(vekil_eden, "Telefon").text = client.get("phone", "")
    ET.SubElement(vekil_eden, "Eposta").text = client.get("email", "")
    ET.SubElement(vekil_eden, "Sehir").text = client.get("city", "")

    # Vekil Avukat
    l_name = (lawyer or {}).get("name", "Av. Hakan Yılmaz")
    l_baro = (lawyer or {}).get("baro", "İstanbul Barosu")
    l_sicil = (lawyer or {}).get("sicil", "12345")

    vekil = ET.SubElement(root, "VekilAvukat")
    ET.SubElement(vekil, "AdSoyad").text = l_name
    ET.SubElement(vekil, "Baro").text = l_baro
    ET.SubElement(vekil, "SicilNo").text = l_sicil

    # Özel Yetkiler
    yetkiler = ET.SubElement(root, "OzelYetkiler")
    ET.SubElement(yetkiler, "AhzuKabz").text = "true"
    ET.SubElement(yetkiler, "SulhIbra").text = "true"
    ET.SubElement(yetkiler, "FeragatKabul").text = "true"
    ET.SubElement(yetkiler, "ArabuluculukTemsil").text = "true"
    ET.SubElement(yetkiler, "Tevkil").text = "true"

    xml_bytes = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    return xml_bytes.decode("utf-8")


# -------------------------------------------------------------------------------------------------
# 1136 Sayılı Avukatlık Kanunu m. 38 Çıkar Çatışması (Conflict Check) Motoru
# -------------------------------------------------------------------------------------------------

def normalize_text(text):
    if not text:
        return ""
    t = str(text).strip().lower()
    return (t.replace("ı", "i")
             .replace("ğ", "g")
             .replace("ü", "u")
             .replace("ş", "s")
             .replace("ö", "o")
             .replace("ç", "c")
             .replace("İ", "i"))


def check_conflict_of_interest(db_or_conn_or_list, query_data):
    """
    1136 Sayılı Avukatlık Kanunu m. 38/b ("Aynı işte menfaati zıt bir tarafa avukatlık etmiş veya mütalaa vermiş olması")
    ve TBB Meslek Kuralları Madde 35-36 esasları uyarınca:
    - Müvekkil adayı ile mevcut karşı taraflar arasında çatışma denetimi
    - Karşı taraf ile mevcut müvekkiller arasında çatışma denetimi
    - TCKN / VKN kesin eşleşmesi ve isim/unvan çapraz benzerlik analizi
    """
    query_data = query_data or {}
    c_name = query_data.get("full_name") or ""
    c_id = (query_data.get("id_number") or "").strip()
    o_name = query_data.get("opponent_name") or ""
    o_vkn = (query_data.get("opponent_vkn") or "").strip()
    exclude_code = query_data.get("intake_code") or ""

    norm_c_name = normalize_text(c_name)
    norm_o_name = normalize_text(o_name)

    # Veri kaynağını listeye dönüştür
    rows = []
    if isinstance(db_or_conn_or_list, list):
        rows = db_or_conn_or_list
    elif isinstance(db_or_conn_or_list, sqlite3.Connection):
        conn = db_or_conn_or_list
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM intakes")
        rows = [dict(r) for r in cur.fetchall()]
    elif isinstance(db_or_conn_or_list, str) and (db_or_conn_or_list.endswith(".db") or sqlite3):
        try:
            with sqlite3.connect(db_or_conn_or_list) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute("SELECT * FROM intakes")
                rows = [dict(r) for r in cur.fetchall()]
        except Exception:
            rows = []

    matches = []
    risk_level = "CLEAN"

    for r in rows:
        r_code = r.get("intake_code") or ""
        if exclude_code and r_code == exclude_code:
            continue

        r_client_name = r.get("full_name") or ""
        r_client_id = (r.get("id_number") or "").strip()
        r_opp_name = r.get("opponent_name") or ""
        r_opp_vkn = (r.get("opponent_vkn") or "").strip()
        r_status = r.get("status") or ""
        r_category = r.get("legal_category") or ""

        norm_r_client = normalize_text(r_client_name)
        norm_r_opp = normalize_text(r_opp_name)

        # 1. KRİTİK: Karşı Taraf olarak belirtilen kişi/şirket daha önce müvekkilimiz olmuş! (TCKN/VKN)
        if o_vkn and r_client_id and o_vkn == r_client_id:
            matches.append({
                "severity": "CRITICAL",
                "type": "OPPONENT_IS_FORMER_CLIENT",
                "intake_code": r_code,
                "legal_category": r_category,
                "status": r_status,
                "matched_value": o_vkn,
                "detail": f"Karşı taraf '{o_name}' ({o_vkn}), {r_code} sayılı dosyada MÜVEKKİLİMİZDİR. Avukatlık Kanunu m. 38 gereğince işin REDDİ zorunludur."
            })
            risk_level = "CRITICAL"

        # 2. KRİTİK: Başvuran kişi daha önce başka bir dosyada Karşı Taraf olmuş! (TCKN/VKN)
        if c_id and r_opp_vkn and c_id == r_opp_vkn:
            matches.append({
                "severity": "CRITICAL",
                "type": "APPLICANT_WAS_OPPONENT",
                "intake_code": r_code,
                "legal_category": r_category,
                "status": r_status,
                "matched_value": c_id,
                "detail": f"Başvuran '{c_name}' ({c_id}), {r_code} sayılı dosyada KARŞI TARAF olarak kayıtlıdır. Menfaat çatışması sebebiyle vekillik üstlenilmesi yasaktır."
            })
            if risk_level != "CRITICAL":
                risk_level = "CRITICAL"

        # 3. YÜKSEK: İsim bazlı çapraz eşleşme (Karşı Taraf = Eski Müvekkil)
        if norm_o_name and norm_r_client and (norm_o_name == norm_r_client or (len(norm_o_name) >= 6 and norm_o_name in norm_r_client)):
            # TCKN kontrolü henüz yapılmadıysa veya yoksa ekle
            if not any(m.get("intake_code") == r_code and m.get("type") == "OPPONENT_IS_FORMER_CLIENT" for m in matches):
                matches.append({
                    "severity": "HIGH",
                    "type": "NAME_MATCH_OPPONENT_IS_CLIENT",
                    "intake_code": r_code,
                    "legal_category": r_category,
                    "status": r_status,
                    "matched_value": r_client_name,
                    "detail": f"Karşı taraf ismi '{o_name}', {r_code} dosyasındaki müvekkilimiz '{r_client_name}' ile eşleşmektedir."
                })
                if risk_level not in ("CRITICAL", "HIGH"):
                    risk_level = "HIGH"

        # 4. YÜKSEK: İsim bazlı çapraz eşleşme (Başvuran = Eski Karşı Taraf)
        if norm_c_name and norm_r_opp and (norm_c_name == norm_r_opp or (len(norm_c_name) >= 6 and norm_c_name in norm_r_opp)):
            if not any(m.get("intake_code") == r_code and m.get("type") == "APPLICANT_WAS_OPPONENT" for m in matches):
                matches.append({
                    "severity": "HIGH",
                    "type": "NAME_MATCH_APPLICANT_WAS_OPPONENT",
                    "intake_code": r_code,
                    "legal_category": r_category,
                    "status": r_status,
                    "matched_value": r_opp_name,
                    "detail": f"Başvuran ismi '{c_name}', {r_code} dosyasındaki hasım/karşı taraf '{r_opp_name}' ile eşleşmektedir."
                })
                if risk_level not in ("CRITICAL", "HIGH"):
                    risk_level = "HIGH"

        # 5. ORTA / BİLGİ: Mevcut Müvekkilin Yeni Dosyası veya Mükerrer Başvuru
        if c_id and r_client_id and c_id == r_client_id:
            matches.append({
                "severity": "INFO",
                "type": "EXISTING_CLIENT",
                "intake_code": r_code,
                "legal_category": r_category,
                "status": r_status,
                "matched_value": c_id,
                "detail": f"Müvekkil '{c_name}', büromuzun {r_code} sayılı dosyasında da müvekkilimizdir (Mevcut Müvekkil)."
            })
            if risk_level == "CLEAN":
                risk_level = "INFO"

    has_conflict = any(m["severity"] in ("CRITICAL", "HIGH") for m in matches)
    if risk_level == "CRITICAL":
        legal_warning = "🚨 DİKKAT: Avukatlık Kanunu m. 38/b uyarınca aynı uyuşmazlıkta veya menfaati çatışan tarafa vekillik verilmesi kesin olarak YASAKTIR. Dosya derhal REDDEDİLMELİDİR."
    elif risk_level == "HIGH":
        legal_warning = "⚠️ UYARI: İsim ve unvan eşleşmesi bulunmaktadır. Dosya kabulünden önce TCKN/VKN ve geçmiş dosya ayrıntıları incelenmelidir."
    elif risk_level == "INFO":
        legal_warning = "ℹ️ BİLGİ: Başvuran büromuzun mevcut veya geçmiş müvekkilidir. Çıkar çatışması tespit edilmemiştir."
    else:
        legal_warning = "✅ TEMİZ: Yapılan conflict check sorgusunda herhangi bir menfaat çatışması tespit edilmemiştir."

    return {
        "has_conflict": has_conflict,
        "risk_level": risk_level,
        "conflict_count": len(matches),
        "matches": matches,
        "legal_warning": legal_warning,
        "statutory_basis": "1136 Sayılı Avukatlık Kanunu m. 38/b ve TBB Meslek Kuralları m. 35/36"
    }


# -------------------------------------------------------------------------------------------------
# 1136 Sayılı Avukatlık Kanunu m. 163 & 164 Avukatlık Ücret Sözleşmesi Şablonu
# -------------------------------------------------------------------------------------------------

def generate_avukatlik_ucret_sozlesmesi(client, terms=None, lawyer=None):
    """
    1136 Sayılı Avukatlık Kanunu m. 163 (Avukatlık sözleşmesinin serbestçe düzenlenmesi),
    m. 164 (Ücret tarifeleri ve karşı taraf vekalet ücreti) uyarınca
    resmi Avukatlık Ücret Sözleşmesi metni üretir.
    """
    terms = terms or {}
    c_name = client.get("full_name", "Belirtilmedi")
    c_id = client.get("id_number", "Belirtilmedi")
    c_city = client.get("city", "İstanbul")
    c_phone = client.get("phone", "")
    c_email = client.get("email", "")
    intake = client.get("intake_code", "DOSYA-2026")
    category = client.get("legal_category", "Genel Dava ve Hukuki Danışmanlık")
    opponent = client.get("opponent_name", "Belirtilmedi")

    l_name = (lawyer or {}).get("name", "Av. Hakan Yılmaz")
    l_baro = (lawyer or {}).get("baro", "İstanbul Barosu")
    l_sicil = (lawyer or {}).get("sicil", "12345")
    l_addr = (lawyer or {}).get("address", "Adalet Sarayı Karşısı No:10")

    fee_type = terms.get("ucret_turu", "nispi")
    if fee_type == "nispi":
        fee_rate = float(terms.get("ucret_orani", 0.15)) * 100
        fee_desc = f"Hükmolunacak / tahsil edilecek net dava ve takip bedelinin %{fee_rate:.1f}'i + %20 KDV"
    else:
        fee_amount = float(terms.get("ucret_tutari", 50000.0))
        fee_desc = f"{fee_amount:,.2f} TL (Türk Lirası) maktu ücret + %20 KDV"

    odeme_vadesi = terms.get("odeme_plani", "Vekaletnamenin teslimi ve dava açılışında peşin / tahsilatta")
    masraf_avansi = float(terms.get("masraf_avansi", 10000.0))
    jurisdiction = terms.get("yetkili_yer", "İstanbul Mahkemeleri ve İcra Daireleri")
    date_str = terms.get("sozlesme_tarihi") or datetime.now().strftime("%d.%m.%Y")

    return f"""AVUKATLIK ÜCRET SÖZLEŞMESİ
(1136 Sayılı Avukatlık Kanunu Madde 163 ve Madde 164 Hükümleri Uyarınca)

BÜRO DOSYA NO: {intake}
DÜZENLEME TARİHİ: {date_str}

1. TARAFLAR:
İŞ SAHİBİ (MÜVEKKİL):
Adı Soyadı / Unvan : {c_name}
TCKN / VKN         : {c_id}
Tebligat Adresi    : {c_city}
İletişim           : {c_phone} | {c_email}

VEKİL (AVUKAT):
Avukat             : {l_name} ({l_baro} - Sicil No: {l_sicil})
Büro Adresi        : {l_addr}

2. İŞİN KONUSU:
İşbu sözleşmenin konusu; İş Sahibi'nin, hasmı ({opponent}) aleyhine {category} alanında açılmış veya açılacak dava, icra takibi ve hukuki işlemlerin ilk derece mahkemeleri, istinaf (BAM) ve temyiz (Yargıtay/Danıştay) nezdinde yürütülmesi, takibi ve sonuçlandırılmasıdır.

3. AVUKATLIK ÜCRETİ VE ÖDEME ŞARTLARI:
a) Kararlaştırılan Ücret: {fee_desc}.
b) Ödeme Planı: İşbu ücret {odeme_vadesi} ödenecektir.
c) İşin sulh, feragat veya kabulle sonuçlanması halinde dahi Avukatlık Kanunu m. 165 uyarınca kararlaştırılan ücretin tamamı muaccel hale gelir.

4. GİDERLER VE MASRAF AVANSI:
HMK m. 120 uyarınca dava harçları, tebligat, keşif, bilirkişi ücretleri ve icra giderleri müvekkile aittir. İş Sahibi, dava açılışında asgari {masraf_avansi:,.2f} TL masraf avansını avukata tevdi etmeyi kabul eder.

5. KARŞI TARAF VEKALET ÜCRETİ (Avukatlık Kanunu Madde 164/Son):
Dava veya icra takibi sonucunda, mahkeme veya icra müdürlüğü tarafından tarifeye dayanılarak karşı tarafa yüklenecek ve ilamda hükmolunacak yasal vekalet ücreti tamamen ve münhasıran AVUKATA AİTTİR. İş Sahibi bu ücretten feragat edemez ve hak talep edemez.

6. YETKİLİ MAHKEME VE İCRA DAİRESİ:
İşbu sözleşmeden doğabilecek her türlü ihtilafın hallinde {jurisdiction} ile Türkiye Barolar Birliği Tahkim Kurulu yetkilidir.

İşbu sözleşme 6 maddeden ibaret olup, 2 (iki) nüsha olarak tanzim edilmiş ve taraflarca okunarak serbest iradeleriyle imza altına alınmıştır.

İŞ SAHİBİ (MÜVEKKİL)                         VEKİL (AVUKAT)
İmza                                         İmza / Kaşe
"""


def generate_gorusme_tutanagi(client, lawyer=None):
    """
    Avukat ve müvekkil adayı arasındaki ilk ön görüşme, uyuşmazlık özeti ve
    delil teslim tutanağını tanzim eder.
    """
    c_name = client.get("full_name", "Belirtilmedi")
    c_id = client.get("id_number", "Belirtilmedi")
    c_city = client.get("city", "İstanbul")
    intake = client.get("intake_code", "DOSYA-2026")
    category = client.get("legal_category", "Genel Hukuk")
    opponent = client.get("opponent_name", "Belirtilmedi")
    summary = client.get("case_summary", "Açıklama girilmedi.")
    evidences = client.get("evidences", [])
    if isinstance(evidences, list):
        evid_str = ", ".join(evidences) if evidences else "Belge ibraz edilmedi."
    else:
        evid_str = str(evidences)

    l_name = (lawyer or {}).get("name", "Av. Hakan Yılmaz")
    now_date = datetime.now().strftime("%d.%m.%Y - %H:%M")

    return f"""MÜVEKKİL İLK ÖN GÖRÜŞME VE DOSYA KABUL TUTANAĞI
(1136 Sayılı Avukatlık Kanunu ve Sır Saklama Yükümlülüğü Madde 36 Uyarınca)

DOSYA TAKİP KODU   : {intake}
GÖRÜŞME TARİHİ    : {now_date}
HUKUKİ ALAN        : {category}

TARAFLAR:
MÜVEKKİL ADAYI     : {c_name} (TCKN/VKN: {c_id})
KARŞI TARAF (HASIM): {opponent}
GÖRÜŞMEYİ YAPAN    : {l_name}

GÖRÜŞME DETAYLARI VE UYUŞMAZLIK ÖZETİ:
{summary}

TESLİM EDİLEN BELGE VE DELİLLER:
{evid_str}

BİLGİLENDİRME VE GİZLİLİK:
Müvekkil adayına Avukatlık Kanunu m. 36 gereğince görüşülen tüm hususların ve ibraz edilen belgelerin mesleki sır kapsamında KESİNLİKLE GİZLİ tutulacağı, işin kabulü halinde vekaletname tanzim edileceği ve ücret sözleşmesi akdedileceği bildirilmiştir.

MÜVEKKİL ADAYI                               AVUKAT
{c_name}                                     {l_name}
İmza                                         İmza"""

