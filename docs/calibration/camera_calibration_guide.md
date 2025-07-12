# 📷 Kamera Kalibrasyon Rehberi
# Otonom Bahçe Asistanı (OBA) - Kamera Kalibrasyon Dokümantasyonu

## 📋 GİRİŞ

### Kamera Kalibrasyonu Nedir?

Kamera kalibrasyonu, robot'un kamerasının lens distorsiyonunu ve içsel parametrelerini belirleme sürecidir. Bu süreç AprilTag detection ve navigasyon için kritik öneme sahiptir.

Kalibrasyon olmadan:
- ❌ AprilTag'ler yanlış tespit edilir
- ❌ Mesafe ölçümleri hatalı olur
- ❌ Şarj istasyonuna yaklaşım başarısız olur
- ❌ Görüntü işleme performansı düşer

### Kamera Kalibrasyon Çıktıları

```python
# Kalibrasyon sonuçları
camera_matrix = [
    [fx,  0, cx],    # Focal length X, Center X
    [ 0, fy, cy],    # Focal length Y, Center Y
    [ 0,  0,  1]     # Homogeneous coordinate
]

distortion_coeffs = [k1, k2, p1, p2, k3]  # Distortion coefficients

# k1, k2, k3: Radial distortion
# p1, p2: Tangential distortion
```

---

## 🎯 KAMERA SİSTEMİ ANALİZİ

### Hardware Konfigürasyonu

```yaml
# config/robot_config.yaml
hardware:
  sensors:
    camera:
      port: 0                    # Kamera portu
      resolution: [640, 480]     # Çözünürlük
      framerate: 30              # FPS

apriltag:
  detection_params:
    families: 'tag36h11'         # AprilTag ailesi
    nthreads: 4                  # Thread sayısı
    quad_decimate: 2.0           # Quad decimation
    quad_sigma: 0.0              # Quad sigma
    decode_sharpening: 0.25      # Decode sharpening

  # Kalibrasyon sonuçları (buraya yazılacak)
  kamera_matrix: []
  distortion_coeffs: []
```

### Kamera Özellikleri

```python
# Raspberry Pi Camera v2 özellikleri
CAMERA_SPECS = {
    'sensor': 'Sony IMX219',
    'resolution': '8MP (3280x2464)',
    'video_resolution': '1080p30, 720p60, 640x480p90',
    'field_of_view': '62.2° x 48.8°',
    'focal_length': '3.04mm',
    'aperture': 'f/2.0',
    'focus': 'Fixed focus (1m to infinity)'
}
```

---

## 📷 KAMERA KALİBRASYON SCRIPTI

### Script Özellikleri

```bash
# Script konumu
/workspaces/oba/scripts/camera_calibration.py

# Temel kullanım
python scripts/camera_calibration.py --tam

# Komut satırı seçenekleri
--topla           # Kalibrasyon görüntülerini topla
--kalibrasyon     # Kalibrasyonu yap
--test            # AprilTag testi yap
--tam             # Tam işlem (topla + kalibrasyon + test)
--klasor KLASOR   # Görüntü klasörü
```

### Script Mimarisi

```python
class KameraKalibratoru:
    """Kamera kalibrasyon sınıfı"""

    def __init__(self, satranc_boyutu: Tuple[int, int] = (9, 6)):
        """
        Args:
            satranc_boyutu: Chessboard boyutu (corner count)
        """

    def kalibrasyon_goruntusu_topla(self, kaynak: str = "kamera"):
        """Kalibrasyon görüntülerini toplar"""

    def kalibrasyon_yap(self, goruntu_klasoru: str):
        """Kamera kalibrasyonu yapar"""

    def apriltag_test_et(self, kalibrasyon_sonucu: dict):
        """AprilTag ile testi yapar"""

    def sonuclari_kaydet(self, kalibrasyon_sonucu: dict):
        """Sonuçları kaydeder"""
```

---

## 🎯 KALIBRASYON PATTERN'İ

### Chessboard Pattern

Kamera kalibrasyonu için standart olarak chessboard (satranç tahtası) pattern'i kullanılır:

