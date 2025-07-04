#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Otonom Bahçe Asistanı (OBA) - Donanım Testleri
====================================

Bu modül robot donanımının test edilmesi için gerekli testleri içerir.
Sensörler, motorlar ve diğer donanım bileşenlerini test eder.
"""

from hardware.sensor_okuyucu import SensorOkuyucu
from hardware.motor_kontrolcu import MotorKontrolcu
from test_utils import TestRaporu, TestVeriUreticisi, TestYardimcilari
import asyncio
import os
import sys
import time
import unittest
from unittest.mock import Mock, patch

# Proje klasörünü Python path'ine ekle
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestSensorOkuyucu(unittest.TestCase):
    """Sensör okuyucu testleri."""

    def setUp(self):
        """Test başlangıç ayarları."""
        self.sensor_okuyucu = SensorOkuyucu(simulation_mode=True)
        self.test_verisi = TestVeriUreticisi.ornek_sensor_verisi()

    def tearDown(self):
        """Test sonrası temizlik."""
        if hasattr(self.sensor_okuyucu, '_running'):
            self.sensor_okuyucu._running = False

    def test_sensor_okuyucu_baslangic(self):
        """Sensör okuyucu başlangıç testi."""
        self.assertIsInstance(self.sensor_okuyucu, SensorOkuyucu)
        self.assertTrue(self.sensor_okuyucu.simulation_mode)

    def test_sensor_veri_okuma(self):
        """Sensör veri okuma testi."""
        async def _test():
            # Sensör okuyucuyu başlat
            await self.sensor_okuyucu.basla()

            # Kısa bir süre bekle
            await asyncio.sleep(0.5)

            # Veri okunmuş mu kontrol et
            sensor_data = self.sensor_okuyucu.son_veriyi_al()
            self.assertIsNotNone(sensor_data)

            # Veri yapısını kontrol et
            self.assertTrue(
                TestYardimcilari.assert_sensor_data_valid(sensor_data)
            )

            # Sensör okuyucuyu durdur
            await self.sensor_okuyucu.durdur()

        # Async test çalıştır
        asyncio.run(_test())

    def test_imu_veri_yapisi(self):
        """IMU veri yapısı testi."""
        imu_data = self.test_verisi['imu']

        # Gerekli anahtarlar mevcut mu?
        self.assertIn('ivme', imu_data)
        self.assertIn('gyro', imu_data)
        self.assertIn('compass', imu_data)

        # İvme verisi
        ivme = imu_data['ivme']
        self.assertIn('x', ivme)
        self.assertIn('y', ivme)
        self.assertIn('z', ivme)

        # Gyro verisi
        gyro = imu_data['gyro']
        self.assertIn('x', gyro)
        self.assertIn('y', gyro)
        self.assertIn('z', gyro)

    def test_gps_veri_yapisi(self):
        """GPS veri yapısı testi."""
        gps_data = self.test_verisi['gps']

        # Gerekli anahtarlar mevcut mu?
        self.assertIn('latitude', gps_data)
        self.assertIn('longitude', gps_data)
        self.assertIn('altitude', gps_data)

        # Koordinat sınırları
        self.assertTrue(-90 <= gps_data['latitude'] <= 90)
        self.assertTrue(-180 <= gps_data['longitude'] <= 180)

    def test_batarya_veri_yapisi(self):
        """Batarya veri yapısı testi."""
        batarya_data = self.test_verisi['batarya']

        # Gerekli anahtarlar mevcut mu?
        self.assertIn('voltaj', batarya_data)
        self.assertIn('akim', batarya_data)
        self.assertIn('sarj_durumu', batarya_data)

        # Değer sınırları
        self.assertTrue(0 <= batarya_data['sarj_durumu'] <= 100)
        self.assertTrue(batarya_data['voltaj'] > 0)


class TestMotorKontrolcu(unittest.TestCase):
    """Motor kontrolcü testleri."""

    def setUp(self):
        """Test başlangıç ayarları."""
        self.motor_kontrolcu = MotorKontrolcu(simulation_mode=True)
        self.test_verisi = TestVeriUreticisi.ornek_motor_verisi()

    def tearDown(self):
        """Test sonrası temizlik."""
        # Motorları durdur
        try:
            asyncio.run(self.motor_kontrolcu.tum_motorlari_durdur())
        except Exception:
            pass

    def test_motor_kontrolcu_baslangic(self):
        """Motor kontrolcü başlangıç testi."""
        self.assertIsInstance(self.motor_kontrolcu, MotorKontrolcu)
        self.assertTrue(self.motor_kontrolcu.simulation_mode)

    def test_tekerlek_hareket_kontrolu(self):
        """Tekerlek hareket kontrolü testi."""
        async def _test():
            # Motorları başlat
            await self.motor_kontrolcu.basla()

            # İleri hareket
            await self.motor_kontrolcu.tekerlek_hiz_ayarla(
                sol_hiz=50,
                sag_hiz=50,
                yon='ileri'
            )

            # Motor durumunu kontrol et
            durum = self.motor_kontrolcu.motor_durumunu_al()
            self.assertEqual(durum['sol_tekerlek']['hiz'], 50)
            self.assertEqual(durum['sag_tekerlek']['hiz'], 50)
            self.assertEqual(durum['sol_tekerlek']['yon'], 'ileri')

            # Geri hareket
            await self.motor_kontrolcu.tekerlek_hiz_ayarla(
                sol_hiz=30,
                sag_hiz=30,
                yon='geri'
            )

            durum = self.motor_kontrolcu.motor_durumunu_al()
            self.assertEqual(durum['sol_tekerlek']['yon'], 'geri')

            # Motorları durdur
            await self.motor_kontrolcu.tum_motorlari_durdur()

        asyncio.run(_test())

    def test_donus_hareket_kontrolu(self):
        """Dönüş hareket kontrolü testi."""
        async def _test():
            await self.motor_kontrolcu.basla()

            # Sola dönüş
            await self.motor_kontrolcu.donus_yap(
                aci=-90,  # Sola 90 derece
                hiz=30
            )

            # Sağa dönüş
            await self.motor_kontrolcu.donus_yap(
                aci=45,   # Sağa 45 derece
                hiz=25
            )

            await self.motor_kontrolcu.tum_motorlari_durdur()

        asyncio.run(_test())

    def test_firca_kontrolu(self):
        """Fırça kontrolü testi."""
        async def _test():
            await self.motor_kontrolcu.basla()

            # Fırçayı başlat
            await self.motor_kontrolcu.firca_kontrolu(
                aktif=True,
                hiz=75
            )

            durum = self.motor_kontrolcu.motor_durumunu_al()
            self.assertTrue(durum['firca']['aktif'])
            self.assertEqual(durum['firca']['hiz'], 75)

            # Fırçayı durdur
            await self.motor_kontrolcu.firca_kontrolu(aktif=False)

            durum = self.motor_kontrolcu.motor_durumunu_al()
            self.assertFalse(durum['firca']['aktif'])

            await self.motor_kontrolcu.tum_motorlari_durdur()

        asyncio.run(_test())

    def test_motor_guvenlik_sinirlari(self):
        """Motor güvenlik sınırları testi."""
        # Hız sınırları
        self.assertTrue(0 <= 50 <= 100)  # Normal hız
        self.assertTrue(0 <= 100 <= 100)  # Maksimum hız

        # Geçersiz değerler için test
        with self.assertRaises(ValueError):
            # Negatif hız
            asyncio.run(self.motor_kontrolcu.tekerlek_hiz_ayarla(-10, 50))

        with self.assertRaises(ValueError):
            # Çok yüksek hız
            asyncio.run(self.motor_kontrolcu.tekerlek_hiz_ayarla(150, 50))


class TestDonanim(unittest.TestCase):
    """Genel donanım testleri."""

    def setUp(self):
        """Test başlangıç ayarları."""
        self.sensor_okuyucu = SensorOkuyucu(simulation_mode=True)
        self.motor_kontrolcu = MotorKontrolcu(simulation_mode=True)

    def test_donanim_entegrasyonu(self):
        """Donanım entegrasyon testi."""
        async def _test():
            # Her iki sistemi de başlat
            await self.sensor_okuyucu.basla()
            await self.motor_kontrolcu.basla()

            # Kısa bir süre çalıştır
            await asyncio.sleep(1.0)

            # Sensör verisi geldi mi?
            sensor_data = self.sensor_okuyucu.son_veriyi_al()
            self.assertIsNotNone(sensor_data)

            # Motor kontrolü çalışıyor mu?
            await self.motor_kontrolcu.tekerlek_hiz_ayarla(25, 25)
            motor_durum = self.motor_kontrolcu.motor_durumunu_al()
            self.assertEqual(motor_durum['sol_tekerlek']['hiz'], 25)

            # Sistemleri durdur
            await self.motor_kontrolcu.tum_motorlari_durdur()
            await self.sensor_okuyucu.durdur()

        asyncio.run(_test())

    def test_donanim_performansi(self):
        """Donanım performans testi."""
        async def _test():
            await self.sensor_okuyucu.basla()

            # Performans ölçümü
            baslangic_zamani = time.time()
            veri_sayisi = 0

            for _ in range(50):
                sensor_data = self.sensor_okuyucu.son_veriyi_al()
                if sensor_data:
                    veri_sayisi += 1
                await asyncio.sleep(0.02)  # 50Hz

            bitis_zamani = time.time()
            # Süre hesaplama - kullanımasak da ölçüm için gerekli
            _ = bitis_zamani - baslangic_zamani

            # En az %80 veri oranı bekleniyor
            veri_orani = veri_sayisi / 50
            self.assertGreater(veri_orani, 0.8)

            await self.sensor_okuyucu.durdur()

        asyncio.run(_test())


async def donanim_testlerini_calistir():
    """Tüm donanım testlerini çalıştır."""
    rapor = TestRaporu()

    print("🔧 Donanım Testleri Başlıyor...")
    print("=" * 50)

    # Test sınıfları
    test_siniflari = [
        TestSensorOkuyucu,
        TestMotorKontrolcu,
        TestDonanim
    ]

    for test_sinifi in test_siniflari:
        print(f"\n📋 {test_sinifi.__name__} testleri...")

        # Test suite oluştur
        suite = unittest.TestLoader().loadTestsFromTestCase(test_sinifi)

        for test in suite:
            test_adi = test._testMethodName
            baslangic = time.time()

            try:
                # Async test mi kontrol et
                test_method = getattr(test, test_adi)
                if asyncio.iscoroutinefunction(test_method):
                    await test_method()
                else:
                    test_method()

                sure = time.time() - baslangic
                rapor.test_sonucu_ekle(
                    f"{test_sinifi.__name__}.{test_adi}", True, sure)
                print(f"  ✅ {test_adi} ({sure:.2f}s)")

            except Exception as e:
                sure = time.time() - baslangic
                rapor.test_sonucu_ekle(
                    f"{test_sinifi.__name__}.{test_adi}", False, sure, str(e))
                print(f"  ❌ {test_adi} ({sure:.2f}s) - {e}")

    # Raporu göster
    print("\n" + rapor.rapor_olustur())

    # Raporu kaydet
    rapor.rapor_kaydet('logs/donanim_test_raporu.txt')

if __name__ == "__main__":
    # Test runner
    print("🧪 Donanım Test Runner")
    asyncio.run(donanim_testlerini_calistir())
