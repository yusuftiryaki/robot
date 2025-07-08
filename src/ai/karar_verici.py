"""
🧠 AI Karar Verici - Robot'un Beyni
Hacı Abi'nin yapay zeka algoritması burada!

Bu sınıf robot'un ne yapacağına karar verir:
- Sensör verilerini analiz eder
- Durum değerlendirmesi yapar
- Optimal hareket stratejisi belirler
- Acil durum yönetimi
"""

import json
import logging
import math
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


class Oncelik(Enum):
    """Karar öncelik seviyeleri"""
    KRITIK = 1    # Acil durum, güvenlik
    YUKSEK = 2    # Engel kaçınma, şarj
    ORTA = 3      # Normal görev
    DUSUK = 4     # Optimizasyon


class HareketTipi(Enum):
    """Hareket tipi enum'u"""
    DURMA = "durma"
    ILERI = "ileri"
    GERI = "geri"
    SOL_DONME = "sol_donme"
    SAG_DONME = "sag_donme"
    YAY_HAREKET = "yay_hareket"
    ZIGZAG = "zigzag"


@dataclass
class KararSonucu:
    """AI karar sonucu"""
    hareket: Dict[str, float]  # {"linear": 0.0, "angular": 0.0}
    oncelik: Oncelik
    sebep: str
    guven_skoru: float  # 0-1 arası
    aksesuar_komutlari: Dict[str, bool]
    alternatif_eylemler: List[str]


