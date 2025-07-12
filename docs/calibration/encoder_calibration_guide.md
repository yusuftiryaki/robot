# 🔧 Encoder Kalibrasyon Rehberi
# Otonom Bahçe Asistanı (OBA) - Encoder Kalibrasyon Dokümantasyonu

## 📋 GİRİŞ

### Encoder Kalibrasyonu Nedir?

Encoder kalibrasyonu, robotun tekerlek encoderlarından aldığı pulse sinyallerini gerçek mesafe ve açı değerlerine doğru bir şekilde dönüştürmek için yapılan kritik bir işlemdir. Bu kalibrasyon olmadan robot:

- ❌ Mesafeyi yanlış ölçer
- ❌ Hedefine ulaşamaz
- ❌ Düz çizgide gidemez
- ❌ Doğru açılarda dönemez

### Kalibrasyon Türleri

1. **Mesafe Kalibrasyonu** - Pulse sayısından gerçek mesafeyi hesaplama
2. **Dönüş Kalibrasyonu** - Tekerlek base mesafesini doğru belirleme
3. **Doğrulama Testi** - Kalibrasyonu kontrol etme

---

## 🔍 ENCODER SİSTEMİ ANALİZİ

### Robot Encoder Konfigürasyonu

```yaml
# config/robot_config.yaml
hardware:
  sensors:
    encoders:
      sol_encoder:
        pin_a: 19                    # GPIO19 - Sol encoder A kanalı
        pin_b: 16                    # GPIO16 - Sol encoder B kanalı
        pulses_per_revolution: 360   # Motor encoder çözünürlüğü
      sag_encoder:
        pin_a: 26                    # GPIO26 - Sağ encoder A kanalı
        pin_b: 20                    # GPIO20 - Sağ encoder B kanalı
        pulses_per_revolution: 360   # Motor encoder çözünürlüğü

navigation:
  wheel_diameter: 0.065    # metre (tekerlek çapı)
  wheel_base: 0.235       # metre (tekerlekler arası mesafe)
  max_speed: 0.5          # m/s (maksimum hız)
  max_angular_speed: 1.0  # rad/s (maksimum açısal hız)
```

### Teorik Hesaplamalar

```python
# Temel formüller
tekerlek_cevresi = π × tekerlek_capi
pulse_per_meter = pulses_per_revolution / tekerlek_cevresi
mesafe = pulse_sayisi / pulse_per_meter

# Örnek hesaplama
tekerlek_capi = 0.065m
tekerlek_cevresi = 3.14159 × 0.065 = 0.204m
pulse_per_meter = 360 / 0.204 = 1765 pulse/m
```

---

## 🚀 ENCODER KALİBRASYON SCRIPTI

### Script Özellikleri

```bash
# Script konumu
/workspaces/oba/scripts/encoder_calibration.py

# Temel kullanım
python scripts/encoder_calibration.py --interactive

# Komut satırı seçenekleri
--distance DISTANCE    # Kalibrasyon mesafesi (metre)
--angle ANGLE          # Kalibrasyon açısı (derece)
--test                 # Doğrulama testi
--interactive          # İnteraktif mod
--config CONFIG        # Konfigürasyon dosyası yolu
```

### Script Yapısı

```python
class EncoderKalibrator:
    """Encoder kalibrasyon sınıfı"""

    def __init__(self, config_path: str = None):
        """Kalibratörü başlat"""

    async def mesafe_kalibrasyonu(self, hedef_mesafe: float = 1.0):
        """Mesafe kalibrasyonu yapar"""

    async def donus_kalibrasyonu(self, hedef_aci: float = 90.0):
        """Dönüş kalibrasyonu yapar"""

    async def dogrulama_testi(self, test_mesafe: float = 0.5):
        """Kalibrasyon doğrulama testi"""

    async def konfigurasyonu_guncelle(self):
        """Sonuçları config dosyasına yazar"""
```

---

## 📏 MESAFE KALİBRASYONU

### Adım 1: Hazırlık

```bash
# Gerekli araçlar
- Metre/cetvel (minimum 2 metre)
- Düz zemin (minimum 3 metre)
- Kağıt/kalem (ölçümleri not etmek için)

# Çalışma alanı hazırlığı
1. Robot'u düz zemine yerleştir
2. Önünde 2 metre engelsiz alan olsun
3. Başlangıç noktasını işaretle
4. Ölçüm aracını hazırla
```

### Adım 2: Script Başlatma

```bash
# İnteraktif mod ile başlat
cd /workspaces/oba
python scripts/encoder_calibration.py --interactive

# Menüden "1. Mesafe Kalibrasyonu" seç
```

### Adım 3: Kalibrasyon Süreci

