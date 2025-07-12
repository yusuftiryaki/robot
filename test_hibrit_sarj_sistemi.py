#!/usr/bin/env python3
"""
🔋 GPS + AprilTag Hibrit Şarj Sistemi Testi
Hacı Abi'nin hibrit navigasyon sistemini test edelim!
"""

import asyncio
import logging
import math
from typing import Any, Dict
from unittest.mock import AsyncMock, Mock

import numpy as np

# Test için konfigürasyon
from src.core.smart_config import SmartConfigManager
from src.navigation.sarj_istasyonu_yaklasici import (SarjIstasyonuYaklasici,
                                                     SarjYaklasimDurumu)

# Test konfigürasyonu
TEST_CONFIG_PATH = "config/robot_config.yaml"

# Mock konum takipçi sınıfı


class MockKonumTakipci:
    def __init__(self):
        # Robot başlangıç konumu (şarj istasyonundan 20m uzakta)
        self.x = 0.0
        self.y = 0.0
        self.heading = 0.0

        # Test GPS konumları
        self.base_lat = 41.0082
        self.base_lon = 28.9784

    def get_mevcut_konum(self):
        """Mock mevcut konum"""
        mock_konum = Mock()
        mock_konum.x = self.x
        mock_konum.y = self.y
        mock_konum.heading = self.heading
        return mock_konum

    def get_mesafe_to_gps(self, lat: float, lon: float) -> float:
        """GPS koordinatlarına mesafe hesapla"""
        # Basit mesafe hesaplaması (test için)
        target_x, target_y = self._gps_to_local(lat, lon)
        return math.sqrt((target_x - self.x)**2 + (target_y - self.y)**2)

    def get_bearing_to_gps(self, lat: float, lon: float) -> float:
        """GPS koordinatlarına yön açısı"""
        target_x, target_y = self._gps_to_local(lat, lon)
        return math.atan2(target_y - self.y, target_x - self.x)

    def _gps_to_local(self, lat: float, lon: float):
        """GPS'i local koordinata çevir (test için basit)"""
        # Test için şarj istasyonu (20, 0) konumunda
        if lat == self.base_lat and lon == self.base_lon:
            return 20.0, 0.0
        return 0.0, 0.0

    def gps_hedef_dogrulugu(self, lat: float, lon: float, accuracy: float):
        """GPS hedef doğruluk analizi"""
        mesafe = self.get_mesafe_to_gps(lat, lon)
        bearing = math.degrees(self.get_bearing_to_gps(lat, lon))

        if mesafe <= accuracy:
            dogruluk = "yuksek"
        elif mesafe <= accuracy * 3:
            dogruluk = "orta"
        else:
            dogruluk = "dusuk"

        return {
            "mesafe": mesafe,
            "bearing": bearing,
            "dogruluk_seviyesi": dogruluk
        }

    def hareket_et(self, linear: float, angular: float, sure: float = 0.5):
        """Robot hareketini simüle et"""
        # Basit hareket simülasyonu
        self.heading += angular * sure
        self.x += linear * math.cos(self.heading) * sure
        self.y += linear * math.sin(self.heading) * sure


