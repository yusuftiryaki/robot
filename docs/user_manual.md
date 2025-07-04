# Kullanım Kılavuzu
# Otonom Bahçe Asistanı (OBA) - User Manual

## 🚀 HIZLI BAŞLANGIÇ

### İlk Çalıştırma (5 Dakikada)

#### 1. Güç ve Güvenlik Kontrolleri
```
✅ Batarya şarj durumu: >%70
✅ Acil stop butonu test edildi
✅ Tüm tampon sensörleri çalışıyor
✅ Güç anahtarı OFF konumunda
✅ Çalışma alanı temiz ve engelsiz
```

#### 2. Sistem Başlatma
```bash
# Robot üzerindeki güç düğmesini açın
# LED'ler sırasıyla yanacak:
# 🔴 Power ON (Kırmızı)
# 🟡 Boot Process (Sarı)
# 🟢 System Ready (Yeşil)

# Wi-Fi bağlantısı kurulunca:
# 🔵 Network Connected (Mavi)
```

#### 3. Web Arayüzüne Erişim
```
1. Akıllı telefonunuzdan Wi-Fi listesine bakın
2. "BahceRobotu_XXXX" ağını bulun
3. Şifre: "robot2024"
4. Bağlandıktan sonra tarayıcıda: http://192.168.4.1
5. Ana kontrol paneli açılacak
```

## 📱 WEB ARAYÜZÜ KULLANIMI

### Ana Ekran Özellikleri

```
┌─────────────────────────────────────────┐
│  🤖 OTONOM BAHÇE ROBOTU v1.0           │
│                                         │
│  📹 [CANLI KAMERA GÖRÜNTÜSÜ]           │
│  ┌─────────────────────────────────────┐ │
│  │                                     │ │
│  │        🏞️ Bahçe Görünümü           │ │
│  │                                     │ │
│  └─────────────────────────────────────┘ │
│                                         │
│  📊 SİSTEM DURUMU                      │
│  ┌─────┬─────┬─────┬─────────────────┐ │
│  │🔋85%│📍GPS│🧭45°│ ⚡ Çalışıyor    │ │
│  └─────┴─────┴─────┴─────────────────┘ │
│                                         │
│  🎮 MANUEL KONTROL                     │
│  ┌─────────────────────────────────────┐ │
│  │    [🔼]         [▶️]  [STOP] [◀️]   │ │
│  │ [◀️][🔽][▶️]                        │ │
│  └─────────────────────────────────────┘ │
│                                         │
│  🗓️ GÖREV YÖNETİMİ                     │
│  ┌─────────────────────────────────────┐ │
│  │ [ALAN TARAMA] [NOKTA GİT] [ŞARJA GİT]│ │
│  └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

### 📹 Canlı Kamera
- **Gerçek zamanlı görüntü**: 30 FPS
- **Zoom**: Parmakla yakınlaştırma/uzaklaştırma
- **Tam ekran**: Çift dokunma
- **Kayıt**: Uzun basma ile video kayıt

### 📊 Durum Göstergeleri

#### Batarya Durumu
```
🔋 100% - 🟢 Mükemmel (>80%)
🔋 65%  - 🟡 İyi (50-80%)
🔋 30%  - 🟠 Düşük (20-50%)
🔋 10%  - 🔴 Kritik (<20%) → Otomatik şarjj
```

#### GPS Durumu
```
📍 3D Fix - 🟢 Hassas konum (±1m)
📍 2D Fix - 🟡 Yaklaşık konum (±5m)
📍 No Fix - 🔴 Konum bulunamıyor
```

#### Pusula (Yönelim)
```
🧭 45° - Robot burcu (0°=Kuzey)
⬆️ İleri yön göstergesi
📐 Açısal hassasiyet: ±2°
```

### 🎮 Manuel Kontrol

#### Temel Hareket
```
🔼 İleri Git    - Düz ileri hareket
🔽 Geri Git     - Düz geri hareket
◀️ Sola Dön     - Yerinde sola dönüş
▶️ Sağa Dön     - Yerinde sağa dönüş
⏹️ STOP        - Acil durma
```

#### Gelişmiş Kontroller
```
🎚️ Hız Kontrolü    - 10%-100% arası
🎯 Hassas Hareket   - Küçük adımlarla
🔄 Sürekli Dönüş    - Belirlenen açıya dön
📏 Mesafe Kontrolü  - Belirli mesafe git
```

**💡 İpucu**: Manuel kontrol sırasında otomatik sistemler devre dışı kalır.

### 🗓️ Görev Yönetimi

#### ALAN TARAMA Modu
```
1. [ALAN TARAMA] butonuna basın
2. Haritada başlangıç noktasını işaretleyin
3. Tarama alanının köşelerini belirleyin
4. Biçme parametrelerini ayarlayın:
   - Biçme yüksekliği: 2-5 cm
   - Hız: Yavaş/Normal/Hızlı
   - Kaplama: %70-95
