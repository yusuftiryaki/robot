"""
🛡️ Güvenlik Sistemi - Robot'un Guardian Angel'ı
Hacı Abi güvenliği hiç şaka yapmaz!

Bu sistem robot'un güvenli çalışmasını sağlar:
- Eğim kontrolü (devrilme önleme)
- Acil durdurma butonu (sensör okuyucu üzerinden)
- Batarya güvenlik kontrolleri
- Watchdog timer
"""

import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

from hardware.hal.interfaces import AcilDurmaVeri, GucVeri, IMUVeri


class GuvenlikSeviyesi(Enum):
    """Güvenlik seviyesi enum'u"""
    GUVENLI = 1
    UYARI = 2
    TEHLIKE = 3
    ACIL_DURUM = 4


@dataclass
class GuvenlikDurumu:
    """Güvenlik durumu bilgisi"""
    seviye: GuvenlikSeviyesi
    acil_durum: bool
    sebep: str
    detaylar: Dict[str, Any]


class GuvenlikSistemi:
    """
    🛡️ Robot Güvenlik Sistemi

    Robot'un güvenli çalışmasını sağlayan ana güvenlik sınıfı.
    Çeşitli sensörlerden gelen verileri analiz eder ve
    tehlikeli durumları tespit eder.
    """

    def __init__(self, config: Dict[str, Any], sensor_okuyucu):
        self.config = config
        self.sensor_okuyucu = sensor_okuyucu
        self.logger = logging.getLogger("GuvenlikSistemi")

        # Güvenlik sistemi genel ayarları
        safety_config = config.get("safety", {})
        self.guvenlik_sistemi_aktif = safety_config.get("enabled", True)

        # Acil durum yönetimi ayarları
        emergency_config = safety_config.get("emergency_management", {})
        self.acil_durum_kontrol_aktif = emergency_config.get("enabled", True)
        self.otomatik_kurtarma = emergency_config.get("auto_recovery", False)

        # Acil durdurma butonu ayarları
        emergency_button_config = emergency_config.get("emergency_stop_button", {})
        self.acil_buton_kontrol_aktif = emergency_button_config.get("enabled", True)
        self.manuel_reset_gerekli = emergency_button_config.get("require_manual_reset", True)

        # Eğim kontrolü ayarları
        tilt_config = safety_config.get("tilt_control", {})
        self.egim_kontrol_aktif = tilt_config.get("enabled", True)
        self.max_egim_acisi = tilt_config.get("max_tilt_angle", 30)
        self.uyari_esigi = tilt_config.get("warning_threshold", 0.7)
        self.hizli_degisim_esigi = tilt_config.get("rapid_change_threshold", 10)

        # Batarya güvenlik ayarları
        battery_config = safety_config.get("battery_safety", {})
        self.batarya_kontrol_aktif = battery_config.get("enabled", True)
        self.min_batarya_voltaji = battery_config.get("min_battery_voltage", 10.5)
        self.hizli_bosalma_esigi = battery_config.get("rapid_drain_threshold", 5.0)
        self.max_akim_cekimi = battery_config.get("max_current_draw", 5.0)

        # Watchdog ayarları
        watchdog_config = safety_config.get("watchdog", {})
        self.watchdog_aktif = watchdog_config.get("enabled", True)
        self.watchdog_timeout = watchdog_config.get("timeout", 5)

        # Loglama ayarları
        logging_config = safety_config.get("logging", {})
        self.tum_olaylari_logla = logging_config.get("log_all_events", True)
        self.log_seviyesi = logging_config.get("log_level", "INFO")

        # Durum takibi
        self.acil_durum_aktif = False
        self.son_watchdog_zamani = time.time()
        self.guvenlik_ihlal_sayaci = 0

        # Önceki değerler (trend analizi için)
        self.onceki_egim = {"roll": 0, "pitch": 0}
        self.onceki_batarya_seviye = 100

        self._log_baslangic_durumu()

    def _log_baslangic_durumu(self):
        """Başlangıç durumunu logla"""
        if not self.guvenlik_sistemi_aktif:
            self.logger.warning("⚠️ GÜVENLİK SİSTEMİ DEVRE DIŞI!")
            return

        self.logger.info("🛡️ Güvenlik sistemi başlatıldı")
        self.logger.info(f"  📊 Acil durum kontrolü: {'✅' if self.acil_durum_kontrol_aktif else '❌'}")
        self.logger.info(f"  📐 Eğim kontrolü: {'✅' if self.egim_kontrol_aktif else '❌'}")
        self.logger.info(f"  🔋 Batarya kontrolü: {'✅' if self.batarya_kontrol_aktif else '❌'}")
        self.logger.info(f"  ⏰ Watchdog kontrolü: {'✅' if self.watchdog_aktif else '❌'}")

    def _emergency_stop_callback(self, channel):
        """Acil durdurma butonu basıldığında çağrılır - artık kullanılmıyor"""
        # Bu callback artık sensör okuyucu üzerinden yönetiliyor
        self.logger.debug("Eski GPIO callback çağrıldı (artık kullanılmıyor)")

    def acil_durum_kontrolu(self, sensor_data: Dict[str, Any]):
        """
        Ana güvenlik kontrol döngüsü. Tüm kontrolleri yapar ve gerekirse
        acil durumu aktif eder.
        """
        # Güvenlik sistemi devre dışıysa hiçbir şey yapma
        if not self.guvenlik_sistemi_aktif:
            return

        # Zaten acil durumdaysa, yeni kontrol yapmaya gerek yok.
        if self.acil_durum_aktif:
            return

        try:
            # Kapsamlı kontrol fonksiyonunu çağırarak mevcut güvenlik durumunu al
            guvenlik_durumu = self.kontrol_et(sensor_data)

            # Eğer durum ACIL_DURUM ise, sistemi kilitle
            if guvenlik_durumu.seviye == GuvenlikSeviyesi.ACIL_DURUM:
                self.logger.critical(
                    f"🚨 ACİL DURUM TETİKLENDİ! Sebep: {guvenlik_durumu.sebep}"
                )
                self.acil_durum_aktif = True
                self.guvenlik_ihlal_sayaci += 1
                # Olayı logla
                if self.tum_olaylari_logla:
                    self._log_guvenlik_olayi(guvenlik_durumu.seviye, f"Sebep: {guvenlik_durumu.sebep} - Detaylar: {guvenlik_durumu.detaylar}")

            # Diğer seviyeler için sadece loglama yapabiliriz
            elif guvenlik_durumu.seviye != GuvenlikSeviyesi.GUVENLI and self.tum_olaylari_logla:
                self._log_guvenlik_olayi(guvenlik_durumu.seviye, f"Sebep: {guvenlik_durumu.sebep} - Detaylar: {guvenlik_durumu.detaylar}")

        except Exception as e:
            self.logger.error(f"Güvenlik kontrolü sırasında beklenmedik hata: {e}", exc_info=True)
            # Güvenlik sistemi aktifse fail-safe moduna geç
            if self.guvenlik_sistemi_aktif:
                self.acil_durum_aktif = True  # Ne olur ne olmaz, güvenli tarafta kalalım.

    def acil_durum_aktif_mi(self) -> bool:
        """Acil durumun aktif olup olmadığını döndürür."""
        return self.acil_durum_aktif

    def reset(self):
        """Güvenlik durumunu sıfırlar (örneğin, acil durum sonrası)."""
        self.logger.warning("Güvenlik durumu sıfırlanıyor.")
        self.acil_durum_aktif = False
        self.son_watchdog_zamani = time.time()
        self.guvenlik_ihlal_sayaci = 0
        self.logger.info("Güvenlik durumu normale döndü.")

    def kontrol_et(self, sensor_data: Dict[str, Any]) -> GuvenlikDurumu:
        """
        🔍 Ana güvenlik kontrolü

        Tüm sensör verilerini analiz eder ve güvenlik durumunu belirler.
        """
        # Güvenlik sistemi devre dışıysa güvenli döndür
        if not self.guvenlik_sistemi_aktif:
            return GuvenlikDurumu(
                seviye=GuvenlikSeviyesi.GUVENLI,
                acil_durum=False,
                sebep="Güvenlik sistemi devre dışı",
                detaylar={"safety_system_disabled": True}
            )

        # Watchdog'u güncelle (aktifse)
        if self.watchdog_aktif:
            self.watchdog_update()

        # Acil durdurma butonu kontrolü (aktifse)
        if self.acil_buton_kontrol_aktif and self.acil_durum_kontrol_aktif:
            acil_durma_verisi = sensor_data.get("acil_durma")
            if self.acil_durum_aktif or self._acil_durdurma_basili(acil_durma_verisi):
                return GuvenlikDurumu(
                    seviye=GuvenlikSeviyesi.ACIL_DURUM,
                    acil_durum=True,
                    sebep="Acil durdurma butonu basıldı",
                    detaylar={"button_pressed": True}
                )

        kontrollar = []

        # Eğim kontrolü (aktifse)
        if self.egim_kontrol_aktif:
            imu_verisi = sensor_data.get("imu")
            egim_kontrolu = self._egim_kontrol(imu_verisi)
            kontrollar.append(egim_kontrolu)
            if egim_kontrolu.acil_durum:
                return egim_kontrolu

        # Batarya güvenlik kontrolü (aktifse)
        if self.batarya_kontrol_aktif:
            guc_verisi = sensor_data.get("guc")
            batarya_kontrolu = self._batarya_guvenlik_kontrol(guc_verisi)
            kontrollar.append(batarya_kontrolu)
            if batarya_kontrolu.acil_durum:
                return batarya_kontrolu

        # Watchdog kontrolü (aktifse)
        if self.watchdog_aktif:
            watchdog_kontrolu = self._watchdog_kontrol()
            kontrollar.append(watchdog_kontrolu)
            if watchdog_kontrolu.acil_durum:
                return watchdog_kontrolu

        # Hiç kontrol aktif değilse veya hepsi güvenliyse
        if not kontrollar:
            return GuvenlikDurumu(
                seviye=GuvenlikSeviyesi.GUVENLI,
                acil_durum=False,
                sebep="Tüm güvenlik kontrolleri devre dışı",
                detaylar={"no_active_controls": True}
            )

        # En yüksek seviyeli uyarıyı döndür
        en_kritik = max(kontrollar, key=lambda x: list(GuvenlikSeviyesi).index(x.seviye))
        return en_kritik

    def _egim_kontrol(self, imu_data: Optional[IMUVeri]) -> GuvenlikDurumu:
        """📐 Robot eğim kontrolü - devrilmeyi önle"""
        if not imu_data:
            return GuvenlikDurumu(
                seviye=GuvenlikSeviyesi.UYARI,
                acil_durum=False,
                sebep="IMU verisi yok",
                detaylar={"imu_missing": True}
            )

        roll = abs(imu_data.roll)
        pitch = abs(imu_data.pitch)

        max_egim = max(roll, pitch)

        # Kritik eğim - acil durum
        if max_egim > self.max_egim_acisi:
            self.logger.warning(f"🚨 KRİTİK EĞİM! Roll: {roll:.1f}°, Pitch: {pitch:.1f}°")
            return GuvenlikDurumu(
                seviye=GuvenlikSeviyesi.ACIL_DURUM,
                acil_durum=True,
                sebep=f"Kritik eğim tespit edildi: {max_egim:.1f}°",
                detaylar={"roll": roll, "pitch": pitch, "max_angle": max_egim}
            )

        # Uyarı seviyesi eğim
        elif max_egim > self.max_egim_acisi * self.uyari_esigi:
            return GuvenlikDurumu(
                seviye=GuvenlikSeviyesi.UYARI,
                acil_durum=False,
                sebep=f"Yüksek eğim: {max_egim:.1f}°",
                detaylar={"roll": roll, "pitch": pitch, "max_angle": max_egim}
            )

        # Eğim hızla artıyor mu?
        roll_degisim = abs(roll - self.onceki_egim["roll"])
        pitch_degisim = abs(pitch - self.onceki_egim["pitch"])

        if roll_degisim > self.hizli_degisim_esigi or pitch_degisim > self.hizli_degisim_esigi:
            return GuvenlikDurumu(
                seviye=GuvenlikSeviyesi.TEHLIKE,
                acil_durum=False,
                sebep="Hızlı eğim değişimi",
                detaylar={"roll_change": roll_degisim, "pitch_change": pitch_degisim}
            )

        # Önceki değerleri kaydet
        self.onceki_egim = {"roll": roll, "pitch": pitch}

        return GuvenlikDurumu(
            seviye=GuvenlikSeviyesi.GUVENLI,
            acil_durum=False,
            sebep="Eğim normal",
            detaylar={"roll": roll, "pitch": pitch}
        )

    def _batarya_guvenlik_kontrol(self, guc_data: Optional[GucVeri]) -> GuvenlikDurumu:
        """🔋 Batarya güvenlik kontrolü"""
        if not guc_data:
            return GuvenlikDurumu(
                seviye=GuvenlikSeviyesi.UYARI,
                acil_durum=False,
                sebep="Batarya verisi yok",
                detaylar={"battery_missing": True}
            )

        voltaj = guc_data.voltaj
        seviye = guc_data.batarya_seviyesi
        akim = guc_data.akim

        # Kritik düşük voltaj
        if voltaj < self.min_batarya_voltaji:
            return GuvenlikDurumu(
                seviye=GuvenlikSeviyesi.ACIL_DURUM,
                acil_durum=True,
                sebep=f"Kritik düşük voltaj: {voltaj:.1f}V",
                detaylar={"voltage": voltaj, "level": seviye, "current": akim}
            )

        # Hızlı batarya tükenmesi
        seviye_degisim = self.onceki_batarya_seviye - seviye
        if seviye_degisim > self.hizli_bosalma_esigi:  # Config'den alınan eşik
            self.onceki_batarya_seviye = seviye
            return GuvenlikDurumu(
                seviye=GuvenlikSeviyesi.UYARI,
                acil_durum=False,
                sebep=f"Hızlı batarya tükenmesi: {seviye_degisim:.1f}%",
                detaylar={"voltage": voltaj, "level": seviye, "drain_rate": seviye_degisim}
            )

        # Aşırı akım
        if akim > self.max_akim_cekimi:  # Config'den alınan eşik
            return GuvenlikDurumu(
                seviye=GuvenlikSeviyesi.UYARI,
                acil_durum=False,
                sebep=f"Yüksek akım tüketimi: {akim:.1f}A",
                detaylar={"voltage": voltaj, "level": seviye, "current": akim}
            )

        self.onceki_batarya_seviye = seviye

        return GuvenlikDurumu(
            seviye=GuvenlikSeviyesi.GUVENLI,
            acil_durum=False,
            sebep="Batarya durumu normal",
            detaylar={"voltage": voltaj, "level": seviye, "current": akim}
        )

    def _watchdog_kontrol(self) -> GuvenlikDurumu:
        """⏰ Watchdog timer kontrolü"""
        suanki_zaman = time.time()
        son_update_farki = suanki_zaman - self.son_watchdog_zamani

        if son_update_farki > self.watchdog_timeout:
            return GuvenlikDurumu(
                seviye=GuvenlikSeviyesi.ACIL_DURUM,
                acil_durum=True,
                sebep=f"Watchdog timeout: {son_update_farki:.1f}s",
                detaylar={"timeout": son_update_farki, "threshold": self.watchdog_timeout}
            )

        return GuvenlikDurumu(
            seviye=GuvenlikSeviyesi.GUVENLI,
            acil_durum=False,
            sebep="Watchdog normal",
            detaylar={"last_update": son_update_farki}
        )

    def _acil_durdurma_basili(self, acil_durma_verisi: Optional[AcilDurmaVeri]) -> bool:
        """Acil durdurma butonu basılı mı kontrol et (sensör verilerinden)"""
        if not acil_durma_verisi:
            return False

        # AcilDurmaVeri objesinden durumu oku
        return acil_durma_verisi.aktif

    def watchdog_update(self):
        """Watchdog timer'ı güncelle"""
        self.son_watchdog_zamani = time.time()

    def acil_durum_temizle(self):
        """Acil durumu temizle (manuel müdahale sonrası)"""
        # Güvenlik sistemi devre dışıysa her zaman temizlenmesine izin ver
        if not self.guvenlik_sistemi_aktif:
            self.acil_durum_aktif = False
            self.guvenlik_ihlal_sayaci = 0
            self.logger.info("✅ Acil durum temizlendi (güvenlik sistemi devre dışı)")
            return True

        # Manuel reset gerekli mi kontrol et
        if self.manuel_reset_gerekli:
            # Manuel reset, artık sensör verilerinden kontrol edilecek
            # Burada sadece bayrak temizler, gerçek buton durumu sonraki döngüde kontrol edilir
            self.acil_durum_aktif = False
            self.guvenlik_ihlal_sayaci = 0
            self.logger.info("✅ Acil durum manuel olarak temizlendi")
            return True
        else:
            # Otomatik kurtarma aktifse (geliştirme/test aşamasında kullanışlı)
            if self.otomatik_kurtarma:
                self.acil_durum_aktif = False
                self.guvenlik_ihlal_sayaci = 0
                self.logger.info("✅ Acil durum otomatik olarak temizlendi")
                return True
            else:
                self.logger.warning("⚠️ Manuel reset gerekli - acil durum temizlenemedi")
                return False

    def guvenlik_raporu(self) -> Dict[str, Any]:
        """Detaylı güvenlik raporu"""
        return {
            "sistem_durumu": {
                "guvenlik_sistemi_aktif": self.guvenlik_sistemi_aktif,
                "acil_durum_aktif": self.acil_durum_aktif,
                "son_watchdog": time.time() - self.son_watchdog_zamani,
                "ihlal_sayaci": self.guvenlik_ihlal_sayaci,
            },
            "kontrol_durumu": {
                "acil_durum_kontrolu": self.acil_durum_kontrol_aktif,
                "acil_buton_kontrolu": self.acil_buton_kontrol_aktif,
                "egim_kontrolu": self.egim_kontrol_aktif,
                "batarya_kontrolu": self.batarya_kontrol_aktif,
                "watchdog_kontrolu": self.watchdog_aktif,
            },
            "konfigürasyon": {
                "max_egim": self.max_egim_acisi,
                "uyari_esigi": self.uyari_esigi,
                "hizli_degisim_esigi": self.hizli_degisim_esigi,
                "min_batarya_voltaji": self.min_batarya_voltaji,
                "hizli_bosalma_esigi": self.hizli_bosalma_esigi,
                "max_akim_cekimi": self.max_akim_cekimi,
                "watchdog_timeout": self.watchdog_timeout,
                "otomatik_kurtarma": self.otomatik_kurtarma,
                "manuel_reset_gerekli": self.manuel_reset_gerekli,
            }
        }

    def _log_guvenlik_olayi(self, seviye: GuvenlikSeviyesi, mesaj: str):
        """Güvenlik olaylarını loglar"""
        log_mesaji = f"[{seviye.name}] {mesaj}"
        if seviye == GuvenlikSeviyesi.ACIL_DURUM:
            self.logger.critical(log_mesaji)
        elif seviye == GuvenlikSeviyesi.TEHLIKE:
            self.logger.error(log_mesaji)
        elif seviye == GuvenlikSeviyesi.UYARI:
            self.logger.warning(log_mesaji)
        else:
            self.logger.info(log_mesaji)

    def __del__(self):
        """Nesne yok edilirken temizlik"""
        # GPIO artık sensör okuyucu tarafından yönetiliyor
        self.logger.debug("Güvenlik sistemi temizleniyor")
