"""
🌐 Web Arayüzü - Robot Kontrol Paneli
Hacı Abi'nin web arayüzü burada!

Mobile-first tasarım ile:
- Canlı kamera görüntüsü
- Robot durumu izleme
- Manuel kontrol
- Görev yönetimi
"""

import asyncio
import logging
import threading
import time
from datetime import datetime
from typing import Any, Dict

# OpenCV import'u koşullu yap (dev container'da sorun çıkarmasın)
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("⚠️ OpenCV kullanılamıyor - video stream devre dışı")

from flask import Flask, Response, jsonify, render_template, request
from flask_socketio import SocketIO, emit


class WebArayuz:
    """
    🌐 Ana Web Arayüzü Sınıfı

    Flask ve SocketIO ile real-time robot kontrolü sağlar.
    """

    def __init__(self, robot_instance, web_config: Dict[str, Any]):
        self.robot = robot_instance
        self.config = web_config
        self.logger = logging.getLogger("WebArayuz")

        # Flask app kurulumu
        self.app = Flask(
            __name__,
            template_folder='/workspaces/oba/src/web/templates',
            static_folder='/workspaces/oba/src/web/static'
        )
        secret_key = web_config.get('secret_key', 'haci_abi_secret_2024')
        self.app.config['SECRET_KEY'] = secret_key

        # SocketIO kurulumu
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")

        # Web durumu
        self.connected_clients = 0
        self.streaming_active = False

        # Threading için lock
        self.data_lock = threading.Lock()
        self.latest_robot_data = {}

        self._setup_routes()
        self._setup_socketio_events()

        self.logger.info("🌐 Web arayüzü başlatıldı")

    def _setup_routes(self):
        """HTTP route'ları ayarla"""

        @self.app.route('/')
        def index():
            """Ana sayfa"""
            return render_template('index.html')

        @self.app.route('/api/robot/status')
        def robot_status():
            """Robot durumu API"""
            try:
                with self.data_lock:
                    status = self.latest_robot_data.copy()

                return jsonify({
                    "success": True,
                    "data": status,
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500

        @self.app.route('/api/robot/command', methods=['POST'])
        def robot_command():
            """Robot komut API"""
            try:
                data = request.get_json()
                command = data.get('command')
                params = data.get('params', {})

                result = self._execute_command(command, params)

                return jsonify({
                    "success": True,
                    "result": result,
                    "command": command
                })
            except Exception as e:
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500

        @self.app.route('/api/robot/logs')
        def get_logs():
            """Robot logları API"""
            try:
                # Son 100 log satırını oku
                with open('logs/robot.log', 'r') as f:
                    lines = f.readlines()
                    recent_logs = lines[-100:] if len(lines) > 100 else lines

                return jsonify({
                    "success": True,
                    "logs": [line.strip() for line in recent_logs]
                })
            except Exception as e:
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500

        @self.app.route('/video_feed')
        def video_feed():
            """Video stream endpoint"""
            return Response(
                self._generate_video_stream(),
                mimetype='multipart/x-mixed-replace; boundary=frame'
            )

    def _setup_socketio_events(self):
        """SocketIO event'larını ayarla"""

        @self.socketio.on('connect')
        def handle_connect():
            self.connected_clients += 1
            client_count = self.connected_clients
            message = f"📱 Yeni client bağlandı. Toplam: {client_count}"
            self.logger.info(message)
            emit('connected', {'message': 'Robot kontrolüne bağlandınız!'})

        @self.socketio.on('disconnect')
        def handle_disconnect():
            self.connected_clients -= 1
            client_count = self.connected_clients
            message = f"📱 Client bağlantısı kesildi. Toplam: {client_count}"
            self.logger.info(message)

        @self.socketio.on('manual_control')
        def handle_manual_control(data):
            """Manuel kontrol komutları"""
            try:
                linear = data.get('linear', 0.0)
                angular = data.get('angular', 0.0)

                # Robot'a hareket komutunu gönder
                self._send_movement_command(linear, angular)

                emit('command_executed', {
                    'success': True,
                    'command': 'manual_control',
                    'params': {'linear': linear, 'angular': angular}
                })
            except Exception as e:
                emit('command_executed', {
                    'success': False,
                    'error': str(e)
                })

        @self.socketio.on('start_mission')
        def handle_start_mission(data):
            """Görev başlatma"""
            try:
                mission_type = data.get('type', 'mowing')
                # params = data.get('params', {})  # Gelecekte kullanılacak

                if hasattr(self.robot, 'gorev_baslat'):
                    self.robot.gorev_baslat()

                emit('mission_started', {
                    'success': True,
                    'mission_type': mission_type
                })
            except Exception as e:
                emit('mission_started', {
                    'success': False,
                    'error': str(e)
                })

        @self.socketio.on('stop_mission')
        def handle_stop_mission():
            """Görev durdurma"""
            try:
                if hasattr(self.robot, 'gorev_durdur'):
                    self.robot.gorev_durdur()

                emit('mission_stopped', {'success': True})
            except Exception as e:
                emit('mission_stopped', {
                    'success': False,
                    'error': str(e)
                })

        @self.socketio.on('emergency_stop')
        def handle_emergency_stop():
            """Acil durdurma"""
            try:
                if hasattr(self.robot, 'acil_durdur'):
                    self.robot.acil_durdur()

                emit('emergency_stopped', {'success': True})
                self.socketio.emit('emergency_alert', {
                    'message': 'ACİL DURDURMA AKTİF!'
                })
            except Exception as e:
                emit('emergency_stopped', {
                    'success': False,
                    'error': str(e)
                })

    def _execute_command(self, command: str, params: Dict[str, Any]) -> Any:
        """Robot komutunu çalıştır"""
        if command == "start_mission":
            if hasattr(self.robot, 'gorev_baslat'):
                self.robot.gorev_baslat()
                return "Görev başlatıldı"

        elif command == "stop_mission":
            if hasattr(self.robot, 'gorev_durdur'):
                self.robot.gorev_durdur()
                return "Görev durduruldu"

        elif command == "emergency_stop":
            if hasattr(self.robot, 'acil_durdur'):
                self.robot.acil_durdur()
                return "Acil durdurma aktif"

        elif command == "manual_move":
            linear = params.get('linear', 0.0)
            angular = params.get('angular', 0.0)
            self._send_movement_command(linear, angular)
            return f"Hareket komutu: linear={linear}, angular={angular}"

        elif command == "set_brushes":
            aktif = params.get('active', False)
            # Robot'a fırça komutunu gönder
            return f"Fırçalar {'açıldı' if aktif else 'kapatıldı'}"

        else:
            raise ValueError(f"Bilinmeyen komut: {command}")

    def _send_movement_command(self, linear: float, angular: float):
        """Robot'a hareket komutu gönder"""
        # Bu fonksiyon robot'un motor kontrolcüsüne bağlanacak
        try:
            if hasattr(self.robot, 'motor_kontrolcu'):
                # Hareket komutunu async olarak çalıştır
                # Gerçek implementasyon için asyncio bridge gerekli
                pass
        except Exception as e:
            self.logger.error(f"❌ Hareket komutu hatası: {e}")

    def _generate_video_stream(self):
        """Video stream generator"""
        if not CV2_AVAILABLE:
            # OpenCV yoksa boş frame gönder
            while True:
                message = b'--frame\r\nContent-Type: text/plain\r\n\r\n'
                message += b'OpenCV not available\r\n'
                yield message
                time.sleep(1)
            return

        while True:
            try:
                if hasattr(self.robot, 'kamera_islemci'):
                    # Robot'tan görüntü al
                    frame = asyncio.run(self.robot.kamera_islemci.goruntu_al())

                    if frame is not None:
                        # JPEG formatına çevir
                        jpeg_params = [cv2.IMWRITE_JPEG_QUALITY, 80]
                        ret, buffer = cv2.imencode('.jpg', frame, jpeg_params)
                        if ret:
                            frame_bytes = buffer.tobytes()
                            content_type = b'Content-Type: image/jpeg\r\n\r\n'
                            yield (b'--frame\r\n' + content_type +
                                   frame_bytes + b'\r\n')

                time.sleep(0.1)  # 10 FPS
            except Exception as e:
                self.logger.error(f"❌ Video stream hatası: {e}")
                time.sleep(1)

    def robot_data_guncelle(self, robot_data: Dict[str, Any]):
        """Robot verilerini güncelle ve client'lara gönder"""
        try:
            with self.data_lock:
                self.latest_robot_data = robot_data.copy()

            # Bağlı client'lara real-time veri gönder
            if self.connected_clients > 0:
                self.socketio.emit('robot_data_update', robot_data)

        except Exception as e:
            self.logger.error(f"❌ Robot data güncelleme hatası: {e}")

    def run(self, host: str = '0.0.0.0', port: int = 5000,
            debug: bool = False):
        """Web sunucusunu başlat"""
        self.logger.info(f"🌐 Web sunucusu başlatılıyor: http://{host}:{port}")
        self.socketio.run(self.app, host=host, port=port, debug=debug)


# Web arayüzü için yardımcı fonksiyonlar
def robot_data_to_web_format(robot_data: Dict[str, Any]) -> Dict[str, Any]:
    """Robot verisini web formatına çevir"""
    try:
        web_data = {
            "timestamp": datetime.now().isoformat(),
            "robot_status": {
                "state": robot_data.get("durum", "bilinmeyen"),
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

        # Robot durumu
        if "durum_bilgisi" in robot_data:
            durum_bilgisi = robot_data["durum_bilgisi"]
            web_data["robot_status"]["state"] = durum_bilgisi.get(
                "durum", "bilinmeyen")

        # Sensör verileri
        if "sensor_data" in robot_data:
            sensor_data = robot_data["sensor_data"]

            # GPS
            if "gps" in sensor_data and sensor_data["gps"]:
                gps_data = sensor_data["gps"]
                web_data["sensors"]["gps"] = {
                    "latitude": gps_data.get("latitude", 0),
                    "longitude": gps_data.get("longitude", 0),
                    "satellites": gps_data.get("satellites", 0),
                    "fix_quality": gps_data.get("fix_quality", 0)
                }

            # IMU
            if "imu" in sensor_data and sensor_data["imu"]:
                imu_data = sensor_data["imu"]
                web_data["sensors"]["imu"] = {
                    "roll": imu_data.get("roll", 0),
                    "pitch": imu_data.get("pitch", 0),
                    "yaw": imu_data.get("yaw", 0),
                    "temperature": imu_data.get("temperature", 0)
                }

            # Batarya
            if "batarya" in sensor_data and sensor_data["batarya"]:
                batarya_data = sensor_data["batarya"]
                web_data["sensors"]["battery"] = {
                    "voltage": batarya_data.get("voltage", 0),
                    "current": batarya_data.get("current", 0),
                    "level": batarya_data.get("level", 0),
                    "power": batarya_data.get("power", 0)
                }
                web_data["robot_status"]["battery_level"] = batarya_data.get(
                    "level", 0)

        # Konum bilgisi
        if "konum_bilgisi" in robot_data:
            konum = robot_data["konum_bilgisi"]
            web_data["robot_status"]["position"] = {
                "x": konum.get("x", 0),
                "y": konum.get("y", 0),
                "heading": konum.get("theta", 0)
            }

        # Motor durumu
        if "motor_durumu" in robot_data:
            motor_data = robot_data["motor_durumu"]
            web_data["motors"] = {
                "left_speed": motor_data.get("hizlar", {}).get("sol", 0),
                "right_speed": motor_data.get("hizlar", {}).get("sag", 0),
                "brushes_active": any(motor_data.get("fircalar", {}).values()),
                "fan_active": motor_data.get("fan", False)
            }

        return web_data

    except Exception as e:
        logging.getLogger("WebArayuz").error(f"❌ Web data çevirme hatası: {e}")
        return {
            "timestamp": datetime.now().isoformat(),
            "error": "Veri çevirme hatası"
        }
