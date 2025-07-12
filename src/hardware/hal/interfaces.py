"""
🔧 Hardware Abstraction Layer (HAL) - Interfaces
Hacı Abi'nin HAL pattern implementasyonu burada!

Bu modül, donanım abstraction layer'ının arayüzlerini tanımlar.
Gerçek donanım ve simülasyon implementasyonları bu arayüzleri kullanır.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class SensorVeri:
    """Temel sensör verisi"""
    timestamp: str
    gecerli: bool
    hata_mesaji: Optional[str] = None


@dataclass
class IMUVeri(SensorVeri):
    """IMU sensör verisi"""
    ivme_x: float = 0.0
    ivme_y: float = 0.0
    ivme_z: float = 0.0
    acisal_hiz_x: float = 0.0
    acisal_hiz_y: float = 0.0
    acisal_hiz_z: float = 0.0
    roll: float = 0.0
    pitch: float = 0.0
    yaw: float = 0.0
    sicaklik: float = 0.0


@dataclass
class GPSVeri(SensorVeri):
    """GPS sensör verisi"""
    enlem: float = 0.0
    boylam: float = 0.0
    yukseklik: float = 0.0
    uydu_sayisi: int = 0
    fix_kalitesi: int = 0
    hiz: float = 0.0
    yön: float = 0.0


@dataclass
class GucVeri(SensorVeri):
    """Güç sensör verisi"""
    voltaj: float = 0.0
    akim: float = 0.0
    guc: float = 0.0
    batarya_seviyesi: float = 0.0  # %0-100


@dataclass
class TamponVeri(SensorVeri):
    """Tampon sensör verisi"""
    basildi: bool = False


@dataclass
class EnkoderVeri(SensorVeri):
    """Encoder sensör verisi"""
    sol_teker: int = 0
    sag_teker: int = 0


@dataclass
class AcilDurmaVeri(SensorVeri):
    """Acil durdurma butonu verisi"""
    aktif: bool = False


@dataclass
class MotorDurumuVeri:
    """Motor durumu verisi"""
    sol_hiz: float = 0.0      # -1.0 ile 1.0 arası
    sag_hiz: float = 0.0      # -1.0 ile 1.0 arası
    ana_firca: bool = False
    sol_firca: bool = False
    sag_firca: bool = False
    fan: bool = False
    motorlar_aktif: bool = False
    dogrusal_hiz: float = 0.0  # m/s
    acisal_hiz: float = 0.0    # rad/s
    saglikli: bool = True       # Motor sistemi sağlıklı mı?


# === HAL Interfaces ===

class MotorInterface(ABC):
    """Motor kontrol arayüzü"""

    @abstractmethod
    async def baslat(self) -> bool:
        """Motor sistemini başlat"""
        pass

    @abstractmethod
    async def durdur(self):
        """Motor sistemini durdur"""
        pass

    @abstractmethod
    async def tekerlek_hiz_ayarla(self, sol_hiz: float, sag_hiz: float):
        """Tekerlek motorlarının hızını ayarla (-1.0 ile 1.0 arası)"""
        pass

    @abstractmethod
    async def firca_kontrol(self, ana: bool, sol: bool, sag: bool):
        """Fırça motorlarını kontrol et"""
        pass

    @abstractmethod
    async def fan_kontrol(self, aktif: bool):
        """Fan motorunu kontrol et"""
        pass

    @abstractmethod
    async def acil_durdur(self):
        """Tüm motorları acil olarak durdur"""
        pass

    @abstractmethod
    def motor_durumu_al(self) -> MotorDurumuVeri:
        """Mevcut motor durumunu al"""
        pass

    @abstractmethod
    def saglikli_mi(self) -> bool:
        """Motor sistemi sağlıklı mı?"""
        pass


class SensorInterface(ABC):
    """Temel sensör arayüzü"""

    @abstractmethod
    async def baslat(self) -> bool:
        """Sensörü başlat"""
        pass

    @abstractmethod
    async def durdur(self):
        """Sensörü durdur"""
        pass

    @abstractmethod
    async def veri_oku(self) -> Optional[SensorVeri]:
        """Sensörden veri oku"""
        pass

    @abstractmethod
    def saglikli_mi(self) -> bool:
        """Sensör sağlıklı mı?"""
        pass


class IMUInterface(SensorInterface):
    """IMU sensör arayüzü"""

    @abstractmethod
    async def veri_oku(self) -> Optional[IMUVeri]:
        """IMU verisi oku"""
        pass

    @abstractmethod
    async def kalibrasyon_yap(self) -> bool:
        """IMU kalibrasyonu yap"""
        pass


class GPSInterface(SensorInterface):
    """GPS sensör arayüzü"""

    @abstractmethod
    async def veri_oku(self) -> Optional[GPSVeri]:
        """GPS verisi oku"""
        pass


class GucInterface(SensorInterface):
    """Güç sensör arayüzü"""

    @abstractmethod
    async def veri_oku(self) -> Optional[GucVeri]:
        """Güç verisi oku"""
        pass


class TamponInterface(SensorInterface):
    """Tampon sensör arayüzü"""

    @abstractmethod
    async def veri_oku(self) -> Optional[TamponVeri]:
        """Tampon verisi oku"""
        pass


class EnkoderInterface(SensorInterface):
    """Encoder sensör arayüzü"""

    @abstractmethod
    async def veri_oku(self) -> Optional[EnkoderVeri]:
        """Encoder verisi oku"""
        pass


class AcilDurmaInterface(SensorInterface):
    """Acil durdurma butonu arayüzü"""

    @abstractmethod
    async def veri_oku(self) -> Optional[AcilDurmaVeri]:
        """Acil durdurma verisi oku"""
        pass


class HardwareFactory(ABC):
    """Donanım fabrika arayüzü"""

    @abstractmethod
    def imu_olustur(self, config: Dict[str, Any]) -> IMUInterface:
        """IMU sensörü oluştur"""
        pass

    @abstractmethod
    def gps_olustur(self, config: Dict[str, Any]) -> GPSInterface:
        """GPS sensörü oluştur"""
        pass

    @abstractmethod
    def guc_olustur(self, config: Dict[str, Any]) -> GucInterface:
        """Güç sensörü oluştur"""
        pass

    @abstractmethod
    def tampon_olustur(self, config: Dict[str, Any]) -> TamponInterface:
        """Tampon sensörü oluştur"""
        pass

    @abstractmethod
    def enkoder_olustur(self, config: Dict[str, Any]) -> EnkoderInterface:
        """Encoder sensörü oluştur"""
        pass

    @abstractmethod
    def acil_durma_olustur(self, config: Dict[str, Any]) -> AcilDurmaInterface:
        """Acil durdurma butonu oluştur"""
        pass

    @abstractmethod
    def motor_olustur(self, config: Dict[str, Any]) -> MotorInterface:
        """Motor kontrolcüsü oluştur"""
        pass
