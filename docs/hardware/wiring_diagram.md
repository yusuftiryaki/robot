# Donanım Bağlantı Diyagramı
# Otonom Bahçe Asistanı (OBA) - Raspberry Pi 4

## 🔌 ANA BAĞLANTI ŞEMASI

```
                           RASPBERRY PI 4
                         ┌─────────────────┐
                         │     GPIO PINOUT │
                         │                 │
              ┌──────────┤ 3.3V (Pin 1)    │
              │          │ 5V   (Pin 2)    │
     IMU ─────┼──────────┤ SDA  (Pin 3)    │
     (I2C)    │          │ 5V   (Pin 4)    │
              └──────────┤ SCL  (Pin 5)    │
                         │ GND  (Pin 6) ───┼─── GND BUS
                         │ GPIO4(Pin 7) ───┼─── MOTOR_EN
                         │ TXD  (Pin 8)    │
                         │ GND  (Pin 9) ───┼─── GND BUS
                         │ RXD  (Pin 10)   │
                         │ GPIO17(Pin11)───┼─── SOL_MOTOR_PWM
                         │ GPIO18(Pin12)───┼─── SOL_MOTOR_DIR
                         │ GPIO27(Pin13)───┼─── SAG_MOTOR_PWM
                         │ GND   (Pin14)───┼─── GND BUS
                         │ GPIO22(Pin15)───┼─── SAG_MOTOR_DIR
                         │ GPIO23(Pin16)───┼─── FIRCA_PWM
                         │ 3.3V (Pin17)    │
                         │ GPIO24(Pin18)───┼─── FIRCA_DIR
                         │ MOSI (Pin19)    │
                         │ GND   (Pin20)───┼─── GND BUS
                         │ MISO (Pin21)    │
                         │ GPIO25(Pin22)───┼─── FAN_PWM
                         │ SCLK (Pin23)    │
                         │ CE0   (Pin24)   │
                         │ GND   (Pin25)───┼─── GND BUS
                         │ CE1   (Pin26)   │
                         │ GPIO5 (Pin29)───┼─── TAMPON_1
                         │ GND   (Pin30)───┼─── GND BUS
                         │ GPIO6 (Pin31)───┼─── TAMPON_2
                         │ GPIO12(Pin32)───┼─── TAMPON_3
                         │ GPIO13(Pin33)───┼─── TAMPON_4
                         │ GND   (Pin34)───┼─── GND BUS
                         │ GPIO19(Pin35)───┼─── ENC_SOL_A
                         │ GPIO16(Pin36)───┼─── ENC_SOL_B
                         │ GPIO26(Pin37)───┼─── ENC_SAG_A
                         │ GPIO20(Pin38)───┼─── ENC_SAG_B
                         │ GND   (Pin39)───┼─── GND BUS
                         │ GPIO21(Pin40)───┼─── BUZZER
                         └─────────────────┘
```

## 🚗 MOTOR SÜRÜCÜ BAĞLANTISI (L298N)

```
    RASPBERRY PI 4              L298N MOTOR DRIVER               MOTORS
                               ┌─────────────────┐
GPIO17 (PWM) ──────────────────┤ ENA             │
                               │                 │              ┌─────────┐
GPIO18 (DIR) ──────────────────┤ IN1       OUT1 ├──────────────┤ SOL     │
                               │                 │              │ MOTOR   │
GND ───────────────────────────┤ IN2       OUT2 ├──────────────┤         │
                               │                 │              └─────────┘
GPIO27 (PWM) ──────────────────┤ ENB             │
                               │                 │              ┌─────────┐
GPIO22 (DIR) ──────────────────┤ IN3       OUT3 ├──────────────┤ SAĞ     │
                               │                 │              │ MOTOR   │
GND ───────────────────────────┤ IN4       OUT4 ├──────────────┤         │
                               │                 │              └─────────┘
12V BATTERY ───────────────────┤ VCC             │
                               │                 │
GND ───────────────────────────┤ GND             │
                               └─────────────────┘
```

