# Donanım Kurulum Rehberi
# Otonom Bahçe Asistanı (OBA) - Adım Adım Montaj

## 📋 GEREKLI MALZEMELER

### Ana Bileşenler
- [ ] Raspberry Pi 4 (4GB RAM)
- [ ] MicroSD Kart (64GB, Class 10)
- [ ] Mi Vacuum Essential şasisi
- [ ] 12V 5000mAh LiPo Batarya
- [ ] L298N Motor Driver Board
- [ ] Buck Converter (12V→5V 3A)
- [ ] Buck Converter (12V→3.3V 1A)

### Sensörler
- [ ] MPU6050 IMU Sensörü
- [ ] NEO-8M GPS Modülü
- [ ] HC-SR04 Ultrasonik Sensör (x6)
- [ ] Raspberry Pi Camera V2
- [ ] Mikroswitch Tampon Sensörü (x4)
- [ ] INA219 Güç Monitör Sensörü 🆕
- [ ] Buzzer (5V)

### AprilTag Şarj İstasyonu Bileşenleri 🆕
- [ ] AprilTag Etiketleri (15cm, ID: 0-4)
- [ ] Şarj İstasyonu Baz Ünitesi
- [ ] Manyetik Şarj Konektörleri
- [ ] INA219 Güç Sensörü (şarj tespiti için)
- [ ] Şarj İstasyonu LED'leri (durum göstergesi)
- [ ] AprilTag Montaj Aparatı (ayarlanabilir)

### Kablolar ve Bağlantı
- [ ] Jumper Wire Seti (Erkek-Erkek, Dişi-Dişi)
- [ ] Breadboard veya PCB
- [ ] 40 Pin GPIO Extension Cable
- [ ] CSI Camera Cable
- [ ] Micro USB Kablo (güç)
- [ ] XT60 Connector (batarya)

### Mekanik Parçalar
- [ ] M3 Vidalar ve Somunlar
- [ ] Plastik Stand-off'lar
- [ ] Alüminyum L Profiller
- [ ] IP65 Elektronik Kutu
- [ ] Silikon Conta ve Kauçuk

### Araçlar
- [ ] Tornavida Seti
- [ ] Multimetre
- [ ] Isı Tabancası
- [ ] Matkap ve Delici Uçlar
- [ ] Sıcak Silikon
- [ ] Kablo Bağı

## 🔧 MONTAJ AŞAMALARI

### AŞAMA 1: ŞASİ HAZIRLIĞI

#### 1.1 Mi Vacuum Şasi Analizi
```
┌─────────────────────────────────────────┐
│              ÜST GÖRÜNÜM                │
│                                         │
│  [Sensör Bölgesi]    [Ana Platform]     │
│                                         │
│  ┌─[Ön]─┐           ┌─[Elektronik]─┐   │
│  │       │           │   Bölgesi    │   │
│  │       │           │              │   │
│  └───────┘           └──────────────┘   │
│                                         │
│  [Sol Motor]         [Sağ Motor]        │
│      │                   │             │
│      └─[Tekerlek]─   ─[Tekerlek]─┘      │
│                                         │
│              [Batarya Bölgesi]          │
└─────────────────────────────────────────┘
```

#### 1.2 Mevcut Motorları Analiz Et
- **Sol Motor**: Orijinal Mi Vacuum motoru kullanılacak
- **Sağ Motor**: Orijinal Mi Vacuum motoru kullanılacak
- **Fırça Motor**: Mevcut fırça sistemi adapte edilecek
- **Fan Motor**: Emme fanı mevcut sistem kullanılacak

**⚠️ Önemli**: Orijinal motor kontrol kartını çıkartıp L298N ile değiştireceğiz.

#### 1.3 Elektronik Platform Oluştur
```bash
# Gerekli ölçümler
- Platform boyutu: 20cm x 15cm
- Yükseklik: Kameraya 15cm clearance
- Delik pozisyonları: Raspberry Pi mounting holes
```

### AŞAMA 2: GÜÇ SİSTEMİ KURULUMU

#### 2.1 Batarya Bağlantısı
```
12V BATTERY
    │
    ├─── MAIN SWITCH ───┬─── L298N (Motor Driver)
    │                   │
    │                   ├─── Buck 12V→5V ─── Raspberry Pi
    │                   │
    │                   └─── Buck 12V→3.3V ─── Sensors
    │
    └─── FUSE (10A) ─── Ground Distribution
```

**Önemli Güvenlik Notları:**
- Ana şaltere güvenlik kilidi ekle
- 10A sigorta kullan
- Batarya bağlantısında polariteyi kontrol et

