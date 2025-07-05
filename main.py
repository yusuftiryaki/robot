#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Otonom Bahçe Asistanı (OBA) - Ana Başlatma Scripti
=================================================

Bu script bahçe asistanının ana başlatma noktasıdır.
Robot sistemini başlatır, web arayüzünü açar ve ana döngüyü çalıştırır.
Akıllı ortam tespiti ile otomatik olarak dev/production modu seçer.

Kullanım:
    python main.py [--debug] [--web-only]

Örnekler:
    python main.py                    # Akıllı mod (ortam otomatik tespit)
    python main.py --debug           # Debug modu
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

from core.robot import BahceRobotu
from core.smart_config import SmartConfigManager
from web.web_server import WebArayuz

# Smart config'i ilk başta yükle
config_manager = SmartConfigManager()
config = config_manager.load_config()


def setup_logging_from_config():
    """Config'ten logging kuralım"""
    log_config = config.get("logging", {})
    level = getattr(logging, log_config.get("level", "INFO"))

    # Console config
    console_config = log_config.get("console", {})
    console_format = console_config.get("format", '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # File config
    file_config = log_config.get("file", {})

    handlers = []

    # Console handler
    if console_config.get("enabled", True):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(console_format))
        handlers.append(console_handler)

    # File handler
    if file_config.get("enabled", True):
        log_path = file_config.get("path", "logs")
        log_filename = file_config.get("filename", "robot.log")
        os.makedirs(log_path, exist_ok=True)

        file_handler = logging.FileHandler(f"{log_path}/{log_filename}")
        file_handler.setFormatter(logging.Formatter(console_format))
        handlers.append(file_handler)

    # Logging'i kur
    logging.basicConfig(
        level=level,
        handlers=handlers,
        force=True
    )


# Logging'i kur
setup_logging_from_config()
logger = logging.getLogger(__name__)


