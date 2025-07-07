# 🐳 Docker Setup ve Deployment Test Ortamı

Bu dokümantasyon, OBA projesinin Docker tabanlı test ve deployment altyapısını açıklar.

## 🚀 Dev Container Docker Desteği

### Docker Socket Mounting

Dev container Docker desteği ile donatılmıştır ve Docker socket mounting kullanır:

```json
{
  "features": {
    "ghcr.io/devcontainers/features/docker-outside-of-docker:1": {
      "version": "latest",
      "enableNonRootDocker": "true"
    }
  },
  "mounts": [
    "source=/var/run/docker.sock,target=/var/run/docker.sock,type=bind"
  ],
  "runArgs": [
    "--privileged"
  ]
}
```

### Dev Container Yeniden Build

Docker desteğinin aktif olması için dev container'ı yeniden build etmeniz gerekir:

1. **Command Palette** açın (`Ctrl+Shift+P`)
2. **"Dev Containers: Rebuild Container"** seçin
3. Container yeniden build edilecek ve Docker desteği aktif olacak

### Docker Test Etme

```bash
# Container rebuild sonrası Docker'ı test edin
docker --version
docker ps

# Test ortamını başlatın
oba-test-env start
```

## 🔧 Docker Test Ortamı

### Raspberry Pi Simülasyon Container'ı

`docker/Dockerfile.test-pi` dosyası Raspberry Pi ortamını simüle eder:

- **ARM64 simülasyonu** (debian:bookworm-slim)
- **SSH Server** (test deployment için)
- **Python ve pip** (OBA dependencies için)
- **Systemd** (service testing için)

### Test Ortamı Yönetimi

```bash
# Test ortamını başlat
oba-test-env start

# Test ortamında deployment test et
oba-test-env test

# Test ortamına SSH ile bağlan
oba-test-env ssh

# Test ortamı loglarını görüntüle
oba-test-env logs

# Test ortamını durdur ve temizle
oba-test-env clean
```

### Deployment Testing

```bash
# Local deployment test
oba-deploy localhost --port 2222

# Test environment'da doğrulama
oba-test-deployment --port 2222

# Interactive deployment test
oba-quick-deploy
```

## 🏗️ Docker Test Ortamı Özellikleri

### Simülasyon Kapsamı

- **SSH Access**: Real Pi gibi SSH bağlantısı
- **File Transfer**: rsync ve scp desteği
- **Python Environment**: venv ve pip desteği
- **Service Management**: systemd simülasyonu
- **Log Management**: Python logging simülasyonu

### Sınırlamalar

- **GPIO**: Gerçek GPIO pinleri yok (mock)
- **Sensors**: Sensor hardware simülasyonu
- **Camera**: USB camera simülasyonu
- **Motors**: PWM ve motor kontrol simülasyonu

## 📋 Komut Referansı

### Test Ortamı Komutları

```bash
oba-test-env start          # Ortamı başlat
oba-test-env stop           # Ortamı durdur
oba-test-env test           # Deployment test
oba-test-env validate       # Ortam doğrulama
oba-test-env ssh            # SSH bağlantısı
oba-test-env logs           # Container logları
oba-test-env shell          # Direct shell access
oba-test-env rebuild        # Container'ı yeniden build et
oba-test-env clean          # Tam temizlik
```

### Deployment Komutları

```bash
oba-deploy <target>         # Otomatik deployment
oba-quick-deploy            # İnteraktif deployment
oba-test-deployment         # Deployment doğrulama
```

## 🛠️ Troubleshooting

### Docker Permission Hatası

```bash
# Dev container'da Docker permissions
sudo usermod -aG docker $USER
sudo chmod 666 /var/run/docker.sock
```

### Container Build Hatası

```bash
# Dev container'ı yeniden build et
# Command Palette > "Dev Containers: Rebuild Container"

# Manual Docker build test
cd docker/
docker build -t oba-test-pi -f Dockerfile.test-pi .
```

### Port Conflict

```bash
# Port 2222 kullanımda ise
oba-test-env start --port 2223
oba-deploy localhost --port 2223
```

## 📖 İleri Seviye

### Custom Test Environment

Test ortamını özelleştirmek için `docker/Dockerfile.test-pi` dosyasını düzenleyebilirsiniz.

### Multiple Test Instances

```bash
# Farklı portlarda multiple test ortamları
oba-test-env start --port 2222 --name oba-test-1
oba-test-env start --port 2223 --name oba-test-2
```

### Development Workflow

1. **Local development** dev container'da
2. **Deployment test** Docker test ortamında
3. **Real hardware test** gerçek Raspberry Pi'de
4. **Production deployment** field robot'a

Bu sayede geliştirme döngüsünde hiç gerçek hardware'a dokunmadan deployment scriptlerinizi test edebilirsiniz! 🎯
