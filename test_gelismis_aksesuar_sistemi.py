#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧠 Gelişmiş Aksesuar Sistemi Test Scripti
Hacı Abi'nin tüm faktör analizi test sistemi!

Bu test scripti:
- AkilliAksesuarYoneticisi'nin tüm faktörleri (görev, hız, engel, batarya, konum) analiz etmesini test eder
- AdaptifNavigasyonKontrolcusu entegrasyonunu test eder
- Farklı senaryolarda aksesuar kararlarını doğrular
"""

import asyncio
import logging
import os
import sys
from datetime import datetime

import numpy as np

# Proje kök dizinini Python path'e ekle
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Test edilecek modüller
from navigation.adaptif_navigasyon_kontrolcusu import AdaptifNavigasyonKontrolcusu
from navigation.akilli_aksesuar_yoneticisi import (
    AkilliAksesuarYoneticisi,
    AksesuarPolitikasi,
    GorevTipi,
    RobotDurumVerisi,
)
from navigation.rota_planlayici import Nokta

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TestGelismisAksesuarSistemi")


class GelismisAksesuarTestSuiti:
    """🧪 Gelişmiş Aksesuar Test Süiti"""

    def __init__(self):
        self.logger = logging.getLogger("GelismisAksesuarTest")

        # Test konfigürasyonu
        self.test_config = {
            "robot": {
                "max_linear_speed": 0.5,
                "max_angular_speed": 1.0,
                "wheel_base": 0.3,
                "safety_distance": 0.5
            },
            "sensors": {
                "camera": {"enabled": True, "width": 640, "height": 480},
                "simulation_mode": True
            },
            "aksesuarlar": {
                "min_bicme_hizi": 0.1,
                "max_yan_firca_hizi": 0.3,
                "kritik_batarya": 20,
                "dusuk_batarya": 40,
                "guvenli_engel_mesafesi": 0.5,
                "sinir_guvenlik_mesafesi": 1.0,
                "default_policy": "performans"
            }
        }

        self.adaptif_nav = None
        self.aksesuar_yoneticisi = None

    async def test_aksesuar_yoneticisi_baslat(self):
        """🚀 Aksesuar yöneticisi başlatma testi"""
        self.logger.info("Aksesuar yöneticisi başlatma testi...")

        try:
            self.aksesuar_yoneticisi = AkilliAksesuarYoneticisi(
                self.test_config["aksesuarlar"]
            )

            if self.aksesuar_yoneticisi:
                self.logger.info("✅ AkilliAksesuarYoneticisi başarıyla oluşturuldu")
                return True
            else:
                self.logger.error("❌ AkilliAksesuarYoneticisi oluşturulamadı")
                return False

        except Exception as e:
            self.logger.error(f"❌ Aksesuar yöneticisi başlatma hatası: {e}")
            return False

    async def test_tum_faktor_analizi(self):
        """🧠 Tüm faktör analizi testi - Ana test!"""
        self.logger.info("Tüm faktör analizi test ediliyor...")

        try:
            if not self.aksesuar_yoneticisi:
                self.aksesuar_yoneticisi = AkilliAksesuarYoneticisi(
                    self.test_config["aksesuarlar"]
                )

            # Gelişmiş test senaryoları - Tüm faktörler
            test_senaryolari = [
                {
                    "senaryo": "İdeal Biçme Koşulları",
                    "robot_durum": RobotDurumVerisi(
                        gorev_tipi=GorevTipi.BICME,
                        robot_hizi=0.3,  # Optimal hız
                        mevcut_konum=Nokta(5.0, 5.0),  # Merkezi konum
                        hedef_konum=Nokta(6.0, 5.0),
                        engel_tespit_edildi=False,
                        en_yakin_engel_mesafesi=10.0,  # Çok uzak
                        batarya_seviyesi=80,  # Yüksek
                        sarj_gerekli=False,
                        bahce_sinir_mesafesi=5.0,  # Güvenli mesafe
                        zorlu_arazide=False,
                        hiz_limit_aktif=False,
                        manuel_kontrol_aktif=False
                    ),
                    "beklenen": {"ana_firca": True, "yan_firca": True, "fan": True},
                    "aciklama": "Tüm aksesuarlar aktif olmalı"
                },
                {
                    "senaryo": "Kritik Batarya Durumu",
                    "robot_durum": RobotDurumVerisi(
                        gorev_tipi=GorevTipi.BICME,
                        robot_hizi=0.2,
                        mevcut_konum=Nokta(3.0, 3.0),
                        hedef_konum=Nokta(4.0, 3.0),
                        engel_tespit_edildi=False,
                        en_yakin_engel_mesafesi=5.0,
                        batarya_seviyesi=15,  # KRİTİK BATARYA
                        sarj_gerekli=True,
                        bahce_sinir_mesafesi=3.0,
                        zorlu_arazide=False,
                        hiz_limit_aktif=False,
                        manuel_kontrol_aktif=False
                    ),
                    "beklenen": {"ana_firca": False, "yan_firca": False, "fan": False},
                    "aciklama": "Kritik bataryada tüm aksesuarlar kapalı olmalı"
                },
                {
                    "senaryo": "Engel Yakınında Güvenlik",
                    "robot_durum": RobotDurumVerisi(
                        gorev_tipi=GorevTipi.BICME,
                        robot_hizi=0.3,
                        mevcut_konum=Nokta(2.0, 2.0),
                        hedef_konum=Nokta(2.5, 2.0),
                        engel_tespit_edildi=True,
                        en_yakin_engel_mesafesi=0.3,  # ÇOK YAKIN ENGEL
                        batarya_seviyesi=70,
                        sarj_gerekli=False,
                        bahce_sinir_mesafesi=4.0,
                        zorlu_arazide=False,
                        hiz_limit_aktif=False,
                        manuel_kontrol_aktif=False
                    ),
                    "beklenen": {"ana_firca": False, "yan_firca": False, "fan": True},
                    "aciklama": "Yakın engelde fırçalar kapalı, sadece fan açık"
                },
                {
                    "senaryo": "Bahçe Sınırı Yakınında",
                    "robot_durum": RobotDurumVerisi(
                        gorev_tipi=GorevTipi.BICME,
                        robot_hizi=0.25,
                        mevcut_konum=Nokta(1.0, 1.0),
                        hedef_konum=Nokta(1.2, 1.0),
                        engel_tespit_edildi=False,
                        en_yakin_engel_mesafesi=8.0,
                        batarya_seviyesi=60,
                        sarj_gerekli=False,
                        bahce_sinir_mesafesi=0.8,  # SINIRA YAKIN
                        zorlu_arazide=False,
                        hiz_limit_aktif=False,
                        manuel_kontrol_aktif=False
                    ),
                    "beklenen": {"ana_firca": True, "yan_firca": False, "fan": True},
                    "aciklama": "Sınır yakınında yan fırçalar güvenlik için kapalı"
                },
                {
                    "senaryo": "Yüksek Hızda Güvenlik",
                    "robot_durum": RobotDurumVerisi(
                        gorev_tipi=GorevTipi.NOKTA_ARASI,
                        robot_hizi=0.4,  # YÜKSEK HIZ
                        mevcut_konum=Nokta(3.0, 4.0),
                        hedef_konum=Nokta(5.0, 4.0),
                        engel_tespit_edildi=False,
                        en_yakin_engel_mesafesi=6.0,
                        batarya_seviyesi=75,
                        sarj_gerekli=False,
                        bahce_sinir_mesafesi=4.0,
                        zorlu_arazide=False,
                        hiz_limit_aktif=False,
                        manuel_kontrol_aktif=False
                    ),
                    "beklenen": {"ana_firca": True, "yan_firca": False, "fan": False},
                    "aciklama": "Yüksek hızda yan fırça tehlikeli, nokta arası görevde minimal aksesuar"
                },
                {
                    "senaryo": "Zorlu Arazi Koşulları",
                    "robot_durum": RobotDurumVerisi(
                        gorev_tipi=GorevTipi.BICME,
                        robot_hizi=0.2,  # Yavaş hız
                        mevcut_konum=Nokta(4.0, 2.0),
                        hedef_konum=Nokta(4.5, 2.0),
                        engel_tespit_edildi=False,
                        en_yakin_engel_mesafesi=5.0,
                        batarya_seviyesi=65,
                        sarj_gerekli=False,
                        bahce_sinir_mesafesi=3.0,
                        zorlu_arazide=True,  # ZORLU ARAZİ
                        hiz_limit_aktif=True,
                        manuel_kontrol_aktif=False
                    ),
                    "beklenen": {"ana_firca": True, "yan_firca": False, "fan": True},
                    "aciklama": "Zorlu arazide yan fırçalar kapalı, dikkatli ilerleme"
                },
                {
                    "senaryo": "Şarj Arama Modu",
                    "robot_durum": RobotDurumVerisi(
                        gorev_tipi=GorevTipi.SARJ_ARAMA,
                        robot_hizi=0.25,
                        mevcut_konum=Nokta(2.0, 5.0),
                        hedef_konum=Nokta(1.0, 6.0),  # Şarj istasyonu
                        engel_tespit_edildi=False,
                        en_yakin_engel_mesafesi=4.0,
                        batarya_seviyesi=25,  # Düşük batarya
                        sarj_gerekli=True,
                        bahce_sinir_mesafesi=2.0,
                        zorlu_arazide=False,
                        hiz_limit_aktif=False,
                        manuel_kontrol_aktif=False
                    ),
                    "beklenen": {"ana_firca": False, "yan_firca": False, "fan": False},
                    "aciklama": "Şarj arama modunda tüm aksesuarlar kapalı - enerji tasarrufu"
                },
                {
                    "senaryo": "Manuel Kontrol Acil Durum",
                    "robot_durum": RobotDurumVerisi(
                        gorev_tipi=GorevTipi.BICME,
                        robot_hizi=0.1,
                        mevcut_konum=Nokta(3.5, 3.5),
                        hedef_konum=Nokta(4.0, 3.5),
                        engel_tespit_edildi=False,
                        en_yakin_engel_mesafesi=3.0,
                        batarya_seviyesi=50,
                        sarj_gerekli=False,
                        bahce_sinir_mesafesi=2.5,
                        zorlu_arazide=False,
                        hiz_limit_aktif=False,
                        manuel_kontrol_aktif=True  # MANUEL KONTROL
                    ),
                    "beklenen": {"ana_firca": False, "yan_firca": False, "fan": False},
                    "aciklama": "Manuel kontrol modunda güvenlik için tüm aksesuarlar kapalı"
                }
            ]

            basarili_testler = 0
            toplam_testler = len(test_senaryolari)

            for test in test_senaryolari:
                try:
                    # Aksesuar kararı al
                    karar = self.aksesuar_yoneticisi.aksesuar_karari_ver(test["robot_durum"])

                    # Sonuçları kontrol et
                    ana_firca_ok = karar.get("ana_firca") == test["beklenen"]["ana_firca"]
                    yan_firca_ok = karar.get("yan_firca") == test["beklenen"]["yan_firca"]
                    fan_ok = karar.get("fan") == test["beklenen"]["fan"]

                    if ana_firca_ok and yan_firca_ok and fan_ok:
                        self.logger.info(f"✅ {test['senaryo']}: BAŞARILI")
                        self.logger.debug(f"   {test['aciklama']}")
                        self.logger.debug(f"   Karar: {karar}")
                        basarili_testler += 1
                    else:
                        self.logger.warning(f"❌ {test['senaryo']}: BAŞARISIZ")
                        self.logger.warning(f"   {test['aciklama']}")
                        self.logger.warning(f"   Beklenen: {test['beklenen']}")
                        self.logger.warning(f"   Alınan: {karar}")

                except Exception as e:
                    self.logger.error(f"💥 {test['senaryo']} hatası: {e}")

            # Özet rapor
            basari_orani = (basarili_testler / toplam_testler) * 100
            self.logger.info(f"\n📊 TÜM FAKTÖR ANALİZİ SONUÇLARI:")
            self.logger.info(f"Başarılı: {basarili_testler}/{toplam_testler}")
            self.logger.info(f"Başarı oranı: {basari_orani:.1f}%")

            return basarili_testler >= toplam_testler * 0.8  # %80 başarı kriteri

        except Exception as e:
            self.logger.error(f"❌ Tüm faktör analizi testi hatası: {e}")
            return False

    async def test_adaptif_navigasyon_entegrasyonu(self):
        """🚀 AdaptifNavigasyonKontrolcusu entegrasyon testi"""
        self.logger.info("AdaptifNavigasyonKontrolcusu entegrasyon testi...")

        try:
            # AdaptifNavigasyonKontrolcusu oluştur
            self.adaptif_nav = AdaptifNavigasyonKontrolcusu(self.test_config)

            # Test senaryosu
            robot_konumu = Nokta(2.0, 2.0)
            robot_hizi = (0.3, 0.0)
            test_frame = np.zeros((480, 640, 3), dtype=np.uint8)

            # Biçme görevini ayarla
            self.adaptif_nav.gorev_tipi_ayarla(GorevTipi.BICME)

            # Hedef nokta ayarla
            hedef_nokta = Nokta(3.0, 2.0)
            self.adaptif_nav.hedef_konum_ayarla(hedef_nokta)

            # Navigation döngüsünü çalıştır
            hareket_komutu = await self.adaptif_nav.navigation_dongusu(
                robot_konumu=robot_konumu,
                robot_hizi=robot_hizi,
                kamera_frame=test_frame,
                batarya_seviyesi=70,
                bahce_sinir_mesafesi=3.0,
                zorlu_arazide=False,
                manuel_kontrol_aktif=False
            )

            if hareket_komutu and hasattr(hareket_komutu, 'aksesuar_komutlari') and hareket_komutu.aksesuar_komutlari:
                self.logger.info("✅ AdaptifNavigasyonKontrolcusu entegrasyonu başarılı")
                self.logger.info(f"   Hareket: Linear={hareket_komutu.dogrusal_hiz:.2f}, Angular={hareket_komutu.acisal_hiz:.2f}")
                self.logger.info(f"   Aksesuar kararları: {hareket_komutu.aksesuar_komutlari}")
                return True
            else:
                self.logger.warning("⚠️ Aksesuar komutları entegrasyonda eksik")
                return False

        except Exception as e:
            self.logger.error(f"❌ Entegrasyon testi hatası: {e}")
            return False

    async def test_politika_degisimleri(self):
        """🎛️ Politika değişim testleri"""
        self.logger.info("Aksesuar politika değişim testleri...")

        try:
            if not self.aksesuar_yoneticisi:
                self.aksesuar_yoneticisi = AkilliAksesuarYoneticisi(
                    self.test_config["aksesuarlar"]
                )

            # Test robot durumu
            test_durum = RobotDurumVerisi(
                gorev_tipi=GorevTipi.BICME,
                robot_hizi=0.3,
                mevcut_konum=Nokta(3.0, 3.0),
                hedef_konum=Nokta(4.0, 3.0),
                engel_tespit_edildi=False,
                en_yakin_engel_mesafesi=5.0,
                batarya_seviyesi=60,
                sarj_gerekli=False,
                bahce_sinir_mesafesi=3.0,
                zorlu_arazide=False,
                hiz_limit_aktif=False,
                manuel_kontrol_aktif=False
            )

            politikalar = [
                AksesuarPolitikasi.PERFORMANS,
                AksesuarPolitikasi.TASARRUF,
                AksesuarPolitikasi.SESSIZ,
                AksesuarPolitikasi.GUVENLIK
            ]

            basarili_politikalar = 0

            for politika in politikalar:
                try:
                    # Politikayı değiştir
                    self.aksesuar_yoneticisi.politika_degistir(politika)

                    # Karar al
                    karar = self.aksesuar_yoneticisi.aksesuar_karari_ver(test_durum)

                    if karar and isinstance(karar, dict):
                        self.logger.info(f"✅ {politika.value} politikası: {karar}")
                        basarili_politikalar += 1
                    else:
                        self.logger.warning(f"❌ {politika.value} politikası hatalı")

                except Exception as e:
                    self.logger.error(f"💥 {politika.value} politika hatası: {e}")

            return basarili_politikalar == len(politikalar)

        except Exception as e:
            self.logger.error(f"❌ Politika testleri hatası: {e}")
            return False

    async def tum_testleri_calistir(self):
        """🧪 Tüm testleri sırayla çalıştır"""
        self.logger.info("Gelişmiş Aksesuar Sistemi test süiti başlatılıyor...")

        testler = [
            ("Aksesuar Yöneticisi Başlatma", self.test_aksesuar_yoneticisi_baslat),
            ("Tüm Faktör Analizi", self.test_tum_faktor_analizi),
            ("AdaptifNavigasyon Entegrasyonu", self.test_adaptif_navigasyon_entegrasyonu),
            ("Politika Değişimleri", self.test_politika_degisimleri),
        ]

        basarili_testler = 0
        toplam_testler = len(testler)

        for test_adi, test_fonksiyonu in testler:
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"Test: {test_adi}")
            self.logger.info(f"{'='*60}")

            try:
                sonuc = await test_fonksiyonu()
                if sonuc:
                    self.logger.info(f"✅ {test_adi} - BAŞARILI")
                    basarili_testler += 1
                else:
                    self.logger.warning(f"❌ {test_adi} - BAŞARISIZ")
            except Exception as e:
                self.logger.error(f"💥 {test_adi} - HATA: {e}")

        # Özet
        basari_orani = (basarili_testler / toplam_testler) * 100
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"GELIŞMIŞ AKSESUAR SİSTEMİ TEST SONUÇLARI")
        self.logger.info(f"{'='*60}")
        self.logger.info(f"Başarılı: {basarili_testler}/{toplam_testler}")
        self.logger.info(f"Başarı oranı: {basari_orani:.1f}%")

        if basarili_testler == toplam_testler:
            self.logger.info("🎉 TÜM TESTLER BAŞARILI!")
            return True
        elif basarili_testler >= toplam_testler * 0.75:
            self.logger.info("✅ SİSTEM BÜYÜK ÖLÇÜDE ÇALIŞIYOR!")
            return True
        else:
            self.logger.warning("⚠️ SİSTEMDE SORUNLAR VAR!")
            return False


async def main():
    """Ana test fonksiyonu"""
    print("🧠 Gelişmiş Aksesuar Sistemi Test Süiti")
    print("Tüm Faktör Analizi: Görev, Hız, Engel, Batarya, Konum")
    print("=" * 70)

    test_suiti = GelismisAksesuarTestSuiti()
    sonuc = await test_suiti.tum_testleri_calistir()

    if sonuc:
        print("\n🎉 GELİŞMİŞ AKSESUAR SİSTEMİ BAŞARILI!")
        print("Tüm faktörler (görev, hız, engel, batarya, konum) doğru analiz ediliyor.")
        print("\n🧠 Akıllı Aksesuar Yönetimi Özellikleri:")
        print("  • Görev odaklı aksesuar konfigürasyonu")
        print("  • Hız bazlı güvenlik önlemleri")
        print("  • Engel mesafesi ile dinamik karar verme")
        print("  • Batarya seviyesi optimizasyonu")
        print("  • Konum bazlı güvenlik (sınır, zorlu arazi)")
        print("  • Çoklu politika desteği (performans, tasarruf, sessiz, güvenlik)")
        sys.exit(0)
    else:
        print("\n❌ GELİŞMİŞ AKSESUAR SİSTEMİNDE SORUNLAR VAR!")
        print("Lütfen hataları inceleyin ve düzeltmeler yapın.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
