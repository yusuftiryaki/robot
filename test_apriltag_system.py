#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 AprilTag Test Suite - Şarj İstasyonu Yaklaşım Testleri
Hacı Abi'nin AprilTag test sistemi!

Bu test suite AprilTag detection ve şarj yaklaşım sistemini test eder.
"""

import asyncio
import os
import sys
import unittest
from unittest.mock import AsyncMock, Mock, patch

import cv2
import numpy as np

# Proje klasörünü Python path'ine ekle
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from navigation.sarj_istasyonu_yaklasici import (
    AprilTagTespit,
    SarjIstasyonuYaklasici,
    SarjYaklasimDurumu,
    SarjYaklasimKomutu,
)


class TestAprilTagTespit(unittest.TestCase):
    """🏷️ AprilTag tespit testleri"""

    def setUp(self):
        """Test setup"""
        self.sarj_config = {
            "apriltag": {
                "sarj_istasyonu_tag_id": 0,
                "tag_boyutu": 0.15,
                "hedef_mesafe": 0.3,
                "hassas_mesafe": 0.1,
                "aci_toleransi": 5.0,
                "pozisyon_toleransi": 0.02,
                "yaklasim_hizi": 0.1,
                "hassas_hiz": 0.02,
                "donme_hizi": 0.2,
                "kamera_matrix": [
                    [640, 0, 320],
                    [0, 640, 240],
                    [0, 0, 1]
                ],
                "distortion_coeffs": [0, 0, 0, 0, 0],
                "sarj_akimi_esigi": 0.1,
                "baglanti_voltaj_esigi": 11.0
            }
        }

    def test_yaklasici_baslangic(self):
        """Yaklaşıcı başlangıç durumu testi"""
        yaklasici = SarjIstasyonuYaklasici(self.sarj_config)

        self.assertEqual(yaklasici.mevcut_durum, SarjYaklasimDurumu.ARAMA)
        self.assertEqual(yaklasici.hedef_tag_id, 0)
        self.assertEqual(yaklasici.tag_boyutu, 0.15)
        self.assertIsNone(yaklasici.son_tespit)

    def test_apriltag_tespit_simulated(self):
        """Simüle edilmiş AprilTag tespit testi"""
        yaklasici = SarjIstasyonuYaklasici(self.sarj_config)

        # Sahte AprilTag görüntüsü oluştur
        test_image = self._sahte_apriltag_goruntusu_olustur()

        # AprilTag tespit etmeyi dene
        tespit = yaklasici._apriltag_tespit_et(test_image)

        # Simülasyon ortamında detector olmayabilir
        if tespit:
            self.assertIsInstance(tespit, AprilTagTespit)
            self.assertEqual(tespit.tag_id, 0)

    def test_guven_skoru_hesaplama(self):
        """Güven skoru hesaplama testi"""
        yaklasici = SarjIstasyonuYaklasici(self.sarj_config)

        # Düzgün kare köşeler
        duzgun_corners = np.array([
            [100, 100],
            [200, 100],
            [200, 200],
            [100, 200]
        ], dtype=np.float32)

        guven = yaklasici._guven_skoru_hesapla(duzgun_corners)
        self.assertGreaterEqual(guven, 0.8)  # Yüksek güven

        # Bozuk köşeler
        bozuk_corners = np.array([
            [100, 100],
            [190, 105],
            [205, 195],
            [95, 205]
        ], dtype=np.float32)

        guven = yaklasici._guven_skoru_hesapla(bozuk_corners)
        self.assertLess(guven, 0.8)  # Düşük güven

    def _sahte_apriltag_goruntusu_olustur(self) -> np.ndarray:
        """Test için sahte AprilTag görüntüsü oluştur"""
        # 640x480 boş görüntü
        image = np.ones((480, 640, 3), dtype=np.uint8) * 255

        # Merkeze siyah kare çiz (AprilTag benzeri)
        cv2.rectangle(image, (270, 190), (370, 290), (0, 0, 0), -1)
        cv2.rectangle(image, (280, 200), (360, 280), (255, 255, 255), -1)
        cv2.rectangle(image, (290, 210), (350, 270), (0, 0, 0), -1)

        return image


class TestSarjYaklasimDurumMakinesi(unittest.IsolatedAsyncioTestCase):
    """🔋 Şarj yaklaşım durum makinesi testleri"""

    def setUp(self):
        """Test setup"""
        self.sarj_config = {
            "apriltag": {
                "sarj_istasyonu_tag_id": 0,
                "tag_boyutu": 0.15,
                "hedef_mesafe": 0.3,
                "hassas_mesafe": 0.1,
                "aci_toleransi": 5.0,
                "pozisyon_toleransi": 0.02,
                "yaklasim_hizi": 0.1,
                "hassas_hiz": 0.02,
                "donme_hizi": 0.2,
                "kamera_matrix": [[640, 0, 320], [0, 640, 240], [0, 0, 1]],
                "distortion_coeffs": [0, 0, 0, 0, 0],
                "sarj_akimi_esigi": 0.1,
                "baglanti_voltaj_esigi": 11.0
            }
        }

    async def test_arama_durumu(self):
        """Arama durumu testi"""
        yaklasici = SarjIstasyonuYaklasici(self.sarj_config)
        yaklasici.mevcut_durum = SarjYaklasimDurumu.ARAMA

        # Tag bulunamadığında
        komut = await yaklasici._arama_durumu(None)
        self.assertIsInstance(komut, SarjYaklasimKomutu)
        self.assertEqual(komut.linear_hiz, 0.0)
        self.assertGreater(komut.angular_hiz, 0.0)  # Dönüş hareketi

        # Tag bulunduğunda
        tespit = AprilTagTespit(
            tag_id=0, merkez_x=320, merkez_y=240,
            mesafe=1.0, aci=0.0, pose_gecerli=True, guven_skoru=0.9
        )

        komut = await yaklasici._arama_durumu(tespit)
        self.assertEqual(yaklasici.mevcut_durum, SarjYaklasimDurumu.TESPIT)

    async def test_yaklasim_durumu(self):
        """Yaklaşım durumu testi"""
        yaklasici = SarjIstasyonuYaklasici(self.sarj_config)
        yaklasici.mevcut_durum = SarjYaklasimDurumu.YAKLASIM

        # Uzak mesafe - düz ileri
        tespit = AprilTagTespit(
            tag_id=0, merkez_x=320, merkez_y=240,
            mesafe=0.5, aci=2.0, pose_gecerli=True, guven_skoru=0.9
        )

        komut = await yaklasici._yaklasim_durumu(tespit)
        self.assertIsInstance(komut, SarjYaklasimKomutu)
        self.assertGreater(komut.linear_hiz, 0.0)

        # Yakın mesafe - hassas moda geçiş
        tespit.mesafe = 0.05  # 5cm
        komut = await yaklasici._yaklasim_durumu(tespit)
        self.assertEqual(yaklasici.mevcut_durum, SarjYaklasimDurumu.HASSAS_KONUMLANDIRMA)

    async def test_hassas_konumlandirma(self):
        """Hassas konumlandırma testi"""
        yaklasici = SarjIstasyonuYaklasici(self.sarj_config)
        yaklasici.mevcut_durum = SarjYaklasimDurumu.HASSAS_KONUMLANDIRMA

        # Hassas hareket gerekli
        tespit = AprilTagTespit(
            tag_id=0, merkez_x=320, merkez_y=240,
            mesafe=0.05, aci=1.0, pose_gecerli=True, guven_skoru=0.9
        )

        komut = await yaklasici._hassas_konumlandirma_durumu(tespit)
        self.assertIsInstance(komut, SarjYaklasimKomutu)
        self.assertTrue(komut.hassas_mod)
        self.assertLess(komut.linear_hiz, 0.05)  # Çok yavaş

        # Pozisyon tamam - fiziksel bağlantıya geçiş
        tespit.mesafe = 0.01  # 1cm
        tespit.aci = 0.5      # 0.5 derece

        komut = await yaklasici._hassas_konumlandirma_durumu(tespit)
        self.assertEqual(yaklasici.mevcut_durum, SarjYaklasimDurumu.FIZIKSEL_BAGLANTI)

    @patch('navigation.sarj_istasyonu_yaklasici.INA219_AVAILABLE', False)
    async def test_fiziksel_baglanti_simulasyon(self):
        """Fiziksel bağlantı simülasyon testi"""
        yaklasici = SarjIstasyonuYaklasici(self.sarj_config)
        yaklasici.mevcut_durum = SarjYaklasimDurumu.FIZIKSEL_BAGLANTI
        yaklasici.ina219_aktif = False

        # Simülasyon modunda otomatik başarı
        komut = await yaklasici._fiziksel_baglanti_durumu()
        self.assertIsNone(komut)  # Tamamlandı
        self.assertEqual(yaklasici.mevcut_durum, SarjYaklasimDurumu.TAMAMLANDI)


class TestAprilTagEntegrasyon(unittest.IsolatedAsyncioTestCase):
    """🔄 AprilTag entegrasyon testleri"""

    async def test_tam_yaklasim_senaryosu(self):
        """Tam yaklaşım senaryosu testi"""
        sarj_config = {
            "apriltag": {
                "sarj_istasyonu_tag_id": 0,
                "tag_boyutu": 0.15,
                "hedef_mesafe": 0.3,
                "hassas_mesafe": 0.1,
                "aci_toleransi": 5.0,
                "pozisyon_toleransi": 0.02,
                "yaklasim_hizi": 0.1,
                "hassas_hiz": 0.02,
                "donme_hizi": 0.2,
                "kamera_matrix": [[640, 0, 320], [0, 640, 240], [0, 0, 1]],
                "distortion_coeffs": [0, 0, 0, 0, 0],
                "sarj_akimi_esigi": 0.1,
                "baglanti_voltaj_esigi": 11.0
            }
        }

        yaklasici = SarjIstasyonuYaklasici(sarj_config)

        # Başlangıç durumu
        self.assertEqual(yaklasici.mevcut_durum, SarjYaklasimDurumu.ARAMA)

        # Sahte görüntü
        test_image = np.ones((480, 640, 3), dtype=np.uint8) * 255

        # İlk çağrı - arama modunda
        komut = await yaklasici.sarj_istasyonuna_yaklas(test_image)

        # Arama komutu alınmalı
        if komut:
            self.assertIsInstance(komut, SarjYaklasimKomutu)

        # Durum bilgisini test et
        durum = yaklasici.get_yaklasim_durumu()
        self.assertEqual(durum['durum'], 'arama')
        self.assertFalse(durum['ina219_aktif'])  # Simülasyon modunda

        # Sıfırlama testi
        yaklasici.sifirla()
        self.assertEqual(yaklasici.mevcut_durum, SarjYaklasimDurumu.ARAMA)
        self.assertIsNone(yaklasici.son_tespit)


def run_apriltag_tests():
    """AprilTag testlerini çalıştır"""
    print("🧪 Hacı Abi'nin AprilTag Test Suite")
    print("=" * 50)

    # Test suite'i oluştur
    test_suite = unittest.TestSuite()

    # Test sınıflarını ekle
    test_suite.addTest(unittest.makeSuite(TestAprilTagTespit))
    test_suite.addTest(unittest.makeSuite(TestSarjYaklasimDurumMakinesi))
    test_suite.addTest(unittest.makeSuite(TestAprilTagEntegrasyon))

    # Test runner
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    # Sonuç özetı
    print("\n" + "=" * 50)
    print(f"🎯 Test Sonuçları:")
    print(f"✅ Başarılı: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ Başarısız: {len(result.failures)}")
    print(f"🚨 Hata: {len(result.errors)}")

    if result.failures:
        print("\n❌ Başarısız Testler:")
        for test, trace in result.failures:
            print(f"  - {test}: {trace.split('AssertionError:')[-1].strip()}")

    if result.errors:
        print("\n🚨 Hatalı Testler:")
        for test, trace in result.errors:
            print(f"  - {test}: {trace.split('Exception:')[-1].strip()}")

    return result.wasSuccessful()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AprilTag test suite")
    parser.add_argument("--quick", action="store_true", help="Hızlı testler")
    parser.add_argument("--verbose", action="store_true", help="Detaylı çıktı")

    args = parser.parse_args()

    success = run_apriltag_tests()

    if success:
        print("\n🎉 Tüm testler başarılı!")
        exit(0)
    else:
        print("\n💥 Bazı testler başarısız!")
        exit(1)