5. [BAŞLAT] ile görevi başlatın
```

**Tarama Desenleri:**
```
📐 Biçerdöver:     ═══════════
                   ═══════════  (Önerilen)
                   ═══════════

🌀 Spiral:         ┌─────────┐
                   │ ┌─────┐ │  (Dar alanlar)
                   │ └─────┘ │

🎯 Rastgele:       ∿∿∿∿∿∿∿∿∿
                   ∿∿∿∿∿∿∿∿∿  (Engelli alanlar)
```

#### NOKTA GİT Modu
```
1. [NOKTA GİT] butonuna basın
2. Haritada hedef noktayı dokunarak seçin
3. Rota seçeneklerini belirleyin:
   - En kısa yol
   - Engelleri dolaş
   - Güvenli rota
4. [GİT] ile görevi başlatın
```

#### ŞARJA GİT Modu
```
🔋 Otomatik: Batarya %25'in altına düştüğünde
📍 Manuel: [ŞARJA GİT] butonuyla istediğiniz zaman
🎯 Akıllı Şarj: Görev tamamlandıktan sonra

Şarj İstasyonu Bulma:
- IR işaretleri takip eder
- Kamera ile görsel tanıma
- Hassas yanaşma (<2cm)
- Otomatik bağlantı
```

## 🛡️ GÜVENLİK ÖZELLİKLERİ

### Acil Durma Sistemleri

#### 1. Manuel Acil Stop
```
🔴 Fiziksel Buton: Robot üzerinde kırmızı buton
📱 Mobil Acil Stop: Uygulamada STOP butonu
⌨️ Tuş Kombinasyonu: Ctrl+Alt+S (web arayüzü)
```

#### 2. Otomatik Güvenlik
```
⚠️ Tampon Sensörleri: Çarpma anında dur
📏 Mesafe Koruması: 10cm'den yakın dur
⚖️ Eğim Koruması: >20° eğimde dur
🔋 Düşük Batarya: Kritik seviyede şarja git
🌡️ Aşırı Isınma: Sıcaklık koruması
```

#### 3. Yazılım Güvenliği
```
🚧 Sanal Çit: Belirlenen alanın dışına çıkmaz
🏠 Ev Koruması: Bina yakınında yavaşlar
🌳 Engel Hafızası: Öğrenilen engelleri hatırlar
⏰ Zaman Koruması: Gece çalışmaz (opsiyonel)
```

### Güvenlik Ayarları
```
🔧 Ayarlar → Güvenlik

📏 Minimum Mesafe: 5-30 cm (varsayılan: 10cm)
⚖️ Maksimum Eğim: 10-25° (varsayılan: 15°)
⚡ Acil Fren Mesafesi: 2-10 cm (varsayılan: 5cm)
🔔 Ses Uyarıları: Açık/Kapalı
📱 SMS Uyarıları: Kritik durumlar için
```

## 🔧 BAKIM VE TEMİZLİK

### Günlük Bakım (5 dakika)

#### Temizlik Kontrolleri
```
1. 🧽 Fırçaları temizle:
   - Ana fırçayı çıkart
   - Saçları ve ipleri temizle
   - Su ile yıka ve kurula

2. 🔍 Sensörleri kontrol et:
   - Ultrasonik sensörlerde kir/böcek var mı?
   - Kamera lensini yumuşak bezle sil
   - Tampon sensörleri test et

3. ⚙️ Mekanik kontrol:
   - Tekerlek çevresindeki saçları çıkart
   - Vida gevşeklikleri kontrol et
   - Anormal ses var mı?
```

#### Yazılım Kontrolleri
```
📱 Mobil uygulamadan:
- Log dosyalarını kontrol et
- Hata mesajları var mı?
- Güncellemeler mevcut mu?
- Disk alanı yeterli mi?

🔋 Batarya durumu:
- Şarj döngü sayısı
- Maksimum kapasite kaybı
- Anormal ısınma var mı?
```

### Haftalık Bakım (30 dakika)

#### Detaylı Temizlik
```
1. 🚿 Su ile yıkama:
   - Elektronik bölgesi kapalı
   - Alçak basınç kullan
   - Sabun yerine özel temizleyici

2. 🔧 Mekanik servis:
   - Tekerlek rulmanları yağla
   - Motor bağlantıları sıkıştır
   - Kablo bağlantıları kontrol et

3. 🖥️ Yazılım bakımı:
   - Tam sistem güncellemesi
   - Log dosyalarını temizle
   - Veri tabanını optimize et
   - Yedek alma
```

### Aylık Bakım (2 saat)

#### Kapsamlı Kontrol
```
🔋 Batarya bakımı:
- Kapasite testi
- Hücre dengeleme
- Terminal temizliği
- Değiştirme gereksinimi

⚙️ Kalibrasyon:
- IMU sensör kalibrasyonu
- GPS referans noktası güncelle
- Kamera focus ayarı
- Motor encoder kalibrasyonu

