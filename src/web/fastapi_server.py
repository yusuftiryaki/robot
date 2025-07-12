"""
🚀 FastAPI Web Arayüzü - Robot Kontrol Paneli
Hacı Abi'nin modern async web arayüzü!

Migration Features:
- Native async support
- Automatic API docs (Swagger)
- WebSocket real-time updates
- Type validation
- Better performance
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

# OpenCV import'u koşullu yap
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("⚠️ OpenCV kullanılamıyor - video stream devre dışı")

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

# =====================================
# 🏗️ PYDANTIC MODELS (Type Safety)
# =====================================


class RobotCommand(BaseModel):
    """Robot komut modeli"""
    command: str = Field(..., description="Komut adı")
    params: Dict[str, Any] = Field(default_factory=dict, description="Komut parametreleri")


class ManualControl(BaseModel):
    """Manuel kontrol modeli"""
    linear: float = Field(0.0, ge=-1.0, le=1.0, description="Doğrusal hız (-1.0 ile 1.0 arası)")
    angular: float = Field(0.0, ge=-1.0, le=1.0, description="Açısal hız (-1.0 ile 1.0 arası)")


class MissionStart(BaseModel):
    """Görev başlatma modeli"""
    type: str = Field("mowing", description="Görev tipi")
    params: Dict[str, Any] = Field(default_factory=dict, description="Görev parametreleri")


class NavigationTarget(BaseModel):
    """Navigasyon hedef modeli"""
    x: float = Field(..., description="X koordinatı (metre)")
    y: float = Field(..., description="Y koordinatı (metre)")


class NavigationWaypoint(BaseModel):
    """Navigasyon waypoint modeli"""
    x: float = Field(..., description="X koordinatı (metre)")
    y: float = Field(..., description="Y koordinatı (metre)")


class NavigationMode(BaseModel):
    """Navigasyon modu modeli"""
    mode: str = Field("normal", description="Navigasyon modu: normal, aggressive, conservative, emergency")


class APIResponse(BaseModel):
    """Standart API yanıt modeli"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class WebSocketManager:
    """WebSocket bağlantı yöneticisi"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.logger = logging.getLogger("WebSocketManager")

    async def connect(self, websocket: WebSocket):
        """Yeni WebSocket bağlantısı kabul et"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.logger.info(f"🔌 Yeni WebSocket bağlantısı: {len(self.active_connections)} aktif")

    def disconnect(self, websocket: WebSocket):
        """WebSocket bağlantısını kapat"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        self.logger.info(f"🔌 WebSocket bağlantısı kapandı: {len(self.active_connections)} aktif")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Tek bir client'a mesaj gönder"""
        try:
            await websocket.send_text(message)
        except Exception as e:
            self.logger.error(f"❌ WebSocket mesaj gönderme hatası: {e}")

    async def broadcast(self, message: Dict[str, Any]):
        """Tüm bağlı client'lara mesaj gönder"""
        if not self.active_connections:
            return

        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                self.logger.error(f"❌ Broadcast hatası: {e}")
                disconnected.append(connection)

        # Bağlantısı kopan client'ları temizle
        for connection in disconnected:
            self.disconnect(connection)


