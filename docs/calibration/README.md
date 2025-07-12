# 🔧 Kalibrasyon Rehberi - Ana Sayfa
# Otonom Bahçe Asistanı (OBA) - Kalibrasyon Dokümantasyonu

## 📋 KALIBRASYON SİSTEMİNE GENEL BAKIŞ

### Neden Kalibrasyon Gerekli?

Robot'un doğru çalışması için tüm sensörlerinin ve sistemlerinin kalibre edilmesi gerekir. Kalibrasyon olmadan:

- ❌ Robot hedefine varamaz
- ❌ Mesafe ölçümleri hatalı olur
- ❌ Şarj istasyonuna yaklaşamaz
- ❌ Navigasyon sistemi çalışmaz

### Kalibrasyon Türleri

```
🎯 Ana Kalibrasyon Sistemleri:

📏 Encoder Kalibrasyonu
├── Mesafe kalibrasyonu
├── Dönüş kalibrasyonu
└── Doğrulama testleri

📷 Kamera Kalibrasyonu
├── Lens distorsiyon düzeltmesi
├── AprilTag optimizasyonu
└── Görüntü işleme iyileştirmesi

🧭 IMU Kalibrasyonu (Gelecek)
├── Gyroscope kalibrasyonu
├── Accelerometer kalibrasyonu
└── Magnetometer kalibrasyonu

🛰️ GPS Kalibrasyonu (Gelecek)
├── Referans noktası belirleme
├── Offset düzeltmesi
└── Doğruluk optimizasyonu
```

---

## 🚀 HIZLI BAŞLANGIÇ

### Tam Kalibrasyon Süreci

```bash
# 1. Encoder kalibrasyonu
python scripts/encoder_calibration.py --interactive

# 2. Kamera kalibrasyonu
python scripts/camera_calibration.py --tam

# 3. Sistem doğrulama
python main.py --test-calibration
```

### Kalibrasyon Sırası

```
📋 Önerilen Kalibrasyon Sırası:

1️⃣ Encoder Kalibrasyonu (Temel hareket)
   ├── Mesafe kalibrasyonu
   ├── Dönüş kalibrasyonu
   └── Doğrulama testi

2️⃣ Kamera Kalibrasyonu (Görüntü işleme)
   ├── Chessboard görüntü toplama
   ├── Kalibrasyon hesaplama
   └── AprilTag testi

3️⃣ Sistem Entegrasyonu
   ├── Config güncelleme
   ├── Çapraz doğrulama
   └── Performans testi
```

---

## 📏 ENCODER KALİBRASYONU

### Temel Bilgiler

Encoder kalibrasyonu, robot'un tekerlek hareketlerini doğru mesafe ve açı değerlerine dönüştürme sürecidir.

```yaml
# Encoder konfigürasyonu
hardware:
  sensors:
    encoders:
      sol_encoder:
        pulses_per_revolution: 360
      sag_encoder:
        pulses_per_revolution: 360

navigation:
  wheel_diameter: 0.065    # Kalibre edilecek
  wheel_base: 0.235       # Kalibre edilecek
```

### Hızlı Kullanım

```bash
# İnteraktif kalibrasyon
python scripts/encoder_calibration.py --interactive

# Menü seçenekleri:
# 1. Mesafe Kalibrasyonu
# 2. Dönüş Kalibrasyonu
# 3. Konfigürasyon Güncelle
# 4. Doğrulama Testi
```

### Beklenen Sonuçlar

```
📊 Başarılı Encoder Kalibrasyonu:

✅ Mesafe Hatası: < %2
✅ Dönüş Hatası: < %3
✅ Doğrulama: Geçti
✅ Config: Güncellendi
```

👉 **Detaylı Bilgi:** [Encoder Kalibrasyon Rehberi](encoder_calibration_guide.md)

---

## 📷 KAMERA KALİBRASYONU

### Temel Bilgiler

Kamera kalibrasyonu, lens distorsiyonunu düzeltme ve AprilTag tespit performansını optimize etme sürecidir.

```yaml
# Kamera konfigürasyonu
apriltag:
  kamera_matrix:          # Kalibre edilecek
    - [fx, 0, cx]
    - [0, fy, cy]
    - [0, 0, 1]
  distortion_coeffs: []   # Kalibre edilecek
```

### Hızlı Kullanım

```bash
# Tam kalibrasyon süreci
python scripts/camera_calibration.py --tam

# Aşamalar:
# 1. Chessboard görüntü toplama
# 2. Kalibrasyon hesaplama
# 3. AprilTag testi
```

### Beklenen Sonuçlar

```
📊 Başarılı Kamera Kalibrasyonu:

✅ Reprojection Error: < 0.5 piksel
✅ AprilTag Tespit: > %90
✅ Mesafe Hatası: < 5cm
✅ Config: Güncellendi
```

👉 **Detaylı Bilgi:** [Kamera Kalibrasyon Rehberi](camera_calibration_guide.md)

---

## 🛠️ KALIBRASYON ARAÇLARI

### Mevcut Scriptler