```
📐 Chessboard Özellikleri:

🔲 Boyut: 9x6 iç köşe (10x7 kare)
🔲 Kare boyutu: 25mm x 25mm
🔲 Toplam boyut: 250mm x 175mm (A4 kağıda sığar)
🔲 Renk: Siyah-beyaz alternatif
🔲 Kalite: Yüksek çözünürlük, net kenarlar
```

### Pattern Yazdırma

```bash
# Pattern dosyası indirme
wget https://raw.githubusercontent.com/opencv/opencv/master/doc/pattern.png

# Veya OpenCV ile oluşturma
python -c "
import cv2
import numpy as np

# 9x6 chessboard oluştur
board_size = (9, 6)
square_size = 25  # mm

# Chessboard görüntüsü oluştur
board = np.zeros((board_size[1]*square_size, board_size[0]*square_size), dtype=np.uint8)
for i in range(board_size[1]):
    for j in range(board_size[0]):
        if (i + j) % 2 == 0:
            board[i*square_size:(i+1)*square_size, j*square_size:(j+1)*square_size] = 255

cv2.imwrite('chessboard_pattern.png', board)
print('Chessboard pattern kaydedildi: chessboard_pattern.png')
"
```

### Yazdırma Ayarları

```
🖨️ Yazdırma Gereksinimleri:

📄 Kağıt: A4 beyaz kağıt (en az 80gr)
🖨️ Yazıcı: Laser yazıcı (daha keskin)
🎯 Ayarlar:
  - Gerçek boyut (100% scale)
  - Yüksek kalite
  - Renk: Siyah-beyaz
  - Çerçeve yok

⚠️ DİKKAT: Boyut doğruluğu kritik!
```

---

## 📸 KALIBRASYON GÖRÜNTÜ TOPLAMA

### Adım 1: Hazırlık

```bash
# Gerekli malzemeler
- Chessboard pattern (yazdırılmış)
- Düz tabla/karton (pattern'i düzleştirmek için)
- İyi aydınlatma
- Sabit kamera pozisyonu
- Temiz kamera lensi

# Ortam hazırlığı
1. Kamerayı sabit pozisyona kur
2. Düzgün aydınlatma sağla (gölge yok)
3. Pattern'i düz yüzeye yapıştır
4. Çalışma alanını temizle
```

### Adım 2: Görüntü Toplama

```bash
# Script'i görüntü toplama modunda çalıştır
python scripts/camera_calibration.py --topla

# Kontroller
📋 KULLANIM:
  - SPACE: Görüntü kaydet
  - ESC: Çıkış
  - En az 20 farklı açıdan görüntü alın
```

### Adım 3: Pattern Pozisyonları

```
📐 Gerekli Pattern Pozisyonları:

🎯 Temel Pozisyonlar (Minimum):
1. Merkez - düz bakış
2. Sol üst köşe
3. Sağ üst köşe
4. Sol alt köşe
5. Sağ alt köşe

🎯 Ek Pozisyonlar (Kalite için):
6. Merkez - yakın mesafe
7. Merkez - uzak mesafe
8. 45° açıyla sol
9. 45° açıyla sağ
10. 30° açıyla yukarı
11. 30° açıyla aşağı
12. Çapraz pozisyonlar

🎯 İleri Seviye (Mükemmel için):
13-20. Farklı açı kombinasyonları
```

### Adım 4: Görüntü Kalite Kontrolü

```python
# Kalite kontrol kriterleri
QUALITY_CRITERIA = {
    'pattern_detection': True,      # Pattern tespit edildi
    'corner_count': 54,             # 9x6 = 54 köşe
    'sharpness': 'high',            # Keskinlik yüksek
    'lighting': 'uniform',          # Düzgün aydınlatma
    'distortion': 'minimal',        # Minimal distorsiyon
    'coverage': 'full_frame'        # Tam frame coverage
}
```

---

## 🔬 KALIBRASYON HESAPLAMALARI

### Adım 1: Kalibrasyon Başlatma

```bash
# Kalibrasyon işlemini başlat
python scripts/camera_calibration.py --kalibrasyon

# Veya tam işlem
python scripts/camera_calibration.py --tam
```

### Adım 2: Görüntü İşleme

