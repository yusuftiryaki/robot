"""
🔧 Motor Kontrolcü Factory - HAL Pattern Kullanımı
Hacı Abi'nin motor kontrolcü factory'si!

Bu modül, environment'a göre doğru HAL implementasyonunu seçer
ve motor kontrolcüyü proper şekilde başlatır.
"""

import logging
from typing import Any, Dict

from .hal.hardware import GercekHardwareFactory
from .hal.interfaces import HardwareFactory
from .hal.simulation import SimulasyonHardwareFactory
from .motor_kontrolcu import MotorKontrolcu


class MotorKontrolcuFactory:
    """
    Motor kontrolcü fabrikası

    Environment manager'a göre doğru HAL implementasyonunu seçer.
    """

    def __init__(self, environment_manager):
        self.logger = logging.getLogger("MotorKontrolcuFactory")
        self.environment_manager = environment_manager
        self.is_simulation = environment_manager.is_simulation_mode

        # HAL Factory'yi seç
        if self.is_simulation:
            self.hal_factory: HardwareFactory = SimulasyonHardwareFactory()
            self.logger.info("🎮 Simülasyon HAL factory seçildi")
        else:
            self.hal_factory: HardwareFactory = GercekHardwareFactory()
            self.logger.info("⚙️ Gerçek donanım HAL factory seçildi")

    def motor_kontrolcu_olustur(self, motor_config: Dict[str, Any]) -> MotorKontrolcu:
        """
        Motor kontrolcü oluştur

        Args:
            motor_config: Motor konfigürasyon ayarları

        Returns:
            MotorKontrolcu: HAL pattern kullanaran motor kontrolcü
        """
        try:
            # HAL implementasyonunu oluştur
            motor_hal = self.hal_factory.motor_olustur(motor_config)

            # Motor kontrolcüyü oluştur
            motor_kontrolcu = MotorKontrolcu(motor_hal, motor_config)

            self.logger.info(f"✅ Motor kontrolcü oluşturuldu (Mod: {'Simülasyon' if self.is_simulation else 'Gerçek'})")
            return motor_kontrolcu

        except Exception as e:
            self.logger.error(f"❌ Motor kontrolcü oluşturma hatası: {e}")
            raise


# Convenience function for easy usage
def create_motor_kontrolcu(environment_manager, motor_config: Dict[str, Any]) -> MotorKontrolcu:
    """
    Motor kontrolcü oluşturmak için kolaylık fonksiyonu

    Args:
        environment_manager: Ortam yöneticisi
        motor_config: Motor konfigürasyonu

    Returns:
        MotorKontrolcu: Hazır motor kontrolcü
    """
    factory = MotorKontrolcuFactory(environment_manager)
    return factory.motor_kontrolcu_olustur(motor_config)
