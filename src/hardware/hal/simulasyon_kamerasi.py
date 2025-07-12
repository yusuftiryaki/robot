"""
📷 Simülasyon Kamerası Implementation
Hacı Abi'nin temiz simülasyon kamerası!

Bu sınıf, test ve geliştirme için simülasyon kamerası sağlar.
Gerçek kamera API'sini taklit eder ama sahte görüntüler üretir.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

import numpy as np

from .kamera_interface import KameraInterface


class SimulasyonKamerasi(KameraInterface):
    """
    🎮 Simülasyon Kamerası Implementation

    Test ve geliştirme için temiz simülasyon görüntüleri üretir.
    Engel tespit algoritmalarını tetiklemeyen, düz çimen görüntüleri.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger("SimulasyonKamerasi")

        # Kamera parametreleri
        self.resolution = (
            config.get("width", 640),
            config.get("height", 480)
        )
        self.fps = config.get("fps", 30)

        # Simülasyon parametreleri
        simulation_params = config.get("simulation_params", {})
        self.test_pattern = simulation_params.get("test_pattern", True)
        self.noise_level = simulation_params.get("noise_level", 0.01)

        # Durum değişkenleri
        self.aktif = False
        self.son_goruntu = None
        self.goruntu_sayaci = 0
        self.baslangic_zamani = None

        self.logger.info(f"🎮 Simülasyon kamerası oluşturuldu: {self.resolution}@{self.fps}fps")

    async def baslat(self) -> bool:
        """🚀 Simülasyon kamerasını başlat"""
        try:
            self.logger.info("🚀 Simülasyon kamerası başlatılıyor...")

            # İlk görüntüyü oluştur
            self.son_goruntu = self._perfect_grass_image_olustur()

            self.aktif = True
            self.baslangic_zamani = datetime.now()
            self.goruntu_sayaci = 0

            self.logger.info("✅ Simülasyon kamerası hazır!")
            return True

        except Exception as e:
            self.logger.error(f"❌ Simülasyon kamerası başlatma hatası: {e}")
            return False

    async def goruntu_al(self) -> Optional[np.ndarray]:
        """📸 Simülasyon görüntüsü üret"""
        if not self.aktif:
            self.logger.warning("⚠️ Kamera aktif değil!")
            return None

        try:
            # Mükemmel çimen görüntüsü oluştur
            if self.test_pattern:
                goruntu = self._perfect_grass_image_olustur()
            else:
                # Tamamen düz yeşil
                goruntu = np.zeros((self.resolution[1], self.resolution[0], 3), dtype=np.uint8)
                goruntu[:, :] = [30, 140, 30]  # BGR mükemmel çimen yeşili

            # Çok hafif noise (algoritmaları tetiklemesin)
            if self.noise_level > 0:
                minimal_noise = np.random.normal(0, self.noise_level * 2, goruntu.shape)
                goruntu = np.clip(goruntu + minimal_noise, 0, 255).astype(np.uint8)

            self.son_goruntu = goruntu
            self.goruntu_sayaci += 1

            # FPS kontrolü için küçük delay
            await asyncio.sleep(1.0 / self.fps if self.fps > 0 else 0.033)

            return goruntu

        except Exception as e:
            self.logger.error(f"❌ Simülasyon görüntü alma hatası: {e}")
            return None

    def _perfect_grass_image_olustur(self) -> np.ndarray:
        """🌱 Mükemmel düz çimen görüntüsü oluştur"""
        img = np.zeros((self.resolution[1], self.resolution[0], 3), dtype=np.uint8)

        # Mükemmel uniform yeşil çimen - hiçbir algoritma tetiklenmeyecek
        perfect_grass_color = [30, 140, 30]  # BGR formatında doğal çimen yeşili
        img[:, :] = perfect_grass_color

        # Hiç varyasyon yok - threshold, edge detection hiçbir şey bulamayacak
        return img

    async def durdur(self) -> None:
        """🛑 Simülasyon kamerasını durdur"""
        try:
            self.logger.info("🛑 Simülasyon kamerası durduruluyor...")

            self.aktif = False
            self.son_goruntu = None

            self.logger.info("✅ Simülasyon kamerası durduruldu")

        except Exception as e:
            self.logger.error(f"❌ Simülasyon kamerası durdurma hatası: {e}")

    def get_kamera_bilgisi(self) -> Dict[str, Any]:
        """ℹ️ Simülasyon kamera bilgilerini al"""
        return {
            "tip": "simulation",
            "aktif": self.aktif,
            "resolution": self.resolution,
            "fps": self.fps,
            "goruntu_sayaci": self.goruntu_sayaci,
            "test_pattern": self.test_pattern,
            "noise_level": self.noise_level,
            "baslangic_zamani": self.baslangic_zamani.isoformat() if self.baslangic_zamani else None,
            "son_goruntu_var": self.son_goruntu is not None
        }

    def get_resolution(self) -> Tuple[int, int]:
        """📐 Çözünürlük al"""
        return self.resolution

    def is_simulation(self) -> bool:
        """🔍 Simülasyon modunda mı?"""
        return True

    def set_parametreler(self, parametreler: Dict[str, Any]) -> bool:
        """⚙️ Simülasyon parametrelerini ayarla"""
        try:
            if "noise_level" in parametreler:
                self.noise_level = parametreler["noise_level"]
                self.logger.info(f"🔧 Noise level ayarlandı: {self.noise_level}")

            if "test_pattern" in parametreler:
                self.test_pattern = parametreler["test_pattern"]
                self.logger.info(f"🔧 Test pattern ayarlandı: {self.test_pattern}")

            return True

        except Exception as e:
            self.logger.error(f"❌ Parametre ayarlama hatası: {e}")
            return False

    def goruntu_kaydet(self, dosya_yolu: str) -> bool:
        """💾 Simülasyon görüntüsünü kaydet"""
        if self.son_goruntu is None:
            self.logger.warning("⚠️ Kaydedilecek görüntü yok!")
            return False

        try:
            # OpenCV import kontrolü
            try:
                import cv2
                cv2.imwrite(dosya_yolu, self.son_goruntu)
                self.logger.info(f"💾 Simülasyon görüntüsü kaydedildi: {dosya_yolu}")
                return True
            except ImportError:
                # OpenCV yoksa numpy ile kaydet
                np.save(dosya_yolu.replace('.jpg', '.npy'), self.son_goruntu)
                self.logger.info(f"💾 Simülasyon görüntüsü numpy olarak kaydedildi: {dosya_yolu}")
                return True

        except Exception as e:
            self.logger.error(f"❌ Görüntü kaydetme hatası: {e}")
            return False

    def __del__(self):
        """🧹 Simülasyon kamerası temizleniyor"""
        if hasattr(self, 'logger') and hasattr(self, 'aktif') and self.aktif:
            self.logger.info("🧹 Simülasyon kamerası temizleniyor...")