```python
# Kalibrasyon süreci
def kalibrasyon_yap(self, goruntu_klasoru: str):
    """Kalibrasyon algoritması"""

    # 1. Görüntüleri yükle
    images = glob.glob(os.path.join(goruntu_klasoru, "*.jpg"))

    # 2. Her görüntüde chessboard köşelerini bul
    for image_path in images:
        img = cv2.imread(image_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Chessboard köşelerini tespit et
        ret, corners = cv2.findChessboardCorners(gray, self.satranc_boyutu)

        if ret:
            # Köşe hassasiyetini arttır
            corners2 = cv2.cornerSubPix(gray, corners, (11,11), (-1,-1), criteria)

            # 3D ve 2D noktaları kaydet
            self.objpoints.append(self.objp)
            self.imgpoints.append(corners2)

    # 3. Kalibrasyon hesapla
    ret, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
        self.objpoints, self.imgpoints, gray.shape[::-1], None, None
    )

    return camera_matrix, dist_coeffs
```

### Adım 3: Hata Analizi

```python
def _kalibrasyon_hatasi_hesapla(self, camera_matrix, dist_coeffs, rvecs, tvecs):
    """Reprojection error hesapla"""

    total_error = 0
    total_points = 0

    for i in range(len(self.objpoints)):
        # 3D noktaları 2D'ye project et
        imgpoints2, _ = cv2.projectPoints(
            self.objpoints[i], rvecs[i], tvecs[i],
            camera_matrix, dist_coeffs
        )

        # Gerçek ve hesaplanan noktalar arasındaki hata
        error = cv2.norm(self.imgpoints[i], imgpoints2, cv2.NORM_L2)
        total_error += error / len(imgpoints2)
        total_points += 1

    return total_error / total_points
```

### Adım 4: Sonuç Değerlendirme

```
📊 Örnek Kalibrasyon Sonuçları:

✅ Kalibrasyon tamamlandı!
📊 Ortalama hata: 0.245 piksel
📷 Görüntü boyutu: (640, 480)
📈 Başarılı görüntü: 18/20

🔢 Camera Matrix:
[[525.6  0.0  320.3]
 [  0.0 526.1 240.7]
 [  0.0   0.0   1.0]]

🔢 Distortion Coefficients:
[-0.123, 0.089, -0.001, 0.002, -0.045]
```

---

## 💾 SONUÇ KAYDETME

### Otomatik Kaydetme

```python
def sonuclari_kaydet(self, kalibrasyon_sonucu: dict):
    """Kalibrasyon sonuçlarını kaydet"""

    # 1. Pickle formatında kaydet
    with open("kamera_kalibrasyon.pkl", 'wb') as f:
        pickle.dump(kalibrasyon_sonucu, f)

    # 2. YAML formatında kaydet
    self._yaml_formatinda_kaydet(kalibrasyon_sonucu, "kamera_kalibrasyon.yaml")

    # 3. Robot config'e entegre et
    self._config_guncelle(kalibrasyon_sonucu)
```

### YAML Formatı

```yaml
# kamera_kalibrasyon.yaml
# Bu değerleri robot_config.yaml dosyasına kopyalayın

apriltag:
  kamera_matrix:
    - [525.6, 0.0, 320.3]
    - [0.0, 526.1, 240.7]
    - [0.0, 0.0, 1.0]
  distortion_coeffs: [-0.123, 0.089, -0.001, 0.002, -0.045]

# Kalibrasyon Bilgileri:
# Ortalama hata: 0.245 piksel
# Başarılı görüntü: 18
# Görüntü boyutu: [640, 480]
# Kalibrasyon tarihi: 2025-07-09
```

### Robot Config Güncellemesi

```bash
# Manuel güncelleme
cp kamera_kalibrasyon.yaml config/robot_config.yaml

# Veya otomatik entegrasyon
python -c "
import yaml

# Kalibrasyon sonuçlarını yükle
with open('kamera_kalibrasyon.yaml', 'r') as f:
    calib_data = yaml.safe_load(f)

# Robot config'i güncelle
with open('config/robot_config.yaml', 'r') as f:
    robot_config = yaml.safe_load(f)

robot_config['apriltag'].update(calib_data['apriltag'])

# Güncellenmiş config'i kaydet
with open('config/robot_config.yaml', 'w') as f:
    yaml.dump(robot_config, f, default_flow_style=False)

print('Robot config güncellendi!')
"
```

