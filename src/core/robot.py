"""
🤖 Bahçe Asistanı (OBA) - Ana Robot Sınıfı
Hacı Abi'nin emeği burada!

Bu sınıf tüm robot sistemlerini koordine eder.
Durum makinesi prensibi ile çalışır - güvenli ve öngörülebilir.
"""

import asyncio
import logging
import math
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Tuple

from ai.karar_verici import KararVerici
from core.environment_manager import EnvironmentManager
from core.guvenlik_sistemi import GuvenlikSistemi
from core.smart_config import load_smart_config
from hardware.sensor_okuyucu import SensorOkuyucu
from navigation.adaptif_navigasyon_kontrolcusu import AdaptifNavigasyonKontrolcusu
from navigation.bahce_sinir_kontrol import BahceSinirKontrol
from navigation.konum_takipci import KonumTakipci
from navigation.rota_planlayici import RotaPlanlayici
from navigation.sarj_istasyonu_yaklasici import SarjIstasyonuYaklasici
from vision.kamera_islemci import KameraIslemci


class RobotDurumu(Enum):
    """Robot'un mevcut durumu"""
    BASLATILIYOR = "baslatiliyor"
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
        self.durum = RobotDurumu.BASLATILIYOR
        self.onceki_durum = None

        # Logger'ı global setup'tan al - kendi logging setup yapmıyoruz!
        self.logger = logging.getLogger("BahceRobotu")

        # 🌍 Environment Manager'ı başlat - Ortam tespiti için
        self.environment_manager = EnvironmentManager()
        self.logger.info(f"🌍 Ortam tespit edildi: {self.environment_manager.environment_type.value}")
        self.logger.info(f"🎮 Simülasyon modu: {'Aktif' if self.environment_manager.is_simulation_mode else 'Pasif'}")

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

        # Async başlatma kontrolü
        self._async_baslat_gerekli = False

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
            # ⚙️ Motor Kontrolcü - HAL Factory Pattern ile
            motor_config = self.config.get("motors", {})
            from hardware.motor_factory import create_motor_kontrolcu
            self.motor_kontrolcu = create_motor_kontrolcu(self.environment_manager, motor_config)

            # 📡 Sensör Okuyucu - Environment Manager ile
            sensor_config = self.config.get("sensors", {})
            self.sensor_okuyucu = SensorOkuyucu(sensor_config, self.environment_manager)

            # Async başlatmaları event loop varsa zamanla ve yoksa not al
            try:
                loop = asyncio.get_running_loop()
                # Event loop varsa async başlatmaları task olarak ekle
                asyncio.create_task(self._sensörleri_başlat())
                asyncio.create_task(self._motorları_başlat())
                asyncio.create_task(self._kamerayi_baslat())
            except RuntimeError:
                # Event loop yok, async başlatmaları daha sonra yapılacak şekilde işaretle
                self.logger.info("📝 Event loop yok, async başlatmalar ana döngüde yapılacak")
                self._async_baslat_gerekli = True

        except Exception as e:
            self.logger.critical(f"CRITICAL: Donanım başlatma hatası: {e}", exc_info=True)
            self.logger.critical("Donanım başlatılamadığı için sistem durduruluyor. Lütfen konfigürasyonu ve bağlantıları kontrol edin.")
            self.durum = RobotDurumu.HATA
            self.calisma_durumu = False
            # Hata durumunda dummy objeler oluşturarak sistemin tamamen çökmesini engelleyebiliriz.
            # Bu, loglama ve web arayüzünün çalışmaya devam etmesini sağlar.
            self.motor_kontrolcu = None  # veya DummyMotorKontrolcu()
            self.sensor_okuyucu = None  # veya DummySensorOkuyucu()
            self._async_baslat_gerekli = False
            return  # Fonksiyondan erken çık

        # Vision
        try:
            # 📷 Kamera İşlemci
            camera_config = self.config.get("camera", {})
            self.kamera_islemci = KameraIslemci(camera_config)
        except Exception as e:
            self.logger.error(f"⚠️ Kamera başlatma hatası: {e}", exc_info=True)
            self.kamera_islemci = None  # Kamera olmadan da çalışabilir

        # Navigation
        try:
            # 🗺️ Konum Takipçi
            nav_config = self.config.get("navigation", {})
            self.konum_takipci = KonumTakipci(nav_config)

            # 📍 Rota Planlayıcı
            self.rota_planlayici = RotaPlanlayici(nav_config)

            # 🌳 Bahçe Sınır Kontrol
            self.bahce_sinir_kontrol = BahceSinirKontrol(nav_config)

            # 🧭 Adaptif Navigasyon Kontrolcüsü (Ana Navigasyon Sistemi)
            self.adaptif_navigasyon = AdaptifNavigasyonKontrolcusu(nav_config)
            self.logger.info("✅ Adaptif navigasyon sistemi entegre edildi")

        except Exception as e:
            self.logger.critical(f"CRITICAL: Navigasyon başlatma hatası: {e}", exc_info=True)
            self.durum = RobotDurumu.HATA
            self.calisma_durumu = False
            return

        # 🔋 Şarj Sistemi (GPS + AprilTag hibrit)
        try:
            charging_config = self.config.get("charging", {})
            navigation_config = self.config.get("navigation", {})

            # GPS + AprilTag hibrit şarj sistemi
            self.sarj_yaklasici = SarjIstasyonuYaklasici(
                sarj_config=charging_config,
                nav_config=navigation_config,
                konum_takipci=self.konum_takipci
            )
            self.logger.info("✅ GPS + AprilTag hibrit şarj sistemi entegre edildi")
        except Exception as e:
            self.logger.error(f"⚠️ Şarj sistemi başlatma hatası: {e}", exc_info=True)
            self.sarj_yaklasici = None  # Şarj olmadan da çalışabilir

        # AI
        try:
            # 🧠 Karar Verici
            ai_config = self.config.get("ai", {})
            self.karar_verici = KararVerici(ai_config)
        except Exception as e:
            self.logger.error(f"⚠️ AI başlatma hatası: {e}", exc_info=True)
            self.karar_verici = None

        # Core
        try:
            # 🛡️ Güvenlik Sistemi
            safety_config = self.config.get("safety", {})
            self.guvenlik_sistemi = GuvenlikSistemi(safety_config, self.sensor_okuyucu)
        except Exception as e:
            self.logger.error(f"⚠️ Güvenlik sistemi başlatma hatası: {e}", exc_info=True)
            self.guvenlik_sistemi = None  # Hata durumunda None olarak ayarla

        self.logger.info("✅ Tüm alt sistemler başarıyla başlatıldı!")

    def _log_smart_config_info(self):
        """Akıllı konfigürasyonun özetini loglar."""
        self.logger.info("--- Akıllı Konfigürasyon Özeti ---")
        runtime_info = self.config.get("runtime", {})
        env_type = runtime_info.get("environment_type", "Bilinmiyor")
        is_sim = runtime_info.get("is_simulation", False)
        is_hw = runtime_info.get("is_hardware", False)

        self.logger.info(f"Ortam Türü: {env_type}")
        self.logger.info(f"Simülasyon Modu: {'Aktif' if is_sim else 'Pasif'}")
        self.logger.info(f"Donanım Modu: {'Aktif' if is_hw else 'Pasif'}")

        capabilities = runtime_info.get("capabilities", {})
        active_caps = [cap for cap, available in capabilities.items() if available]
        if active_caps:
            self.logger.info(f"Aktif Yetenekler: {', '.join(active_caps)}")
        else:
            self.logger.info("Aktif Donanım Yeteneği Yok.")
        self.logger.info("------------------------------------")

    async def ana_dongu(self):
        """Ana robot döngüsü - Durum makinesi"""
        self.logger.info("🤖 Ana döngü başlatıldı. CTRL+C ile durdurabilirsiniz.")
        # Durum zaten BASLATILIYOR olarak ayarlandı

        while self.calisma_durumu:
            try:
                # 1. Sensör verilerini oku
                # Donanım hazır değilse veya hata durumundaysa sensör okumayı atla
                if not self.sensor_okuyucu or self.durum == RobotDurumu.HATA:
                    await asyncio.sleep(1)  # Hata durumunda CPU'yu yormamak için bekle
                    continue

                sensor_data = await self.sensor_okuyucu.tüm_sensör_verilerini_oku()

                # 🧭 Konum takipçiyi güncelle (KRITIK - eksikti!)
                if self.konum_takipci:
                    try:
                        await self.konum_takipci.konum_guncelle(sensor_data)
                    except Exception as e:
                        self.logger.warning(f"⚠️ Konum takipçi güncelleme hatası: {e}")

                # Güvenlik kontrolü
                if self.guvenlik_sistemi:
                    self.guvenlik_sistemi.acil_durum_kontrolu(sensor_data)
                    if self.guvenlik_sistemi.acil_durum_aktif_mi():
                        # Eğer zaten acil durumda değilsek, durumu değiştir.
                        if self.durum != RobotDurumu.ACIL_DURUM:
                            self.logger.warning("Güvenlik sistemi tarafından ACİL DURUM'a geçildi!")
                            self.durum = RobotDurumu.ACIL_DURUM

                # Durum değiştiyse logla
                if self.durum != self.onceki_durum:
                    self.logger.info(f"Durum Değişikliği: {self.onceki_durum} -> {self.durum}")
                    self.onceki_durum = self.durum

                # 3. Durum Makinesi (State Machine)
                if self.durum == RobotDurumu.BASLATILIYOR:
                    await self._baslatiliyor_durumu(sensor_data)
                elif self.durum == RobotDurumu.ACIL_DURUM:
                    await self._acil_durum_durumu()
                elif self.durum == RobotDurumu.BEKLEME:
                    await self._bekleme_durumu(sensor_data)
                elif self.durum == RobotDurumu.GOREV_YAPMA:
                    await self._gorev_yapma_durumu(sensor_data)
                elif self.durum == RobotDurumu.SARJ_ARAMA:
                    await self._sarj_arama_durumu(sensor_data)
                elif self.durum == RobotDurumu.SARJ_OLMA:
                    await self._sarj_olma_durumu(sensor_data)
                elif self.durum == RobotDurumu.HATA:
                    self.logger.error("Sistem HATA durumunda. Ana döngü durduruluyor.")
                    self.calisma_durumu = False

                # Döngü gecikmesi
                dongu_suresi = self.config.get("robot", {}).get("dongu_suresi_sn", 0.1)
                await asyncio.sleep(dongu_suresi)

            except asyncio.CancelledError:
                self.logger.info("Ana döngü iptal edildi (CancelledError).")
                self.calisma_durumu = False
            except Exception as e:
                self.logger.critical(f"Ana döngüde beklenmedik kritik hata: {e}", exc_info=True)
                self.durum = RobotDurumu.HATA
                self.calisma_durumu = False

        self.logger.info("Ana döngü sona erdi. Kapatma işlemleri başlıyor.")
        await self.kapat()

    async def baslat(self):
        """Robotun ana döngüsünü başlatır."""
        if self.durum == RobotDurumu.HATA:
            self.logger.error("HATA durumundaki robot başlatılamaz. Lütfen logları inceleyin.")
            return
        self.calisma_durumu = True
        await self.ana_dongu()

    async def durdur(self):
        """Robotun ana döngüsünü güvenli bir şekilde durdurur."""
        self.logger.info("Durdurma komutu alındı...")
        self.calisma_durumu = False
        # Ana döngünün bitmesini bekle
        # Bu kısım, ana_dongu'nun CancelledError yakalamasına bağlı
        # Alternatif olarak, bir event kullanılabilir.

    async def kapat(self):
        """Robotun tüm alt sistemlerini kapatır."""
        self.logger.info("Kapatma prosedürü başlatıldı...")
        if self.motor_kontrolcu:
            await self.motor_kontrolcu.acil_durdur()
            self.logger.info("Motorlar durduruldu.")
        if self.sensor_okuyucu:
            try:
                await self.sensor_okuyucu.durdur()
                self.logger.info("Sensörler durduruldu.")
            except AttributeError:
                self.logger.warning("⚠️ Sensör okuyucu durdur metodu bulunamadı")
            except Exception as e:
                self.logger.error(f"⚠️ Sensör durdurma hatası: {e}")
        if self.kamera_islemci:
            try:
                await self.kamera_islemci.durdur()
                self.logger.info("Kamera işlemci durduruldu.")
            except AttributeError:
                self.logger.warning("⚠️ Kamera işlemci durdur metodu bulunamadı")
            except Exception as e:
                self.logger.error(f"⚠️ Kamera durdurma hatası: {e}")

        # Diğer kapatma işlemleri buraya eklenebilir
        self.logger.info("🤖 OBA başarıyla kapatıldı. İyi günler, Hacı Abi!")

    def acil_durdur(self):
        """Acil durdurma - sync metod"""
        self.logger.warning("🚨 ACİL DURDURMA AKTİVLEŞTİRİLDİ!")
        self.durum = RobotDurumu.ACIL_DURUM
        self.acil_durum_aktif = True

    def sarj_istasyonuna_git(self):
        """Manuel şarj istasyonuna gitme komutu"""
        if self.sarj_yaklasici:
            self.logger.info("🔋 Manuel şarj komutu alındı")
            self.durum = RobotDurumu.SARJ_ARAMA
            # Şarj yaklaşıcıyı sıfırla (temiz başlangıç için)
            self.sarj_yaklasici.sifirla()
        else:
            self.logger.error("❌ Şarj sistemi mevcut değil!")

    def hedef_konum_ayarla(self, x: float, y: float):
        """Adaptif navigasyon için hedef konum ayarla"""
        if self.adaptif_navigasyon:
            from navigation.rota_planlayici import Nokta
            hedef = Nokta(x=x, y=y)
            self.adaptif_navigasyon.hedef_konum_ayarla(hedef)
            self.logger.info(f"🎯 Hedef konum ayarlandı: ({x:.2f}, {y:.2f})")
        else:
            self.logger.error("❌ Adaptif navigasyon sistemi mevcut değil!")

    def waypoint_ekle(self, x: float, y: float):
        """Adaptif navigasyon rotasına waypoint ekle"""
        if self.adaptif_navigasyon:
            from navigation.rota_planlayici import Nokta, RotaNoktasi
            nokta = Nokta(x=x, y=y)
            waypoint = RotaNoktasi(
                nokta=nokta,
                yon=0.0,  # Varsayılan yön
                hiz=0.3,  # Varsayılan hız
                aksesuar_aktif=True  # Fırçalar aktif
            )
            self.adaptif_navigasyon.waypoint_ekle(waypoint)
            self.logger.info(f"📍 Waypoint eklendi: ({x:.2f}, {y:.2f})")
        else:
            self.logger.error("❌ Adaptif navigasyon sistemi mevcut değil!")

    def navigation_modunu_ayarla(self, mod: str):
        """Navigasyon modunu değiştir: normal, aggressive, conservative, emergency"""
        if self.adaptif_navigasyon:
            self.adaptif_navigasyon.navigation_modu_degistir(mod)
            self.logger.info(f"🧭 Navigasyon modu değiştirildi: {mod}")
        else:
            self.logger.error("❌ Adaptif navigasyon sistemi mevcut değil!")

    def navigation_durumunu_al(self) -> Dict[str, Any]:
        """Adaptif navigasyon durumunu al"""
        if self.adaptif_navigasyon:
            return self.adaptif_navigasyon.durum_raporu()
        else:
            return {"hata": "Adaptif navigasyon sistemi mevcut değil"}

    def aksesuar_politikasi_ayarla(self, politika: str):
        """
        Aksesuar politikasını değiştir

        Args:
            politika (str): performans, tasarruf, sessiz, guvenlik
        """
        if self.adaptif_navigasyon and hasattr(self.adaptif_navigasyon, 'aksesuar_yoneticisi'):
            try:
                from navigation.akilli_aksesuar_yoneticisi import AksesuarPolitikasi

                # String'i enum'a çevir
                politika_map = {
                    "performans": AksesuarPolitikasi.PERFORMANS,
                    "tasarruf": AksesuarPolitikasi.TASARRUF,
                    "sessiz": AksesuarPolitikasi.SESSIZ,
                    "guvenlik": AksesuarPolitikasi.GUVENLIK
                }

                if politika in politika_map:
                    self.adaptif_navigasyon.aksesuar_politikasi_ayarla(politika_map[politika])
                    self.logger.info(f"🎛️ Aksesuar politikası değiştirildi: {politika}")
                else:
                    self.logger.error(f"❌ Geçersiz aksesuar politikası: {politika}")
                    self.logger.info("Geçerli politikalar: performans, tasarruf, sessiz, guvenlik")

            except Exception as e:
                self.logger.error(f"❌ Aksesuar politikası ayarlama hatası: {e}")
        else:
            self.logger.error("❌ Adaptif navigasyon veya aksesuar yöneticisi mevcut değil!")

    def aksesuar_durumunu_al(self) -> Dict[str, Any]:
        """Aksesuar yöneticisi durumunu al"""
        if self.adaptif_navigasyon and hasattr(self.adaptif_navigasyon, 'aksesuar_yoneticisi'):
            try:
                return self.adaptif_navigasyon.aksesuar_yoneticisi.durum_raporu()
            except Exception as e:
                self.logger.error(f"❌ Aksesuar durumu alma hatası: {e}")
                return {"hata": str(e)}
        else:
            return {"hata": "Aksesuar yöneticisi mevcut değil"}

    def manuel_aksesuar_kontrol(self, ana_firca: bool | None = None, yan_firca: bool | None = None, fan: bool | None = None):
        """
        Aksesuarları manuel olarak kontrol et

        Args:
            ana_firca (bool, optional): Ana fırça durumu
            yan_firca (bool, optional): Yan fırçalar durumu
            fan (bool, optional): Fan durumu
        """
        if self.motor_kontrolcu:
            try:
                # Manuel aksesuar komutları oluştur
                aksesuar_komutlari = {}
                if ana_firca is not None:
                    aksesuar_komutlari["ana_firca"] = ana_firca
                if yan_firca is not None:
                    aksesuar_komutlari["yan_firca"] = yan_firca
                if fan is not None:
                    aksesuar_komutlari["fan"] = fan

                if aksesuar_komutlari:
                    # Async metodları sync wrapper ile çağır
                    import asyncio
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # Zaten bir event loop çalışıyorsa task oluştur
                        asyncio.create_task(
                            self.motor_kontrolcu.aksesuarlari_kontrol_et(aksesuar_komutlari)
                        )
                    else:
                        # Event loop yoksa çalıştır
                        loop.run_until_complete(
                            self.motor_kontrolcu.aksesuarlari_kontrol_et(aksesuar_komutlari)
                        )

                    self.logger.info(f"🔧 Manuel aksesuar kontrolü: {aksesuar_komutlari}")
                else:
                    self.logger.warning("⚠️ Hiçbir aksesuar komutu belirtilmedi")

            except Exception as e:
                self.logger.error(f"❌ Manuel aksesuar kontrol hatası: {e}")
        else:
            self.logger.error("❌ Motor kontrolcü mevcut değil!")

    def gorev_baslat(self):
        """Görev başlatma komutu"""
        if self.durum != RobotDurumu.ACIL_DURUM:
            self.logger.info("🌱 Görev başlatıldı")
            self.durum = RobotDurumu.GOREV_YAPMA
            self.gorev_aktif = True
            self.adaptif_navigasyon.rota_ayarla(rota_tipi="mowing")  # Rotayı başlatma için ayarla
        else:
            self.logger.warning("⚠️ Acil durum aktif - görev başlatılamaz!")

    def gorev_durdur(self):
        """Görev durdurma komutu"""
        self.logger.info("⏹️ Görev durduruldu")
        self.durum = RobotDurumu.BEKLEME
        self.gorev_aktif = False

    def get_robot_durumu(self) -> Dict[str, Any]:
        """Robot durumu bilgisi döndür"""
        sarj_durumu = None
        if self.sarj_yaklasici:
            sarj_durumu = self.sarj_yaklasici.get_yaklasim_durumu()

        return {
            "durum": self.durum.value,
            "gorev_aktif": self.gorev_aktif,
            "acil_durum": self.acil_durum_aktif,
            "sarj_sistemi": {
                "mevcut": self.sarj_yaklasici is not None,
                "durum": sarj_durumu
            },
            "calisma_durumu": self.calisma_durumu
        }

    async def get_robot_data(self) -> Dict[str, Any]:
        """
        🤖 Robot'tan kapsamlı veri toplama

        Tüm alt sistemlerden veri toplayarak web arayüzü için
        detaylı robot durumu döndürür.
        """

        try:
            # Timestamp
            timestamp = datetime.now().isoformat()

            # Temel robot durumu
            robot_status = {
                "state": self.durum.value,
                "battery_level": 0,
                "position": {"x": 0.0, "y": 0.0, "heading": 0.0},
                "mission_progress": 0
            }

            # Sensör verileri - başlangıç değerleri
            sensors = {
                "gps": {
                    "latitude": 0.0,
                    "longitude": 0.0,
                    "satellites": 0,
                    "fix_quality": 0,
                    "accuracy": 0.0
                },
                "imu": {
                    "roll": 0.0,
                    "pitch": 0.0,
                    "yaw": 0.0,
                    "temperature": 20.0
                },
                "battery": {
                    "voltage": 0.0,
                    "current": 0.0,
                    "level": 0,
                    "power": 0.0
                },
                "obstacles": []
            }

            # Motor durumları
            motors = {
                "left_speed": 0.0,
                "right_speed": 0.0,
                "brushes_active": False,
                "fan_active": False
            }

            # Pozisyon bilgisi (robot_status ile aynı ama ayrı alan)
            position = {"x": 0.0, "y": 0.0, "heading": 0.0}

            # Görev istatistikleri
            mission_stats = {
                "total_distance": 0.0,
                "working_time": 0.0,
                "average_speed": 0.0,
                "max_speed": 0.0
            }

            # Şarj istasyonu mesafesi
            dock_distance = 0.0

            # 1. Sensör verilerini al
            try:
                if self.sensor_okuyucu:
                    # Sensör verilerini senkron şekilde al

                    sensor_data = {}

                    # Sensör okuyucudan async metodu güvenli şekilde çağır
                    try:
                        sensor_data = await self.sensor_okuyucu.tum_sensorleri_oku()
                    except Exception as async_error:
                        self.logger.debug(f"Async sensör okuma hatası, sync alternatif deneniyor: {async_error}")

                    # GPS verilerini işle
                    if 'gps' in sensor_data and sensor_data['gps']:
                        gps_data = sensor_data['gps']
                        sensors["gps"] = {
                            "latitude": gps_data.enlem,
                            "longitude": gps_data.boylam,
                            "satellites": gps_data.uydu_sayisi,
                            "fix_quality": gps_data.fix_kalitesi,
                            "accuracy": gps_data.hiz  # GPS'te accuracy yok, hız var
                        }

                    # IMU verilerini işle
                    if 'imu' in sensor_data and sensor_data['imu']:
                        imu_data = sensor_data['imu']
                        sensors["imu"] = {
                            "roll": imu_data.roll,
                            "pitch": imu_data.pitch,
                            "yaw": imu_data.yaw,
                            "temperature": imu_data.sicaklik
                        }

                        # Position heading'ini IMU'dan al
                        position["heading"] = imu_data.yaw
                        robot_status["position"]["heading"] = imu_data.yaw

                    # Batarya verilerini işle
                    if 'guc' in sensor_data and sensor_data['guc']:
                        battery_data = sensor_data['guc']
                        voltage = battery_data.get('voltaj', 0.0)
                        current = battery_data.get('akim', 0.0)
                        level = battery_data.get('batarya_seviyesi', 0)

                        sensors["battery"] = {
                            "voltage": voltage,
                            "current": current,
                            "level": level,
                            "power": battery_data.get('guc', voltage * abs(current))
                        }
                        robot_status["battery_level"] = level

                    # Engel tespiti
                    if 'obstacles' in sensor_data:
                        sensors["obstacles"] = sensor_data['obstacles'] or []

            except Exception as e:
                self.logger.warning(f"⚠️ Sensör veri alma hatası: {e}")

            # 2. Konum takipçiden pozisyon al
            try:
                if self.konum_takipci:
                    konum = self.konum_takipci.get_mevcut_konum()
                    if konum:
                        if hasattr(konum, 'x') and hasattr(konum, 'y'):
                            position["x"] = konum.x
                            position["y"] = konum.y
                            robot_status["position"]["x"] = konum.x
                            robot_status["position"]["y"] = konum.y
                        elif hasattr(konum, 'latitude') and hasattr(konum, 'longitude'):
                            # GPS koordinatlarını meter sistemine çevir
                            position["x"] = konum.longitude * 111320  # Yaklaşık dönüşüm
                            position["y"] = konum.latitude * 110540
                            robot_status["position"]["x"] = position["x"]
                            robot_status["position"]["y"] = position["y"]
            except Exception as e:
                self.logger.warning(f"⚠️ Konum takipçi veri alma hatası: {e}")

            # 3. Motor kontrolcüden durumları ve aksesuar bilgilerini al
            try:
                if self.motor_kontrolcu:
                    motor_durumları = self.motor_kontrolcu.motor_durumu_al()
                    motors["left_speed"] = motor_durumları.sol_hiz
                    motors["right_speed"] = motor_durumları.sag_hiz
                    motors["brushes_active"] = motor_durumları.ana_firca
                    motors["fan_active"] = motor_durumları.fan

                    # Detaylı aksesuar durumları
                    motors["main_brush"] = motor_durumları.ana_firca
                    motors["side_brushes"] = motor_durumları.sol_firca or motor_durumları.sag_firca
                    motors["left_brush"] = motor_durumları.sol_firca
                    motors["right_brush"] = motor_durumları.sag_firca
            except Exception as e:
                self.logger.warning(f"⚠️ Motor kontrolcü veri alma hatası: {e}")

            # 4. Görev ilerlemesi
            if self.gorev_aktif and self.durum == RobotDurumu.GOREV_YAPMA:
                # Basit ilerleme hesabı - geliştirilmesi gerekebilir
                robot_status["mission_progress"] = min(50 + (sensors["battery"]["level"] // 2), 100)

            # 5. Şarj istasyonu bilgileri
            charging_station = {
                "gps_coordinates": {"latitude": 0.0, "longitude": 0.0},
                "accuracy_radius": 3.0,
                "precise_approach_distance": 0.5,
                "apriltag_detection_range": 0.5,
                "approach_speeds": {"gps_approach": 0.3, "precise_approach": 0.1},
                "configured": False,
                "hybrid_system": False,
                "distance": 0.0,
                "bearing": 0.0,
                "accuracy": "UNKNOWN"
            }

            try:
                if self.sarj_yaklasici:
                    sarj_durumu = self.sarj_yaklasici.get_yaklasim_durumu()
                    charging_station.update(sarj_durumu)

            except Exception as e:
                self.logger.warning(f"⚠️ Şarj istasyonu veri alma hatası: {e}")

            # 6. Bahçe sınır durumu
            boundary_status = {
                "active": False,
                "distance_to_fence": 0.0,
                "fence_violations": 0,
                "violation_rate": 0.0,
                "garden_area": 0.0,
                "status": "UNKNOWN",
                "buffer_distance": 3.0,
                "warning_distance": 5.0
            }

            try:
                if self.bahce_sinir_kontrol:
                    boundary_status["active"] = True

                    # Mevcut konumu kullanarak sınır durumu al
                    if sensors["gps"]["latitude"] != 0.0:
                        sinir_durumu = self.bahce_sinir_kontrol.get_current_boundary_status_for_web(
                            sensors["gps"]["latitude"],
                            sensors["gps"]["longitude"]
                        )
                        boundary_status.update(sinir_durumu)
            except Exception as e:
                self.logger.warning(f"⚠️ Bahçe sınır veri alma hatası: {e}")

            # 7. Aksesuar yöneticisi durumu
            smart_accessories = {
                "available": False,
                "current_policy": "unknown",
                "energy_saving_active": False,
                "decision_count": 0,
                "last_decision_time": 0.0,
                "factors_analysis": {
                    "mission_type": "unknown",
                    "speed": 0.0,
                    "battery_level": 0,
                    "obstacle_distance": 0.0,
                    "boundary_distance": 0.0,
                    "rough_terrain": False
                }
            }

            try:
                if self.adaptif_navigasyon and hasattr(self.adaptif_navigasyon, 'aksesuar_yoneticisi'):
                    aksesuar_durumu = self.adaptif_navigasyon.aksesuar_yoneticisi.durum_raporu()
                    smart_accessories["available"] = True
                    smart_accessories["current_policy"] = aksesuar_durumu.get("mevcut_politika", "unknown")
                    smart_accessories["energy_saving_active"] = aksesuar_durumu.get("enerji_tasarruf_aktif", False)
                    smart_accessories["decision_count"] = aksesuar_durumu.get("toplam_karar_sayisi", 0)
                    smart_accessories["last_decision_time"] = aksesuar_durumu.get("son_karar_zamani", 0.0)

                    # Faktör analizi bilgilerini ekle
                    smart_accessories["factors_analysis"].update({
                        "mission_type": self.adaptif_navigasyon.mevcut_gorev_tipi.value if hasattr(self.adaptif_navigasyon, 'mevcut_gorev_tipi') else "unknown",
                        "speed": motors.get("left_speed", 0.0),  # Robot hızı
                        "battery_level": sensors["battery"]["level"],
                        "obstacle_distance": min([obs.get("distance", 999) for obs in sensors["obstacles"]] + [999]),
                        "boundary_distance": boundary_status.get("distance_to_fence", 0.0),
                        "rough_terrain": abs(sensors["imu"]["roll"]) > 15 or abs(sensors["imu"]["pitch"]) > 15
                    })

            except Exception as e:
                self.logger.warning(f"⚠️ Aksesuar yöneticisi veri alma hatası: {e}")

            # Sonuç JSON'ını oluştur
            robot_data = {
                "timestamp": timestamp,
                "robot_status": robot_status,
                "sensors": sensors,
                "motors": motors,
                "position": position,
                "mission_stats": mission_stats,
                "dock_distance": dock_distance,
                "charging_station": charging_station,
                "boundary_status": boundary_status,
                "smart_accessories": smart_accessories
            }

            return robot_data

        except Exception as e:
            self.logger.error(f"❌ Robot veri toplama hatası: {e}")
            # Hata durumunda minimal veri döndür
            return {
                "timestamp": datetime.now().isoformat(),
                "robot_status": {
                    "state": "hata",
                    "battery_level": 0,
                    "position": {"x": 0.0, "y": 0.0, "heading": 0.0},
                    "mission_progress": 0
                },
                "sensors": {
                    "gps": {"latitude": 0.0, "longitude": 0.0, "satellites": 0, "fix_quality": 0, "accuracy": 0.0},
                    "imu": {"roll": 0.0, "pitch": 0.0, "yaw": 0.0, "temperature": 20.0},
                    "battery": {"voltage": 0.0, "current": 0.0, "level": 0, "power": 0.0},
                    "obstacles": []
                },
                "motors": {"left_speed": 0.0, "right_speed": 0.0, "brushes_active": False, "fan_active": False},
                "position": {"x": 0.0, "y": 0.0, "heading": 0.0},
                "mission_stats": {"total_distance": 0.0, "working_time": 0.0, "average_speed": 0.0, "max_speed": 0.0},
                "dock_distance": 0.0,
                "charging_station": {"configured": False, "hybrid_system": False, "distance": 0.0},
                "boundary_status": {"active": False, "status": "ERROR"},
                "error": str(e)
            }

    # --- DURUM YÖNETİCİ METODLARI ---

    async def _acil_durum_durumu(self):
        """Acil durum state'i. Motorları durdur ve bekle."""
        self.logger.warning("🚨 ACİL DURUM AKTİF 🚨 - Tüm hareketler durduruldu.")
        if self.motor_kontrolcu:
            await self.motor_kontrolcu.acil_durdur()
        # Bu durumda, robot bir reset komutu beklemelidir.
        # Şimdilik, sadece döngüde bekleyecek.
        # TODO: Web arayüzünden veya başka bir yolla reset mekanizması ekle.
        return {"message": "Reset özelliği henüz uygulanmadı"}

    async def _bekleme_durumu(self, sensor_data: Dict[str, Any]):
        """Bekleme state'i. Yeni komut veya görev bekler."""
        self.logger.debug("Durum: Bekleme. Komut bekleniyor...")

    async def _gorev_yapma_durumu(self, sensor_data: Dict[str, Any]):
        """Görev yapma state'i. Adaptif navigasyon ile hareket eder."""
        self.logger.debug("Durum: Görev yapma.")

        # Sistemlerin hazır olup olmadığını kontrol et
        if not self.motor_kontrolcu:
            self.logger.warning("⚠️ Motor kontrolcü mevcut değil!")
            self.durum = RobotDurumu.BEKLEME
            return

        # Adaptif navigasyon mevcut mu kontrol et
        if not self.adaptif_navigasyon:
            self.logger.warning("⚠️ Adaptif navigasyon sistemi mevcut değil! AI karar verici ile devam...")
            # Fallback: AI karar verici ile çalış
            await self._gorev_yapma_ai_fallback(sensor_data)
            return

        try:
            # 1. Robot konumunu al
            robot_konumu = None
            robot_hizi = (0.0, 0.0)

            # Konum takipçiden konum al
            if self.konum_takipci:
                konum = self.konum_takipci.get_mevcut_konum()
                if konum:
                    # Konum nesnesini Nokta nesnesine dönüştür (Adaptif navigasyon için)
                    from navigation.rota_planlayici import Nokta
                    if hasattr(konum, 'x') and hasattr(konum, 'y'):
                        # Konum nesnesinin x,y değerlerini kullan
                        robot_konumu = Nokta(x=konum.x, y=konum.y)
                    elif hasattr(konum, 'latitude') and hasattr(konum, 'longitude'):
                        # GPS koordinatlarını meter sistemine çevir (basit dönüşüm)
                        robot_konumu = Nokta(
                            x=konum.longitude * 111320,  # Yaklaşık dönüşüm
                            y=konum.latitude * 110540
                        )

            # Motor kontrolcüden hız bilgisi al
            if self.motor_kontrolcu:
                try:
                    motor_durumları = self.motor_kontrolcu.motor_durumu_al()

                    robot_hizi = motor_durumları.dogrusal_hiz, motor_durumları.acisal_hiz
                except Exception as e:
                    self.logger.debug(f"Motor hız bilgisi alma hatası: {e}")

            # 2. Kamera görüntüsü al
            kamera_frame = None
            if self.kamera_islemci:
                try:
                    kamera_frame = await self.kamera_islemci.goruntu_al()
                except Exception as e:
                    self.logger.debug(f"Kamera görüntü alma hatası: {e}")

            # 3. Adaptif navigasyon çağır (batarya ve çevresel faktörlerle)
            if robot_konumu is not None:
                # Batarya seviyesi al
                guc_data = sensor_data.get("guc")
                batarya_seviyesi = guc_data.batarya_seviyesi if guc_data and guc_data.gecerli else 100

                # Çevresel faktörleri hesapla
                bahce_sinir_mesafesi = 10.0  # Default değer
                zorlu_arazide = False

                # Bahçe sınır kontrolü varsa gerçek mesafeyi al
                if self.bahce_sinir_kontrol and sensor_data.get("gps"):
                    try:
                        gps_data = sensor_data["gps"]
                        if gps_data.enlem and gps_data.boylam:
                            sinir_durumu = self.bahce_sinir_kontrol.get_current_boundary_status_for_web(
                                gps_data.enlem, gps_data.boylam
                            )
                            bahce_sinir_mesafesi = sinir_durumu.get("distance_to_fence", 10.0)
                    except Exception as e:
                        self.logger.debug(f"Bahçe sınır mesafe alma hatası: {e}")

                # IMU'dan zorlu arazi tespiti
                if sensor_data.get("imu"):
                    try:
                        imu_data = sensor_data["imu"]
                        roll = abs(imu_data.roll)
                        pitch = abs(imu_data.pitch)
                        # Eğim 15 dereceden fazlaysa zorlu arazi kabul et
                        zorlu_arazide = roll > 15.0 or pitch > 15.0
                    except Exception as e:
                        self.logger.debug(f"IMU zorlu arazi tespiti hatası: {e}")

                # AdaptifNavigasyon'ı tüm faktörlerle çağır
                hareket_komutlari = await self.adaptif_navigasyon.navigation_dongusu(
                    robot_konumu=robot_konumu,
                    robot_hizi=robot_hizi,
                    kamera_frame=kamera_frame,
                    batarya_seviyesi=batarya_seviyesi,
                    bahce_sinir_mesafesi=bahce_sinir_mesafesi,
                    zorlu_arazide=zorlu_arazide,
                    manuel_kontrol_aktif=False  # Manuel kontrol şimdilik false
                )

                # 4. Hareket ve aksesuar komutlarını motor kontrolcüye gönder
                if hareket_komutlari:
                    # Hareket komutlarını uygula
                    await self.motor_kontrolcu.hareket_et(
                        hareket_komutlari.dogrusal_hiz,
                        hareket_komutlari.acisal_hiz
                    )

                    # 🧠 Akıllı aksesuar komutlarını uygula
                    if hasattr(hareket_komutlari, 'aksesuar_komutlari') and hareket_komutlari.aksesuar_komutlari:
                        await self.motor_kontrolcu.aksesuarlari_kontrol_et(
                            hareket_komutlari.aksesuar_komutlari
                        )
                        self.logger.debug(f"🔧 Aksesuar komutları uygulandı: {hareket_komutlari.aksesuar_komutlari}")

                    # Güvenlik skoru kontrolü
                    if hareket_komutlari.guvenlik_skoru < 0.3:  # Düşük güvenlik skoru
                        self.logger.warning("⚠️ Düşük güvenlik skoru, dikkatli hareket!")

                    self.logger.debug(f"🧭 Adaptif navigasyon: doğrusal={hareket_komutlari.dogrusal_hiz:.3f}, açısal={hareket_komutlari.acisal_hiz:.3f}, güvenlik={hareket_komutlari.guvenlik_skoru:.2f}")
                else:
                    # Komut yok, güvenli dur ve tüm aksesuarları kapat
                    await self.motor_kontrolcu.hareket_et(0.0, 0.0)
                    await self.motor_kontrolcu.aksesuarlari_kontrol_et({
                        "ana_firca": False, "yan_firca": False, "fan": False
                    })
                    self.logger.debug("🚙 Adaptif navigasyon: durma komutu, aksesuarlar kapatıldı")
            else:
                # Konum bilinmiyor, güvenli dur
                await self.motor_kontrolcu.hareket_et(0.0, 0.0)
                self.logger.warning("⚠️ Robot konumu bilinmiyor, duruyorum")

        except Exception as e:
            self.logger.error(f"❌ Adaptif navigasyon hatası: {e}")
            # Hata durumunda güvenli dur
            if self.motor_kontrolcu:
                await self.motor_kontrolcu.hareket_et(0.0, 0.0)
            # Fallback: AI karar verici ile devam et
            await self._gorev_yapma_ai_fallback(sensor_data)

    async def _gorev_yapma_ai_fallback(self, sensor_data: Dict[str, Any]):
        """AI karar verici ile görev yapma (adaptif navigasyon yoksa fallback)"""
        # Karar verici mevcut mu kontrol et
        if not self.karar_verici:
            self.logger.warning("⚠️ AI karar verici de mevcut değil!")
            self.durum = RobotDurumu.BEKLEME
            return

        try:
            # Kamera verilerini al
            kamera_data = {}
            if self.kamera_islemci:
                try:
                    kamera_data = await self.kamera_islemci.engel_analiz_et() or {}
                except Exception as e:
                    self.logger.debug(f"Kamera veri alma hatası: {e}")
                    kamera_data = {}

            # AI'dan karar al
            karar = await self.karar_verici.next_action_belirle(sensor_data, kamera_data)

            if karar:
                # Motor komutunu uygula
                linear_hiz = karar.hareket.get("linear", 0.0)
                angular_hiz = karar.hareket.get("angular", 0.0)

                await self.motor_kontrolcu.hareket_et(linear_hiz, angular_hiz)

                # Aksesuar komutlarını uygula
                await self.motor_kontrolcu.aksesuarlari_kontrol_et(karar.aksesuar_komutlari)

                # Kritik durumda durum değiştir
                if karar.oncelik.value <= 2:  # KRITIK veya YUKSEK öncelik
                    if "şarj" in karar.sebep.lower():
                        self.durum = RobotDurumu.SARJ_ARAMA
                        self.logger.info(f"🔋 Şarj gerekli: {karar.sebep}")
                    elif "acil" in karar.sebep.lower() or "kritik" in karar.sebep.lower():
                        self.durum = RobotDurumu.ACIL_DURUM
                        self.logger.warning(f"🚨 Acil durum: {karar.sebep}")

                # Log karar
                self.logger.debug(f"🧠 AI Fallback Kararı: {karar.sebep} (güven: {karar.guven_skoru:.2f})")

            else:
                # Karar alınamazsa güvenli dur
                await self.motor_kontrolcu.hareket_et(0.0, 0.0)
                self.logger.warning("⚠️ AI'dan karar alınamadı, duruyorum")

        except Exception as e:
            self.logger.error(f"❌ Görev yapma sırasında hata: {e}")
            # Hata durumunda güvenli dur
            if self.motor_kontrolcu:
                await self.motor_kontrolcu.hareket_et(0.0, 0.0)
            self.durum = RobotDurumu.BEKLEME

    async def _sarj_arama_durumu(self, sensor_data: Dict[str, Any]):
        """Şarj arama state'i. Şarj istasyonunu bulmaya çalışır."""
        self.logger.info("Durum: Şarj istasyonu aranıyor...")

        # Şarj yaklaşıcı mevcut mu kontrol et
        if not self.sarj_yaklasici:
            self.logger.error("❌ Şarj yaklaşıcı mevcut değil!")
            self.durum = RobotDurumu.HATA
            return

        # Kamera mevcut mu kontrol et
        if not self.kamera_islemci:
            self.logger.error("❌ Kamera mevcut değil - şarj sistemi kamera gerektirir!")
            self.durum = RobotDurumu.HATA
            return

        try:
            # Kamera görüntüsü al
            kamera_data = await self.kamera_islemci.goruntu_al()

            if kamera_data is not None:
                # Şarj yaklaşım komutunu al
                komut = await self.sarj_yaklasici.sarj_istasyonuna_yaklas(kamera_data)

                if komut is not None:
                    # Hareket komutunu motor kontrolcüye gönder
                    if self.motor_kontrolcu:
                        await self.motor_kontrolcu.hareket_et(komut.linear_hiz, komut.angular_hiz)
                    else:
                        self.logger.warning("⚠️ Motor kontrolcü mevcut değil!")

                    # Debug loglama
                    if komut.hassas_mod:
                        self.logger.debug(f"🎯 Hassas şarj hareketi: linear={komut.linear_hiz:.3f}, angular={komut.angular_hiz:.3f}")
                    else:
                        self.logger.debug(f"🔍 Şarj arama hareketi: linear={komut.linear_hiz:.3f}, angular={komut.angular_hiz:.3f}")
                else:
                    # Yaklaşım tamamlandı - şarj olma durumuna geç
                    yaklasim_durumu = self.sarj_yaklasici.get_yaklasim_durumu()
                    if yaklasim_durumu["durum"] == "tamamlandi":
                        self.logger.info("🔋 Şarj istasyonuna başarıyla yaklaşıldı!")
                        self.durum = RobotDurumu.SARJ_OLMA
                    else:
                        self.logger.warning(f"⚠️ Şarj yaklaşım durumu: {yaklasim_durumu['durum']}")
            else:
                self.logger.warning("⚠️ Kamera verisi alınamadı")

        except Exception as e:
            self.logger.error(f"❌ Şarj arama sırasında hata: {e}")
            # Hatadan kurtarma - yaklaşıcıyı sıfırla
            self.sarj_yaklasici.sifirla()

    async def _sarj_olma_durumu(self, sensor_data: Dict[str, Any]):
        """Şarj olma state'i. Batarya dolana kadar bekler."""
        self.logger.info("Durum: Şarj oluyor...")

        # Batarya seviyesini kontrol et
        guc_data = sensor_data.get("guc")
        batarya_seviyesi = guc_data.batarya_seviyesi if guc_data and guc_data.gecerli else 0

        if batarya_seviyesi >= 95:  # %95 dolunca şarj tamamlandı say
            self.logger.info("🔋 Batarya tamamen doldu. Göreve dönülüyor...")
            self.durum = RobotDurumu.BEKLEME

            # Şarj yaklaşıcıyı sıfırla (bir sonraki şarj için)
            if self.sarj_yaklasici:
                self.sarj_yaklasici.sifirla()
        else:
            # Şarj devam ediyor
            if batarya_seviyesi > 0:
                self.logger.debug(f"🔋 Şarj oluyor... Batarya: %{batarya_seviyesi}")

            # Şarj sırasında motor durdur
            if self.motor_kontrolcu:
                await self.motor_kontrolcu.hareket_et(0.0, 0.0)

    async def _sensörleri_başlat(self):
        """Sensörleri asenkron olarak başlat"""
        try:
            if self.sensor_okuyucu:
                başarılı = await self.sensor_okuyucu.başlat()
                if başarılı:
                    self.logger.info("✅ Sensörler başarıyla başlatıldı")
                else:
                    self.logger.warning("⚠️ Bazı sensörler başlatılamadı, sistem devam ediyor")
            else:
                self.logger.warning("⚠️ Sensör okuyucu mevcut değil")
        except Exception as e:
            self.logger.error(f"❌ Sensör başlatma hatası: {e}", exc_info=True)

    async def _motorları_başlat(self):
        """Motorları asenkron olarak başlat"""
        try:
            if self.motor_kontrolcu:
                başarılı = await self.motor_kontrolcu.baslat()
                if başarılı:
                    self.logger.info("✅ Motor sistemi başarıyla başlatıldı")
                else:
                    self.logger.error("❌ Motor sistemi başlatılamadı")
            else:
                self.logger.warning("⚠️ Motor kontrolcü mevcut değil")
        except Exception as e:
            self.logger.error(f"❌ Motor başlatma hatası: {e}", exc_info=True)

    async def _kamerayi_baslat(self):
        """Kamerayı asenkron olarak başlat"""
        try:
            if self.kamera_islemci:
                başarılı = await self.kamera_islemci.baslat()
                if başarılı:
                    self.logger.info("✅ Kamera sistemi başarıyla başlatıldı")
                else:
                    self.logger.warning("⚠️ Kamera sistemi başlatılamadı")
            else:
                self.logger.warning("⚠️ Kamera işlemci mevcut değil")
        except Exception as e:
            self.logger.error(f"❌ Kamera başlatma hatası: {e}", exc_info=True)

    async def _baslatiliyor_durumu(self, sensor_data: Dict[str, Any]):
        """
        🚀 Başlatılıyor state'i - Sistem başlangıç görevleri

        Bu durumda robot:
        - Sistem sağlık kontrolü yapar
        - GPS referans noktası ayarlar (simülasyon/gerçek hardware otomatik)
        - Tüm alt sistemlerin hazır olup olmadığını kontrol eder
        - Hazırsa BEKLEME durumuna geçer
        """
        self.logger.info("🚀 Robot başlatılıyor - Sistem kontrolleri yapılıyor...")

        # 1. Sistem sağlık kontrolü
        sistem_saglikli = True

        try:
            # Kritik sistemlerin varlığını kontrol et
            if not self.motor_kontrolcu:
                self.logger.error("❌ Motor kontrolcü mevcut değil!")
                sistem_saglikli = False

            if not self.sensor_okuyucu:
                self.logger.error("❌ Sensör okuyucu mevcut değil!")
                sistem_saglikli = False

            if not self.konum_takipci:
                self.logger.error("❌ Konum takipçi mevcut değil!")
                sistem_saglikli = False

            # Kritik olmayan sistemlerin varlığını kontrol et
            if not self.kamera_islemci:
                self.logger.warning("⚠️ Kamera işlemci mevcut değil - kamerasız çalışılacak")

            if not self.adaptif_navigasyon:
                self.logger.warning("⚠️ Adaptif navigasyon mevcut değil - AI fallback kullanılacak")

            if not self.sarj_yaklasici:
                self.logger.warning("⚠️ Şarj yaklaşıcı mevcut değil - şarj özelliği kullanılamayacak")

            # Eğer kritik sistem yoksa HATA durumuna geç
            if not sistem_saglikli:
                self.logger.critical("💀 Kritik sistemler eksik - HATA durumuna geçiliyor!")
                self.durum = RobotDurumu.HATA
                return

            # 2. GPS referans noktası ayarlama
            if self.konum_takipci:
                # GPS referansı daha önce ayarlandı mı kontrol et
                if not hasattr(self.konum_takipci, 'gps_reference') or not self.konum_takipci.gps_reference:

                    # 🌍 Gerçek hardware'de GPS verisini bekle
                    if 'gps' in sensor_data and sensor_data['gps']:
                        gps_data = sensor_data['gps']
                        # GPSVeri dataclass'ından veri al
                        lat = gps_data.enlem
                        lon = gps_data.boylam
                        fix_quality = gps_data.fix_kalitesi

                        # GPS fix'i var ve geçerli koordinatlar varsa referans olarak ayarla
                        if fix_quality > 0 and lat != 0.0 and lon != 0.0:
                            self.konum_takipci.gps_referans_ayarla(lat, lon)
                            self.logger.info(f"🌍 GPS referans noktası ayarlandı: ({lat:.6f}, {lon:.6f})")
                        else:
                            self.logger.info(f"🔍 GPS fix'i bekleniyor... (fix_kalitesi={fix_quality})")
                            return  # GPS fix'i yoksa bekle
                    else:
                        self.logger.info("📡 GPS verisi bekleniyor...")
                        return  # GPS verisi yoksa bekle

            # 3. Kamera sistem sağlık kontrolü
            if self.kamera_islemci:
                kamera_durumu = self.kamera_islemci.get_kamera_durumu()
                if not kamera_durumu.get("aktif", False):
                    self.logger.warning("⚠️ Kamera sistemi henüz hazır değil - başlatılması bekleniyor...")
                    return  # Kamera hazır değilse bekle
                else:
                    self.logger.info("✅ Kamera sistemi hazır ve aktif")
            else:
                self.logger.warning("⚠️ Kamera işlemci mevcut değil - kamerasız devam ediliyor")

            # 4. Güvenlik sistemi kontrolü
            if self.guvenlik_sistemi:
                # Başlangıçta acil durum olmamalı
                if self.guvenlik_sistemi.acil_durum_aktif_mi():
                    self.logger.warning("⚠️ Güvenlik sistemi acil durum rapor ediyor - düzeltmek için bekliyor...")
                    return  # Acil durum varsa bekle

            # 5. Batarya seviye kontrolü
            guc_data = sensor_data.get("guc")
            batarya_seviyesi = guc_data.batarya_seviyesi if guc_data and guc_data.gecerli else 100
            if batarya_seviyesi < 15:  # %15'in altında çok kritik
                self.logger.error(f"🔋 Batarya çok düşük (%{batarya_seviyesi}) - Başlatma iptal ediliyor!")
                self.durum = RobotDurumu.HATA
                return
            elif batarya_seviyesi < 25:  # %25'in altında uyarı ver ama başlat
                self.logger.warning(f"🔶 Batarya düşük (%{batarya_seviyesi}) - Başlatıldıktan sonra şarj gerekebilir")

            # 6. Tüm kontroller başarılı - BEKLEME durumuna geç
            self.logger.info("✅ Tüm sistem kontrolleri başarılı!")
            self.logger.info("🎯 GPS referans noktası ayarlandı")
            self.logger.info(f"🔋 Batarya seviyesi: %{batarya_seviyesi}")
            self.logger.info("🤖 Robot BEKLEME durumuna geçiyor - Komut beklemeye başlıyor")

            self.durum = RobotDurumu.BEKLEME

        except Exception as e:
            self.logger.error(f"❌ Başlatma durumu hatası: {e}", exc_info=True)
            self.durum = RobotDurumu.HATA


def _setup_logging(config: Dict[str, Any]):
    """Logging konfigürasyonu"""
    log_level = config.get("logging", {}).get("level", "INFO").upper()
    numeric_level = getattr(logging, log_level, logging.INFO)
    logging.basicConfig(level=numeric_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