```
🔧 Encoder Kalibrasyon Süreci:

1. Script encoder sayaçlarını sıfırlar
2. Başlangıç encoder değerlerini okur
3. Robot belirtilen mesafe kadar hareket eder
4. Bitiş encoder değerlerini okur
5. Kullanıcıdan fiziksel mesafe ölçümü ister
6. Kalibrasyon hesaplamalarını yapar
7. Sonuçları gösterir
```

### Adım 4: Fiziksel Ölçüm

```
📐 Fiziksel Ölçüm Adımları:

1. Robot'un hareket ettiği mesafeyi ölçün
2. Başlangıç ve bitiş noktaları arasındaki GERÇEK mesafeyi alın
3. Ölçümü metre cinsinden script'e girin
4. Hassasiyet için 0.001m (1mm) hassasiyetinde ölçün

⚠️ DİKKAT: Tekerlek kayması olabilir, gerçek mesafeyi ölçün!
```

### Adım 5: Sonuç Analizi

```
📊 Örnek Kalibrasyon Sonuçları:

============================================================
📊 MESAFE KALİBRASYON SONUÇLARI
============================================================
📏 Fiziksel Mesafe: 1.000 m
🔢 Sol Encoder Pulse: 1750
🔢 Sağ Encoder Pulse: 1760
📊 Ortalama Pulse: 1755.0
📐 Pulse/Meter (Gerçek): 1755.0
📐 Pulse/Meter (Teorik): 1765.0
⚠️  Hata: -0.6%
🔧 Mevcut Tekerlek Çapı: 0.065 m
🔧 Önerilen Tekerlek Çapı: 0.066 m
🔧 Kalibrasyon Faktörü: 0.994
============================================================
```

### Hata Değerlendirme

```python
# Hata toleransları
if abs(hata_yuzdesi) < 2:
    print("✅ Kalibrasyon çok iyi! Hata %2'nin altında.")
elif abs(hata_yuzdesi) < 5:
    print("⚠️ Kalibrasyon kabul edilebilir. Hata %5'in altında.")
else:
    print("❌ Kalibrasyon düzeltilmeli! Hata %5'in üstünde.")
```

---

## 🔄 DÖNÜŞ KALİBRASYONU

### Dönüş Kalibrasyonu Nedir?

Dönüş kalibrasyonu, robot'un tekerlek base mesafesini (tekerlekler arası mesafe) doğru belirleme işlemidir. Bu değer yanlış olursa:

- Robot istenen açıdan fazla veya az döner
- Hedefine varmak için sürekli düzeltme yapar
- Navigasyon hassasiyeti düşer

### Adım 1: Hazırlık

```bash
# Gerekli araçlar
- Açı ölçer (rapportör/dijital açı ölçer)
- Sabit referans noktası (duvar/çizgi)
- Kalem (robot yönünü işaretlemek için)

# Robot pozisyonu
1. Robot'u düz zemine yerleştir
2. Ön tarafını sabit bir referans noktasına hizala
3. Başlangıç açısını işaretle
4. Çevresinde 1 metre boş alan olsun
```

### Adım 2: Script ile Dönüş Kalibrasyonu

```bash
# Menüden "2. Dönüş Kalibrasyonu" seç
# Kalibrasyon açısı: 90° (varsayılan)
# Robot sağa doğru 90° dönecek
```

### Adım 3: Açı Ölçümü

```
📐 Açı Ölçüm Yöntemleri:

1. **Rapportör Yöntemi:**
   - Başlangıç yönünü çiz
   - Robot dönüş sonrası yönünü çiz
   - Aralarındaki açıyı ölç

2. **Dijital Açı Ölçer:**
   - Robot'un üstüne yerleştir
   - Başlangıç değerini sıfırla
   - Dönüş sonrası değeri oku

3. **Referans Nokta Yöntemi:**
   - Duvara olan mesafeyi ölç
   - Trigonometrik hesaplama yap
```

### Adım 4: Sonuç Analizi

```
📊 Örnek Dönüş Kalibrasyon Sonuçları:

============================================================
🔄 DÖNÜŞ KALİBRASYON SONUÇLARI
============================================================
📐 Fiziksel Açı: 90.0°
🔢 Sol Encoder Pulse: 415
🔢 Sağ Encoder Pulse: -420
📏 Sol Mesafe: 0.117 m
📏 Sağ Mesafe: -0.118 m
📐 Mevcut Tekerlek Base: 0.235 m
📐 Gerçek Tekerlek Base: 0.238 m
⚠️  Hata: 1.3%
🔧 Kalibrasyon Faktörü: 1.013
============================================================
```

---

## 🧪 DOĞRULAMA TESTİ

### Test Prosedürü

