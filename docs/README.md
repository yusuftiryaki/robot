# 📋 Dokümantasyon İndeksi
# Otonom Bahçe Asistanı (OBA) - Tüm Belgeler

## 🚀 HIZLI ERİŞİM

### Başlangıç Rehberleri
- [🏠 Ana README](../README.md) - Proje ana sayfası
- [🚀 Hızlı Başlangıç](../README.md#hızlı-başlangıç) - Geliştirme ortamı kurulumu
- [🍓 Raspberry Pi Setup](deployment/raspberry_pi_setup.md) - Production kurulum

### Kalibrasyon Sistemi
- [🔧 Kalibrasyon Ana Rehberi](calibration/README.md) - Tüm kalibrasyon sistemleri
- [📏 Encoder Kalibrasyonu](calibration/encoder_calibration_guide.md) - Encoder kalibrasyon rehberi
- [📷 Kamera Kalibrasyonu](calibration/camera_calibration_guide.md) - Kamera kalibrasyon rehberi

---

## 📚 DETAYLI DOKÜMANTASYON

### 🔧 Hardware Dokümantasyonu
```
docs/hardware/
├── assembly_guide.md          # Montaj rehberi
├── wiring_diagram.md          # Elektriksel şemalar
└── troubleshooting.md         # Hardware sorun giderme
```

**Öne Çıkan Konular:**
- Mi Vacuum Essential dönüşümü
- Raspberry Pi 4 entegrasyonu
- Motor ve encoder bağlantıları
- Kamera ve sensör kurulumu
- Güç sistemi tasarımı

### 📏 Kalibrasyon Dokümantasyonu
```
docs/calibration/
├── README.md                  # Ana kalibrasyon rehberi
├── encoder_calibration_guide.md  # Encoder kalibrasyonu
└── camera_calibration_guide.md   # Kamera kalibrasyonu
```

**Öne Çıkan Konular:**
- Encoder mesafe kalibrasyonu
- Tekerlek base kalibrasyonu
- Kamera lens distorsiyon düzeltmesi
- AprilTag tespit optimizasyonu
- Sistem doğrulama testleri

### 🚀 Deployment Dokümantasyonu
```
docs/deployment/
└── raspberry_pi_setup.md      # Raspberry Pi kurulum rehberi
```

**Öne Çıkan Konular:**
- Raspberry Pi OS kurulumu
- Sistem konfigürasyonu
- Service kurulumu
- Network ayarları
- Güvenlik konfigürasyonu

### 📱 Kullanım Dokümantasyonu
```
docs/
├── user_manual.md             # Kullanım kılavuzu
├── apriltag_placement_guide.md  # AprilTag yerleştirme
├── apriltag_printing_guide.md   # AprilTag yazdırma
└── docker_setup.md            # Docker kurulumu
```

**Öne Çıkan Konular:**
- Web arayüzü kullanımı
- Robot kontrolü
- Görev programlama
- AprilTag sistemi
- Bakım ve kalibrasyon

---

## 🎯 KONUYA GÖRE ERİŞİM

### 🔧 Kalibrasyon Yapmak İstiyorum
1. [Ana Kalibrasyon Rehberi](calibration/README.md) - Genel bakış
2. [Encoder Kalibrasyonu](calibration/encoder_calibration_guide.md) - Mesafe ve dönüş
3. [Kamera Kalibrasyonu](calibration/camera_calibration_guide.md) - Görüntü işleme

### 🔨 Robot Kurmak İstiyorum
1. [Hardware Montaj](hardware/assembly_guide.md) - Fiziksel kurulum
2. [Raspberry Pi Setup](deployment/raspberry_pi_setup.md) - Yazılım kurulumu
3. [Kalibrasyon Sistemi](calibration/README.md) - Sistem kalibrasyonu

### 🏷️ AprilTag Sistemi Kurmak İstiyorum
1. [AprilTag Yazdırma](apriltag_printing_guide.md) - Tag yazdırma
2. [AprilTag Yerleştirme](apriltag_placement_guide.md) - Tag yerleştirme
3. [Kamera Kalibrasyonu](calibration/camera_calibration_guide.md) - Tespit optimizasyonu

### 🐛 Sorun Gidermek İstiyorum
1. [Hardware Troubleshooting](hardware/assembly_guide.md#sorun-giderme) - Donanım sorunları
2. [Kalibrasyon Troubleshooting](calibration/README.md#sorun-giderme) - Kalibrasyon sorunları
3. [User Manual](user_manual.md) - Genel kullanım sorunları

### 💻 Geliştirme Yapmak İstiyorum
1. [Ana README](../README.md) - Proje yapısı
2. [Docker Setup](docker_setup.md) - Development ortamı
3. [API Dokümantasyonu](../src/README.md) - Kod yapısı

---

## 📊 DOKÜMANTASYON İSTATİSTİKLERİ

### Güncel Dokümantasyon Durumu
```
✅ Tamamlanan Belgeler:
- [x] Ana README.md
- [x] Hardware montaj rehberi
- [x] Raspberry Pi setup rehberi
- [x] Encoder kalibrasyon rehberi (YENİ)
- [x] Kamera kalibrasyon rehberi (YENİ)
- [x] Kalibrasyon ana rehberi (YENİ)
- [x] User manual
- [x] AprilTag rehberleri

🔄 Güncellenecek Belgeler:
- [ ] API dokümantasyonu
- [ ] Troubleshooting rehberi
- [ ] Developer guide
- [ ] Hardware wiring diagram

📋 Eksik Belgeler:
- [ ] IMU kalibrasyon rehberi
- [ ] GPS kalibrasyon rehberi
- [ ] Advanced configuration guide
- [ ] Performance tuning guide
```

### Dokümantasyon Metrikleri
```
📄 Toplam Sayfa Sayısı: 12
📏 Toplam Satır Sayısı: ~3,500
🔧 Kalibrasyon Sayfaları: 3 (YENİ)
🚀 Setup Rehberleri: 2
📱 Kullanım Rehberleri: 4
🔨 Hardware Rehberleri: 3
```

---

## 🎉 YENİ EKLENENLER (2025-07-09)

### 🔧 Kapsamlı Kalibrasyon Dokümantasyonu
- **[Ana Kalibrasyon Rehberi](calibration/README.md)** - Tüm kalibrasyon sistemlerine genel bakış
- **[Encoder Kalibrasyon Rehberi](calibration/encoder_calibration_guide.md)** - Detaylı encoder kalibrasyonu
- **[Kamera Kalibrasyon Rehberi](calibration/camera_calibration_guide.md)** - Kapsamlı kamera kalibrasyonu

### 📈 Özellikler
- ✅ Adım adım kalibrasyon prosedürleri
- ✅ Troubleshooting rehberleri
- ✅ Performans optimizasyonu
- ✅ Kalite kontrol kriterleri
- ✅ Interaktif script kullanımı
- ✅ Hata analizi ve çözümleri

### 🔗 Entegrasyon
- Ana README.md güncellendi
- User manual güncellendi
- Hardware assembly guide güncellendi
- AprilTag placement guide güncellendi
- Raspberry Pi setup güncellendi

---

## 📋 KALITE KONTROL

### Dokümantasyon Kalite Kriterleri
```
✅ Her belge şunları içerir:
- Açık başlık ve amaç
- Adım adım talimatlar
- Kod örnekleri
- Troubleshooting bölümü
- Güncellenme tarihi
- Yazar bilgisi

✅ Teknik kalite:
- Doğru komut satırı örnekleri
- Güncel dosya yolları
- Çalışır kod parçaları
- Açık hata mesajları
- Performans metrikleri
```

### Güncellik Takibi
```
📅 Son Güncelleme: 2025-07-09
🔄 Güncelleme Sıklığı: Hardware değişikliği ile
📝 Bakım Sorumlusu: Hacı Abi
🎯 Hedef Audience: Geliştiriciler ve Son Kullanıcılar
```

---

## 🤝 KATKI SAĞLAMA

### Dokümantasyon Katkısı
```bash
# Yeni dokümantasyon ekleme
1. docs/ klasörüne uygun dosyayı ekle
2. Bu index dosyasını güncelle
3. Ana README.md'yi güncelle
4. Pull request aç

# Mevcut dokümantasyon güncelleme
1. İlgili dosyayı düzenle
2. Güncellenme tarihini güncelle
3. Değişiklikleri test et
4. Pull request aç
```

### Dokümantasyon Standartları
- Markdown formatı kullan
- Türkçe yazım kurallarına uy
- Emoji kullan (görsel zenginlik için)
- Kod örnekleri ekle
- Troubleshooting bölümü ekle

---

## 🔗 HIZLI LİNKLER

### Ana Belgeler
- [🏠 Ana README](../README.md)
- [🔧 Kalibrasyon](calibration/README.md)
- [🍓 Raspberry Pi Setup](deployment/raspberry_pi_setup.md)
- [📱 User Manual](user_manual.md)

### Kalibrasyon Sistemi
- [📏 Encoder Kalibrasyonu](calibration/encoder_calibration_guide.md)
- [📷 Kamera Kalibrasyonu](calibration/camera_calibration_guide.md)
- [🏷️ AprilTag Sistemi](apriltag_placement_guide.md)

### Geliştirme
- [🐳 Docker Setup](docker_setup.md)
- [🔨 Hardware Assembly](hardware/assembly_guide.md)
- [🔧 Wiring Diagram](hardware/wiring_diagram.md)

---

**Son Güncelleme:** 2025-07-09
**Versiyon:** 2.0 (Kalibrasyon dokümantasyonu eklendi)
**Yazar:** Hacı Abi 📚
