# 🌱 Otonom Bahçe Asistanı (OBA) - Mi Vacuum Essential Dönüşümü

Bu proje, Mi Vacuum Essential Robot'un şasisini kullanarak Raspberry Pi 4 tabanlı otonom bir bahçe asistanı oluşturmayı amaçlıyor. OBA, ataletli seyrüsefer, gelişmiş odometri, otonom görev yönetimi ve web tabanlı uzaktan kontrol özelliklerine sahiptir.

## 🚀 Hızlı Başlangıç

### Dev Container ile Geliştirme (Önerilen)
```bash
# 1. Projeyi VS Code ile aç
code .

# 2. "Reopen in Container" seçeneğini seç
# Container otomatik olarak tüm bağımlılıkları yükleyecek ve
# oba-* komutlarını sistem PATH'ine ekleyecek

# 3. Helper komutları kullan
oba-help                     # Tüm komutları göster
oba-start --debug            # Debug modunda test et
oba-test                     # Testleri çalıştır
oba-status                   # Sistem durumunu kontrol et

# 4. Yeni deployment komutları (Docker ile)
oba-deploy 192.168.1.100     # Pi'ye otomatik deployment
oba-quick-deploy             # İnteraktif deployment sihirbazı
oba-test-env start           # Docker test ortamı başlat
oba-test-deployment          # Deployment doğrulama

# 5. VS Code otomatik olarak:
# - Docker desteği (Docker socket mounting ile)
# - Deployment test ortamı (Docker tabanlı Pi simülasyonu)
# - Önerilen ekstensionları yükleyecek
# - Debug konfigürasyonlarını hazırlayacak
# - Python environment'ı ayarlayacek
```

### 🚀 Otomatik Raspberry Pi Deployment (Önerilen)
```bash
# 1. Hızlı kurulum (interaktif)
oba-quick-deploy

# 2. Komut satırından
oba-deploy --ip 192.168.1.100 --password mypassword

# 3. Gelişmiş seçenekler
oba-deploy --ip 192.168.1.100 --password mypassword \
           --skip-system-update --verbose

# 4. Deployment testi
oba-test-deployment --ip 192.168.1.100
```

### 📱 Manuel Raspberry Pi Kurulumu
```bash
# 1. Raspberry Pi OS kurulumu
# Hardware bağlantı diyagramı: docs/hardware/wiring_diagram.md
# Montaj rehberi: docs/hardware/assembly_guide.md

# 2. Proje klonlama
git clone <repository_url>
cd bahce_robotu

# 3. Python environment kurulumu
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Sistem testleri
python tests/test_runner.py --module hardware

# 5. Robot başlatma
python main.py --debug
```

## 📁 Proje Yapısı

```
bahce_robotu/
├── main.py                 # Ana başlatma scripti
├── requirements.txt        # Python bağımlılıkları
├── config/                 # Konfigürasyon dosyaları
│   └── robot_config.yaml   # Robot ayarları
├── src/                    # Ana kaynak kodları
│   ├── core/              # Çekirdek robot sistemi
│   │   ├── robot.py       # Ana robot sınıfı
│   │   └── guvenlik_sistemi.py # Güvenlik katmanları
│   ├── hardware/          # Donanım kontrol modülleri
│   │   ├── motor_kontrolcu.py  # Motor sürücüleri
│   │   └── sensor_okuyucu.py   # Sensör okuma
│   ├── navigation/        # Navigasyon ve haritalama
│   │   ├── konum_takipci.py    # Odometri ve Kalman
│   │   └── rota_planlayici.py  # A* ve biçerdöver
│   ├── vision/            # Kamera ve görüntü işleme
│   │   └── kamera_islemci.py   # Engel tanıma
│   ├── ai/                # Yapay zeka ve karar verme
│   │   └── karar_verici.py     # Fuzzy logic
│   └── web/               # Web arayüzü
│       ├── web_server.py       # Flask backend
│       └── templates/          # HTML şablonları
├── tests/                 # Test dosyaları
│   ├── test_runner.py     # Ana test runner
│   ├── test_hardware.py   # Donanım testleri
│   ├── test_navigation.py # Navigation testleri
│   └── test_utils.py      # Test yardımcıları
├── docs/                  # Dokümantasyon
│   ├── hardware/          # Donanım dokümantasyonu
│   │   ├── wiring_diagram.md   # Bağlantı şemaları
│   │   └── assembly_guide.md   # Montaj rehberi
│   └── user_manual.md     # Kullanım kılavuzu
├── logs/                  # Log dosyaları
└── .devcontainer/         # Dev container ayarları
    ├── devcontainer.json  # Container konfigürasyonu
    └── post-create.sh     # Kurulum scripti
```

