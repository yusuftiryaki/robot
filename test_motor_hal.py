#!/usr/bin/env python3
"""
🧪 Motor Kontrolcü Test - HAL Pattern Doğrulama
Hacı Abi'nin yeni motor kontrolcü test scripti!

Bu script, HAL pattern refaktöring'inden sonra motor kontrolcünün
doğru çalıştığını test eder.
"""

import asyncio
import logging
import sys
import time
from unittest.mock import Mock

# Add src to path for imports
sys.path.append('/workspaces/oba/src')

from hardware.motor_factory import create_motor_kontrolcu


# Mock environment manager
class MockEnvironmentManager:
    def __init__(self, simulation_mode: bool = True):
        self.is_simulation_mode = simulation_mode


async def test_motor_kontrolcu():
    """Motor kontrolcü test fonksiyonu"""

    # Logging setup
    logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger("MotorTest")

    logger.info("🧪 Motor kontrolcü HAL pattern testi başlıyor...")

    # Mock config
    motor_config = {
        "wheel_diameter": 0.065,
        "wheel_base": 0.235,
        "max_linear_speed": 0.5,
        "encoder_pulses_per_rev": 360,
        "wheels": {
            "left": {"pin_a": 18, "pin_b": 19, "pwm_pin": 12},
            "right": {"pin_a": 20, "pin_b": 21, "pwm_pin": 13}
        },
        "brushes": {
            "side_left": {"pin_a": 22, "pin_b": 23},
            "side_right": {"pin_a": 24, "pin_b": 25}
        },
        "main_systems": {
            "brush": {"pin_a": 26, "pin_b": 27},
            "fan": {"pin_a": 5, "pin_b": 6}
        }
    }

    # Environment manager (simülasyon modu)
    env_manager = MockEnvironmentManager(simulation_mode=True)

    try:
        # Motor kontrolcü oluştur
        logger.info("📦 Motor kontrolcü oluşturuluyor...")
        motor_kontrolcu = create_motor_kontrolcu(env_manager, motor_config)

        # Başlat
        logger.info("🚀 Motor kontrolcü başlatılıyor...")
        success = await motor_kontrolcu.baslat()

        if not success:
            logger.error("❌ Motor kontrolcü başlatılamadı!")
            return False

        # Sağlık kontrolü
        saglik = motor_kontrolcu.saglikli_mi()
        logger.info(f"💊 Motor sağlık durumu: {saglik}")

        # Motor durumu kontrol et
        durum = motor_kontrolcu.motor_durumu_al()
        logger.info(f"📊 İlk motor durumu: {durum}")

        # Test 1: Hareket komutları
        logger.info("🏃 Test 1: Hareket komutları...")

        # İleri hareket
        await motor_kontrolcu.hareket_et(0.2, 0.0)  # 0.2 m/s ileri
        await asyncio.sleep(1)

        # Sağa dönüş
        await motor_kontrolcu.hareket_et(0.0, 0.5)  # 0.5 rad/s sağa
        await asyncio.sleep(1)

        # Dur
        await motor_kontrolcu.hareket_et(0.0, 0.0)
        await asyncio.sleep(0.5)

        # Test 2: Fırça kontrolü
        logger.info("🧹 Test 2: Fırça kontrolü...")
        await motor_kontrolcu.firca_kontrol(ana=True, sol=True, sag=False)
        await asyncio.sleep(1)

        await motor_kontrolcu.firca_kontrol(ana=False, sol=False, sag=True)
        await asyncio.sleep(1)

        # Test 3: Fan kontrolü
        logger.info("🌪️ Test 3: Fan kontrolü...")
        await motor_kontrolcu.fan_kontrol(True)
        await asyncio.sleep(1)

        await motor_kontrolcu.fan_kontrol(False)
        await asyncio.sleep(0.5)

        # Test 4: Acil durdurma
        logger.info("🚨 Test 4: Acil durdurma...")
        await motor_kontrolcu.hareket_et(0.3, 0.2)  # Hareket halindeyken
        await asyncio.sleep(0.2)
        await motor_kontrolcu.acil_durdur()

        # Final durum
        final_durum = motor_kontrolcu.motor_durumu_al()
        logger.info(f"🏁 Final motor durumu: {final_durum}")

        # Temizlik
        logger.info("🧹 Temizlik yapılıyor...")
        await motor_kontrolcu.temizle()

        logger.info("✅ Tüm testler başarılı!")
        return True

    except Exception as e:
        logger.error(f"❌ Test hatası: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = asyncio.run(test_motor_kontrolcu())
    exit(0 if success else 1)
    exit(0 if success else 1)
