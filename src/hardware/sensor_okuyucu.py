"""
📡 Sensör Okuyucu - Modern HAL Tabanlı Implementasyon
Hacı Abi'nin yenilenmiş sensör yönetimi burada!

Bu sınıf HAL (Hardware Abstraction Layer) pattern'i kullanarak
sensör verilerini yönetir. Gerçek donanım ve simülasyon arasında
sorunsuz geçiş sağlar.

🔧 Özellikler:
- HAL pattern ile donanım abstraction
- Simülasyon ve gerçek donanım desteği
- Tutarlı Türkçe isimlendirme
- Modüler yapı
- Hata yönetimi
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from .hal.hardware import GercekHardwareFactory
from .hal.interfaces import (AcilDurmaInterface, AcilDurmaVeri, EnkoderInterface,
                             EnkoderVeri, GPSInterface, GPSVeri, GucInterface, GucVeri,
                             HardwareFactory, IMUInterface, IMUVeri, TamponInterface,
                             TamponVeri)
from .hal.simulation import SimulasyonHardwareFactory, get_simulation_manager


class SensorOkuyucu:
    """
    📡 Ana Sensör Okuyucu Sınıfı

    HAL pattern kullanarak tüm sensörleri yönetir.
    Simülasyon ve gerçek donanım arasında sorunsuz geçiş sağlar.
    """

    def __init__(self, sensor_config: Dict[str, Any], environment_manager, smart_config: Optional[Dict[str, Any]] = None):
        """Sensör okuyucu başlatıcı"""
        self.config = sensor_config
        self.smart_config = smart_config or {}
        self.environment_manager = environment_manager
        self.logger = logging.getLogger("SensorOkuyucu")

        # Simülasyon modu kontrolü
        self.simülasyon_modu = self.environment_manager.is_simulation_mode

        # Sensör durumları
        self.sensörler_aktif = False
        self.son_okuma_zamanı = {}

        # Hardware factory seçimi
        if self.simülasyon_modu:
            self.hardware_factory: HardwareFactory = SimulasyonHardwareFactory()
            self.logger.info("🎮 Simülasyon modu - Sahte sensörler kullanılacak")
        else:
            self.hardware_factory = GercekHardwareFactory()
            self.logger.info("🔧 Gerçek donanım modu - Fiziksel sensörler kullanılacak")

        # Sensör interfaceleri
        self.imu_sensor: Optional[IMUInterface] = None
        self.gps_sensor: Optional[GPSInterface] = None
        self.guc_sensor: Optional[GucInterface] = None
        self.tampon_sensor: Optional[TamponInterface] = None
        self.enkoder_sensor: Optional[EnkoderInterface] = None
        self.acil_durma_sensor: Optional[AcilDurmaInterface] = None

        # Sensörleri başlat
        self.logger.info(f"📡 Sensör okuyucu başlatıldı (Simülasyon: {self.simülasyon_modu})")
        self._sensörleri_başlat()

    def _sensörleri_başlat(self):
        """Sensörleri başlat"""
        try:
            # IMU sensörü
            imu_config = self.config.get("imu", {})
            if imu_config.get("enabled", True):
                self.imu_sensor = self.hardware_factory.imu_olustur(imu_config)

            # GPS sensörü
            gps_config = self.config.get("gps", {})
            if gps_config.get("enabled", True):
                self.gps_sensor = self.hardware_factory.gps_olustur(gps_config)

            # Güç sensörü
            guc_config = self.config.get("guc", {})
            if guc_config.get("enabled", True):
                self.guc_sensor = self.hardware_factory.guc_olustur(guc_config)

            # Tampon sensörü
            tampon_config = self.config.get("tampon", {})
            if tampon_config.get("enabled", True):
                self.tampon_sensor = self.hardware_factory.tampon_olustur(tampon_config)

            # Encoder sensörü
            enkoder_config = self.config.get("enkoder", {})
            if enkoder_config.get("enabled", True):
                self.enkoder_sensor = self.hardware_factory.enkoder_olustur(enkoder_config)

            # Acil durdurma butonu
            acil_durma_config = self.config.get("acil_durma", {})
            if acil_durma_config.get("enabled", True):
                self.acil_durma_sensor = self.hardware_factory.acil_durma_olustur(acil_durma_config)

            self.logger.info("✅ Sensör interfaceleri oluşturuldu")

        except Exception as e:
            self.logger.error(f"❌ Sensör başlatma hatası: {e}", exc_info=True)
            raise

    async def başlat(self) -> bool:
        """Tüm sensörleri başlat"""
        try:
            self.logger.info("🔧 Sensörler başlatılıyor...")

            başlatma_sonuçları = []

            # IMU başlat
            if self.imu_sensor:
                sonuç = await self.imu_sensor.baslat()
                başlatma_sonuçları.append(("IMU", sonuç))

            # GPS başlat
            if self.gps_sensor:
                sonuç = await self.gps_sensor.baslat()
                başlatma_sonuçları.append(("GPS", sonuç))

            # Güç sensörü başlat
            if self.guc_sensor:
                sonuç = await self.guc_sensor.baslat()
                başlatma_sonuçları.append(("Güç", sonuç))

            # Tampon sensörü başlat
            if self.tampon_sensor:
                sonuç = await self.tampon_sensor.baslat()
                başlatma_sonuçları.append(("Tampon", sonuç))

            # Encoder başlat
            if self.enkoder_sensor:
                sonuç = await self.enkoder_sensor.baslat()
                başlatma_sonuçları.append(("Encoder", sonuç))

            # Acil durdurma başlat
            if self.acil_durma_sensor:
                sonuç = await self.acil_durma_sensor.baslat()
                başlatma_sonuçları.append(("Acil Durma", sonuç))

            # Sonuçları logla
            başarılı_sensörler = []
            başarısız_sensörler = []

            for sensor_adı, sonuç in başlatma_sonuçları:
                if sonuç:
                    başarılı_sensörler.append(sensor_adı)
                else:
                    başarısız_sensörler.append(sensor_adı)

            if başarılı_sensörler:
                self.logger.info(f"✅ Başarılı sensörler: {', '.join(başarılı_sensörler)}")

            if başarısız_sensörler:
                self.logger.warning(f"⚠️ Başarısız sensörler: {', '.join(başarısız_sensörler)}")

            # En az bir sensör başarılı ise devam et
            if başarılı_sensörler:
                self.sensörler_aktif = True
                self.logger.info("✅ Sensör sistemi hazır")
                return True
            else:
                self.logger.error("❌ Hiçbir sensör başlatılamadı")
                return False

        except Exception as e:
            self.logger.error(f"❌ Sensör başlatma hatası: {e}", exc_info=True)
            return False

    async def durdur(self):
        """Tüm sensörleri durdur"""
        try:
            self.logger.info("🛑 Sensörler durduruluyor...")

            # Tüm sensörleri durdur
            if self.imu_sensor:
                await self.imu_sensor.durdur()

            if self.gps_sensor:
                await self.gps_sensor.durdur()

            if self.guc_sensor:
                await self.guc_sensor.durdur()

            if self.tampon_sensor:
                await self.tampon_sensor.durdur()

            if self.enkoder_sensor:
                await self.enkoder_sensor.durdur()

            if self.acil_durma_sensor:
                await self.acil_durma_sensor.durdur()

            self.sensörler_aktif = False
            self.logger.info("✅ Tüm sensörler durduruldu")

        except Exception as e:
            self.logger.error(f"❌ Sensör durdurma hatası: {e}", exc_info=True)

    async def tüm_sensör_verilerini_oku(self) -> Dict[str, Any]:
        """
        📊 Tüm sensörlerden paralel veri okuma

        Returns:
            Dict: Tüm sensör verileri
        """
        if not self.sensörler_aktif:
            self.logger.warning("⚠️ Sensörler aktif değil, okuma yapılamıyor")
            return {}

        try:
            # Paralel okuma görevleri
            görevler = {}

            if self.imu_sensor:
                görevler["imu"] = self.imu_sensor.veri_oku()

            if self.gps_sensor:
                görevler["gps"] = self.gps_sensor.veri_oku()

            if self.guc_sensor:
                görevler["guc"] = self.guc_sensor.veri_oku()

            if self.tampon_sensor:
                görevler["tampon"] = self.tampon_sensor.veri_oku()

            if self.enkoder_sensor:
                görevler["enkoder"] = self.enkoder_sensor.veri_oku()

            if self.acil_durma_sensor:
                görevler["acil_durma"] = self.acil_durma_sensor.veri_oku()

            # Görevleri paralel çalıştır
            sonuçlar = await asyncio.gather(*görevler.values(), return_exceptions=True)

            # Sonuçları organize et
            sensör_verileri = {}
            for sensor_adı, sonuç in zip(görevler.keys(), sonuçlar):
                if isinstance(sonuç, Exception):
                    self.logger.error(f"❌ {sensor_adı} sensörü okuma hatası: {sonuç}")
                    sensör_verileri[sensor_adı] = None
                else:
                    sensör_verileri[sensor_adı] = sonuç

            # Genel bilgileri ekle
            sensör_verileri["timestamp"] = datetime.now().isoformat()
            sensör_verileri["sistem_durumu"] = {
                "sensörler_aktif": self.sensörler_aktif,
                "simülasyon_modu": self.simülasyon_modu,
                "sağlıklı_sensörler": self._sağlıklı_sensörleri_say()
            }

            # Son okuma zamanını güncelle
            self.son_okuma_zamanı["genel"] = datetime.now().isoformat()

            return sensör_verileri

        except Exception as e:
            self.logger.error(f"❌ Sensör verisi okuma hatası: {e}", exc_info=True)
            return {}

    def _sağlıklı_sensörleri_say(self) -> Dict[str, bool]:
        """Sağlıklı sensörleri say"""
        durum = {}

        if self.imu_sensor:
            durum["imu"] = self.imu_sensor.saglikli_mi()

        if self.gps_sensor:
            durum["gps"] = self.gps_sensor.saglikli_mi()

        if self.guc_sensor:
            durum["guc"] = self.guc_sensor.saglikli_mi()

        if self.tampon_sensor:
            durum["tampon"] = self.tampon_sensor.saglikli_mi()

        if self.enkoder_sensor:
            durum["enkoder"] = self.enkoder_sensor.saglikli_mi()

        if self.acil_durma_sensor:
            durum["acil_durma"] = self.acil_durma_sensor.saglikli_mi()

        return durum

    async def imu_verisi_oku(self) -> Optional[IMUVeri]:
        """🧭 IMU sensöründen veri oku"""
        if not self.imu_sensor:
            return None

        try:
            veri = await self.imu_sensor.veri_oku()
            self.son_okuma_zamanı["imu"] = datetime.now().isoformat()
            return veri
        except Exception as e:
            self.logger.error(f"❌ IMU okuma hatası: {e}")
            return None

    async def gps_verisi_oku(self) -> Optional[GPSVeri]:
        """🗺️ GPS sensöründen veri oku"""
        if not self.gps_sensor:
            return None

        try:
            veri = await self.gps_sensor.veri_oku()
            self.son_okuma_zamanı["gps"] = datetime.now().isoformat()
            return veri
        except Exception as e:
            self.logger.error(f"❌ GPS okuma hatası: {e}")
            return None

    async def güç_verisi_oku(self) -> Optional[GucVeri]:
        """🔋 Güç sensöründen veri oku"""
        if not self.guc_sensor:
            return None

        try:
            veri = await self.guc_sensor.veri_oku()
            self.son_okuma_zamanı["guc"] = datetime.now().isoformat()
            return veri
        except Exception as e:
            self.logger.error(f"❌ Güç okuma hatası: {e}")
            return None

    async def tampon_verisi_oku(self) -> Optional[TamponVeri]:
        """🚧 Tampon sensöründen veri oku"""
        if not self.tampon_sensor:
            return None

        try:
            veri = await self.tampon_sensor.veri_oku()
            self.son_okuma_zamanı["tampon"] = datetime.now().isoformat()
            return veri
        except Exception as e:
            self.logger.error(f"❌ Tampon okuma hatası: {e}")
            return None

    async def enkoder_verisi_oku(self) -> Optional[EnkoderVeri]:
        """⚙️ Encoder sensöründen veri oku"""
        if not self.enkoder_sensor:
            return None

        try:
            veri = await self.enkoder_sensor.veri_oku()
            self.son_okuma_zamanı["enkoder"] = datetime.now().isoformat()
            return veri
        except Exception as e:
            self.logger.error(f"❌ Encoder okuma hatası: {e}")
            return None

    async def acil_durma_verisi_oku(self) -> Optional[AcilDurmaVeri]:
        """🚨 Acil durdurma butonundan veri oku"""
        if not self.acil_durma_sensor:
            return None

        try:
            veri = await self.acil_durma_sensor.veri_oku()
            self.son_okuma_zamanı["acil_durma"] = datetime.now().isoformat()
            return veri
        except Exception as e:
            self.logger.error(f"❌ Acil durma okuma hatası: {e}")
            return None

    async def imu_kalibrasyonu_yap(self) -> bool:
        """🎯 IMU kalibrasyonu yap"""
        if not self.imu_sensor:
            self.logger.warning("⚠️ IMU sensörü mevcut değil, kalibrasyon yapılamıyor")
            return False

        try:
            self.logger.info("🎯 IMU kalibrasyonu başlatılıyor...")
            sonuç = await self.imu_sensor.kalibrasyon_yap()

            if sonuç:
                self.logger.info("✅ IMU kalibrasyonu başarılı")
            else:
                self.logger.error("❌ IMU kalibrasyonu başarısız")

            return sonuç

        except Exception as e:
            self.logger.error(f"❌ IMU kalibrasyon hatası: {e}", exc_info=True)
            return False

    def robot_durumu_güncelle(self, durum: str, linear_hız: float = 0.0, angular_hız: float = 0.0):
        """
        🤖 Robot durumunu güncelle (simülasyon için)

        Args:
            durum: Robot durumu ("bekleme", "hareket", "sarj", "gorev")
            linear_hız: Linear hız (m/s)
            angular_hız: Angular hız (rad/s)
        """
        if self.simülasyon_modu:
            try:
                simulation_manager = get_simulation_manager()
                simulation_manager.robot_durumu_guncelle(durum, linear_hız, angular_hız)
                self.logger.debug(f"🔄 Robot durumu güncellendi: {durum}")
            except Exception as e:
                self.logger.error(f"❌ Robot durumu güncelleme hatası: {e}")

    def sensör_durumu_al(self) -> Dict[str, Any]:
        """📊 Sensör durumu bilgisi al"""
        return {
            "aktif": self.sensörler_aktif,
            "simülasyon_modu": self.simülasyon_modu,
            "sağlıklı_sensörler": self._sağlıklı_sensörleri_say(),
            "son_okuma_zamanları": self.son_okuma_zamanı.copy(),
            "toplam_sensör_sayısı": len([s for s in [
                self.imu_sensor, self.gps_sensor, self.guc_sensor,
                self.tampon_sensor, self.enkoder_sensor, self.acil_durma_sensor
            ] if s is not None])
        }

    def __del__(self):
        """Yıkıcı - sensörleri temizle"""
        try:
            if hasattr(self, 'logger'):
                self.logger.info("👋 Sensör okuyucu kapatılıyor...")
        except Exception:
            pass  # Yıkıcıda hata ignore et