```bash
# Menüden "4. Doğrulama Testi" seç
# Test mesafesi: 0.5m (varsayılan)

# Test süreci:
1. Robot belirlenen mesafe kadar hareket eder
2. Encoder'lardan mesafe hesaplanır
3. Fiziksel mesafe ölçülür
4. Hata hesaplanır
5. Başarı/başarısızlık değerlendirilir
```

### Başarı Kriterleri

```python
# Test sonucu değerlendirme
if hata_yuzdesi < 2:
    print("✅ Doğrulama başarılı! Kalibrasyon çok iyi.")
elif hata_yuzdesi < 5:
    print("⚠️ Doğrulama kabul edilebilir. Kalibrasyon yeterli.")
else:
    print("❌ Doğrulama başarısız! Kalibrasyon tekrar edilmeli.")
```

### Çoklu Test Önerisi

```bash
# Farklı mesafelerle test et
python scripts/encoder_calibration.py --test --distance 0.3
python scripts/encoder_calibration.py --test --distance 0.7
python scripts/encoder_calibration.py --test --distance 1.0

# Sonuçları karşılaştır
```

---

## 💾 KONFİGÜRASYON GÜNCELLEMESİ

### Otomatik Güncelleme

```bash
# Menüden "3. Konfigürasyon Güncelle" seç
# Script otomatik olarak:
1. Mevcut config dosyasının backup'ını alır
2. Yeni hesaplanan değerleri uygular
3. Dosyayı günceller
4. Değişiklikleri rapor eder
```

### Manuel Güncelleme

```yaml
# config/robot_config.yaml dosyasını düzenle
navigation:
  wheel_diameter: 0.066    # Kalibrasyon sonucu
  wheel_base: 0.238       # Dönüş kalibrasyonu sonucu

  # Kalibrasyon faktörleri (opsiyonel)
  calibration_factors:
    distance_factor: 0.994
    rotation_factor: 1.013
    last_calibration: "2025-07-09"
```

### Backup Sistemi

```bash
# Backup dosyaları
config/robot_config.yaml.backup     # Otomatik backup
config/robot_config.yaml.backup.1   # Önceki backup
config/robot_config.yaml.backup.2   # Daha önceki backup

# Geri yüklemek için
cp config/robot_config.yaml.backup config/robot_config.yaml
```

---

## 🔍 SORUN GİDERME

### Yaygın Sorunlar ve Çözümleri

#### 1. Encoder Sinyali Alınmıyor

```bash
# Symptom: Encoder pulse'ları 0 veya çok düşük
# Çözüm:
1. GPIO bağlantılarını kontrol et
2. Encoder güç beslemesini kontrol et
3. Interrupt konfigürasyonunu kontrol et

# Test komutu
python -c "
import RPi.GPIO as GPIO
import time
GPIO.setmode(GPIO.BCM)
GPIO.setup(19, GPIO.IN, pull_up_down=GPIO.PUD_UP)
print('GPIO 19 durumu:', GPIO.input(19))
GPIO.cleanup()
"
```

#### 2. Asymmetric Encoder Readings

```bash
# Symptom: Sol ve sağ encoder çok farklı değerler
# Çözüm:
1. Tekerlek çaplarını kontrol et
2. Motor bağlantılarını kontrol et
3. Encoder mounting'ini kontrol et
4. Tekerlek kayması olup olmadığını kontrol et
```

#### 3. Tutarsız Kalibrasyon Sonuçları

```bash
# Symptom: Her kalibrasyon farklı sonuç
# Çözüm:
1. Zemin düzlüğünü kontrol et
2. Tekerlek hizalamasını kontrol et
3. Batarya voltajını kontrol et
4. Aynı hızda test yap
5. Çoklu ölçüm al ve ortalama hesapla
```

#### 4. Yüksek Hata Oranları

```bash
# Symptom: %5'ten yüksek hata
# Çözüm:
1. Fiziksel ölçüm hassasiyetini arttır
2. Tekerlek çapını manuel ölç
3. Encoder PPR değerini kontrol et
4. Mekanik toleransları kontrol et
```

### Debug Modları

```bash
# Debug ile çalıştır
python scripts/encoder_calibration.py --interactive --debug

# Log seviyesini arttır
export PYTHONPATH=/workspaces/oba
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
# ... encoder calibration code
"
```

---

## 📊 PERFORMANS DEĞERLENDİRME

### Kalibrasyon Kalitesi Metrikleri

```python
# Kalite değerlendirme kriterleri
EXCELLENT = hata_yuzdesi < 1.0    # Mükemmel
GOOD = hata_yuzdesi < 2.0         # İyi
ACCEPTABLE = hata_yuzdesi < 5.0   # Kabul edilebilir
POOR = hata_yuzdesi >= 5.0        # Kötü - yeniden kalibre et
```

### Beklenen Performans

