"""
🎯 Dinamik Engel Kaçınıcı - Dynamic Window Approach (DWA)
Hacı Abi'nin gerçek zamanlı engel kaçınma sistemi!

Bu modül robot'un hareket halindeyken anlık engelleri tespit edip
güvenli rotalar oluşturmak için kullanılır.
"""

import logging
import math
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np

from .rota_planlayici import Nokta


@dataclass
class HareketKomutlari:
    """Robot hareket komutları + akıllı aksesuar kontrolü"""
    dogrusal_hiz: float  # m/s
    acisal_hiz: float    # rad/s
    guvenlik_skoru: float  # 0-1 arası
    aksesuar_komutlari: Optional[Dict[str, bool]] = None  # Akıllı aksesuar kararları


@dataclass
class DinamikEngel:
    """Dinamik engel tanımı"""
    nokta: Nokta
    yaricap: float
    hiz: float = 0.0      # m/s (0 = statik)
    yon: float = 0.0      # radyan
    tespit_zamani: float = 0.0
    guven_seviyesi: float = 1.0  # 0-1 arası


class DinamikEngelKacinici:
    """
    🎯 Dynamic Window Approach (DWA) ile dinamik engel kaçınma

    Bu sınıf robot'un hareket halindeyken anlık engelleri tespit edip
    güvenli hareket komutları üretir.
    """

    def __init__(self, robot_config: Dict):
        self.logger = logging.getLogger("DinamikEngelKacinici")

        # Robot fiziksel parametreleri
        self.max_dogrusal_hiz = robot_config.get("max_linear_speed", 0.5)  # m/s
        self.max_acisal_hiz = robot_config.get("max_angular_speed", 1.0)   # rad/s
        self.max_dogrusal_ivme = robot_config.get("max_linear_accel", 0.5)  # m/s²
        self.max_acisal_ivme = robot_config.get("max_angular_accel", 1.0)   # rad/s²

        # Güvenlik parametreleri
        self.robot_yaricapi = robot_config.get("robot_radius", 0.3)  # 30cm
        self.guvenlik_mesafesi = robot_config.get("safety_distance", 0.5)  # 50cm
        self.on_goruş_mesafesi = robot_config.get("lookahead_distance", 2.0)  # 2m

        # DWA parametreleri
        self.hiz_cozunurlugu = 0.05  # 5cm/s adımlar
        self.acisal_cozunurlugu = 0.1  # 0.1 rad adımlar
        self.zaman_ufku = 2.0  # 2 saniye öngörü
        self.dt = 0.1  # 100ms adımlar

        # Skor ağırlıkları
        self.hedef_agirlik = 1.0      # Hedefe yakınlık
        self.engel_agirlik = 2.0      # Engelden uzaklık
        self.hiz_agirlik = 0.5        # Hız tercih (hızlı=iyi)
        self.yumusak_agirlik = 0.3    # Yumuşak hareket (az dönüş)

        # Engel listesi
        self.dinamik_engeller: List[DinamikEngel] = []
        self.engel_timeout = 5.0  # 5 saniye sonra eski engelleri sil

        self.logger.info("🎯 Dinamik engel kaçınıcı başlatıldı")

    def engel_ekle(self, engel: DinamikEngel):
        """Yeni dinamik engel ekle"""
        engel.tespit_zamani = time.time()
        self.dinamik_engeller.append(engel)
        self.logger.debug(f"🚨 Yeni engel: ({engel.nokta.x:.2f}, {engel.nokta.y:.2f})")

    def engelleri_temizle(self):
        """Eski engelleri temizle"""
        simdi = time.time()
        onceki_sayi = len(self.dinamik_engeller)

        self.dinamik_engeller = [
            engel for engel in self.dinamik_engeller
            if (simdi - engel.tespit_zamani) < self.engel_timeout
        ]

        if len(self.dinamik_engeller) != onceki_sayi:
            self.logger.debug(f"🧹 {onceki_sayi - len(self.dinamik_engeller)} eski engel silindi")

    def en_iyi_hareket_bul(self,
                           mevcut_konum: Nokta,
                           mevcut_hiz: Tuple[float, float],  # (doğrusal, açısal)
                           hedef_nokta: Nokta) -> Optional[HareketKomutlari]:
        """
        🎯 DWA ile en iyi hareket komutlarını bul

        Args:
            mevcut_konum: Robot'un mevcut konumu
            mevcut_hiz: (doğrusal_hız, açısal_hız) tuple'ı
            hedef_nokta: Hedef nokta

        Returns:
            En iyi hareket komutları veya None
        """
        self.engelleri_temizle()

        dogrusal_hiz, acisal_hiz = mevcut_hiz

        # Hız aşımı kontrolü yap
        hiz_kontrol = self.hiz_asimi_kontrol(dogrusal_hiz, acisal_hiz)

        # Acil müdahale gerekiyorsa direkt acil komutları dön
        if hiz_kontrol["acil_mudahale_gerekli"]:
            acil_komutlar = hiz_kontrol["onerilen_komutlar"]
            return HareketKomutlari(
                dogrusal_hiz=acil_komutlar["dogrusal_hiz"],
                acisal_hiz=acil_komutlar["acisal_hiz"],
                guvenlik_skoru=0.1  # Düşük skor - acil durum
            )

        # Dynamic Window hesapla
        hiz_penceresi = self._dynamic_window_hesapla(dogrusal_hiz, acisal_hiz)

        en_iyi_komut = None
        en_iyi_skor = -float('inf')

        # Tüm olası hız kombinasyonlarını test et
        for v in hiz_penceresi['dogrusal']:
            for w in hiz_penceresi['acisal']:
                # Bu hız kombinasyonu güvenli mi?
                if self._hareket_guvenli_mi(mevcut_konum, v, w):
                    skor = self._hareket_skorla(mevcut_konum, v, w, hedef_nokta)

                    if skor > en_iyi_skor:
                        en_iyi_skor = skor
                        en_iyi_komut = HareketKomutlari(
                            dogrusal_hiz=v,
                            acisal_hiz=w,
                            guvenlik_skoru=skor
                        )

        if en_iyi_komut:
            self.logger.debug(f"🎯 En iyi hareket: v={en_iyi_komut.dogrusal_hiz:.2f}, "
                              f"w={en_iyi_komut.acisal_hiz:.2f}, skor={en_iyi_skor:.2f}")
        else:
            self.logger.warning("⚠️ Güvenli hareket bulunamadı - EMERGENCY STOP!")

        return en_iyi_komut

    def _dynamic_window_hesapla(self, mevcut_v: float, mevcut_w: float) -> Dict:
        """Mevcut hıza göre ulaşılabilir hız penceresini hesapla"""

        # İvme sınırlarına göre ulaşılabilir hızlar
        dt = self.dt

        v_min = max(0, mevcut_v - self.max_dogrusal_ivme * dt)
        v_max = min(self.max_dogrusal_hiz, mevcut_v + self.max_dogrusal_ivme * dt)

        w_min = max(-self.max_acisal_hiz, mevcut_w - self.max_acisal_ivme * dt)
        w_max = min(self.max_acisal_hiz, mevcut_w + self.max_acisal_ivme * dt)

        # Debug bilgisi
        self.logger.debug(f"🔧 Hız penceresi: v_min={v_min:.3f}, v_max={v_max:.3f}, dt={dt:.3f}")
        self.logger.debug(f"🔧 Çözünürlük: {self.hiz_cozunurlugu:.3f}")

        # Güvenli hız listelerini oluştur
        if v_max <= v_min:
            # Robot maksimum hızın üzerinde - acil yavaşlatma senaryosu
            if mevcut_v > self.max_dogrusal_hiz:
                self.logger.warning(f"🚨 Robot maksimum hızın üzerinde: {mevcut_v:.3f} > {self.max_dogrusal_hiz:.3f}")
                self.logger.warning(f"⚠️ Doğrusal hız penceresi geçersiz: v_min={v_min:.3f} >= v_max={v_max:.3f}")
                # Acil fren senaryosu: sadece yavaşlama komutları
                yavaslatma_hiz = max(0, mevcut_v - self.max_dogrusal_ivme * dt * 2)  # 2x fren kuvveti
                dogrusal_hizlar = np.array([yavaslatma_hiz, v_max])  # Yavaşlatma seçenekleri
                self.logger.info(f"🛑 Acil yavaşlatma modu: hedef hız={yavaslatma_hiz:.3f} m/s")
            else:
                # Normal dur komutu
                dogrusal_hizlar = np.array([0.0])  # Dur komutu
        else:
            # Normal hız penceresi
            step_count = max(1, int((v_max - v_min) / self.hiz_cozunurlugu))
            dogrusal_hizlar = np.linspace(v_min, v_max, step_count + 1)

        if w_max <= w_min:
            self.logger.warning(f"⚠️ Açısal hız penceresi geçersiz: w_min={w_min:.3f} >= w_max={w_max:.3f}")
            acisal_hizlar = np.array([0.0])  # Düz git komutu
        else:
            # Minimum bir eleman garantisi için step kontrolü
            step_count = max(1, int((w_max - w_min) / self.acisal_cozunurlugu))
            acisal_hizlar = np.linspace(w_min, w_max, step_count + 1)

        self.logger.debug(f"🎯 Pencere boyutları: doğrusal={len(dogrusal_hizlar)}, açısal={len(acisal_hizlar)}")

        return {
            'dogrusal': dogrusal_hizlar,
            'acisal': acisal_hizlar
        }

    def _hareket_guvenli_mi(self, konum: Nokta, v: float, w: float) -> bool:
        """Verilen hız kombinasyonu güvenli mi simüle et"""

        # Robot'un gelecekteki yörüngesini simüle et
        x, y, theta = konum.x, konum.y, 0.0

        for t in np.arange(0, self.zaman_ufku, self.dt):
            # Hareket modeli (diferansiyel tahrik)
            if abs(w) < 1e-6:  # Düz hareket
                x += v * math.cos(theta) * self.dt
                y += v * math.sin(theta) * self.dt
            else:  # Eğrisel hareket
                x += (v / w) * (math.sin(theta + w * self.dt) - math.sin(theta))
                y += (v / w) * (math.cos(theta) - math.cos(theta + w * self.dt))
                theta += w * self.dt

            # Bu noktada engel var mı?
            robot_nokta = Nokta(x, y)
            if self._noktada_engel_var_mi(robot_nokta):
                return False

        return True

    def _noktada_engel_var_mi(self, nokta: Nokta) -> bool:
        """Verilen noktada engel var mı kontrol et"""

        for engel in self.dinamik_engeller:
            mesafe = math.sqrt(
                (nokta.x - engel.nokta.x)**2 +
                (nokta.y - engel.nokta.y)**2
            )

            # Robot yarıçapı + engel yarıçapı + güvenlik mesafesi
            tehlike_mesafesi = self.robot_yaricapi + engel.yaricap + self.guvenlik_mesafesi

            if mesafe < tehlike_mesafesi:
                return True

        return False

    def _hareket_skorla(self, konum: Nokta, v: float, w: float, hedef: Nokta) -> float:
        """Hareket kombinasyonunu skorla"""

        # 1. Hedef odaklılık - hedefe ne kadar yaklaşıyor
        hedef_skor = self._hedef_skoru_hesapla(konum, v, w, hedef)

        # 2. Engel uzaklığı - engellerden ne kadar uzak
        engel_skor = self._engel_skoru_hesapla(konum, v, w)

        # 3. Hız skoru - hızlı hareket tercih edilir
        hiz_skor = v / self.max_dogrusal_hiz

        # 4. Yumuşaklık skoru - ani dönüşler cezalandırılır
        yumusak_skor = 1.0 - abs(w) / self.max_acisal_hiz

        # Toplam skor
        toplam_skor = (
            self.hedef_agirlik * hedef_skor +
            self.engel_agirlik * engel_skor +
            self.hiz_agirlik * hiz_skor +
            self.yumusak_agirlik * yumusak_skor
        )

        return toplam_skor

    def _hedef_skoru_hesapla(self, konum: Nokta, v: float, w: float, hedef: Nokta) -> float:
        """Hedefe yakınlaşma skoru"""

        # Zaman ufkunda robot nerede olacak?
        x, y, theta = konum.x, konum.y, 0.0

        for t in np.arange(0, self.zaman_ufku, self.dt):
            if abs(w) < 1e-6:
                x += v * math.cos(theta) * self.dt
                y += v * math.sin(theta) * self.dt
            else:
                x += (v / w) * (math.sin(theta + w * self.dt) - math.sin(theta))
                y += (v / w) * (math.cos(theta) - math.cos(theta + w * self.dt))
                theta += w * self.dt

        # Hedefe mesafe
        son_mesafe = math.sqrt((x - hedef.x)**2 + (y - hedef.y)**2)
        mevcut_mesafe = math.sqrt((konum.x - hedef.x)**2 + (konum.y - hedef.y)**2)

        # Yaklaşma oranı (pozitif = yaklaşıyor)
        yaklasma = (mevcut_mesafe - son_mesafe) / mevcut_mesafe

        return max(0, yaklasma)

    def _engel_skoru_hesapla(self, konum: Nokta, v: float, w: float) -> float:
        """Engel uzaklık skoru"""

        if not self.dinamik_engeller:
            return 1.0  # Engel yok, maksimum skor

        min_mesafe = float('inf')

        # Robot'un yörüngesini simüle et
        x, y, theta = konum.x, konum.y, 0.0

        for t in np.arange(0, self.zaman_ufku, self.dt):
            if abs(w) < 1e-6:
                x += v * math.cos(theta) * self.dt
                y += v * math.sin(theta) * self.dt
            else:
                x += (v / w) * (math.sin(theta + w * self.dt) - math.sin(theta))
                y += (v / w) * (math.cos(theta) - math.cos(theta + w * self.dt))
                theta += w * self.dt

            # Bu noktadaki en yakın engel mesafesi
            robot_nokta = Nokta(x, y)
            for engel in self.dinamik_engeller:
                mesafe = math.sqrt(
                    (robot_nokta.x - engel.nokta.x)**2 +
                    (robot_nokta.y - engel.nokta.y)**2
                )
                mesafe -= (self.robot_yaricapi + engel.yaricap)  # Net mesafe
                min_mesafe = min(min_mesafe, mesafe)

        # Mesafeyi normalize et (0-1 arası)
        if min_mesafe <= 0:
            return 0.0  # Çarpışma riski
        elif min_mesafe >= self.on_goruş_mesafesi:
            return 1.0  # Güvenli mesafe
        else:
            return min_mesafe / self.on_goruş_mesafesi

    def engel_durumu_raporu(self) -> Dict:
        """Mevcut engel durumu raporu"""
        self.engelleri_temizle()

        return {
            "toplam_engel": len(self.dinamik_engeller),
            "engeller": [
                {
                    "konum": (engel.nokta.x, engel.nokta.y),
                    "yaricap": engel.yaricap,
                    "hiz": engel.hiz,
                    "yas": time.time() - engel.tespit_zamani
                }
                for engel in self.dinamik_engeller
            ]
        }

    def acil_fren_gerekli_mi(self, mevcut_konum: Nokta, mevcut_hiz: float) -> bool:
        """Acil fren gerekli mi kontrol et"""

        # Durma mesafesi hesapla
        durma_mesafesi = (mevcut_hiz ** 2) / (2 * self.max_dogrusal_ivme)

        # Bu mesafe içinde engel var mı?
        for engel in self.dinamik_engeller:
            mesafe = math.sqrt(
                (mevcut_konum.x - engel.nokta.x)**2 +
                (mevcut_konum.y - engel.nokta.y)**2
            )

            tehlike_mesafesi = self.robot_yaricapi + engel.yaricap + self.guvenlik_mesafesi

            if mesafe - tehlike_mesafesi <= durma_mesafesi:
                self.logger.warning(f"🚨 ACİL FREN! Engel {mesafe:.2f}m mesafede")
                return True

        return False

    def hiz_asimi_kontrol(self, mevcut_dogrusal_hiz: float, mevcut_acisal_hiz: float) -> Dict:
        """
        🚨 Robot'un hız sınırlarını aşıp aşmadığını kontrol et

        Returns:
            Dict: kontrol sonuçları ve acil müdahale bilgileri
        """
        hiz_asimi_durumu = {
            "dogrusal_asim": False,
            "acisal_asim": False,
            "acil_mudahale_gerekli": False,
            "onerilen_komutlar": {}
        }

        # Doğrusal hız kontrolü
        if mevcut_dogrusal_hiz > self.max_dogrusal_hiz:
            hiz_asimi_durumu["dogrusal_asim"] = True
            asim_orani = (mevcut_dogrusal_hiz - self.max_dogrusal_hiz) / self.max_dogrusal_hiz

            if asim_orani > 0.3:  # %30'dan fazla aşım
                hiz_asimi_durumu["acil_mudahale_gerekli"] = True
                self.logger.error(f"🚨 KRİTİK HIZ AŞIMI: {mevcut_dogrusal_hiz:.3f} m/s "
                                  f"(%{asim_orani*100:.1f} aşım)")
            else:
                self.logger.warning(f"⚠️ Doğrusal hız aşımı: {mevcut_dogrusal_hiz:.3f} m/s "
                                    f"(limit: {self.max_dogrusal_hiz:.3f})")

        # Açısal hız kontrolü
        if abs(mevcut_acisal_hiz) > self.max_acisal_hiz:
            hiz_asimi_durumu["acisal_asim"] = True
            asim_orani = (abs(mevcut_acisal_hiz) - self.max_acisal_hiz) / self.max_acisal_hiz

            if asim_orani > 0.3:  # %30'dan fazla aşım
                hiz_asimi_durumu["acil_mudahale_gerekli"] = True
                self.logger.error(f"🚨 KRİTİK AÇISAL HIZ AŞIMI: {abs(mevcut_acisal_hiz):.3f} rad/s "
                                  f"(%{asim_orani*100:.1f} aşım)")
            else:
                self.logger.warning(f"⚠️ Açısal hız aşımı: {abs(mevcut_acisal_hiz):.3f} rad/s "
                                    f"(limit: {self.max_acisal_hiz:.3f})")

        # Acil müdahale komutları üret
        if hiz_asimi_durumu["acil_mudahale_gerekli"]:
            # Acil fren komutları
            acil_dogrusal = max(0, mevcut_dogrusal_hiz - self.max_dogrusal_ivme * self.dt * 3)
            acil_acisal = mevcut_acisal_hiz * 0.5  # %50 azalt

            hiz_asimi_durumu["onerilen_komutlar"] = {
                "dogrusal_hiz": acil_dogrusal,
                "acisal_hiz": acil_acisal,
                "acil_fren": True
            }

            self.logger.critical(f"🛑 ACİL FREN KOMUTLARI: "
                                 f"v={acil_dogrusal:.3f}, w={acil_acisal:.3f}")

        return hiz_asimi_durumu
