"""
🔋 Şarj İstasyonu Yaklaşıcı - AprilTag Destekli Hassas Konumlandırma
Hacı Abi'nin şarj istasyonu yaklaşım algoritması!

Bu sınıf AprilTag kullanarak mm hassasiyetinde şarj istasyonuna yaklaşım sağlar:
- AprilTag tespit ve pose estimation
- INA219 ile fiziksel bağlantı kontrolü
- Adaptive hız kontrolü
- Hassas konumlandırma algoritmaları
"""

import asyncio
import logging
import math
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

try:
    from ina219 import INA219
    INA219_AVAILABLE = True
except ImportError:
    INA219_AVAILABLE = False
    print("⚠️ INA219 kütüphanesi yok - simülasyon modunda çalışacak")


class SarjYaklasimDurumu(Enum):
    """Şarj yaklaşım durum makinesi"""
    ARAMA = "arama"                    # AprilTag arama
    TESPIT = "tespit"                  # AprilTag tespit edildi
    YAKLASIM = "yaklasim"              # Yaklaşım başladı
    HASSAS_KONUMLANDIRMA = "hassas"    # Hassas konumlandırma
    FIZIKSEL_BAGLANTI = "baglanti"     # Fiziksel bağlantı kontrolü
    TAMAMLANDI = "tamamlandi"          # Şarj başladı
    HATA = "hata"                      # Hata durumu


@dataclass
class AprilTagTespit:
    """AprilTag tespit sonucu"""
    tag_id: int
    merkez_x: float
    merkez_y: float
    mesafe: float
    aci: float
    pose_gecerli: bool
    guven_skoru: float


@dataclass
class SarjYaklasimKomutu:
    """Şarj yaklaşım hareket komutu"""
    linear_hiz: float
    angular_hiz: float
    sure: float
    hassas_mod: bool = False


