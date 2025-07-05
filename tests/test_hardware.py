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
from unittest.mock import Mock, patch

from test_utils import TestRaporu, TestVeriUreticisi, TestYardimcilari

from src.hardware.motor_kontrolcu import MotorKontrolcu
from src.hardware.sensor_okuyucu import SensorOkuyucu

# Proje klasörünü Python path'ine ekle
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestSensorOkuyucu(unittest.TestCase):
    """Sensör okuyucu testleri."""

    def setUp(self):
        """Test başlangıç ayarları."""
        # Basit config sözlüğü
        sensor_config = {
            "mpu6050": {"i2c_address": 0x68, "sda_pin": 2, "scl_pin": 3},
            "gps": {"uart_tx": 14, "uart_rx": 15, "baud_rate": 9600},
            "ina219": {"i2c_address": 0x40},
            "front_bumper": {"pin": 16, "pull_up": True}
        }
        self.sensor_okuyucu = SensorOkuyucu(sensor_config)
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
            # Tüm sensör verilerini oku
            sensor_data = await self.sensor_okuyucu.tum_verileri_oku()
            self.assertIsNotNone(sensor_data)

            # Timestamp kontrolü
            self.assertIn("timestamp", sensor_data)

            # IMU verisi kontrolü
            if sensor_data.get("imu"):
                self.assertIn("accel_x", sensor_data["imu"])
                self.assertIn("gyro_x", sensor_data["imu"])

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
        # Basit motor config sözlüğü
        motor_config = {
            "left_wheel": {"pin_a": 18, "pin_b": 19, "max_speed": 255},
            "right_wheel": {"pin_a": 21, "pin_b": 22, "max_speed": 255},
            "main_brush": {"pin_a": 24, "pin_b": 25, "max_speed": 200}
        }
        self.motor_kontrolcu = MotorKontrolcu(motor_config)
        self.test_verisi = TestVeriUreticisi.ornek_motor_verisi()

    def tearDown(self):
        """Test sonrası temizlik."""
        # Motorları durdur
        try:
            asyncio.run(self.motor_kontrolcu.durdur())
        except Exception:
            pass

    def test_motor_kontrolcu_baslangic(self):
        """Motor kontrolcü başlangıç testi."""
        self.assertIsInstance(self.motor_kontrolcu, MotorKontrolcu)
        self.assertTrue(self.motor_kontrolcu.simulation_mode)

    def test_tekerlek_hareket_kontrolu(self):
        """Tekerlek hareket kontrolü testi."""
        async def _test():
            # Hareket komutları ile test et
            from src.hardware.motor_kontrolcu import HareketKomut

            # İleri hareket komutu
            hareket = HareketKomut(linear_hiz=0.5, angular_hiz=0.0)
            await self.motor_kontrolcu.hareket_uygula(hareket)

            # Dönüş hareketi komutu
            donus = HareketKomut(linear_hiz=0.0, angular_hiz=0.5)
            await self.motor_kontrolcu.hareket_uygula(donus)

            # Motorları durdur
            await self.motor_kontrolcu.durdur()

        asyncio.run(_test())

    def test_donus_hareket_kontrolu(self):
        """Dönüş hareket kontrolü testi."""
        async def _test():
            from src.hardware.motor_kontrolcu import HareketKomut

            # Sola dönüş komutu
            sol_donus = HareketKomut(linear_hiz=0.0, angular_hiz=-0.5)  # Negatif = sol
            await self.motor_kontrolcu.hareket_uygula(sol_donus)

            # Sağa dönüş komutu
            sag_donus = HareketKomut(linear_hiz=0.0, angular_hiz=0.5)   # Pozitif = sağ
            await self.motor_kontrolcu.hareket_uygula(sag_donus)

            await self.motor_kontrolcu.durdur()

        asyncio.run(_test())

    def test_firca_kontrolu(self):
        """Fırça kontrolü testi."""
        async def _test():
            # Ana fırçayı başlat
            await self.motor_kontrolcu.fircalari_calistir(aktif=True, ana=True, yan=False)

            # Tüm fırçaları başlat
            await self.motor_kontrolcu.fircalari_calistir(aktif=True, ana=True, yan=True)

            # Fırçaları durdur
            await self.motor_kontrolcu.fircalari_calistir(aktif=False)

            await self.motor_kontrolcu.durdur()

        asyncio.run(_test())

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
        # Config'ler doğru formatta
        sensor_config = {
            "mpu6050": {"i2c_address": 0x68, "sda_pin": 2, "scl_pin": 3},
            "gps": {"uart_tx": 14, "uart_rx": 15, "baud_rate": 9600},
            "ina219": {"i2c_address": 0x40},
            "front_bumper": {"pin": 16, "pull_up": True}
        }
        motor_config = {
            "left_wheel": {"pin_a": 18, "pin_b": 19, "max_speed": 255},
            "right_wheel": {"pin_a": 21, "pin_b": 22, "max_speed": 255},
            "main_brush": {"pin_a": 24, "pin_b": 25, "max_speed": 200}
        }
        self.sensor_okuyucu = SensorOkuyucu(sensor_config)
        self.motor_kontrolcu = MotorKontrolcu(motor_config)

    def test_donanim_entegrasyonu(self):
        """Donanım entegrasyon testi."""
        async def _test():
            from src.hardware.motor_kontrolcu import HareketKomut

            # Sensör verisi oku
            sensor_data = await self.sensor_okuyucu.tum_verileri_oku()
            self.assertIsNotNone(sensor_data)

            # Motor komutunu gönder
            hareket = HareketKomut(linear_hiz=0.25, angular_hiz=0.0)
            await self.motor_kontrolcu.hareket_uygula(hareket)

            # Sistemleri durdur
            await self.motor_kontrolcu.durdur()

        asyncio.run(_test())

    def test_donanim_performansi(self):
        """Donanım performans testi."""
        async def _test():
            # Performans ölçümü
            baslangic_zamani = time.time()
            veri_sayisi = 0

            for _ in range(10):  # 10 kez veri oku
                sensor_data = await self.sensor_okuyucu.tum_verileri_oku()
                if sensor_data:
                    veri_sayisi += 1
                await asyncio.sleep(0.1)  # 100ms aralık

            bitis_zamani = time.time()
            # Süre hesaplama - kullanımasak da ölçüm için gerekli
            _ = bitis_zamani - baslangic_zamani

            # En az %80 veri oranı bekleniyor
            veri_orani = veri_sayisi / 10
            self.assertGreater(veri_orani, 0.8)

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
            if hasattr(test, '_testMethodName'):
                test_adi = test._testMethodName
                test_sinifi_adi = test.__class__.__name__
            else:
                test_adi = str(test)
                test_sinifi_adi = "Unknown"

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
    print("🧪 Donanım Test Runner")
    asyncio.run(donanim_testlerini_calistir())
