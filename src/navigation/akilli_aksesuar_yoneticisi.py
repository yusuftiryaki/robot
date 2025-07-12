"""
🔧 Akıllı Aksesuar Yöneticisi - Robot'un Beyni!
Hacı Abi'nin çok faktörlü aksesuar karar sistemi!

Bu modül robot'un aksesuarlarını (fırçalar, fan) akıllıca yönetir:
- Görev odaklı karar verme
- Hız, engel, batarya, konum analizleri
- Enerji optimizasyonu
- Güvenlik önceliği
"""

import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional

from .rota_planlayici import Nokta


class GorevTipi(Enum):
    """Görev tipi enum'u"""
    BEKLEME = "bekleme"
    BICME = "mowing"
    SARJ_ARAMA = "charging"
    SARJ_OLMA = "docked"
    NOKTA_ARASI = "point_to_point"
    ACIL_DURUM = "emergency"


class AksesuarPolitikasi(Enum):
    """Aksesuar politika enum'u"""
    PERFORMANS = "performans"  # Maksimum temizlik
    TASARRUF = "tasarruf"     # Enerji tasarrufu
    SESSIZ = "sessiz"         # Gürültü minimizasyonu
    GUVENLIK = "guvenlik"     # Güvenlik odaklı


@dataclass
class RobotDurumVerisi:
    """Robot'un mevcut durumu - aksesuar kararı için gerekli"""
    gorev_tipi: GorevTipi
    robot_hizi: float  # m/s
    mevcut_konum: Nokta
    hedef_konum: Optional[Nokta]

    # Engel durumu
    engel_tespit_edildi: bool
    en_yakin_engel_mesafesi: float  # metre

    # Batarya durumu
    batarya_seviyesi: int  # 0-100%
    sarj_gerekli: bool

    # Konum durumu
    bahce_sinir_mesafesi: float  # metre
    zorlu_arazide: bool

    # Çevresel faktörler
    hiz_limit_aktif: bool
    manuel_kontrol_aktif: bool


