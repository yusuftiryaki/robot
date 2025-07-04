#!/usr/bin/env python3
"""
🚀 Smart Environment Test
Ortam Tespit ve Konfigürasyon Testi
"""

import os
import sys
from pathlib import Path

# Proje path'ini ekle
PROJECT_ROOT = Path(__file__).parent
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
        # Ortam tespiti yap
        from core.environment_manager import EnvironmentManager
        env_manager = EnvironmentManager()
        is_dev_container = env_manager.is_dev_container()
        is_raspberry_pi = env_manager.is_raspberry_pi()

        # Temel paketleri test et (her ortamda gerekli)
        import numpy as np
        print(f"✅ NumPy: {np.__version__}")

        import cv2
        print(f"✅ OpenCV: {cv2.__version__ if hasattr(cv2, '__version__') else 'Versiyon bilinmiyor'}")

        import flask
        print(f"✅ Flask: {flask.__version__}")

        import yaml
        print(f"✅ PyYAML: {yaml.__version__}")

        # Ortam bazlı paket testi
        if is_dev_container:
            # Dev container'da Raspberry Pi paketlerini test etme
            print("⚪ RPi.GPIO: Test atlandı (Dev container ortamı)")
            print("💡 Dev container ortamında Raspberry Pi paketleri test edilmez")
        elif is_raspberry_pi:
            # Raspberry Pi'da donanım paketlerini test et
            try:
                import RPi.GPIO as GPIO
                print("✅ RPi.GPIO: Mevcut ve çalışıyor")

                try:
                    import gpiozero
                    print("✅ gpiozero: Mevcut")
                except ImportError:
                    print("⚠️ gpiozero: Mevcut değil")

            except (ImportError, RuntimeError) as e:
                print(f"❌ RPi.GPIO: Hata - {e}")
                return False
        else:
            # Diğer ortamlarda uyarı ver
            print("⚪ RPi.GPIO: Test atlandı (Raspberry Pi değil)")

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
