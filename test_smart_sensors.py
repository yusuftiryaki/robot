#!/usr/bin/env python3
"""
🧠 Akıllı Sensör Simülasyonu Test Script
Hacı Abi'nin test sistemi!

Bu script robotun farklı durumlarında sensör verilerinin
nasıl değiştiğini test eder.
"""

import asyncio
import logging
import sys
import time
from pathlib import Path

# Proje kökünü path'e ekle
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from core.robot import BahceRobotu, RobotDurumu
from hardware.motor_kontrolcu import HareketKomut


async def test_akilli_simulasyon():
    """🧠 Akıllı simülasyon testleri"""

    # Logging setup
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger("AkilliSimulasyonTest")

    logger.info("🚀 Akıllı Sensör Simülasyonu Test Başlıyor!")
    logger.info("=" * 60)

    try:
        # Robot'u başlat
        robot = BahceRobotu()
        await asyncio.sleep(1)

        # Test 1: Bekleme Modu
        logger.info("🧪 TEST 1: Bekleme Modu Sensör Verileri")
        robot.durum_degistir(RobotDurumu.BEKLEME)
        await asyncio.sleep(0.5)

        sensor_data = await robot.sensor_verilerini_al()
        logger.info(f"📡 GPS: {sensor_data.get('gps', {}).get('latitude'):.6f}, {sensor_data.get('gps', {}).get('longitude'):.6f}")
        logger.info(f"📡 GPS Hız: {sensor_data.get('gps', {}).get('speed'):.2f} km/h")
        logger.info(f"🧭 IMU Roll: {sensor_data.get('imu', {}).get('roll'):.2f}°")
        logger.info(f"🔋 Batarya: {sensor_data.get('batarya', {}).get('level'):.1f}%")

        await asyncio.sleep(2)

        # Test 2: Hareket Modu
        logger.info("\n🧪 TEST 2: Hareket Modu Sensör Verileri")
        robot.durum_degistir(RobotDurumu.GOREV_YAPMA)

        # Hareket simülasyonu
        if robot.motor_kontrolcu:
            hareket = HareketKomut(linear_hiz=0.3, angular_hiz=0.1)
            await robot.motor_kontrolcu.hareket_uygula(hareket)

        await asyncio.sleep(1)

        sensor_data = await robot.sensor_verilerini_al()
        logger.info(f"📡 GPS: {sensor_data.get('gps', {}).get('latitude'):.6f}, {sensor_data.get('gps', {}).get('longitude'):.6f}")
        logger.info(f"📡 GPS Hız: {sensor_data.get('gps', {}).get('speed'):.2f} km/h")
        logger.info(f"🧭 IMU Roll: {sensor_data.get('imu', {}).get('roll'):.2f}°")
        logger.info(f"🔋 Batarya: {sensor_data.get('batarya', {}).get('level'):.1f}%")

        await asyncio.sleep(3)

        # Test 3: Şarj Modu
        logger.info("\n🧪 TEST 3: Şarj Modu Sensör Verileri")
        robot.durum_degistir(RobotDurumu.SARJ_OLMA)

        await asyncio.sleep(1)

        sensor_data = await robot.sensor_verilerini_al()
        logger.info(f"📡 GPS: {sensor_data.get('gps', {}).get('latitude'):.6f}, {sensor_data.get('gps', {}).get('longitude'):.6f}")
        logger.info(f"📡 GPS Hız: {sensor_data.get('gps', {}).get('speed'):.2f} km/h")
        logger.info(f"🧭 IMU Roll: {sensor_data.get('imu', {}).get('roll'):.2f}°")
        logger.info(f"🔋 Batarya: {sensor_data.get('batarya', {}).get('level'):.1f}%")
        logger.info(f"🔌 Batarya Voltage: {sensor_data.get('batarya', {}).get('voltage'):.2f}V")

        await asyncio.sleep(2)

        # Test 4: Tekrar Hareket
        logger.info("\n🧪 TEST 4: Tekrar Hareket - Konum Değişimi")
        robot.durum_degistir(RobotDurumu.GOREV_YAPMA)

        if robot.motor_kontrolcu:
            hareket = HareketKomut(linear_hiz=0.5, angular_hiz=0.3)
            await robot.motor_kontrolcu.hareket_uygula(hareket)

        # Konum değişimini gözlemle
        baslangic_pos = None
        for i in range(5):
            sensor_data = await robot.sensor_verilerini_al()
            current_pos = (sensor_data.get('gps', {}).get('latitude'),
                           sensor_data.get('gps', {}).get('longitude'))

            if baslangic_pos is None:
                baslangic_pos = current_pos
                logger.info(f"📍 Başlangıç pozisyonu: {current_pos[0]:.6f}, {current_pos[1]:.6f}")
            else:
                # Mesafe hesapla (yaklaşık)
                lat_diff = abs(current_pos[0] - baslangic_pos[0])
                lon_diff = abs(current_pos[1] - baslangic_pos[1])
                logger.info(f"📍 Pozisyon {i+1}: {current_pos[0]:.6f}, {current_pos[1]:.6f}")
                logger.info(f"📏 Değişim: lat={lat_diff:.6f}, lon={lon_diff:.6f}")

            await asyncio.sleep(1)

        # Test 5: Bekleme Moduna Geri Dön
        logger.info("\n🧪 TEST 5: Bekleme Moduna Geri Dönüş")
        robot.durum_degistir(RobotDurumu.BEKLEME)

        await asyncio.sleep(1)

        sensor_data = await robot.sensor_verilerini_al()
        logger.info(f"📡 GPS: {sensor_data.get('gps', {}).get('latitude'):.6f}, {sensor_data.get('gps', {}).get('longitude'):.6f}")
        logger.info(f"📡 GPS Hız: {sensor_data.get('gps', {}).get('speed'):.2f} km/h")
        logger.info(f"🧭 IMU Roll: {sensor_data.get('imu', {}).get('roll'):.2f}°")

        logger.info("\n✅ Tüm testler tamamlandı!")
        logger.info("=" * 60)

        # Robot'u kapat
        await robot.kapat()

    except Exception as e:
        logger.error(f"❌ Test hatası: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(test_akilli_simulasyon())
