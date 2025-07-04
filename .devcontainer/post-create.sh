#!/bin/bash

echo "🤖 Hacı Abi'nin Bahçe Robotu Development Environment Kuruluyor..."

# Python paketlerini yükle
pip install --upgrade pip

# Requirements.txt'ten paketleri yükle (tek kaynak, düzenli yaklaşım)
echo "📦 Requirements.txt'ten paketler yükleniyor..."
pip install -r requirements.txt

echo "✅ Paketler yüklendi!"

# Simulator data klasörünü oluştur
mkdir -p /workspace/simulator_data
mkdir -p /workspace/logs

# Test verilerini oluştur
echo "🧪 Test verilerini oluşturuyorum..."
python3 << 'EOF'
import json
import numpy as np
from datetime import datetime, timedelta
import os

# Simülasyon GPS koordinatları (Ankara yakınlarında)
base_lat = 39.9334
base_lon = 32.8597

# Test GPS rotası oluştur
test_route = []
for i in range(100):
    lat = base_lat + (np.random.random() - 0.5) * 0.001
    lon = base_lon + (np.random.random() - 0.5) * 0.001
    test_route.append({"lat": lat, "lon": lon, "timestamp": datetime.now().isoformat()})

# Simulator verileri
simulator_data = {
    "test_route": test_route,
    "motor_configs": {
        "left_wheel": {"pin_a": 18, "pin_b": 19, "encoder_pin": 20},
        "right_wheel": {"pin_a": 21, "pin_b": 22, "encoder_pin": 23},
        "main_brush": {"pin_a": 24, "pin_b": 25},
        "side_brush_left": {"pin_a": 26, "pin_b": 27},
        "side_brush_right": {"pin_a": 5, "pin_b": 6},
        "fan": {"pin_a": 12, "pin_b": 13}
    },
    "sensor_configs": {
        "mpu6050_i2c": {"address": "0x68", "sda": 2, "scl": 3},
        "gps_uart": {"tx": 14, "rx": 15},
        "camera": {"port": 0},
        "front_bumper": {"pin": 16},
        "ina219": {"address": "0x40", "sda": 2, "scl": 3}
    },
    "simulation_values": {
        "battery_voltage": 12.5,
        "battery_current": 1.2,
        "gps_coordinates": {"lat": base_lat, "lon": base_lon},
        "imu_orientation": {"roll": 0, "pitch": 0, "yaw": 0},
        "encoder_counts": {"left": 0, "right": 0}
    }
}

# Dosyaya kaydet
with open('/workspace/simulator_data/config.json', 'w') as f:
    json.dump(simulator_data, f, indent=2)

print("✅ Simulator data hazırlandı!")
EOF

echo "🔧 OBA Helper Scripts'lerini yükleniyor..."

# Script'leri executable yap
chmod +x scripts/oba-*

# Alias'ları hem .bashrc hem .zshrc'ye ekle (shell bağımsız)
echo "" >> ~/.bashrc
echo "# OBA Robot Helper Scripts" >> ~/.bashrc
echo "alias oba-help='/workspaces/oba/scripts/oba-help'" >> ~/.bashrc
echo "alias oba-start='/workspaces/oba/scripts/oba-start'" >> ~/.bashrc
echo "alias oba-test='/workspaces/oba/scripts/oba-test'" >> ~/.bashrc
echo "alias oba-status='/workspaces/oba/scripts/oba-status'" >> ~/.bashrc
echo "alias oba-logs='/workspaces/oba/scripts/oba-logs'" >> ~/.bashrc
echo "alias oba-clean='/workspaces/oba/scripts/oba-clean'" >> ~/.bashrc

# Zsh için de aynı alias'ları ekle
echo "" >> ~/.zshrc
echo "# OBA Robot Helper Scripts" >> ~/.zshrc
echo "alias oba-help='/workspaces/oba/scripts/oba-help'" >> ~/.zshrc
echo "alias oba-start='/workspaces/oba/scripts/oba-start'" >> ~/.zshrc
echo "alias oba-test='/workspaces/oba/scripts/oba-test'" >> ~/.zshrc
echo "alias oba-status='/workspaces/oba/scripts/oba-status'" >> ~/.zshrc
echo "alias oba-logs='/workspaces/oba/scripts/oba-logs'" >> ~/.zshrc
echo "alias oba-clean='/workspaces/oba/scripts/oba-clean'" >> ~/.zshrc

# Mevcut session için alias'ları aktif et (hangi shell olursa olsun)
source ~/.bashrc 2>/dev/null || true
source ~/.zshrc 2>/dev/null || true

echo "✅ OBA Helper Scripts yüklendi!"
echo "   oba-help    - Yardım ve komut listesi"
echo "   oba-start   - Robot başlat"
echo "   oba-test    - Test suite çalıştır"
echo "   oba-status  - Robot durumu kontrol"
echo "   oba-logs    - Log dosyalarını görüntüle"
echo "   oba-clean   - Geçici dosyaları temizle"

echo "🎉 Development environment hazır! Hacı Abi işi bitirdi."
echo "📝 Şu komutları terminalde kullanabilirsiniz:"
echo "   oba-help              # Tüm komutları göster"
echo "   oba-start sim debug   # Simülasyon modunda başlat"
echo "   oba-test              # Testleri çalıştır"
echo "   oba-status            # Durum kontrol"
