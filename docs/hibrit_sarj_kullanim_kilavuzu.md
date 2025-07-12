# 🔋 GPS + AprilTag Hibrit Şarj Sistemi Kullanım Kılavuzu

## 🚀 Hızlı Başlangıç

### 1. Sistem Gereksinimleri
```bash
# Gerekli Python paketleri
pip install opencv-python
pip install ina219  # Güç sensörü için
pip install pyserial  # GPS için (opsiyonel)
```

### 2. Konfigürasyon Ayarları
`config/robot_config.yaml` dosyasını düzenleyin:

```yaml
charging:
  enabled: true

  # GPS Şarj İstasyonu Koordinatları
  gps_dock:
    latitude: 41.0082    # ← Şarj istasyonunuz GPS koordinatı
    longitude: 28.9784   # ← Şarj istasyonunuz GPS koordinatı
    accuracy_radius: 3.0 # GPS hata payı (metre)

    # Geçiş Mesafeleri
    precise_approach_distance: 0.5     # AprilTag geçiş mesafesi
    medium_distance_threshold: 10.0    # Orta mesafe
    apriltag_detection_range: 0.5      # AprilTag algılama menzili

    # Hız Ayarları
    approach_speeds:
      normal: 0.3      # Normal yaklaşım hızı (m/s)
      slow: 0.2        # Yavaş yaklaşım (m/s)
      very_slow: 0.1   # Çok yavaş (m/s)
      precise: 0.02    # Hassas konumlandırma (m/s)
```

### 3. AprilTag Kurulumu
```yaml
charging:
  apriltag:
    sarj_istasyonu_tag_id: 0    # Şarj istasyonu AprilTag ID'si
    tag_boyutu: 0.08            # Tag boyutu (metre)
    kamera_matrix: [            # Kamera kalibrasyonu
      [640, 0, 320],
      [0, 640, 240],
      [0, 0, 1]
    ]
```

## 📋 Kullanım Senaryoları

### Senaryo 1: 🏠 Küçük Bahçe (GPS İsteğe Bağlı)
```python
# GPS olmadan sadece AprilTag
sarj_yaklasici = SarjIstasyonuYaklasici(
    sarj_config=charging_config,
    nav_config=None,           # GPS kapalı
    konum_takipci=None
)
```

**Davranış:**
- Robot direkt AprilTag arama modunda başlar
- Dönerek şarj istasyonunu arar
- Bulduğunda hassas yaklaşım yapar

### Senaryo 2: 🌾 Büyük Bahçe (Hibrit Mod)
```python
# GPS + AprilTag hibrit
sarj_yaklasici = SarjIstasyonuYaklasici(
    sarj_config=charging_config,
    nav_config=navigation_config,  # GPS aktif
    konum_takipci=konum_takipci
)
```

**Davranış:**
- Robot GPS navigasyon modunda başlar
- GPS waypoint'lerini takip eder
- 0.5m yakınına gelince AprilTag moduna geçer
- Hassas konumlandırma yapar

## 🎛️ Manuel Kontrol

### Robot Kodundan Kullanım
```python
# Manuel şarj istasyonuna gitme komutu
robot.sarj_istasyonuna_git()

# Durum kontrolü
durum = robot.get_robot_durumu()
print(f"Şarj durumu: {durum['sarj_sistemi']}")
```

### Web Arayüzünden
```javascript
// Şarj istasyonuna git
fetch('/api/sarj_istasyonuna_git', {method: 'POST'})

// Durum bilgisi al
fetch('/api/durum')
  .then(response => response.json())
  .then(data => console.log(data.sarj_sistemi))
```

## 📊 Durum İzleme

### GPS Navigasyon Durumu
```python
durum = sarj_yaklasici.get_yaklasim_durumu()

print(f"Aktif mod: {durum['durum']}")
print(f"GPS aktif: {durum['gps_navigasyon']['aktif']}")
print(f"Waypoint: {durum['gps_navigasyon']['mevcut_waypoint']}")
print(f"Kalan mesafe: {durum['gps_navigasyon']['mesafe_kalan']}m")
```

