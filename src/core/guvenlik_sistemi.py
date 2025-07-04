"""
🛡️ Güvenlik Sistemi - Robot'un Guardian Angel'ı
Hacı Abi güvenliği hiç şaka yapmaz!

Bu sistem robot'un güvenli çalışmasını sağlar:
- Eğim kontrolü (devrilme önleme)
- Engel mesafe kontrolü
- Acil durdurma butonu
- Batarya güvenlik kontrolleri
- Watchdog timer
"""

import time
import logging
from typing import Dict, Any, NamedTuple
from dataclasses import dataclass
from enum import Enum


class GuvenlikSeviyesi(Enum):
    """Güvenlik seviyesi enum'u"""
    GUVENLI = "guvenli"
    UYARI = "uyari"
    TEHLIKE = "tehlike"
    ACIL_DURUM = "acil_durum"


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
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger("GuvenlikSistemi")
        
        # Güvenlik eşikleri
        self.max_egim_acisi = config.get("max_tilt_angle", 30)  # derece
        self.min_engel_mesafesi = config.get("obstacle_distance", 0.3)  # metre
        self.min_batarya_voltaji = config.get("min_battery_voltage", 10.5)  # volt
        self.watchdog_timeout = config.get("watchdog_timeout", 5)  # saniye
        
        # Acil durdurma pin'i
        self.acil_durdurma_pin = config.get("emergency_stop_pin", 17)
        
        # Durum takibi
        self.acil_durum_aktif = False
        self.son_watchdog_zamani = time.time()
        self.guvenlik_ihlal_sayaci = 0
        
        # Önceki değerler (trend analizi için)
        self.onceki_egim = {"roll": 0, "pitch": 0}
        self.onceki_batarya_seviye = 100
        
        self.logger.info("🛡️ Güvenlik sistemi başlatıldı")
        self._init_emergency_stop()
    
    def _init_emergency_stop(self):
        """Acil durdurma butonunu başlat"""
        try:
            # Raspberry Pi'de GPIO başlatma
            import RPi.GPIO as GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.acil_durdurma_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.add_event_detect(
                self.acil_durdurma_pin, 
                GPIO.FALLING, 
                callback=self._emergency_stop_callback, 
                bouncetime=200
            )
            self.logger.info(f"🚨 Acil durdurma butonu hazır (Pin {self.acil_durdurma_pin})")
        except Exception as e:
            self.logger.warning(f"⚠️ Acil durdurma butonu başlatılamadı: {e}")
    
    def _emergency_stop_callback(self, channel):
        """Acil durdurma butonu basıldığında çağrılır"""
        self.logger.warning("🚨 ACİL DURDURMA BUTONU BASILDI!")
        self.acil_durum_aktif = True
    
    def kontrol_et(self, sensor_data: Dict[str, Any]) -> GuvenlikDurumu:
        """
        🔍 Ana güvenlik kontrolü
        
        Tüm sensör verilerini analiz eder ve güvenlik durumunu belirler.
        """
        # Watchdog'u güncelle
        self.watchdog_update()
        
        # Acil durdurma butonu kontrolü
        if self.acil_durum_aktif or self._acil_durdurma_basili():
            return GuvenlikDurumu(
                seviye=GuvenlikSeviyesi.ACIL_DURUM,
                acil_durum=True,
                sebep="Acil durdurma butonu basıldı",
                detaylar={"button_pressed": True}
            )
        
        # Eğim kontrolü
        egim_kontrolu = self._egim_kontrol(sensor_data.get("imu", {}))
        if egim_kontrolu.acil_durum:
            return egim_kontrolu
        
        # Engel mesafe kontrolü
        engel_kontrolu = self._engel_mesafe_kontrol(sensor_data.get("ultrasonik", {}))
        if engel_kontrolu.acil_durum:
            return engel_kontrolu
        
        # Batarya güvenlik kontrolü
        batarya_kontrolu = self._batarya_guvenlik_kontrol(sensor_data.get("batarya", {}))
        if batarya_kontrolu.acil_durum:
            return batarya_kontrolu
        
        # Watchdog kontrolü
        watchdog_kontrolu = self._watchdog_kontrol()
        if watchdog_kontrolu.acil_durum:
            return watchdog_kontrolu
        
        # En yüksek seviyeli uyarıyı döndür
        kontrollar = [egim_kontrolu, engel_kontrolu, batarya_kontrolu, watchdog_kontrolu]
        en_kritik = max(kontrollar, key=lambda x: list(GuvenlikSeviyesi).index(x.seviye))
        
        return en_kritik
    
    def _egim_kontrol(self, imu_data: Dict[str, Any]) -> GuvenlikDurumu:
        """📐 Robot eğim kontrolü - devrilmeyi önle"""
        if not imu_data:
            return GuvenlikDurumu(
                seviye=GuvenlikSeviyesi.UYARI,
                acil_durum=False,
                sebep="IMU verisi yok",
                detaylar={"imu_missing": True}
            )
        
        roll = abs(imu_data.get("roll", 0))
        pitch = abs(imu_data.get("pitch", 0))
        
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
        elif max_egim > self.max_egim_acisi * 0.7:
            return GuvenlikDurumu(
                seviye=GuvenlikSeviyesi.UYARI,
                acil_durum=False,
                sebep=f"Yüksek eğim: {max_egim:.1f}°",
                detaylar={"roll": roll, "pitch": pitch, "max_angle": max_egim}
            )
        
        # Eğim hızla artıyor mu?
        roll_degisim = abs(roll - self.onceki_egim["roll"])
        pitch_degisim = abs(pitch - self.onceki_egim["pitch"])
        
        if roll_degisim > 10 or pitch_degisim > 10:  # 10 derece/döngü
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
    
    def _engel_mesafe_kontrol(self, ultrasonik_data: Dict[str, Any]) -> GuvenlikDurumu:
        """📏 Engel mesafe kontrolü"""
        if not ultrasonik_data:
            return GuvenlikDurumu(
                seviye=GuvenlikSeviyesi.UYARI,
                acil_durum=False,
                sebep="Ultrasonik sensör verisi yok",
                detaylar={"ultrasonic_missing": True}
            )
        
        # Tüm yönlerdeki mesafeleri kontrol et
        mesafeler = {
            "on": ultrasonik_data.get("front", float('inf')),
            "sol": ultrasonik_data.get("left", float('inf')),
            "sag": ultrasonik_data.get("right", float('inf')),
            "arka": ultrasonik_data.get("back", float('inf'))
        }
        
        en_yakin_mesafe = min(mesafeler.values())
        en_yakin_yon = min(mesafeler, key=mesafeler.get)
        
        # Çok yakın engel - acil durum
        if en_yakin_mesafe < self.min_engel_mesafesi * 0.5:
            return GuvenlikDurumu(
                seviye=GuvenlikSeviyesi.ACIL_DURUM,
                acil_durum=True,
                sebep=f"Çok yakın engel ({en_yakin_yon}): {en_yakin_mesafe:.2f}m",
                detaylar={"distances": mesafeler, "closest": en_yakin_mesafe}
            )
        
        # Yakın engel - uyarı
        elif en_yakin_mesafe < self.min_engel_mesafesi:
            return GuvenlikDurumu(
                seviye=GuvenlikSeviyesi.UYARI,
                acil_durum=False,
                sebep=f"Yakın engel ({en_yakin_yon}): {en_yakin_mesafe:.2f}m",
                detaylar={"distances": mesafeler, "closest": en_yakin_mesafe}
            )
        
        return GuvenlikDurumu(
            seviye=GuvenlikSeviyesi.GUVENLI,
            acil_durum=False,
            sebep="Engel mesafesi güvenli",
            detaylar={"distances": mesafeler}
        )
    
    def _batarya_guvenlik_kontrol(self, batarya_data: Dict[str, Any]) -> GuvenlikDurumu:
        """🔋 Batarya güvenlik kontrolü"""
        if not batarya_data:
            return GuvenlikDurumu(
                seviye=GuvenlikSeviyesi.UYARI,
                acil_durum=False,
                sebep="Batarya verisi yok",
                detaylar={"battery_missing": True}
            )
        
        voltaj = batarya_data.get("voltage", 12.0)
        seviye = batarya_data.get("level", 50)
        akim = batarya_data.get("current", 0)
        
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
        if seviye_degisim > 5:  # 5% hızla düşüyor
            self.onceki_batarya_seviye = seviye
            return GuvenlikDurumu(
                seviye=GuvenlikSeviyesi.UYARI,
                acil_durum=False,
                sebep=f"Hızlı batarya tükenmesi: {seviye_degisim:.1f}%",
                detaylar={"voltage": voltaj, "level": seviye, "drain_rate": seviye_degisim}
            )
        
        # Aşırı akım
        if akim > 5.0:  # 5A'dan fazla
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
    
    def _acil_durdurma_basili(self) -> bool:
        """Acil durdurma butonu basılı mı kontrol et"""
        try:
            import RPi.GPIO as GPIO
            return not GPIO.input(self.acil_durdurma_pin)  # Pull-up, basılı = LOW
        except:
            return False
    
    def watchdog_update(self):
        """Watchdog timer'ı güncelle"""
        self.son_watchdog_zamani = time.time()
    
    def acil_durum_temizle(self):
        """Acil durumu temizle (manuel müdahale sonrası)"""
        if not self._acil_durdurma_basili():
            self.acil_durum_aktif = False
            self.guvenlik_ihlal_sayaci = 0
            self.logger.info("✅ Acil durum temizlendi")
            return True
        return False
    
    def guvenlik_raporu(self) -> Dict[str, Any]:
        """Detaylı güvenlik raporu"""
        return {
            "acil_durum_aktif": self.acil_durum_aktif,
            "son_watchdog": time.time() - self.son_watchdog_zamani,
            "ihlal_sayaci": self.guvenlik_ihlal_sayaci,
            "konfigürasyon": {
                "max_egim": self.max_egim_acisi,
                "min_engel_mesafesi": self.min_engel_mesafesi,
                "min_batarya_voltaji": self.min_batarya_voltaji,
                "watchdog_timeout": self.watchdog_timeout
            }
        }
    
    def __del__(self):
        """Güvenlik sistemi kapatılıyor"""
        try:
            import RPi.GPIO as GPIO
            GPIO.cleanup()
        except:
            pass