---

## 🏷️ APRILTAG TEST SİSTEMİ

### Test Başlatma

```bash
# AprilTag test modunu başlat
python scripts/camera_calibration.py --test

# Kontroller
📋 KULLANIM:
  - ESC: Çıkış
  - AprilTag (ID: 0-10) gösterin
  - Farklı mesafe ve açılardan test edin
```

### Test Kriterleri

```python
# AprilTag tespit kriterleri
APRILTAG_TEST_CRITERIA = {
    'detection_range': {
        'min_distance': 0.1,      # 10cm
        'max_distance': 3.0,      # 3m
        'optimal_distance': 0.5   # 50cm
    },
    'angle_tolerance': {
        'max_angle': 60,          # ±60°
        'optimal_angle': 30       # ±30°
    },
    'accuracy': {
        'position_error': 0.02,   # 2cm
        'angle_error': 5,         # 5°
        'distance_error': 0.05    # 5cm
    }
}
```

### Test Sonuçları

```
🏷️ AprilTag Test Sonuçları:

✅ Tespit Başarılı:
📏 Mesafe: 0.47m (±0.02m)
📐 Açı: 15.3° (±2.1°)
🎯 ID: 0 (Şarj İstasyonu)
⚡ FPS: 12.5
🔍 Güvenilirlik: 95%

📊 Performans Metrikleri:
- Tespit oranı: 18/20 (90%)
- Ortalama hata: 0.018m
- Işlem süresi: 45ms/frame
- Kararlılık: İyi
```

---

## 🔍 SORUN GİDERME

### Yaygın Sorunlar

#### 1. Chessboard Pattern Tespit Edilmiyor

```bash
# Symptom: "❌ Başarısız: kalibrasyon_xxx.jpg"
# Çözümler:

🔍 Görüntü Kalitesi:
- Keskinlik yeterli mi?
- Aydınlatma düzgün mü?
- Gölge var mı?
- Pattern düz mü?

🔍 Pattern Problemi:
- Boyut doğru mu? (9x6 corner)
- Yazdırma kalitesi iyi mi?
- Kırışık/bükülmüş mü?
- Kontrast yeterli mi?

🔍 Kamera Problemi:
- Focus doğru mu?
- Lens temiz mi?
- Çözünürlük uygun mu?
- Expo süre doğru mu?
```

#### 2. Yüksek Kalibrasyon Hatası

```bash
# Symptom: Ortalama hata > 0.5 piksel
# Çözümler:

🎯 Görüntü Kalitesi Arttırma:
- Daha fazla görüntü topla (30+)
- Farklı açılardan görüntü al
- Daha iyi aydınlatma kullan
- Kamera sabitliğini arttır

🎯 Pattern Kalitesi:
- Daha kaliteli yazdırma
- Düz yüzey kullan
- Boyut doğruluğunu kontrol et
- Yeni pattern yazdır
```

#### 3. AprilTag Tespit Edilmiyor

```bash
# Symptom: AprilTag test modunda tespit yok
# Çözümler:

🏷️ AprilTag Kontrolleri:
- ID doğru mu? (0-10 arası)
- Boyut uygun mu? (15cm)
- Yazdırma kalitesi iyi mi?
- Aydınlatma yeterli mi?

🏷️ Kalibrasyon Kontrolleri:
- Distortion coefficients doğru mu?
- Camera matrix makul mu?
- Kalibrasyon hatası düşük mü?
- Config dosyası güncel mi?
```

#### 4. Mesafe Ölçüm Hatası

```bash
# Symptom: AprilTag mesafe ölçümü yanlış
# Çözümler:

📏 Kalibrasyon Doğruluğu:
- Chessboard boyutunu doğrula
- Fiziksel ölçüm doğru mu?
- Kamera matrix değerleri makul mi?
- Distortion correction aktif mi?

📏 AprilTag Boyutu:
- Gerçek boyut 15cm mi?
- Yazdırma scale doğru mu?
- Code'da boyut doğru mu?
```

