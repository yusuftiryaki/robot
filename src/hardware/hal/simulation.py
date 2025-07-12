"""
🎮 Simülasyon HAL - Sahte Donanım Implementasyonu
Hacı Abi'nin simülasyon magic'i burada!

Bu modül, gerçek donanım olmadan test yapmak için sahte sensör verisi üretir.
Akıllı simülasyon: Robot durumuna göre gerçekçi veriler üretir.
"""

import asyncio
import json
import logging
import math
import time
from datetime import datetime
from typing import Any, Dict, Optional

from .interfaces import (
    AcilDurmaInterface,
    AcilDurmaVeri,
    EnkoderInterface,
    EnkoderVeri,
    GPSInterface,
    GPSVeri,
    GucInterface,
    GucVeri,
    HardwareFactory,
    IMUInterface,
    IMUVeri,
    MotorDurumuVeri,
    MotorInterface,
    TamponInterface,
    TamponVeri,
)


class SimulasyonDataManager:
    """Simülasyon verilerini yönetir"""

    def __init__(self):
        self.logger = logging.getLogger("SimulasyonDataManager")
        self.simulation_data = self._load_simulation_data()
        self.simulation_time_start = time.time()

        # Robot durumu - diğer modüllerden güncellenecek
        self.robot_durumu = {
            "durum": "bekleme",  # bekleme, hareket, sarj, gorev
            "linear_hiz": 0.0,
            "angular_hiz": 0.0,
            "konum": {"x": 0.0, "y": 0.0, "heading": 0.0},
            "hareket_halinde": False,
            "timestamp": time.time()
        }

        self.current_gps_position = self.simulation_data['gps'].copy()

    def _load_simulation_data(self) -> Dict[str, Any]:
        """Simülasyon verilerini config dosyasından yükle"""
        try:
            with open('/workspaces/oba/config/simulation_data.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.warning("⚠️ Simülasyon config dosyası bulunamadı, varsayılan değerler kullanılıyor")
            return {
                "imu": {
                    "ivme_x": 0.1, "ivme_y": 0.0, "ivme_z": 9.8,
                    "acisal_hiz_x": 0.0, "acisal_hiz_y": 0.01, "acisal_hiz_z": 0.0,
                    "roll": 0.0, "pitch": 0.0, "yaw": 0.0, "sicaklik": 25.0
                },
                "gps": {
                    "enlem": 41.0082, "boylam": 28.9784, "yukseklik": 856.0,
                    "uydu_sayisi": 8, "fix_kalitesi": 3, "hiz": 0.0, "yön": 0.0
                },
                "guc": {
                    "voltaj": 12.5, "akim": -0.5, "guc": 6.25, "batarya_seviyesi": 85.0
                },
                "tampon": {"basildi": False},
                "enkoder": {"sol_teker": 0, "sag_teker": 0},
                "acil_durma": {"aktif": False}
            }

    def robot_durumu_guncelle(self, durum: str, linear_hiz: float = 0.0, angular_hiz: float = 0.0):
        """Robot durumunu güncelle"""
        old_durum = self.robot_durumu["durum"]
        self.robot_durumu.update({
            "durum": durum,
            "linear_hiz": linear_hiz,
            "angular_hiz": angular_hiz,
            "hareket_halinde": abs(linear_hiz) > 0.01 or abs(angular_hiz) > 0.01,
            "timestamp": time.time()
        })

        if old_durum != durum:
            self.logger.info(f"🔄 Robot durumu değişti: {old_durum} → {durum}")

    def konum_guncelle(self, dt: float):
        """Simülasyon konumunu güncelle"""
        if not self.robot_durumu["hareket_halinde"]:
            return

        # Linear hareket
        if abs(self.robot_durumu["linear_hiz"]) > 0.01:
            heading_rad = math.radians(self.robot_durumu["konum"]["heading"])
            dx = self.robot_durumu["linear_hiz"] * math.cos(heading_rad) * dt
            dy = self.robot_durumu["linear_hiz"] * math.sin(heading_rad) * dt

            # GPS koordinatlarına dönüştür
            lat_delta = dy / 111000.0
            lon_delta = dx / (111000.0 * math.cos(math.radians(self.current_gps_position["enlem"])))

            self.current_gps_position["enlem"] += lat_delta
            self.current_gps_position["boylam"] += lon_delta

            self.robot_durumu["konum"]["x"] += dx
            self.robot_durumu["konum"]["y"] += dy

        # Angular hareket
        if abs(self.robot_durumu["angular_hiz"]) > 0.01:
            heading_delta = math.degrees(self.robot_durumu["angular_hiz"] * dt)
            self.robot_durumu["konum"]["heading"] += heading_delta
            self.robot_durumu["konum"]["heading"] = self.robot_durumu["konum"]["heading"] % 360


# Global simülasyon data manager
_simulation_manager = SimulasyonDataManager()


class SimulasyonIMU(IMUInterface):
    """Simülasyon IMU sensörü"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger("SimulasyonIMU")
        self.aktif = False
        self.kalibrasyon_verisi = {
            "ivme_offset": {"x": 0.0, "y": 0.0, "z": 0.0},
            "gyro_offset": {"x": 0.0, "y": 0.0, "z": 0.0}
        }

    async def baslat(self) -> bool:
        """IMU sensörünü başlat"""
        try:
            self.aktif = True
            self.logger.info("✅ Simülasyon IMU başlatıldı")
            return True
        except Exception as e:
            self.logger.error(f"❌ IMU başlatma hatası: {e}")
            return False

    async def durdur(self):
        """IMU sensörünü durdur"""
        self.aktif = False
        self.logger.info("🛑 Simülasyon IMU durduruldu")

    async def veri_oku(self) -> Optional[IMUVeri]:
        """IMU verisi oku"""
        if not self.aktif:
            return None

        try:
            t = time.time() - _simulation_manager.simulation_time_start
            base_data = _simulation_manager.simulation_data["imu"]

            # Robot durumuna göre IMU verisi
            if _simulation_manager.robot_durumu["durum"] == "bekleme":
                # Bekleme modunda minimal titreşim
                return IMUVeri(
                    timestamp=datetime.now().isoformat(),
                    gecerli=True,
                    hata_mesaji=None,
                    ivme_x=0.02 * math.sin(t * 0.1),
                    ivme_y=0.02 * math.cos(t * 0.1),
                    ivme_z=9.81 + 0.01 * math.sin(t * 0.05),
                    acisal_hiz_x=0.005 * math.sin(t * 0.2),
                    acisal_hiz_y=0.005 * math.cos(t * 0.2),
                    acisal_hiz_z=0.002 * math.sin(t * 0.1),
                    roll=0.2 * math.sin(t * 0.05),
                    pitch=0.1 * math.cos(t * 0.05),
                    yaw=_simulation_manager.robot_durumu["konum"]["heading"],
                    sicaklik=25.0 + 0.5 * math.sin(t * 0.02)
                )

            elif _simulation_manager.robot_durumu["durum"] == "hareket":
                # Hareket modunda gerçekçi IMU verileri
                linear_vel = _simulation_manager.robot_durumu["linear_hiz"]
                angular_vel = _simulation_manager.robot_durumu["angular_hiz"]

                return IMUVeri(
                    timestamp=datetime.now().isoformat(),
                    gecerli=True,
                    hata_mesaji=None,
                    ivme_x=linear_vel * 2.0 + 0.1 * math.sin(t * 2.0),
                    ivme_y=0.05 * math.cos(t * 3.0),
                    ivme_z=9.81 + 0.02 * math.sin(t * 1.5),
                    acisal_hiz_x=0.01 * math.sin(t * 1.0),
                    acisal_hiz_y=0.01 * math.cos(t * 1.0),
                    acisal_hiz_z=angular_vel + 0.005 * math.sin(t * 2.0),
                    roll=0.3 * math.sin(t * 0.5),
                    pitch=0.2 * math.cos(t * 0.5),
                    yaw=_simulation_manager.robot_durumu["konum"]["heading"],
                    sicaklik=26.0 + 0.5 * math.sin(t * 0.02)
                )

            else:
                # Diğer durumlar için base data
                return IMUVeri(
                    timestamp=datetime.now().isoformat(),
                    gecerli=True,
                    hata_mesaji=None,
                    **base_data
                )

        except Exception as e:
            self.logger.error(f"❌ IMU veri okuma hatası: {e}")
            return IMUVeri(
                timestamp=datetime.now().isoformat(),
                gecerli=False,
                hata_mesaji=str(e),
                ivme_x=0.0, ivme_y=0.0, ivme_z=0.0,
                acisal_hiz_x=0.0, acisal_hiz_y=0.0, acisal_hiz_z=0.0,
                roll=0.0, pitch=0.0, yaw=0.0, sicaklik=0.0
            )

    async def kalibrasyon_yap(self) -> bool:
        """IMU kalibrasyonu yap"""
        if not self.aktif:
            return False

        self.logger.info("🎯 IMU kalibrasyonu başlatılıyor...")
        await asyncio.sleep(2.0)  # Simülasyon kalibrasyonu
        self.logger.info("✅ IMU kalibrasyonu tamamlandı")
        return True

    def saglikli_mi(self) -> bool:
        """IMU sağlıklı mı?"""
        return self.aktif


class SimulasyonGPS(GPSInterface):
    """Simülasyon GPS sensörü"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger("SimulasyonGPS")
        self.aktif = False

    async def baslat(self) -> bool:
        """GPS sensörünü başlat"""
        try:
            self.aktif = True
            self.logger.info("✅ Simülasyon GPS başlatıldı")
            return True
        except Exception as e:
            self.logger.error(f"❌ GPS başlatma hatası: {e}")
            return False

    async def durdur(self):
        """GPS sensörünü durdur"""
        self.aktif = False
        self.logger.info("🛑 Simülasyon GPS durduruldu")

    async def veri_oku(self) -> Optional[GPSVeri]:
        """GPS verisi oku"""
        if not self.aktif:
            return None

        try:
            # Konum güncellemesi
            dt = time.time() - _simulation_manager.robot_durumu["timestamp"]
            _simulation_manager.konum_guncelle(dt)
            _simulation_manager.robot_durumu["timestamp"] = time.time()

            base_data = _simulation_manager.simulation_data["gps"]

            return GPSVeri(
                timestamp=datetime.now().isoformat(),
                gecerli=True,
                hata_mesaji=None,
                enlem=_simulation_manager.current_gps_position["enlem"],
                boylam=_simulation_manager.current_gps_position["boylam"],
                yukseklik=base_data["yukseklik"],
                uydu_sayisi=base_data["uydu_sayisi"],
                fix_kalitesi=base_data["fix_kalitesi"],
                hiz=abs(_simulation_manager.robot_durumu["linear_hiz"]),
                yön=_simulation_manager.robot_durumu["konum"]["heading"]
            )

        except Exception as e:
            self.logger.error(f"❌ GPS veri okuma hatası: {e}")
            return GPSVeri(
                timestamp=datetime.now().isoformat(),
                gecerli=False,
                hata_mesaji=str(e),
                enlem=0.0, boylam=0.0, yukseklik=0.0,
                uydu_sayisi=0, fix_kalitesi=0, hiz=0.0, yön=0.0
            )

    def saglikli_mi(self) -> bool:
        """GPS sağlıklı mı?"""
        return self.aktif


class SimulasyonGuc(GucInterface):
    """Simülasyon güç sensörü"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger("SimulasyonGuc")
        self.aktif = False
        self.batarya_seviyesi = 85.0  # %85 başlangıç

    async def baslat(self) -> bool:
        """Güç sensörünü başlat"""
        try:
            self.aktif = True
            self.logger.info("✅ Simülasyon güç sensörü başlatıldı")
            return True
        except Exception as e:
            self.logger.error(f"❌ Güç sensörü başlatma hatası: {e}")
            return False

    async def durdur(self):
        """Güç sensörünü durdur"""
        self.aktif = False
        self.logger.info("🛑 Simülasyon güç sensörü durduruldu")

    async def veri_oku(self) -> Optional[GucVeri]:
        """Güç verisi oku"""
        if not self.aktif:
            return None

        try:
            # base_data = _simulation_manager.simulation_data["guc"]

            # Hareket durumuna göre güç tüketimi
            if _simulation_manager.robot_durumu["hareket_halinde"]:
                akim = -1.5  # Hareket halinde daha fazla akım
            else:
                akim = -0.2  # Bekleme durumunda düşük akım

            # Basit batarya deşarj simülasyonu
            dt = 0.1  # Yaklaşık update süresi
            self.batarya_seviyesi -= abs(akim) * dt / 3600.0  # Saat bazında deşarj
            self.batarya_seviyesi = max(0.0, self.batarya_seviyesi)

            # Voltaj seviyeye göre
            voltaj = 10.5 + (12.6 - 10.5) * (self.batarya_seviyesi / 100.0)

            return GucVeri(
                timestamp=datetime.now().isoformat(),
                gecerli=True,
                hata_mesaji=None,
                voltaj=voltaj,
                akim=akim,
                guc=abs(voltaj * akim),
                batarya_seviyesi=self.batarya_seviyesi
            )

        except Exception as e:
            self.logger.error(f"❌ Güç veri okuma hatası: {e}")
            return GucVeri(
                timestamp=datetime.now().isoformat(),
                gecerli=False,
                hata_mesaji=str(e),
                voltaj=0.0, akim=0.0, guc=0.0, batarya_seviyesi=0.0
            )

    def saglikli_mi(self) -> bool:
        """Güç sensörü sağlıklı mı?"""
        return self.aktif


class SimulasyonTampon(TamponInterface):
    """Simülasyon tampon sensörü"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger("SimulasyonTampon")
        self.aktif = False

    async def baslat(self) -> bool:
        """Tampon sensörünü başlat"""
        try:
            self.aktif = True
            self.logger.info("✅ Simülasyon tampon sensörü başlatıldı")
            return True
        except Exception as e:
            self.logger.error(f"❌ Tampon sensörü başlatma hatası: {e}")
            return False

    async def durdur(self):
        """Tampon sensörünü durdur"""
        self.aktif = False
        self.logger.info("🛑 Simülasyon tampon sensörü durduruldu")

    async def veri_oku(self) -> Optional[TamponVeri]:
        """Tampon verisi oku"""
        if not self.aktif:
            return None

        try:
            # Simülasyonda bazen engel var gibi davran
            t = time.time()
            engel_var = (int(t) % 10) == 0  # Her 10 saniyede bir engel

            return TamponVeri(
                timestamp=datetime.now().isoformat(),
                gecerli=True,
                hata_mesaji=None,
                basildi=engel_var
            )

        except Exception as e:
            self.logger.error(f"❌ Tampon veri okuma hatası: {e}")
            return TamponVeri(
                timestamp=datetime.now().isoformat(),
                gecerli=False,
                hata_mesaji=str(e),
                basildi=False
            )

    def saglikli_mi(self) -> bool:
        """Tampon sensörü sağlıklı mı?"""
        return self.aktif


class SimulasyonEnkoder(EnkoderInterface):
    """Simülasyon encoder sensörü"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger("SimulasyonEnkoder")
        self.aktif = False
        self.sol_sayac = 0
        self.sag_sayac = 0

    async def baslat(self) -> bool:
        """Encoder sensörünü başlat"""
        try:
            self.aktif = True
            self.logger.info("✅ Simülasyon encoder sensörü başlatıldı")
            return True
        except Exception as e:
            self.logger.error(f"❌ Encoder sensörü başlatma hatası: {e}")
            return False

    async def durdur(self):
        """Encoder sensörünü durdur"""
        self.aktif = False
        self.logger.info("🛑 Simülasyon encoder sensörü durduruldu")

    async def veri_oku(self) -> Optional[EnkoderVeri]:
        """Encoder verisi oku"""
        if not self.aktif:
            return None

        try:
            # Hareket durumuna göre encoder artışı
            if _simulation_manager.robot_durumu["hareket_halinde"]:
                linear_vel = _simulation_manager.robot_durumu["linear_hiz"]
                angular_vel = _simulation_manager.robot_durumu["angular_hiz"]

                # Basit encoder simülasyonu
                dt = 0.1  # Yaklaşık update süresi
                teker_yaricapi = 0.033  # m

                # Linear hız encoder'a çevir
                linear_encoder_delta = int(linear_vel * dt / (2 * math.pi * teker_yaricapi) * 1000)

                # Angular hız encoder'a çevir (diferansiyel)
                angular_encoder_delta = int(angular_vel * dt * 50)

                self.sol_sayac += linear_encoder_delta - angular_encoder_delta
                self.sag_sayac += linear_encoder_delta + angular_encoder_delta

            return EnkoderVeri(
                timestamp=datetime.now().isoformat(),
                gecerli=True,
                hata_mesaji=None,
                sol_teker=self.sol_sayac,
                sag_teker=self.sag_sayac
            )

        except Exception as e:
            self.logger.error(f"❌ Encoder veri okuma hatası: {e}")
            return EnkoderVeri(
                timestamp=datetime.now().isoformat(),
                gecerli=False,
                hata_mesaji=str(e),
                sol_teker=0,
                sag_teker=0
            )

    def saglikli_mi(self) -> bool:
        """Encoder sensörü sağlıklı mı?"""
        return self.aktif


class SimulasyonAcilDurma(AcilDurmaInterface):
    """Simülasyon acil durdurma butonu"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger("SimulasyonAcilDurma")
        self.saglik_durumu = True
        self.acil_durum_aktif = False

    async def baslat(self) -> bool:
        """Acil durdurma butonunu başlat"""
        self.logger.debug("Simülasyon acil durdurma butonu başlatıldı")
        return True

    async def durdur(self):
        """Acil durdurma butonunu durdur"""
        self.logger.debug("Simülasyon acil durdurma butonu durduruldu")

    async def veri_oku(self) -> Optional[AcilDurmaVeri]:
        """Acil durdurma verisi oku"""
        try:
            # Simülasyonda acil durdurma genellikle pasif
            # Test amaçlı belirli koşullarda aktif olabilir
            test_aktif = False

            return AcilDurmaVeri(
                timestamp=datetime.now().isoformat(),
                gecerli=True,
                aktif=test_aktif
            )

        except Exception as e:
            self.logger.error(f"Acil durdurma verisi okunamadı: {e}")
            return AcilDurmaVeri(
                timestamp=datetime.now().isoformat(),
                gecerli=False,
                hata_mesaji=str(e)
            )

    def saglikli_mi(self) -> bool:
        """Acil durdurma sağlıklı mı?"""
        return self.saglik_durumu


class SimulasyonMotor(MotorInterface):
    """Simülasyon motor kontrolcüsü"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger("SimulasyonMotor")
        self.saglik_durumu = True

        # Motor durumları
        self.motor_durumu = MotorDurumuVeri(
            sol_hiz=0.0,
            sag_hiz=0.0,
            ana_firca=False,
            sol_firca=False,
            sag_firca=False,
            fan=False,
            motorlar_aktif=False
        )

        # Motor fizik parametreleri
        self.max_hiz = config.get("max_linear_speed", 0.5)  # m/s
        self.tekerlek_base = config.get("wheel_base", 0.235)  # metre

        # Simülasyon için log throttling
        self.last_log_time = 0.0
        self.log_interval = 5.0  # 5 saniyede bir log

    async def baslat(self) -> bool:
        """Motor sistemini başlat"""
        self.motor_durumu.motorlar_aktif = True
        self.logger.info("🎮 Simülasyon motor sistemi başlatıldı")
        return True

    async def durdur(self):
        """Motor sistemini durdur"""
        await self.acil_durdur()
        self.motor_durumu.motorlar_aktif = False
        self.logger.info("🎮 Simülasyon motor sistemi durduruldu")

    async def tekerlek_hiz_ayarla(self, sol_hiz: float, sag_hiz: float):
        """Tekerlek motorlarının hızını ayarla"""
        if not self.motor_durumu.motorlar_aktif:
            return

        # Hızları sınırla
        sol_hiz = max(-1.0, min(1.0, sol_hiz))
        sag_hiz = max(-1.0, min(1.0, sag_hiz))

        self.motor_durumu.sol_hiz = sol_hiz
        self.motor_durumu.sag_hiz = sag_hiz

        # 🎮 Simülasyon manager'ı güncelle
        # Differential drive kinematik ile robot hızını hesapla
        linear_velocity = (sol_hiz + sag_hiz) / 2 * self.max_hiz
        angular_velocity = (sag_hiz - sol_hiz) / self.tekerlek_base * self.max_hiz

        # Robot durumunu güncelle
        if abs(linear_velocity) > 0.01 or abs(angular_velocity) > 0.01:
            durum = "hareket"
        else:
            durum = "bekleme"

        _simulation_manager.robot_durumu_guncelle(durum, linear_velocity, angular_velocity)

        # Throttled logging
        current_time = time.time()
        if current_time - self.last_log_time > self.log_interval:
            self.logger.debug(f"🎮 Simülasyon tekerlek hızları: Sol={sol_hiz:.2f}, Sağ={sag_hiz:.2f}")
            self.logger.debug(f"🚀 Robot hızları: Linear={linear_velocity:.2f}m/s, Angular={angular_velocity:.2f}rad/s")
            self.last_log_time = current_time

    async def firca_kontrol(self, ana: bool, sol: bool, sag: bool):
        """Fırça motorlarını kontrol et"""
        self.motor_durumu.ana_firca = ana
        self.motor_durumu.sol_firca = sol
        self.motor_durumu.sag_firca = sag

        self.logger.debug(f"🎮 Simülasyon fırçalar: Ana={ana}, Sol={sol}, Sağ={sag}")

    async def fan_kontrol(self, aktif: bool):
        """Fan motorunu kontrol et"""
        self.motor_durumu.fan = aktif
        self.logger.debug(f"🎮 Simülasyon fan: {aktif}")

    async def acil_durdur(self):
        """Tüm motorları acil olarak durdur"""
        self.motor_durumu.sol_hiz = 0.0
        self.motor_durumu.sag_hiz = 0.0
        self.motor_durumu.ana_firca = False
        self.motor_durumu.sol_firca = False
        self.motor_durumu.sag_firca = False
        self.motor_durumu.fan = False

        self.logger.warning("🚨 Simülasyon acil durdurma!")

    def motor_durumu_al(self) -> MotorDurumuVeri:
        """Mevcut motor durumunu al"""
        return self.motor_durumu

    def saglikli_mi(self) -> bool:
        """Motor sistemi sağlıklı mı?"""
        return self.saglik_durumu


# === Hardware Factory ===

class SimulasyonHardwareFactory(HardwareFactory):
    """Simülasyon donanım fabrikası"""

    def __init__(self):
        self.logger = logging.getLogger("SimulasyonFactory")

    def imu_olustur(self, config: Dict[str, Any]) -> IMUInterface:
        """Simülasyon IMU oluştur"""
        return SimulasyonIMU(config)

    def gps_olustur(self, config: Dict[str, Any]) -> GPSInterface:
        """Simülasyon GPS oluştur"""
        return SimulasyonGPS(config)

    def guc_olustur(self, config: Dict[str, Any]) -> GucInterface:
        """Simülasyon güç sensörü oluştur"""
        return SimulasyonGuc(config)

    def tampon_olustur(self, config: Dict[str, Any]) -> TamponInterface:
        """Simülasyon tampon sensörü oluştur"""
        return SimulasyonTampon(config)

    def enkoder_olustur(self, config: Dict[str, Any]) -> EnkoderInterface:
        """Simülasyon encoder sensörü oluştur"""
        return SimulasyonEnkoder(config)

    def acil_durma_olustur(self, config: Dict[str, Any]) -> AcilDurmaInterface:
        """Simülasyon acil durdurma butonu oluştur"""
        return SimulasyonAcilDurma(config)

    def motor_olustur(self, config: Dict[str, Any]) -> MotorInterface:
        """Simülasyon motor kontrolcüsü oluştur"""
        return SimulasyonMotor(config)


# Global fonksiyonlar
def get_simulation_manager() -> SimulasyonDataManager:
    """Global simülasyon manager'ı döndür"""
    return _simulation_manager