class KararVerici:
    """
    🧠 Ana AI Karar Verici Sınıfı

    Robot'un tüm sensör verilerini analiz ederek
    en uygun hareket stratejisini belirler.
    """

    def __init__(self, ai_config: Dict[str, Any]):
        self.config = ai_config
        self.logger = logging.getLogger("KararVerici")

        # Config'ten AI ayarlarını al
        self.enabled = ai_config.get("enabled", True)
        self.debug_mode = ai_config.get("debug_mode", False)
        self.model_path = ai_config.get("model_path", "/workspaces/oba/models")
        self.use_cpu = ai_config.get("use_cpu", True)
        self.confidence_threshold = ai_config.get("confidence_threshold", 0.5)

        # Karar parametreleri
        self.guvenlik_mesafesi = 0.5  # metre
        self.hiz_limitleri = {
            "normal": 0.3,      # m/s
            "yavas": 0.1,       # m/s
            "acil": 0.0         # m/s (dur)
        }

        # Öğrenme ve adaptasyon
        self.gecmis_kararlar: List[KararSonucu] = []
        self.basari_oranlari = {
            "engel_kacirma": 0.8,
            "rota_takibi": 0.9,
            "enerji_yonetimi": 0.7
        }

        # AI modeli (eğer enabled ise)
        self.ai_model = None
        if self.enabled:
            self._load_ai_model()

        # Durum hafızası
        self.onceki_durum = None
        self.karar_sayaci = 0
        self.son_engel_zamani = 0

        # Fuzzy logic parametreleri
        self._init_fuzzy_logic()

        self.logger.info("🧠 AI karar verici başlatıldı")

    def _init_fuzzy_logic(self):
        """Fuzzy logic sistemini başlat"""
        # Mesafe üyelik fonksiyonları
        self.mesafe_uyelik = {
            "cok_yakin": lambda x: max(0, min(1, (0.3 - x) / 0.3)) if x <= 0.3 else 0,
            "yakin": lambda x: max(0, min((x - 0.2) / 0.3, (0.8 - x) / 0.3)) if 0.2 <= x <= 0.8 else 0,
            "uzak": lambda x: max(0, (x - 0.5) / 1.0) if x >= 0.5 else 0
        }

        # Hız üyelik fonksiyonları
        self.hiz_uyelik = {
            "yavaş": lambda x: max(0, min(1, (0.2 - x) / 0.2)) if x <= 0.2 else 0,
            "orta": lambda x: max(0, min((x - 0.1) / 0.2, (0.4 - x) / 0.2)) if 0.1 <= x <= 0.4 else 0,
            "hizli": lambda x: max(0, (x - 0.3) / 0.2) if x >= 0.3 else 0
        }

    async def next_action_belirle(self, sensor_data: Dict[str, Any], kamera_data: Dict[str, Any]) -> KararSonucu:
        """
        🎯 Ana karar fonksiyonu

        Tüm verileri analiz ederek robot'un bir sonraki eylemini belirler.
        """
        self.karar_sayaci += 1

        # Acil durum kontrolü (en yüksek öncelik)
        acil_karar = await self._acil_durum_kontrol(sensor_data)
        if acil_karar:
            return acil_karar

        # AI model ile tahmin (varsa)
        ai_prediction = self._predict_with_ai(sensor_data)
        if ai_prediction and self.debug_mode:
            self.logger.debug(f"🤖 AI önerisi: {ai_prediction}")

        # Güvenlik kontrolü
        guvenlik_karar = await self._guvenlik_analizi(sensor_data, kamera_data)
        if guvenlik_karar:
            return guvenlik_karar

        # Engel kaçınma
        engel_karar = await self._engel_kacirma_analizi(kamera_data)
        if engel_karar:
            return engel_karar

        # Görev odaklı karar
        gorev_karar = await self._gorev_analizi(sensor_data, kamera_data)
        if gorev_karar:
            return gorev_karar

        # Varsayılan karar (dur)
        return self._varsayilan_karar()

    async def _acil_durum_kontrol(self, sensor_data: Dict[str, Any]) -> Optional[KararSonucu]:
        """🚨 Acil durum analizi"""
        # Tampon sensörü kontrolü
        tampon_data = sensor_data.get("tampon", {})
        if tampon_data.get("front_bumper", False):
            return KararSonucu(
                hareket={"linear": 0.0, "angular": 0.0},
                oncelik=Oncelik.KRITIK,
                sebep="Ön tampon sensörü tetiklendi",
                guven_skoru=1.0,
                aksesuar_komutlari={"ana_firca": False, "yan_firca": False, "fan": False},
                alternatif_eylemler=["geri_git", "saga_don", "sola_don"]
            )

        # Eğim kontrolü (devrilme riski)
        imu_data = sensor_data.get("imu", {})
        if imu_data:
            roll = abs(imu_data.get("roll", 0))
            pitch = abs(imu_data.get("pitch", 0))
            max_egim = max(roll, pitch)

            if max_egim > 25:  # 25 dereceden fazla eğim
                return KararSonucu(
                    hareket={"linear": 0.0, "angular": 0.0},
                    oncelik=Oncelik.KRITIK,
                    sebep=f"Kritik eğim tespit edildi: {max_egim:.1f}°",
                    guven_skoru=1.0,
                    aksesuar_komutlari={"ana_firca": False, "yan_firca": False, "fan": False},
                    alternatif_eylemler=["geri_git"]
                )

        # Düşük batarya acil durumu
        batarya_data = sensor_data.get("batarya", {})
        if batarya_data:
            seviye = batarya_data.get("level", 50)
            if seviye < 10:  # %10'un altında
                return KararSonucu(
                    hareket={"linear": 0.0, "angular": 0.0},
                    oncelik=Oncelik.KRITIK,
                    sebep=f"Kritik batarya seviyesi: %{seviye:.1f}",
                    guven_skoru=1.0,
                    aksesuar_komutlari={"ana_firca": False, "yan_firca": False, "fan": False},
                    alternatif_eylemler=["sarj_istasyonuna_git"]
                )

        return None

    async def _guvenlik_analizi(self, sensor_data: Dict[str, Any], kamera_data: Dict[str, Any]) -> Optional[KararSonucu]:
        """🛡️ Güvenlik analizi"""
        # Kamera tabanlı engel tespiti (ultrasonik sensörler yerine)
        # Ultrasonik sensörler kaldırıldı, sadece kamera kullanılıyor
        kamera_engel_data = kamera_data.get("engeller", [])
        if kamera_engel_data:
            # En yakın engeli bul
            en_yakin_engel = min(kamera_engel_data, key=lambda e: e.get("mesafe", float('inf')))
            on_mesafe = en_yakin_engel.get("mesafe", float('inf'))

            if on_mesafe < self.guvenlik_mesafesi:
                # Engel tipine göre kaçış stratejisi
                if en_yakin_engel.get("tip") == "insan":
                    # İnsan varsa dur ve bekle
                    angular_hiz = 0.0
                    yon = "dur"
                else:
                    # Diğer engeller için rastgele kaçış (ultrasonik yan sensörleri olmadığı için)
                    angular_hiz = 0.3 if self.son_karar_zamani % 2 == 0 else -0.3
                    yon = "saga" if angular_hiz > 0 else "sola"

                return KararSonucu(
                    hareket={"linear": 0.0, "angular": angular_hiz},
                    oncelik=Oncelik.YUKSEK,
                    sebep=f"Güvenlik mesafesi ihlali: {on_mesafe:.2f}m, {yon} dönülüyor",
                    guven_skoru=0.9,
                    aksesuar_komutlari={"ana_firca": False, "yan_firca": False, "fan": False},
                    alternatif_eylemler=["geri_git", "dur"]
                )

        return None

    async def _engel_kacirma_analizi(self, kamera_data: Dict[str, Any]) -> Optional[KararSonucu]:
        """🚧 Kamera tabanlı engel kaçınma"""
        if not kamera_data.get("analiz_basarili", False):
            return None

        engeller = kamera_data.get("engeller", [])
        if not engeller:
            return None

        # En yakın engeli bul
        en_yakin_engel = min(engeller, key=lambda e: e["mesafe"])

        if en_yakin_engel["mesafe"] < 1.0:  # 1 metre yakınlık
            # Engel konumuna göre kaçınma stratejisi
            img_center = 320  # Görüntü merkezi (640px / 2)
            engel_x = en_yakin_engel["konum"][0]

            if engel_x < img_center - 50:  # Engel solda
                # Sağa kaç
                hareket = {"linear": 0.1, "angular": -0.3}
                yon_aciklama = "sağa kaçma"
            elif engel_x > img_center + 50:  # Engel sağda
                # Sola kaç
                hareket = {"linear": 0.1, "angular": 0.3}
                yon_aciklama = "sola kaçma"
            else:  # Engel ortada
                # Geri git
                hareket = {"linear": -0.1, "angular": 0.0}
                yon_aciklama = "geri gitme"

            return KararSonucu(
                hareket=hareket,
                oncelik=Oncelik.YUKSEK,
                sebep=f"{en_yakin_engel['tip']} engeli tespit edildi ({en_yakin_engel['mesafe']:.2f}m), {yon_aciklama}",
                guven_skoru=en_yakin_engel["guven_skoru"],
                aksesuar_komutlari={"ana_firca": False, "yan_firca": False, "fan": False},
                alternatif_eylemler=["dur", "alternatif_rota"]
            )

        return None

    async def _gorev_analizi(self, sensor_data: Dict[str, Any], kamera_data: Dict[str, Any]) -> Optional[KararSonucu]:
        """🎯 Görev odaklı karar verme"""
        # Batarya seviyesi kontrolü
        batarya_data = sensor_data.get("batarya", {})
        batarya_seviye = batarya_data.get("level", 50) if batarya_data else 50

        # Düşük batarya - şarj istasyonu ara
        if batarya_seviye < 25:
            return await self._sarj_arama_karari(kamera_data)

        # Normal görev - biçme
        return await self._bicme_karari(kamera_data)

    async def _sarj_arama_karari(self, kamera_data: Dict[str, Any]) -> KararSonucu:
        """🔋 Şarj istasyonu arama kararı"""
        # Şarj istasyonu görünür mü?
        if kamera_data.get("sarj_istasyonu_gorunur", False):
            sarj_konum = kamera_data["konum"]
            sarj_mesafe = kamera_data["mesafe"]

            img_center = 320
            hata = sarj_konum[0] - img_center

            # PID benzeri kontrol
            angular_hiz = -hata * 0.005  # Proportional control
            linear_hiz = max(0.05, min(0.2, 0.3 - sarj_mesafe * 0.1))

            return KararSonucu(
                hareket={"linear": linear_hiz, "angular": angular_hiz},
                oncelik=Oncelik.YUKSEK,
                sebep=f"Şarj istasyonuna yönelme (mesafe: {sarj_mesafe:.2f}m)",
                guven_skoru=kamera_data.get("guven_skoru", 0.7),
                aksesuar_komutlari={"ana_firca": False, "yan_firca": False, "fan": False},
                alternatif_eylemler=["sarj_istasyonu_ara"]
            )
        else:
            # Şarj istasyonu ara (dönerek)
            return KararSonucu(
                hareket={"linear": 0.0, "angular": 0.3},
                oncelik=Oncelik.YUKSEK,
                sebep="Şarj istasyonu aranıyor",
                guven_skoru=0.6,
                aksesuar_komutlari={"ana_firca": False, "yan_firca": False, "fan": False},
                alternatif_eylemler=["gps_rota", "manuel_kontrol"]
            )

    async def _bicme_karari(self, kamera_data: Dict[str, Any]) -> KararSonucu:
        """🌱 Biçme görevi kararı"""
        # Otlak analizi var mı?
        if "bicme_onceligi" in kamera_data:
            bicme_onceligi = kamera_data["bicme_onceligi"]

            if bicme_onceligi > 0.3:  # Biçme değer
                # Fuzzy logic ile hız belirleme
                hiz = self._fuzzy_hiz_hesapla(bicme_onceligi)

                return KararSonucu(
                    hareket={"linear": hiz, "angular": 0.0},
                    oncelik=Oncelik.ORTA,
                    sebep=f"Biçme görevi (öncelik: {bicme_onceligi:.2f})",
                    guven_skoru=0.8,
                    aksesuar_komutlari={"ana_firca": True, "yan_firca": True, "fan": True},
                    alternatif_eylemler=["rota_planla", "alan_tara"]
                )
            else:
                # Otlak alanı ara
                return KararSonucu(
                    hareket={"linear": 0.2, "angular": 0.1},
                    oncelik=Oncelik.DUSUK,
                    sebep="Uygun otlak alanı aranıyor",
                    guven_skoru=0.6,
                    aksesuar_komutlari={"ana_firca": False, "yan_firca": False, "fan": False},
                    alternatif_eylemler=["alan_degistir", "rota_planla"]
                )

        # Varsayılan araştırma hareketi
        return KararSonucu(
            hareket={"linear": 0.2, "angular": 0.0},
            oncelik=Oncelik.DUSUK,
            sebep="Araştırma hareketi",
            guven_skoru=0.5,
            aksesuar_komutlari={"ana_firca": False, "yan_firca": False, "fan": False},
            alternatif_eylemler=["dur", "rota_planla"]
        )

    def _fuzzy_hiz_hesapla(self, bicme_onceligi: float) -> float:
        """Fuzzy logic ile hız hesaplama"""
        # Öncelik seviyesine göre üyelik hesapla
        dusuk_uyelik = max(0, min(1, (0.5 - bicme_onceligi) / 0.3))
        orta_uyelik = max(0, min((bicme_onceligi - 0.3) / 0.2, (0.7 - bicme_onceligi) / 0.2))
        yuksek_uyelik = max(0, (bicme_onceligi - 0.6) / 0.4)

        # Hız seviyeleri
        dusuk_hiz = 0.1
        orta_hiz = 0.2
        yuksek_hiz = 0.3

        # Ağırlıklı ortalama (defuzzification)
        pay = (dusuk_uyelik * dusuk_hiz + orta_uyelik * orta_hiz + yuksek_uyelik * yuksek_hiz)
        payda = dusuk_uyelik + orta_uyelik + yuksek_uyelik

        if payda > 0:
            return pay / payda
        else:
            return 0.2  # Varsayılan hız

    def _varsayilan_karar(self) -> KararSonucu:
        """Varsayılan karar (hiçbir koşul sağlanmadığında)"""
        return KararSonucu(
            hareket={"linear": 0.0, "angular": 0.0},
            oncelik=Oncelik.DUSUK,
            sebep="Bekleme durumu",
            guven_skoru=0.3,
            aksesuar_komutlari={"ana_firca": False, "yan_firca": False, "fan": False},
            alternatif_eylemler=["manuel_kontrol", "rota_planla"]
        )

    def karar_basarisini_degerlendır(self, karar: KararSonucu, sonuc: Dict[str, Any]):
        """
        📊 Karar başarısını değerlendir ve öğren

        Args:
            karar: Verilen karar
            sonuc: Kararın sonucu
        """
        basari = sonuc.get("basari", False)

        # Başarı oranlarını güncelle
        if "engel" in karar.sebep and basari:
            self.basari_oranlari["engel_kacirma"] = min(1.0, self.basari_oranlari["engel_kacirma"] + 0.01)
        elif "engel" in karar.sebep and not basari:
            self.basari_oranlari["engel_kacirma"] = max(0.0, self.basari_oranlari["engel_kacirma"] - 0.01)

        # Karar geçmişine ekle
        self.gecmis_kararlar.append(karar)
        if len(self.gecmis_kararlar) > 100:  # Son 100 kararı sakla
            self.gecmis_kararlar.pop(0)

        self.logger.debug(f"📊 Karar değerlendirildi: {basari}, Sebep: {karar.sebep}")

    def get_ogrenme_istatistikleri(self) -> Dict[str, Any]:
        """Öğrenme ve performans istatistikleri"""
        return {
            "basari_oranlari": self.basari_oranlari.copy(),
            "toplam_karar": self.karar_sayaci,
            "son_kararlar": [k.sebep for k in self.gecmis_kararlar[-10:]],
            "ortalama_guven": np.mean([k.guven_skoru for k in self.gecmis_kararlar]) if self.gecmis_kararlar else 0.0
        }

    def parametreleri_ayarla(self, yeni_parametreler: Dict[str, Any]):
        """AI parametrelerini dinamik olarak ayarla"""
        if "guvenlik_mesafesi" in yeni_parametreler:
            self.guvenlik_mesafesi = yeni_parametreler["guvenlik_mesafesi"]

        if "hiz_limitleri" in yeni_parametreler:
            self.hiz_limitleri.update(yeni_parametreler["hiz_limitleri"])

        self.logger.info("🔧 AI parametreleri güncellendi")

    def karar_gecmisini_kaydet(self, dosya_adi: str):
        """Karar geçmişini dosyaya kaydet"""
        try:
            gecmis_data = []
            for karar in self.gecmis_kararlar:
                gecmis_data.append({
                    "hareket": karar.hareket,
                    "oncelik": karar.oncelik.value,
                    "sebep": karar.sebep,
                    "guven_skoru": karar.guven_skoru,
                    "aksesuar": karar.aksesuar_komutlari,
                    "timestamp": datetime.now().isoformat()
                })

            with open(f"logs/{dosya_adi}.json", "w") as f:
                json.dump({
                    "istatistikler": self.get_ogrenme_istatistikleri(),
                    "kararlar": gecmis_data
                }, f, indent=2)

            self.logger.info(f"💾 Karar geçmişi kaydedildi: {dosya_adi}.json")

        except Exception as e:
            self.logger.error(f"❌ Karar geçmişi kaydetme hatası: {e}")

    def _load_ai_model(self):
        """AI modelini yükle"""
        try:
            if self.debug_mode:
                self.logger.debug(f"🤖 AI Model yükleniyor: {self.model_path}")

            # Model dosyasını kontrol et
            import os
            if not os.path.exists(self.model_path):
                self.logger.warning(f"⚠️ Model dizini bulunamadı: {self.model_path}")
                os.makedirs(self.model_path, exist_ok=True)
                self.ai_model = None
                return

            # Model formatlarını kontrol et ve yükle
            model_files = os.listdir(self.model_path)

            if any(f.endswith('.h5') or f.endswith('.keras') for f in model_files):
                # TensorFlow/Keras modeli
                try:
                    import tensorflow as tf
                    keras_model = next((f for f in model_files if f.endswith('.h5') or f.endswith('.keras')), None)
                    if keras_model:
                        self.ai_model = tf.keras.models.load_model(os.path.join(self.model_path, keras_model))
                        self.model_type = 'tensorflow'
                        self.logger.info(f"✅ TensorFlow modeli yüklendi: {keras_model}")
                except ImportError:
                    self.logger.warning("⚠️ TensorFlow bulunamadı, model yüklenemedi")

            elif any(f.endswith('.pt') or f.endswith('.pth') for f in model_files):
                # PyTorch modeli
                try:
                    import torch
                    torch_model = next((f for f in model_files if f.endswith('.pt') or f.endswith('.pth')), None)
                    if torch_model:
                        device = 'cpu' if self.use_cpu else 'cuda'
                        self.ai_model = torch.load(os.path.join(self.model_path, torch_model), map_location=device)
                        self.model_type = 'pytorch'
                        self.logger.info(f"✅ PyTorch modeli yüklendi: {torch_model}")
                except ImportError:
                    self.logger.warning("⚠️ PyTorch bulunamadı, model yüklenemedi")

            elif any(f.endswith('.pkl') or f.endswith('.joblib') for f in model_files):
                # Scikit-learn modeli
                try:
                    import joblib
                    sklearn_model = next((f for f in model_files if f.endswith('.pkl') or f.endswith('.joblib')), None)
                    if sklearn_model:
                        self.ai_model = joblib.load(os.path.join(self.model_path, sklearn_model))
                        self.model_type = 'sklearn'
                        self.logger.info(f"✅ Scikit-learn modeli yüklendi: {sklearn_model}")
                except ImportError:
                    self.logger.warning("⚠️ Joblib bulunamadı, model yüklenemedi")
            else:
                self.logger.info("🤖 Model dosyası bulunamadı, rule-based mode aktif")
                self.ai_model = None
                self.model_type = 'rule_based'
            self.logger.info(f"✅ AI Model hazır (CPU modu: {self.use_cpu})")
            self.logger.info(f"🎯 Confidence threshold: {self.confidence_threshold}")

        except Exception as e:
            self.logger.error(f"❌ AI Model yükleme hatası: {e}")
            self.ai_model = None

    def _predict_with_ai(self, sensor_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """AI model ile tahmin yap"""
        if not self.enabled or self.ai_model is None:
            return None

        try:
            # Burada AI model ile tahmin yapılır
            # Örnek veri işleme
            if self.debug_mode:
                self.logger.debug("🤖 AI tahmin yapılıyor...")

            # Şimdilik None dön
            return None

        except Exception as e:
            self.logger.error(f"❌ AI tahmin hatası: {e}")
            return None
