"""
🏭 Kamera Factory - HAL Pattern Implementation
Hacı Abi'nin temiz kamera factory'si!

Bu factory, environment'a göre doğru kamera implementasyonunu seçer.
SOLID prensiplerine uygun, temiz factory pattern.
"""

import logging
from typing import Any, Dict

from .fiziksel_kamera import FizikselKamera
from .kamera_interface import KameraInterface
from .simulasyon_kamerasi import SimulasyonKamerasi


class KameraFactory:
    """
    🏭 Kamera Factory Class

    Environment'a göre doğru kamera implementasyonunu oluşturur.
    Simülasyon/Fiziksel kamera arasında otomatik seçim yapar.
    """

    @staticmethod
    def create_kamera(config: Dict[str, Any]) -> KameraInterface:
        """
        🎯 Kamera implementasyonu oluştur

        Args:
            config: Kamera konfigürasyonu

        Returns:
            KameraInterface: Doğru kamera implementasyonu

        Raises:
            ValueError: Desteklenmeyen kamera tipi
        """
        logger = logging.getLogger("KameraFactory")

        # Config'ten kamera tipini al
        kamera_tipi = config.get("type", "auto")

        # Auto detection
        if kamera_tipi == "auto":
            kamera_tipi = KameraFactory._detect_kamera_tipi()
            logger.info(f"🔍 Otomatik tespit: {kamera_tipi} kamera")

        # Kamera implementasyonunu oluştur
        if kamera_tipi == "simulation":
            logger.info("🎮 Simülasyon kamerası oluşturuluyor...")
            return SimulasyonKamerasi(config)

        elif kamera_tipi == "hardware":
            logger.info("📷 Fiziksel kamera oluşturuluyor...")
            return FizikselKamera(config)

        else:
            raise ValueError(f"❌ Desteklenmeyen kamera tipi: {kamera_tipi}")

    @staticmethod
    def _detect_kamera_tipi() -> str:
        """
        🔍 Otomatik kamera tipi tespiti

        Returns:
            str: "simulation" veya "hardware"
        """
        try:
            # Picamera2 availability kontrolü
            import importlib.util

            # Picamera2 modülü mevcut mu?
            picamera2_spec = importlib.util.find_spec("picamera2")
            if picamera2_spec is None:
                return "simulation"

            # Kamera aygıtı kontrolü
            import os
            if os.path.exists("/dev/video0"):
                return "hardware"
            else:
                return "simulation"

        except Exception:
            # Herhangi bir hata durumunda simülasyon
            return "simulation"

    @staticmethod
    def get_available_kamera_tipleri() -> list:
        """
        📋 Mevcut kamera tiplerini listele

        Returns:
            list: Desteklenen kamera tipleri
        """
        available = ["simulation"]  # Her zaman mevcut

        try:
            import importlib.util
            import os

            # Picamera2 modülü mevcut mu?
            picamera2_spec = importlib.util.find_spec("picamera2")
            if picamera2_spec is not None and os.path.exists("/dev/video0"):
                available.append("hardware")
        except Exception:
            pass

        return available

    @staticmethod
    def validate_config(config: Dict[str, Any]) -> bool:
        """
        ✅ Kamera config'ini doğrula

        Args:
            config: Kontrol edilecek konfigürasyon

        Returns:
            bool: Config geçerli mi?
        """
        logger = logging.getLogger("KameraFactory")

        try:
            # Zorunlu alanlar
            required_fields = ["width", "height", "fps"]
            for field in required_fields:
                if field not in config:
                    logger.error(f"❌ Config'te eksik alan: {field}")
                    return False

            # Değer kontrolleri
            if config["width"] <= 0 or config["height"] <= 0:
                logger.error("❌ Geçersiz çözünürlük değerleri")
                return False

            if config["fps"] <= 0:
                logger.error("❌ Geçersiz FPS değeri")
                return False

            # Kamera tipi kontrolü
            kamera_tipi = config.get("type", "auto")
            if kamera_tipi not in ["auto", "simulation", "hardware"]:
                logger.error(f"❌ Geçersiz kamera tipi: {kamera_tipi}")
                return False

            logger.info("✅ Kamera config geçerli")
            return True

        except Exception as e:
            logger.error(f"❌ Config doğrulama hatası: {e}")
            return False