class AkilliAksesuarYoneticisi:
    """
    🧠 Akıllı Aksesuar Yöneticisi

    Robot'un aksesuarlarını (fırçalar, fan) akıllıca yönetir.
    Tüm faktörleri analiz ederek optimum aksesuar konfigürasyonu belirler.
    """

    def __init__(self, aksesuar_config: Dict):
        self.logger = logging.getLogger("AkilliAksesuarYoneticisi")
        self.config = aksesuar_config

        # Varsayılan politika
        self.mevcut_politika = AksesuarPolitikasi.PERFORMANS

        # Karar parametreleri
        self.min_bicme_hizi = self.config.get("min_bicme_hizi", 0.1)  # m/s
        self.max_yan_firca_hizi = self.config.get("max_yan_firca_hizi", 0.3)  # m/s
        self.kritik_batarya_seviyesi = self.config.get("kritik_batarya", 20)  # %
        self.dusuk_batarya_seviyesi = self.config.get("dusuk_batarya", 40)  # %
        self.guvenli_engel_mesafesi = self.config.get("guvenli_engel_mesafesi", 0.5)  # metre
        self.sinir_guvenlik_mesafesi = self.config.get("sinir_guvenlik_mesafesi", 1.0)  # metre

        # Performance tracking
        self.karar_sayisi = 0
        self.son_karar_zamani = 0.0
        self.enerji_tasarruf_modu_aktif = False

        self.logger.info("🧠 Akıllı aksesuar yöneticisi başlatıldı")

    def aksesuar_karari_ver(self, robot_durum: RobotDurumVerisi) -> Dict[str, bool]:
        """
        🎯 Ana karar verme fonksiyonu

        Tüm faktörleri analiz ederek akıllı aksesuar kararı verir.

        Args:
            robot_durum: Robot'un mevcut durumu

        Returns:
            Dict[str, bool]: Aksesuar komutları
                - "ana_firca": Ana fırça durumu
                - "yan_firca": Yan fırçalar durumu
                - "fan": Fan durumu
        """
        self.karar_sayisi += 1
        self.son_karar_zamani = time.time()

        try:
            # 1. Acil durumları kontrol et
            if self._acil_durum_kontrolu(robot_durum):
                return self._acil_durum_konfigurasyonu()

            # 2. Görev odaklı temel karar
            temel_karar = self._gorev_odakli_karar(robot_durum)

            # 3. Güvenlik faktörleri
            guvenlik_karar = self._guvenlik_analizli_karar(robot_durum, temel_karar)

            # 4. Performans optimizasyonu
            optimized_karar = self._performans_optimizasyonu(robot_durum, guvenlik_karar)

            # 5. Enerji yönetimi
            final_karar = self._enerji_yonetimi(robot_durum, optimized_karar)

            # Debug log
            self.logger.debug(f"🎯 Aksesuar kararı: {final_karar}")
            self.logger.debug(f"📊 Faktörler: Görev={robot_durum.gorev_tipi.value}, "
                              f"Hız={robot_durum.robot_hizi:.2f}, "
                              f"Batarya={robot_durum.batarya_seviyesi}%, "
                              f"Engel={robot_durum.en_yakin_engel_mesafesi:.2f}m")

            return final_karar

        except Exception as e:
            self.logger.error(f"❌ Aksesuar karar hatası: {e}")
            # Güvenli varsayılan
            return {"ana_firca": False, "yan_firca": False, "fan": False}

    def _acil_durum_kontrolu(self, durum: RobotDurumVerisi) -> bool:
        """🚨 Acil durum kontrolü"""

        # Görev acil durum
        if durum.gorev_tipi == GorevTipi.ACIL_DURUM:
            return True

        # Çok yakın engel
        if durum.engel_tespit_edildi and durum.en_yakin_engel_mesafesi < 0.2:
            return True

        # Kritik batarya (config'den alınan değer)
        if durum.batarya_seviyesi <= self.kritik_batarya_seviyesi:
            return True

        # Manuel kontrol aktif
        if durum.manuel_kontrol_aktif:
            return True

        return False

    def _acil_durum_konfigurasyonu(self) -> Dict[str, bool]:
        """🚨 Acil durum aksesuar konfigürasyonu"""
        self.logger.warning("🚨 Acil durum - tüm aksesuarlar kapatılıyor")
        return {"ana_firca": False, "yan_firca": False, "fan": False}

    def _gorev_odakli_karar(self, durum: RobotDurumVerisi) -> Dict[str, bool]:
        """🎯 Görev odaklı temel aksesuar kararı"""

        if durum.gorev_tipi == GorevTipi.BICME:
            # Biçme görevi - tam aksesuar aktif
            return {"ana_firca": True, "yan_firca": True, "fan": True}

        elif durum.gorev_tipi == GorevTipi.SARJ_ARAMA:
            # Şarj arama - sadece hareket, temizlik yok
            return {"ana_firca": False, "yan_firca": False, "fan": False}

        elif durum.gorev_tipi == GorevTipi.SARJ_OLMA:
            # Şarj oluyor - hiçbir aksesuar
            return {"ana_firca": False, "yan_firca": False, "fan": False}

        elif durum.gorev_tipi == GorevTipi.NOKTA_ARASI:
            # Nokta arası hareket - seçmeli temizlik
            return {"ana_firca": True, "yan_firca": False, "fan": False}

        elif durum.gorev_tipi == GorevTipi.BEKLEME:
            # Bekleme - hiçbir aksesuar
            return {"ana_firca": False, "yan_firca": False, "fan": False}

        else:
            # Bilinmeyen görev - güvenli varsayılan
            return {"ana_firca": False, "yan_firca": False, "fan": False}

    def _guvenlik_analizli_karar(self, durum: RobotDurumVerisi, temel_karar: Dict[str, bool]) -> Dict[str, bool]:
        """🛡️ Güvenlik faktörleri ile karar düzenleme"""

        karar = temel_karar.copy()

        # Engel yakınında güvenlik önlemleri
        if durum.engel_tespit_edildi and durum.en_yakin_engel_mesafesi < self.guvenli_engel_mesafesi:
            self.logger.debug(f"🛡️ Engel güvenliği: {durum.en_yakin_engel_mesafesi:.2f}m - yan fırçalar kapatıldı")
            karar["yan_firca"] = False  # Yan fırçalar zararlı olabilir

            # Çok yakın engel - ana fırçayı da kapat
            if durum.en_yakin_engel_mesafesi < 0.35:  # 0.3 -> 0.35 daha toleranslı
                karar["ana_firca"] = False
                self.logger.debug("🛡️ Çok yakın engel - ana fırça da kapatıldı")

        # Bahçe sınırı yakınında
        if durum.bahce_sinir_mesafesi < self.sinir_guvenlik_mesafesi:
            karar["yan_firca"] = False  # Sınır yakınında yan fırça riskli
            self.logger.debug(f"🛡️ Sınır güvenliği: {durum.bahce_sinir_mesafesi:.2f}m - yan fırçalar kapatıldı")

        # Zorlu arazi
        if durum.zorlu_arazide:
            karar["yan_firca"] = False  # Zorlu arazide dikkat
            self.logger.debug("🛡️ Zorlu arazi - yan fırçalar kapatıldı")

        # Hızlı hareket
        if durum.robot_hizi > self.max_yan_firca_hizi:
            karar["yan_firca"] = False  # Hızda yan fırça tehlikeli
            self.logger.debug(f"🛡️ Yüksek hız: {durum.robot_hizi:.2f}m/s - yan fırçalar kapatıldı")

        return karar

    def _performans_optimizasyonu(self, durum: RobotDurumVerisi, guvenlik_karar: Dict[str, bool]) -> Dict[str, bool]:
        """⚡ Performans optimizasyonu"""

        karar = guvenlik_karar.copy()

        # Politikaya göre optimizasyon
        if self.mevcut_politika == AksesuarPolitikasi.PERFORMANS:
            # Performans modu - mümkün olduğunca aktif
            if durum.gorev_tipi == GorevTipi.BICME and durum.robot_hizi >= self.min_bicme_hizi:
                # Yeterli hızda - fan'ı aktifleştir
                karar["fan"] = True

        elif self.mevcut_politika == AksesuarPolitikasi.SESSIZ:
            # Sessiz mod - fan'ı kapat
            karar["fan"] = False
            self.logger.debug("🔇 Sessiz mod - fan kapatıldı")

        elif self.mevcut_politika == AksesuarPolitikasi.GUVENLIK:
            # Güvenlik modu - konservatif yaklaşım
            if durum.robot_hizi > 0.2:  # Orta hızın üstünde
                karar["yan_firca"] = False

        # Düşük hızda aksesuar optimizasyonu
        if durum.robot_hizi < self.min_bicme_hizi:
            # Çok yavaş - yan fırçalar etkisiz, kapat
            karar["yan_firca"] = False
            self.logger.debug(f"⚡ Düşük hız: {durum.robot_hizi:.2f}m/s - yan fırçalar etkisiz")

        return karar

    def _enerji_yonetimi(self, durum: RobotDurumVerisi, performans_karar: Dict[str, bool]) -> Dict[str, bool]:
        """🔋 Enerji yönetimi ve optimizasyon"""

        karar = performans_karar.copy()

        # Kritik batarya seviyesi
        if durum.batarya_seviyesi <= self.kritik_batarya_seviyesi:
            # Sadece ana fırça, diğerleri kapat
            karar["yan_firca"] = False
            karar["fan"] = False
            self.enerji_tasarruf_modu_aktif = True
            self.logger.warning(f"🔋 Kritik batarya: {durum.batarya_seviyesi}% - enerji tasarrufu modu")

        elif durum.batarya_seviyesi <= self.dusuk_batarya_seviyesi:
            # Düşük batarya - fan'ı kapat
            karar["fan"] = False
            self.logger.debug(f"🔋 Düşük batarya: {durum.batarya_seviyesi}% - fan kapatıldı")

        # Şarj gerekli durumu
        if durum.sarj_gerekli:
            # Şarj gerekli - minimum enerji kullan
            karar["yan_firca"] = False
            karar["fan"] = False
            self.logger.debug("🔋 Şarj gerekli - aksesuar kullanımı minimal")

        # Enerji tasarruf modu reset
        if durum.batarya_seviyesi > self.dusuk_batarya_seviyesi:
            self.enerji_tasarruf_modu_aktif = False

        return karar

    def politika_degistir(self, yeni_politika: AksesuarPolitikasi):
        """🎛️ Aksesuar politikasını değiştir"""
        self.mevcut_politika = yeni_politika
        self.logger.info(f"🎛️ Aksesuar politikası değişti: {yeni_politika.value}")

    def durum_raporu(self) -> Dict:
        """📊 Aksesuar yöneticisi durum raporu"""
        return {
            "mevcut_politika": self.mevcut_politika.value,
            "enerji_tasarruf_aktif": self.enerji_tasarruf_modu_aktif,
            "toplam_karar_sayisi": self.karar_sayisi,
            "son_karar_zamani": self.son_karar_zamani,
            "parametreler": {
                "min_bicme_hizi": self.min_bicme_hizi,
                "max_yan_firca_hizi": self.max_yan_firca_hizi,
                "kritik_batarya": self.kritik_batarya_seviyesi,
                "dusuk_batarya": self.dusuk_batarya_seviyesi
            }
        }

    def konfigurasyonu_guncelle(self, yeni_config: Dict):
        """⚙️ Konfigürasyonu çalışma zamanında güncelle"""
        self.config.update(yeni_config)

        # Parametreleri yenile
        self.min_bicme_hizi = self.config.get("min_bicme_hizi", 0.1)
        self.max_yan_firca_hizi = self.config.get("max_yan_firca_hizi", 0.3)
        self.kritik_batarya_seviyesi = self.config.get("kritik_batarya", 20)
        self.dusuk_batarya_seviyesi = self.config.get("dusuk_batarya", 40)

        self.logger.info("⚙️ Aksesuar yöneticisi konfigürasyonu güncellendi")