## 🛠 Özellikler

### ✅ Tamamlanan Özellikler
- **Ataletli Seyrüsefer**: Encoder + IMU + GPS füzyonu ile hassas konum takibi
- **Gelişmiş Odometri**: Kalman filtresi ile sensör verilerinin birleştirilmesi
- **Otonom Görev Yönetimi**: Biçerdöver metodu ile sistematik alan tarama
- **Otonom Şarj Sistemi**: Batarya izleme ve otomatik şarj istasyonu docking
- **Güvenlik Katmanları**: Acil stop, tampon sensörleri, eğim koruması
- **Kamera Tabanlı Algılama**: OpenCV ile engel tanıma ve encoder destekli hassas hareket
- **Web Arayüzü**: Mobile-first tasarımla uzaktan kontrol ve izleme
- **Dev Container Ortamı**: Hızlı geliştirme için hazır geliştirme ortamı

### 🚧 Geliştirilmekte Olan Özellikler
- **OpenVLA Entegrasyonu**: İleri seviye AI görüntü analizi
- **Gelişmiş Haritalama**: SLAM algoritması ile dinamik harita oluşturma
- **Makine Öğrenmesi**: Görev optimizasyonu için ML modelleri

## 📱 Web Arayüzü Özellikleri

OBA, modern ve responsive web arayüzüne sahip:

### 🎮 Kontrol Özellikleri
- **Canlı Kamera**: 1920x1080 @ 30fps video stream
- **Manuel Kontrol**: Joystick benzeri dokunmatik kontroller
- **Görev Yönetimi**: Alan tarama, nokta navigasyon, şarj görevleri
- **Gerçek Zamanlı Durum**: Batarya, GPS, sensör verileri

### 📊 İzleme Özellikleri
- **Canlı Harita**: Robot konumu ve rota görüntüleme
- **Performans Metrikleri**: Hız, verimlilik, enerji kullanımı
- **Log Görüntüleme**: Detaylı sistem logları
- **Hata Yönetimi**: Uyarılar ve sorun giderme rehberi

### 🔧 Ayar Özellikleri
- **Robot Parametreleri**: Hız, hassasiyet, güvenlik ayarları
- **Görev Konfigürasyonu**: Biçme yüksekliği, kaplama oranı
- **Ağ Ayarları**: Wi-Fi, uzaktan erişim
- **Bakım Zamanları**: Otomatik bakım hatırlatıcıları
- Manuel kontrol paneli
- Görev planlama arayüzü

## 🔧 Konfigürasyon

Ana konfigürasyon dosyası: `config/robot_config.yaml`

Simulator verileri: `.devcontainer/simulator_data/config.json`

## 🧪 Test Sistemi

Kapsamlı test suite ile kod kalitesi sağlanmaktadır:

### Test Komutları
```bash
# Tüm testleri çalıştır
python tests/test_runner.py

# Belirli modül testleri
python tests/test_runner.py --module hardware
python tests/test_runner.py --module navigation

# Detaylı çıktı ile
python tests/test_runner.py --verbose
```

### Test Kapsamı
- **Donanım Testleri**: Sensör okuma, motor kontrolü, GPIO testleri
- **Navigation Testleri**: Konum takibi, rota planlama, kinematik testleri
- **Sistem Testleri**: Konfigürasyon, dosya sistemi, bellek kullanımı
- **Entegrasyon Testleri**: Modül arası iletişim, web arayüzü

## 📚 Dokümantasyon

### Hardware Dokümantasyonu
- **[Bağlantı Diyagramları](docs/hardware/wiring_diagram.md)**: Detaylı elektriksel şemalar
- **[Montaj Rehberi](docs/hardware/assembly_guide.md)**: Adım adım kurulum talimatları

### Kullanım Kılavuzları
- **[User Manual](docs/user_manual.md)**: Kapsamlı kullanım kılavuzu
- **[API Dokümantasyonu](docs/api.md)**: Web API referansı
- **[Troubleshooting](docs/troubleshooting.md)**: Sorun giderme rehberi

## 🔧 Komut Satırı Araçları

OBA, geliştirme ve kullanım kolaylığı için bir dizi komut satırı aracı sunar:

### Ana Komutlar
```bash
oba-help                     # Tüm komutları ve örnekleri göster
oba-start                    # Robotu normal modda başlat
oba-start --web-only         # Sadece Web modunda başlat
oba-start --debug            # Debug modunda başlat
oba-stop                     # Robotu güvenli bir şekilde durdur
oba-stop --force             # Robotu zorla durdur
oba-status                   # Robot durumunu kontrol et
```

### Test ve Geliştirme
```bash
oba-test                     # Tüm testleri çalıştır
oba-test hardware            # Donanım testleri
oba-test navigation          # Navigation testleri
oba-test quick               # Hızlı testler
```

### Monitoring ve Bakım
```bash
oba-logs                     # Tüm logları göster
oba-logs error               # Sadece hataları göster
oba-logs follow              # Canlı log takibi
oba-clean                    # Geçici dosyaları temizle
oba-clean cache              # Cache dosyalarını temizle
oba-clean all                # Tam temizlik
```

### Durum Kontrolleri
```bash
oba-status                   # Genel sistem durumu
oba-status battery           # Batarya durumu
oba-status gps               # GPS durumu
oba-status sensors           # Sensör durumu
oba-status network           # Ağ durumu
```

> **💡 İpucu**: Tüm komutlar `--help` parametresi ile detaylı yardım bilgilerini gösterir.

## ⚙️ Kurulum Detayları

### Sistem Gereksinimleri
- **Hardware**: Raspberry Pi 4 (4GB RAM önerilir)
- **OS**: Raspberry Pi OS (Bullseye veya sonrası)
- **Python**: 3.9+ (3.10 önerilir)
- **Disk Alanı**: 8GB serbest alan

### Bağımlılıklar
```bash
# Ana Python paketleri
pip install flask flask-socketio opencv-python numpy scipy

# Raspberry Pi özgü paketleri
pip install RPi.GPIO gpiozero adafruit-circuitpython-motor

# Opsiyonel AI paketleri
pip install tensorflow-lite torch torchvision
```

### Konfigürasyon
```bash
# GPIO ve I2C aktifleştirme
sudo raspi-config
# → Interface Options → I2C → Enable
# → Interface Options → Camera → Enable

# Systemd service kurulumu
sudo cp config/bahce-robotu.service /etc/systemd/system/
sudo systemctl enable bahce-robotu.service
```

## 🔧 Geliştirme Rehberi

### Katkıda Bulunma
1. Repository'yi fork edin
2. Feature branch oluşturun (`git checkout -b feature/yeni-ozellik`)
3. Değişikliklerinizi commit edin (`git commit -am 'Yeni özellik eklendi'`)
4. Branch'i push edin (`git push origin feature/yeni-ozellik`)
5. Pull Request oluşturun

### Kod Standartları
- **PEP 8**: Python kod standardı
- **Type Hints**: Tüm fonksiyonlarda tip belirteci
- **Docstrings**: Sınıf ve fonksiyon dokümantasyonu
- **Test Coverage**: %80+ test kapsamı hedefi

### Debug Modu
```bash
# Detaylı debug çıktısı
python main.py --debug

# Sadece belirli modül debug
export DEBUG_MODULES="navigation,sensors"
python main.py --debug
```

## 🚨 Güvenlik ve Sorumluluk

⚠️ **Önemli Güvenlik Uyarıları**:
- Robot çalışırken alanda insan veya hayvan olmamasını sağlayın
- Acil stop butonunun her zaman erişilebilir olduğundan emin olun
- Batarya güvenlik prosedürlerini takip edin
- Su geçirmez olmayan parçaları yağmurdan koruyun

📋 **Sorumluluk Reddi**: Bu proje eğitim ve araştırma amaçlıdır. Kullanımından kaynaklanan hasar ve zararlardan geliştirici sorumlu değildir.

## 📞 Destek ve İletişim

### Teknik Destek
- **GitHub Issues**: Bug raporları ve özellik istekleri
- **Discussions**: Genel sorular ve tartışmalar
- **Email**: support@bahcerobotu.com

### Topluluk
- **Telegram**: @BahceRobotuTR
- **Discord**: [OBA Geliştirici Topluluğu](link)
- **Forum**: [community.bahcerobotu.com](link)

## 📄 Lisans

Bu proje MIT lisansı altında yayınlanmıştır. Detaylar için [LICENSE](LICENSE) dosyasına bakınız.

---

**🤖 İyi robotlar, iyi bahçeler!** 🌱