```bash
# Encoder kalibrasyon scripti
/workspaces/oba/scripts/encoder_calibration.py
├── İnteraktif mod
├── Mesafe kalibrasyonu
├── Dönüş kalibrasyonu
├── Doğrulama testi
└── Config güncelleme

# Kamera kalibrasyon scripti
/workspaces/oba/scripts/camera_calibration.py
├── Görüntü toplama
├── Kalibrasyon hesaplama
├── AprilTag testi
└── Sonuç kaydetme
```

### Yardımcı Araçlar

```bash
# Test scriptleri
python test_apriltag_system.py --live-test
python test_navigation.py --encoder-test
python test_hardware.py --calibration-check

# Debugging araçları
python -m src.hardware.motor_kontrolcu --test
python -m src.vision.kamera_islemci --test
```

---

## 📊 KALIBRASYON DURUMU

### Durum Kontrol Komutları

```bash
# Genel durum kontrolü
oba-status

# Kalibrasyon durumu
python -c "
import yaml
with open('config/robot_config.yaml', 'r') as f:
    config = yaml.safe_load(f)

print('📏 Encoder Durumu:')
print(f'  Tekerlek Çapı: {config[\"navigation\"][\"wheel_diameter\"]}m')
print(f'  Tekerlek Base: {config[\"navigation\"][\"wheel_base\"]}m')

print('📷 Kamera Durumu:')
apriltag = config.get('apriltag', {})
if apriltag.get('kamera_matrix'):
    print('  ✅ Kamera matrix mevcut')
else:
    print('  ❌ Kamera matrix eksik')

if apriltag.get('distortion_coeffs'):
    print('  ✅ Distortion coeffs mevcut')
else:
    print('  ❌ Distortion coeffs eksik')
"
```

### Kalibrasyon Geçmişi

```bash
# Kalibrasyon logları
ls -la config/*.backup
tail -n 20 logs/calibration.log

# Son değişiklikler
git log --oneline config/robot_config.yaml
```

---

## 🧪 DOĞRULAMA TESTLERİ

### Encoder Doğrulama

```bash
# Mesafe doğrulama
python scripts/encoder_calibration.py --test

# Çoklu mesafe testi
for distance in 0.3 0.5 0.7 1.0; do
    echo "Test mesafesi: ${distance}m"
    python scripts/encoder_calibration.py --test --distance $distance
done
```

### Kamera Doğrulama

```bash
# AprilTag tespit testi
python scripts/camera_calibration.py --test

# Mesafe doğrulama
python test_apriltag_system.py --distance-test
```

### Sistem Entegrasyonu Testi

```bash
# Tam sistem testi
python main.py --test-navigation

# Şarj yaklaşım testi
python main.py --test-charging-approach
```

---

## 🔍 SORUN GİDERME

### Yaygın Sorunlar

#### 1. Encoder Kalibrasyonu Başarısız

```
❌ Semptom: Yüksek hata oranları
🔧 Çözüm:
  - Zemin düzlüğünü kontrol et
  - Tekerlek hizalamasını kontrol et
  - Fiziksel ölçüm hassasiyetini arttır
  - Çoklu ölçüm al
```

#### 2. Kamera Kalibrasyonu Başarısız

```
❌ Semptom: Chessboard tespit edilmiyor
🔧 Çözüm:
  - Pattern kalitesini kontrol et
  - Aydınlatmayı iyileştir
  - Kamera focus'unu ayarla
  - Farklı açılardan görüntü al
```

#### 3. AprilTag Tespit Edilmiyor

```
❌ Semptom: AprilTag test başarısız
🔧 Çözüm:
  - Kalibrasyon sonuçlarını kontrol et
  - AprilTag boyutunu doğrula
  - Aydınlatma koşullarını kontrol et
  - Config güncellemesini kontrol et
```

### Debug Komutları

```bash
# Encoder debug
python -c "
from src.hardware.motor_kontrolcu import MotorKontrolcu
import asyncio

async def test():
    motor = MotorKontrolcu({})
    print('Encoder verileri:', motor.get_enkoder_verileri())

asyncio.run(test())
"

# Kamera debug
python -c "
import cv2
cap = cv2.VideoCapture(0)
ret, frame = cap.read()
print('Kamera durumu:', ret)
print('Frame boyutu:', frame.shape if ret else 'Yok')
cap.release()
"
```

---

## 📅 KALIBRASYON TAKVIMI

### Kalibrasyon Sıklığı

```
📅 Önerilen Kalibrasyon Takvimi:

🔄 İlk Kurulum:
  - Tam encoder kalibrasyonu
  - Tam kamera kalibrasyonu
  - Sistem entegrasyonu testi

🔄 Haftalık Kontrol:
  - Encoder doğrulama testi
  - AprilTag tespit testi
  - Genel sistem kontrolü

🔄 Aylık Bakım:
  - Encoder hassasiyet kontrolü
  - Kamera lens temizliği
  - Kalibrasyon sonuçları analizi

🔄 Üç Aylık Bakım:
  - Tam encoder kalibrasyonu
  - Kamera kalibrasyon kontrolü
  - Sistem performans analizi

🔄 Hardware Değişikliği Sonrası:
  - İlgili sistemin tam kalibrasyonu
  - Entegrasyon testleri
  - Performans karşılaştırması
```