```
📈 Tipik Performans Değerleri:

🎯 Mesafe Kalibrasyonu:
- Mükemmel: ±0.5% hata
- İyi: ±1.0% hata
- Kabul edilebilir: ±2.0% hata

🎯 Dönüş Kalibrasyonu:
- Mükemmel: ±1.0% hata
- İyi: ±2.0% hata
- Kabul edilebilir: ±3.0% hata

🎯 Doğrulama Testi:
- Geçer: ±5.0% hata
- Başarısız: >±5.0% hata
```

### Kalibrasyon Sıklığı

```
📅 Kalibrasyon Takvimi:

🔄 İlk Kurulum: Tam kalibrasyon gerekli
🔄 Haftalık: Doğrulama testi
🔄 Aylık: Mesafe kalibrasyonu
🔄 3 Aylık: Tam kalibrasyon
🔄 Hardware değişikliği sonrası: Tam kalibrasyon
```

---

## 🚀 GELİŞMİŞ ÖZELLIKLER

### Otomatik Kalibrasyon

```python
# Gelecek özellik: Otomatik kalibrasyon
# Robot kendi kendini kalibre edecek
class AutoCalibrator:
    def __init__(self):
        self.reference_markers = []  # AprilTag'ler
        self.calibration_route = []  # Kalibrasyon rotası

    async def auto_calibrate(self):
        """Otomatik kalibrasyon yapar"""
        # 1. Bilinen mesafedeki AprilTag'leri tespit et
        # 2. Mesafe ölçümü yap
        # 3. Encoder okumalarını karşılaştır
        # 4. Otomatik düzeltme uygula
```

### Adaptif Kalibrasyon

```python
# Çalışma sırasında sürekli düzeltme
class AdaptiveCalibrator:
    def __init__(self):
        self.running_average = []
        self.drift_detector = DriftDetector()

    async def continuous_calibration(self):
        """Sürekli kalibrasyon düzeltmesi"""
        # GPS ve encoder verilerini karşılaştır
        # Drift tespit et
        # Mikro düzeltmeler uygula
```

### Çoklu Sensor Fusion

```python
# Encoder + GPS + IMU kalibrasyonu
class MultiSensorCalibrator:
    def __init__(self):
        self.encoder_data = []
        self.gps_data = []
        self.imu_data = []

    async def fused_calibration(self):
        """Çoklu sensör kalibrasyonu"""
        # Tüm sensör verilerini kullan
        # Optimal kalibrasyon hesapla
        # Noise filtreleme uygula
```

---

## 📋 KONTROL LİSTESİ

### Kalibrasyon Öncesi Kontrol

```
✅ Kontrol Listesi:

🔧 Hardware:
[ ] Encoder'lar doğru bağlı
[ ] GPIO pinleri doğru
[ ] Güç beslemesi stabil
[ ] Tekerlekler sıkı
[ ] Zemin düz ve temiz

💻 Software:
[ ] Script çalıştırılabilir
[ ] Config dosyası mevcut
[ ] Backup alındı
[ ] Test environment hazır
[ ] Debug logging aktif

🎯 Ortam:
[ ] Yeterli çalışma alanı
[ ] Ölçüm araçları hazır
[ ] Referans noktaları belirlendi
[ ] Dış etkiler minimized
[ ] Güvenlik önlemleri alındı
```

### Kalibrasyon Sonrası Kontrol

```
✅ Sonuç Kontrolü:

📊 Kalibrasyon:
[ ] Hata oranı kabul edilebilir
[ ] Sonuçlar tutarlı
[ ] Config güncellendi
[ ] Backup alındı
[ ] Doğrulama testi geçti

🧪 Test:
[ ] Mesafe testi başarılı
[ ] Dönüş testi başarılı
[ ] Çoklu test yapıldı
[ ] Performans kaydedildi
[ ] Dokümantasyon güncellendi
```

---

## 📝 SONUÇ

Encoder kalibrasyonu, robot navigasyonunun temelini oluşturan kritik bir süreçtir. Bu rehber ile:

- ✅ Hassas mesafe ölçümü elde edebilirsiniz
- ✅ Doğru açısal hareket sağlayabilirsiniz
- ✅ Navigasyon kalitesini artırabilirsiniz
- ✅ Sistematik kalibrasyon yapabilirsiniz

**Unutmayın:** İyi bir kalibrasyon, iyi bir robot performansının anahtarıdır!

---

## 🔗 İLGİLİ BELGELER

- [Kamera Kalibrasyon Rehberi](camera_calibration_guide.md)
- [Hardware Kurulum Rehberi](../hardware/assembly_guide.md)
- [Raspberry Pi Setup](../deployment/raspberry_pi_setup.md)
- [Troubleshooting Guide](../troubleshooting.md)

---

**Son Güncelleme:** 2025-07-09
**Versiyon:** 1.0
**Yazar:** Hacı Abi 🤖
