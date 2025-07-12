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
from web.fastapi_server import FastAPIWebServer

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
        self.web_server: Optional[FastAPIWebServer] = None
        self.calisma_durumu = True
        self.shutdown_event = asyncio.Event()

        # Async task'ler için referans
        self.fastapi_task: Optional[asyncio.Task] = None
        self.robot_task: Optional[asyncio.Task] = None
        self.uvicorn_server = None  # Uvicorn server referansı

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
            logger.info("🤖 Robot ana döngüsü durdurma sinyali gönderildi")

        # Shutdown event'ini set et - Bu async task'lere signal verir
        try:
            # Event loop'ta shutdown event'ini set et
            loop = asyncio.get_event_loop()
            loop.call_soon_threadsafe(self.shutdown_event.set)
            logger.info("📡 Async shutdown event gönderildi")
        except RuntimeError:
            logger.warning("⚠️ Event loop bulunamadı - shutdown event gönderilemedi")

        logger.info("📱 Signal handler tamamlandı - graceful shutdown başlayacak...")

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
            current_config = config_manager.load_config()
            web_config = current_config.get('web_interface', {})

            self.web_server = FastAPIWebServer(self.robot, web_config)

            # Pure Async Approach - FastAPI server'ı async olarak başlat
            logger.info("🚀 FastAPI server async başlatılıyor...")

            if not self.web_only:
                # Robot + FastAPI server'ı parallel çalıştır
                logger.info("🔄 Robot ve FastAPI server parallel başlatılıyor...")

                # Task'leri ayrı ayrı oluştur (cancellation için)
                self.fastapi_task = asyncio.create_task(
                    self._fastapi_server_baslat(web_config),
                    name="FastAPI-Server"
                )
                self.robot_task = asyncio.create_task(
                    self.robot_ana_dongasu(),
                    name="Robot-Ana-Dongu"
                )

                try:
                    # Shutdown monitoring task'i de ekle
                    shutdown_task = asyncio.create_task(
                        self._shutdown_monitor(),
                        name="Shutdown-Monitor"
                    )

                    # Task'leri parallel çalıştır ve shutdown'ı bekle
                    done, pending = await asyncio.wait(
                        [self.fastapi_task, self.robot_task, shutdown_task],
                        return_when=asyncio.FIRST_COMPLETED
                    )

                    # Shutdown signal geldi mi kontrol et
                    if shutdown_task in done:
                        logger.info("🛑 Shutdown signal alındı - task'ler iptal ediliyor...")
                        await self._graceful_task_cancellation([self.fastapi_task, self.robot_task])

                except KeyboardInterrupt:
                    logger.info("🛑 Ctrl+C alındı - graceful shutdown başlıyor...")
                    await self._graceful_task_cancellation([self.fastapi_task, self.robot_task])
                except asyncio.CancelledError:
                    logger.info("🛑 Task'ler iptal edildi")

            else:
                logger.info("📱 Sadece FastAPI server modu")

                # Tek task için de aynı pattern
                self.fastapi_task = asyncio.create_task(
                    self._fastapi_server_baslat(web_config),
                    name="FastAPI-Server-Only"
                )

                try:
                    # Shutdown monitoring task'i ekle
                    shutdown_task = asyncio.create_task(
                        self._shutdown_monitor(),
                        name="Shutdown-Monitor"
                    )

                    # Task'leri bekle
                    done, pending = await asyncio.wait(
                        [self.fastapi_task, shutdown_task],
                        return_when=asyncio.FIRST_COMPLETED
                    )

                    # Shutdown signal geldi mi kontrol et
                    if shutdown_task in done:
                        logger.info("🛑 Shutdown signal alındı - FastAPI server iptal ediliyor...")
                        await self._graceful_task_cancellation([self.fastapi_task])

                except KeyboardInterrupt:
                    logger.info("🛑 Ctrl+C alındı - FastAPI server iptal ediliyor...")
                    await self._graceful_task_cancellation([self.fastapi_task])
                except asyncio.CancelledError:
                    logger.info("✅ FastAPI server iptal edildi")

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
        logger.info("🧹 Graceful shutdown - temizlik işlemleri başlıyor...")

        try:
            # 1. Önce task'leri kontrol et ve graceful cancel et
            active_tasks = []
            if self.fastapi_task and not self.fastapi_task.done():
                active_tasks.append(self.fastapi_task)
            if self.robot_task and not self.robot_task.done():
                active_tasks.append(self.robot_task)

            if active_tasks:
                logger.info(f"🔄 {len(active_tasks)} aktif task graceful olarak kapatılıyor...")
                await self._graceful_task_cancellation(active_tasks, timeout=8.0)

            # 2. FastAPI server'ı kapat
            if self.uvicorn_server:
                logger.info("🌐 Uvicorn server kapatılıyor...")
                try:
                    await asyncio.wait_for(
                        self._shutdown_uvicorn_server(),
                        timeout=5.0
                    )
                except asyncio.TimeoutError:
                    logger.warning("⚠️ Uvicorn server timeout - force shutdown")
                except Exception as e:
                    logger.error(f"❌ Uvicorn server kapatma hatası: {e}")
                finally:
                    self.uvicorn_server = None

            # 3. Robot sistemini temizle
            if self.robot:
                logger.info("🤖 Robot sistemi temizleniyor...")
                try:
                    await asyncio.wait_for(
                        self.robot.kapat(),
                        timeout=5.0
                    )
                except asyncio.TimeoutError:
                    logger.warning("⚠️ Robot kapatma timeout - acil durdur")
                    # Sync method - acil durdur
                    try:
                        self.robot.acil_durdur()
                    except Exception as e:
                        logger.error(f"Acil durdur hatası: {e}")
                except Exception as e:
                    logger.error(f"❌ Robot kapatma hatası: {e}")
                finally:
                    self.robot = None

            # 4. Web server referansını temizle
            if self.web_server:
                logger.info("🌐 Web server referansı temizleniyor...")
                self.web_server = None

            # 5. Task referanslarını temizle
            self.fastapi_task = None
            self.robot_task = None

            logger.info("✅ Graceful shutdown tamamlandı")

        except Exception as e:
            logger.error(f"❌ Temizlik sırasında hata: {e}")
            logger.info("🚨 Emergency cleanup başlatılıyor...")

            # Emergency cleanup
            try:
                if self.robot:
                    self.robot.acil_durdur()
                    self.robot = None
            except Exception:
                pass

            # Force task cancel
            if self.fastapi_task and not self.fastapi_task.done():
                self.fastapi_task.cancel()
            if self.robot_task and not self.robot_task.done():
                self.robot_task.cancel()

            logger.info("🚨 Emergency cleanup tamamlandı")

    async def _shutdown_uvicorn_server(self):
        """Uvicorn server'ı graceful olarak kapat."""
        if self.uvicorn_server:
            logger.info("🔄 Uvicorn server graceful shutdown...")
            await self.uvicorn_server.shutdown()
            logger.info("✅ Uvicorn server kapatıldı")

    async def _fastapi_server_baslat(self, web_config: dict):
        """FastAPI server'ı pure async olarak başlat"""
        try:
            import uvicorn

            host = web_config.get('host', '0.0.0.0')
            port = web_config.get('port', 8000)

            logger.info(f"🚀 FastAPI server başlatılıyor: http://{host}:{port}")

            # Web server var mı kontrol et
            if not self.web_server:
                raise ValueError("FastAPI web server instance bulunamadı")

            # Uvicorn Config ve Server oluştur
            uvicorn_config = uvicorn.Config(
                app=self.web_server.app,
                host=host,
                port=port,
                log_level="info",
                access_log=True
            )

            # Server referansını sakla - graceful shutdown için
            self.uvicorn_server = uvicorn.Server(uvicorn_config)

            # Server'ı async olarak başlat
            logger.info("🔄 Uvicorn server async serve başlıyor...")
            await self.uvicorn_server.serve()
            logger.info("✅ Uvicorn server serve tamamlandı")

        except asyncio.CancelledError:
            logger.info("🛑 FastAPI server task iptal edildi")
        except Exception as e:
            logger.error(f"❌ FastAPI server async başlatma hatası: {e}")
            raise

    async def _shutdown_monitor(self):
        """Shutdown event'ini bekler ve sinyal geldiğinde tamamlanır."""
        try:
            await self.shutdown_event.wait()
            logger.info("🔔 Shutdown event alındı")
        except asyncio.CancelledError:
            logger.info("🔔 Shutdown monitor iptal edildi")

    async def _graceful_task_cancellation(self, tasks: list, timeout: float = 10.0):
        """Task'leri graceful şekilde iptal eder."""
        logger.info(f"🔄 {len(tasks)} task graceful olarak iptal ediliyor...")

        # Task'leri cancel et
        for task in tasks:
            if task and not task.done():
                task.cancel()
                logger.debug(f"📤 Task iptal edildi: {task.get_name()}")

        # Tamamlanmalarını bekle (timeout ile)
        if tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=timeout
                )
                logger.info("✅ Tüm task'ler graceful olarak iptal edildi")
            except asyncio.TimeoutError:
                logger.warning(f"⚠️ Task'ler {timeout}s içinde tamamlanamadı - force cancel")
                # Force cancel yap
                for task in tasks:
                    if task and not task.done():
                        task.cancel()
                        logger.warning(f"🚨 Force cancel: {task.get_name()}")
            except Exception as e:
                logger.error(f"❌ Task cancellation hatası: {e}")


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