### Debug Komutları

```bash
# Kamera testi
python -c "
import cv2
cap = cv2.VideoCapture(0)
ret, frame = cap.read()
if ret:
    cv2.imwrite('camera_test.jpg', frame)
    print('Kamera çalışıyor')
else:
    print('Kamera hatası')
cap.release()
"

# Chessboard tespit testi
python -c "
import cv2
import numpy as np

img = cv2.imread('kalibrasyon_000.jpg')
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
ret, corners = cv2.findChessboardCorners(gray, (9,6))
print(f'Chessboard tespit: {ret}')
if ret:
    print(f'Köşe sayısı: {len(corners)}')
"

# AprilTag tespit testi
python -c "
import cv2
import numpy as np

# ArUco detector
aruco_dict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_APRILTAG_36h11)
detector_params = cv2.aruco.DetectorParameters_create()

img = cv2.imread('apriltag_test.jpg')
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
corners, ids, _ = cv2.aruco.detectMarkers(gray, aruco_dict, parameters=detector_params)

print(f'AprilTag tespit: {ids is not None}')
if ids is not None:
    print(f'Tespit edilen ID\'ler: {ids.flatten()}')
"
```

---

## 📊 PERFORMANS OPTİMİZASYONU

### Kamera Ayarları

```python
# Optimal kamera ayarları
CAMERA_SETTINGS = {
    'resolution': (640, 480),    # Hız için düşük çözünürlük
    'fps': 15,                   # Kararlı tespit için
    'exposure': 'auto',          # Otomatik exposure
    'white_balance': 'auto',     # Otomatik white balance
    'focus': 'manual',           # Manuel focus (infinity)
    'brightness': 50,            # Orta brightness
    'contrast': 50,              # Orta contrast
    'saturation': 50             # Orta saturation
}
```

### AprilTag Parametreleri

```python
# Optimal AprilTag parametreleri
APRILTAG_PARAMS = {
    'families': 'tag36h11',      # Yüksek güvenilirlik
    'nthreads': 4,               # Çok thread
    'quad_decimate': 2.0,        # Hız optimizasyonu
    'quad_sigma': 0.0,           # Noise filtreleme
    'refine_edges': True,        # Kenar iyileştirme
    'decode_sharpening': 0.25,   # Keskinlik
    'debug': False               # Debug kapalı
}
```

### Performans Metrikleri

```
📈 Target Performance:

🎯 Tespit Performansı:
- Tespit oranı: >90%
- Tespit süresi: <50ms
- FPS: >10
- Güvenilirlik: >95%

🎯 Hassasiyet:
- Mesafe hatası: <5cm
- Açı hatası: <5°
- Pozisyon hatası: <2cm
- Kararlılık: İyi (±2cm)

🎯 Çalışma Koşulları:
- Mesafe aralığı: 0.1-3.0m
- Açı toleransı: ±60°
- Aydınlatma: 200-2000 lux
- Çevre koşulları: İç/dış mekan
```

---

## 🚀 GELİŞMİŞ ÖZELLIKLER

### Otomatik Kalibrasyon

```python
# Gelecek özellik: Otomatik kalibrasyon
class AutoCameraCalibrator:
    def __init__(self):
        self.reference_patterns = []
        self.calibration_images = []

    async def auto_calibrate(self):
        """Otomatik kamera kalibrasyonu"""
        # 1. Bilinen pattern'leri tespit et
        # 2. Otomatik görüntü toplama
        # 3. Kalibrasyon hesaplama
        # 4. Sonuçları uygula
```

### Gerçek Zamanlı Kalibrasyon

```python
# Sürekli kalibrasyon düzeltmesi
class RealTimeCalibrator:
    def __init__(self):
        self.calibration_buffer = []
        self.drift_detector = DriftDetector()

    async def continuous_calibration(self):
        """Sürekli kalibrasyon güncelleme"""
        # AprilTag ile sürekli doğrulama
        # Drift tespit etme
        # Mikro düzeltmeler
```

### Çoklu Kamera Desteği