### AprilTag Durumu
```python
if durum['son_tespit']:
    print(f"AprilTag mesafe: {durum['son_tespit']['mesafe']:.2f}m")
    print(f"Açı: {durum['son_tespit']['aci']:.1f}°")
    print(f"Güven: {durum['son_tespit']['guven_skoru']:.2f}")
```

## 🔧 Sorun Giderme

### Problem: GPS Navigasyonu Çalışmıyor
**Kontrol:**
1. `konum_takipci` None olmasın
2. `gps_dock` koordinatları doğru olsun
3. `nav_config` boş olmasın

**Çözüm:**
```python
# Debug için
logger.setLevel(logging.DEBUG)

# GPS durumu kontrol
if sarj_yaklasici.rota_planlayici:
    print("GPS aktif")
else:
    print("GPS pasif - sadece AprilTag modu")
```

### Problem: AprilTag Tespit Edilmiyor
**Kontrol:**
1. Kamera çalışır durumda olsun
2. AprilTag doğru ID'de olsun (`sarj_istasyonu_tag_id`)
3. Aydınlatma yeterli olsun
4. Tag boyutu doğru ayarlansın

**Çözüm:**
```python
# AprilTag debug
cv2.imwrite("debug_kamera.jpg", kamera_data)
# Görüntüyü kontrol edin

# Detector parametreleri
detector_params.adaptiveThreshWinSizeMin = 3  # Düşük ışık için
```

### Problem: Robot Şarj İstasyonunda Dolanıyor
**Sebep:** Çok fazla waypoint üretimi

**Çözüm:**
```yaml
navigation:
  path_planning:
    grid_resolution: 0.5  # 0.1'den artırın (daha az waypoint)
```

```python
# Hibrit geçiş mesafesini artırın
charging:
  gps_dock:
    precise_approach_distance: 1.0  # 0.5'ten artırın
```

## ⚡ Performans Optimizasyonu

### GPS Navigasyon Hızlandırma
```yaml
charging:
  gps_dock:
    approach_speeds:
      normal: 0.5      # Hızı artırın (dikkatli!)
```

### AprilTag Tespit Optimizasyonu
```python
# Detector parametreleri optimize edin
detector_params.minMarkerPerimeterRate = 0.05  # Artırın
detector_params.maxMarkerPerimeterRate = 3.0   # Azaltın
```

### Waypoint Azaltma
```python
# GPS rotasında waypoint filtreleme
# rota_planlayici.py'de
if len(gps_rotasi) > 50:
    # Her 2. waypoint'i al
    gps_rotasi = gps_rotasi[::2]
```

## 📋 Bakım ve Kalibrasyon

### Haftalık Kontrol
- [ ] AprilTag'ler temiz ve hasarsız mı?
- [ ] Kamera lens temiz mi?
- [ ] GPS antenna bağlantısı sağlam mı?
- [ ] INA219 sensör okumaları normal mi?

### Aylık Kalibrasyon
```bash
# Kamera kalibrasyonu
python scripts/camera_calibration.py

# GPS accuracy testi
python test_gps_accuracy.py

# AprilTag detection testi
python test_apriltag_system.py
```

## 🎯 Sonraki Seviye

### RTK-GPS Entegrasyonu
```yaml
navigation:
  gps:
    type: "rtk"  # Yüksek hassasiyet
    base_station_ip: "192.168.1.100"
    accuracy_target: 0.02  # 2cm hassasiyet
```

### Çoklu AprilTag
```yaml
charging:
  apriltag:
    multiple_tags: true
    tag_ids: [0, 1, 2]  # Ana + yedek tag'ler
    min_detection_count: 2  # En az 2 tag görmeli
```

## 🚀 İyi Şanslar!

Hibrit şarj sistemi artık hazır! GPS ile uzaktan gelip, AprilTag ile hassas konumlanma - en iyi teknolojilerin birleşimi.

**Herhangi bir sorun olursa:** `logs/robot.log` dosyasını kontrol edin ve debug mode açın.

**İpucu:** İlk testlerde `approach_speeds` değerlerini düşük tutun, sistem alıştıktan sonra artırın.

Hacı Abi, kolay gelsin! 🔋⚡