🧪 Performans testleri:
- Hız ve hassasiyet testleri
- Batarya yaşam süre testi
- Sensör doğruluk testleri
- İletişim kalitesi testi
```

## 📊 PERFORMANS TAKİBİ

### Çalışma İstatistikleri

#### Günlük Rapor
```
📈 Robot Performans Raporu - 25.12.2024

⏰ Çalışma Süresi: 3 saat 25 dakika
📏 Kat Edilen Mesafe: 2.8 km
🔋 Batarya Kullanımı: %78 → %12
🎯 Görev Başarı Oranı: %94

📊 Alan Bilgileri:
- Biçilen Alan: 850 m²
- Ortalama Hız: 0.35 m/s
- Engel Karşılaşma: 12 kez
- Şarj Döngüsü: 2 kez

⚠️ Dikkat Gereken Durumlar:
- Sol tekerlek anormal titreşim (14:30)
- GPS sinyal kaybı (15:45-15:47)
- Yüksek motor sıcaklığı (16:20)
```

#### Haftalık Trend
```
📊 Haftalık Performans Trendi

Verimlilik: ████████░░ %85 (↗️ %3)
Güvenilirlik: ██████████ %97 (→ %0)
Enerji Tasarrufu: ███████░░░ %72 (↗️ %5)

🔥 En İyi Gün: Çarşamba (%97 verimlilik)
❄️ En Zor Gün: Pazartesi (%78 verimlilik, yağmur)

💡 Öneriler:
- Sol motor bakımı önerilir
- Kamera lens temizliği gerekli
- GPS anteni pozisyonu optimize edilebilir
```

### Hata Yönetimi

#### Yaygın Uyarılar ve Çözümleri

```
⚠️ UYARI: "Düşük GPS sinyali"
🔧 Çözüm:
- Açık alana taşı
- GPS anteni kontrol et
- 2-3 dakika bekle

⚠️ UYARI: "Yüksek motor sıcaklığı"
🔧 Çözüm:
- Robotu gölgelik alana taşı
- 10 dakika soğumasını bekle
- Motor fan çalışıyor mu kontrol et

⚠️ UYARI: "Tampon sensör aktif"
🔧 Çözüm:
- Robotun etrafını kontrol et
- Engeli kaldır
- Sensör temizliği yap

⚠️ UYARI: "Kalman filtresi sapması"
🔧 Çözüm:
- IMU kalibrasyonu yap
- Robotun düz zeminde olduğundan emin ol
- Sistemi restart et
```

#### Kritik Hatalar

```
🚨 HATA: "Acil stop aktif"
🔧 Çözüm:
1. Güvenlik butonunu kontrol et
2. Sistemi manuel olarak restart et
3. Tüm sensörleri test et

🚨 HATA: "Motor sürücü hatası"
🔧 Çözüm:
1. Ana gücü kapat
2. Motor bağlantıları kontrol et
3. L298N kartını kontrol et
4. Teknik servis gerekiyorsa iletişime geç

🚨 HATA: "Kritik batarya seviyesi"
🔧 Çözüm:
1. Robotu derhal şarj istasyonuna götür
2. Manuel olarak şarj et
3. Batarya kapasitesini test et
```

## 🌐 UZAKTAN ERİŞİM

### Wi-Fi Konfigürasyonu

#### Ev Wi-Fi'ı Bağlama
```
1. Web arayüzünde Ayarlar → Wi-Fi
2. "Mevcut Ağları Tarama"
3. Ev ağınızı seçin
4. Şifreyi girin
5. "Bağlan" tuşuna basın
6. Robot restart olacak
7. Ev ağından 192.168.1.xxx IP ile erişin
```

#### Uzaktan Erişim (İnternet üzerinden)
```
🌍 Gereksinimler:
- Dinamik DNS servisi (DuckDNS vb.)
- Router port yönlendirme (8080 → Robot IP)
- VPN bağlantısı (güvenlik için önerilir)

📱 Mobil erişim:
- Android/iOS uygulaması
- Push notification'lar
- GPS konum takibi
- Acil uzaktan kapama
```

### Bulut Hizmetleri

#### Veri Senkronizasyonu
```
☁️ Otomatik yedekleme:
- Günlük performans verileri
- Hata logları
- Harita verileri
- Görev geçmişi

📊 Analitik:
- Performans trendleri
- Karşılaştırmalı analiz
- Tahmine dayalı bakım
- Kullanım optimizasyonu
```

Bu kılavuz robotunuzun tüm özelliklerini etkin şekilde kullanmanıza yardımcı olacaktır. Sorularınız için teknik destek ekibimizle iletişime geçin! 🤖

**📞 Teknik Destek**: support@bahcerobotu.com
**📱 Telegram Grubu**: @BahceRobotuDestek
**📚 Dokümantasyon**: https://docs.bahcerobotu.com