#### 2.2 Güç Dağıtım Panosu
```python
# Power management config
POWER_CONFIG = {
    'main_voltage': 12.0,      # Ana sistem voltajı
    'logic_voltage': 5.0,      # Raspberry Pi
    'sensor_voltage': 3.3,     # Sensörler
    'motor_voltage': 12.0,     # Motorlar
    'max_current': 8.0,        # Maksimum akım (A)
    'low_battery_threshold': 11.1,  # Düşük batarya uyarısı
    'critical_battery': 10.5    # Kritik batarya seviyesi
}
```

### AŞAMA 3: RASPBERRY PI KURULUMU

#### 3.1 İşletim Sistemi Kurulumu
```bash
# Raspberry Pi OS (Lite) kurulum
# 1. Raspberry Pi Imager ile SD karta yaz
# 2. SSH ve I2C'yi aktif et
# 3. İlk boot ve güncellemeler

sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip git i2c-tools -y

# GPIO ve I2C ayarları
sudo raspi-config
# Interface Options → I2C → Enable
# Interface Options → Camera → Enable
# Interface Options → SSH → Enable
```

#### 3.2 Python Geliştirme Ortamı
```bash
# Proje klonlama
cd /home/pi
git clone <repository_url> bahce_robotu
cd bahce_robotu

# Virtual environment oluştur
python3 -m venv venv
source venv/bin/activate

# Requirements kurulum
pip install -r requirements.txt
```

#### 3.3 Systemd Service Kurulum
```bash
# Robot service dosyası oluştur
sudo nano /etc/systemd/system/bahce-robotu.service

# Service içeriği:
[Unit]
Description=Otonom Bahce Robotu
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/bahce_robotu
ExecStart=/home/pi/bahce_robotu/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target

# Service'i aktif et
sudo systemctl enable bahce-robotu.service
```

### AŞAMA 4: SENSÖR MONTAJLARI

#### 4.1 IMU Sensörü (MPU6050)
**Montaj Pozisyonu**: Robot merkezinde, titreşimden korunmuş
```
     ┌─[IMU]─┐
     │ MPU   │  ← Sponge padding ile titreşim izolasyonu
     │ 6050  │
     └───────┘
```

**Bağlantı Test:**
```bash
# I2C tarama
i2cdetect -y 1
# 0x68 adresinde cihaz görünmeli

# Test script
python3 -c "
import smbus
bus = smbus.SMBus(1)
print('IMU Connection:', hex(bus.read_byte(0x68)))
"
```

#### 4.2 GPS Modülü (NEO-8M)
**Montaj Pozisyonu**: Robot üst kısmında, metalik engellerden uzak
```
      🛰️
   ┌─[GPS]─┐
   │ NEO-8M│  ← En üst seviyede, açık gökyüzü erişimi
   │       │
   └───────┘
```

**Bağlantı Test:**
```bash
# UART testi
sudo cat /dev/ttyAMA0
# NMEA mesajları görünmeli: $GPGGA, $GPRMC, vb.

# GPS test script
python3 -c "
import serial
gps = serial.Serial('/dev/ttyAMA0', 9600, timeout=1)
for i in range(10):
    print(gps.readline().decode('ascii', errors='ignore').strip())
"
```

#### 4.3 Kamera (Pi Camera V2)
**Montaj Pozisyonu**: Robot ön kısmında, temiz görüş alanı
```
      📷
   ┌─[CAM]─┐
   │ Pi V2 │  ← Lens temiz, 45° aşağı açı
   │       │
   └───────┘
```

**Bağlantı Test:**
```bash
# Kamera testi
raspistill -o test.jpg -t 1000
# test.jpg dosyası oluşmalı

# Video stream test
raspivid -t 10000 -w 640 -h 480 -fps 30 -o test.h264
"
```
**Montaj Pozisyonu**: Ön kısımda, temiz görüş alanı
```
     ┌─[CAMERA]─┐
     │   📷     │  ← 15° aşağı açı, zemin görünümü için
     │  V2.1    │
     └──────────┘
```

**Kamera Test:**
```bash
# Kamera testi
raspistill -o test_image.jpg
ls -la test_image.jpg

# Video stream testi
raspivid -t 5000 -o test_video.h264
```
### AŞAMA 5: MOTOR SİSTEMİ ENTEGRASYONU

#### 5.1 Orijinal Motorları Analiz Et
```python
# Mi Vacuum motor özellikleri (tahmin)
MOTOR_SPECS = {
    'voltage': 12,          # V
    'max_current': 2.5,     # A per motor
    'encoder_ppr': 360,     # Pulse per revolution
    'wheel_diameter': 0.1,  # m
    'gear_ratio': 30,       # Motor to wheel
    'max_rpm': 150          # Wheel RPM
}
```

