"""
📷 Fiziksel Kamera Implementation
Hacı Abi'nin gerçek kamera interface'i!

Bu sınıf, Raspberry Pi kamerası ile gerçek görüntü işleme yapar.
HAL pattern ile temiz ayrım sağlar.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

import numpy as np

from .kamera_interface import KameraInterface


class FizikselKamera(KameraInterface):
    """
    📷 Fiziksel Kamera Implementation

    Raspberry Pi kamerası ile gerçek görüntü işleme.
    Picamera2 API'sini kullanır.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger("FizikselKamera")

        # Kamera parametreleri
        self.resolution = (
            config.get("width", 640),
            config.get("height", 480)
        )
        self.fps = config.get("fps", 30)
        self.device = config.get("device", "/dev/video0")
        self.auto_exposure = config.get("auto_exposure", True)

        # Durum değişkenleri
        self.camera = None
        self.aktif = False
        self.son_goruntu = None
        self.goruntu_sayaci = 0
        self.baslangic_zamani = None

        self.logger.info(f"📷 Fiziksel kamera oluşturuldu: {self.resolution}@{self.fps}fps")

    async def baslat(self) -> bool:
        """🚀 Fiziksel kamerayı başlat"""
        try:
            self.logger.info("🚀 Fiziksel kamera başlatılıyor...")

            # Picamera2 import et
            try:
                from picamera2 import Picamera2
            except ImportError as e:
                self.logger.error(f"❌ Picamera2 import hatası: {e}")
                self.logger.error("💡 Fiziksel kamera için picamera2 kütüphanesi gerekli!")
                return False

            # Kamerayı başlat
            self.camera = Picamera2()

            # Konfigürasyon oluştur
            config = self.camera.create_preview_configuration(
                main={"format": "RGB888", "size": self.resolution}
            )

            # Kamerayı yapılandır
            self.camera.configure(config)

            # Kamera kontrollerini ayarla
            if not self.auto_exposure:
                # Manuel exposure ayarları
                self.camera.set_controls({
                    "AeEnable": False,
                    "ExposureTime": 10000,  # 10ms
                    "AnalogueGain": 1.0
                })

            # Kamerayı başlat
            self.camera.start()

            # Kamera ısınması için bekle
            await asyncio.sleep(0.5)

            self.aktif = True
            self.baslangic_zamani = datetime.now()
            self.goruntu_sayaci = 0

            self.logger.info("✅ Fiziksel kamera hazır!")
            return True

        except Exception as e:
            self.logger.error(f"❌ Fiziksel kamera başlatma hatası: {e}")
            return False

    async def goruntu_al(self) -> Optional[np.ndarray]:
        """📸 Fiziksel kameradan görüntü al"""
        if not self.aktif or self.camera is None:
            self.logger.warning("⚠️ Kamera aktif değil!")
            return None

        try:
            # Picamera2'den görüntü al
            goruntu = self.camera.capture_array()

            # RGB'den BGR'ye çevir (OpenCV formatı)
            try:
                import cv2
                goruntu = cv2.cvtColor(goruntu, cv2.COLOR_RGB2BGR)
            except ImportError:
                # OpenCV yoksa manuel RGB->BGR çevirimi
                goruntu = goruntu[:, :, ::-1]  # RGB -> BGR

            self.son_goruntu = goruntu
            self.goruntu_sayaci += 1

            return goruntu

        except Exception as e:
            self.logger.error(f"❌ Fiziksel görüntü alma hatası: {e}")
            return None

    async def durdur(self) -> None:
        """🛑 Fiziksel kamerayı durdur"""
        try:
            self.logger.info("🛑 Fiziksel kamera durduruluyor...")

            if self.camera is not None:
                try:
                    self.camera.stop()
                    self.camera.close()
                    self.logger.info("✅ Fiziksel kamera durduruldu")
                except Exception as e:
                    self.logger.warning(f"⚠️ Kamera durdurma uyarısı: {e}")
                finally:
                    self.camera = None

            self.aktif = False
            self.son_goruntu = None

        except Exception as e:
            self.logger.error(f"❌ Fiziksel kamera durdurma hatası: {e}")

    def get_kamera_bilgisi(self) -> Dict[str, Any]:
        """ℹ️ Fiziksel kamera bilgilerini al"""
        return {
            "tip": "hardware",
            "aktif": self.aktif,
            "resolution": self.resolution,
            "fps": self.fps,
            "device": self.device,
            "auto_exposure": self.auto_exposure,
            "goruntu_sayaci": self.goruntu_sayaci,
            "baslangic_zamani": self.baslangic_zamani.isoformat() if self.baslangic_zamani else None,
            "son_goruntu_var": self.son_goruntu is not None
        }

    def get_resolution(self) -> Tuple[int, int]:
        """📐 Çözünürlük al"""
        return self.resolution

    def is_simulation(self) -> bool:
        """🔍 Simülasyon modunda mı?"""
        return False

    def set_parametreler(self, parametreler: Dict[str, Any]) -> bool:
        """⚙️ Fiziksel kamera parametrelerini ayarla"""
        if not self.aktif or self.camera is None:
            self.logger.warning("⚠️ Kamera aktif değil, parametreler ayarlanamadı!")
            return False

        try:
            controls = {}

            # Exposure ayarları
            if "exposure_time" in parametreler:
                controls["ExposureTime"] = parametreler["exposure_time"]
                self.logger.info(f"🔧 Exposure time ayarlandı: {parametreler['exposure_time']}")

            if "analog_gain" in parametreler:
                controls["AnalogueGain"] = parametreler["analog_gain"]
                self.logger.info(f"🔧 Analog gain ayarlandı: {parametreler['analog_gain']}")

            if "auto_exposure" in parametreler:
                controls["AeEnable"] = parametreler["auto_exposure"]
                self.auto_exposure = parametreler["auto_exposure"]
                self.logger.info(f"🔧 Auto exposure ayarlandı: {parametreler['auto_exposure']}")

            # Parametreleri uygula
            if controls:
                self.camera.set_controls(controls)
                return True

            return True

        except Exception as e:
            self.logger.error(f"❌ Parametre ayarlama hatası: {e}")
            return False

    def goruntu_kaydet(self, dosya_yolu: str) -> bool:
        """💾 Fiziksel kamera görüntüsünü kaydet"""
        if self.son_goruntu is None:
            self.logger.warning("⚠️ Kaydedilecek görüntü yok!")
            return False

        try:
            # OpenCV ile kaydet
            try:
                import cv2
                cv2.imwrite(dosya_yolu, self.son_goruntu)
                self.logger.info(f"💾 Fiziksel kamera görüntüsü kaydedildi: {dosya_yolu}")
                return True
            except ImportError:
                # OpenCV yoksa numpy ile kaydet
                np.save(dosya_yolu.replace('.jpg', '.npy'), self.son_goruntu)
                self.logger.info(f"💾 Fiziksel kamera görüntüsü numpy olarak kaydedildi: {dosya_yolu}")
                return True

        except Exception as e:
            self.logger.error(f"❌ Görüntü kaydetme hatası: {e}")
            return False

    def __del__(self):
        """🧹 Fiziksel kamera temizleniyor"""
        if hasattr(self, 'logger') and hasattr(self, 'aktif') and self.aktif:
            self.logger.info("🧹 Fiziksel kamera temizleniyor...")
            if hasattr(self, 'camera') and self.camera is not None:
                try:
                    self.camera.stop()
                    self.camera.close()
                except Exception:
                    pass
