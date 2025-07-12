"""
🚀 Adaptif Navigasyon Kontrolcüsü - Ana Entegrasyon
Hacı Abi'nin master navigation sistemi!

Bu modül statik planlama + dinamik engel kaçınma + sensör füzyonunu
birleştirerek tam otonomluk sağlar.
"""

import asyncio
import logging
import math
import time
from typing import Dict, List, Optional, Tuple

from .akilli_aksesuar_yoneticisi import (
    AkilliAksesuarYoneticisi,
    AksesuarPolitikasi,
    GorevTipi,
    RobotDurumVerisi,
)
from .dinamik_engel_kacinici import DinamikEngel, DinamikEngelKacinici, HareketKomutlari
from .engel_tespit_sistemi import EngelTespitSistemi
from .rota_planlayici import Nokta, RotaNoktasi, RotaPlanlayici


class AdaptifNavigasyonKontrolcusu:
    """
    🚀 Master navigasyon kontrolcüsü

    Statik planlama + dinamik engel kaçınma + sensör füzyonu
    Bu sınıf tüm navigasyon katmanlarını yönetir ve koordine eder.
    """

    def __init__(self, navigation_config: Dict):
        self.logger = logging.getLogger("AdaptifNavigasyon")

        # Alt sistemleri başlat
        self.rota_planlayici = RotaPlanlayici(navigation_config)
        self.engel_kacinici = DinamikEngelKacinici(navigation_config.get("robot", {}))
        self.engel_tespit = EngelTespitSistemi(navigation_config.get("sensors", {}))

        # 🧠 Akıllı aksesuar yöneticisi
        self.aksesuar_yoneticisi = AkilliAksesuarYoneticisi(
            navigation_config.get("aksesuarlar", {})
        )

        # Mevcut görev durumu
        self.mevcut_gorev_tipi = GorevTipi.BEKLEME
        self.mevcut_batarya_seviyesi = 100  # %
        self.sarj_gerekli = False

        # Kontrol parametreleri
        self.max_replanning_frekansi = 2.0  # 2 Hz - 500ms'de bir replan
        self.son_replanning_zamani = 0.0

        # Navigation modları
        self.navigation_modu = "normal"  # normal, aggressive, conservative, emergency

        # Waypoint takip parametreleri
        self.waypoint_tolerance = 0.3  # 30cm tolerans
        self.mevcut_waypoint: Optional[RotaNoktasi] = None
        self.mevcut_robot_konumu: Optional[Nokta] = None
        self.mevcut_robot_hizi: Tuple[float, float] = (0.0, 0.0)

        # Emergency durumları
        self.emergency_stop_aktif = False
        self.stuck_detection_sayaci = 0
        self.stuck_detection_limit = 20  # 20 döngü = ~10 saniye

        # Performans metrikleri
        self.navigation_metrikleri = {
            "toplam_replanning": 0,
            "emergency_stop_sayisi": 0,
            "stuck_detection_sayisi": 0,
            "ortalama_hiz": 0.0,
            "hedef_yaklaşim_dogrulugu": 0.0
        }

        self.logger.info("🚀 Adaptif navigasyon kontrolcüsü başlatıldı")

    async def navigation_dongusu(self,
                                 robot_konumu: Nokta,
                                 robot_hizi: Tuple[float, float],
                                 kamera_frame=None,
                                 batarya_seviyesi: int = 100,
                                 bahce_sinir_mesafesi: float = 10.0,
                                 zorlu_arazide: bool = False,
                                 manuel_kontrol_aktif: bool = False) -> Optional[HareketKomutlari]:
        """
        🔄 Ana navigasyon döngüsü - kamera odaklı + akıllı aksesuar yönetimi

        Args:
            robot_konumu: Robot'un mevcut konumu
            robot_hizi: (doğrusal_hız, açısal_hız) tuple'ı
            kamera_frame: Kamera görüntüsü (ana sensör)
            batarya_seviyesi: Batarya yüzdesi (0-100)
            bahce_sinir_mesafesi: Bahçe sınırına olan mesafe (metre)
            zorlu_arazide: Zorlu arazi durumu
            manuel_kontrol_aktif: Manuel kontrol aktif mi?

        Returns:
            Robot hareket komutları veya None (dur)
        """

        # Durum güncelle
        self.mevcut_robot_konumu = robot_konumu
        self.mevcut_robot_hizi = robot_hizi
        self.mevcut_batarya_seviyesi = batarya_seviyesi

        # Emergency stop kontrolü
        if self.emergency_stop_aktif:
            return self._emergency_stop_komutu()

        # Kamera ile engel tara (ana tespit sistemi)
        engeller = await self.engel_tespit.engelleri_tara(
            kamera_frame, robot_konumu
        )

        # Engelleri dinamik kaçınıcıya ekle
        for engel in engeller:
            self.engel_kacinici.engel_ekle(engel)

        # Acil fren gerekli mi?
        if self.engel_kacinici.acil_fren_gerekli_mi(robot_konumu, robot_hizi[0]):
            self.logger.warning("🚨 ACİL FREN TETİKLENDİ!")
            self.navigation_metrikleri["emergency_stop_sayisi"] += 1
            return self._emergency_stop_komutu()

        # Mevcut waypoint var mı?
        if not self.mevcut_waypoint:
            self.mevcut_waypoint = self.rota_planlayici.get_next_waypoint()

        if not self.mevcut_waypoint:
            self.logger.info("✅ Rota tamamlandı!")
            return HareketKomutlari(0.0, 0.0, 1.0)  # Dur

        # Waypoint'e ulaştık mı?
        if self._waypoint_ulasildi_mi(robot_konumu, self.mevcut_waypoint):
            self.logger.debug(f"✅ Waypoint ulaşıldı: ({self.mevcut_waypoint.nokta.x:.2f}, {self.mevcut_waypoint.nokta.y:.2f})")
            self.mevcut_waypoint = self.rota_planlayici.get_next_waypoint()

            if not self.mevcut_waypoint:
                return HareketKomutlari(0.0, 0.0, 1.0)  # Rota bitti

        # Dinamik engel kaçınma ile hareket komutları üret
        hareket_komutlari = self.engel_kacinici.en_iyi_hareket_bul(
            robot_konumu,
            robot_hizi,
            self.mevcut_waypoint.nokta
        )

        # Hareket komutları bulunamadı mı? (Sıkışma durumu)
        if not hareket_komutlari:
            return await self._sikisma_durumu_coz(robot_konumu)

        # 🧠 Akıllı aksesuar kararı ver
        aksesuar_komutlari = self._aksesuar_karari_ver(
            robot_konumu, robot_hizi, engeller,
            batarya_seviyesi, bahce_sinir_mesafesi,
            zorlu_arazide, manuel_kontrol_aktif
        )

        # Hareket komutlarına aksesuar komutlarını ekle
        hareket_komutlari.aksesuar_komutlari = aksesuar_komutlari

        # Hareket komutlarını navigasyon moduna göre ayarla
        return self._hareket_komutlarini_ayarla(hareket_komutlari)

    def _aksesuar_karari_ver(self,
                             robot_konumu: Nokta,
                             robot_hizi: Tuple[float, float],
                             engeller: List[DinamikEngel],
                             batarya_seviyesi: int,
                             bahce_sinir_mesafesi: float,
                             zorlu_arazide: bool,
                             manuel_kontrol_aktif: bool) -> Dict[str, bool]:
        """
        🧠 Akıllı aksesuar karar verme algoritması

        Tüm faktörleri analiz ederek optimal aksesuar konfigürasyonu belirler.
        """

        # Robot durum verisi hazırla
        robot_hiz_skalar = math.sqrt(robot_hizi[0]**2 + robot_hizi[1]**2)

        # En yakın engel mesafesini bul
        en_yakin_engel_mesafesi = float('inf')
        engel_tespit_edildi = len(engeller) > 0

        if engel_tespit_edildi:
            for engel in engeller:
                mesafe = math.sqrt(
                    (engel.nokta.x - robot_konumu.x)**2 +
                    (engel.nokta.y - robot_konumu.y)**2
                )
                en_yakin_engel_mesafesi = min(en_yakin_engel_mesafesi, mesafe)
        else:
            en_yakin_engel_mesafesi = 10.0  # Engel yok, varsayılan mesafe

        # Robot durum verisi oluştur
        robot_durum = RobotDurumVerisi(
            gorev_tipi=self.mevcut_gorev_tipi,
            robot_hizi=robot_hiz_skalar,
            mevcut_konum=robot_konumu,
            hedef_konum=self.mevcut_waypoint.nokta if self.mevcut_waypoint else None,

            # Engel durumu
            engel_tespit_edildi=engel_tespit_edildi,
            en_yakin_engel_mesafesi=en_yakin_engel_mesafesi,

            # Batarya durumu
            batarya_seviyesi=batarya_seviyesi,
            sarj_gerekli=self.sarj_gerekli,

            # Konum durumu
            bahce_sinir_mesafesi=bahce_sinir_mesafesi,
            zorlu_arazide=zorlu_arazide,

            # Çevresel faktörler
            hiz_limit_aktif=self.navigation_modu == "conservative",
            manuel_kontrol_aktif=manuel_kontrol_aktif
        )

        # Akıllı aksesuar yöneticisinden karar al
        return self.aksesuar_yoneticisi.aksesuar_karari_ver(robot_durum)

    def rota_ayarla(self, rota_tipi: str, hedef_nokta: Optional[Nokta] = None):
        """🗺️ Yeni rota ayarla ve görev tipini güncelle"""

        if rota_tipi == "mowing":
            # Biçme rotası
            self.mevcut_gorev_tipi = GorevTipi.BICME
            asyncio.create_task(self._bicme_rotasi_ayarla())
        elif rota_tipi == "charging":
            # Şarj rotası
            self.mevcut_gorev_tipi = GorevTipi.SARJ_ARAMA
            asyncio.create_task(self._sarj_rotasi_ayarla())
        elif rota_tipi == "point_to_point" and hedef_nokta:
            # Nokta-nokta rotası
            self.mevcut_gorev_tipi = GorevTipi.NOKTA_ARASI
            asyncio.create_task(self._nokta_rotasi_ayarla(hedef_nokta))
        else:
            self.logger.error(f"❌ Bilinmeyen rota tipi: {rota_tipi}")

    def gorev_tipi_ayarla(self, yeni_gorev: GorevTipi):
        """📋 Görev tipini manuel olarak ayarla"""
        self.mevcut_gorev_tipi = yeni_gorev
        self.logger.info(f"📋 Görev tipi değişti: {yeni_gorev.value}")

    def batarya_durumu_guncelle(self, seviye: int, sarj_gerekli: bool = False):
        """🔋 Batarya durumunu güncelle"""
        self.mevcut_batarya_seviyesi = seviye
        self.sarj_gerekli = sarj_gerekli

        # Batarya durumuna göre görev tipi güncelle
        if sarj_gerekli or seviye < 20:
            self.mevcut_gorev_tipi = GorevTipi.SARJ_ARAMA

    def aksesuar_politikasi_ayarla(self, politika: AksesuarPolitikasi):
        """🎛️ Aksesuar politikasını değiştir"""
        self.aksesuar_yoneticisi.politika_degistir(politika)
        self.logger.info(f"🎛️ Aksesuar politikası: {politika.value}")

    async def _bicme_rotasi_ayarla(self):
        """🌾 Biçme rotası ayarla"""
        self.logger.info("🌾 Biçme rotası planlanıyor...")

        try:
            rota = await self.rota_planlayici.boustrophedon_rota_olustur()
            if rota:
                self.logger.info(f"✅ Biçme rotası hazır: {len(rota)} waypoint")
                self.mevcut_waypoint = None  # Yeni rotayı başlat
            else:
                self.logger.error("❌ Biçme rotası oluşturulamadı!")
        except Exception as e:
            self.logger.error(f"❌ Biçme rotası hatası: {e}")

    async def _sarj_rotasi_ayarla(self):
        """🔋 Şarj rotası ayarla"""
        self.logger.info("🔋 Şarj rotası planlanıyor...")

        try:
            # GPS config'i al (gerçek implementasyonda config'ten)
            gps_config = {
                "latitude": 40.123456,
                "longitude": 29.123456,
                "accuracy_radius": 3.0
            }

            rota = await self.rota_planlayici.sarj_istasyonu_rotasi(
                konum_takipci=None,  # Gerçek implementasyonda konum takipçi gerekli
                gps_dock_config=gps_config
            )

            if rota:
                self.logger.info(f"✅ Şarj rotası hazır: {len(rota)} waypoint")
                self.mevcut_waypoint = None
            else:
                self.logger.error("❌ Şarj rotası oluşturulamadı!")
        except Exception as e:
            self.logger.error(f"❌ Şarj rotası hatası: {e}")

    async def _nokta_rotasi_ayarla(self, hedef: Nokta):
        """🎯 Nokta-nokta rotası ayarla"""
        self.logger.info(f"🎯 Hedef nokta rotası: ({hedef.x:.2f}, {hedef.y:.2f})")

        try:
            if not self.mevcut_robot_konumu:
                self.logger.error("❌ Robot konumu bilinmiyor!")
                return

            # Robot konumunu Nokta nesnesine dönüştür (A* algoritması için)
            if hasattr(self.mevcut_robot_konumu, 'x') and hasattr(self.mevcut_robot_konumu, 'y'):
                # Zaten Nokta nesnesiyse direkt kullan
                baslangic_nokta = self.mevcut_robot_konumu
            else:
                # Konum nesnesiyse Nokta'ya dönüştür
                baslangic_nokta = Nokta(
                    x=self.mevcut_robot_konumu.x,
                    y=self.mevcut_robot_konumu.y
                )

            # A* ile rota bul
            nokta_listesi = await self.rota_planlayici.a_star_rota_bul(
                baslangic_nokta, hedef
            )

            if nokta_listesi:
                # Nokta listesini RotaNoktasi'na çevir
                rota = []
                for i, nokta in enumerate(nokta_listesi):
                    # Yön hesapla
                    if i + 1 < len(nokta_listesi):
                        dx = nokta_listesi[i + 1].x - nokta.x
                        dy = nokta_listesi[i + 1].y - nokta.y
                        yon = math.atan2(dy, dx)
                    else:
                        yon = 0.0

                    rota_noktasi = RotaNoktasi(
                        nokta=nokta,
                        yon=yon,
                        hiz=0.3,  # Normal hız
                        aksesuar_aktif=False
                    )
                    rota.append(rota_noktasi)

                # Rotayı ayarla
                self.rota_planlayici.mevcut_rota = rota
                self.rota_planlayici.rota_index = 0
                self.mevcut_waypoint = None

                self.logger.info(f"✅ Nokta rotası hazır: {len(rota)} waypoint")
            else:
                self.logger.error("❌ Hedefe rota bulunamadı!")
        except Exception as e:
            self.logger.error(f"❌ Nokta rotası hatası: {e}")

    def _waypoint_ulasildi_mi(self, robot_konum: Nokta, waypoint: RotaNoktasi) -> bool:
        """📍 Waypoint'e ulaşıldı mı kontrol et"""
        mesafe = math.sqrt(
            (robot_konum.x - waypoint.nokta.x)**2 +
            (robot_konum.y - waypoint.nokta.y)**2
        )
        return mesafe <= self.waypoint_tolerance

    async def _sikisma_durumu_coz(self, robot_konumu: Nokta) -> HareketKomutlari:
        """🔄 Sıkışma durumunu çöz"""

        self.stuck_detection_sayaci += 1
        self.navigation_metrikleri["stuck_detection_sayisi"] += 1

        self.logger.warning(f"⚠️ Sıkışma tespit edildi! Sayaç: {self.stuck_detection_sayaci}")

        if self.stuck_detection_sayaci >= self.stuck_detection_limit:
            self.logger.error("🚨 Robot sıkıştı - emergency stop!")
            self.emergency_stop_aktif = True
            return self._emergency_stop_komutu()

        # Replanning gerekli mi?
        simdi = time.time()
        if (simdi - self.son_replanning_zamani) > (1.0 / self.max_replanning_frekansi):
            await self._replanning_yap()
            self.son_replanning_zamani = simdi

        # Geri gitmeyi dene
        return HareketKomutlari(-0.1, 0.2, 0.3)  # Yavaş geri git ve dön

    async def _replanning_yap(self):
        """🔄 Rotayı yeniden planla"""

        self.logger.info("🔄 Rota yeniden planlanıyor...")
        self.navigation_metrikleri["toplam_replanning"] += 1

        if not self.mevcut_waypoint or not self.mevcut_robot_konumu:
            return

        try:
            # Mevcut konumu Nokta nesnesine dönüştür (A* algoritması için)
            if hasattr(self.mevcut_robot_konumu, 'x') and hasattr(self.mevcut_robot_konumu, 'y'):
                # Zaten Nokta nesnesiyse direkt kullan
                baslangic_nokta = self.mevcut_robot_konumu
            else:
                # Konum nesnesiyse Nokta'ya dönüştür
                baslangic_nokta = Nokta(
                    x=self.mevcut_robot_konumu.x,
                    y=self.mevcut_robot_konumu.y
                )

            # Mevcut konumdan hedefe yeni rota bul
            yeni_nokta_listesi = await self.rota_planlayici.a_star_rota_bul(
                baslangic_nokta,
                self.mevcut_waypoint.nokta
            )

            if yeni_nokta_listesi:
                # Yeni rotayı ayarla
                # Bu implementasyonda basitleştirilmiştir
                self.logger.info("✅ Yeni rota bulundu")
                self.stuck_detection_sayaci = 0  # Sıfırla
            else:
                self.logger.warning("⚠️ Yeni rota bulunamadı")

        except Exception as e:
            self.logger.error(f"❌ Replanning hatası: {e}")

    def _hareket_komutlarini_ayarla(self, komutlar: HareketKomutlari) -> HareketKomutlari:
        """⚙️ Hareket komutlarını navigasyon moduna göre ayarla"""

        if self.navigation_modu == "conservative":
            # Muhafazakar mod - hızları azalt
            komutlar.dogrusal_hiz *= 0.5
            komutlar.acisal_hiz *= 0.5
        elif self.navigation_modu == "aggressive":
            # Agresif mod - hızları artır (sınırlarda)
            komutlar.dogrusal_hiz *= 1.2
            komutlar.acisal_hiz *= 1.2
        # normal mod için değişiklik yok

        # Güvenlik sınırları
        komutlar.dogrusal_hiz = max(-0.5, min(komutlar.dogrusal_hiz, 0.5))
        komutlar.acisal_hiz = max(-1.0, min(komutlar.acisal_hiz, 1.0))

        return komutlar

    def _emergency_stop_komutu(self) -> HareketKomutlari:
        """🛑 Emergency stop komutu"""
        return HareketKomutlari(0.0, 0.0, 0.0)

    def emergency_stop_kaldir(self):
        """🟢 Emergency stop'u kaldır"""
        self.emergency_stop_aktif = False
        self.stuck_detection_sayaci = 0
        self.logger.info("🟢 Emergency stop kaldırıldı")

    def navigation_modu_degistir(self, yeni_mod: str):
        """🎛️ Navigation modunu değiştir"""

        valid_modlar = ["normal", "aggressive", "conservative", "emergency"]
        if yeni_mod in valid_modlar:
            self.navigation_modu = yeni_mod
            self.logger.info(f"🎛️ Navigation modu değişti: {yeni_mod}")
        else:
            self.logger.error(f"❌ Geçersiz navigation modu: {yeni_mod}")

    def hedef_konum_ayarla(self, hedef: Nokta):
        """🎯 Hedef konum ayarla ve basit waypoint oluştur"""
        self.logger.info(f"🎯 Yeni hedef konum: ({hedef.x:.2f}, {hedef.y:.2f})")

        # Basit waypoint oluştur ve ayarla
        from .rota_planlayici import RotaNoktasi
        hedef_waypoint = RotaNoktasi(
            nokta=hedef,
            yon=0.0,
            hiz=0.3,
            aksesuar_aktif=True
        )
        self.mevcut_waypoint = hedef_waypoint

    def waypoint_ekle(self, waypoint: RotaNoktasi):
        """📍 Rotaya waypoint ekle"""
        self.logger.info(f"📍 Waypoint eklendi: ({waypoint.nokta.x:.2f}, {waypoint.nokta.y:.2f})")

        # Mevcut rotaya waypoint ekle
        if self.rota_planlayici.mevcut_rota:
            self.rota_planlayici.mevcut_rota.append(waypoint)
        else:
            # Yeni rota oluştur
            self.rota_planlayici.mevcut_rota = [waypoint]
            self.rota_planlayici.rota_index = 0

    def durum_raporu(self) -> Dict:
        """📊 Navigasyon durum raporu"""

        return {
            "navigation_modu": self.navigation_modu,
            "emergency_stop": self.emergency_stop_aktif,
            "gorev_tipi": self.mevcut_gorev_tipi.value,
            "batarya_seviyesi": self.mevcut_batarya_seviyesi,
            "sarj_gerekli": self.sarj_gerekli,
            "mevcut_waypoint": {
                "x": self.mevcut_waypoint.nokta.x if self.mevcut_waypoint else None,
                "y": self.mevcut_waypoint.nokta.y if self.mevcut_waypoint else None
            },
            "stuck_sayaci": self.stuck_detection_sayaci,
            "rota_ilerleme": self.rota_planlayici.rota_ilerlemesi(),
            "engel_durumu": self.engel_kacinici.engel_durumu_raporu(),
            "sensor_durumu": self.engel_tespit.sensör_durumu_raporu(),
            "aksesuar_durumu": self.aksesuar_yoneticisi.durum_raporu(),
            "metrikkler": self.navigation_metrikleri
        }

    async def kalibrasyon_yap(self):
        """⚙️ Tüm sistemlerin kalibrasyonu"""
        self.logger.info("⚙️ Sistem kalibrasyonu başlatılıyor...")

        # Sensör kalibrasyonu
        self.engel_tespit.sensör_kalibrasyonu_yap()

        # Test modları
        sensor_test = await self.engel_tespit.test_modu_calistir()

        if sensor_test:
            self.logger.info("✅ Sistem kalibrasyonu tamamlandı")
        else:
            self.logger.error("❌ Kalibrasyon hatası!")

    async def performans_optimizasyonu(self):
        """🚀 Performans optimizasyonu"""

        # Metriklerden öğren ve parametreleri optimize et
        metrikkler = self.navigation_metrikleri

        if metrikkler["toplam_replanning"] > 50:
            # Çok fazla replanning - grid resolution'ı artır
            self.rota_planlayici.grid_resolution *= 1.1
            self.logger.info("📈 Grid resolution artırıldı")

        if metrikkler["emergency_stop_sayisi"] > 10:
            # Çok fazla emergency stop - güvenlik mesafesini artır
            self.engel_kacinici.guvenlik_mesafesi *= 1.1
            self.logger.info("📈 Güvenlik mesafesi artırıldı")

        self.logger.info("🚀 Performans optimizasyonu tamamlandı")