#### 5.2 L298N Motor Driver Bağlantısı
**Motor Driver Test:**
```python
import RPi.GPIO as GPIO
import time

# Pin tanımları
ENA = 17    # Sol motor PWM
IN1 = 18    # Sol motor direction 1
IN2 = 24    # Sol motor direction 2
ENB = 27    # Sağ motor PWM
IN3 = 22    # Sağ motor direction 1
IN4 = 23    # Sağ motor direction 2

GPIO.setmode(GPIO.BCM)
GPIO.setup([ENA, IN1, IN2, ENB, IN3, IN4], GPIO.OUT)

# PWM setup
left_pwm = GPIO.PWM(ENA, 1000)   # 1kHz
right_pwm = GPIO.PWM(ENB, 1000)  # 1kHz
left_pwm.start(0)
right_pwm.start(0)

def motor_test():
    print("İleri hareket...")
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.HIGH)
    GPIO.output(IN4, GPIO.LOW)
    left_pwm.ChangeDutyCycle(50)
    right_pwm.ChangeDutyCycle(50)
    time.sleep(2)

    print("Dur...")
    left_pwm.ChangeDutyCycle(0)
    right_pwm.ChangeDutyCycle(0)
    time.sleep(1)

    print("Geri hareket...")
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.HIGH)
    left_pwm.ChangeDutyCycle(50)
    right_pwm.ChangeDutyCycle(50)
    time.sleep(2)

    # Temizle
    left_pwm.stop()
    right_pwm.stop()
    GPIO.cleanup()

motor_test()
```

### AŞAMA 6: TAMPON SENSÖRLÜ GÜVENLİK SİSTEMİ

#### 6.1 Mikroswitch Montajı
**Tampon Sensör Pozisyonları:**
```
    [SW1]           [SW2]
      │               │
   ┌──┴─────────────┴──┐
   │     ÖN TAMPON     │  ← Yay sistemi ile
   └──┬─────────────┬──┘
   [SW4]           [SW3]
```

**Tampon Test:**
```python
import RPi.GPIO as GPIO

# Tampon pin tanımları
BUMPER_PINS = {
    'front_left': 5,
    'front_right': 6,
    'left': 12,
    'right': 13
}

GPIO.setmode(GPIO.BCM)
for pin in BUMPER_PINS.values():
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def test_bumpers():
    while True:
        for name, pin in BUMPER_PINS.items():
            if GPIO.input(pin) == GPIO.LOW:
                print(f"TAMPON BASILI: {name}")
        time.sleep(0.1)

test_bumpers()
```

### AŞAMA 7: FİNAL TEST VE KALİBRASYON

#### 7.1 Tam Sistem Testi
```bash
# Ana uygulamayı test modunda çalıştır
cd /home/pi/bahce_robotu

# Gerçek donanım testi
python main.py --debug

# Test raporlarını kontrol et
cat logs/robot.log
```

#### 7.2 Sensör Kalibrasyonu
```python
# IMU kalibrasyon
python3 -c "
from src.hardware.sensor_okuyucu import SensorOkuyucu
import asyncio

async def calibrate():
    sensor = SensorOkuyucu(simulation_mode=False)
    await sensor.basla()
    await sensor.imu_kalibre_et()
    print('IMU kalibrasyon tamamlandı')
    await sensor.durdur()

asyncio.run(calibrate())
"
```

#### 7.3 Güvenlik Test Prosedürü
```bash
# 1. Acil Stop Testi
echo "Acil stop butonunu test et"

# 2. Tampon Sensör Testi
echo "Her tamponu manuel olarak bas"

# 3. Eğim Sensör Testi
echo "Robotu eğimli yüzeye koy"

# 4. Batarya Düşük Testi
echo "Batarya voltajını düşür ve uyarıları kontrol et"

# 5. Engel Algılama Testi
echo "Ultrasonik sensörler önüne engel koy"
```

## 📊 PERFORMANS BEKLENTİLERİ

### Hareket Performansı
- **Maksimum hız**: 0.5 m/s
- **Minimum dönüş yarıçapı**: 0.15 m
- **Rampa kabiliyeti**: 15°
- **Çalışma süresi**: 45-60 dakika

### Sensör Performansı
- **GPS hassasiyeti**: ±2-3 metre
- **IMU çözünürlüğü**: 0.1° açısal
- **Kamera çözünürlüğü**: 1920x1080 @ 30fps
- **Engel tespiti**: Kamera tabanlı computer vision