class FastAPIWebServer:
    """
    🚀 FastAPI tabanlı modern web server

    Features:
    - Native async support
    - Real-time WebSocket updates
    - Automatic API documentation
    - Type validation
    - Better performance
    """

    def __init__(self, robot_ornegi, web_konfig: Dict[str, Any]):
        self.robot = robot_ornegi
        self.konfig = web_konfig
        self.logger = logging.getLogger("FastAPIWebServer")

        # WebSocket manager
        self.websocket_manager = WebSocketManager()

        # FastAPI app oluştur
        self.app = FastAPI(
            title="🤖 OBA Robot Control API",
            description="Hacı Abi'nin modern robot kontrol arayüzü",
            version="2.0.0",
            docs_url="/docs",  # Swagger UI
            redoc_url="/redoc"  # ReDoc
        )

        # Templates ve static files
        self.templates = Jinja2Templates(directory="/workspaces/oba/src/web/templates")

        # Static files mount et
        self.app.mount("/static", StaticFiles(directory="/workspaces/oba/src/web/static"), name="static")

        # Routes'ları ayarla
        self._setup_routes()

        # Startup/Shutdown events
        self._setup_events()

        # Background tasks için flag
        self._running = False

        self.logger.info("🚀 FastAPI web server başlatıldı")

    def _setup_events(self):
        """Startup ve shutdown events ayarla"""

        @self.app.on_event("startup")
        async def startup_event():
            """Server başlarken çalışacak tasks"""
            self.logger.info("🚀 FastAPI server startup...")
            self._running = True

            # Background tasks'ları başlat
            asyncio.create_task(self.start_background_tasks())

        @self.app.on_event("shutdown")
        async def shutdown_event():
            """Server kapanırken çalışacak cleanup"""
            self.logger.info("🛑 FastAPI server shutdown...")
            self._running = False

    def _setup_routes(self):
        """HTTP routes ve WebSocket endpoints ayarla"""

        # =====================================
        # 🏠 STATIC PAGES
        # =====================================

        @self.app.get("/", response_class=HTMLResponse)
        async def index(request: Request):
            """Ana sayfa - mevcut index.html template'ini kullan"""
            return self.templates.TemplateResponse("index.html", {"request": request})

        # =====================================
        # 🤖 ROBOT API ENDPOINTS
        # =====================================

        @self.app.get("/api/robot/status", response_model=APIResponse)
        async def robot_status():
            """Robot durumu al"""
            try:
                durum_verisi = await self._guncel_robot_durumu_al()
                return APIResponse(success=True, data=durum_verisi)
            except Exception as e:
                self.logger.error(f"❌ Robot status hatası: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/robot/command", response_model=APIResponse)
        async def robot_command(command: RobotCommand):
            """Robot komut gönder"""
            try:
                sonuc = await self._komut_calistir(command.command, command.params)

                # WebSocket'e broadcast yap
                await self.websocket_manager.broadcast({
                    "type": "command_executed",
                    "command": command.command,
                    "result": sonuc,
                    "timestamp": datetime.now().isoformat()
                })

                return APIResponse(success=True, data=sonuc)
            except Exception as e:
                self.logger.error(f"❌ Robot komut hatası: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/robot/manual_control", response_model=APIResponse)
        async def manual_control(control: ManualControl):
            """Manuel robot kontrolü"""
            try:
                await self._hareket_komutu_gonder(control.linear, control.angular)

                # WebSocket'e broadcast yap
                await self.websocket_manager.broadcast({
                    "type": "manual_control",
                    "linear": control.linear,
                    "angular": control.angular,
                    "timestamp": datetime.now().isoformat()
                })

                return APIResponse(
                    success=True,
                    data=f"Hareket komutu: linear={control.linear:.2f}, angular={control.angular:.2f}"
                )
            except Exception as e:
                self.logger.error(f"❌ Manuel kontrol hatası: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/robot/start_mission", response_model=APIResponse)
        async def start_mission(mission: MissionStart):
            """Görev başlat"""
            try:
                if hasattr(self.robot, 'gorev_baslat'):
                    await self.robot.gorev_baslat()

                # WebSocket broadcast
                await self.websocket_manager.broadcast({
                    "type": "mission_started",
                    "mission_type": mission.type,
                    "timestamp": datetime.now().isoformat()
                })

                return APIResponse(success=True, data=f"{mission.type} görevi başlatıldı")
            except Exception as e:
                self.logger.error(f"❌ Görev başlatma hatası: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/robot/stop_mission", response_model=APIResponse)
        async def stop_mission():
            """Görev durdur"""
            try:
                if hasattr(self.robot, 'gorev_durdur'):
                    await self.robot.gorev_durdur()

                # WebSocket broadcast
                await self.websocket_manager.broadcast({
                    "type": "mission_stopped",
                    "timestamp": datetime.now().isoformat()
                })

                return APIResponse(success=True, data="Görev durduruldu")
            except Exception as e:
                self.logger.error(f"❌ Görev durdurma hatası: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/robot/emergency_stop", response_model=APIResponse)
        async def emergency_stop():
            """Acil durdurma"""
            try:
                if hasattr(self.robot, 'acil_durdur'):
                    await self.robot.acil_durdur()

                # WebSocket broadcast - acil durum!
                await self.websocket_manager.broadcast({
                    "type": "emergency_stop",
                    "message": "ACİL DURDURMA AKTİF!",
                    "timestamp": datetime.now().isoformat()
                })

                return APIResponse(success=True, data="ACİL DURDURMA AKTİF!")
            except Exception as e:
                self.logger.error(f"❌ Acil durdurma hatası: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # =====================================
        # 🧭 ADAPTIF NAVIGASYON ENDPOINTS
        # =====================================

        @self.app.post("/api/navigation/set_target", response_model=APIResponse)
        async def set_navigation_target(target: NavigationTarget):
            """Adaptif navigasyon hedef konum ayarla"""
            try:
                if hasattr(self.robot, 'hedef_konum_ayarla'):
                    self.robot.hedef_konum_ayarla(target.x, target.y)

                # WebSocket broadcast
                await self.websocket_manager.broadcast({
                    "type": "navigation_target_set",
                    "target": {"x": target.x, "y": target.y},
                    "timestamp": datetime.now().isoformat()
                })

                return APIResponse(
                    success=True,
                    data=f"Hedef konum ayarlandı: ({target.x:.2f}, {target.y:.2f})"
                )
            except Exception as e:
                self.logger.error(f"❌ Hedef konum ayarlama hatası: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/navigation/add_waypoint", response_model=APIResponse)
        async def add_navigation_waypoint(waypoint: NavigationWaypoint):
            """Adaptif navigasyon rotasına waypoint ekle"""
            try:
                if hasattr(self.robot, 'waypoint_ekle'):
                    self.robot.waypoint_ekle(waypoint.x, waypoint.y)

                # WebSocket broadcast
                await self.websocket_manager.broadcast({
                    "type": "navigation_waypoint_added",
                    "waypoint": {"x": waypoint.x, "y": waypoint.y},
                    "timestamp": datetime.now().isoformat()
                })

                return APIResponse(
                    success=True,
                    data=f"Waypoint eklendi: ({waypoint.x:.2f}, {waypoint.y:.2f})"
                )
            except Exception as e:
                self.logger.error(f"❌ Waypoint ekleme hatası: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/navigation/set_mode", response_model=APIResponse)
        async def set_navigation_mode(mode: NavigationMode):
            """Adaptif navigasyon modunu ayarla"""
            try:
                if hasattr(self.robot, 'navigation_modunu_ayarla'):
                    self.robot.navigation_modunu_ayarla(mode.mode)

                # WebSocket broadcast
                await self.websocket_manager.broadcast({
                    "type": "navigation_mode_changed",
                    "mode": mode.mode,
                    "timestamp": datetime.now().isoformat()
                })

                return APIResponse(
                    success=True,
                    data=f"Navigasyon modu değiştirildi: {mode.mode}"
                )
            except Exception as e:
                self.logger.error(f"❌ Navigasyon modu ayarlama hatası: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/navigation/status", response_model=APIResponse)
        async def get_navigation_status():
            """Adaptif navigasyon durumunu al"""
            try:
                if hasattr(self.robot, 'navigation_durumunu_al'):
                    nav_durumu = self.robot.navigation_durumunu_al()
                    return APIResponse(success=True, data=nav_durumu)
                else:
                    return APIResponse(
                        success=False,
                        error="Adaptif navigasyon sistemi mevcut değil"
                    )
            except Exception as e:
                self.logger.error(f"❌ Navigasyon durumu alma hatası: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/navigation/start_mowing", response_model=APIResponse)
        async def start_mowing_route():
            """Biçme rotası başlat"""
            try:
                if hasattr(self.robot, 'adaptif_navigasyon') and self.robot.adaptif_navigasyon:
                    self.robot.adaptif_navigasyon.rota_ayarla("mowing")

                    # WebSocket broadcast
                    await self.websocket_manager.broadcast({
                        "type": "mowing_route_started",
                        "timestamp": datetime.now().isoformat()
                    })

                    return APIResponse(success=True, data="Biçme rotası başlatıldı")
                else:
                    raise HTTPException(status_code=500, detail="Adaptif navigasyon sistemi mevcut değil")
            except Exception as e:
                self.logger.error(f"❌ Biçme rotası başlatma hatası: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/navigation/start_charging", response_model=APIResponse)
        async def start_charging_route():
            """Şarj rotası başlat"""
            try:
                if hasattr(self.robot, 'adaptif_navigasyon') and self.robot.adaptif_navigasyon:
                    self.robot.adaptif_navigasyon.rota_ayarla("charging")

                    # WebSocket broadcast
                    await self.websocket_manager.broadcast({
                        "type": "charging_route_started",
                        "timestamp": datetime.now().isoformat()
                    })

                    return APIResponse(success=True, data="Şarj rotası başlatıldı")
                else:
                    raise HTTPException(status_code=500, detail="Adaptif navigasyon sistemi mevcut değil")
            except Exception as e:
                self.logger.error(f"❌ Şarj rotası başlatma hatası: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/robot/logs", response_model=APIResponse)
        async def get_logs():
            """Robot logları al"""
            try:
                # Async file reading
                import aiofiles

                async with aiofiles.open('logs/robot.log', 'r', encoding='utf-8') as f:
                    content = await f.read()
                    satirlar = content.split('\n')
                    son_loglar = satirlar[-100:] if len(satirlar) > 100 else satirlar

                return APIResponse(success=True, data={"logs": [satir.strip() for satir in son_loglar if satir.strip()]})
            except Exception as e:
                self.logger.error(f"❌ Log okuma hatası: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # =====================================
        # 📹 VIDEO STREAM
        # =====================================

        @self.app.get("/video_feed")
        async def video_feed():
            """Video stream endpoint"""
            return StreamingResponse(
                self._video_stream_generator(),
                media_type="multipart/x-mixed-replace; boundary=frame"
            )

        # =====================================
        # 🔌 WEBSOCKET ENDPOINT (DISABLED FOR NOW)
        # =====================================

        # @self.app.websocket("/ws")
        # async def websocket_endpoint(websocket: WebSocket):
        #     """WebSocket real-time iletişim"""
        #     await self.websocket_manager.connect(websocket)
        #     try:
        #         while True:
        #             # Client'tan mesaj bekle
        #             data = await websocket.receive_text()
        #
        #             # Echo back (geliştirilebilir)
        #             await self.websocket_manager.send_personal_message(
        #                 f"Echo: {data}", websocket
        #             )
        #
        #     except WebSocketDisconnect:
        #         self.websocket_manager.disconnect(websocket)

    # =====================================
    # 🔧 HELPER METHODS
    # =====================================

    async def _guncel_robot_durumu_al(self) -> Dict[str, Any]:
        """Robot'tan güncel durum bilgilerini al - ASYNC"""
        try:
            durum_verisi = {
                "timestamp": datetime.now().isoformat(),
                "robot_status": {
                    "state": "bilinmeyen",
                    "battery_level": 0,
                    "position": {"x": 0, "y": 0, "heading": 0},
                    "mission_progress": 0
                },
                "sensors": {
                    "gps": {"latitude": 0, "longitude": 0, "satellites": 0},
                    "imu": {"roll": 0, "pitch": 0, "yaw": 0},
                    "battery": {"voltage": 0, "current": 0, "level": 0},
                    "obstacles": []
                },
                "motors": {
                    "left_speed": 0,
                    "right_speed": 0,
                    "brushes_active": False,
                    "fan_active": False
                }
            }

            # Robot'tan güncel verileri al - ASYNC!
            if hasattr(self.robot, 'get_robot_data'):
                robot_verisi = await self.robot.get_robot_data()
                durum_verisi = self._robot_veri_to_web_veri(robot_verisi)

            return durum_verisi

        except Exception as e:
            self.logger.error(f"❌ Robot durum alma hatası: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": f"Durum alınamadı: {str(e)}"
            }

    async def _komut_calistir(self, komut: str, parametreler: Dict[str, Any]) -> Any:
        """Robot komutunu çalıştır - ASYNC"""
        if komut == "start_mission":
            if hasattr(self.robot, 'gorev_baslat'):
                await self.robot.gorev_baslat()
                return "Görev başlatıldı"

        elif komut == "stop_mission":
            if hasattr(self.robot, 'gorev_durdur'):
                await self.robot.gorev_durdur()
                return "Görev durduruldu"

        elif komut == "emergency_stop":
            if hasattr(self.robot, 'acil_durdur'):
                await self.robot.acil_durdur()
                return "Acil durdurma aktif"

        elif komut == "manual_move":
            dogrusal = parametreler.get('linear', 0.0)
            acisal = parametreler.get('angular', 0.0)
            await self._hareket_komutu_gonder(dogrusal, acisal)
            return f"Hareket komutu: linear={dogrusal}, angular={acisal}"

        elif komut == "set_brushes":
            aktif = parametreler.get('active', False)
            if hasattr(self.robot, 'motor_kontrolcu') and self.robot.motor_kontrolcu:
                await self.robot.motor_kontrolcu.set_firca_durumu(aktif)
            return f"Fırçalar {'açıldı' if aktif else 'kapatıldı'}"

        elif komut == "set_fan":
            aktif = parametreler.get('active', False)
            if hasattr(self.robot, 'motor_kontrolcu') and self.robot.motor_kontrolcu:
                await self.robot.motor_kontrolcu.set_fan_durumu(aktif)
            return f"Fan {'açıldı' if aktif else 'kapatıldı'}"

        elif komut == "get_boundary_info":
            if hasattr(self.robot, 'bahce_sinir_kontrol') and self.robot.bahce_sinir_kontrol:
                try:
                    if hasattr(self.robot, 'konum_takipci') and self.robot.konum_takipci:
                        konum = await self.robot.konum_takipci.get_mevcut_konum()
                        if hasattr(konum, 'latitude') and hasattr(konum, 'longitude'):
                            return await self.robot.bahce_sinir_kontrol.get_current_boundary_status_for_web(
                                konum.latitude, konum.longitude
                            )
                    return {"aktif": False, "hata": "GPS konumu alınamadı"}
                except Exception as e:
                    return {"aktif": False, "hata": f"Bahçe sınır kontrolü hatası: {e}"}
            else:
                return {"aktif": False, "hata": "Robot bahçe sınır fonksiyonuna sahip değil"}

        elif komut == "return_to_dock":
            if hasattr(self.robot, 'sarj_istasyonuna_git'):
                await self.robot.sarj_istasyonuna_git()
                return "Şarj istasyonuna gitme başlatıldı"
            else:
                return "Robot şarj fonksiyonuna sahip değil"

        else:
            raise ValueError(f"Bilinmeyen komut: {komut}")

    async def _hareket_komutu_gonder(self, dogrusal: float, acisal: float):
        """Robot'a hareket komutu gönder - ASYNC"""
        try:
            if hasattr(self.robot, 'motor_kontrolcu') and self.robot.motor_kontrolcu:
                # HareketKomut objesi oluştur
                from ..hardware.motor_kontrolcu import HareketKomut

                hareket_komutu = HareketKomut(
                    linear_hiz=dogrusal,
                    angular_hiz=acisal,
                    sure=0.1  # 100ms süre ile hareket
                )

                # Direct async call - no more threading!
                await self.robot.motor_kontrolcu.hareket_uygula(hareket_komutu)

                self.logger.debug(f"🎮 Hareket komutu gönderildi: linear={dogrusal:.2f}, angular={acisal:.2f}")

            else:
                self.logger.warning("⚠️ Motor kontrolcü bulunamadı")

        except Exception as e:
            self.logger.error(f"❌ Hareket komutu hatası: {e}")

    async def _video_stream_generator(self):
        """Video stream generator - ASYNC"""
        if not CV2_AVAILABLE:
            while True:
                mesaj = b'--frame\r\nContent-Type: text/plain\r\n\r\n'
                mesaj += b'OpenCV not available\r\n'
                yield mesaj
                await asyncio.sleep(1)
            return

        while True:
            try:
                if hasattr(self.robot, 'kamera_islemci'):
                    # ASYNC image capture
                    kare = await self.robot.kamera_islemci.goruntu_al()

                    if kare is not None:
                        # JPEG encode
                        jpeg_parametreleri = [cv2.IMWRITE_JPEG_QUALITY, 80]
                        ret, buffer = cv2.imencode('.jpg', kare, jpeg_parametreleri)
                        if ret:
                            kare_baytlari = buffer.tobytes()
                            icerik_tipi = b'Content-Type: image/jpeg\r\n\r\n'
                            yield (b'--frame\r\n' + icerik_tipi +
                                   kare_baytlari + b'\r\n')

                await asyncio.sleep(0.05)  # 20 FPS - faster than Flask!
            except Exception as e:
                self.logger.error(f"❌ Video stream hatası: {e}")
                await asyncio.sleep(1)

    def _robot_veri_to_web_veri(self, robot_verisi: Dict[str, Any]) -> Dict[str, Any]:
        """Robot verisini web formatına çevir - aynı logic"""
        # Bu metodu Flask versiyonundan kopyalayabiliriz
        # Şimdilik basit implementation
        try:
            return {
                "timestamp": datetime.now().isoformat(),
                "robot_status": robot_verisi.get("robot_status", {}),
                "sensors": robot_verisi.get("sensors", {}),
                "motors": robot_verisi.get("motors", {}),
                **robot_verisi  # Tüm verileri dahil et
            }
        except Exception as e:
            self.logger.error(f"❌ Web data çevirme hatası: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": "Veri çevirme hatası"
            }

    async def start_background_tasks(self):
        """Background tasks başlat"""
        self._running = True

        # Real-time status broadcast task
        async def status_broadcaster():
            while self._running:
                try:
                    if self.websocket_manager.active_connections:
                        durum = await self._guncel_robot_durumu_al()
                        await self.websocket_manager.broadcast({
                            "type": "status_update",
                            "data": durum
                        })
                except Exception as e:
                    self.logger.error(f"❌ Status broadcast hatası: {e}")

                await asyncio.sleep(1)  # Her saniye güncelle

        # Task'ı başlat
        asyncio.create_task(status_broadcaster())
        self.logger.info("📡 Background tasks başlatıldı")

    async def shutdown(self):
        """Graceful shutdown"""
        self.logger.info("🛑 FastAPI server kapatılıyor...")
        self._running = False

        # WebSocket bağlantılarını kapat
        for connection in self.websocket_manager.active_connections:
            try:
                await connection.close()
            except Exception:
                pass

        self.logger.info("✅ FastAPI server kapatıldı")

    def run(self, host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
        """Server'ı çalıştır"""
        import uvicorn

        self.logger.info(f"🚀 FastAPI server başlatılıyor: http://{host}:{port}")
        self.logger.info(f"📖 API Docs: http://{host}:{port}/docs")

        # Server'ı çalıştır - uvicorn kendi event loop'unu kuracak
        uvicorn.run(
            self.app,
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
