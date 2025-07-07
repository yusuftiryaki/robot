# 🍓 Raspberry Pi Kurulum Rehberi - OBA Robot Production Deployment

## 📋 ÖNKOŞULLAR

### Donanım Gereksinimleri

- ✅ Raspberry Pi 4 (4GB RAM) - **Tavsiye edilir**
- ✅ MicroSD Kart (64GB, Class 10+)
- ✅ Güvenilir internet bağlantısı
- ✅ SSH erişimi için terminal

### Yazılım Gereksinimleri
- Raspberry Pi Imager
- SSH Client (Windows için PuTTY)
- SCP/SFTP Client

---

## 🚀 AŞAMA 1: RASPBERRY PI OS KURULUMU

### 1.1 OS İmajını Hazırla
```bash
# Raspberry Pi Imager ile:
# 1. "Raspberry Pi OS Lite (64-bit)" seç
# 2. Advanced Options (⚙️) ile:
#    - SSH Enable ✅
#    - Username: pi
#    - Password: [güçlü şifre]
#    - WiFi bilgileri
#    - Locale: tr-TR.UTF-8
```

### 1.2 İlk Boot ve Güncelleme
```bash
# SSH ile bağlan
ssh pi@[raspberry-pi-ip]

# Sistem güncellemesi
sudo apt update && sudo apt upgrade -y

# Gerekli temel paketler
sudo apt install -y git python3 python3-pip python3-venv \
                    i2c-tools gpio raspi-config \
                    build-essential cmake pkg-config \
                    libjpeg-dev libtiff5-dev libjasper-dev libpng-dev \
                    libavcodec-dev libavformat-dev libswscale-dev \
                    libv4l-dev libxvidcore-dev libx264-dev \
                    libfontconfig1-dev libcairo2-dev \
                    libgdk-pixbuf2.0-dev libpango1.0-dev \
                    libgtk2.0-dev libgtk-3-dev \
                    libatlas-base-dev gfortran \
                    libhdf5-dev libhdf5-serial-dev \
                    libhdf5-103 python3-pyqt5 \
                    python3-dev python3-distutils

# Reboot
sudo reboot
```

---

## 🔧 AŞAMA 2: SISTEM KONFIGÜRASYONU

### 2.1 GPIO ve Kamera Aktifleştir
```bash
# raspi-config ile ayarlar
sudo raspi-config

# Aşağıdakileri aktifleştir:
# 3 Interface Options:
#   - I2C: Enable ✅
#   - SPI: Enable ✅
#   - Camera: Enable ✅
#   - SSH: Enable ✅
# 5 Localisation Options:
#   - Timezone: Europe/Istanbul
#   - Keyboard: Turkish
```

### 2.2 Kullanıcı İzinleri
```bash
# Pi kullanıcısını gerekli gruplara ekle
sudo usermod -a -G i2c,spi,gpio,video,input pi

# Logout/login yap
logout
ssh pi@[raspberry-pi-ip]

# Test et
groups pi
# Çıktıda i2c, spi, gpio, video olmalı
```

---

## 📦 AŞAMA 3: OBA ROBOT KURULUMU

### 3.1 Proje Klonlama
```bash
# Ana dizinde çalış
cd /home/pi

# Repository klonla (URL'yi güncelleyin)
git clone https://github.com/[user]/oba.git
cd oba

# Branch kontrolü
git branch -a
git checkout main  # veya master
```

### 3.2 Python Environment Kurulumu
```bash
# Virtual environment oluştur
python3 -m venv venv
source venv/bin/activate

# Pip güncelle
pip install --upgrade pip setuptools wheel

# Dependencies yükle
pip install -r requirements.txt

# OpenCV kurulumu (Raspberry Pi için özel)
pip install opencv-python-headless==4.8.1.78
pip install opencv-contrib-python-headless==4.8.1.78
```

### 3.3 Sistem Testleri
```bash
# Python environment aktif olduğundan emin ol
source venv/bin/activate

# Hardware testleri
python -m pytest tests/test_hardware.py -v

# I2C cihazları kontrol et
i2cdetect -y 1

# Kamera testi
libcamera-hello --preview --timeout 5000
```

---

## ⚙️ AŞAMA 4: PRODUCTION KONFIGÜRASYONU

### 4.1 Config Dosyasını Kopyala
```bash
# Production config'i aktif et
cp config/environments/raspberry_pi.yaml config/robot_config.yaml

# Config'i düzenle (gerekiyorsa)
nano config/robot_config.yaml
```

### 4.2 Log Dizinleri Oluştur
```bash
# Log klasörleri
mkdir -p logs
mkdir -p temp
mkdir -p data/maps
mkdir -p data/sensor_data

# İzinleri ayarla
chmod 755 logs temp data
```