class SarjIstasyonuYaklasici:
    """
    🔋 AprilTag Tabanlı Şarj İstasyonu Yaklaşıcı

    Bu sınıf robot'un şarj istasyonuna hassas şekilde yaklaşmasını sağlar.
    AprilTag vision ve INA219 güç sensörü ile tam otomatik şarj.
    """

    def __init__(self, sarj_config: Dict[str, Any]):
        self.config = sarj_config
        self.logger = logging.getLogger("SarjIstasyonuYaklasici")

        # AprilTag parametreleri
        self.apriltag_config = sarj_config.get("apriltag", {})
        self.hedef_tag_id = self.apriltag_config.get("sarj_istasyonu_tag_id", 0)
        self.kamera_matrix = np.array(self.apriltag_config.get("kamera_matrix", [
            [640, 0, 320],
            [0, 640, 240],
            [0, 0, 1]
        ]), dtype=np.float32)
        self.distortion_coeffs = np.array(self.apriltag_config.get("distortion_coeffs", [0, 0, 0, 0, 0]), dtype=np.float32)

        # Tag boyutu (metre cinsinden)
        self.tag_boyutu = self.apriltag_config.get("tag_boyutu", 0.08)  # 8cm (küçük)

        # Yaklaşım parametreleri
        self.hedef_mesafe = sarj_config.get("hedef_mesafe", 0.25)  # 25cm
        self.hassas_mesafe = sarj_config.get("hassas_mesafe", 0.08)  # 8cm
        self.aci_toleransi = sarj_config.get("aci_toleransi", 5.0)  # 5 derece
        self.pozisyon_toleransi = sarj_config.get("pozisyon_toleransi", 0.02)  # 2cm

        # Hız parametreleri
        self.yaklasim_hizi = sarj_config.get("yaklasim_hizi", 0.1)  # 10 cm/s
        self.hassas_hiz = sarj_config.get("hassas_hiz", 0.02)  # 2 cm/s
        self.donme_hizi = sarj_config.get("donme_hizi", 0.2)  # 0.2 rad/s

        # INA219 güç sensörü
        self.ina219_aktif = False
        self.sarj_akimi_esigi = sarj_config.get("sarj_akimi_esigi", 0.1)  # 100mA
        self.baglanti_voltaj_esigi = sarj_config.get("baglanti_voltaj_esigi", 11.0)  # 11V

        # Durum takibi
        self.mevcut_durum = SarjYaklasimDurumu.ARAMA
        self.son_tespit: Optional[AprilTagTespit] = None
        self.tespit_sayaci = 0
        self.hata_sayaci = 0

        # AprilTag detector
        self.detector = None
        self._apriltag_detector_baslat()

        # INA219 başlat
        self._ina219_baslat()

        self.logger.info("🔋 Şarj istasyonu yaklaşıcı hazır")

    def _apriltag_detector_baslat(self):
        """AprilTag detector'ı başlat"""
        try:
            # OpenCV sürüm uyumluluğu
            try:
                # OpenCV 4.7+ için yeni API
                self.aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_APRILTAG_36h11)
                self.detector_params = cv2.aruco.DetectorParameters()
            except AttributeError:
                # OpenCV 4.6 ve öncesi için eski API
                self.aruco_dict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_APRILTAG_36h11)
                self.detector_params = cv2.aruco.DetectorParameters_create()

            # Detector parametrelerini optimize et
            if hasattr(self.detector_params, 'adaptiveThreshWinSizeMin'):
                self.detector_params.adaptiveThreshWinSizeMin = 3
                self.detector_params.adaptiveThreshWinSizeMax = 23
                self.detector_params.adaptiveThreshWinSizeStep = 10
                self.detector_params.minMarkerPerimeterRate = 0.03
                self.detector_params.maxMarkerPerimeterRate = 4.0

            self.logger.info("✅ AprilTag detector hazır")

        except Exception as e:
            self.logger.error(f"❌ AprilTag detector hatası: {e}")
            self.detector = None

    def _ina219_baslat(self):
        """INA219 güç sensörünü başlat"""
        try:
            if INA219_AVAILABLE:
                # INA219 sensörünü başlat
                self.ina219 = INA219(shunt_ohms=0.1, address=0x40)
                self.ina219.configure()
                self.ina219_aktif = True
                self.logger.info("✅ INA219 güç sensörü hazır")
            else:
                self.logger.warning("⚠️ INA219 simülasyon modunda")
                self.ina219_aktif = False

        except Exception as e:
            self.logger.error(f"❌ INA219 başlatma hatası: {e}")
            self.ina219_aktif = False

    async def sarj_istasyonuna_yaklas(self, kamera_data: np.ndarray) -> Optional[SarjYaklasimKomutu]:
        """
        🎯 Ana yaklaşım fonksiyonu

        Args:
            kamera_data: Kamera görüntüsü

        Returns:
            Hareket komutu veya None (yaklaşım tamamlandı)
        """
        try:
            # AprilTag tespit et
            tespit_sonucu = self._apriltag_tespit_et(kamera_data)

            # Durum makinesini işle
            return await self._durum_makinesini_isle(tespit_sonucu)

        except Exception as e:
            self.logger.error(f"❌ Şarj yaklaşım hatası: {e}")
            self.mevcut_durum = SarjYaklasimDurumu.HATA
            return None

    def _apriltag_tespit_et(self, kamera_data: np.ndarray) -> Optional[AprilTagTespit]:
        """AprilTag tespit ve pose estimation"""
        try:
            if self.detector is None:
                return None

            # Gri seviyeye çevir
            gray = cv2.cvtColor(kamera_data, cv2.COLOR_BGR2GRAY)

            # AprilTag tespit et
            corners, ids, _ = cv2.aruco.detectMarkers(gray, self.aruco_dict, parameters=self.detector_params)

            if ids is not None and len(ids) > 0:
                # Hedef tag'i bul
                hedef_index = None
                for i, tag_id in enumerate(ids):
                    if tag_id[0] == self.hedef_tag_id:
                        hedef_index = i
                        break

                if hedef_index is not None:
                    # Pose estimation
                    corner = corners[hedef_index]

                    # Tag merkezini hesapla
                    merkez_x = float(np.mean(corner[0][:, 0]))
                    merkez_y = float(np.mean(corner[0][:, 1]))

                    # Pose estimation yap
                    tag_points = np.array([
                        [-self.tag_boyutu / 2, -self.tag_boyutu / 2, 0],
                        [self.tag_boyutu / 2, -self.tag_boyutu / 2, 0],
                        [self.tag_boyutu / 2, self.tag_boyutu / 2, 0],
                        [-self.tag_boyutu / 2, self.tag_boyutu / 2, 0]
                    ], dtype=np.float32)

                    success, rvec, tvec = cv2.solvePnP(
                        tag_points, corner[0], self.kamera_matrix, self.distortion_coeffs
                    )

                    if success:
                        # Mesafe ve açı hesapla
                        mesafe = float(np.linalg.norm(tvec))
                        aci = float(math.degrees(math.atan2(tvec[0][0], tvec[2][0])))

                        # Güven skoru hesapla (corner'ların ne kadar düzgün olduğuna bak)
                        guven_skoru = self._guven_skoru_hesapla(corner[0])

                        tespit = AprilTagTespit(
                            tag_id=self.hedef_tag_id,
                            merkez_x=merkez_x,
                            merkez_y=merkez_y,
                            mesafe=mesafe,
                            aci=aci,
                            pose_gecerli=True,
                            guven_skoru=guven_skoru
                        )

                        self.son_tespit = tespit
                        self.tespit_sayaci += 1

                        self.logger.debug(f"📍 AprilTag tespit: mesafe={mesafe:.2f}m, açı={aci:.1f}°")
                        return tespit

            return None

        except Exception as e:
            self.logger.error(f"❌ AprilTag tespit hatası: {e}")
            return None

    def _guven_skoru_hesapla(self, corners: np.ndarray) -> float:
        """AprilTag tespit güven skoru hesapla"""
        try:
            # Köşeler arası mesafeleri hesapla
            kenar_uzunluklari = []
            for i in range(4):
                p1 = corners[i]
                p2 = corners[(i + 1) % 4]
                uzunluk = np.linalg.norm(p2 - p1)
                kenar_uzunluklari.append(uzunluk)

            # Kenar uzunlukları ne kadar eşit?
            ort_uzunluk = np.mean(kenar_uzunluklari)
            varyans = np.var(kenar_uzunluklari)

            # Düşük varyans = yüksek güven
            guven_skoru = max(0.0, 1.0 - (varyans / (ort_uzunluk ** 2)))

            return guven_skoru

        except Exception:
            return 0.0

    async def _durum_makinesini_isle(self, tespit: Optional[AprilTagTespit]) -> Optional[SarjYaklasimKomutu]:
        """Durum makinesini işle"""

        if self.mevcut_durum == SarjYaklasimDurumu.ARAMA:
            return await self._arama_durumu(tespit)

        elif self.mevcut_durum == SarjYaklasimDurumu.TESPIT:
            return await self._tespit_durumu(tespit)

        elif self.mevcut_durum == SarjYaklasimDurumu.YAKLASIM:
            return await self._yaklasim_durumu(tespit)

        elif self.mevcut_durum == SarjYaklasimDurumu.HASSAS_KONUMLANDIRMA:
            return await self._hassas_konumlandirma_durumu(tespit)

        elif self.mevcut_durum == SarjYaklasimDurumu.FIZIKSEL_BAGLANTI:
            return await self._fiziksel_baglanti_durumu()

        elif self.mevcut_durum == SarjYaklasimDurumu.TAMAMLANDI:
            return None  # Yaklaşım tamamlandı

        elif self.mevcut_durum == SarjYaklasimDurumu.HATA:
            return await self._hata_durumu()

        return None

    async def _arama_durumu(self, tespit: Optional[AprilTagTespit]) -> Optional[SarjYaklasimKomutu]:
        """AprilTag arama durumu"""
        if tespit is not None and tespit.guven_skoru > 0.5:
            self.logger.info(f"🎯 AprilTag bulundu! ID: {tespit.tag_id}")
            self.mevcut_durum = SarjYaklasimDurumu.TESPIT
            return await self._tespit_durumu(tespit)

        # Yavaş dönüş yaparak ara
        return SarjYaklasimKomutu(
            linear_hiz=0.0,
            angular_hiz=0.1,  # Yavaş dönüş
            sure=0.5
        )

    async def _tespit_durumu(self, tespit: Optional[AprilTagTespit]) -> Optional[SarjYaklasimKomutu]:
        """AprilTag tespit edildi - yaklaşıma geçiş"""
        if tespit is None:
            # Tespit kaybedildi - aramaya dön
            self.mevcut_durum = SarjYaklasimDurumu.ARAMA
            return await self._arama_durumu(None)

        if tespit.mesafe > self.hedef_mesafe:
            self.mevcut_durum = SarjYaklasimDurumu.YAKLASIM
            return await self._yaklasim_durumu(tespit)
        else:
            self.mevcut_durum = SarjYaklasimDurumu.HASSAS_KONUMLANDIRMA
            return await self._hassas_konumlandirma_durumu(tespit)

    async def _yaklasim_durumu(self, tespit: Optional[AprilTagTespit]) -> Optional[SarjYaklasimKomutu]:
        """AprilTag'e yaklaşım"""
        if tespit is None:
            self.hata_sayaci += 1
            if self.hata_sayaci > 10:
                self.mevcut_durum = SarjYaklasimDurumu.ARAMA
                self.hata_sayaci = 0
            return SarjYaklasimKomutu(linear_hiz=0.0, angular_hiz=0.0, sure=0.1)

        self.hata_sayaci = 0

        # Mesafe kontrolü
        if tespit.mesafe <= self.hassas_mesafe:
            self.mevcut_durum = SarjYaklasimDurumu.HASSAS_KONUMLANDIRMA
            return await self._hassas_konumlandirma_durumu(tespit)

        # Açı düzeltme
        if abs(tespit.aci) > self.aci_toleransi:
            angular_hiz = -0.1 if tespit.aci > 0 else 0.1
            return SarjYaklasimKomutu(
                linear_hiz=0.0,
                angular_hiz=angular_hiz,
                sure=0.2
            )

        # Düz ileri hareket
        return SarjYaklasimKomutu(
            linear_hiz=self.yaklasim_hizi,
            angular_hiz=0.0,
            sure=0.5
        )

    async def _hassas_konumlandirma_durumu(self, tespit: Optional[AprilTagTespit]) -> Optional[SarjYaklasimKomutu]:
        """Hassas konumlandırma"""
        if tespit is None:
            self.hata_sayaci += 1
            if self.hata_sayaci > 5:
                self.mevcut_durum = SarjYaklasimDurumu.ARAMA
                self.hata_sayaci = 0
            return SarjYaklasimKomutu(linear_hiz=0.0, angular_hiz=0.0, sure=0.1)

        self.hata_sayaci = 0

        # Pozisyon kontrolü
        if (tespit.mesafe <= self.pozisyon_toleransi and
                abs(tespit.aci) <= self.aci_toleransi):
            self.logger.info("🎯 Hassas konumlandırma tamamlandı!")
            self.mevcut_durum = SarjYaklasimDurumu.FIZIKSEL_BAGLANTI
            return await self._fiziksel_baglanti_durumu()

        # Çok hassas hareket
        linear_hiz = min(self.hassas_hiz, tespit.mesafe * 0.1)
        angular_hiz = -tespit.aci * 0.01  # Çok küçük açı düzeltmesi

        return SarjYaklasimKomutu(
            linear_hiz=linear_hiz,
            angular_hiz=angular_hiz,
            sure=0.2,
            hassas_mod=True
        )

    async def _fiziksel_baglanti_durumu(self) -> Optional[SarjYaklasimKomutu]:
        """Fiziksel bağlantı kontrolü"""
        try:
            # INA219 ile akım ve voltaj ölç
            if self.ina219_aktif:
                voltaj = self.ina219.voltage()
                akim = self.ina219.current()

                self.logger.debug(f"⚡ Voltaj: {voltaj:.2f}V, Akım: {akim:.2f}mA")

                # Şarj başladı mı kontrol et
                if (voltaj > self.baglanti_voltaj_esigi and
                        akim > self.sarj_akimi_esigi):
                    self.logger.info("🔋 Şarj bağlantısı başarılı!")
                    self.mevcut_durum = SarjYaklasimDurumu.TAMAMLANDI
                    return None

                # Biraz daha yaklaşmaya çalış
                return SarjYaklasimKomutu(
                    linear_hiz=0.005,  # 5mm/s
                    angular_hiz=0.0,
                    sure=0.5,
                    hassas_mod=True
                )
            else:
                # Simülasyon modunda - bağlantı başarılı say
                await asyncio.sleep(1)
                self.logger.info("🔋 Simülasyon: Şarj bağlantısı başarılı!")
                self.mevcut_durum = SarjYaklasimDurumu.TAMAMLANDI
                return None

        except Exception as e:
            self.logger.error(f"❌ Fiziksel bağlantı kontrolü hatası: {e}")
            self.mevcut_durum = SarjYaklasimDurumu.HATA
            return None

    async def _hata_durumu(self) -> Optional[SarjYaklasimKomutu]:
        """Hata durumu - recovery"""
        await asyncio.sleep(1)
        self.logger.warning("🔄 Hata durumundan çıkış - aramaya dön")
        self.mevcut_durum = SarjYaklasimDurumu.ARAMA
        self.hata_sayaci = 0
        return None

    def get_yaklasim_durumu(self) -> Dict[str, Any]:
        """Yaklaşım durumu bilgisi"""
        return {
            "durum": self.mevcut_durum.value,
            "son_tespit": {
                "mesafe": self.son_tespit.mesafe if self.son_tespit else None,
                "aci": self.son_tespit.aci if self.son_tespit else None,
                "guven_skoru": self.son_tespit.guven_skoru if self.son_tespit else None
            } if self.son_tespit else None,
            "tespit_sayaci": self.tespit_sayaci,
            "hata_sayaci": self.hata_sayaci,
            "ina219_aktif": self.ina219_aktif
        }

    def sifirla(self):
        """Yaklaşım durumunu sıfırla"""
        self.mevcut_durum = SarjYaklasimDurumu.ARAMA
        self.son_tespit = None
        self.tespit_sayaci = 0
        self.hata_sayaci = 0
        self.logger.info("🔄 Şarj yaklaşım durumu sıfırlandı")

    def __del__(self):
        """Temizlik"""
        if hasattr(self, 'logger'):
            self.logger.info("👋 Şarj istasyonu yaklaşıcı kapatılıyor...")