### Sistemik Performans
- **Boot zamanı**: ~30 saniye
- **Response time**: <100ms
- **CPU kullanımı**: %40-60
- **Bellek kullanımı**: ~1GB

## 🔧 SORUN GİDERME

### Yaygın Sorunlar

#### 1. Robot Boot Olmuyor
- Güç bağlantılarını kontrol et
- SD kart sorunlarını kontrol et
- Serial konsol ile debug yap

#### 2. Sensörler Çalışmıyor
```bash
# I2C cihaz kontrolü
i2cdetect -y 1

# GPIO pin durumu
gpio readall

# Syslog kontrol
tail -f /var/log/syslog
```

#### 3. Motorlar Hareket Etmiyor
- L298N power LED kontrolü
- Motor bağlantı kontrolü
- PWM sinyal kontrolü

#### 4. GPS Sinyal Almıyor
- Anten konumu kontrolü
- UART bağlantı kontrolü
- Satellite view test

Bu rehber ile robotunuz tam olarak çalışır hale gelecektir. Her adımı dikkatli takip edin ve test etmeyi unutmayın! 🤖

# AprilTag Şarj İstasyonu Kurulum Rehberi
# Otonom Bahçe Asistanı (OBA) - Adım Adım Montaj

## 🔋 APRILTAG ŞARJ İSTASYONU KURULUMU

### AŞAMA 9: AprilTag Şarj İstasyonu Montajı

#### 9.1 Şarj İstasyonu Baz Ünitesi

**Gerekli Malzemeler:**
- Şarj İstasyonu Baz Ünitesi
- 12V Güç Adaptörü (5A)
- Manyetik Şarj Konektörleri
- INA219 Güç Monitör Sensörü
- AprilTag Etiketleri (ID: 0-4, 15cm boyut)
- LED Durum Göstergesi

```bash
# 1. Baz ünitesinin düz zemine yerleştirilmesi
# - Stabilite için en az 1m² düz alan gerekli
# - Güneş ışığından korunmalı (kamera için)
# - Temiz ve kuru zemin

# 2. Güç bağlantısı
+ Pozitif: Kırmızı kablo (12V)
- Negatif: Siyah kablo (GND)
Güç: 12V 5A adaptör (60W)
```

#### 9.2 AprilTag Etiket Yerleştirme

**AprilTag Konumlandırma Prensipleri:**

```
    [TAG_1]    [TAG_0]    [TAG_2]
       🏷️        🎯        🏷️
      (Yedek)   (Ana)     (Yedek)
        ↑         ↑         ↑
     45° açı   Düz bakış  45° açı
```

**Montaj Adımları:**

1. **Ana AprilTag (ID: 0) - Merkez:**
   - Şarj noktasından 30cm yükseklikte
   - Robot kamerasına düz bakacak şekilde
   - 15cm x 15cm boyutunda
   - Siyah çerçeve ile beyaz zemin üzerine

2. **Yedek AprilTag'ler (ID: 1-4) - Çevre:**
   - Ana tag'in etrafında 50cm mesafede
   - 45° açıyla robot kamerasına bakacak şekilde
   - Farklı yaklaşım açıları için yedek rotalar

3. **Etiket Kalitesi Kontrolleri:**
   ```bash
   # AprilTag kalite kontrol scripti
   python scripts/apriltag_generator.py --test-detection

   # Kamera ile tespit kontrolü
   python test_apriltag_system.py --live-test
   ```

#### 9.3 INA219 Güç Sensörü Bağlantısı

**INA219 Şarj Tespiti Kurulumu:**

```
Raspberry Pi          INA219          Şarj Devres
GPIO 2 (SDA)   <--->  SDA
GPIO 3 (SCL)   <--->  SCL
3.3V           <--->  VCC
GND            <--->  GND
                      VIN+   <--->  Şarj + Kablosu
                      VIN-   <--->  Şarj - Kablosu
```

**INA219 Konfigürasyonu:**
```python
# INA219 şarj tespiti parametreleri
SARJ_AKIMI_ESIGI = 0.1      # 100mA (şarj başladı)
BAGLANTI_VOLTAJ_ESIGI = 11.0 # 11V (fiziksel bağlantı)
SAMPLING_RATE = 10           # 10Hz ölçüm sıklığı
```

#### 9.4 Manyetik Şarj Konektörü

**Manyetik Konektör Özellikleri:**
- **Akım kapasitesi:** 5A
- **Voltaj:** 12V
- **Manyetik kuvvet:** 20N (2kg çekme kuvveti)
- **Su geçirmezlik:** IP65
- **Yanlış kutup koruması:** Var

