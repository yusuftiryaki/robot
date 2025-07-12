"""
📷 Kamera İşlemci - Robot'un Gözleri (HAL Pattern)
Hacı Abi'nin görüntü işleme algoritması burada!

Bu sınıf robot'un kamerasından görüntü işler:
- Engel tanıma ve sınıflandırma
- Şarj istasyonu tespiti
- Otlak alanı analizi
- HAL pattern ile temiz kamera abstraction

HAL Pattern kullanarak simülasyon ve gerçek kamera arasında temiz ayrım sağlar.
"""

# OpenCV import - dev container OpenGL sorunu için koşullu
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  OpenCV import hatası: {e}")
    print("   Dev container'da OpenGL sorunu olabilir")
    CV2_AVAILABLE = False
    # Dummy cv2 module for dev environment

    class DummyCV2:
        def __init__(self):
            self.CAP_PROP_FRAME_WIDTH = 3
            self.CAP_PROP_FRAME_HEIGHT = 4
            self.CAP_PROP_FPS = 5
            self.COLOR_BGR2RGB = 4
            self.COLOR_BGR2HSV = 40
            self.COLOR_HSV2BGR = 54
            self.COLOR_BGR2GRAY = 7
            self.INTER_AREA = 3
            self.MORPH_CLOSE = 3
            self.MORPH_OPEN = 2
            self.MORPH_RECT = 0
            self.MORPH_ELLIPSE = 2
            self.THRESH_BINARY = 0
            self.THRESH_BINARY_INV = 1
            self.THRESH_OTSU = 8
            self.ADAPTIVE_THRESH_GAUSSIAN_C = 1
            self.RETR_EXTERNAL = 0
            self.CHAIN_APPROX_SIMPLE = 2

        def VideoCapture(self, *args):
            return DummyVideoCapture()

        def resize(self, img, size, interpolation=None):
            return np.zeros((*size[::-1], 3), dtype=np.uint8)

        def cvtColor(self, img, code):
            return img

        def threshold(self, img, thresh, maxval, type):
            return thresh, img

        def adaptiveThreshold(self, img, maxval, adaptive_method, thresh_type, block_size, c):
            return img

        def morphologyEx(self, img, op, kernel):
            return img

        def getStructuringElement(self, shape, ksize):
            return np.ones(ksize, dtype=np.uint8)

        def inRange(self, img, lower, upper):
            return np.zeros((img.shape[0], img.shape[1]), dtype=np.uint8)

        def GaussianBlur(self, img, ksize, sigma):
            return img

        def arcLength(self, contour, closed):
            return 100.0

        def findContours(self, img, mode, method):
            return [], []

        def contourArea(self, contour):
            return 0

        def boundingRect(self, contour):
            return (0, 0, 0, 0)

        def bitwise_and(self, img1, img2, mask=None):
            return img1

        def countNonZero(self, img):
            return 0

        def rectangle(self, img, pt1, pt2, color, thickness):
            return img

        def putText(self, img, text, org, fontFace, fontScale, color, thickness):
            return img

        @property
        def FONT_HERSHEY_SIMPLEX(self):
            return 0

        def imencode(self, ext, img):
            return True, b'dummy_image_data'

        def imwrite(self, filename, img):
            return True

    class DummyVideoCapture:
        def __init__(self):
            self.opened = False

        def isOpened(self):
            return self.opened

        def read(self):
            return False, np.zeros((480, 640, 3), dtype=np.uint8)

        def release(self):
            pass

        def set(self, prop, value):
            pass

        def get(self, prop):
            return 0

    cv2 = DummyCV2()

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# HAL Pattern imports
try:
    from hardware.hal import KameraFactory, KameraInterface
except ImportError:
    from src.hardware.hal import KameraFactory, KameraInterface


class EngelTipi(Enum):
    """Engel tipi enum'u"""
    BILINMEYEN = "bilinmeyen"
    AGAC = "agac"
    TAS = "tas"
    DUVAR = "duvar"
    INSAN = "insan"
    HAYVAN = "hayvan"
    ARAC = "arac"


@dataclass
class Engel:
    """Tespit edilen engel"""
    tip: EngelTipi
    konum: Tuple[int, int]  # (x, y) pixel koordinatı
    boyut: Tuple[int, int]  # (genişlik, yükseklik)
    mesafe: float  # tahmini mesafe (metre)
    guven_skoru: float  # 0-1 arası