class RobotUygulama:
    """
    Ana robot uygulaması sınıfı.

    Robot sistemini ve web arayüzünü yönetir.
    Graceful shutdown ve hata yönetimi sağlar.
    """

    def __init__(self, debug: bool = False, web_only: bool = False):
        """
        Robot uygulamasını başlat.

        Args:
            debug: Debug modu aktif mi?
            web_only: Sadece web arayüzü mi çalışsın?
        """
        self.debug = debug
        self.web_only = web_only
        self.robot: Optional[BahceRobotu] = None
        self.web_server: Optional[WebArayuz] = None
        self.web_thread = None
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
            f"Debug: {debug}, Web-Only: {web_only}"
        )

    def _signal_handler(self, signum, frame):
        """Graceful shutdown için signal handler."""
        logger.info(f"🛑 Çıkış sinyali alındı: {signum}")
        self.calisma_durumu = False

        # Robot'un da ana döngüsünü durdur
        if self.robot:
            self.robot.calisma_durumu = False
            logger.info("🤖 Robot ana döngüsü durduruldu")

        # Web server'ı da durdur
        if self.web_server:
            # Flask app'i durdurmak için calisma_durumu=False yap
            # Thread join'i temizle() fonksiyonunda yapılacak
            logger.info("🌐 Web sunucusu kapatılıyor...")

        # Ana döngüyü zorla bitir
        logger.info("📱 Uygulama kapatılıyor...")

    async def _show_smart_config_info(self):
        """Robot başladıktan sonra akıllı config bilgilerini göster"""
        if not self.robot:
            return

        try:
            runtime_info = self.robot.config.get("runtime", {})

            logger.info("=" * 60)
            logger.info("🧠 AKILLI ORTAM TESPİT SONUÇLARI")
            logger.info("=" * 60)

            # Temel bilgiler
            env_type = runtime_info.get("environment_type", "unknown")
            is_sim = runtime_info.get("is_simulation", False)
            is_hardware = runtime_info.get("is_hardware", False)

            logger.info(f"🌍 Tespit edilen ortam: {env_type}")
            logger.info(f"🎮 Simülasyon modu: {'✅ Aktif' if is_sim else '❌ Pasif'}")
            logger.info(f"⚙️ Donanım modu: {'✅ Aktif' if is_hardware else '❌ Pasif'}")

            # Config bilgileri
            motor_type = self.robot.config.get("motors", {}).get("type", "unknown")
            web_port = self.robot.config.get("web_interface", {}).get("port", 0)

            logger.info(f"🚗 Motor tipi: {motor_type}")
            logger.info(f"🌐 Web portu: {web_port}")

            # Aktif donanım yetenekleri
            capabilities = runtime_info.get("capabilities", {})
            active_caps = [cap for cap, available in capabilities.items() if available]
            if active_caps:
                logger.info(f"🔧 Aktif donanım: {', '.join(active_caps)}")
            else:
                logger.info("🔧 Aktif donanım: Simülasyon modu")

            logger.info("=" * 60)

        except Exception as e:
            logger.warning(f"Akıllı config bilgileri gösterilemedi: {e}")

    async def basla(self):
        """Ana uygulama döngüsünü başlat."""
        try:
            logger.info("🌱 Otonom Bahçe Asistanı Başlatılıyor...")
            logger.info("🧠 Akıllı ortam tespiti aktif...")

            # Robot sistemini başlat (web-only modunda değilse)
            if not self.web_only:
                logger.info("🤖 Robot sistemi başlatılıyor...")

                # Robot nesnesini oluştur - akıllı config ile
                self.robot = BahceRobotu()

                # Akıllı config bilgilerini göster
                await self._show_smart_config_info()

                logger.info("✅ Robot sistemi başarıyla başlatıldı!")
            else:
                logger.info("📱 Web-only modu - Robot sistemi atlanıyor")

            # Web arayüzü başlat
            logger.info("🌐 Web arayüzü başlatılıyor...")

            # Config'ten web ayarlarını al
            config = config_manager.load_config()
            web_config = config.get('web', {})

            # Varsayılan değerlerle birleştir
            web_config.setdefault('secret_key', 'oba_secret_2024')
            web_config.setdefault('debug', False)  # Thread modunda ve web-only'de debug=False
            web_config.setdefault('host', '0.0.0.0')
            web_config.setdefault('port', 5000)

            self.web_server = WebArayuz(self.robot, web_config)

            # Web sunucusunu thread'de başlat
            import threading
            self.web_thread = threading.Thread(
                target=self.web_server.calistir,
                daemon=False  # Graceful shutdown için daemon=False
            )
            self.web_thread.start()
            logger.info("✅ Web sunucusu thread'de başlatıldı")

            # Web sunucusunun başlatılmasını bekle
            await asyncio.sleep(2)

            if not self.web_only:
                # Robot ana döngüsünü başlat
                await self.robot_ana_dongasu()
            else:
                logger.info("📱 Sadece web arayüzü modu aktif")
                # Ana döngü - signal handler'ları dinler
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
                # WebArayuz'un kapat() metodunu kullan
                self.web_server.kapat()

                # Thread join'i ile bekle
                if self.web_thread and self.web_thread.is_alive():
                    logger.info("🌐 Web thread'i bekleniyor...")
                    self.web_thread.join(timeout=5)  # 5 saniye bekle

                    # Hala çalışıyorsa zorla kapat
                    if self.web_thread.is_alive():
                        logger.warning("⚠️ Web thread hala çalışıyor - zorla kapatılıyor")

                        # Thread'i zorla sonlandır
                        import ctypes

                        # Thread ID'sini al
                        thread_id = self.web_thread.ident
                        if thread_id:
                            try:
                                # PyThreadState_SetAsyncExc ile thread'i sonlandır
                                res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
                                    ctypes.c_long(thread_id),
                                    ctypes.py_object(SystemExit)
                                )
                                if res == 0:
                                    logger.warning("🚨 Thread ID bulunamadı")
                                elif res != 1:
                                    logger.error("🚨 Thread sonlandırma hatası")
                                    # Geri al
                                    ctypes.pythonapi.PyThreadState_SetAsyncExc(
                                        ctypes.c_long(thread_id), None
                                    )
                                else:
                                    logger.info("✅ Web thread zorla sonlandırıldı")
                            except Exception as e:
                                logger.error(f"❌ Thread zorla sonlandırma hatası: {e}")
                    else:
                        logger.info("✅ Web thread normal şekilde kapandı")

                self.web_server = None
                self.web_thread = None

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
  python main.py                    Normal modda başlat (akıllı ortam tespiti)
  python main.py --debug           Debug modu ile başlat
  python main.py --web-only        Sadece web arayüzü
        """
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Debug modu - detaylı loglar'
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
    print(f"� Web-Only: {'Evet' if args.web_only else 'Hayır'}")
    print("🧠 Akıllı Ortam Tespiti: Aktif")
    print("-" * 50)

    # Uygulamayı başlat
    uygulama = RobotUygulama(
        debug=args.debug,
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
