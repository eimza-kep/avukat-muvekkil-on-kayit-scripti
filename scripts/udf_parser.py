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
