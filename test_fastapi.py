#!/usr/bin/env python3
"""
🧪 FastAPI Server Test Script
Hacı Abi'nin FastAPI test aracı!

Usage:
    python test_fastapi.py
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.web.fastapi_server import FastAPIWebServer


class MockRobot:
    """Test için mock robot sınıfı"""

    def __init__(self):
        self.logger = logging.getLogger("MockRobot")
        self.motor_kontrolcu = MockMotorController()

    async def get_robot_data(self):
        """Mock robot data"""
        return {
            "timestamp": "2025-07-10T14:30:45.123456",
            "robot_status": {
                "state": "test_mode",
                "battery_level": 85,
                "position": {"x": 12.34, "y": 8.76, "heading": 45.2},
                "mission_progress": 67
            },
            "sensors": {
                "gps": {"latitude": 41.0082, "longitude": 28.9784, "satellites": 8},
                "imu": {"roll": 1.2, "pitch": -0.8, "yaw": 45.2},
                "battery": {"voltage": 12.8, "current": 2.1, "level": 85},
                "obstacles": []
            },
            "motors": {
                "left_speed": 0.35,
                "right_speed": 0.40,
                "brushes_active": True,
                "fan_active": False
            }
        }

    async def gorev_baslat(self):
        self.logger.info("🚀 Mock görev başlatıldı")

    async def gorev_durdur(self):
        self.logger.info("🛑 Mock görev durduruldu")

    async def acil_durdur(self):
        self.logger.info("🚨 Mock acil durdurma!")


class MockMotorController:
    """Test için mock motor controller"""

    def __init__(self):
        self.logger = logging.getLogger("MockMotorController")

    async def hareket_uygula(self, hareket_komutu):
        self.logger.info(f"🎮 Mock hareket: {hareket_komutu.linear_hiz}, {hareket_komutu.angular_hiz}")

    async def set_firca_durumu(self, aktif):
        self.logger.info(f"🧹 Mock fırça: {'AÇIK' if aktif else 'KAPALI'}")

    async def set_fan_durumu(self, aktif):
        self.logger.info(f"💨 Mock fan: {'AÇIK' if aktif else 'KAPALI'}")


class HareketKomut:
    """Mock hareket komutu sınıfı"""

    def __init__(self, linear_hiz: float, angular_hiz: float, sure: float = 0.1):
        self.linear_hiz = linear_hiz
        self.angular_hiz = angular_hiz
        self.sure = sure


def main():
    """Test script ana fonksiyonu"""

    # Logging setup
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger = logging.getLogger("FastAPITest")
    logger.info("🧪 FastAPI Server Test Başlıyor...")

    # Mock robot oluştur
    mock_robot = MockRobot()

    # Test config
    test_config = {
        'host': '127.0.0.1',
        'port': 8000,
        'debug': True
    }

    # FastAPI server oluştur
    try:
        server = FastAPIWebServer(mock_robot, test_config)

        logger.info("✅ FastAPI server oluşturuldu")
        logger.info("🌐 Test URLs:")
        logger.info("  - Ana sayfa: http://127.0.0.1:8000/")
        logger.info("  - API Docs: http://127.0.0.1:8000/docs")
        logger.info("  - Robot Status: http://127.0.0.1:8000/api/robot/status")
        logger.info("  - WebSocket: ws://127.0.0.1:8000/ws")
        logger.info("")
        logger.info("🧪 Server başlatılıyor... (Ctrl+C ile durdurun)")

        # Server'ı çalıştır
        server.run(host="127.0.0.1", port=8000, reload=True)

    except Exception as e:
        logger.error(f"❌ Test hatası: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
