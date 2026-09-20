# ⚖️ Hukuk Büroları İçin Müvekkil Ön Görüşme ve Çıkar Çatışması Scripti

[![CI](https://github.com/eimza-kep/avukat-muvekkil-on-kayit-scripti/actions/workflows/ci.yml/badge.svg)](https://github.com/eimza-kep/avukat-muvekkil-on-kayit-scripti/actions/workflows/ci.yml)
[![Lisans: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Kurulum Süresi](https://img.shields.io/badge/Kurulum-1%20Dakika-brightgreen)](#)
[![Bağımlılık](https://img.shields.io/badge/ba%C4%9F%C4%B1ml%C4%B1l%C4%B1k-0%20(S%C4%B1f%C4%B1r)-blue)](#)

Avukatlar, hukuk büroları ve arabulucuların web sitelerine veya intranetlerine **1 dakikada kurabileceği**, 1136 Sayılı Avukatlık Kanunu'na tam uyumlu **Müvekkil Ön Görüşme, Dosya Kabul ve Çıkar Çatışması (Conflict Check) Scripti**.

---

## 🌟 Temel Özellikler

1. **Prestijli ve Kurumsal Tasarım:**
   - Müvekkil adayı bilgileri (Bireysel / Tüzel Kişi, TCKN/VKN, İletişim).
   - Hukuki Uyuşmazlık Kategorisi (İş Hukuku, Gayrimenkul & Kira, Ticaret & Şirketler, İcra & Alacak, Aile & Boşanma vb.).
   - Olay özeti ve mevcut delil envanteri kontrol listesi (Sözleşme, dekont, WhatsApp yazışması, ihtarname).
2. **Çıkar Çatışması (Conflict Check) Denetimi (Avukatlık Kanunu Md. 38):**
   - Karşı taraf bilgileri zorunlu olarak toplanır.
   - Yönetim panelindeki canlı arama çubuğu ile geçmiş müvekkiller ve karşı taraflar taranarak çıkar çatışması riski anında tespit edilir.
3. **Avukatlık Sır Saklama ve Gizlilik Beyanı (Avukatlık Kanunu Md. 36):**
   - Form sonunda yer alan yasal gizlilik ve aydınlatma onayı ile mesleki etik kurallarına tam uyum sağlanır.
4. **Dosya Kabul ve Randevu Yönetim Paneli (`admin.html`):**
   - Başvuruları listeleme, filtreleme ve aşamalarını takip etme (`Ön İncelemede` -> `Randevu Verildi` -> `Vekaletname Alındı / Dosya Açıldı` -> `Çıkar Çatışması / Red`).
   - Tek tıkla Excel/CSV dışa aktarma.
5. **Çift Arka Uç Desteği:**
   - **cPanel / Paylaşımlı Hosting:** `api.php` ve JSON depolama.
   - **VPS / Yerel:** Python `server.py` ve SQLite veritabanı.
   - **Statik:** Tarayıcı yerel hafızası (`localStorage`).

---

## 🚀 1 Dakikada Kurulum

### 1. Windows'ta Tek Tıkla Çalıştırma (Test & Demo)
Klasördeki **`Baslat.bat`** dosyasına çift tıklayın! Yerel sunucu otomatik başlar ve tarayıcınızda form açılır.

### 2. Paylaşımlı Hosting / cPanel (Apache & PHP)
1. Dosyaları zip olarak indirin.
2. Sitenizin `public_html/on-gorusme` dizinine yükleyin.
3. `https://siteniz.com/on-gorusme/` adresinden doğrudan kullanın!

### 3. Python Sunucusu ile Çalıştırma
```bash
python server.py
```
- Müvekkil Ön Görüşme Formu: `http://localhost:8082/index.html`
- Dosya Kabul Yönetim Paneli: `http://localhost:8082/admin.html`

---

## 📜 Lisans

Bu proje [MIT Lisansı](LICENSE) ile lisanslanmıştır. Bireysel avukatlar ve kurumsal hukuk büroları tarafından serbestçe kullanılabilir.