class HibritSarjTesti:
    """GPS + AprilTag hibrit şarj sistemi testi"""

    def __init__(self):
        self.logger = logging.getLogger("HibritSarjTesti")
        self.mock_konum_takipci = MockKonumTakipci()

    async def sistemi_baslat(self):
        """Test sistemini başlat"""
        self.logger.info("🔋 Hibrit şarj sistemi testi başlatılıyor...")

        # Konfigürasyon yükle
        config_manager = SmartConfigManager()
        config = config_manager.load_config()

        # Şarj yaklaşıcıyı başlat
        charging_config = config.get("charging", {})
        navigation_config = config.get("navigation", {})

        self.sarj_yaklasici = SarjIstasyonuYaklasici(
            sarj_config=charging_config,
            nav_config=navigation_config,
            konum_takipci=self.mock_konum_takipci
        )

        self.logger.info("✅ Hibrit şarj sistemi hazır")

    async def gps_navigasyon_testi(self):
        """GPS navigasyon fazını test et"""
        self.logger.info("🌍 GPS navigasyon testi başlıyor...")

        # Başlangıç durumu kontrolü
        durum = self.sarj_yaklasici.get_yaklasim_durumu()
        self.logger.info(f"Başlangıç durumu: {durum['durum']}")

        if durum["durum"] != "gps_navigasyon":
            self.logger.warning("⚠️ GPS navigasyon durumunda değil!")
            return False

        # Mock kamera verisi (GPS aşamasında AprilTag yok)
        mock_kamera = np.zeros((480, 640, 3), dtype=np.uint8)

        gps_adim_sayisi = 0
        max_gps_adim = 100  # Maksimum GPS adım sayısı (artırdık)

        while (self.sarj_yaklasici.mevcut_durum == SarjYaklasimDurumu.GPS_NAVIGASYON and
               gps_adim_sayisi < max_gps_adim):

            # Şarj yaklaşım komutunu al
            komut = await self.sarj_yaklasici.sarj_istasyonuna_yaklas(mock_kamera)

            if komut is None:
                self.logger.info("GPS navigasyon tamamlandı!")
                break

            # Hareket simülasyonu (daha büyük adımlar)
            self.mock_konum_takipci.hareket_et(
                komut.linear_hiz,
                komut.angular_hiz,
                komut.sure * 2  # Hareket süresini artır
            )

            # Durum logla
            mevcut_konum = self.mock_konum_takipci.get_mevcut_konum()
            mesafe_kalan = self.mock_konum_takipci.get_mesafe_to_gps(41.0082, 28.9784)

            self.logger.info(
                f"GPS Adım {gps_adim_sayisi}: "
                f"Konum=({mevcut_konum.x:.2f}, {mevcut_konum.y:.2f}), "
                f"Mesafe={mesafe_kalan:.2f}m, "
                f"Linear={komut.linear_hiz:.3f}, Angular={komut.angular_hiz:.3f}"
            )

            gps_adim_sayisi += 1
            await asyncio.sleep(0.1)  # Simülasyon gecikmesi

        # GPS fazı sonuç değerlendirmesi
        final_mesafe = self.mock_konum_takipci.get_mesafe_to_gps(41.0082, 28.9784)

        if self.sarj_yaklasici.mevcut_durum != SarjYaklasimDurumu.GPS_NAVIGASYON:
            self.logger.info(f"✅ GPS navigasyon başarıyla tamamlandı! Final mesafe: {final_mesafe:.2f}m")
            return True
        else:
            self.logger.warning(f"⚠️ GPS navigasyon maksimum adım sayısına ulaştı. Mesafe: {final_mesafe:.2f}m")
            return False

    async def apriltag_simulasyon_testi(self):
        """AprilTag algılama fazını simüle et"""
        self.logger.info("🏷️ AprilTag simülasyon testi başlıyor...")

        # AprilTag simülasyonu için mock kamera verisi oluştur
        # Robot şarj istasyonuna yeterince yakın olduğunda AprilTag algılaması simüle edilir

        apriltag_adim_sayisi = 0
        max_apriltag_adim = 30

        while (self.sarj_yaklasici.mevcut_durum != SarjYaklasimDurumu.TAMAMLANDI and
               apriltag_adim_sayisi < max_apriltag_adim):

            # Mesafe kontrol et - yakınsa AprilTag var gibi simüle et
            mevcut_konum = self.mock_konum_takipci.get_mevcut_konum()
            mesafe_sarj = math.sqrt((20 - mevcut_konum.x)**2 + (0 - mevcut_konum.y)**2)

            if mesafe_sarj < 2.0:  # 2m içindeyse AprilTag simüle et
                # AprilTag'li mock kamera verisi (gerçekte AprilTag detection algoritması çalışacak)
                mock_kamera = self._apriltag_mock_olustur(mesafe_sarj)
            else:
                # AprilTag yok
                mock_kamera = np.zeros((480, 640, 3), dtype=np.uint8)

            # Şarj yaklaşım komutunu al
            komut = await self.sarj_yaklasici.sarj_istasyonuna_yaklas(mock_kamera)

            if komut is None:
                self.logger.info("🔋 Şarj yaklaşımı tamamlandı!")
                break

            # Hareket simülasyonu
            self.mock_konum_takipci.hareket_et(
                komut.linear_hiz,
                komut.angular_hiz,
                komut.sure
            )

            durum = self.sarj_yaklasici.get_yaklasim_durumu()
            self.logger.info(
                f"AprilTag Adım {apriltag_adim_sayisi}: "
                f"Durum={durum['durum']}, "
                f"Mesafe={mesafe_sarj:.2f}m, "
                f"Linear={komut.linear_hiz:.3f}, Angular={komut.angular_hiz:.3f}"
            )

            apriltag_adim_sayisi += 1
            await asyncio.sleep(0.1)

        # AprilTag fazı sonuç
        if self.sarj_yaklasici.mevcut_durum == SarjYaklasimDurumu.TAMAMLANDI:
            self.logger.info("✅ AprilTag yaklaşımı başarıyla tamamlandı!")
            return True
        else:
            self.logger.warning("⚠️ AprilTag yaklaşımı tamamlanamadı")
            return False

    def _apriltag_mock_olustur(self, mesafe: float) -> np.ndarray:
        """AprilTag'li mock kamera verisi oluştur"""
        # Basit mock - gerçekte kamera+AprilTag detection olacak
        mock_kamera = np.zeros((480, 640, 3), dtype=np.uint8)

        # Mesafeye göre tag boyutu simüle et (yakınsa büyük, uzaksa küçük)
        tag_boyutu = max(20, int(100 / (mesafe + 0.1)))
        center_x, center_y = 320, 240

        # Basit kare çiz (AprilTag simülasyonu)
        cv2_available = True
        try:
            import cv2
            cv2.rectangle(
                mock_kamera,
                (center_x - tag_boyutu // 2, center_y - tag_boyutu // 2),
                (center_x + tag_boyutu // 2, center_y + tag_boyutu // 2),
                (255, 255, 255), -1
            )
        except ImportError:
            cv2_available = False

        return mock_kamera

    async def tam_hibrit_testi(self):
        """Tam hibrit sistem testi - GPS'ten AprilTag'e"""
        self.logger.info("🚀 TAM HİBRİT SİSTEM TESTİ BAŞLIYOR!")

        # 1. Sistemi başlat
        await self.sistemi_baslat()

        # 2. GPS navigasyon testi
        gps_basarili = await self.gps_navigasyon_testi()

        if not gps_basarili:
            self.logger.error("❌ GPS navigasyon fazı başarısız!")
            return False

        # 3. AprilTag yaklaşım testi
        apriltag_basarili = await self.apriltag_simulasyon_testi()

        if not apriltag_basarili:
            self.logger.error("❌ AprilTag fazı başarısız!")
            return False

        # 4. Son durum kontrolü
        final_durum = self.sarj_yaklasici.get_yaklasim_durumu()
        self.logger.info(f"🏁 Final durum: {final_durum}")

        self.logger.info("🎉 HİBRİT SİSTEM TESTİ BAŞARIYLA TAMAMLANDI!")
        return True


async def main():
    """Ana test fonksiyonu"""
    # Loglama ayarla
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger = logging.getLogger("HibritSarjTesti")
    logger.info("🔋 GPS + AprilTag Hibrit Şarj Sistemi Testi")

    # Test suite'i çalıştır
    test_suite = HibritSarjTesti()

    try:
        basarili = await test_suite.tam_hibrit_testi()

        if basarili:
            logger.info("✅ TÜM TESTLER BAŞARILI!")
        else:
            logger.error("❌ TESTLERDE HATA!")

    except Exception as e:
        logger.error(f"❌ Test sırasında hata: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())


if __name__ == "__main__":
    asyncio.run(main())