```python
# Çoklu kamera kalibrasyonu
class MultiCameraCalibrator:
    def __init__(self):
        self.cameras = []
        self.stereo_calibration = StereoCalibrator()

    async def calibrate_stereo(self):
        """Stereo kamera kalibrasyonu"""
        # Stereo kalibrasyon
        # Depth mapping
        # 3D reconstruction
```

---

## 📋 KONTROL LİSTESİ

### Kalibrasyon Öncesi

```
✅ Hazırlık Kontrolleri:

🔧 Hardware:
[ ] Kamera bağlı ve çalışıyor
[ ] Lens temiz
[ ] Çözünürlük ayarları doğru
[ ] Aydınlatma yeterli
[ ] Pattern yazdırıldı

💻 Software:
[ ] Script çalıştırılabilir
[ ] OpenCV kurulu
[ ] Kamera sürücüleri aktif
[ ] Yeterli disk alanı
[ ] Backup alındı

🎯 Ortam:
[ ] Çalışma alanı hazır
[ ] Pattern düz yüzeyde
[ ] Kamera sabit
[ ] Gölge yok
[ ] Temiz zemin
```

### Kalibrasyon Sonrası

```
✅ Sonuç Kontrolü:

📊 Kalibrasyon:
[ ] Hata < 0.5 piksel
[ ] 15+ başarılı görüntü
[ ] Camera matrix makul
[ ] Distortion coeffs makul
[ ] Sonuçlar kaydedildi

🧪 Test:
[ ] AprilTag tespit çalışıyor
[ ] Mesafe ölçümü doğru
[ ] Açı hesaplama doğru
[ ] Farklı mesafeler test edildi
[ ] Config güncellendi

🚀 Entegrasyon:
[ ] Robot config güncellendi
[ ] Test sistemi çalışıyor
[ ] Şarj yaklaşımı test edildi
[ ] Dokümantasyon güncellendi
[ ] Backup alındı
```

---

## 📈 KALİTE METRIKLERI

### Kalibrasyon Kalitesi

```python
# Kalite değerlendirme
def evaluate_calibration_quality(reprojection_error, num_images):
    """Kalibrasyon kalitesi değerlendir"""

    if reprojection_error < 0.3 and num_images >= 20:
        return "EXCELLENT"
    elif reprojection_error < 0.5 and num_images >= 15:
        return "GOOD"
    elif reprojection_error < 0.8 and num_images >= 10:
        return "ACCEPTABLE"
    else:
        return "POOR"
```

### Benchmark Değerleri

```
📊 Kalibrasyon Benchmark:

🎯 Reprojection Error:
- Mükemmel: < 0.3 piksel
- İyi: < 0.5 piksel
- Kabul edilebilir: < 0.8 piksel
- Kötü: > 0.8 piksel

🎯 Görüntü Sayısı:
- Minimum: 10 görüntü
- Önerilen: 20 görüntü
- Optimal: 30+ görüntü

🎯 AprilTag Performansı:
- Tespit oranı: > 90%
- Mesafe hatası: < 5cm
- Açı hatası: < 5°
- FPS: > 10
```

---

## 📝 SONUÇ

Kamera kalibrasyonu, AprilTag tabanlı navigasyon sisteminin temel taşıdır. Bu rehber ile:

- ✅ Doğru kamera kalibrasyonu yapabilirsiniz
- ✅ AprilTag tespit performansını optimize edebilirsiniz
- ✅ Şarj istasyonu yaklaşımını iyileştirebilirsiniz
- ✅ Görüntü işleme kalitesini artırabilirsiniz

**Unutmayın:** İyi kalibrasyon = İyi navigasyon!

---

## 🔗 İLGİLİ BELGELER

- [Encoder Kalibrasyon Rehberi](encoder_calibration_guide.md)
- [AprilTag Yerleştirme Rehberi](../apriltag_placement_guide.md)
- [Hardware Kurulum Rehberi](../hardware/assembly_guide.md)
- [Troubleshooting Guide](../troubleshooting.md)

---

**Son Güncelleme:** 2025-07-09
**Versiyon:** 1.0
**Yazar:** Hacı Abi 📷
