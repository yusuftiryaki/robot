"""
⚙️ Motor Kontrolcüsü - Robot'un Kasları
Hacı Abi'nin HAL pattern kullanarak temizlenmiş motor kontrolü!

Bu sınıf HAL (Hardware Abstraction Layer) kullanarak robot'un motorlarını kontrol eder:
- HAL pattern ile temiz mimari
- Simülasyon/gerçek mod ayrımı HAL katmanında
- SOLID prensiplerine uygun tasarım
- Enkoder feedback ve kinematik hesaplamalar
"""

import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Tuple

from .hal.interfaces import MotorDurumuVeri, MotorInterface


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
    ⚙️ Ana Motor Kontrolcüsü - HAL Pattern

    HAL (Hardware Abstraction Layer) kullanarak robot'un tüm motorlarını kontrol eder.
    Simülasyon/gerçek mod ayrımı HAL katmanında yapılır.
    """

    def __init__(self, motor_hal: MotorInterface, motor_config: Dict[str, Any]):
        """
        MotorKontrolcu sınıfının başlatıcısı.

        Args:
            motor_hal (MotorInterface): Motor HAL implementasyonu (gerçek veya simülasyon)
            motor_config (Dict[str, Any]): Motor ayarlarını içeren konfigürasyon.
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.motor_hal = motor_hal
        self.config = motor_config

        # Motor fizik parametreleri
        self.tekerlek_capi = self.config.get("wheel_diameter", 0.065)  # metre
        self.tekerlek_base = self.config.get("wheel_base", 0.235)  # metre
        self.enkoder_pulse_per_rev = self.config.get("encoder_pulses_per_rev", 360)
        self.max_hiz = self.config.get("max_linear_speed", 0.5)  # m/s

        # Log throttle mekanizması - spam önleme
        self.log_throttle_interval = 5.0  # saniye
        self.last_log_times = {
            "hareket": 0.0,
            "firca": 0.0,
            "aksesuar": 0.0
        }

        self.logger.info(f"⚙️ Motor kontrolcü başlatıldı (HAL: {type(motor_hal).__name__})")

    async def baslat(self) -> bool:
        """Motor sistemini başlat"""
        try:
            success = await self.motor_hal.baslat()
            if success:
                self.logger.info("✅ Motor kontrolcü başarıyla başlatıldı")
            else:
                self.logger.error("❌ Motor kontrolcü başlatılamadı")
            return success
        except Exception as e:
            self.logger.error(f"Motor kontrolcü başlatma hatası: {e}")
            return False

    async def hareket_et(self, linear_hiz: float, angular_hiz: float):
        """
        Robotu belirtilen lineer ve angular hızda hareket ettirir.

        Args:
            linear_hiz (float): Lineer hız (m/s)
            angular_hiz (float): Angular hız (rad/s)
        """
        try:
            # Kinematik hesaplama
            sol_hiz_ms, sag_hiz_ms = self._inverse_kinematics(linear_hiz, angular_hiz)

            # Hızları normalize et (-1.0 ile 1.0 arasına)
            sol_guc = sol_hiz_ms / self.max_hiz
            sag_guc = sag_hiz_ms / self.max_hiz

            # Güvenlik sınırları
            sol_guc = max(-1.0, min(1.0, sol_guc))
            sag_guc = max(-1.0, min(1.0, sag_guc))

            # HAL'e gönder
            await self.motor_hal.tekerlek_hiz_ayarla(sol_guc, sag_guc)

            # Throttled logging
            if self._should_log("hareket"):
                self.logger.debug(f"Hareket: Linear={linear_hiz:.2f} m/s, Angular={angular_hiz:.2f} rad/s")
                self.logger.debug(f"Tekerlek güçleri: Sol={sol_guc:.2f}, Sağ={sag_guc:.2f}")

        except Exception as e:
            self.logger.error(f"Hareket komutu hatası: {e}")

    async def acil_durdur(self):
        """
        🚨 Tüm motorları anında durdurur.
        """
        try:
            self.logger.critical("🚨 ACİL DURDURMA! Tüm motorlar durduruluyor.")
            await self.motor_hal.acil_durdur()
            self.logger.info("✅ Tüm motorlar güvenli bir şekilde durduruldu.")
        except Exception as e:
            self.logger.error(f"Acil durdurma hatası: {e}")

    async def firca_kontrol(self, ana: bool | None = None, sol: bool | None = None, sag: bool | None = None):
        """
        Fırça motorlarını kontrol eder.

        Args:
            ana (bool, optional): Ana fırça durumu
            sol (bool, optional): Sol fırça durumu
            sag (bool, optional): Sağ fırça durumu
        """
        try:
            # Mevcut durumu al
            current_state = self.motor_hal.motor_durumu_al()

            # None değerleri mevcut durumla doldur
            ana = ana if ana is not None else current_state.ana_firca
            sol = sol if sol is not None else current_state.sol_firca
            sag = sag if sag is not None else current_state.sag_firca

            await self.motor_hal.firca_kontrol(ana, sol, sag)

            if self._should_log("firca"):
                self.logger.info(f"Fırça durumları: Ana={ana}, Sol={sol}, Sağ={sag}")

        except Exception as e:
            self.logger.error(f"Fırça kontrol hatası: {e}")

    async def fan_kontrol(self, aktif: bool):
        """Fan motorunu kontrol eder."""
        try:
            await self.motor_hal.fan_kontrol(aktif)
            self.logger.info(f"Fan {'açıldı' if aktif else 'kapandı'}")
        except Exception as e:
            self.logger.error(f"Fan kontrol hatası: {e}")

    async def aksesuarlari_kontrol_et(self, aksesuar_komutlari: Dict[str, bool]):
        """
        AI karar verici'den gelen aksesuar komutlarını uygula.

        Args:
            aksesuar_komutlari (Dict[str, bool]): Aksesuar komutları
                - "ana_firca": Ana fırça durumu
                - "yan_firca": Yan fırçalar durumu (sol ve sağ)
                - "fan": Fan durumu
        """
        try:
            # Ana fırça kontrolü
            if "ana_firca" in aksesuar_komutlari:
                ana_firca = aksesuar_komutlari["ana_firca"]
                # Yan fırça kontrolü - tek parametre ile her ikisini kontrol et
                yan_firca = aksesuar_komutlari.get("yan_firca", False)

                await self.firca_kontrol(ana=ana_firca, sol=yan_firca, sag=yan_firca)

            # Fan kontrolü
            if "fan" in aksesuar_komutlari:
                fan_aktif = aksesuar_komutlari["fan"]
                await self.fan_kontrol(fan_aktif)

            # Debug log
            if self._should_log("aksesuar"):
                aktif_aksesuarlar = [k for k, v in aksesuar_komutlari.items() if v]
                if aktif_aksesuarlar:
                    self.logger.debug(f"Aktif aksesuarlar: {', '.join(aktif_aksesuarlar)}")
                else:
                    self.logger.debug("Tüm aksesuarlar kapalı")

        except Exception as e:
            self.logger.error(f"Aksesuar kontrol hatası: {e}")

    def motor_durumu_al(self) -> MotorDurumuVeri:
        """Mevcut motor durumunu al"""
        motor_durumu = self.motor_hal.motor_durumu_al()
        motor_durumu.dogrusal_hiz, motor_durumu.acisal_hiz = self.mevcut_hiz_hesapla()
        motor_durumu.saglikli = self.motor_hal.saglikli_mi()
        self.logger.debug(f"Motor durumu alındı: {motor_durumu}")
        return motor_durumu

    def saglikli_mi(self) -> bool:
        """Motor sistemi sağlıklı mı?"""
        return self.motor_hal.saglikli_mi()

    def _inverse_kinematics(self, linear_hiz: float, angular_hiz: float) -> tuple[float, float]:
        """
        Verilen lineer ve angular hızdan tekerlek hızlarını hesaplar.

        Args:
            linear_hiz (float): Lineer hız (m/s)
            angular_hiz (float): Angular hız (rad/s)

        Returns:
            tuple[float, float]: (sol_tekerlek_hiz, sag_tekerlek_hiz) m/s cinsinden
        """
        # Diferansiyel sürüş kinematiği
        # v_left = v - (w * L / 2)
        # v_right = v + (w * L / 2)
        L = self.tekerlek_base

        v_sol = linear_hiz - (angular_hiz * L / 2.0)
        v_sag = linear_hiz + (angular_hiz * L / 2.0)

        return v_sol, v_sag

    def mevcut_hiz_hesapla(self) -> Tuple[float, float]:
        """
        🚀 Robot'un mevcut doğrusal ve açısal hızını hesapla

        Encoder verileri ve motor komutlarını kullanarak gerçek hızları hesaplar.
        Bu DWA algoritması için kritik!

        Returns:
            Tuple[float, float]: (doğrusal_hız_m/s, açısal_hız_rad/s)
        """
        try:
            if not self.motor_hal:
                self.logger.warning("⚠️ Motor HAL mevcut değil, hız hesaplanamıyor")
                return (0.0, 0.0)

            # Motor durumunu al
            motor_durum = self.motor_hal.motor_durumu_al()

            # Motor güçlerini m/s'ye çevir (-1.0/1.0 → gerçek hız)
            sol_hiz_ms = motor_durum.sol_hiz * self.max_hiz  # m/s
            sag_hiz_ms = motor_durum.sag_hiz * self.max_hiz  # m/s

            # Forward kinematics - tekerlek hızlarından robot hızlarına
            dogrusal_hiz, acisal_hiz = self._forward_kinematics(sol_hiz_ms, sag_hiz_ms)

            # Debug için throttled logging
            if self._should_log("hiz_hesaplama"):
                self.logger.debug(f"🚀 Mevcut hızlar: linear={dogrusal_hiz:.3f} m/s, "
                                  f"angular={acisal_hiz:.3f} rad/s")
                self.logger.debug(f"   Tekerlek hızları: sol={sol_hiz_ms:.3f}, sağ={sag_hiz_ms:.3f}")

            return (dogrusal_hiz, acisal_hiz)

        except Exception as e:
            self.logger.error(f"❌ Hız hesaplama hatası: {e}")
            return (0.0, 0.0)

    def _forward_kinematics(self, sol_hiz_ms: float, sag_hiz_ms: float) -> Tuple[float, float]:
        """
        🔄 Forward Kinematics - Tekerlek hızlarından robot hızlarına

        Args:
            sol_hiz_ms: Sol tekerlek hızı (m/s)
            sag_hiz_ms: Sağ tekerlek hızı (m/s)

        Returns:
            Tuple[float, float]: (doğrusal_hız, açısal_hız)
        """
        # Diferansiyel sürüş forward kinematiği
        # v = (v_left + v_right) / 2
        # w = (v_right - v_left) / L

        dogrusal_hiz = (sol_hiz_ms + sag_hiz_ms) / 2.0
        acisal_hiz = (sag_hiz_ms - sol_hiz_ms) / self.tekerlek_base

        return (dogrusal_hiz, acisal_hiz)

    def _should_log(self, key: str) -> bool:
        """Log spam'ini önlemek için kullanılır."""
        current_time = time.time()
        if current_time - self.last_log_times.get(key, 0) > self.log_throttle_interval:
            self.last_log_times[key] = current_time
            return True
        return False

    async def temizle(self):
        """Motor kontrolcüyü temizler ve kaynakları serbest bırakır."""
        try:
            self.logger.info("Motor kontrolcü temizleniyor...")
            await self.motor_hal.durdur()
            self.logger.info("✅ Motor kontrolcü başarıyla temizlendi.")
        except Exception as e:
            self.logger.error(f"Motor kontrolcü temizleme hatası: {e}")

    def __del__(self):
        """Destructor - async olmayan temizlik için"""
        try:
            # Sync cleanup attempt
            if hasattr(self, 'motor_hal') and hasattr(self.motor_hal, 'motor_durumu_al'):
                # HAL hala aktifse acil durdur
                pass  # Async fonksiyon çağıramayız destructor'da
        except Exception:
            pass  # Destructor'da hata görmezden gel
