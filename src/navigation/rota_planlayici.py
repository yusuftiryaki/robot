"""
🗺️ Rota Planlayıcı - Robot'un Strategisti
Hacı Abi'nin rota planlama algoritması burada!

Bu sınıf robot'un nereye gideceğine karar verir:
- Biçerdöver (boustrophedon) metodu ile sistematik biçme
- A* algoritması ile engelden kaçınma
- Dinamik rota planlaması
- Şarj istasyonu yönlendirme
"""

import heapq
import json
import logging
import math
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np


class RotaTipi(Enum):
    """Rota tipi enum'u"""
    BOUSTROPHEDON = "boustrophedon"  # Biçerdöver metodu
    SPIRAL = "spiral"  # Spiral rota
    PERIMETER = "perimeter"  # Çevre kontrolü
    POINT_TO_POINT = "point_to_point"  # Noktadan noktaya
    RETURN_TO_DOCK = "return_to_dock"  # Şarj istasyonuna dön


@dataclass
class Nokta:
    """2D nokta"""
    x: float
    y: float

    def __eq__(self, other):
        return abs(self.x - other.x) < 0.01 and abs(self.y - other.y) < 0.01

    def __hash__(self):
        return hash((round(self.x, 2), round(self.y, 2)))


@dataclass
class RotaNoktasi:
    """Rota noktası"""
    nokta: Nokta
    yon: float  # radyan
    hiz: float  # m/s
    aksesuar_aktif: bool  # fırçalar vs.


@dataclass
class Alan:
    """Çalışma alanı tanımı"""
    sol_alt: Nokta
    sag_ust: Nokta
    engeller: List[Nokta]


class AStarNode:
    """A* algoritması için düğüm"""

    def __init__(self, nokta: Nokta, g_cost: float = 0, h_cost: float = 0, parent=None):
        self.nokta = nokta
        self.g_cost = g_cost  # Başlangıçtan bu düğüme maliyet
        self.h_cost = h_cost  # Bu düğümden hedefe tahmini maliyet
        self.f_cost = g_cost + h_cost  # Toplam maliyet
        self.parent = parent

    def __lt__(self, other):
        return self.f_cost < other.f_cost

    def __eq__(self, other):
        return self.nokta == other.nokta

    def __hash__(self):
        return hash(self.nokta)


