#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web sunucusu test scripti
Hacı Abi'nin web arayüzünü test etmek için
"""

# Proje klasörünü Python path'ine ekle
import os
import sys
import threading
import time
from datetime import datetime

# Proje klasörünü Python path'ine ekle
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from web.web_server import WebArayuz

project_root = os.path.dirname(__file__)
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

# Web arayüzü import'u


class MockRobot:
    """Mock robot sınıfı - test için"""

    def __init__(self):
        self.durum = "idle"
        self.battery_level = 85
        self.position = {"x": 10.5, "y": 8.2, "theta": 1.57}

    def gorev_baslat(self):
        print("🚀 Görev başlatıldı!")
        self.durum = "working"

    def gorev_durdur(self):
        print("⏹️ Görev durduruldu!")
        self.durum = "idle"

    def acil_durdur(self):
        print("🚨 ACİL DURDURMA!")
        self.durum = "emergency_stop"


def fake_robot_data():
    """Fake robot verisi üret"""
    return {
        "timestamp": datetime.now().isoformat(),
        "durum_bilgisi": {
            "durum": "idle",
            "gorev_ilerleme": 0
        },
        "sensor_data": {
            "gps": {
                "latitude": 41.0082,
                "longitude": 28.9784,
                "satellites": 8,
                "fix_quality": 3
            },
            "imu": {
                "roll": 0.1,
                "pitch": 0.05,
                "yaw": 45.0,
                "temperature": 25.6
            },
            "batarya": {
                "voltage": 12.4,
                "current": 1.2,
                "level": 85,
                "power": 14.88
            }
        },
        "konum_bilgisi": {
            "x": 10.5,
            "y": 8.2,
            "theta": 1.57
        },
        "motor_durumu": {
            "hizlar": {
                "sol": 0,
                "sag": 0
            },
            "fircalar": {
                "ana": False,
                "yan_sol": False,
                "yan_sag": False
            },
            "fan": False
        }
    }


def update_robot_data(web_arayuz):
    """Robot verilerini periyodik olarak güncelle"""
    while True:
        try:
            robot_data = fake_robot_data()
            web_arayuz.robot_data_guncelle(robot_data)
            time.sleep(2)  # 2 saniyede bir güncelle
        except Exception as e:
            print(f"❌ Veri güncelleme hatası: {e}")
            time.sleep(5)


def main():
    """Ana fonksiyon"""
    print("🌐 OBA Web Arayüzü Test Başlatılıyor...")
    print("=" * 50)

    # Mock robot oluştur
    robot = MockRobot()

    # Web konfigürasyonu
    web_config = {
        'secret_key': 'test_secret_key_2024',
        'debug': True
    }

    # Web arayüzü oluştur
    web_arayuz = WebArayuz(robot, web_config)

    # Arka planda veri güncelleme thread'i başlat
    data_thread = threading.Thread(
        target=update_robot_data,
        args=(web_arayuz,),
        daemon=True
    )
    data_thread.start()

    print("🎯 Web sunucusu başlatılıyor...")
    print("📱 Tarayıcınızda şu adresleri açın:")
    print("   • http://localhost:5000")
    print("   • http://0.0.0.0:5000")
    print("   • http://127.0.0.1:5000")
    print()
    print("⚠️  Durdurmak için Ctrl+C")
    print("=" * 50)

    try:
        # Web sunucusunu başlat
        web_arayuz.run(host='0.0.0.0', port=5000, debug=True)
    except KeyboardInterrupt:
        print("\n🛑 Web sunucusu durduruldu!")
    except Exception as e:
        print(f"\n❌ Web sunucusu hatası: {e}")


if __name__ == "__main__":
    main()
