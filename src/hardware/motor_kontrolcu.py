"""
⚙️ Motor Kontrolcüsü - Robot'un Kasları
Hacı Abi'nin motor kontrolü burada!

Bu sınıf robot'un tüm motorlarını kontrol eder:
- Tekerlek motorları (hareket)
- Ana fırça motoru
- Yan fırça motorları
- Fan motoru
- Enkoder okuma ve hız kontrolü
"""

import asyncio
import logging
import math
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Tuple


class MotorTipi(Enum):
    """Motor tipi enum'u"""
    TEKERLEK = "tekerlek"
    FIRCA = "firca"
    FAN = "fan"


@dataclass
class MotorKomut:
    """Motor komut yapısı"""
    sol_hiz: float  # -1.0 ile 1.0 arası
    sag_hiz: float  # -1.0 ile 1.0 arası
    ana_firca: bool
    sol_firca: bool
    sag_firca: bool
    fan: bool


@dataclass
class HareketKomut:
    """Hareket komut yapısı"""
    linear_hiz: float    # m/s
    angular_hiz: float   # rad/s
    sure: float = 0.0    # saniye (0 = sürekli)


class MotorKontrolcu:
    """
    ⚙️ Ana Motor Kontrolcüsü

    Robot'un tüm motorlarını kontrol eden sınıf.
    PWM ile hız kontrolü yapar ve enkoder feedback'i alır.
    """

    def __init__(self, motor_config: Dict[str, Any]):
        self.config = motor_config
        self.logger = logging.getLogger("MotorKontrolcu")

        # Simülasyon modu kontrolü - hemen başta set et
        self.simulation_mode = self._is_simulation()

        # Motor durumları
        self.motorlar_aktif = False
        self.mevcut_hizlar = {"sol": 0.0, "sag": 0.0}
        self.enkoder_sayaclari = {"sol": 0, "sag": 0}
        self.firca_durumu = {"ana": False, "sol": False, "sag": False}
        self.fan_durumu = False

        # PID kontrolcü parametreleri
        self.pid_kp = 1.0
        self.pid_ki = 0.1
        self.pid_kd = 0.05
        self.pid_hata_integral = {"sol": 0.0, "sag": 0.0}
        self.pid_onceki_hata = {"sol": 0.0, "sag": 0.0}

        # Motor fizik parametreleri
        self.tekerlek_capi = 0.065  # metre
        self.tekerlek_base = 0.235  # metre
        self.enkoder_pulse_per_rev = 360

        # Log throttle mekanizması - spam önleme
        self.log_throttle_interval = 5.0  # saniye
        self.last_log_times = {
            "firca_start": 0.0,
            "firca_stop": 0.0
        }

        self.logger.info(f"⚙️ Motor kontrolcü başlatıldı (Simülasyon: {self.simulation_mode})")
        self._init_motors()

    def _should_log(self, log_key: str) -> bool:
        """
        Log throttle kontrolü - belirlenen süre geçmişse log'a izin ver

        Args:
            log_key: Log tipi anahtarı (firca_start, firca_stop, vs.)

        Returns:
            True: Log'a izin ver
            False: Log'ı atla (spam önleme)
        """
        current_time = time.time()
        last_log_time = self.last_log_times.get(log_key, 0.0)

        if current_time - last_log_time >= self.log_throttle_interval:
            self.last_log_times[log_key] = current_time
            return True
        return False

    def _is_simulation(self) -> bool:
        """Simülasyon modunda mı kontrol et"""
        try:
            import RPi.GPIO
            return False
        except (ImportError, RuntimeError):
            # ImportError: paket yok
            # RuntimeError: "This module can only be run on a Raspberry Pi!"
            return True

    def _init_motors(self):
        """Motorları başlat"""
        if self.simulation_mode:
            self._init_simulation_motors()
        else:
            self._init_real_motors()

    def _init_simulation_motors(self):
        """Simülasyon motorlarını başlat"""
        self.logger.info("🔧 Simülasyon motorları başlatılıyor...")
        # Simülasyon için sahte GPIO objesi
        self.gpio_motors = {
            "sol_tekerlek": {"pin_a": 18, "pin_b": 19, "pwm": None},
            "sag_tekerlek": {"pin_a": 21, "pin_b": 22, "pwm": None},
            "ana_firca": {"pin_a": 24, "pin_b": 25, "pwm": None},
            "sol_firca": {"pin_a": 26, "pin_b": 27, "pwm": None},
            "sag_firca": {"pin_a": 5, "pin_b": 6, "pwm": None},
            "fan": {"pin_a": 12, "pin_b": 13, "pwm": None}
        }
        self.logger.info("✅ Simülasyon motorları hazır!")

    def _init_real_motors(self):
        """Gerçek motorları başlat"""
        self.logger.info("🔧 Fiziksel motorlar başlatılıyor...")
        try:
            import RPi.GPIO as GPIO
            from gpiozero import Motor, PWMOutputDevice

            GPIO.setmode(GPIO.BCM)

            # Tekerlek motorları
            self.sol_motor = Motor(
                forward=self.config.get("left_wheel", {}).get("pin_a", 18),
                backward=self.config.get("left_wheel", {}).get("pin_b", 19)
            )
            self.sag_motor = Motor(
                forward=self.config.get("right_wheel", {}).get("pin_a", 21),
                backward=self.config.get("right_wheel", {}).get("pin_b", 22)
            )

            # Fırça motorları
            self.ana_firca_motor = Motor(
                forward=self.config.get("main_brush", {}).get("pin_a", 24),
                backward=self.config.get("main_brush", {}).get("pin_b", 25)
            )
            self.sol_firca_motor = Motor(
                forward=self.config.get("side_brush_left", {}).get("pin_a", 26),
                backward=self.config.get("side_brush_left", {}).get("pin_b", 27)
            )
            self.sag_firca_motor = Motor(
                forward=self.config.get("side_brush_right", {}).get("pin_a", 5),
                backward=self.config.get("side_brush_right", {}).get("pin_b", 6)
            )

            # Fan motoru
            self.fan_motor = Motor(
                forward=self.config.get("fan", {}).get("pin_a", 12),
                backward=self.config.get("fan", {}).get("pin_b", 13)
            )

            # Enkoder pinleri
            self.sol_enkoder_pin = self.config.get("left_wheel", {}).get("encoder_pin", 20)
            self.sag_enkoder_pin = self.config.get("right_wheel", {}).get("encoder_pin", 23)

            GPIO.setup(self.sol_enkoder_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.sag_enkoder_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

            # Enkoder interrupt'larını ayarla
            GPIO.add_event_detect(self.sol_enkoder_pin, GPIO.RISING, callback=self._sol_enkoder_callback)
            GPIO.add_event_detect(self.sag_enkoder_pin, GPIO.RISING, callback=self._sag_enkoder_callback)

            self.logger.info("✅ Fiziksel motorlar hazır!")

        except Exception as e:
            self.logger.error(f"❌ Motor başlatma hatası: {e}")
            self.simulation_mode = True
            self._init_simulation_motors()

    def _sol_enkoder_callback(self, channel):
        """Sol tekerlek enkoder callback"""
        self.enkoder_sayaclari["sol"] += 1

    def _sag_enkoder_callback(self, channel):
        """Sağ tekerlek enkoder callback"""
        self.enkoder_sayaclari["sag"] += 1

    async def hareket_uygula(self, hareket: HareketKomut):
        """
        🚶 Ana hareket uygulama fonksiyonu

        Linear ve angular hızları tekerlek hızlarına çevirir
        """
        # Kinematik hesaplama - differential drive
        sol_hiz, sag_hiz = self._kinematik_hesapla(hareket.linear_hiz, hareket.angular_hiz)

        self.logger.debug(f"🚶 Hareket: linear={hareket.linear_hiz:.2f}m/s, angular={hareket.angular_hiz:.2f}rad/s")
        self.logger.debug(f"⚙️ Tekerlek hızları: sol={sol_hiz:.2f}, sag={sag_hiz:.2f}")

        # Motor hızlarını uygula
        await self._tekerlek_hizlarini_ayarla(sol_hiz, sag_hiz)

        # Belirli süre hareket et
        if hareket.sure > 0:
            await asyncio.sleep(hareket.sure)
            await self.durdur()

    def _kinematik_hesapla(self, linear_hiz: float, angular_hiz: float) -> Tuple[float, float]:
        """
        🧮 Differential drive kinematik hesaplama

        Linear ve angular hızları sol/sağ tekerlek hızlarına çevirir
        """
        # v_sol = v - (ω * L) / 2
        # v_sag = v + (ω * L) / 2
        # v: linear hız, ω: angular hız, L: tekerlek base

        sol_hiz_ms = linear_hiz - (angular_hiz * self.tekerlek_base) / 2
        sag_hiz_ms = linear_hiz + (angular_hiz * self.tekerlek_base) / 2

        # m/s'yi PWM değerine çevir (-1.0 ile 1.0 arası)
        max_hiz = 0.5  # maksimum hız m/s
        sol_pwm = max(-1.0, min(1.0, sol_hiz_ms / max_hiz))
        sag_pwm = max(-1.0, min(1.0, sag_hiz_ms / max_hiz))

        return sol_pwm, sag_pwm

    async def _tekerlek_hizlarini_ayarla(self, sol_hiz: float, sag_hiz: float):
        """Tekerlek motorlarının hızını ayarla"""
        self.mevcut_hizlar["sol"] = sol_hiz
        self.mevcut_hizlar["sag"] = sag_hiz

        if self.simulation_mode:
            await self._simulation_motor_control(sol_hiz, sag_hiz)
        else:
            await self._real_motor_control(sol_hiz, sag_hiz)

    async def _simulation_motor_control(self, sol_hiz: float, sag_hiz: float):
        """Simülasyon motor kontrolü"""
        # Simülasyon enkoder değerlerini güncelle
        dt = 0.1  # 100ms
        sol_rpm = sol_hiz * 60 / (math.pi * self.tekerlek_capi)
        sag_rpm = sag_hiz * 60 / (math.pi * self.tekerlek_capi)

        sol_pulse_per_sec = (sol_rpm / 60) * self.enkoder_pulse_per_rev
        sag_pulse_per_sec = (sag_rpm / 60) * self.enkoder_pulse_per_rev

        self.enkoder_sayaclari["sol"] += int(sol_pulse_per_sec * dt)
        self.enkoder_sayaclari["sag"] += int(sag_pulse_per_sec * dt)

        self.logger.debug(f"🎮 Simülasyon motor: sol={sol_hiz:.2f}, sag={sag_hiz:.2f}")

    async def _real_motor_control(self, sol_hiz: float, sag_hiz: float):
        """Gerçek motor kontrolü"""
        # Sol motor
        if sol_hiz > 0:
            self.sol_motor.forward(abs(sol_hiz))
        elif sol_hiz < 0:
            self.sol_motor.backward(abs(sol_hiz))
        else:
            self.sol_motor.stop()

        # Sağ motor
        if sag_hiz > 0:
            self.sag_motor.forward(abs(sag_hiz))
        elif sag_hiz < 0:
            self.sag_motor.backward(abs(sag_hiz))
        else:
            self.sag_motor.stop()

    async def fircalari_calistir(self, aktif: bool, ana: bool = True, yan: bool = True):
        """
        🌪️ Fırçaları çalıştır/durdur

        Args:
            aktif: Fırçalar çalışsın mı?
            ana: Ana fırça dahil mi?
            yan: Yan fırçalar dahil mi?
        """
        if aktif:
            # Log throttle - sadece 5 saniyede bir defa logla
            if self._should_log("firca_start"):
                self.logger.info("🌪️ Fırçalar çalıştırılıyor...")

            if ana:
                self.firca_durumu["ana"] = True
                await self._ana_firca_calistir(True)

            if yan:
                self.firca_durumu["sol"] = True
                self.firca_durumu["sag"] = True
                await self._yan_fircalari_calistir(True)
        else:
            # Log throttle - sadece 5 saniyede bir defa logla
            if self._should_log("firca_stop"):
                self.logger.info("⏸️ Fırçalar durduruluyor...")

            self.firca_durumu = {"ana": False, "sol": False, "sag": False}
            await self._ana_firca_calistir(False)
            await self._yan_fircalari_calistir(False)

    async def _ana_firca_calistir(self, aktif: bool):
        """Ana fırçayı çalıştır/durdur"""
        if self.simulation_mode:
            self.logger.debug(f"🎮 Ana fırça simülasyon: {aktif}")
        else:
            if aktif:
                self.ana_firca_motor.forward(0.8)  # %80 hız
            else:
                self.ana_firca_motor.stop()

    async def _yan_fircalari_calistir(self, aktif: bool):
        """Yan fırçaları çalıştır/durdur"""
        if self.simulation_mode:
            self.logger.debug(f"🎮 Yan fırçalar simülasyon: {aktif}")
        else:
            if aktif:
                self.sol_firca_motor.forward(0.6)  # %60 hız
                self.sag_firca_motor.forward(0.6)  # %60 hız
            else:
                self.sol_firca_motor.stop()
                self.sag_firca_motor.stop()

    async def fan_calistir(self, aktif: bool):
        """🌬️ Fan'ı çalıştır/durdur"""
        self.fan_durumu = aktif

        if self.simulation_mode:
            self.logger.debug(f"🎮 Fan simülasyon: {aktif}")
        else:
            if aktif:
                self.fan_motor.forward(0.7)  # %70 hız
            else:
                self.fan_motor.stop()

        self.logger.info(f"🌬️ Fan {'çalıştırıldı' if aktif else 'durduruldu'}")

    async def durdur(self):
        """🛑 Tüm motorları durdur"""
        self.logger.info("🛑 Tüm motorlar durduruluyor...")

        await self._tekerlek_hizlarini_ayarla(0.0, 0.0)
        await self.fircalari_calistir(False)
        await self.fan_calistir(False)

        self.motorlar_aktif = False
        self.logger.info("✅ Tüm motorlar durduruldu")

    async def acil_durdur(self):
        """🚨 Acil durdurma - hemen durdur"""
        self.logger.warning("🚨 ACİL DURDURMA!")

        if not self.simulation_mode:
            try:
                self.sol_motor.stop()
                self.sag_motor.stop()
                self.ana_firca_motor.stop()
                self.sol_firca_motor.stop()
                self.sag_firca_motor.stop()
                self.fan_motor.stop()
            except Exception as e:
                self.logger.error(f"❌ Acil durdurma hatası: {e}")

        self.motorlar_aktif = False
        self.mevcut_hizlar = {"sol": 0.0, "sag": 0.0}
        self.firca_durumu = {"ana": False, "sol": False, "sag": False}
        self.fan_durumu = False

    async def test_et(self):
        """🧪 Motor test fonksiyonu"""
        self.logger.info("🧪 Motor testleri başlatılıyor...")

        try:
            # İleri hareket testi
            self.logger.info("➡️ İleri hareket testi...")
            await self.hareket_uygula(HareketKomut(linear_hiz=0.1, angular_hiz=0.0, sure=1.0))

            # Geri hareket testi
            self.logger.info("⬅️ Geri hareket testi...")
            await self.hareket_uygula(HareketKomut(linear_hiz=-0.1, angular_hiz=0.0, sure=1.0))

            # Dönme testi
            self.logger.info("🔄 Dönme testi...")
            await self.hareket_uygula(HareketKomut(linear_hiz=0.0, angular_hiz=0.5, sure=1.0))

            # Fırça testi
            self.logger.info("🌪️ Fırça testi...")
            await self.fircalari_calistir(True)
            await asyncio.sleep(2.0)
            await self.fircalari_calistir(False)

            # Fan testi
            self.logger.info("🌬️ Fan testi...")
            await self.fan_calistir(True)
            await asyncio.sleep(2.0)
            await self.fan_calistir(False)

            self.logger.info("✅ Tüm motor testleri başarılı!")
            return True

        except Exception as e:
            self.logger.error(f"❌ Motor test hatası: {e}")
            return False

    def get_enkoder_verileri(self) -> Dict[str, Any]:
        """Enkoder verilerini al"""
        return {
            "sol_enkoder": self.enkoder_sayaclari["sol"],
            "sag_enkoder": self.enkoder_sayaclari["sag"],
            "sol_hiz": self.mevcut_hizlar["sol"],
            "sag_hiz": self.mevcut_hizlar["sag"]
        }

    def enkoder_sifirla(self):
        """Enkoder sayaçlarını sıfırla"""
        self.enkoder_sayaclari = {"sol": 0, "sag": 0}
        self.logger.info("🔄 Enkoder sayaçları sıfırlandı")

    def get_motor_durumu(self) -> Dict[str, Any]:
        """Motor durumu bilgisi"""
        return {
            "aktif": self.motorlar_aktif,
            "hizlar": self.mevcut_hizlar.copy(),
            "enkoder": self.enkoder_sayaclari.copy(),
            "fircalar": self.firca_durumu.copy(),
            "fan": self.fan_durumu,
            "simulasyon": self.simulation_mode
        }

    def __del__(self):
        """Motor kontrolcü kapatılıyor"""
        if hasattr(self, 'logger'):
            self.logger.info("👋 Motor kontrolcü kapatılıyor...")

        # simulation_mode attribute'u varsa ve gerçek modda ise GPIO temizle
        if hasattr(self, 'simulation_mode') and not self.simulation_mode:
            try:
                import RPi.GPIO as GPIO
                GPIO.cleanup()
            except Exception:
                pass