class RotaPlanlayici:
    """
    🗺️ Ana Rota Planlayıcı Sınıfı

    Robot'un çeşitli görevler için rota planlamasını yapar.
    Engelleri hesaba katarak güvenli rotalar oluşturur.
    """

    def __init__(self, nav_config: Dict[str, Any]):
        self.config = nav_config
        self.logger = logging.getLogger("RotaPlanlayici")

        # Grid parametreleri
        path_config = nav_config.get("path_planning", {})
        self.grid_resolution = path_config.get("grid_resolution", 0.1)  # 10cm
        self.obstacle_padding = path_config.get("obstacle_padding", 0.2)  # 20cm

        # Çalışma alanı
        self.calisma_alani: Optional[Alan] = None
        self.engel_grid: Optional[np.ndarray] = None
        self.grid_genislik = 0
        self.grid_yukseklik = 0

        # Şarj istasyonu konumu
        self.sarj_istasyonu: Optional[Nokta] = None

        # Mevcut rota
        self.mevcut_rota: List[RotaNoktasi] = []
        self.rota_index = 0

        # Biçme parametreleri
        mowing_config = nav_config.get("missions", {}).get("mowing", {})
        self.bicme_overlap = mowing_config.get("overlap", 0.1)  # 10cm örtüşme
        self.bicme_hiz = mowing_config.get("speed", 0.3)  # 0.3 m/s

        self.logger.info("🗺️ Rota planlayıcı başlatıldı")

    def calisma_alanini_ayarla(self, alan: Alan):
        """
        📐 Çalışma alanını ayarla

        Args:
            alan: Çalışma alanı tanımı
        """
        self.calisma_alani = alan

        # Grid boyutlarını hesapla
        genislik = alan.sag_ust.x - alan.sol_alt.x
        yukseklik = alan.sag_ust.y - alan.sol_alt.y

        self.grid_genislik = int(genislik / self.grid_resolution) + 1
        self.grid_yukseklik = int(yukseklik / self.grid_resolution) + 1

        # Engel grid'ini oluştur
        self._engel_grid_olustur()

        self.logger.info(f"📐 Çalışma alanı ayarlandı: {genislik:.1f}m x {yukseklik:.1f}m")
        self.logger.info(f"🔢 Grid boyutu: {self.grid_genislik} x {self.grid_yukseklik}")

    def _engel_grid_olustur(self):
        """Engel grid'ini oluştur"""
        if not self.calisma_alani:
            return

        # Grid'i sıfırla (False = boş, True = engel)
        self.engel_grid = np.zeros((self.grid_yukseklik, self.grid_genislik), dtype=bool)

        # Engelleri grid'e işle
        for engel in self.calisma_alani.engeller:
            self._engeli_grid_ekle(engel)

        self.logger.info(f"🚧 {len(self.calisma_alani.engeller)} engel grid'e eklendi")

    def _engeli_grid_ekle(self, engel: Nokta):
        """Tek bir engeli grid'e ekle (padding ile)"""
        if not self.calisma_alani:
            return

        # Engel etrafında padding uygula
        padding_grid = int(self.obstacle_padding / self.grid_resolution)

        # Engel merkezini grid koordinatına çevir
        grid_x = int((engel.x - self.calisma_alani.sol_alt.x) / self.grid_resolution)
        grid_y = int((engel.y - self.calisma_alani.sol_alt.y) / self.grid_resolution)

        # Padding alanını engel olarak işaretle
        for dy in range(-padding_grid, padding_grid + 1):
            for dx in range(-padding_grid, padding_grid + 1):
                gx = grid_x + dx
                gy = grid_y + dy

                if 0 <= gx < self.grid_genislik and 0 <= gy < self.grid_yukseklik:
                    self.engel_grid[gy, gx] = True

    def sarj_istasyonu_ayarla(self, konum: Nokta):
        """🔌 Şarj istasyonu konumunu ayarla"""
        self.sarj_istasyonu = konum
        self.logger.info(f"🔌 Şarj istasyonu konumu: ({konum.x:.2f}, {konum.y:.2f})")

    async def boustrophedon_rota_olustur(self) -> List[RotaNoktasi]:
        """
        🌾 Biçerdöver metodu ile sistematik biçme rotası oluştur

        Bu metod tarla biçimi için optimize edilmiş en etkili yöntemdir.
        Robot alanı çizgiler halinde tarayarak hiçbir bölgeyi kaçırmaz.
        """
        if not self.calisma_alani:
            self.logger.error("❌ Çalışma alanı tanımlanmamış!")
            return []

        self.logger.info("🌾 Biçerdöver rotası oluşturuluyor...")

        rota_noktalari: List[RotaNoktasi] = []

        # Biçme şerit genişliği (fırça genişliği - örtüşme)
        fir_ca_genisligi = 0.25  # Mi Robot fırça genişliği yaklaşık 25cm
        serit_genisligi = fir_ca_genisligi - self.bicme_overlap

        # Alanın sol alt köşesinden başla
        baslangic_x = self.calisma_alani.sol_alt.x
        bitis_x = self.calisma_alani.sag_ust.x
        baslangic_y = self.calisma_alani.sol_alt.y
        bitis_y = self.calisma_alani.sag_ust.y

        # Y ekseni boyunca şeritler oluştur
        mevcut_y = baslangic_y
        serit_no = 0

        while mevcut_y < bitis_y:
            if serit_no % 2 == 0:  # Çift şeritler: soldan sağa
                x_start, x_end = baslangic_x, bitis_x
                yon = 0.0  # Doğu yönü
            else:  # Tek şeritler: sağdan sola
                x_start, x_end = bitis_x, baslangic_x
                yon = math.pi  # Batı yönü

            # Şerit üzerinde nokta oluştur
            serit_noktalari = await self._serit_noktalari_olustur(
                x_start, x_end, mevcut_y, yon
            )
            rota_noktalari.extend(serit_noktalari)

            # Sonraki şeride geçiş noktası
            mevcut_y += serit_genisligi
            if mevcut_y < bitis_y:
                # Şerit değiştirme hareketi
                gecis_noktasi = RotaNoktasi(
                    nokta=Nokta(x_end, mevcut_y),
                    yon=math.pi / 2 if serit_no % 2 == 0 else -math.pi / 2,
                    hiz=self.bicme_hiz * 0.5,  # Daha yavaş geçiş
                    aksesuar_aktif=True
                )
                rota_noktalari.append(gecis_noktasi)

            serit_no += 1

        self.mevcut_rota = rota_noktalari
        self.rota_index = 0

        self.logger.info(f"✅ Biçerdöver rotası oluşturuldu: {len(rota_noktalari)} nokta")
        return rota_noktalari

    async def _serit_noktalari_olustur(self, x_start: float, x_end: float, y: float, yon: float) -> List[RotaNoktasi]:
        """Tek bir şerit için nokta listesi oluştur"""
        noktalari: List[RotaNoktasi] = []

        # Şerit yönünü belirle
        if x_start < x_end:  # Soldan sağa
            step = self.grid_resolution
        else:  # Sağdan sola
            step = -self.grid_resolution

        mevcut_x = x_start
        while (step > 0 and mevcut_x <= x_end) or (step < 0 and mevcut_x >= x_end):
            # Bu noktada engel var mı kontrol et
            if self._nokta_guvenli_mi(Nokta(mevcut_x, y)):
                nokta = RotaNoktasi(
                    nokta=Nokta(mevcut_x, y),
                    yon=yon,
                    hiz=self.bicme_hiz,
                    aksesuar_aktif=True  # Biçme sırasında fırçalar aktif
                )
                noktalari.append(nokta)
            else:
                # Engel varsa engeli aşmak için A* kullan
                engel_asma_noktalari = await self._engel_as(
                    Nokta(mevcut_x - step, y),
                    Nokta(mevcut_x + step, y)
                )
                noktalari.extend(engel_asma_noktalari)

            mevcut_x += step

        return noktalari

    def _nokta_guvenli_mi(self, nokta: Nokta) -> bool:
        """Verilen nokta güvenli mi kontrol et"""
        if not self.calisma_alani or self.engel_grid is None:
            return True

        # Nokta çalışma alanı içinde mi?
        if (nokta.x < self.calisma_alani.sol_alt.x or
            nokta.x > self.calisma_alani.sag_ust.x or
            nokta.y < self.calisma_alani.sol_alt.y or
                nokta.y > self.calisma_alani.sag_ust.y):
            return False

        # Grid koordinatına çevir
        grid_x = int((nokta.x - self.calisma_alani.sol_alt.x) / self.grid_resolution)
        grid_y = int((nokta.y - self.calisma_alani.sol_alt.y) / self.grid_resolution)

        # Sınırlar içinde mi?
        if (0 <= grid_x < self.grid_genislik and
                0 <= grid_y < self.grid_yukseklik):
            return not self.engel_grid[grid_y, grid_x]

        return False

    async def _engel_as(self, baslangic: Nokta, hedef: Nokta) -> List[RotaNoktasi]:
        """Engeli aşmak için A* algoritması ile rota bul"""
        rota = await self.a_star_rota_bul(baslangic, hedef)

        # Rota noktalarını RotaNoktasi'na çevir
        rota_noktalari = []
        for i, nokta in enumerate(rota):
            # Yön hesapla
            if i + 1 < len(rota):
                dx = rota[i + 1].x - nokta.x
                dy = rota[i + 1].y - nokta.y
                yon = math.atan2(dy, dx)
            else:
                yon = 0.0

            rota_noktasi = RotaNoktasi(
                nokta=nokta,
                yon=yon,
                hiz=self.bicme_hiz * 0.7,  # Engel geçişinde yavaş
                aksesuar_aktif=False  # Engel geçişinde fırçalar kapalı
            )
            rota_noktalari.append(rota_noktasi)

        return rota_noktalari

    async def a_star_rota_bul(self, baslangic: Nokta, hedef: Nokta) -> List[Nokta]:
        """
        🎯 A* algoritması ile en kısa güvenli rota bul

        Args:
            baslangic: Başlangıç noktası
            hedef: Hedef noktası

        Returns:
            List[Nokta]: Rota noktalarının listesi
        """
        if not self._nokta_guvenli_mi(baslangic) or not self._nokta_guvenli_mi(hedef):
            self.logger.warning("⚠️ Başlangıç veya hedef nokta güvenli değil!")
            return []

        # A* algoritması
        open_set = []
        closed_set: Set[Nokta] = set()

        # Başlangıç düğümü
        start_node = AStarNode(
            nokta=baslangic,
            g_cost=0,
            h_cost=self._heuristic(baslangic, hedef)
        )
        heapq.heappush(open_set, start_node)

        while open_set:
            current_node = heapq.heappop(open_set)

            # Hedefe ulaştık mı?
            if current_node.nokta == hedef:
                return self._reconstruct_path(current_node)

            closed_set.add(current_node.nokta)

            # Komşu düğümleri kontrol et
            for komsur in self._get_neighbors(current_node.nokta):
                if komsur in closed_set or not self._nokta_guvenli_mi(komsur):
                    continue

                g_cost = current_node.g_cost + self._distance(current_node.nokta, komsur)
                h_cost = self._heuristic(komsur, hedef)

                neighbor_node = AStarNode(
                    nokta=komsur,
                    g_cost=g_cost,
                    h_cost=h_cost,
                    parent=current_node
                )

                # Bu düğüm zaten open_set'te mi ve daha iyi mi?
                existing = next((n for n in open_set if n.nokta == komsur), None)
                if existing is None or neighbor_node.g_cost < existing.g_cost:
                    if existing:
                        open_set.remove(existing)
                    heapq.heappush(open_set, neighbor_node)

        self.logger.warning("⚠️ A* ile rota bulunamadı!")
        return []

    def _heuristic(self, nokta1: Nokta, nokta2: Nokta) -> float:
        """A* için heuristik fonksiyon (Manhattan mesafesi)"""
        return abs(nokta1.x - nokta2.x) + abs(nokta1.y - nokta2.y)

    def _distance(self, nokta1: Nokta, nokta2: Nokta) -> float:
        """İki nokta arası Öklid mesafesi"""
        return math.sqrt((nokta1.x - nokta2.x)**2 + (nokta1.y - nokta2.y)**2)

    def _get_neighbors(self, nokta: Nokta) -> List[Nokta]:
        """Verilen noktanın komşularını al (8 yön)"""
        komsu_list = []

        for dx in [-self.grid_resolution, 0, self.grid_resolution]:
            for dy in [-self.grid_resolution, 0, self.grid_resolution]:
                if dx == 0 and dy == 0:
                    continue

                komsu = Nokta(nokta.x + dx, nokta.y + dy)
                komsu_list.append(komsu)

        return komsu_list

    def _reconstruct_path(self, node: AStarNode) -> List[Nokta]:
        """A* düğümünden geriye giderek rotayı oluştur"""
        path = []
        current = node

        while current:
            path.append(current.nokta)
            current = current.parent

        path.reverse()
        return path

    async def sarj_istasyonu_rotasi(self, konum_takipci=None, gps_dock_config: Dict[str, Any] = None) -> Optional[List[RotaNoktasi]]:
        """
        🔋 GPS destekli şarj istasyonu rotası oluştur

        Args:
            konum_takipci: KonumTakipci nesnesi (mevcut konum için)
            gps_dock_config: Şarj istasyonu GPS konfigürasyonu

        Returns:
            Şarj istasyonuna güvenli rota
        """
        if not gps_dock_config:
            self.logger.warning("⚠️ Şarj istasyonu GPS konfigürasyonu bulunamadı!")
            return await self._fallback_sarj_rotasi()

        dock_lat = gps_dock_config.get("latitude")
        dock_lon = gps_dock_config.get("longitude")
        gps_accuracy = gps_dock_config.get("accuracy_radius", 3.0)

        if not dock_lat or not dock_lon:
            self.logger.error("❌ Şarj istasyonu GPS koordinatları eksik!")
            return await self._fallback_sarj_rotasi()

        if not konum_takipci:
            self.logger.warning("⚠️ Konum takipçi yok, varsayılan rota kullanılıyor")
            return await self._fallback_sarj_rotasi()

        # Mevcut konum ve şarj istasyonuna olan mesafeyi al
        mevcut_konum = konum_takipci.get_mevcut_konum()
        gps_analiz = konum_takipci.gps_hedef_dogrulugu(dock_lat, dock_lon, gps_accuracy)

        self.logger.info(f"🗺️ Şarj istasyonu GPS analizi: {gps_analiz['dogruluk_seviyesi']}")
        self.logger.info(f"📍 Mesafe: {gps_analiz['mesafe']:.2f}m, Yön: {gps_analiz['bearing']:.1f}°")

        # GPS doğruluğuna göre strateji belirle
        mesafe = gps_analiz["mesafe"]

        if mesafe <= gps_accuracy:
            # Şarj istasyonu GPS hata payı içinde - hassas yaklaşım
            return await self._hassas_sarj_yaklasimu(mevcut_konum, dock_lat, dock_lon, konum_takipci)
        elif mesafe <= 10.0:
            # Orta mesafe - GPS rehberli yaklaşım
            return await self._gps_rehberli_yaklaşım(mevcut_konum, dock_lat, dock_lon, konum_takipci)
        else:
            # Uzak mesafe - A* ile planlama
            return await self._uzak_mesafe_planlamasi(mevcut_konum, dock_lat, dock_lon, konum_takipci)

    async def _hassas_sarj_yaklasimu(self, mevcut_konum, dock_lat: float, dock_lon: float, konum_takipci) -> List[RotaNoktasi]:
        """🎯 GPS hata payı içindeyken hassas yaklaşım"""
        self.logger.info("🎯 Hassas şarj yaklaşımı - kamera ve sensörler aktif")

        # Şarj istasyonunu local koordinata çevir
        dock_x, dock_y = konum_takipci._gps_to_local(dock_lat, dock_lon)

        # Basit düz rota oluştur - çok yavaş
        rota = []
        steps = 5  # 5 adımda yaklaş

        for i in range(steps + 1):
            progress = i / steps
            x = mevcut_konum.x + (dock_x - mevcut_konum.x) * progress
            y = mevcut_konum.y + (dock_y - mevcut_konum.y) * progress

            # Son adımlarda çok yavaş
            if progress > 0.8:
                hiz = 0.05  # 5 cm/s - ultra yavaş
            elif progress > 0.6:
                hiz = 0.1   # 10 cm/s - çok yavaş
            else:
                hiz = 0.2   # 20 cm/s - yavaş

            # Hedefe yön
            yon = konum_takipci.get_bearing_to_gps(dock_lat, dock_lon)

            rota_noktasi = RotaNoktasi(
                nokta=Nokta(x, y),
                yon=yon,
                hiz=hiz,
                aksesuar_aktif=False
            )
            rota.append(rota_noktasi)

        return rota

    async def _gps_rehberli_yaklaşım(self, mevcut_konum, dock_lat: float, dock_lon: float, konum_takipci) -> List[RotaNoktasi]:
        """🧭 GPS rehberli orta mesafe yaklaşımı"""
        self.logger.info("🧭 GPS rehberli yaklaşım")

        # Şarj istasyonunu local koordinata çevir
        dock_x, dock_y = konum_takipci._gps_to_local(dock_lat, dock_lon)

        # Waypoint'ler oluştur (her 2 metrede bir)
        mesafe = konum_takipci.get_mesafe_to(dock_x, dock_y)
        waypoint_sayisi = max(3, int(mesafe / 2.0))

        rota = []
        for i in range(waypoint_sayisi + 1):
            progress = i / waypoint_sayisi
            x = mevcut_konum.x + (dock_x - mevcut_konum.x) * progress
            y = mevcut_konum.y + (dock_y - mevcut_konum.y) * progress

            # Mesafeye göre hız ayarla
            kalan_mesafe = konum_takipci.get_mesafe_to_gps(dock_lat, dock_lon)
            if kalan_mesafe < 3.0:
                hiz = 0.1  # Son 3m'de yavaş
            elif kalan_mesafe < 6.0:
                hiz = 0.2  # Son 6m'de orta hız
            else:
                hiz = 0.3  # Normal hız

            yon = konum_takipci.get_bearing_to_gps(dock_lat, dock_lon)

            rota_noktasi = RotaNoktasi(
                nokta=Nokta(x, y),
                yon=yon,
                hiz=hiz,
                aksesuar_aktif=False
            )
            rota.append(rota_noktasi)

        self.logger.info(f"✅ GPS rehberli rota: {len(rota)} waypoint")
        return rota

    async def _uzak_mesafe_planlamasi(self, mevcut_konum, dock_lat: float, dock_lon: float, konum_takipci) -> List[RotaNoktasi]:
        """🗺️ Uzak mesafeden A* ile planlama"""
        self.logger.info("🗺️ Uzak mesafe - A* algoritması ile planlama")

        # Şarj istasyonunu local koordinata çevir
        dock_x, dock_y = konum_takipci._gps_to_local(dock_lat, dock_lon)
        dock_nokta = Nokta(dock_x, dock_y)
        mevcut_nokta = Nokta(mevcut_konum.x, mevcut_konum.y)

        # A* ile engelleri aşarak rota bul
        rota_noktalari = await self.a_star_rota_bul(mevcut_nokta, dock_nokta)

        if not rota_noktalari:
            self.logger.error("❌ A* ile rota bulunamadı!")
            return []

        # Rota noktalarını RotaNoktasi'na çevir
        sarj_rotasi = []
        for i, nokta in enumerate(rota_noktalari):
            # Yön hesapla
            if i + 1 < len(rota_noktalari):
                dx = rota_noktalari[i + 1].x - nokta.x
                dy = rota_noktalari[i + 1].y - nokta.y
                yon = math.atan2(dy, dx)
            else:
                yon = konum_takipci.get_bearing_to_gps(dock_lat, dock_lon)

            # Şarja yaklaştıkça yavaşla
            mesafe_kalan = self._distance(nokta, dock_nokta)
            if mesafe_kalan < 1.0:
                hiz = 0.1  # Son 1m çok yavaş
            elif mesafe_kalan < 3.0:
                hiz = 0.2  # Son 3m yavaş
            else:
                hiz = 0.3  # Normal hız

            rota_noktasi = RotaNoktasi(
                nokta=nokta,
                yon=yon,
                hiz=hiz,
                aksesuar_aktif=False
            )
            sarj_rotasi.append(rota_noktasi)

        self.logger.info(f"✅ A* şarj rotası: {len(sarj_rotasi)} nokta")
        return sarj_rotasi

    async def _fallback_sarj_rotasi(self) -> Optional[List[RotaNoktasi]]:
        """🔄 Fallback - eski yöntem ile şarj rotası"""
        self.logger.warning("🔄 GPS olmadan şarj rotası - eski yöntem kullanılıyor")

        if not self.sarj_istasyonu:
            self.logger.error("❌ Şarj istasyonu konumu hiç tanımlanmamış!")
            return None

        # Mevcut konum varsayılan
        mevcut_konum = Nokta(0.0, 0.0)

        # A* ile şarj istasyonuna rota bul
        rota_noktalari = await self.a_star_rota_bul(mevcut_konum, self.sarj_istasyonu)

        if not rota_noktalari:
            self.logger.error("❌ Fallback rota da bulunamadı!")
            return None

        # Basit rota oluştur
        sarj_rotasi = []
        for i, nokta in enumerate(rota_noktalari):
            yon = 0.0 if i == len(rota_noktalari) - 1 else math.atan2(
                rota_noktalari[i + 1].y - nokta.y,
                rota_noktalari[i + 1].x - nokta.x
            )

            rota_noktasi = RotaNoktasi(
                nokta=nokta,
                yon=yon,
                hiz=0.2,  # Yavaş güvenli hız
                aksesuar_aktif=False
            )
            sarj_rotasi.append(rota_noktasi)

        return sarj_rotasi

    def get_next_waypoint(self) -> Optional[RotaNoktasi]:
        """
        ➡️ Rotadan bir sonraki hedefe noktayı al

        Returns:
            Sonraki rota noktası veya None (rota bitti)
        """
        if not self.mevcut_rota or self.rota_index >= len(self.mevcut_rota):
            return None

        waypoint = self.mevcut_rota[self.rota_index]
        self.rota_index += 1

        self.logger.debug(f"➡️ Sonraki waypoint: ({waypoint.nokta.x:.2f}, {waypoint.nokta.y:.2f})")
        return waypoint

    def rota_tamamlandi_mi(self) -> bool:
        """Mevcut rota tamamlandı mı?"""
        return self.rota_index >= len(self.mevcut_rota)

    def rota_ilerlemesi(self) -> Dict[str, Any]:
        """Rota ilerleme durumu"""
        if not self.mevcut_rota:
            return {"tamamlanan": 0, "toplam": 0, "yuzde": 0}

        return {
            "tamamlanan": self.rota_index,
            "toplam": len(self.mevcut_rota),
            "yuzde": (self.rota_index / len(self.mevcut_rota)) * 100
        }

    def rotayi_sifirla(self):
        """Mevcut rotayı sıfırla"""
        self.mevcut_rota.clear()
        self.rota_index = 0
        self.logger.info("🔄 Rota sıfırlandı")

    def save_rota(self, dosya_adi: str):
        """Rotayı dosyaya kaydet"""
        try:
            rota_data = []
            for nokta in self.mevcut_rota:
                rota_data.append({
                    "x": nokta.nokta.x,
                    "y": nokta.nokta.y,
                    "yon": nokta.yon,
                    "hiz": nokta.hiz,
                    "aksesuar_aktif": nokta.aksesuar_aktif
                })

            with open(f"logs/{dosya_adi}.json", "w") as f:
                json.dump(rota_data, f, indent=2)

            self.logger.info(f"💾 Rota kaydedildi: {dosya_adi}.json")

        except Exception as e:
            self.logger.error(f"❌ Rota kaydetme hatası: {e}")

    def get_rota_istatistikleri(self) -> Dict[str, Any]:
        """Rota istatistikleri"""
        if not self.mevcut_rota:
            return {}

        toplam_mesafe = 0.0
        bicme_mesafesi = 0.0

        for i in range(len(self.mevcut_rota) - 1):
            mesafe = self._distance(
                self.mevcut_rota[i].nokta,
                self.mevcut_rota[i + 1].nokta
            )
            toplam_mesafe += mesafe

            if self.mevcut_rota[i].aksesuar_aktif:
                bicme_mesafesi += mesafe

        return {
            "toplam_nokta": len(self.mevcut_rota),
            "toplam_mesafe": toplam_mesafe,
            "bicme_mesafesi": bicme_mesafesi,
            "sadece_hareket": toplam_mesafe - bicme_mesafesi,
            "verimlilik": (bicme_mesafesi / toplam_mesafe * 100) if toplam_mesafe > 0 else 0
        }
