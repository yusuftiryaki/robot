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
from functools import wraps
from typing import Any, Dict

# OpenCV import'u koşullu yap (dev container'da sorun çıkarmasın)
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("⚠️ OpenCV kullanılamıyor - video stream devre dışı")

from flask import Flask, Response, jsonify, render_template, request


def istek_logla(f):
    """API isteklerini loglayan decorator"""
    @wraps(f)
    def dekore_edilmis_fonksiyon(*args, **kwargs):
        try:
            # İstek bilgilerini al
            metot = request.method
            yol = request.path
            uzak_adres = request.remote_addr

            # Log'a kaydet
            logger = logging.getLogger("WebArayuz")
            logger.info(f"🌐 API İsteği: {metot} {yol} - IP: {uzak_adres}")

            # Fonksiyonu çalıştır
            sonuc = f(*args, **kwargs)

            # Başarı logu
            logger.info(f"✅ API Yanıtı: {yol} - Başarılı")

            return sonuc
        except Exception as e:
            # Hata logu
            logger = logging.getLogger("WebArayuz")
            logger.error(f"❌ API Hatası: {yol} - {str(e)}")
            raise
    return dekore_edilmis_fonksiyon


class WebArayuz:
    """
    🌐 Ana Web Arayüzü Sınıfı

    Flask ile HTTP API tabanlı robot kontrolü sağlar.
    """

    def __init__(self, robot_ornegi, web_konfig: Dict[str, Any]):
        self.robot = robot_ornegi
        self.konfig = web_konfig
        self.logger = logging.getLogger("WebArayuz")

        # Flask app kurulumu
        self.app = Flask(
            __name__,
            template_folder='/workspaces/oba/src/web/templates',
            static_folder='/workspaces/oba/src/web/static'
        )
        gizli_anahtar = web_konfig.get('secret_key', 'haci_abi_secret_2024')
        self.app.config['SECRET_KEY'] = gizli_anahtar

        # Werkzeug (Flask) HTTP loglarını sessizleştir
        import logging as werkzeug_logging
        werkzeug_log = werkzeug_logging.getLogger('werkzeug')
        werkzeug_log.setLevel(werkzeug_logging.WARNING)  # Sadece WARNING ve üzeri

        # Web durumu
        self.yayin_aktif = False

        # Threading için lock
        self.veri_kilidi = threading.Lock()
        self.son_robot_verisi = {}
        self.calisma_durumu = True  # Arka plan thread kontrolü

        self._yollari_ayarla()

        self.logger.info("🌐 Web arayüzü başlatıldı")

        # Arka plan görevlerini başlat
        self.arkaplan_gorevlerini_baslat()

    def _yollari_ayarla(self):
        """HTTP route'ları ayarla"""

        @self.app.route('/')
        def index():
            """Ana sayfa"""
            return render_template('index.html')

        @self.app.route('/api/robot/status')
        def robot_durumu():
            """Robot durumu API"""
            try:
                # Robot'tan güncel status bilgisi al
                durum_verisi = self._guncel_robot_durumu_al()

                return jsonify({
                    "success": True,
                    "data": durum_verisi,
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                self.logger.error(f"❌ Robot status alma hatası: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500

        @self.app.route('/api/robot/command', methods=['POST'])
        @istek_logla
        def robot_komut():
            """Robot komut API"""
            try:
                veri = request.get_json()
                komut = veri.get('command')
                parametreler = veri.get('params', {})

                sonuc = self._komut_calistir(komut, parametreler)

                return jsonify({
                    "success": True,
                    "result": sonuc,
                    "command": komut
                })
            except Exception as e:
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500

        @self.app.route('/api/robot/logs')
        def loglari_al():
            """Robot logları API"""
            try:
                # Son 100 log satırını oku
                with open('logs/robot.log', 'r', encoding='utf-8') as f:
                    satirlar = f.readlines()
                    son_loglar = satirlar[-100:] if len(satirlar) > 100 else satirlar

                return jsonify({
                    "success": True,
                    "logs": [satir.strip() for satir in son_loglar]
                })
            except Exception as e:
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500

        @self.app.route('/video_feed')
        def video_akisi():
            """Video stream endpoint"""
            return Response(
                self._video_akisi_uret(),
                mimetype='multipart/x-mixed-replace; boundary=frame'
            )

        @self.app.route('/api/robot/manual_control', methods=['POST'])
        @istek_logla
        def manuel_kontrol():
            """Manuel kontrol API"""
            try:
                veri = request.get_json()
                dogrusal = veri.get('linear', 0.0)
                acisal = veri.get('angular', 0.0)

                # Robot'a hareket komutunu gönder
                self._hareket_komutu_gonder(dogrusal, acisal)

                return jsonify({
                    'success': True,
                    'command': 'manual_control',
                    'params': {'linear': dogrusal, 'angular': acisal}
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/api/robot/start_mission', methods=['POST'])
        @istek_logla
        def gorev_baslat():
            """Görev başlatma API"""
            try:
                veri = request.get_json() or {}
                gorev_tipi = veri.get('type', 'mowing')

                if hasattr(self.robot, 'gorev_baslat'):
                    self.robot.gorev_baslat()

                return jsonify({
                    'success': True,
                    'mission_type': gorev_tipi,
                    'message': 'Görev başlatıldı'
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/api/robot/stop_mission', methods=['POST'])
        @istek_logla
        def gorev_durdur():
            """Görev durdurma API"""
            try:
                if hasattr(self.robot, 'gorev_durdur'):
                    self.robot.gorev_durdur()

                return jsonify({
                    'success': True,
                    'message': 'Görev durduruldu'
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/api/robot/emergency_stop', methods=['POST'])
        @istek_logla
        def acil_durdur():
            """Acil durdurma API"""
            try:
                if hasattr(self.robot, 'acil_durdur'):
                    self.robot.acil_durdur()

                return jsonify({
                    'success': True,
                    'message': 'ACİL DURDURMA AKTİF!'
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

    def arkaplan_gorevlerini_baslat(self):
        """Arka plan görevlerini başlat"""
        def robot_verisini_guncelle():
            """Robot verisini periyodik olarak güncelle"""
            while self.calisma_durumu:
                try:
                    # Kapatılma kontrolü
                    if not self.calisma_durumu:
                        break

                    # Robot'tan güncel veri al
                    guncel_durum = self._guncel_robot_durumu_al()

                    # Cache'i güncelle
                    with self.veri_kilidi:
                        self.son_robot_verisi = guncel_durum

                    # Veri cache'de güncel tutuluyor
                    # HTTP API'lerde kullanılacak

                    time.sleep(2)  # 2 saniyede bir güncelle

                except Exception as e:
                    # Shutdown exception'ları atla
                    if "shutdown" in str(e).lower() or "interpreter" in str(e).lower():
                        self.logger.debug(f"Shutdown sırasında beklenen hata: {e}")
                        break
                    self.logger.error(f"❌ Arka plan güncelleme hatası: {e}")
                    time.sleep(5)  # Hata durumunda 5 saniye bekle

        # Arka plan thread'ini başlat
        self.arkaplan_thread = threading.Thread(target=robot_verisini_guncelle, daemon=True)
        self.arkaplan_thread.start()
        self.logger.info("🔄 Arka plan veri güncelleme başlatıldı")

    def _komut_calistir(self, komut: str, parametreler: Dict[str, Any]) -> Any:
        """Robot komutunu çalıştır"""
        if komut == "start_mission":
            if hasattr(self.robot, 'gorev_baslat'):
                self.robot.gorev_baslat()
                return "Görev başlatıldı"

        elif komut == "stop_mission":
            if hasattr(self.robot, 'gorev_durdur'):
                self.robot.gorev_durdur()
                return "Görev durduruldu"

        elif komut == "emergency_stop":
            if hasattr(self.robot, 'acil_durdur'):
                self.robot.acil_durdur()
                return "Acil durdurma aktif"

        elif komut == "manual_move":
            dogrusal = parametreler.get('linear', 0.0)
            acisal = parametreler.get('angular', 0.0)
            self._hareket_komutu_gonder(dogrusal, acisal)
            return f"Hareket komutu: linear={dogrusal}, angular={acisal}"

        elif komut == "set_brushes":
            aktif = parametreler.get('active', False)
            # Robot'a fırça komutunu gönder
            return f"Fırçalar {'açıldı' if aktif else 'kapatıldı'}"

        elif komut == "set_fan":
            aktif = parametreler.get('active', False)
            # Robot'a fan komutunu gönder
            return f"Fan {'açıldı' if aktif else 'kapatıldı'}"

        elif komut == "return_to_dock":
            # Şarj istasyonuna dönme komutunu gönder
            return "Şarj istasyonuna dönülüyor"

        else:
            raise ValueError(f"Bilinmeyen komut: {komut}")

    def _hareket_komutu_gonder(self, dogrusal: float, acisal: float):
        """Robot'a hareket komutu gönder"""
        # Bu fonksiyon robot'un motor kontrolcüsüne bağlanacak
        try:
            if hasattr(self.robot, 'motor_kontrolcu'):
                # Hareket komutunu async olarak çalıştır
                # Gerçek implementasyon için asyncio bridge gerekli
                pass
        except Exception as e:
            self.logger.error(f"❌ Hareket komutu hatası: {e}")

    def _video_akisi_uret(self):
        """Video stream generator"""
        if not CV2_AVAILABLE:
            # OpenCV yoksa boş frame gönder
            while True:
                mesaj = b'--frame\r\nContent-Type: text/plain\r\n\r\n'
                mesaj += b'OpenCV not available\r\n'
                yield mesaj
                time.sleep(1)
            return

        while True:
            try:
                if hasattr(self.robot, 'kamera_islemci'):
                    # Robot'tan görüntü al
                    kare = asyncio.run(self.robot.kamera_islemci.goruntu_al())

                    if kare is not None:
                        # JPEG formatına çevir
                        jpeg_parametreleri = [cv2.IMWRITE_JPEG_QUALITY, 80]
                        ret, buffer = cv2.imencode('.jpg', kare, jpeg_parametreleri)
                        if ret:
                            kare_baytlari = buffer.tobytes()
                            icerik_tipi = b'Content-Type: image/jpeg\r\n\r\n'
                            yield (b'--frame\r\n' + icerik_tipi +
                                   kare_baytlari + b'\r\n')

                time.sleep(0.1)  # 10 FPS
            except Exception as e:
                self.logger.error(f"❌ Video stream hatası: {e}")
                time.sleep(1)

    def _guncel_robot_durumu_al(self) -> Dict[str, Any]:
        """Robot'tan güncel status bilgisi al"""
        try:
            # Robot durum bilgisi
            robot_durumu = self.robot.get_durum_bilgisi()

            # Sensor verilerini güvenli şekilde al
            sensor_verisi = {}
            try:
                # Shutdown kontrolü
                if not self.calisma_durumu:
                    sensor_verisi = {}
                else:
                    # Async methodları çalıştırmak için thread kullan
                    def sensor_verisi_al():
                        try:
                            dongu = asyncio.new_event_loop()
                            asyncio.set_event_loop(dongu)
                            try:
                                return dongu.run_until_complete(self.robot.sensor_verilerini_al())
                            finally:
                                dongu.close()
                        except Exception as e:
                            # Shutdown exception'ları daha sessiz yakala
                            if "shutdown" in str(e).lower() or "interpreter" in str(e).lower():
                                return {}
                            self.logger.warning(f"⚠️ Sensor verisi alınamadı: {e}")
                            return {}

                    # Thread'de çalıştır
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        gelecek = executor.submit(sensor_verisi_al)
                        sensor_verisi = gelecek.result(timeout=2)  # 2 saniye timeout

            except Exception as e:
                # Shutdown exception'ları daha sessiz yakala
                if "shutdown" in str(e).lower() or "interpreter" in str(e).lower():
                    sensor_verisi = {}
                else:
                    self.logger.warning(f"⚠️ Sensor verisi alınamadı: {e}")
                    sensor_verisi = {}

            # Motor durumu
            motor_durumu = {}
            if hasattr(self.robot, 'motor_kontrolcu') and self.robot.motor_kontrolcu:
                motor_durumu = self.robot.motor_kontrolcu.get_motor_durumu()

            # Sensor okuyucu durumu
            sensor_okuyucu_durumu = {}
            if hasattr(self.robot, 'sensor_okuyucu') and self.robot.sensor_okuyucu:
                sensor_okuyucu_durumu = self.robot.sensor_okuyucu.get_sensor_durumu()

            # Konum bilgisi ve istatistikler
            konum_bilgisi = {}
            hareket_istatistikleri = {}
            if hasattr(self.robot, 'konum_takipci') and self.robot.konum_takipci:
                try:
                    konum_bilgisi = self.robot.konum_takipci.get_mevcut_konum()
                    hareket_istatistikleri = self.robot.konum_takipci.get_hareket_istatistikleri()
                except Exception as e:
                    self.logger.debug(f"Konum bilgisi alınamadı: {e}")

            # Hepsini birleştir
            tam_durum = {
                "durum_bilgisi": robot_durumu,
                "sensor_data": sensor_verisi,
                "motor_durumu": motor_durumu,
                "sensor_okuyucu_durumu": sensor_okuyucu_durumu,
                "konum_bilgisi": konum_bilgisi,
                "hareket_istatistikleri": hareket_istatistikleri,
                "timestamp": datetime.now().isoformat()
            }

            # Web formatına çevir
            return robot_verisini_web_formatina_cevir(tam_durum)

        except Exception as e:
            self.logger.error(f"❌ Robot status alma hatası: {e}")
            # Hata durumunda cache'den ver
            with self.veri_kilidi:
                return self.son_robot_verisi.copy() if self.son_robot_verisi else {}

    def kapat(self):
        """Web arayüzünü graceful shutdown yap"""
        self.logger.info("🌐 Web arayüzü kapatılıyor...")

        # Arka plan thread'ini durdur
        self.calisma_durumu = False

        # Thread'in bitmesini bekle
        if hasattr(self, 'arkaplan_thread') and self.arkaplan_thread.is_alive():
            self.logger.info("🔄 Arka plan thread'i bekleniyor...")
            self.arkaplan_thread.join(timeout=3)
            if self.arkaplan_thread.is_alive():
                self.logger.warning("⚠️ Arka plan thread hala çalışıyor")

        self.logger.info("✅ Web arayüzü kapatıldı")

    def calistir(self, host: str = '0.0.0.0', port: int = 5000,
                 debug: bool = False):
        """Web sunucusunu başlat"""
        self.logger.info(f"🌐 Web sunucusu başlatılıyor: http://{host}:{port}")

        # Flask app'i çalıştır
        self.app.run(host=host, port=port, debug=debug, threaded=True)


# Web arayüzü için yardımcı fonksiyonlar
def robot_verisini_web_formatina_cevir(robot_verisi: Dict[str, Any]) -> Dict[str, Any]:
    """Robot verisini web formatına çevir"""
    try:
        web_verisi = {
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

        # Robot durum bilgisi
        if "durum_bilgisi" in robot_verisi:
            durum_bilgisi = robot_verisi["durum_bilgisi"]
            web_verisi["robot_status"]["state"] = durum_bilgisi.get("durum", "bilinmeyen")

        # Sensor verileri - yeni format
        if "sensor_data" in robot_verisi:
            sensor_verisi = robot_verisi["sensor_data"]

            # GPS - yeni format
            if "gps" in sensor_verisi:
                gps_verisi = sensor_verisi["gps"]
                web_verisi["sensors"]["gps"] = {
                    "latitude": gps_verisi.get("latitude", 0),
                    "longitude": gps_verisi.get("longitude", 0),
                    "satellites": gps_verisi.get("satellites", 0),
                    "fix_quality": gps_verisi.get("fix_quality", 0)
                }

            # IMU - yeni format
            if "imu" in sensor_verisi:
                imu_verisi = sensor_verisi["imu"]
                web_verisi["sensors"]["imu"] = {
                    "roll": imu_verisi.get("roll", 0),
                    "pitch": imu_verisi.get("pitch", 0),
                    "yaw": imu_verisi.get("yaw", 0),
                    "temperature": imu_verisi.get("temperature", 0)
                }

            # Batarya - yeni format (battery key'i kullan)
            if "battery" in sensor_verisi:
                batarya_verisi = sensor_verisi["battery"]
                web_verisi["sensors"]["battery"] = {
                    "voltage": batarya_verisi.get("voltage", 0),
                    "current": batarya_verisi.get("current", 0),
                    "level": batarya_verisi.get("percentage", batarya_verisi.get("level", 0)),
                    "power": batarya_verisi.get("power", 0)
                }
                web_verisi["robot_status"]["battery_level"] = batarya_verisi.get(
                    "percentage", batarya_verisi.get("level", 0))

            # Eski format desteği - batarya
            elif "batarya" in sensor_verisi and sensor_verisi["batarya"]:
                batarya_verisi = sensor_verisi["batarya"]
                web_verisi["sensors"]["battery"] = {
                    "voltage": batarya_verisi.get("voltage", 0),
                    "current": batarya_verisi.get("current", 0),
                    "level": batarya_verisi.get("level", 0),
                    "power": batarya_verisi.get("power", 0)
                }
                web_verisi["robot_status"]["battery_level"] = batarya_verisi.get("level", 0)

        # Konum bilgisi
        if "konum_bilgisi" in robot_verisi:
            konum = robot_verisi["konum_bilgisi"]
            # Konum objesi dataclass ise attribute'lara doğrudan eriş
            if hasattr(konum, 'x'):
                web_verisi["robot_status"]["position"] = {
                    "x": getattr(konum, 'x', 0),
                    "y": getattr(konum, 'y', 0),
                    "heading": getattr(konum, 'theta', 0)
                }
            # Konum dict ise normal erişim
            elif isinstance(konum, dict):
                web_verisi["robot_status"]["position"] = {
                    "x": konum.get("x", 0),
                    "y": konum.get("y", 0),
                    "heading": konum.get("theta", 0)
                }
            else:
                web_verisi["robot_status"]["position"] = {
                    "x": 0,
                    "y": 0,
                    "heading": 0
                }

        # Motor durumu
        if "motor_durumu" in robot_verisi:
            motor_verisi = robot_verisi["motor_durumu"]
            web_verisi["motors"] = {
                "left_speed": motor_verisi.get("hizlar", {}).get("sol", 0),
                "right_speed": motor_verisi.get("hizlar", {}).get("sag", 0),
                "brushes_active": any(motor_verisi.get("fircalar", {}).values()),
                "fan_active": motor_verisi.get("fan", False)
            }

        # Hareket istatistikleri
        if "hareket_istatistikleri" in robot_verisi:
            istatistikler = robot_verisi["hareket_istatistikleri"]
            web_verisi["mission_stats"] = {
                "total_distance": istatistikler.get("toplam_mesafe", 0),
                "working_time": istatistikler.get("hareket_sayisi", 0) * 0.1 / 60,  # Yaklaşık çalışma süresi (dakika)
                "average_speed": istatistikler.get("ortalama_hiz", 0),
                "max_speed": istatistikler.get("max_hiz", 0)
            }

        return web_verisi

    except Exception as e:
        logging.getLogger("WebArayuz").error(f"❌ Web data çevirme hatası: {e}")
        return {
            "timestamp": datetime.now().isoformat(),
            "error": "Veri çevirme hatası"
        }