## 🧭 IMU SENSÖRÜ BAĞLANTISI (MPU6050)

```
    RASPBERRY PI 4                MPU6050 IMU
                                 ┌─────────────┐
3.3V (Pin 1) ────────────────────┤ VCC         │
                                 │             │
SDA (Pin 3) ─────────────────────┤ SDA         │
                                 │             │
SCL (Pin 5) ─────────────────────┤ SCL         │
                                 │             │
GND (Pin 6) ─────────────────────┤ GND         │
                                 │             │
GPIO4 (Pin 7) ───────────────────┤ INT         │
                                 └─────────────┘

I2C Adres: 0x68
```

## 📡 GPS MODÜLÜ BAĞLANTISI (NEO-8M)

```
    RASPBERRY PI 4                NEO-8M GPS
                                 ┌─────────────┐
5V (Pin 2) ──────────────────────┤ VCC         │
                                 │             │
TXD (Pin 8) ─────────────────────┤ RX          │
                                 │             │
RXD (Pin 10) ────────────────────┤ TX          │
                                 │             │
GND (Pin 9) ─────────────────────┤ GND         │
                                 └─────────────┘

UART: /dev/ttyAMA0
Baud Rate: 9600
```

##  TAMPON SENSÖRLERI (Mikroswitch)

```
    RASPBERRY PI 4              TAMPON SENSÖRLERI

GPIO5 (Pin 29) ─────────┬──────┤ TAMPON_1 (Ön Sol)
                        │      │
                       ┌┴┐     │
                       │R│10kΩ │
                       │ │     │
                       └┬┘     │
                        │      │
GND (Pin 30) ───────────┴──────┤ TAMPON_GND

GPIO6 (Pin 31) ─────────────────┤ TAMPON_2 (Ön Sağ)
GPIO12 (Pin 32) ────────────────┤ TAMPON_3 (Sol)
GPIO13 (Pin 33) ────────────────┤ TAMPON_4 (Sağ)
```

## 🎥 KAMERA BAĞLANTISI

```
    RASPBERRY PI 4              PI CAMERA V2
                               ┌─────────────┐
CSI Connector ─────────────────┤ FLEX CABLE  │
(Camera Port)                  │             │
                               │ 8MP CAMERA  │
                               │             │
                               └─────────────┘

Device: /dev/video0
Resolution: 1920x1080 @ 30fps
```

## 🔋 GÜÇ DAĞITIMI

```
                         12V LiPo BATTERY
                              │
                              ├─── L298N Motor Driver (12V)
                              │
                         ┌────┴────┐
                         │ Buck    │ 5V @ 3A
                         │Converter├─────┬─── Raspberry Pi 4
                         │ 12V→5V  │     │
                         └─────────┘     ├─── GPS Modülü
                                         │
                                         ├─── Encoder Sensörleri
                                         │
                                         └─── Fan Motor

                              │
                         ┌────┴────┐
                         │ Buck    │ 3.3V @ 1A
                         │Converter├─────┬─── IMU Sensörü
                         │ 12V→3.3V│     │
                         └─────────┘     └─── Pull-up Resistors
```

## ⚡ ELEKTRIK ÖZELLİKLERİ

### Güç Tüketimi
- Raspberry Pi 4: 5V @ 2.5A (12.5W)
- Motor Sürücü: 12V @ 5A peak (60W)
- IMU Sensörü: 3.3V @ 5mA (0.016W)
- GPS Modülü: 5V @ 50mA (0.25W)
- Encoder (x2): 3.3V @ 5mA each (0.033W)
- Kamera: 5V @ 250mA (1.25W)
- **Toplam: ~75W peak**

### Batarya Kapasitesi
- 12V 5000mAh LiPo
- **Çalışma Süresi: ~45-60 dakika**