**Konektör Montajı:**
```
Robot Tarafı:
- Şasinin arka kısmına monte et
- INA219 sensörü devreye dahil et
- LED gösterge ekle (şarj durumu için)

İstasyon Tarafı:
- Baz ünitesinde merkezi konum
- Otomatik hizalama için kılavuz yuvası
- Manyetik çekim alanı optimizasyonu
```

#### 9.5 AprilTag Sistem Testi

**Test Senaryoları:**

1. **AprilTag Tespit Testi:**
   ```bash
   # Test 1: Statik tespit
   python test_apriltag_system.py --static-test

   # Test 2: Hareket halinde tespit
   python test_apriltag_system.py --motion-test

   # Test 3: Farklı mesafeler
   python test_apriltag_system.py --distance-test
   ```

2. **Yaklaşım Algoritması Testi:**
   ```bash
   # Manuel yaklaşım testi
   python -m src.navigation.sarj_istasyonu_yaklasici --test-mode

   # Otomatik yaklaşım testi
   python main.py --test-charging-approach
   ```

3. **INA219 Bağlantı Testi:**
   ```bash
   # INA219 sensör testi
   python -c "
   from ina219 import INA219
   ina = INA219(address=0x40)
   ina.configure()
   print(f'Voltaj: {ina.voltage():.2f}V')
   print(f'Akım: {ina.current():.2f}mA')
   "
   ```

### AŞAMA 10: Şarj İstasyonu Kalibrasyon

#### 10.1 Kamera Kalibrasyonu

**Kamera Matrix Kalibrasyonu:**
```bash
# Kalibrasyon scriptini çalıştır
python scripts/camera_calibration.py

# AprilTag detection için optimize et
python scripts/apriltag_calibration.py --optimize-detection
```

**Kalibrasyon Sonuçları:**
```yaml
# config/robot_config.yaml güncelle
apriltag:
  kamera_matrix:
    - [fx, 0, cx]   # Focal length X, Center X
    - [0, fy, cy]   # Focal length Y, Center Y
    - [0, 0, 1]     # Homogeneous koordinat
  distortion_coeffs: [k1, k2, p1, p2, k3]  # Distortion katsayıları
```

#### 10.2 Hassas Konum Ayarlama

**Konum Kalibrasyonu Adımları:**

1. **Manuel Test Yaklaşımı:**
   - Robot'u şarj istasyonundan 2m uzağa yerleştir
   - Manuel kontrol ile yaklaşım yap
   - AprilTag tespit mesafelerini not et

2. **Otomatik Kalibrasyon:**
   ```bash
   # Otomatik kalibrasyon modu
   python main.py --calibrate-charging --debug
   ```

3. **Hassas Ayar Parametreleri:**
   ```yaml
   apriltag:
     hedef_mesafe: 0.30      # 30cm hedef mesafe
     hassas_mesafe: 0.10     # 10cm hassas mod başlangıcı
     aci_toleransi: 3.0      # 3° açı toleransı
     pozisyon_toleransi: 0.015  # 1.5cm pozisyon toleransı
   ```

#### 10.3 Performans Optimizasyonu

**FPS ve Gecikme Optimizasyonu:**
```python
# Kamera FPS ayarları
APRILTAG_CAMERA_FPS = 15    # 15 FPS (hassas tespit için)
DETECTION_SKIP_FRAMES = 2   # Her 2 frame'de bir tespit
PROCESSING_TIMEOUT = 200    # 200ms maksimum işlem süresi
```

**Güvenilirlik Testleri:**
- **Gündüz koşulları:** Parlak ışık altında tespit
- **Akşam koşulları:** Düşük ışık altında tespit
- **Hareket halinde:** Robot hareket ederken tespit
- **Mesafe varyasyonları:** 0.1m - 2.0m arası mesafeler

## 📊 APRILTAG SİSTEM ÖZETİ

### Sistem Gereksinimleri
- **Kamera çözünürlüğü:** En az 640x480
- **İşlem gücü:** Raspberry Pi 4 (2GB+ RAM)
- **Aydınlatma:** 200-2000 lux arası
- **AprilTag boyutu:** 15cm (optimum)
- **Tespit mesafesi:** 0.1m - 3.0m

### Performans Metrikleri
- **Tespit oranı:** >95% (optimum koşullarda)
- **Konum hassasiyeti:** ±1cm
- **Açı hassasiyeti:** ±2°
- **Yaklaşım süresi:** 30-60 saniye
- **Şarj bağlantı başarı oranı:** >98%