### Kalibrasyon Kaydı

```bash
# Kalibrasyon kaydı tutma
echo "$(date): Encoder kalibrasyonu tamamlandı" >> logs/calibration_history.log
echo "$(date): Kamera kalibrasyonu tamamlandı" >> logs/calibration_history.log

# Kalibrasyon geçmişi görüntüleme
cat logs/calibration_history.log | tail -n 10
```

---

## 🎯 PERFORMANS OPTİMİZASYONU

### Hedef Performans Değerleri

```
📈 Target Performance Metrics:

🎯 Encoder Performansı:
  - Mesafe hatası: < %1
  - Dönüş hatası: < %2
  - Tekrarlanabilirlik: > %95
  - Kararlılık: Yüksek

🎯 Kamera Performansı:
  - Reprojection error: < 0.3 piksel
  - AprilTag tespit: > %95
  - Mesafe hatası: < 3cm
  - İşlem süresi: < 50ms

🎯 Sistem Performansı:
  - Navigasyon hatası: < 5cm
  - Şarj yaklaşım başarısı: > %98
  - Genel güvenilirlik: > %99
```

### Optimizasyon Teknikleri

```python
# Encoder optimizasyonu
ENCODER_OPTIMIZATION = {
    'sampling_rate': 100,        # Hz
    'filter_type': 'kalman',     # Noise filtreleme
    'averaging_window': 5,       # Hareketli ortalama
    'outlier_rejection': True    # Outlier filtreleme
}

# Kamera optimizasyonu
CAMERA_OPTIMIZATION = {
    'resolution': (640, 480),    # Optimal çözünürlük
    'fps': 15,                   # Kararlı FPS
    'buffer_size': 1,            # Düşük latency
    'auto_exposure': True        # Otomatik exposure
}
```

---

## 📚 EK KAYNAKLAR

### Referans Belgeler

- [OpenCV Camera Calibration](https://docs.opencv.org/master/dc/dbb/tutorial_py_calibration.html)
- [AprilTag Documentation](https://april.eecs.umich.edu/software/apriltag)
- [ROS Navigation Tuning](http://wiki.ros.org/navigation/Tutorials/Navigation%20Tuning%20Guide)

### Videolar ve Tutorials

```bash
# Kalibrasyon videoları (gelecek)
docs/videos/
├── encoder_calibration_tutorial.mp4
├── camera_calibration_tutorial.mp4
└── troubleshooting_guide.mp4
```

### Topluluk Desteği

```bash
# GitHub Issues
https://github.com/[user]/oba/issues

# Wiki sayfaları
https://github.com/[user]/oba/wiki

# Discussions
https://github.com/[user]/oba/discussions
```

---

## 📋 KONTROL LİSTESİ

### Kalibrasyon Tamamlandı Kontrolü

```
✅ Kalibrasyon Tamamlanma Kontrol Listesi:

🔧 Encoder Kalibrasyonu:
[ ] Mesafe kalibrasyonu yapıldı (hata < %2)
[ ] Dönüş kalibrasyonu yapıldı (hata < %3)
[ ] Doğrulama testi geçti
[ ] Config dosyası güncellendi
[ ] Backup alındı

📷 Kamera Kalibrasyonu:
[ ] Chessboard görüntüleri toplandı (20+)
[ ] Kalibrasyon hesaplandı (error < 0.5 piksel)
[ ] AprilTag testi geçti (tespit > %90)
[ ] Config dosyası güncellendi
[ ] Backup alındı

🧪 Sistem Testleri:
[ ] Encoder doğrulama testi geçti
[ ] Kamera doğrulama testi geçti
[ ] Sistem entegrasyonu testi geçti
[ ] Performans testleri geçti
[ ] Dokümantasyon güncellendi

🚀 Production Hazırlığı:
[ ] Tüm testler geçti
[ ] Konfigürasyon stabil
[ ] Performance benchmark'lar karşılandı
[ ] Monitoring kuruldu
[ ] Backup stratejisi hazır
```

---

## 🎉 SONUÇ

Bu kapsamlı kalibrasyon rehberi ile OBA robot'un tüm sistemlerini doğru bir şekilde kalibre edebilirsiniz. Kalibrasyon, robot performansının temel taşıdır ve düzenli bakım gerektirir.

**Unutmayın:** İyi kalibrasyon = İyi robot performansı!

---

## 🔗 HIZLI ERİŞİM

- 📏 [Encoder Kalibrasyon Rehberi](encoder_calibration_guide.md)
- 📷 [Kamera Kalibrasyon Rehberi](camera_calibration_guide.md)
- 🏷️ [AprilTag Yerleştirme Rehberi](../apriltag_placement_guide.md)
- 🔧 [Hardware Kurulum Rehberi](../hardware/assembly_guide.md)
- 🍓 [Raspberry Pi Setup](../deployment/raspberry_pi_setup.md)

---

**Son Güncelleme:** 2025-07-09
**Versiyon:** 1.0
**Yazar:** Hacı Abi 🤖
