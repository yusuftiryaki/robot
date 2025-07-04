"""
🤖 Bahçe Asistanı (OBA) - Ana Robot Sınıfı
Hacı Abi'nin emeği burada!

Bu sınıf tüm robot sistemlerini koordine eder.
Durum makinesi prensibi ile çalışır - güvenli ve öngörülebilir.
"""

import asyncio
import logging
import time
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

import yaml

from ai.karar_verici import KararVerici
from core.guvenlik_sistemi import GuvenlikSistemi
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
        self.config = self._load_config(config_path)
        self.durum = RobotDurumu.BASLANGIC
        self.onceki_durum = None

        # Logging kurulumu
        self._setup_logging()
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
        """Konfigürasyon dosyasını yükle"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"⚠️  Konfigürasyon dosyası bulunamadı: {config_path}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Varsayılan konfigürasyon"""
        return {
            "robot": {"name": "Haci_Abi_Robot", "debug_mode": True},
            "logging": {"level": "INFO", "file": "logs/robot.log"}
        }

    def _setup_logging(self):
        """Logging sistemini kur"""
        log_config = self.config.get("logging", {})
        level = getattr(logging, log_config.get("level", "INFO"))

        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_config.get("file", "logs/robot.log")),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("BahceRobotu")

    def _init_subsystems(self):
        """Alt sistemleri başlat"""
        try:
            self.logger.info("🔧 Alt sistemler başlatılıyor...")

            # Hardware
            self.motor_kontrolcu = MotorKontrolcu(
                self.config.get("hardware", {}).get("motors", {}))
            self.sensor_okuyucu = SensorOkuyucu(
                self.config.get("hardware", {}).get("sensors", {}))

            # Navigation
            self.konum_takipci = KonumTakipci(
                self.config.get("navigation", {}))
            self.rota_planlayici = RotaPlanlayici(
                self.config.get("navigation", {}))

            # Vision & AI
            self.kamera_islemci = KameraIslemci(self.config.get(
                "hardware", {}).get("sensors", {}).get("camera", {}))
            self.karar_verici = KararVerici(self.config.get("ai", {}))

            # Security
            self.guvenlik_sistemi = GuvenlikSistemi(
                self.config.get("safety", {}))

            self.logger.info("✅ Tüm alt sistemler hazır!")

        except Exception as e:
            self.logger.error(f"❌ Alt sistem başlatma hatası: {e}")
            self.durum = RobotDurumu.HATA

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
                guvenlik_durumu = self.guvenlik_sistemi.kontrol_et(sensor_data)

                if guvenlik_durumu.acil_durum:
                    await self._acil_durum_isle(guvenlik_durumu.sebep)
                    continue

                # Konum güncelle
                await self.konum_takipci.konum_guncelle(sensor_data)

                # Durum makinesine göre işlem yap
                await self._durum_makinesini_isle(sensor_data)

                # Kısa bekleme
                await asyncio.sleep(0.1)  # 10 Hz ana döngü

            except Exception as e:
                self.logger.error(f"❌ Ana döngü hatası: {e}")
                await self._hata_isle(str(e))
                await asyncio.sleep(1)

    async def _sensor_verilerini_oku(self) -> Dict[str, Any]:
        """Tüm sensörlerden veri oku"""
        return await self.sensor_okuyucu.tum_verileri_oku()

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

        # Sistem kontrolü
        await self.motor_kontrolcu.test_et()
        await self.sensor_okuyucu.kalibrasyon_yap()

        # İlk konum belirle
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

        # Motor hareketini uygula
        await self.motor_kontrolcu.hareket_uygula(karar["hareket"])

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
