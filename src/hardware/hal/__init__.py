"""
🔧 Hardware Abstraction Layer (HAL) Package
Hacı Abi'nin HAL sistemi burada!

Bu package, donanım abstraction layer'ı sağlar.
Simülasyon ve gerçek donanım arasında sorunsuz geçiş imkanı verir.
"""

# Kamera HAL imports
from .fiziksel_kamera import FizikselKamera

# Existing HAL imports
from .hardware import GercekHardwareFactory
from .interfaces import (  # Veri sınıfları; Interface sınıfları; Factory interface
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
    SensorInterface,
    SensorVeri,
    TamponInterface,
    TamponVeri,
)
from .kamera_factory import KameraFactory
from .kamera_interface import KameraInterface
from .simulasyon_kamerasi import SimulasyonKamerasi
from .simulation import SimulasyonHardwareFactory, get_simulation_manager

__all__ = [
    # Kamera HAL
    "KameraInterface", "SimulasyonKamerasi", "FizikselKamera", "KameraFactory",

    # Veri sınıfları
    "SensorVeri", "IMUVeri", "GPSVeri", "GucVeri", "TamponVeri", "EnkoderVeri", "AcilDurmaVeri", "MotorDurumuVeri",

    # Interface sınıfları
    "SensorInterface", "IMUInterface", "GPSInterface", "GucInterface",
    "TamponInterface", "EnkoderInterface", "AcilDurmaInterface", "MotorInterface",

    # Factory sınıfları
    "HardwareFactory", "SimulasyonHardwareFactory", "GercekHardwareFactory",

    # Utility fonksiyonlar
    "get_simulation_manager"
]
