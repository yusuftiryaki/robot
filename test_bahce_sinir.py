#!/usr/bin/env python3
"""
🏡 Bahçe Sınır Kontrol Sistemi Test Dosyası
Hacı Abi'nin güvenli biçme testleri!
"""

import math
import unittest

from src.navigation.bahce_sinir_kontrol import BahceSinirKontrol, KoordinatNoktasi


class TestBahceSinirKontrol(unittest.TestCase):
    """Bahçe sınır kontrol sistemi testleri"""

    def setUp(self):
        """Test için örnek konfigurasyon"""
        self.test_config = {
            "boundary_coordinates": [
                {"latitude": 39.933500, "longitude": 32.859500},  # Kuzey-batı
                {"latitude": 39.933600, "longitude": 32.859900},  # Kuzey-doğu
                {"latitude": 39.933300, "longitude": 32.859850},  # Güney-doğu
                {"latitude": 39.933200, "longitude": 32.859450}   # Güney-batı
            ],
            "boundary_safety": {
                "buffer_distance": 1.0,
                "warning_distance": 2.0,
                "max_deviation": 0.5,
                "check_frequency": 10
            }
        }

        self.sinir_kontrol = BahceSinirKontrol(self.test_config)

    def test_koordinat_yukleme(self):
        """Koordinat yükleme testleri"""
        self.assertEqual(len(self.sinir_kontrol.boundary_points), 4)
        self.assertAlmostEqual(self.sinir_kontrol.boundary_points[0].latitude, 39.933500, places=6)
        self.assertAlmostEqual(self.sinir_kontrol.boundary_points[0].longitude, 32.859500, places=6)

    def test_polygon_icinde_kontrol(self):
        """Point-in-polygon test"""
        # Bahçe merkezi (içinde olmalı)
        merkez = self.sinir_kontrol.get_boundary_center()
        self.assertTrue(self.sinir_kontrol._point_in_polygon(merkez))

        # Bahçe dışında bir nokta
        dis_nokta = KoordinatNoktasi(39.934000, 32.860000)  # Çok uzak
        self.assertFalse(self.sinir_kontrol._point_in_polygon(dis_nokta))

    def test_mesafe_hesaplama(self):
        """Haversine mesafe hesaplama testi"""
        nokta1 = KoordinatNoktasi(39.933500, 32.859500)
        nokta2 = KoordinatNoktasi(39.933600, 32.859900)

        mesafe = self.sinir_kontrol._haversine_distance(
            nokta1.latitude, nokta1.longitude,
            nokta2.latitude, nokta2.longitude
        )

        # Yaklaşık 30-40 metre olmalı
        self.assertGreater(mesafe, 20)
        self.assertLess(mesafe, 50)

    def test_guvenli_bolge_kontrolu(self):
        """Güvenli bölge kontrolü testi"""
        # Bahçe merkezi - güvenli olmalı
        merkez = self.sinir_kontrol.get_boundary_center()
        sonuc = self.sinir_kontrol.robot_konumunu_kontrol_et(
            merkez.latitude, merkez.longitude
        )

        self.assertTrue(sonuc.guvenli_bolgede)
        self.assertEqual(sonuc.uyari_seviyesi, "güvenli")

    def test_sinir_ihlali(self):
        """Sınır ihlali testi"""
        # Sınır dışında bir nokta
        dis_nokta = KoordinatNoktasi(39.934000, 32.860000)
        sonuc = self.sinir_kontrol.robot_konumunu_kontrol_et(
            dis_nokta.latitude, dis_nokta.longitude
        )

        self.assertFalse(sonuc.guvenli_bolgede)
        self.assertEqual(sonuc.uyari_seviyesi, "tehlike")
        self.assertIsNotNone(sonuc.onerilenen_yon)

    def test_alan_hesaplama(self):
        """Bahçe alan hesaplama testi"""
        alan = self.sinir_kontrol.bahce_alani

        # Alan pozitif olmalı
        self.assertGreater(alan, 0)

        # Makul bir alan olmalı (birkaç bin m²)
        self.assertGreater(alan, 100)
        self.assertLess(alan, 10000)

    def test_istatistikler(self):
        """İstatistik takibi testi"""
        # Birkaç kontrol yap
        merkez = self.sinir_kontrol.get_boundary_center()

        for _ in range(5):
            self.sinir_kontrol.robot_konumunu_kontrol_et(
                merkez.latitude, merkez.longitude
            )

        stats = self.sinir_kontrol.get_boundary_stats()

        self.assertEqual(stats["toplam_kontrol"], 5)
        self.assertEqual(stats["sinir_ihlali"], 0)
        self.assertEqual(stats["ihlal_orani"], 0.0)

    def test_web_verisi_hazirla(self):
        """Web arayüzü için veri hazırlama testi"""
        web_verisi = self.sinir_kontrol.visualize_boundary_for_web()

        self.assertIn("boundary_points", web_verisi)
        self.assertIn("center", web_verisi)
        self.assertIn("area", web_verisi)
        self.assertIn("buffer_distance", web_verisi)

        # 4 sınır noktası olmalı
        self.assertEqual(len(web_verisi["boundary_points"]), 4)

        # Merkez koordinatları makul olmalı
        center = web_verisi["center"]
        self.assertAlmostEqual(center["lat"], 39.933400, places=4)
        self.assertAlmostEqual(center["lon"], 32.859687, places=4)


def run_boundary_tests():
    """Bahçe sınır testlerini çalıştır"""
    print("🏡 Bahçe Sınır Kontrol Testleri Başlatılıyor...")
    print("=" * 50)

    # Test suite oluştur
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBahceSinirKontrol)

    # Test çalıştır
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("=" * 50)
    if result.wasSuccessful():
        print("✅ Tüm bahçe sınır testleri başarılı!")
        return True
    else:
        print("❌ Bazı testler başarısız oldu!")
        return False


if __name__ == "__main__":
    run_boundary_tests()
    run_boundary_tests()
