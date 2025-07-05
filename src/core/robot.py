"""
🤖 Bahçe Asistanı (OBA) - Ana Robot Sınıfı
Hacı Abi'nin emeği burada!

Bu sınıf tüm robot sistemlerini koordine eder.
Durum makinesi prensibi ile çalışır - güvenli ve öngörülebilir.
"""

import asyncio
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict

from ai.karar_verici import KararVerici
from core.guvenlik_sistemi import GuvenlikSistemi
from core.smart_config import load_smart_config
from hardware.motor_kontrolcu import MotorKontrolcu
from hardware.sensor_okuyucu import SensorOkuyucu
from navigation.konum_takipci import KonumTakipci
from navigation.rota_planlayici import RotaPlanlayici
from vision.kamera_islemci import KameraIslemci


class RobotDurumu(Enum):
    """Robot'un mevcut durumu"""
    BASLANGIC = "baslangic"
    BEKLEME = "bekleme"
    GOREV_YAPMA = "gorev_yapma"
    SARJ_ARAMA = "sarj_arama"
    SARJ_OLMA = "sarj_olma"
    ACIL_DURUM = "acil_durum"
    HATA = "hata"


class BahceRobotu:
    """
    🌱 Ana Bahçe Asistanı (OBA) Sınıfı

    Bu sınıf robotun beyni! Tüm subsistemi koordine eder:
    - Motor kontrolü
    - Sensör okuma
    - Navigasyon
    - Görev yönetimi
    - Güvenlik
    """

    def __init__(self, config_path: str = "config/robot_config.yaml"):
        """Robot'u başlat"""
        # Önce temel durumları ayarla
        self.durum = RobotDurumu.BASLANGIC
        self.onceki_durum = None

        # Logger'ı global setup'tan al - kendi logging setup yapmıyoruz!
        self.logger = logging.getLogger("BahceRobotu")

        # Akıllı config yükle
        self.config = self._load_config(config_path)

        # Akıllı config bilgilerini göster
        self._log_smart_config_info()

        self.logger.info("🤖 Hacı Abi'nin Bahçe Asistanı (OBA) başlatılıyor...")

        # Alt sistemleri başlat
        self._init_subsystems()

        # Robot durumu
        self.gorev_aktif = False
        self.sarj_gerekli = False
        self.acil_durum_aktif = False

        # Ana döngü kontrolü
        self.calisma_durumu = True

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Akıllı konfigürasyon yükleme - Ortam bazlı"""
        try:
            # 🧠 Akıllı config yükleme - Ortam tespiti ile
            self.logger.info("🧠 Akıllı konfigürasyon yükleniyor...")
            config = load_smart_config(config_path)

            # Ortam bilgilerini logla
            runtime_info = config.get("runtime", {})
            env_type = runtime_info.get("environment_type", "unknown")
            is_sim = runtime_info.get("is_simulation", False)

            self.logger.info(f"🌍 Tespit edilen ortam: {env_type}")
            self.logger.info(f"🎮 Simülasyon modu: {'Evet' if is_sim else 'Hayır'}")

            # Donanım yeteneklerini logla
            capabilities = runtime_info.get("capabilities", {})
            active_caps = [cap for cap, available in capabilities.items() if available]
            if active_caps:
                self.logger.info(f"🔧 Aktif donanım: {', '.join(active_caps)}")

            return config

        except Exception as e:
            self.logger.error(f"❌ Akıllı config yükleme hatası: {e}")
            self.logger.warning("⚠️ Varsayılan config'e geri döndü")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Varsayılan konfigürasyon - Akıllı config başarısız olursa"""
        self.logger.warning("⚠️ Akıllı config başarısız, varsayılan ayarlar kullanılıyor")
        return {
            "robot": {
                "name": "OBA_Emergency",
                "version": "1.0.0",
                "debug_mode": True
            },
            "simulation": {
                "enabled": True  # Güvenli varsayılan
            },
            "motors": {
                "type": "simulation"  # Güvenli varsayılan
            },
            "sensors": {
                "mock_enabled": True  # Güvenli varsayılan
            },
            "logging": {
                "level": "INFO",
                "console": {"enabled": True},
                "file": {"enabled": True, "path": "logs/robot.log"}
            },
            "web_interface": {
                "enabled": True,
                "host": "127.0.0.1",
                "port": 5000,
                "debug": True
            },
            "runtime": {
                "environment_type": "unknown",
                "is_simulation": True,
                "is_hardware": False,
                "capabilities": {},
                "detected_at": "emergency_fallback"
            }
        }

    def _init_subsystems(self):
        """Alt sistemleri başlat"""
        self.logger.info("🔧 Alt sistemler başlatılıyor...")

        # Hardware - güvenli başlatma
        try:
            self.motor_kontrolcu = MotorKontrolcu(
                self.config.get("hardware", {}).get("motors", {}))
            self.logger.info("✅ Motor kontrolcü hazır")
        except Exception as e:
            self.logger.error(f"❌ Motor kontrolcü hatası: {e}")
            self.motor_kontrolcu = None

        try:
            self.sensor_okuyucu = SensorOkuyucu(
                self.config.get("hardware", {}).get("sensors", {}),
                smart_config=self.config)
            self.logger.info("✅ Sensör okuyucu hazır")
        except Exception as e:
            self.logger.error(f"❌ Sensör okuyucu hatası: {e}")
            self.sensor_okuyucu = None

        # Navigation - güvenli başlatma
        try:
            self.konum_takipci = KonumTakipci(
                self.config.get("navigation", {}))
            self.logger.info("✅ Konum takipçi hazır")
        except Exception as e:
            self.logger.error(f"❌ Konum takipçi hatası: {e}")
            self.konum_takipci = None

        try:
            self.rota_planlayici = RotaPlanlayici(
                self.config.get("navigation", {}))
            self.logger.info("✅ Rota planlayıcı hazır")
        except Exception as e:
            self.logger.error(f"❌ Rota planlayıcı hatası: {e}")
            self.rota_planlayici = None

        # Vision & AI - güvenli başlatma
        try:
            self.kamera_islemci = KameraIslemci(self.config.get(
                "hardware", {}).get("sensors", {}).get("camera", {}))
            self.logger.info("✅ Kamera işlemci hazır")
        except Exception as e:
            self.logger.error(f"❌ Kamera işlemci hatası: {e}")
            self.kamera_islemci = None

        try:
            self.karar_verici = KararVerici(self.config.get("ai", {}))
            self.logger.info("✅ Karar verici hazır")
        except Exception as e:
            self.logger.error(f"❌ Karar verici hatası: {e}")
            self.karar_verici = None

        # Security - güvenli başlatma
        try:
            self.guvenlik_sistemi = GuvenlikSistemi(
                self.config.get("safety", {}))
            self.logger.info("✅ Güvenlik sistemi hazır")
        except Exception as e:
            self.logger.error(f"❌ Güvenlik sistemi hatası: {e}")
            self.guvenlik_sistemi = None

        # Başarılı başlatılan sistem sayısı
        active_systems = sum(1 for system in [
            self.motor_kontrolcu, self.sensor_okuyucu, self.konum_takipci,
            self.rota_planlayici, self.kamera_islemci, self.karar_verici,
            self.guvenlik_sistemi
        ] if system is not None)

        self.logger.info(f"✅ {active_systems}/7 alt sistem hazır!")

        # Kritik sistemler eksikse uyarı ver
        if self.motor_kontrolcu is None or self.sensor_okuyucu is None:
            self.logger.warning("⚠️ Kritik sistemler eksik, sınırlı mod aktif!")
            self.durum = RobotDurumu.BEKLEME
        else:
            self.logger.info("🚀 Tüm kritik sistemler hazır!")

    async def ana_dongu(self):
        """
        🔄 Robot'un ana döngüsü

        Bu fonksiyon robot'un beyninin ana döngüsü.
        Durum makinesine göre hangi işlemlerin yapılacağına karar verir.
        """
        self.logger.info("🚀 Ana döngü başlatıldı!")

        while self.calisma_durumu:
            try:
                # Sensör verilerini oku
                sensor_data = await self._sensor_verilerini_oku()

                # Güvenlik kontrolü
                guvenlik_durumu = None
                if self.guvenlik_sistemi is not None:
                    guvenlik_durumu = self.guvenlik_sistemi.kontrol_et(sensor_data)

                if guvenlik_durumu and guvenlik_durumu.acil_durum:
                    await self._acil_durum_isle(guvenlik_durumu.sebep)
                    continue

                # Konum güncelle
                if self.konum_takipci is not None:
                    await self.konum_takipci.konum_guncelle(sensor_data)

                # Durum makinesine göre işlem yap
                await self._durum_makinesini_isle(sensor_data)

                # Kısa bekleme
                await asyncio.sleep(0.1)  # 10 Hz ana döngü

            except asyncio.CancelledError:
                self.logger.info("🛑 Ana döngü iptal edildi")
                break
            except Exception as e:
                self.logger.error(f"❌ Ana döngü hatası: {e}")
                await self._hata_isle(str(e))
                await asyncio.sleep(1)

        self.logger.info("🛑 Ana döngü temiz şekilde sonlandı")

    async def _sensor_verilerini_oku(self) -> Dict[str, Any]:
        """Tüm sensörlerden veri oku"""
        if self.sensor_okuyucu is None:
            # Simülasyon verisi döndür
            return {
                "timestamp": datetime.now().isoformat(),
                "battery": {"voltage": 12.5, "current": 1.2, "percentage": 85},
                "sensors": {"ultrasonic": {"distance": 50.0}, "bump": False},
                "imu": {"roll": 0.0, "pitch": 0.0, "yaw": 0.0},
                "gps": {"latitude": 39.9334, "longitude": 32.8597, "fix": False}
            }
        return await self.sensor_okuyucu.tum_verileri_oku()

    async def sensor_verilerini_al(self) -> Dict[str, Any]:
        """Tüm sensörlerden veri al (public interface)"""
        return await self._sensor_verilerini_oku()

    async def _durum_makinesini_isle(self, sensor_data: Dict[str, Any]):
        """
        🧠 Durum Makinesinin Beyni

        Robot'un ne yapacağına durum makinesine göre karar verir.
        """
        self.logger.debug(f"🔄 Durum: {self.durum.value}")

        if self.durum == RobotDurumu.BASLANGIC:
            await self._baslangic_durumu()

        elif self.durum == RobotDurumu.BEKLEME:
            await self._bekleme_durumu(sensor_data)

        elif self.durum == RobotDurumu.GOREV_YAPMA:
            await self._gorev_yapma_durumu(sensor_data)

        elif self.durum == RobotDurumu.SARJ_ARAMA:
            await self._sarj_arama_durumu(sensor_data)

        elif self.durum == RobotDurumu.SARJ_OLMA:
            await self._sarj_olma_durumu(sensor_data)

        elif self.durum == RobotDurumu.ACIL_DURUM:
            await self._acil_durum_bekle()

        elif self.durum == RobotDurumu.HATA:
            await self._hata_durumu()

    async def _baslangic_durumu(self):
        """🏁 Robot başlatıldığında yapılan işlemler"""
        self.logger.info("🏁 Robot başlatılıyor...")

        # Sistem kontrolü - None kontrolü ile güvenli çalışma
        if self.motor_kontrolcu is not None:
            await self.motor_kontrolcu.test_et()
        if self.sensor_okuyucu is not None:
            await self.sensor_okuyucu.kalibrasyon_yap()

        # İlk konum belirle
        if self.konum_takipci is not None:
            await self.konum_takipci.ilk_konum_belirle()

        self.durum_degistir(RobotDurumu.BEKLEME)
        self.logger.info("✅ Robot hazır! Görev bekliyor.")

    async def _bekleme_durumu(self, sensor_data: Dict[str, Any]):
        """⏸️ Robot beklemede - görev veya şarj kontrolü"""
        batarya_seviye = sensor_data.get("batarya", {}).get("seviye", 100)

        if batarya_seviye < self.config.get("missions", {}).get("charging", {}).get("battery_low_threshold", 20):
            self.durum_degistir(RobotDurumu.SARJ_ARAMA)
            return

        # Görev var mı kontrol et
        if self.gorev_aktif:
            self.durum_degistir(RobotDurumu.GOREV_YAPMA)

    async def _gorev_yapma_durumu(self, sensor_data: Dict[str, Any]):
        """🌱 Ana görev - biçme işlemi"""
        # Batarya kontrolü
        batarya_seviye = sensor_data.get("batarya", {}).get("seviye", 100)
        if batarya_seviye < self.config.get("missions", {}).get("charging", {}).get("battery_low_threshold", 20):
            self.durum_degistir(RobotDurumu.SARJ_ARAMA)
            return

        # Kamera ile engel kontrolü
        kamera_data = await self.kamera_islemci.engel_analiz_et()

        # AI karar verme
        karar = await self.karar_verici.next_action_belirle(sensor_data, kamera_data)

        # Motor hareketini uygula - Dict'i HareketKomut'a çevir
        from hardware.motor_kontrolcu import HareketKomut
        hareket_komut = HareketKomut(
            linear_hiz=karar.hareket.get("linear", 0.0),
            angular_hiz=karar.hareket.get("angular", 0.0)
        )
        await self.motor_kontrolcu.hareket_uygula(hareket_komut)

        # Fırçaları çalıştır
        await self.motor_kontrolcu.fircalari_calistir(True)

    async def _sarj_arama_durumu(self, sensor_data: Dict[str, Any]):
        """🔍 Şarj istasyonunu ara ve yönel"""
        self.logger.info("🔋 Şarj istasyonu aranıyor...")

        # Fırçaları durdur - enerji tasarrufu
        await self.motor_kontrolcu.fircalari_calistir(False)

        # Şarj istasyonuna yönelme rotası hesapla
        sarj_rota = await self.rota_planlayici.sarj_istasyonu_rotasi()

        if sarj_rota:
            await self.motor_kontrolcu.hareket_uygula(sarj_rota)

            # Şarj istasyonu görünür mü?
            kamera_data = await self.kamera_islemci.sarj_istasyonu_ara()
            if kamera_data.get("sarj_istasyonu_gorunur"):
                self.durum_degistir(RobotDurumu.SARJ_OLMA)

    async def _sarj_olma_durumu(self, sensor_data: Dict[str, Any]):
        """🔌 Şarj istasyonunda şarj ol"""
        self.logger.info("🔌 Şarj oluyor...")

        # Motorları durdur
        await self.motor_kontrolcu.durdur()

        batarya_seviye = sensor_data.get("batarya", {}).get("seviye", 0)
        hedef_seviye = self.config.get("missions", {}).get(
            "charging", {}).get("battery_full_threshold", 95)

        if batarya_seviye >= hedef_seviye:
            self.logger.info("🔋 Şarj tamamlandı!")
            self.durum_degistir(RobotDurumu.BEKLEME)

    async def _acil_durum_isle(self, sebep: str):
        """🚨 Acil durum işle"""
        self.logger.warning(f"🚨 ACİL DURUM: {sebep}")

        self.onceki_durum = self.durum
        self.durum = RobotDurumu.ACIL_DURUM

        # Hemen durdur
        await self.motor_kontrolcu.acil_durdur()

    async def _acil_durum_bekle(self):
        """🚨 Acil durumda bekle"""
        # Güvenlik sistemi temizlenene kadar bekle
        if not self.guvenlik_sistemi.acil_durum_aktif:
            self.logger.info("✅ Acil durum temizlendi")
            self.durum = self.onceki_durum or RobotDurumu.BEKLEME

    async def _hata_isle(self, hata_mesaji: str):
        """❌ Hata durumunu işle"""
        self.logger.error(f"❌ Hata: {hata_mesaji}")
        self.durum = RobotDurumu.HATA
        await self.motor_kontrolcu.durdur()

    async def _hata_durumu(self):
        """❌ Hata durumunda bekle"""
        await asyncio.sleep(5)  # 5 saniye bekle
        self.logger.info("🔄 Hata durumundan çıkılıyor...")
        self.durum = RobotDurumu.BEKLEME

    def durum_degistir(self, yeni_durum: RobotDurumu):
        """Durum değiştir ve logla"""
        self.onceki_durum = self.durum
        self.durum = yeni_durum
        self.logger.info(
            f"🔄 Durum değişti: {self.onceki_durum.value} → {yeni_durum.value}")

    def gorev_baslat(self):
        """Dışarıdan görev başlatma"""
        self.gorev_aktif = True
        self.logger.info("🎯 Görev başlatıldı!")

    def gorev_durdur(self):
        """Dışarıdan görev durdurma"""
        self.gorev_aktif = False
        self.durum_degistir(RobotDurumu.BEKLEME)
        self.logger.info("⏸️ Görev durduruldu!")

    def acil_durdur(self):
        """Dışarıdan acil durdurma"""
        self.acil_durum_aktif = True
        self.logger.warning("🚨 Acil durdurma aktif!")

    async def kapat(self):
        """Robot'u güvenli şekilde kapat"""
        self.logger.info("👋 Robot kapatılıyor...")
        self.calisma_durumu = False
        await self.motor_kontrolcu.durdur()
        self.logger.info("✅ Robot güvenli şekilde kapatıldı!")

    def get_durum_bilgisi(self) -> Dict[str, Any]:
        """Robot durumu hakkında bilgi al"""
        return {
            "durum": self.durum.value,
            "onceki_durum": self.onceki_durum.value if self.onceki_durum else None,
            "gorev_aktif": self.gorev_aktif,
            "acil_durum": self.acil_durum_aktif,
            "zaman": datetime.now().isoformat()
        }

    def _log_smart_config_info(self):
        """Akıllı config bilgilerini logla"""
        runtime_info = self.config.get("runtime", {})

        # Temel bilgileri logla
        self.logger.info("=" * 50)
        self.logger.info("🧠 AKILLI KONFİGÜRASYON BİLGİLERİ")
        self.logger.info("=" * 50)

        # Ortam bilgisi
        env_type = runtime_info.get("environment_type", "unknown")
        is_sim = runtime_info.get("is_simulation", False)
        is_hardware = runtime_info.get("is_hardware", False)

        self.logger.info(f"🌍 Ortam: {env_type}")
        self.logger.info(f"🎮 Simülasyon: {'✅ Aktif' if is_sim else '❌ Pasif'}")
        self.logger.info(f"⚙️ Donanım: {'✅ Aktif' if is_hardware else '❌ Pasif'}")

        # Donanım yetenekleri
        capabilities = runtime_info.get("capabilities", {})
        if capabilities:
            self.logger.info("🔧 Donanım Yetenekleri:")
            for cap_name, available in capabilities.items():
                status = "✅" if available else "❌"
                self.logger.info(f"   {status} {cap_name.upper()}")

        # Config dosya bilgileri
        motor_type = self.config.get("motors", {}).get("type", "unknown")
        mock_sensors = self.config.get("sensors", {}).get("mock_enabled", False)
        web_port = self.config.get("web_interface", {}).get("port", 0)

        self.logger.info(f"🚗 Motor Tipi: {motor_type}")
        self.logger.info(f"📡 Sahte Sensörler: {'✅ Aktif' if mock_sensors else '❌ Pasif'}")
        self.logger.info(f"🌐 Web Port: {web_port}")

        self.logger.info("=" * 50)