## 🔧 MONTAJ ÖNERİLERİ

### PCB Yerleşimi
```
┌─────────────────────────────────────────┐
│  🎥              KAMERA                 │
├─────────────────────────────────────────┤
│  � KAMERA    � ENC_SOL    � ENC_SAG     │
├─────────────────────────────────────────┤
│                                         │
│    🧭 IMU        📍 GPS                 │
│                                         │
│    🖥️ RASPBERRY PI 4                    │
│                                         │
│                                         │
├─────────────────────────────────────────┤
│  🔋 BATTERY     ⚡ POWER_MANAGEMENT     │
├─────────────────────────────────────────┤
│              🚗 L298N                   │
│           MOTOR DRIVER                  │
└─────────────────────────────────────────┘
```

### Kablo Renk Kodu
- **Kırmızı**: +12V (Ana güç)
- **Turuncu**: +5V (Mantık devresi)
- **Sarı**: +3.3V (Sensörler)
- **Siyah**: GND (Ortak toprak)
- **Mavi**: PWM sinyalleri
- **Yeşil**: Digital I/O
- **Beyaz**: I2C/UART haberleşme
- **Mor**: Interrupt sinyalleri

## ⚠️ GÜVENLİK ÖNEMLERİ

1. **Elektrik Güvenliği**
   - Tüm bağlantıları çift kontrol edin
   - Kısa devre koruması kullanın
   - Uygun sigortalar takın

2. **Termal Yönetim**
   - Raspberry Pi için soğutma fanı
   - Motor sürücü için ısı emici
   - Hava dolaşımını engellemeyiniz

3. **Mekanik Güvenlik**
   - Tüm vida bağlantılarını kontrol edin
   - Sallantıyı önlemek için destekler kullanın
   - Kablo gerginliklerini kontrol edin

4. **Su Koruması**
   - Elektronik parçalar için IP65 kutu
   - Kablo girişlerinde conta kullanın
   - Drainage delikleri açın

## 🔍 TEST PROSEDÜRÜ

### 1. Güç Testi
```bash
# Voltaj ölçümü
vcgencmd measure_volts
vcgencmd get_throttled
```

### 2. GPIO Testi
```bash
# GPIO pin durumu
gpio readall
```

### 3. I2C Testi
```bash
# I2C cihazları tarama
i2cdetect -y 1
```

### 4. Kamera Testi
```bash
# Kamera test
raspistill -o test.jpg
```

### 5. GPS Testi
```bash
# GPS sinyal kontrol
cat /dev/ttyAMA0
```

## 🔄 ENCODER SENSÖRLERI BAĞLANTISI

```
    RASPBERRY PI 4              ENCODER SENSÖRLERI

GPIO19 (Pin35) ─────────────────┤ SOL_ENCODER_A
GPIO16 (Pin36) ─────────────────┤ SOL_ENCODER_B
GPIO26 (Pin37) ─────────────────┤ SAG_ENCODER_A
GPIO20 (Pin38) ─────────────────┤ SAG_ENCODER_B

3.3V (Pin1) ────────────────────┤ ENCODER_VCC
GND (Pin39) ────────────────────┤ ENCODER_GND
```

**Encoder Özellikleri:**
- **Çözünürlük**: 360 pulse/devir
- **Çıkış**: Quadrature (A/B kanalı)
- **Voltaj**: 3.3V TTL
- **Akım**: 5mA per encoder
- **Frekans**: Max 100kHz

**Encoder Faydaları:**
```
✅ Hassas odometri (±1mm)
✅ Gerçek zamanlı hız kontrolü
✅ Slip detection (kayma tespiti)
✅ GPS-independent navigation
✅ Kalman filter entegrasyonu
```

Bu diyagram robotun tüm elektronik bağlantılarını göstermektedir. Her bağlantı öncesinde mutlaka pin numaralarını kontrol ediniz!
