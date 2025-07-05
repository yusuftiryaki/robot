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
- [ ] Buzzer (5V)

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
python main.py --debug --simulation

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
