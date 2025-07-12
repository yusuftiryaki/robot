"""
🌱 Bahçe Sınır Kontrol Sistemi
Hacı Abi'nin güvenli biçme çözümü!

Bu modül robotun belirlenen bahçe sınırları içinde kalmasını sağlar.
GPS koordinatlarına dayalı geometrik kontrol yapar.
"""

import logging
import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


@dataclass
class KoordinatNoktasi:
    """GPS koordinat noktası"""
    latitude: float
    longitude: float

    def __str__(self) -> str:
        return f"({self.latitude:.6f}, {self.longitude:.6f})"


@dataclass
class SinirKontrolSonucu:
    """Sınır kontrol sonucu"""
    guvenli_bolgede: bool  # Robot güvenli bölgede mi?
    sinira_mesafe: float  # Sınıra en yakın mesafe (metre)
    en_yakin_sinir_noktasi: KoordinatNoktasi  # En yakın sınır noktası
    uyari_seviyesi: str  # "güvenli", "uyarı", "tehlike"
    onerilenen_yon: Optional[float]  # Güvenli yön (radyan)
    aciklama: str  # Durum açıklaması


class BahceSinirKontrol:
    """
    🏡 Bahçe Sınır Kontrol Sistemi

    Robot'un belirlenen bahçe sınırları içinde kalmasını sağlar.
    Point-in-polygon algoritması ve mesafe hesaplamaları kullanır.
    """

    def __init__(self, sinir_config: Dict[str, Any]):
        self.logger = logging.getLogger("BahceSinirKontrol")
        self.config = sinir_config

        # Sınır koordinatları
        self.sinir_noktalari = self._sinir_koordinatlarini_yukle()

        # Güvenlik parametreleri
        guvenlik_config = sinir_config.get("boundary_safety", {})
        self.buffer_distance = guvenlik_config.get("buffer_distance", 1.0)
        self.warning_distance = guvenlik_config.get("warning_distance", 2.0)
        self.max_deviation = guvenlik_config.get("max_deviation", 0.5)
        self.check_frequency = guvenlik_config.get("check_frequency", 10)

        # İstatistikler
        self.toplam_kontrol_sayisi = 0
        self.sinir_ihlali_sayisi = 0
        self.son_kontrol_zamani = 0

        self.logger.info("🏡 Bahçe sınır kontrol sistemi başlatıldı")
        self.logger.info(f"📍 Sınır noktaları: {len(self.sinir_noktalari)} nokta")
        self.logger.info(f"🛡️ Güvenlik buffer: {self.buffer_distance}m")
        self.logger.info(f"⚠️ Uyarı mesafesi: {self.warning_distance}m")

        # Bahçe alanını hesapla
        self.bahce_alani = self._polygon_alanini_hesapla()
        self.logger.info(f"🌱 Bahçe alanı: {self.bahce_alani:.2f} m²")

    def _sinir_koordinatlarini_yukle(self) -> List[KoordinatNoktasi]:
        """Konfigürasyondan sınır koordinatlarını yükle"""
        koordinatlar = []

        boundary_coords = self.config.get("boundary_coordinates", [])
        if not boundary_coords:
            self.logger.error("❌ Bahçe sınır koordinatları bulunamadı!")
            return []

        for coord in boundary_coords:
            nokta = KoordinatNoktasi(
                latitude=coord["latitude"],
                longitude=coord["longitude"]
            )
            koordinatlar.append(nokta)
            self.logger.debug(f"📍 Sınır noktası: {nokta}")

        return koordinatlar

    def _polygon_alanini_hesapla(self) -> float:
        """Polygon alanını hesapla (Shoelace formula)"""
        if len(self.sinir_noktalari) < 3:
            return 0.0

        # GPS koordinatlarını metre cinsine çevir (yaklaşık)
        metre_noktalari = []
        ref_lat = self.sinir_noktalari[0].latitude
        ref_lon = self.sinir_noktalari[0].longitude

        for nokta in self.sinir_noktalari:
            x = self._haversine_mesafe(ref_lat, ref_lon, ref_lat, nokta.longitude)
            y = self._haversine_mesafe(ref_lat, ref_lon, nokta.latitude, ref_lon)
            metre_noktalari.append((x, y))

        # Shoelace formula
        alan = 0.0
        n = len(metre_noktalari)
        for i in range(n):
            j = (i + 1) % n
            alan += metre_noktalari[i][0] * metre_noktalari[j][1]
            alan -= metre_noktalari[j][0] * metre_noktalari[i][1]

        return abs(alan) / 2.0

    def robot_konumunu_kontrol_et(self, mevcut_lat: float, mevcut_lon: float) -> SinirKontrolSonucu:
        """
        🎯 Robot konumunu kontrol et

        Args:
            mevcut_lat: Mevcut GPS latitude
            mevcut_lon: Mevcut GPS longitude

        Returns:
            SinirKontrolSonucu: Kontrol sonucu
        """
        self.toplam_kontrol_sayisi += 1
        mevcut_konum = KoordinatNoktasi(mevcut_lat, mevcut_lon)

        # Point-in-polygon kontrolü
        polygon_icinde = self._nokta_polygon_icinde_mi(mevcut_konum)

        # Sınıra en yakın mesafe
        en_yakin_mesafe, en_yakin_nokta = self._en_yakin_sinir_noktasini_bul(mevcut_konum)

        # Güvenlik seviyesi belirleme
        if not polygon_icinde:
            # Sınır dışında!
            uyari_seviyesi = "tehlike"
            guvenli_bolgede = False
            aciklama = "🚨 SINIR DIŞINDA! Geri dönülüyor..."
            self.sinir_ihlali_sayisi += 1

        elif en_yakin_mesafe <= self.buffer_distance:
            # Buffer zone içinde
            uyari_seviyesi = "tehlike"
            guvenli_bolgede = False
            aciklama = f"⚠️ Sınıra çok yakın! ({en_yakin_mesafe:.1f}m)"

        elif en_yakin_mesafe <= self.warning_distance:
            # Uyarı bölgesi
            uyari_seviyesi = "uyarı"
            guvenli_bolgede = True
            aciklama = f"🔶 Sınıra yaklaşıyor ({en_yakin_mesafe:.1f}m)"

        else:
            # Güvenli bölge
            uyari_seviyesi = "güvenli"
            guvenli_bolgede = True
            aciklama = f"✅ Güvenli bölgede ({en_yakin_mesafe:.1f}m)"

        # Güvenli yön önerisi
        onerilenen_yon = None
        if not guvenli_bolgede:
            onerilenen_yon = self._guvenli_yon_hesapla(mevcut_konum, en_yakin_nokta)

        sonuc = SinirKontrolSonucu(
            guvenli_bolgede=guvenli_bolgede,
            sinira_mesafe=en_yakin_mesafe,
            en_yakin_sinir_noktasi=en_yakin_nokta,
            uyari_seviyesi=uyari_seviyesi,
            onerilenen_yon=onerilenen_yon,
            aciklama=aciklama
        )

        # Log seviyesine göre yazdır
        if uyari_seviyesi == "tehlike":
            self.logger.warning(f"🚨 {aciklama}")
        elif uyari_seviyesi == "uyarı":
            self.logger.info(f"⚠️ {aciklama}")
        else:
            self.logger.debug(f"✅ {aciklama}")

        return sonuc

    def _nokta_polygon_icinde_mi(self, nokta: KoordinatNoktasi) -> bool:
        """
        Point-in-polygon algoritması (Ray casting)

        Args:
            nokta: Kontrol edilecek nokta

        Returns:
            bool: Nokta polygon içinde mi?
        """
        if len(self.sinir_noktalari) < 3:
            return False

        x, y = nokta.longitude, nokta.latitude
        n = len(self.sinir_noktalari)
        icinde = False

        p1x, p1y = self.sinir_noktalari[0].longitude, self.sinir_noktalari[0].latitude

        for i in range(1, n + 1):
            p2x, p2y = self.sinir_noktalari[i % n].longitude, self.sinir_noktalari[i % n].latitude

            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            icinde = not icinde

            p1x, p1y = p2x, p2y

        return icinde

    def _en_yakin_sinir_noktasini_bul(self, nokta: KoordinatNoktasi) -> Tuple[float, KoordinatNoktasi]:
        """
        En yakın sınır noktasını bul

        Args:
            nokta: Referans nokta

        Returns:
            Tuple[float, KoordinatNoktasi]: (mesafe, nokta)
        """
        min_mesafe = float('inf')
        en_yakin_nokta = self.sinir_noktalari[0]

        for sinir_noktasi in self.sinir_noktalari:
            mesafe = self._haversine_mesafe(
                nokta.latitude, nokta.longitude,
                sinir_noktasi.latitude, sinir_noktasi.longitude
            )

            if mesafe < min_mesafe:
                min_mesafe = mesafe
                en_yakin_nokta = sinir_noktasi

        return min_mesafe, en_yakin_nokta

    def _guvenli_yon_hesapla(self, mevcut_nokta: KoordinatNoktasi,
                             en_yakin_sinir: KoordinatNoktasi) -> float:
        """
        Güvenli yön hesapla (sınırdan uzaklaşma yönü)

        Args:
            mevcut_nokta: Mevcut konum
            en_yakin_sinir: En yakın sınır noktası

        Returns:
            float: Güvenli yön (radyan)
        """
        # Sınır noktasından uzaklaşma yönü
        delta_lat = mevcut_nokta.latitude - en_yakin_sinir.latitude
        delta_lon = mevcut_nokta.longitude - en_yakin_sinir.longitude

        # Bahçe merkezini hesapla
        merkez_lat = sum(p.latitude for p in self.sinir_noktalari) / len(self.sinir_noktalari)
        merkez_lon = sum(p.longitude for p in self.sinir_noktalari) / len(self.sinir_noktalari)

        # Merkeze doğru yön
        merkeze_lat = merkez_lat - mevcut_nokta.latitude
        merkeze_lon = merkez_lon - mevcut_nokta.longitude

        # Ağırlıklı güvenli yön
        guvenli_yon = math.atan2(merkeze_lat * 0.7 + delta_lat * 0.3,
                                 merkeze_lon * 0.7 + delta_lon * 0.3)

        return guvenli_yon

    def _haversine_mesafe(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Haversine formülü ile iki GPS koordinatı arasındaki mesafe

        Args:
            lat1, lon1: İlk koordinat
            lat2, lon2: İkinci koordinat

        Returns:
            float: Mesafe (metre)
        """
        R = 6371000  # Dünya yarıçapı (metre)

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    def bahce_merkezini_al(self) -> KoordinatNoktasi:
        """Bahçe merkezini hesapla"""
        if not self.sinir_noktalari:
            return KoordinatNoktasi(0, 0)

        merkez_lat = sum(p.latitude for p in self.sinir_noktalari) / len(self.sinir_noktalari)
        merkez_lon = sum(p.longitude for p in self.sinir_noktalari) / len(self.sinir_noktalari)

        return KoordinatNoktasi(merkez_lat, merkez_lon)

    def sinir_istatistiklerini_al(self) -> Dict[str, Any]:
        """Sınır kontrol istatistiklerini al"""
        return {
            "toplam_kontrol": self.toplam_kontrol_sayisi,
            "sinir_ihlali": self.sinir_ihlali_sayisi,
            "ihlal_orani": (self.sinir_ihlali_sayisi / max(1, self.toplam_kontrol_sayisi)) * 100,
            "bahce_alani": self.bahce_alani,
            "sinir_nokta_sayisi": len(self.sinir_noktalari),
            "buffer_mesafesi": self.buffer_distance,
            "uyari_mesafesi": self.warning_distance
        }

    def web_icin_sinir_verilerini_hazirla(self) -> Dict[str, Any]:
        """Web arayüzü için sınır verilerini hazırla"""
        sinir_verileri = []

        for nokta in self.sinir_noktalari:
            sinir_verileri.append({
                "lat": nokta.latitude,
                "lon": nokta.longitude
            })

        merkez = self.bahce_merkezini_al()

        return {
            "boundary_points": sinir_verileri,
            "center": {"lat": merkez.latitude, "lon": merkez.longitude},
            "area": self.bahce_alani,
            "buffer_distance": self.buffer_distance,
            "warning_distance": self.warning_distance
        }

    def get_current_boundary_status_for_web(self, mevcut_lat: float, mevcut_lon: float) -> Dict[str, Any]:
        """
        🌐 Web arayüzü için mevcut sınır durumunu al

        Bu fonksiyon web server'ın ihtiyacı olan formatta sınır bilgilerini döndürür.
        Tüm hesaplamalar burada yapılır, web server sadece formatlamakla uğraşır.

        Args:
            mevcut_lat: Mevcut GPS latitude
            mevcut_lon: Mevcut GPS longitude

        Returns:
            Dict: Web API formatında sınır durumu
        """
        if not self.sinir_noktalari:
            return {
                "active": False,
                "distance_to_fence": None,
                "fence_violations": 0,
                "violation_rate": 0.0,
                "garden_area": 0.0,
                "status": "INACTIVE",
                "buffer_distance": self.buffer_distance,
                "warning_distance": self.warning_distance
            }

        try:
            # Sınır kontrolü yap
            kontrol_sonucu = self.robot_konumunu_kontrol_et(mevcut_lat, mevcut_lon)

            # Uyarı seviyesini web formatına çevir
            web_status = self._convert_uyari_to_web_status(kontrol_sonucu.uyari_seviyesi)

            return {
                "active": True,
                "distance_to_fence": kontrol_sonucu.sinira_mesafe,
                "fence_violations": self.sinir_ihlali_sayisi,
                "violation_rate": (self.sinir_ihlali_sayisi / max(1, self.toplam_kontrol_sayisi)) * 100,
                "garden_area": self.bahce_alani,
                "status": web_status,
                "buffer_distance": self.buffer_distance,
                "warning_distance": self.warning_distance
            }

        except Exception as e:
            self.logger.error(f"❌ Sınır durumu web formatı hatası: {e}")
            return {
                "active": False,
                "distance_to_fence": None,
                "fence_violations": self.sinir_ihlali_sayisi,
                "violation_rate": 0.0,
                "garden_area": self.bahce_alani,
                "status": "ERROR",
                "buffer_distance": self.buffer_distance,
                "warning_distance": self.warning_distance
            }

    def _convert_uyari_to_web_status(self, uyari_seviyesi: str) -> str:
        """Uyarı seviyesini web API formatına çevir"""
        status_map = {
            "güvenli": "SAFE",
            "uyarı": "WARNING",
            "tehlike": "DANGER"
        }
        return status_map.get(uyari_seviyesi, "UNKNOWN")