@dataclass
class SarjIstasyonu:
    """Şarj istasyonu tespiti"""
    tespit_edildi: bool
    konum: Tuple[int, int]  # merkez koordinatı
    mesafe: float  # tahmini mesafe
    yon: float  # radyan cinsinden yön
    guven_skoru: float


class KameraIslemci:
    """
    📷 Ana Kamera İşlemci Sınıfı (HAL Pattern)

    HAL pattern kullanarak kamera işlemleri yapar.
    Business logic ve hardware abstraction temiz şekilde ayrılmıştır.
    """

    def __init__(self, camera_config: Dict[str, Any]):
        self.config = camera_config
        self.logger = logging.getLogger("KameraIslemci")

        # HAL Pattern - Kamera interface oluştur
        try:
            self.kamera: KameraInterface = KameraFactory.create_kamera(camera_config)
            self.logger.info(f"📷 Kamera HAL oluşturuldu: {type(self.kamera).__name__}")
        except Exception as e:
            self.logger.error(f"❌ Kamera HAL oluşturma hatası: {e}")
            raise

        # Engel tespit parametreleri - Daha az hassas (simülasyon uyumlu)
        self.engel_min_alan = 1500  # pixel² - Daha büyük minimum alan
        self.engel_max_alan = 50000  # pixel²

        # Şarj istasyonu tespit parametreleri (IR LED'ler için)
        self.sarj_ir_threshold = 200
        self.sarj_min_contour_area = 100

        # Engel tanıma için basit renk aralıkları
        self.renk_araliklari = {
            "yesil": {"lower": np.array([40, 40, 40]), "upper": np.array([80, 255, 255])},
            "kahverengi": {"lower": np.array([10, 50, 20]), "upper": np.array([20, 255, 200])},
            "gri": {"lower": np.array([0, 0, 50]), "upper": np.array([180, 30, 200])}
        }

        self.logger.info(f"📷 Kamera işlemci başlatıldı (HAL: {type(self.kamera).__name__})")

    async def baslat(self) -> bool:
        """🚀 Kamera sistemini başlat"""
        try:
            self.logger.info("🚀 Kamera sistemi başlatılıyor...")
            return await self.kamera.baslat()
        except Exception as e:
            self.logger.error(f"❌ Kamera başlatma hatası: {e}")
            return False

    async def goruntu_al(self) -> Optional[np.ndarray]:
        """
        📸 HAL üzerinden kameradan görüntü al

        Returns:
            numpy.ndarray: BGR formatında görüntü
        """
        try:
            return await self.kamera.goruntu_al()
        except Exception as e:
            self.logger.error(f"❌ HAL görüntü alma hatası: {e}")
            return None

    async def engel_analiz_et(self) -> Dict[str, Any]:
        """
        🚧 Görüntüde engel analizi yap

        Returns:
            Dict: Tespit edilen engeller ve analiz sonuçları
        """
        goruntu = await self.goruntu_al()
        if goruntu is None:
            return {"engeller": [], "analiz_basarili": False}

        try:
            # Görüntüyü HSV'ye çevir
            hsv = cv2.cvtColor(goruntu, cv2.COLOR_BGR2HSV)

            # Engelleri tespit et
            engeller = []

            # Ağaç tespiti (kahverengi alanlar)
            agac_engelleri = await self._agac_tespit_et(hsv)
            engeller.extend(agac_engelleri)

            # Taş tespiti (gri alanlar)
            tas_engelleri = await self._tas_tespit_et(hsv)
            engeller.extend(tas_engelleri)

            # Genel engel tespiti (kontur analizi)
            genel_engeller = await self._genel_engel_tespit_et(goruntu)
            engeller.extend(genel_engeller)

            # Sonuçları analiz et
            analiz_sonucu = {
                "engeller": [self._engel_to_dict(e) for e in engeller],
                "engel_sayisi": len(engeller),
                "en_yakin_engel": self._en_yakin_engel_bul(engeller),
                "guzergah_temiz": len(engeller) == 0,
                "analiz_basarili": True,
                "timestamp": datetime.now().isoformat()
            }

            self.logger.debug(
                f"🚧 Engel analizi: {len(engeller)} engel tespit edildi")
            return analiz_sonucu

        except Exception as e:
            self.logger.error(f"❌ Engel analizi hatası: {e}")
            return {"engeller": [], "analiz_basarili": False}

    async def _agac_tespit_et(self, hsv: np.ndarray) -> List[Engel]:
        """Ağaç tespiti (kahverengi alanlar)"""
        kahverengi_mask = cv2.inRange(
            hsv,
            self.renk_araliklari["kahverengi"]["lower"],
            self.renk_araliklari["kahverengi"]["upper"]
        )

        # Morfolojik işlemler
        kernel = np.ones((5, 5), np.uint8)
        kahverengi_mask = cv2.morphologyEx(
            kahverengi_mask, cv2.MORPH_CLOSE, kernel)
        kahverengi_mask = cv2.morphologyEx(
            kahverengi_mask, cv2.MORPH_OPEN, kernel)

        # Konturları bul
        contours, _ = cv2.findContours(
            kahverengi_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        agaclar = []
        for contour in contours:
            alan = cv2.contourArea(contour)
            if self.engel_min_alan < alan < self.engel_max_alan:
                x, y, w, h = cv2.boundingRect(contour)

                # Ağaç tahmini mesafesi (basit hesaplama)
                mesafe = self._pixel_to_distance(w, h, "agac")

                agac = Engel(
                    tip=EngelTipi.AGAC,
                    konum=(x + w // 2, y + h // 2),
                    boyut=(w, h),
                    mesafe=mesafe,
                    guven_skoru=0.7
                )
                agaclar.append(agac)

        return agaclar

    async def _tas_tespit_et(self, hsv: np.ndarray) -> List[Engel]:
        """Taş tespiti (gri alanlar)"""
        gri_mask = cv2.inRange(
            hsv,
            self.renk_araliklari["gri"]["lower"],
            self.renk_araliklari["gri"]["upper"]
        )

        # Morfolojik işlemler
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        gri_mask = cv2.morphologyEx(gri_mask, cv2.MORPH_CLOSE, kernel)

        # Konturları bul
        contours, _ = cv2.findContours(
            gri_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        taslar = []
        for contour in contours:
            alan = cv2.contourArea(contour)
            if self.engel_min_alan * 0.5 < alan < self.engel_max_alan * 0.3:  # Taşlar daha küçük
                x, y, w, h = cv2.boundingRect(contour)

                # Dairesellik kontrolü (taşlar genelde yuvarlak)
                perimeter = cv2.arcLength(contour, True)
                if perimeter > 0:
                    circularity = 4 * np.pi * alan / (perimeter * perimeter)
                    if circularity > 0.3:  # Yeterince yuvarlak
                        mesafe = self._pixel_to_distance(w, h, "tas")

                        tas = Engel(
                            tip=EngelTipi.TAS,
                            konum=(x + w // 2, y + h // 2),
                            boyut=(w, h),
                            mesafe=mesafe,
                            guven_skoru=circularity
                        )
                        taslar.append(tas)

        return taslar

    async def _genel_engel_tespit_et(self, goruntu: np.ndarray) -> List[Engel]:
        """Genel engel tespiti (kontur analizi) - Daha az hassas"""
        # Gri tonlamaya çevir
        gray = cv2.cvtColor(goruntu, cv2.COLOR_BGR2GRAY)

        # Gaussian blur uygula - Daha fazla blur
        blurred = cv2.GaussianBlur(gray, (21, 21), 0)

        # Adaptive threshold - Daha az hassas parametreler
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 21, 8
        )

        # Konturları bul
        contours, _ = cv2.findContours(
            thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        genel_engeller = []
        for contour in contours:
            alan = cv2.contourArea(contour)
            if self.engel_min_alan < alan < self.engel_max_alan:
                x, y, w, h = cv2.boundingRect(contour)

                # Aspect ratio kontrolü - Daha geniş aralık
                aspect_ratio = w / h
                if 0.1 < aspect_ratio < 10.0:  # Daha geniş aspect ratio aralığı
                    mesafe = self._pixel_to_distance(w, h, "bilinmeyen")

                    engel = Engel(
                        tip=EngelTipi.BILINMEYEN,
                        konum=(x + w // 2, y + h // 2),
                        boyut=(w, h),
                        mesafe=mesafe,
                        guven_skoru=0.5
                    )
                    genel_engeller.append(engel)

        return genel_engeller

    def _pixel_to_distance(self, width: int, height: int, engel_tipi: str) -> float:
        """
        Pixel boyutundan mesafe tahmini

        Bu basit bir hesaplama. Gerçek uygulamada kamera kalibrasyonu gerekli.
        """
        # Gerçek nesne boyutları (metre)
        gercek_boyutlar = {
            "agac": 0.3,  # Ağaç gövdesi yaklaşık 30cm
            "tas": 0.15,  # Taş yaklaşık 15cm
            "bilinmeyen": 0.2  # Ortalama 20cm
        }

        # Basit perspektif hesaplaması
        gercek_boyut = gercek_boyutlar.get(engel_tipi, 0.2)
        focal_length = 500  # Tahmini focal length (kalibrasyonla belirlenecek)

        # Mesafe = (Gerçek_Boyut * Focal_Length) / Pixel_Boyut
        pixel_boyut = max(width, height)
        if pixel_boyut > 0:
            mesafe = (gercek_boyut * focal_length) / pixel_boyut
            return max(0.1, min(10.0, mesafe))  # 0.1m - 10m arası sınırla

        return 2.0  # Varsayılan 2 metre

    def _en_yakin_engel_bul(self, engeller: List[Engel]) -> Optional[Dict[str, Any]]:
        """En yakın engeli bul"""
        if not engeller:
            return None

        en_yakin = min(engeller, key=lambda e: e.mesafe)
        return self._engel_to_dict(en_yakin)

    def _engel_to_dict(self, engel: Engel) -> Dict[str, Any]:
        """Engel objesini dictionary'ye çevir"""
        return {
            "tip": engel.tip.value,
            "konum": engel.konum,
            "boyut": engel.boyut,
            "mesafe": engel.mesafe,
            "guven_skoru": engel.guven_skoru
        }

    async def sarj_istasyonu_ara(self) -> Dict[str, Any]:
        """
        🔌 Şarj istasyonu arama (IR LED tespiti)

        Şarj istasyonunda IR LED'ler olduğunu varsayar.
        """
        goruntu = await self.goruntu_al()
        if goruntu is None:
            return {"sarj_istasyonu_gorunur": False}

        try:
            # Gri tonlamaya çevir
            gray = cv2.cvtColor(goruntu, cv2.COLOR_BGR2GRAY)

            # Parlak noktaları bul (IR LED'ler)
            _, thresh = cv2.threshold(
                gray, self.sarj_ir_threshold, 255, cv2.THRESH_BINARY)

            # Konturları bul
            contours, _ = cv2.findContours(
                thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # IR LED'leri filtrele
            ir_noktalar = []
            for contour in contours:
                alan = cv2.contourArea(contour)
                if self.sarj_min_contour_area < alan < 1000:
                    x, y, w, h = cv2.boundingRect(contour)
                    merkez = (x + w // 2, y + h // 2)
                    ir_noktalar.append(merkez)

            # Şarj istasyonu pattern'i ara (2 yakın LED)
            sarj_tespit = False
            sarj_merkezi = None
            sarj_mesafesi = 0.0
            sarj_yonu = 0.0

            if len(ir_noktalar) >= 2:
                # En yakın 2 LED'i bul
                for i in range(len(ir_noktalar)):
                    for j in range(i + 1, len(ir_noktalar)):
                        p1, p2 = ir_noktalar[i], ir_noktalar[j]
                        mesafe = np.sqrt((p1[0] - p2[0]) **
                                         2 + (p1[1] - p2[1])**2)

                        # LED'ler arası mesafe uygun mu? (20-100 pixel)
                        if 20 < mesafe < 100:
                            sarj_tespit = True
                            sarj_merkezi = (
                                (p1[0] + p2[0]) // 2, (p1[1] + p2[1]) // 2)

                            # Mesafe tahmini (merkez pixel'den)
                            resolution = self.kamera.get_resolution()
                            img_center_x = resolution[0] // 2
                            sarj_mesafesi = self._pixel_to_distance(
                                int(mesafe), int(mesafe), "sarj")

                            # Yön hesaplama (radyan)
                            sarj_yonu = np.arctan2(sarj_merkezi[1] - resolution[1] // 2,
                                                   sarj_merkezi[0] - img_center_x)
                            break

                    if sarj_tespit:
                        break

            sonuc = {
                "sarj_istasyonu_gorunur": sarj_tespit,
                "konum": sarj_merkezi,
                "mesafe": sarj_mesafesi,
                "yon": sarj_yonu,
                "guven_skoru": 0.8 if sarj_tespit else 0.0,
                "ir_nokta_sayisi": len(ir_noktalar)
            }

            if sarj_tespit:
                self.logger.info(
                    f"🔌 Şarj istasyonu tespit edildi! Mesafe: {sarj_mesafesi:.2f}m")

            return sonuc

        except Exception as e:
            self.logger.error(f"❌ Şarj istasyonu arama hatası: {e}")
            return {"sarj_istasyonu_gorunur": False}

    async def otlak_analiz_et(self) -> Dict[str, Any]:
        """
        🌱 Otlak alanı analizi (biçilecek alan tespiti)

        Yeşil alanları tespit eder ve biçme önceliği belirler.
        """
        goruntu = await self.goruntu_al()
        if goruntu is None:
            return {"analiz_basarili": False}

        try:
            # HSV'ye çevir
            hsv = cv2.cvtColor(goruntu, cv2.COLOR_BGR2HSV)

            # Yeşil alan maskesi
            yesil_mask = cv2.inRange(
                hsv,
                self.renk_araliklari["yesil"]["lower"],
                self.renk_araliklari["yesil"]["upper"]
            )

            # Morfolojik işlemler
            kernel = np.ones((5, 5), np.uint8)
            yesil_mask = cv2.morphologyEx(yesil_mask, cv2.MORPH_OPEN, kernel)
            yesil_mask = cv2.morphologyEx(yesil_mask, cv2.MORPH_CLOSE, kernel)

            # Yeşil alan istatistikleri
            total_pixels = yesil_mask.shape[0] * yesil_mask.shape[1]
            yesil_pixels = cv2.countNonZero(yesil_mask)
            yesil_orani = yesil_pixels / total_pixels

            # Otlak yoğunluğu analizi (yeşil tonlama çeşitliliği)
            yesil_alan = cv2.bitwise_and(hsv, hsv, mask=yesil_mask)
            if yesil_pixels > 0:
                # V kanalı (brightness) istatistikleri
                v_channel = yesil_alan[:, :, 2]
                v_nonzero = v_channel[v_channel > 0]

                if len(v_nonzero) > 0:
                    # Type assertion to fix numpy typing issues
                    v_array = np.asarray(v_nonzero, dtype=np.float32)
                    ot_yogunlugu = float(np.mean(v_array)) / 255.0
                    ot_uniformlugu = 1.0 - (float(np.std(v_array)) / 255.0)
                else:
                    ot_yogunlugu = 0.0
                    ot_uniformlugu = 0.0
            else:
                ot_yogunlugu = 0.0
                ot_uniformlugu = 0.0

            # Biçme önceliği hesapla
            bicme_onceligi = yesil_orani * ot_yogunlugu

            analiz_sonucu = {
                "analiz_basarili": True,
                "yesil_alan_orani": yesil_orani,
                "ot_yogunlugu": ot_yogunlugu,
                "ot_uniformlugu": ot_uniformlugu,
                "bicme_onceligi": bicme_onceligi,
                "bicme_onerisi": bicme_onceligi > 0.3,
                "timestamp": datetime.now().isoformat()
            }

            self.logger.debug(
                f"🌱 Otlak analizi: %{yesil_orani*100:.1f} yeşil alan")
            return analiz_sonucu

        except Exception as e:
            self.logger.error(f"❌ Otlak analizi hatası: {e}")
            return {"analiz_basarili": False}

    def get_kamera_durumu(self) -> Dict[str, Any]:
        """HAL üzerinden kamera durumu bilgisi"""
        try:
            hal_bilgi = self.kamera.get_kamera_bilgisi()
            return {
                **hal_bilgi,
                "engel_tespit_parametreleri": {
                    "min_alan": self.engel_min_alan,
                    "max_alan": self.engel_max_alan
                }
            }
        except Exception as e:
            self.logger.error(f"❌ Kamera durumu alma hatası: {e}")
            return {"aktif": False, "hata": str(e)}

    async def durdur(self):
        """
        🛑 HAL üzerinden kamerayı durdur ve kaynakları temizle
        """
        self.logger.info("🛑 Kamera durdurma işlemi başlatılıyor...")

        try:
            await self.kamera.durdur()
            self.logger.info("✅ Kamera HAL üzerinden durduruldu")
        except Exception as e:
            self.logger.error(f"❌ Kamera durdurma hatası: {e}")

    def goruntu_kaydet(self, dosya_adi: str):
        """HAL üzerinden mevcut görüntüyü kaydet"""
        try:
            dosya_yolu = f"logs/{dosya_adi}_{self.kamera.get_kamera_bilgisi().get('goruntu_sayaci', 0)}.jpg"
            if self.kamera.goruntu_kaydet(dosya_yolu):
                self.logger.info(f"💾 Görüntü HAL üzerinden kaydedildi: {dosya_yolu}")
            else:
                self.logger.warning("⚠️ Görüntü kaydedilemedi")
        except Exception as e:
            self.logger.error(f"❌ Görüntü kaydetme hatası: {e}")

    def __del__(self):
        """Kamera işlemci kapatılıyor"""
        if hasattr(self, 'logger'):
            self.logger.info("👋 Kamera işlemci kapatılıyor...")
