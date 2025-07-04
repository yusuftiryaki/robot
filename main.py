#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Otonom Bahçe Asistanı (OBA) - Ana Başlatma Scripti
=================================================

Bu script bahçe asistanının ana başlatma noktasıdır.
Robot sistemini başlatır, web arayüzünü açar ve ana döngüyü çalıştırır.

Kullanım:
    python main.py [--debug] [--simulation] [--web-only]

Örnekler:
    python main.py                    # Normal mod
    python main.py --debug           # Debug modu
    python main.py --simulation      # Simülasyon modu
    python main.py --web-only        # Sadece web arayüzü
"""

import argparse
import asyncio
import logging
import os
import signal
import sys
from typing import Optional

# Python path'e src klasörünü ekle
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.guvenlik_sistemi import GuvenlikSistemi
from core.robot import BahceRobotu
from web.web_server import WebArayuz

# Logger ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/robot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class RobotUygulama:
    """
    Ana robot uygulaması sınıfı.

    Robot sistemini ve web arayüzünü yönetir.
    Graceful shutdown ve hata yönetimi sağlar.
    """

    def __init__(self, debug: bool = False, simulation: bool = False,
                 web_only: bool = False):
        """
        Robot uygulamasını başlat.

        Args:
            debug: Debug modu aktif mi?
            simulation: Simülasyon modu aktif mi?
            web_only: Sadece web arayüzü mi çalışsın?
        """
        self.debug = debug
        self.simulation = simulation
        self.web_only = web_only
        self.robot: Optional[BahceRobotu] = None
        self.web_server: Optional[WebArayuz] = None
        self.calisma_durumu = True

        # Debug modunda log seviyesini artır
        if debug:
            logging.getLogger().setLevel(logging.DEBUG)
            logger.debug("Debug modu aktif")

        # Log klasörünü oluştur
        os.makedirs('logs', exist_ok=True)

        # Signal handler'ları ayarla (Ctrl+C için)
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        logger.info(
            f"Robot uygulaması başlatılıyor - "
            f"Debug: {debug}, Simülasyon: {simulation}, Web-Only: {web_only}"
        )

    def _signal_handler(self, signum, frame):
        """Graceful shutdown için signal handler."""
        logger.info(f"Çıkış sinyali alındı: {signum}")
        self.calisma_durumu = False

        # Robot'un da ana döngüsünü durdur
        if self.robot:
            self.robot.calisma_durumu = False
            logger.info("🤖 Robot ana döngüsü durduruldu")

    async def robot_baslatma_kontrolu(self) -> bool:
        """
        Robotun başlatılmadan önce gerekli kontrolleri yap.

        Returns:
            bool: Robot başlatılabilir mi?
        """
        try:
            # Simülasyon modunda donanım kontrolü atlansın
            if self.simulation:
                logger.info("Simülasyon modu - Donanım kontrolleri atlanıyor")
                return True

            # Gerçek donanımda güvenlik kontrolleri
            if not self.web_only:
                logger.info("Donanım güvenlik kontrolleri yapılıyor...")

                # GPIO izinlerini kontrol et
                try:
                    import RPi.GPIO as GPIO
                    GPIO.setmode(GPIO.BCM)
                    GPIO.cleanup()
                    logger.info("✓ GPIO erişimi başarılı")
                except Exception as e:
                    logger.warning(f"⚠ GPIO erişimi başarısız: {e}")
                    return False

                # I2C cihazlarını kontrol et
                try:
                    import smbus
                    smbus.SMBus(1)  # I2C bus'a erişim testi
                    # IMU ve diğer I2C cihazlarını kontrol edebiliriz
                    logger.info("✓ I2C bus erişimi başarılı")
                except Exception as e:
                    logger.warning(f"⚠ I2C erişimi başarısız: {e}")

                # Kamera erişimini kontrol et
                try:
                    import cv2
                    cap = cv2.VideoCapture(0)
                    if cap.isOpened():
                        logger.info("✓ Kamera erişimi başarılı")
                        cap.release()
                    else:
                        logger.warning("⚠ Kamera erişimi başarısız")
                except Exception as e:
                    logger.warning(f"⚠ Kamera kontrolü başarısız: {e}")

            return True

        except Exception as e:
            logger.error(f"Başlatma kontrolleri başarısız: {e}")
            return False

    async def basla(self):
        """Ana uygulama döngüsünü başlat."""
        try:
            logger.info("🌱 Otonom Bahçe Asistanı Başlatılıyor...")

            # Başlatma kontrolleri
            if not await self.robot_baslatma_kontrolu():
                logger.error("❌ Başlatma kontrolleri başarısız!")
                return

            # Web sunucusunu başlat
            logger.info("🌐 Web sunucusu başlatılıyor...")
            # Web arayüzü başlat
            web_config = {
                'secret_key': 'oba_secret_2024',
                'debug': self.debug
            }
            self.web_server = WebArayuz(self.robot, web_config)

            # Robot sistemini başlat (web-only modunda değilse)
            if not self.web_only:
                logger.info("🤖 Robot sistemi başlatılıyor...")

                # Robot nesnesini oluştur
                self.robot = BahceRobotu()

                # Robot sistemini başlat - ana_dongu() metodunu kullan
                # Not: ana_dongu() metodu zaten var, basla() yok
                logger.info("Robot ana döngüsü başlatılıyor...")

                # Web sunucusuna robot referansını ver
                if hasattr(self.web_server, 'robot_instance'):
                    self.web_server.robot_instance = self.robot
                else:
                    # Web sunucusunu robot ile yeniden oluştur
                    self.web_server = WebArayuz(self.robot, web_config)

                logger.info("✅ Robot sistemi başarıyla başlatıldı!")

            # Web sunucusunu arka planda başlat
            import threading
            web_thread = threading.Thread(
                target=self.web_server.run,
                kwargs={'host': '0.0.0.0', 'port': 5000, 'debug': False},
                daemon=True
            )
            web_thread.start()

            # Web sunucusunun başlatılmasını bekle
            await asyncio.sleep(1)

            if not self.web_only:
                # Robot ana döngüsünü arka planda başlat
                await self.robot_ana_dongasu()
            else:
                logger.info("📱 Sadece web arayüzü modu aktif")
                # Sadece web sunucusunu bekle
                while self.calisma_durumu:
                    await asyncio.sleep(1)

        except KeyboardInterrupt:
            logger.info("👋 Kullanıcı tarafından durduruldu")
        except Exception as e:
            logger.error(f"❌ Kritik hata: {e}")
            raise
        finally:
            await self.temizle()

    async def robot_ana_dongasu(self):
        """Robot ana döngüsü."""
        try:
            logger.info("🔄 Robot ana döngüsü başladı")

            if self.robot:
                # Robot'un ana döngüsünü başlat
                # Ana döngü kendi calisma_durumu kontrolü yapıyor
                await self.robot.ana_dongu()
            else:
                logger.warning("Robot nesnesi bulunamadı!")

            logger.info("🛑 Robot ana döngüsü sonlandı")

        except asyncio.CancelledError:
            logger.info("🛑 Robot ana döngüsü iptal edildi")
        except Exception as e:
            logger.error(f"Robot ana döngüsünde kritik hata: {e}")
            if self.robot:
                # acil_durdur() sync metod
                self.robot.acil_durdur()

    async def temizle(self):
        """Uygulama sonlandırılırken temizlik işlemleri."""
        logger.info("🧹 Temizlik işlemleri başlıyor...")

        try:
            # Robot sistemini temizle
            if self.robot:
                logger.info("🤖 Robot sistemi temizleniyor...")
                await self.robot.kapat()
                self.robot = None

            # Web sunucusunu temizle
            if self.web_server:
                logger.info("🌐 Web sunucusu kapatılıyor...")
                # WebArayuz'da kapat() metodu yok, sadece referansı sil
                self.web_server = None

            logger.info("✅ Temizlik işlemleri tamamlandı")

        except Exception as e:
            logger.error(f"Temizlik sırasında hata: {e}")


def main():
    """Ana fonksiyon - komut satırı argümanlarını işle ve uygulamayı başlat."""
    parser = argparse.ArgumentParser(
        description='Otonom Bahçe Asistanı (OBA)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Örnekler:
  python main.py                    Normal modda başlat
  python main.py --debug           Debug modu ile başlat
  python main.py --simulation      Simülasyon modunda başlat
  python main.py --web-only        Sadece web arayüzü
  python main.py --debug --simulation  Debug + simülasyon modu
        """
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Debug modu - detaylı loglar'
    )

    parser.add_argument(
        '--simulation',
        action='store_true',
        help='Simülasyon modu - gerçek donanım olmadan test'
    )

    parser.add_argument(
        '--web-only',
        action='store_true',
        help='Sadece web arayüzü - robot sistemi başlatılmaz'
    )

    args = parser.parse_args()

    # Banner yazdır
    print("""
╔══════════════════════════════════════╗
║        🌱 OTONOM BAHÇE ASISTANI        ║
║                                      ║
║   Raspberry Pi 4 + Mi Vacuum         ║
║   Ataletli Seyrüsefer + AI           ║
║   Web Arayüzü + Otonom Şarj          ║
╚══════════════════════════════════════╝
""")

    # Sistem bilgilerini göster
    print(f"🐍 Python: {sys.version}")
    print(f"💻 Platform: {sys.platform}")
    print(f"📁 Çalışma dizini: {os.getcwd()}")
    print(f"🔧 Mod: {'Debug' if args.debug else 'Normal'}")
    print(f"🎮 Simülasyon: {'Evet' if args.simulation else 'Hayır'}")
    print(f"🌐 Web-Only: {'Evet' if args.web_only else 'Hayır'}")
    print("-" * 50)

    # Uygulamayı başlat
    uygulama = RobotUygulama(
        debug=args.debug,
        simulation=args.simulation,
        web_only=args.web_only
    )

    try:
        # Asyncio event loop'u başlat
        asyncio.run(uygulama.basla())
    except KeyboardInterrupt:
        print("\n👋 Güle güle!")
    except Exception as e:
        print(f"\n❌ Kritik hata: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
