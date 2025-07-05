"""
📷 Kamera İşlemci - Robot'un Gözleri
Hacı Abi'nin görüntü işleme algoritması burada!

Bu sınıf robot'un kamerasından görüntü işler:
- Engel tanıma ve sınıflandırma
- Şarj istasyonu tespiti
- Otlak alanı analizi
- Görsel odometri (opsiyonel)
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
            self.INTER_AREA = 3
            self.MORPH_CLOSE = 3
            self.MORPH_OPEN = 2
            self.MORPH_RECT = 0
            self.THRESH_BINARY = 0
            self.THRESH_OTSU = 8

        def VideoCapture(self, *args):
            return DummyVideoCapture()

        def resize(self, img, size, interpolation=None):
            return np.zeros((*size[::-1], 3), dtype=np.uint8)

        def cvtColor(self, img, code):
            return img

        def threshold(self, img, thresh, maxval, type):
            return thresh, img

        def morphologyEx(self, img, op, kernel):
            return img

        def getStructuringElement(self, shape, ksize):
            return np.ones(ksize, dtype=np.uint8)

        def findContours(self, img, mode, method):
            return [], []

        def contourArea(self, contour):
            return 0

        def boundingRect(self, contour):
            return (0, 0, 0, 0)

        def rectangle(self, img, pt1, pt2, color, thickness):
            return img

        def putText(self, img, text, org, fontFace, fontScale, color, thickness):
            return img

        @property
        def FONT_HERSHEY_SIMPLEX(self):
            return 0

        def imencode(self, ext, img):
            return True, b'dummy_image_data'

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

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


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
    📷 Ana Kamera İşlemci Sınıfı

    Raspberry Pi kamerasından görüntü alır ve işler.
    OpenCV ile görüntü analizi yapar.
    """

    def __init__(self, camera_config: Dict[str, Any]):
        self.config = camera_config
        self.logger = logging.getLogger("KameraIslemci")

        # Kamera parametreleri - Config'ten al
        # Resolution - hem [width, height] hem de {width: x, height: y} formatlarını destekle
        resolution_config = camera_config.get("resolution", [640, 480])
        if isinstance(resolution_config, list):
            # [width, height] formatında
            self.resolution = tuple(resolution_config)
        else:
            # {width: x, height: y} formatında
            self.resolution = tuple((
                resolution_config.get("width", 640),
                resolution_config.get("height", 480)
            ))
        self.framerate = camera_config.get("fps", 30)
        self.device_id = camera_config.get("device_id", 0)
        self.auto_exposure = camera_config.get("auto_exposure", True)

        # Simülasyon parametreleri
        simulation_params = camera_config.get("simulation_params", {})
        self.test_pattern = simulation_params.get("test_pattern", True)
        self.noise_level = simulation_params.get("noise_level", 0.05)

        # Simülasyon modu
        self.simulation_mode = self._is_simulation()

        # Kamera objesi
        self.camera = None
        self.son_goruntu = None
        self.goruntu_sayaci = 0

        # Engel tespit parametreleri
        self.engel_min_alan = 500  # pixel²
        self.engel_max_alan = 50000  # pixel²

        # Şarj istasyonu tespit parametreleri (IR LED'ler için)
        self.sarj_ir_threshold = 200
        self.sarj_min_contour_area = 100

        # Kalibrasyon parametreleri
        self.camera_matrix = None
        self.dist_coeffs = None

        # Engel tanıma için basit renk aralıkları
        self.renk_araliklari = {
            "yesil": {"lower": np.array([40, 40, 40]), "upper": np.array([80, 255, 255])},
            "kahverengi": {"lower": np.array([10, 50, 20]), "upper": np.array([20, 255, 200])},
            "gri": {"lower": np.array([0, 0, 50]), "upper": np.array([180, 30, 200])}
        }

        self.logger.info(
            f"📷 Kamera işlemci başlatıldı (Simülasyon: {self.simulation_mode})")
        self.logger.info(f"📷 Çözünürlük: {self.resolution}, FPS: {self.framerate}")
        if self.simulation_mode:
            self.logger.info(f"📷 Simülasyon: Test pattern: {self.test_pattern}, Noise: {self.noise_level}")
        self._init_camera()

    def _is_simulation(self) -> bool:
        """Simülasyon modunda mı kontrol et"""
        try:
            from picamera2 import Picamera2
            return False
        except ImportError:
            return True

    def _init_camera(self):
        """Kamerayı başlat"""
        if self.simulation_mode:
            self._init_simulation_camera()
        else:
            self._init_real_camera()

    def _init_simulation_camera(self):
        """Simülasyon kamerası başlat - Config'ten ayarları kullan"""
        self.logger.info("🔧 Simülasyon kamerası başlatılıyor...")

        # Config'ten simülasyon ayarlarını al
        if self.test_pattern:
            # Test paterni ile görüntü oluştur
            self.son_goruntu = self._create_test_pattern()
        else:
            # Düz yeşil görüntü oluştur
            self.son_goruntu = np.zeros(
                (self.resolution[1], self.resolution[0], 3), dtype=np.uint8)
            self.son_goruntu[:, :] = [0, 150, 0]  # Yeşil çimen rengi

        # Noise ekle
        if self.noise_level > 0:
            self._add_noise_to_image()

        self.logger.info("✅ Simülasyon kamerası hazır!")

    def _create_test_pattern(self) -> np.ndarray:
        """Test paterni oluştur"""
        img = np.zeros((self.resolution[1], self.resolution[0], 3), dtype=np.uint8)

        # Satranç tahtası paterni
        square_size = 50
        for i in range(0, self.resolution[1], square_size):
            for j in range(0, self.resolution[0], square_size):
                if (i // square_size + j // square_size) % 2 == 0:
                    img[i:i + square_size, j:j + square_size] = [255, 255, 255]  # Beyaz
                else:
                    img[i:i + square_size, j:j + square_size] = [0, 0, 0]  # Siyah

        return img

    def _add_noise_to_image(self):
        """Görüntüye noise ekle"""
        if self.son_goruntu is not None:
            noise = np.random.normal(0, self.noise_level * 255, self.son_goruntu.shape)
            self.son_goruntu = np.clip(self.son_goruntu + noise, 0, 255).astype(np.uint8)

    def _init_real_camera(self):
        """Gerçek kamerayı başlat"""
        self.logger.info("🔧 Fiziksel kamera başlatılıyor...")
        try:
            from picamera2 import Picamera2

            self.camera = Picamera2()
            config = self.camera.create_preview_configuration(
                main={"format": "RGB888", "size": self.resolution}
            )
            self.camera.configure(config)
            self.camera.start()

            # Kamera kalibrasyonu yükle (varsa)
            self._load_camera_calibration()

            self.logger.info("✅ Fiziksel kamera hazır!")

        except Exception as e:
            self.logger.error(f"❌ Kamera başlatma hatası: {e}")
            self.simulation_mode = True
            self._init_simulation_camera()

    def _load_camera_calibration(self):
        """Kamera kalibrasyon parametrelerini yükle"""
        try:
            # Kalibrasyon dosyası varsa yükle
            # Bu gerçek uygulamada OpenCV kamera kalibrasyonu ile oluşturulur
            self.logger.info("📐 Kamera kalibrasyonu yüklendi")
        except Exception as e:
            self.logger.warning(f"⚠️ Kalibrasyon yüklenemedi: {e}")

    async def goruntu_al(self) -> Optional[np.ndarray]:
        """
        📸 Kameradan görüntü al

        Returns:
            numpy.ndarray: BGR formatında görüntü
        """
        try:
            if self.simulation_mode:
                return await self._simulation_goruntu_al()
            else:
                return await self._real_goruntu_al()
        except Exception as e:
            self.logger.error(f"❌ Görüntü alma hatası: {e}")
            return None

    async def _simulation_goruntu_al(self) -> np.ndarray:
        """Simülasyon görüntüsü oluştur"""
        # Dinamik sahte görüntü oluştur
        goruntu = np.zeros(
            (self.resolution[1], self.resolution[0], 3), dtype=np.uint8)

        # Yeşil arkaplan (çimen)
        goruntu[:, :, 1] = 100  # Yeşil kanal

        # Zamanla değişen sahte engeller ekle
        t = time.time()

        # Sahte ağaç (kahverengi dikdörtgen)
        if int(t) % 10 < 5:  # 5 saniye görünür, 5 saniye gizli
            cv2.rectangle(goruntu, (300, 200), (350, 400), (0, 50, 100), -1)

        # Sahte taş (gri daire)
        if int(t) % 15 < 7:
            cv2.circle(goruntu, (150, 350), 30, (100, 100, 100), -1)

        # Sahte şarj istasyonu (parlak noktalar)
        if int(t) % 20 < 3:  # Arada şarj istasyonu görün
            cv2.circle(goruntu, (500, 300), 10, (255, 255, 255), -1)
            cv2.circle(goruntu, (520, 310), 8, (255, 255, 255), -1)

        # Gürültü ekle
        noise = np.random.randint(0, 20, goruntu.shape, dtype=np.uint8)
        goruntu = cv2.add(goruntu, noise)

        self.son_goruntu = goruntu
        self.goruntu_sayaci += 1

        return goruntu

    async def _real_goruntu_al(self) -> np.ndarray:
        """Gerçek kameradan görüntü al"""
        if self.camera is None:
            return None

        # Picamera2'den görüntü al
        goruntu = self.camera.capture_array()

        # RGB'den BGR'ye çevir (OpenCV formatı)
        goruntu = cv2.cvtColor(goruntu, cv2.COLOR_RGB2BGR)

        self.son_goruntu = goruntu
        self.goruntu_sayaci += 1

        return goruntu

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
        """Genel engel tespiti (kontur analizi)"""
        # Gri tonlamaya çevir
        gray = cv2.cvtColor(goruntu, cv2.COLOR_BGR2GRAY)

        # Gaussian blur uygula
        blurred = cv2.GaussianBlur(gray, (15, 15), 0)

        # Adaptive threshold
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
        )

        # Konturları bul
        contours, _ = cv2.findContours(
            thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        genel_engeller = []
        for contour in contours:
            alan = cv2.contourArea(contour)
            if self.engel_min_alan < alan < self.engel_max_alan:
                x, y, w, h = cv2.boundingRect(contour)

                # Aspect ratio kontrolü
                aspect_ratio = w / h
                if 0.2 < aspect_ratio < 5.0:  # Makul aspect ratio
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
                            img_center_x = self.resolution[0] // 2
                            pixel_distance = abs(
                                sarj_merkezi[0] - img_center_x)
                            sarj_mesafesi = self._pixel_to_distance(
                                int(mesafe), int(mesafe), "sarj")

                            # Yön hesaplama (radyan)
                            sarj_yonu = np.arctan2(sarj_merkezi[1] - self.resolution[1] // 2,
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
                    ot_yogunlugu = np.mean(v_nonzero) / 255.0
                    ot_uniformlugu = 1.0 - (np.std(v_nonzero) / 255.0)
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

    def goruntu_kaydet(self, dosya_adi: str):
        """Mevcut görüntüyü kaydet"""
        if self.son_goruntu is not None:
            try:
                cv2.imwrite(
                    f"logs/{dosya_adi}_{self.goruntu_sayaci}.jpg", self.son_goruntu)
                self.logger.info(
                    f"💾 Görüntü kaydedildi: {dosya_adi}_{self.goruntu_sayaci}.jpg")
            except Exception as e:
                self.logger.error(f"❌ Görüntü kaydetme hatası: {e}")

    def get_kamera_durumu(self) -> Dict[str, Any]:
        """Kamera durumu bilgisi"""
        return {
            "aktif": self.camera is not None or self.simulation_mode,
            "simülasyon": self.simulation_mode,
            "resolution": self.resolution,
            "framerate": self.framerate,
            "goruntu_sayaci": self.goruntu_sayaci,
            "son_goruntu_zamani": datetime.now().isoformat() if self.son_goruntu is not None else None
        }

    def __del__(self):
        """Kamera işlemci kapatılıyor"""
        if hasattr(self, 'logger'):
            self.logger.info("👋 Kamera işlemci kapatılıyor...")

        if hasattr(self, 'camera') and self.camera is not None:
            try:
                self.camera.stop()
                self.camera.close()
            except:
                pass
                pass
