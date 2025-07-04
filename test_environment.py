#!/usr/bin/env python3
"""
🚀 Smart Environment Test
Ortam Tespit ve Konfigürasyon Testi
"""

import os
import sys
from pathlib import Path

# Proje path'ini ekle
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))


def test_environment_detection():
    """Ortam tespiti test et"""
    print("🔍 ORTAM TESPİT TESİ")
    print("=" * 40)

    try:
        from core.environment_manager import EnvironmentManager

        # Environment manager oluştur
        env_manager = EnvironmentManager()

        # Ortam bilgilerini yazdır
        env_manager.print_environment_summary()

        return True
    except Exception as e:
        print(f"❌ Ortam tespit hatası: {e}")
        return False


def test_config_loading():
    """Konfigürasyon yükleme test et"""
    print("\n⚙️ KONFİGÜRASYON TESİ")
    print("=" * 40)

    try:
        from core.smart_config import SmartConfigManager

        # Config manager oluştur
        config_manager = SmartConfigManager()

        # Konfigürasyonu yükle
        config = config_manager.load_config()

        # Özet bilgileri
        summary = config_manager.get_config_summary()
        print(f"🌍 Ortam: {summary['environment']}")
        print(f"🎮 Simülasyon: {summary['simulation_mode']}")
        print(f"🚗 Motor Tipi: {summary['motor_type']}")
        print(f"📷 Kamera: {summary['camera_enabled']}")
        print(f"🌐 Web Port: {summary['web_port']}")
        print(f"📊 Log Level: {summary['log_level']}")

        return True
    except Exception as e:
        print(f"❌ Konfigürasyon test hatası: {e}")
        return False


def test_smart_requirements():
    """Akıllı requirements test et"""
    print("\n📦 PAKET TESİ")
    print("=" * 40)

    try:
        # Temel paketleri test et
        import numpy as np
        print(f"✅ NumPy: {np.__version__}")

        import cv2
        print(f"✅ OpenCV: {cv2.__version__}")

        import flask
        print(f"✅ Flask: {flask.__version__}")

        import yaml
        print(f"✅ PyYAML: {yaml.__version__}")

        # Ortam bazlı paket testi
        try:
            import RPi.GPIO as GPIO
            print("✅ RPi.GPIO: Mevcut (Raspberry Pi)")
        except ImportError:
            print("⚪ RPi.GPIO: Mevcut değil (Development ortamı)")

        return True
    except Exception as e:
        print(f"❌ Paket test hatası: {e}")
        return False


def main():
    """Ana test fonksiyonu"""
    print("🧪 OBA ROBOT ORTAM TESİ")
    print("=" * 50)

    tests = [
        ("Ortam Tespiti", test_environment_detection),
        ("Konfigürasyon", test_config_loading),
        ("Paket Kontrolü", test_smart_requirements)
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test hatası: {e}")
            results.append((test_name, False))

    # Sonuçları özetle
    print("\n" + "=" * 50)
    print("📊 TEST SONUÇLARI")
    print("=" * 50)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ BAŞARILI" if result else "❌ BAŞARISIZ"
        print(f"{test_name}: {status}")
        if result:
            passed += 1

    print(f"\n🎯 Genel Sonuç: {passed}/{total} test geçti")

    if passed == total:
        print("🎉 Tüm testler başarılı! Robot hazır.")
        return 0
    else:
        print("😞 Bazı testler başarısız! Lütfen hataları giderin.")
        return 1


if __name__ == "__main__":
    exit(main())
