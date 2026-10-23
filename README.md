# ⚖️ Hukuk Büroları İçin Müvekkil Ön Görüşme, Çıkar Çatışması ve UDF Portalı

[![Avukat Portal CI](https://github.com/eimza-kep/avukat-muvekkil-on-kayit-scripti/actions/workflows/ci.yml/badge.svg)](https://github.com/eimza-kep/avukat-muvekkil-on-kayit-scripti/actions/workflows/ci.yml)
[![Canlı Demo](https://img.shields.io/badge/Demo-Canl%C4%B1%20Test%20Et-brightgreen.svg)](https://eimza-kep.github.io/avukat-muvekkil-on-kayit-scripti/)
[![Docker Ready](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)](Dockerfile)
[![Lisans: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://python.org)
[![PHP: 7.4+](https://img.shields.io/badge/PHP-7.4%2B-purple.svg)](https://php.net)

Avukatlar, hukuk büroları ve arabulucular için; 1136 Sayılı Avukatlık Kanunu'na tam uyumlu **Müvekkil Ön Görüşme ve Dosya Kabul**, **Çıkar Çatışması (Conflict Check) Denetim Motoru (m. 38)**, **Avukatlık Ücret Sözleşmesi Tanzimi (m. 163 & 164)**, **UYAP UDF Evrak Ayrıştırıcı** ve **UYAP Avukat Portalı Vekaletname XML Dışa Aktarıcısı** barındıran açık kaynaklı LegalTech yazılımı.

---

## 🌟 Temel Yetenekler

1. **📄 UYAP Doküman Editörü (.udf) Ayrıştırıcı Entegrasyonu:**
   - Müvekkil adayının görüşmede getirdiği veya sisteme yüklediği mahkeme dilekçesi, tensip zaptı veya bilirkişi raporu `.udf` dosyalarını anında analiz eder, metin ve özet çıkararak doğrudan müvekkil kartına bağlar (`/api/upload-udf` & `/api/parse-udf`).
2. **📜 UYAP Avukat Portalı Vekaletname Taslağı ve XML Çıktısı:**
   - Müvekkil kabul edildiğinde; TBB ve Noterlik standartlarında Ahzu Kabz, Sulh, İbra, Arabuluculuk ve Tevkil yetkilerini içeren **Genel Dava Vekaletnamesi Taslağı** ve UYAP Avukat Portalı ile uyumlu XML çıktısı üretir (`/api/export-vekalet-xml`).
3. **🔍 Çıkar Çatışması (Conflict of Interest) Denetim Motoru (Avukatlık Kanunu Md. 38):**
   - Karşı taraf bilgileri (Ad/Unvan, TCKN/VKN) zorunlu olarak toplanır.
   - TCKN/VKN ve unvan çapraz taramalı derin analiz motoru (`/api/conflict-check`) sayesinde:
     - Karşı taraf eski müvekkilimiz ise: **🚨 KRİTİK ALARM (İşin reddi zorunludur)**
     - Başvuran eski bir hasım/davalı ise: **🚨 KRİTİK ALARM (Menfaat çatışması riski)**
     - İsim/unvan benzerliklerinde: **⚠️ YÜKSEK RİSK UYARISI**
4. **📜 1136 Sayılı Kanun m. 163 & 164 Avukatlık Ücret Sözleşmesi Tanzimi:**
   - Nispi (%) veya maktu (TL) avukatlık ücreti, KDV, ödeme vadesi, HMK m. 120 gider avansı ve **Avukatlık Kanunu m. 164/son fıkra uyarınca karşı taraf yasal vekalet ücretinin avukata ait olduğu** hükmünü içeren resmi Avukatlık Ücret Sözleşmesi üretir (`/api/ucret-sozlesmesi`).
5. **📋 Müvekkil İlk Görüşme ve Delil Teslim Tutanağı:**
   - Avukatlık Kanunu m. 36 mesleki sır saklama güvencesiyle görüşme özeti, teslim alınan deliller ve müvekkil taleplerini kayıt altına alan imzalı tutanak çıktısı (`/api/gorusme-tutanagi`).
6. **📊 Dosya Kabul ve Randevu Yönetim Paneli (`admin.html`):**
   - Dosya takip kodu (`DOSYA-2026-XXXX`) ile arama, aşama takibi (`Ön İncelemede` -> `Randevu Verildi` -> `Vekaletname Alındı / Dosya Açıldı` -> `Çıkar Çatışması / Red`), UDF belgesi inceleme, canlı conflict check araması ve Excel/CSV dışa aktarımı.
7. **🚀 Sıfır Bağımlılık (Zero-Dependency):**
   - Harici kütüphane gerektirmeyen standart Python modülleri (`sqlite3`, `zipfile`, `xml.etree`).

---

## 🚀 Hızlı Başlangıç

### 1. Windows (Tek Tıkla Çalıştır)
1. Repoyu indirin veya klonlayın.
2. `Baslat.bat` dosyasına çift tıklayın.
3. Otomatik olarak tarayıcınızda açılır:
   - Müvekkil Ön Kayıt Formu: `http://localhost:8082`
   - Dosya Yönetim Paneli: `http://localhost:8082/admin.html`

### 2. Linux & macOS
```bash
git clone https://github.com/eimza-kep/avukat-muvekkil-on-kayit-scripti.git
cd avukat-muvekkil-on-kayit-scripti
chmod +x baslat.sh
./baslat.sh
```

### 3. Docker ile Çalıştırma
```bash
docker build -t avukat-portal .
docker run -d -p 8082:8082 -v $(pwd)/hukuk_dosyalar.db:/app/hukuk_dosyalar.db avukat-portal
```

### 4. PHP / cPanel Paylaşımlı Hosting
Dosyaları sitenizin `public_html/on-kayit` dizinine yükleyin. `api.php` arka ucu JSON tabanlı veritabanı ile otomatik çalışacaktır.

---

## 🔌 API Uç Noktaları

| Yöntem | Endpoint | Açıklama |
|---|---|---|
| `GET` | `/` veya `/index.html` | Müvekkil ön görüşme başvuru formu |
| `GET` | `/admin.html` | Avukat dosya kabul ve conflict check paneli |
| `GET` | `/health` | Servis sağlık durumu kontrolü |
| `GET` | `/api/dosya-listesi` | Tüm kayıtlı başvuruların dökümü ve anlık conflict analizi |
| `POST` | `/api/on-kayit` | Yeni müvekkil ön görüşme kaydı oluşturma |
| `GET/POST` | `/api/conflict-check` | Avukatlık Kanunu m. 38 çıkar çatışması derin sorgulama motoru |
| `GET/POST` | `/api/ucret-sozlesmesi` | Avukatlık Kanunu m. 163 Avukatlık Ücret Sözleşmesi tanzimi |
| `GET/POST` | `/api/gorusme-tutanagi` | Müvekkil ilk ön görüşme ve delil teslim tutanağı üretme |
| `GET` | `/api/export-sozlesme-txt?code=...` | Ücret sözleşmesini veya görüşme tutanağını `.txt` olarak indirme |
| `GET` | `/api/vekaletname-taslagi?code=...` | Dosyaya ait genel dava vekaletname metni |
| `GET` | `/api/export-vekalet-xml?code=...` | UYAP Avukat Portalı vekalet XML dosyası indirme |
| `POST` | `/api/parse-udf` | Ham veya base64 UYAP UDF belgesi ayrıştırma |
| `POST` | `/api/upload-udf` | UDF evrakını doğrudan müvekkil dosyasına bağlama |

---

## 📊 Dosya Yapısı

```
avukat-muvekkil-on-kayit-scripti/
├── index.html              # Müvekkil ön kayıt formu ve UDF sürükle-bırak yükleyici
├── admin.html              # Avukat dosya kabul, conflict check ve vekalet paneli
├── server.py               # Python SQLite HTTP REST sunucusu (Port 8082)
├── api.php                 # PHP tabanlı REST backend
├── Dockerfile              # Docker container dağıtım dosyası
├── Baslat.bat              # Windows tek tıkla başlatıcı
├── baslat.sh               # Linux / macOS başlatıcı
├── scripts/
│   ├── udf_parser.py       # UDF ayrıştırıcı ve UYAP vekaletname motoru
│   └── test_avukat.py      # Kapsamlı birim test paketi
├── .github/
│   └── workflows/ci.yml    # GitHub Actions otomatik CI test akışı
└── README.md               # Detaylı dokümantasyon
```

---

## 🧪 Birim Testleri Çalıştırma

```bash
python scripts/test_avukat.py
```

Test paketi şunları doğrular:
- ✅ SQLite veritabanı şeması ve migration bütünlüğü
- ✅ 1136 Sayılı Avukatlık Kanunu m. 38 çıkar çatışması (conflict check) çapraz sorgulama ve alarm mantığı
- ✅ 1136 Sayılı Kanun m. 163 & 164 nispi ve maktu Avukatlık Ücret Sözleşmesi tanzimi
- ✅ Müvekkil ilk ön görüşme ve delil teslim tutanağı üretimi
- ✅ UYAP UDF (ZIP ve XML) dosya ayrıştırma, metin ve özet çıkarma
- ✅ TBB standartlarında Ahzu Kabz yetkili vekaletname metni ve UYAP XML şeması

---

## 🌐 LegalTech & E-Dönüşüm Açık Kaynak Ekosistemi

Bu yazılım, [@eimza-kep](https://github.com/eimza-kep) açık kaynak LegalTech ekosisteminin hukuk bürosu otomasyon bileşenidir. İlgili diğer araçlar:

* ⚖️ [avukat-hukuk-excel-hesaplamalari](https://github.com/eimza-kep/avukat-hukuk-excel-hesaplamalari) - Baro AAÜT vekalet ücreti, arabuluculuk ve icra harç hesaplayıcıları.
* ⚖️ [avukat-arabuluculuk-basvuru-scripti](https://github.com/eimza-kep/avukat-arabuluculuk-basvuru-scripti) - UYAP Arabuluculuk Portalı XML ve ilk oturum evrak portali.
* 📄 [udf2md](https://github.com/eimza-kep/udf2md) - UYAP `.udf` dava dosyalarını Markdown ve JSON'a dönüştürücü LegalTech aracı.
* 📝 [javascript-udf-editor](https://github.com/eimza-kep/uyap-web-udf-editor) - Tarayıcı tabanlı sıfır Java UYAP dilekçe görüntüleyici ve düzenleyici.
* 🔒 [kurumsal-kvkk-basvuru-scripti](https://github.com/eimza-kep/kurumsal-kvkk-basvuru-scripti) - Müvekkil KVKK aydınlatma ve açık rıza kayıt portali.
* 🌟 [awesome-turkiye-e-donusum](https://github.com/eimza-kep/awesome-turkiye-e-donusum) - Türkiye e-Dönüşüm açık kaynak araçları ve kütüphaneleri kürasyonu.

---

## 📜 Lisans

Bu proje **MIT Lisansı** ile lisanslanmıştır. Bireysel avukatlar ve kurumsal hukuk büroları tarafından serbestçe kullanılabilir.
