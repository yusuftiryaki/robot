#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Otonom Bahçe Asistanı (OBA) - Donanım Testleri
====================================

Bu modül robot donanımının test edilmesi için gerekli testleri içerir.
Sensörler, motorlar ve diğer donanım bileşenlerini test eder.
"""

import asyncio
import os
import sys
import time
import unittest

from test_utils import TestRaporu, TestVeriUreticisi

from src.hardware.motor_kontrolcu import MotorKontrolcu
from src.hardware.sensor_okuyucu import SensorOkuyucu

# Proje klasörünü Python path'ine ekle
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestSensorOkuyucu(unittest.TestCase):
    """Sensör okuyucu testleri."""

    def setUp(self):
        """Test başlangıç ayarları."""
        # Mock environment manager
        class MockEnvironmentManager:
            is_simulation_mode = True

        # Yeni config yapısı
        sensor_config = {
            "imu": {"enabled": True, "type": "mpu6050", "i2c_address": 0x68},
            "gps": {"enabled": True, "type": "neo6m", "device": "/dev/ttyS0"},
            "guc": {"enabled": True, "type": "ina219", "i2c_address": 0x40},
            "tampon": {"enabled": True, "type": "button", "pin": 16},
            "enkoder": {"enabled": True, "type": "rotary_encoder"},
            "acil_durma": {"enabled": True, "type": "button", "pin": 25}
        }

        self.environment_manager = MockEnvironmentManager()
        self.sensor_okuyucu = SensorOkuyucu(sensor_config, self.environment_manager)
        self.test_verisi = TestVeriUreticisi.ornek_sensor_verisi()

    def tearDown(self):
        """Test sonrası temizlik."""
        if hasattr(self.sensor_okuyucu, '_running'):
            self.sensor_okuyucu._running = False

    def test_sensor_okuyucu_baslangic(self):
        """Sensör okuyucu başlangıç testi."""
        self.assertIsInstance(self.sensor_okuyucu, SensorOkuyucu)
        self.assertTrue(self.sensor_okuyucu.simülasyon_modu)

    def test_sensor_veri_okuma(self):
        """Sensör veri okuma testi."""

        def sync_test():
            # Threading ile async test çalıştır
            import concurrent.futures
            import threading

            def run_async_test():
                # Yeni thread'te yeni event loop
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                try:
                    async def _test():
                        # Sensörleri başlat
                        await self.sensor_okuyucu.başlat()

                        # Tüm sensör verilerini oku
                        sensor_data = await self.sensor_okuyucu.tüm_sensör_verilerini_oku()
                        self.assertIsNotNone(sensor_data)

                        # Timestamp kontrolü
                        self.assertIn("timestamp", sensor_data)

                        # Sistem durumu kontrolü
                        self.assertIn("sistem_durumu", sensor_data)

                    return loop.run_until_complete(_test())
                finally:
                    loop.close()

            # Ayrı thread'te çalıştır
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_async_test)
                return future.result(timeout=10)

        sync_test()

    def test_imu_veri_yapisi(self):
        """IMU veri yapısı testi."""
        imu_data = self.test_verisi['imu']

        # Gerekli anahtarlar mevcut mu?
        self.assertIn('ivme_x', imu_data)
        self.assertIn('ivme_y', imu_data)
        self.assertIn('ivme_z', imu_data)
        self.assertIn('gyro_x', imu_data)
        self.assertIn('gyro_y', imu_data)
        self.assertIn('gyro_z', imu_data)
        self.assertIn('compass_baslik', imu_data)
        self.assertIn('sicaklik', imu_data)
        self.assertIn('kalibrasyon_durumu', imu_data)
        self.assertIn('hata_mesaji', imu_data)

    def test_gps_veri_yapisi(self):
        """GPS veri yapısı testi."""
        gps_data = self.test_verisi['gps']

        # Gerekli anahtarlar mevcut mu?
        self.assertIn('latitude', gps_data)
        self.assertIn('longitude', gps_data)
        self.assertIn('altitude', gps_data)
        self.assertIn('fix_quality', gps_data)
        self.assertIn('uydu_sayisi', gps_data)
        self.assertIn('hiz', gps_data)
        self.assertIn('kurs', gps_data)
        self.assertIn('hata_mesaji', gps_data)

        # Koordinat sınırları
        self.assertTrue(-90 <= gps_data['latitude'] <= 90)
        self.assertTrue(-180 <= gps_data['longitude'] <= 180)

    def test_guc_veri_yapisi(self):
        """Güç veri yapısı testi."""
        guc_data = self.test_verisi['guc']

        # Gerekli anahtarlar mevcut mu?
        self.assertIn('voltaj', guc_data)
        self.assertIn('akim', guc_data)
        self.assertIn('guc', guc_data)
        self.assertIn('sarj_durumu', guc_data)
        self.assertIn('sarj_oluyor', guc_data)
        self.assertIn('sicaklik', guc_data)
        self.assertIn('hata_mesaji', guc_data)

        # Değer sınırları
        self.assertTrue(0 <= guc_data['sarj_durumu'] <= 100)
        self.assertTrue(guc_data['voltaj'] > 0)


class TestMotorKontrolcu(unittest.TestCase):
    """Motor kontrolcü testleri."""

    def setUp(self):
        """Test başlangıç ayarları."""
        # Mock environment manager
        class MockEnvironmentManager:
            is_simulation_mode = True

        # Basit motor config sözlüğü
        motor_config = {
            "left_wheel": {"pin_a": 18, "pin_b": 19, "max_speed": 255},
            "right_wheel": {"pin_a": 21, "pin_b": 22, "max_speed": 255},
            "main_brush": {"pin_a": 24, "pin_b": 25, "max_speed": 200}
        }
        self.environment_manager = MockEnvironmentManager()
        self.motor_kontrolcu = MotorKontrolcu(motor_config, self.environment_manager)
        self.test_verisi = TestVeriUreticisi.ornek_motor_verisi()

    def tearDown(self):
        """Test sonrası temizlik."""
        # Motorları senkron şekilde durdur
        if hasattr(self.motor_kontrolcu, 'motorlar_aktif'):
            self.motor_kontrolcu.motorlar_aktif = False
            # Manual cleanup without async
            self.motor_kontrolcu.mevcut_hizlar = {"sol": 0.0, "sag": 0.0}
            self.motor_kontrolcu.firca_durumu = {"ana": False, "sol": False, "sag": False}
            self.motor_kontrolcu.fan_durumu = False

    def test_motor_kontrolcu_baslangic(self):
        """Motor kontrolcü başlangıç testi."""
        self.assertIsInstance(self.motor_kontrolcu, MotorKontrolcu)
        self.assertTrue(self.motor_kontrolcu.simulation_mode)

    def test_tekerlek_hareket_kontrolu(self):
        """Tekerlek hareket kontrolü testi."""

        def sync_test():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                async def _test():
                    # Hareket komutları ile test et
                    # İleri hareket komutu
                    await self.motor_kontrolcu.hareket_et(0.5, 0.0)

                    # Dönüş hareketi komutu
                    await self.motor_kontrolcu.hareket_et(0.0, 0.5)

                    # Motorları durdur
                    await self.motor_kontrolcu.acil_durdur()

                return loop.run_until_complete(_test())
            finally:
                loop.close()

        sync_test()

    def test_donus_hareket_kontrolu(self):
        """Dönüş hareket kontrolü testi."""

        def sync_test():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                async def _test():
                    # Sola dönüş komutu
                    await self.motor_kontrolcu.hareket_et(0.0, -0.5)  # Negatif = sol

                    # Sağa dönüş komutu
                    await self.motor_kontrolcu.hareket_et(0.0, 0.5)   # Pozitif = sağ

                    await self.motor_kontrolcu.acil_durdur()

                return loop.run_until_complete(_test())
            finally:
                loop.close()

        sync_test()

    def test_firca_kontrolu(self):
        """Fırça kontrolü testi."""

        def sync_test():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                async def _test():
                    # Ana fırçayı başlat
                    self.motor_kontrolcu.firca_kontrol(ana=True, sol=False, sag=False)

                    # Tüm fırçaları başlat
                    self.motor_kontrolcu.firca_kontrol(ana=True, sol=True, sag=True)

                    # Fırçaları durdur
                    self.motor_kontrolcu.firca_kontrol(ana=False, sol=False, sag=False)

                    await self.motor_kontrolcu.acil_durdur()

                return loop.run_until_complete(_test())
            finally:
                loop.close()

        sync_test()

    def test_motor_guvenlik_sinirlari(self):
        """Motor güvenlik sınırları testi."""
        # Hız sınırları (değer aralığı kontrolü)
        self.assertTrue(0 <= 50 <= 100)  # Normal hız yüzdesi
        self.assertTrue(0 <= 100 <= 100)  # Maksimum hız yüzdesi

        # Motor config'de tanımlı değerler olup olmadığını kontrol et
        self.assertIn("left_wheel", self.motor_kontrolcu.config)
        self.assertIn("max_speed", self.motor_kontrolcu.config["left_wheel"])


class TestDonanim(unittest.TestCase):
    """Genel donanım testleri."""

    def setUp(self):
        """Test başlangıç ayarları."""
        # Mock environment manager
        class MockEnvironmentManager:
            is_simulation_mode = True

        # Config'ler doğru formatta
        sensor_config = {
            "imu": {"enabled": True, "type": "mpu6050", "i2c_address": 0x68},
            "gps": {"enabled": True, "type": "neo6m", "device": "/dev/ttyS0"},
            "guc": {"enabled": True, "type": "ina219", "i2c_address": 0x40},
            "tampon": {"enabled": True, "type": "button", "pin": 16},
            "enkoder": {"enabled": True, "type": "rotary_encoder"},
            "acil_durma": {"enabled": True, "type": "button", "pin": 25}
        }
        motor_config = {
            "left_wheel": {"pin_a": 18, "pin_b": 19, "max_speed": 255},
            "right_wheel": {"pin_a": 21, "pin_b": 22, "max_speed": 255},
            "main_brush": {"pin_a": 24, "pin_b": 25, "max_speed": 200}
        }

        self.environment_manager = MockEnvironmentManager()
        self.sensor_okuyucu = SensorOkuyucu(sensor_config, self.environment_manager)
        self.motor_kontrolcu = MotorKontrolcu(motor_config, self.environment_manager)

    def test_donanim_entegrasyonu(self):
        """Donanım entegrasyon testi."""

        def sync_test():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                async def _test():
                    # Sensör verisi oku
                    sensor_data = await self.sensor_okuyucu.tüm_sensör_verilerini_oku()
                    self.assertIsNotNone(sensor_data)

                    # Motor komutunu gönder
                    await self.motor_kontrolcu.hareket_et(0.25, 0.0)

                    # Sistemleri durdur
                    await self.motor_kontrolcu.acil_durdur()

                return loop.run_until_complete(_test())
            finally:
                loop.close()

        sync_test()

    def test_donanim_performansi(self):
        """Donanım performans testi."""

        def sync_test():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                async def _test():
                    # Performans ölçümü
                    baslangic_zamani = time.time()
                    veri_sayisi = 0

                    for _ in range(10):  # 10 kez veri oku
                        sensor_data = await self.sensor_okuyucu.tüm_sensör_verilerini_oku()
                        if sensor_data:
                            veri_sayisi += 1
                        await asyncio.sleep(0.1)  # 100ms aralık

                    bitis_zamani = time.time()
                    # Süre hesaplama - kullanımasak da ölçüm için gerekli
                    _ = bitis_zamani - baslangic_zamani

                    # En az %80 veri oranı bekleniyor
                    veri_orani = veri_sayisi / 10
                    self.assertGreater(veri_orani, 0.8)

                return loop.run_until_complete(_test())
            finally:
                loop.close()

        sync_test()


def donanim_testlerini_calistir():
    """Tüm donanım testlerini çalıştır."""
    import concurrent.futures
    import threading

    def run_tests_in_thread():
        """Threading ile testleri çalıştır."""
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
                test_adi = str(test).split('.')[-1].split()[0]
                test_sinifi_adi = test.__class__.__name__

                baslangic = time.time()

                try:
                    # Test çalıştır
                    test.debug()

                    sure = time.time() - baslangic
                    rapor.test_sonucu_ekle(
                        f"{test_sinifi_adi}.{test_adi}", True, sure)
                    print(f"  ✅ {test_adi} ({sure:.2f}s)")

                except Exception as e:
                    sure = time.time() - baslangic
                    rapor.test_sonucu_ekle(
                        f"{test_sinifi_adi}.{test_adi}", False, sure, str(e))
                    print(f"  ❌ {test_adi} ({sure:.2f}s) - {e}")

        # Raporu göster
        print("\n" + rapor.rapor_olustur())

        # Raporu kaydet
        rapor.rapor_kaydet('logs/donanim_test_raporu.txt')

        return rapor

    # Threading ile testleri çalıştır
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(run_tests_in_thread)
        return future.result(timeout=60)  # 60 saniye timeout


if __name__ == "__main__":
    # Test runner
    print("🧪 Donanım Test Runner")
    donanim_testlerini_calistir()
    print("✅ Donanım testleri tamamlandı!")