### 4.3 Script'leri PATH'e Ekle
```bash
# .bashrc'ye ekle
echo 'export PATH="/home/pi/oba/scripts:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Script'lere execute izni ver
chmod +x scripts/*

# Test et
oba-help
```

---

## 🚀 AŞAMA 5: SERVİS KURULUMU

### 5.1 Systemd Service Oluştur
```bash
# Service dosyası oluştur
sudo nano /etc/systemd/system/oba-robot.service
```

Service içeriği:
```ini
[Unit]
Description=OBA Autonomous Garden Robot
After=network.target
Wants=network.target

[Service]
Type=simple
User=pi
Group=pi
WorkingDirectory=/home/pi/oba
Environment=PATH=/home/pi/oba/venv/bin:/home/pi/oba/scripts:/usr/local/bin:/usr/bin:/bin
ExecStart=/home/pi/oba/venv/bin/python main.py
ExecStop=/home/pi/oba/scripts/oba-stop
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### 5.2 Service'i Aktifleştir
```bash
# Service'i yükle
sudo systemctl daemon-reload
sudo systemctl enable oba-robot.service

# Manuel test
sudo systemctl start oba-robot.service
sudo systemctl status oba-robot.service

# Logları izle
sudo journalctl -u oba-robot.service -f
```

---

## 🌐 AŞAMA 6: NETWORK AYARLARI

### 6.1 Statik IP (Opsiyonel)
```bash
# dhcpcd.conf'u düzenle
sudo nano /etc/dhcpcd.conf

# Aşağıdakini ekle (IP'leri ağınıza göre ayarlayın):
interface wlan0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=192.168.1.1 8.8.8.8
```

### 6.2 Güvenlik Duvarı (UFW)
```bash
# UFW yükle ve ayarla
sudo apt install ufw -y

# Temel kurallar
sudo ufw default deny incoming
sudo ufw default allow outgoing

# SSH ve Web interface
sudo ufw allow ssh
sudo ufw allow 8080

# Aktifleştir
sudo ufw enable
sudo ufw status
```

---

## 🧪 AŞAMA 7: FINAL TEST

### 7.1 Manuel Test
```bash
# Robot'u manuel başlat
cd /home/pi/oba
source venv/bin/activate
oba-start --debug

# Başka terminalde durum kontrol et
oba-status
oba-logs follow
```

### 7.2 Web Interface Test
```bash
# Tarayıcıda aç:
http://[raspberry-pi-ip]:8080

# Kontroller:
# ✅ Robot durumu görünüyor mu?
# ✅ Manual kontrol çalışıyor mu?
# ✅ Loglar aktif mi?
# ✅ Acil stop çalışıyor mu?
```

### 7.3 Sistem Testi
```bash
# Tam sistem testi
oba-test

# Hardware spesifik test
oba-test hardware

# Reboot sonrası otomatik başlama testi
sudo reboot

# 2-3 dakika sonra kontrol et
ssh pi@[raspberry-pi-ip]
oba-status
```

---

## 🔧 SORUN GİDERME

### Yaygın Sorunlar

#### 1. I2C Sensörler Algılanmıyor
```bash
# I2C aktif mi kontrol et
lsmod | grep i2c
sudo raspi-config  # Interface Options → I2C → Enable

# Sensör taraması
i2cdetect -y 1
```

#### 2. Kamera Çalışmıyor
```bash
# Kamera aktif mi?
sudo raspi-config  # Interface Options → Camera → Enable

# Test
libcamera-hello --list-cameras
```

#### 3. GPIO İzin Hatası
```bash
# Kullanıcı gpio grubunda mı?
groups pi

# Yoksa ekle
sudo usermod -a -G gpio pi
```

#### 4. Web Interface Açılmıyor
```bash
# Port dinleniyor mu?
netstat -tlnp | grep 8080

# Firewall kontrolü
sudo ufw status

# Service durumu
sudo systemctl status oba-robot.service
```

---

## 📱 UZAKTAN ERİŞİM (Opsiyonel)

### SSH Tunnel ile Güvenli Erişim
```bash
# Local makinedan
ssh -L 8080:localhost:8080 pi@[raspberry-pi-ip]

# Artık localhost:8080'den erişebilirsin
```

### VPN Setup (İleri Seviye)
```bash
# WireGuard kurulumu
sudo apt install wireguard -y

# Konfigürasyon dosyası oluştur
sudo nano /etc/wireguard/wg0.conf
```

---

## 🎉 TEBRIKLER!

OBA Robot artık Raspberry Pi'de production-ready olarak çalışıyor! 🚀

**Yararlı Komutlar:**
```bash
oba-status        # Sistem durumu
oba-logs error    # Hata logları
oba-start --debug # Debug modu
oba-stop          # Güvenli durdurma
oba-clean         # Temizlik
```

**Web Interface:** http://[raspberry-pi-ip]:8080

Bu rehber ile robot'un %99.9 uptime ile çalışması beklenir! 💪
