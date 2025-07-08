"""
📡 Sensör Okuyucu - Robot'un Duyuları
Hacı Abi'nin sensör yönetimi burada!

Bu sınıf robot'un tüm sensörlerini okur:
- MPU-6050 IMU (ivmeölçer, jiroskop)
- GPS NEO-6M
- INA219 akım/voltaj sensörü
- Ön tampon sensörü
- Encoder sensörleri (odometri için)
"""

import asyncio
import json
import logging
import math
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class IMUData:
    """IMU sensör verisi"""
    accel_x: float
    accel_y: float
    accel_z: float
    gyro_x: float
    gyro_y: float
    gyro_z: float
    roll: float
    pitch: float
    yaw: float
    temperature: float


@dataclass
class GPSData:
    """GPS sensör verisi"""
    latitude: float
    longitude: float
    altitude: float
    satellites: int
    fix_quality: int
    speed: float
    course: float
    timestamp: str


@dataclass
class PowerData:
    """Güç sensör verisi"""
    voltage: float
    current: float
    power: float
    level: float  # batarya seviyesi %


@dataclass
class RobotState:
    """Robot durumu - sensör simülasyonu için"""
    state: str  # "bekleme", "hareket", "sarj", "gorev"
    linear_velocity: float  # m/s
    angular_velocity: float  # rad/s
    position: Dict[str, float]  # {"x": 0.0, "y": 0.0, "heading": 0.0}
    is_moving: bool
    timestamp: float


class SensorOkuyucu:
    """
    📡 Ana Sensör Okuyucu Sınıfı

    Robot'un tüm sensörlerini okur ve verileri işler.
    Simülasyon modunda sahte veriler üretir.
    """

    def __init__(self, sensor_config: Dict[str, Any], smart_config: Optional[Dict[str, Any]] = None):
        self.config = sensor_config
        self.smart_config = smart_config
        self.logger = logging.getLogger("SensorOkuyucu")

        # Simülasyon modu kontrolü
        self.simulation_mode = self._is_simulation()

        # Sensör durumları
        self.sensors_aktif = False
        self.son_okuma_zamani = {}

        # 🧠 Akıllı simülasyon için robot durumu takibi
        self.robot_state = RobotState(
            state="bekleme",
            linear_velocity=0.0,
            angular_velocity=0.0,
            position={"x": 0.0, "y": 0.0, "heading": 0.0},
            is_moving=False,
            timestamp=time.time()
        )

        # Simülasyon için sabit konum (bekleme modunda)
        self.base_position = {"lat": 39.9334, "lon": 32.8597}
        self.current_position = self.base_position.copy()

        # Kalibrasyon verileri
        self.imu_kalibrasyon: Dict[str, Dict[str, float]] = {
            "accel_offset": {"x": 0.0, "y": 0.0, "z": 0.0},
            "gyro_offset": {"x": 0.0, "y": 0.0, "z": 0.0}
        }

        # Simülasyon verileri - Config'ten yükle
        self.simulation_data = self._load_config_simulation_data()
        self.simulation_time_start = time.time()

        self.logger.info(f"📡 Sensör okuyucu başlatıldı (Simülasyon: {self.simulation_mode})")
        self._init_sensors()

    def update_robot_state(self, state: str, linear_vel: float = 0.0, angular_vel: float = 0.0):
        """
        🧠 Robot durumunu güncelle - Akıllı simülasyon için

        Args:
            state: Robot durumu ("bekleme", "hareket", "sarj", "gorev")
            linear_vel: Linear hız m/s
            angular_vel: Açısal hız rad/s
        """
        old_state = self.robot_state.state
        self.robot_state.state = state
        self.robot_state.linear_velocity = linear_vel
        self.robot_state.angular_velocity = angular_vel
        self.robot_state.is_moving = abs(linear_vel) > 0.01 or abs(angular_vel) > 0.01
        self.robot_state.timestamp = time.time()

        if old_state != state:
            self.logger.info(f"🔄 Robot durumu değişti: {old_state} → {state}")
            if state == "bekleme":
                self.logger.info("⏸️ Bekleme modunda - konum sabit")
            elif state == "hareket":
                self.logger.info(f"🚀 Hareket modunda - hız: {linear_vel:.2f} m/s")
            elif state == "sarj":
                self.logger.info("🔋 Şarj modunda - konum sabit")

    def _update_position_simulation(self, dt: float):
        """
        🗺️ Simülasyon konumunu güncelle

        Args:
            dt: Delta time (saniye)
        """
        if not self.robot_state.is_moving:
            return  # Hareket halinde değilse konum değişmez

        # Linear hareket
        if abs(self.robot_state.linear_velocity) > 0.01:
            # Hareket yönü (heading)
            heading_rad = math.radians(self.robot_state.position["heading"])

            # Konum değişikliği
            dx = self.robot_state.linear_velocity * math.cos(heading_rad) * dt
            dy = self.robot_state.linear_velocity * math.sin(heading_rad) * dt

            # GPS koordinatlarına dönüştür (yaklaşık)
            # 1 derece latitude ~ 111 km
            # 1 derece longitude ~ 111 km * cos(latitude)
            lat_delta = dy / 111000.0
            lon_delta = dx / (111000.0 * math.cos(math.radians(self.current_position["lat"])))

            self.current_position["lat"] += lat_delta
            self.current_position["lon"] += lon_delta

            self.robot_state.position["x"] += dx
            self.robot_state.position["y"] += dy

        # Angular hareket
        if abs(self.robot_state.angular_velocity) > 0.01:
            heading_delta = math.degrees(self.robot_state.angular_velocity * dt)
            self.robot_state.position["heading"] += heading_delta
            # Heading'i 0-360 arası tut
            self.robot_state.position["heading"] = self.robot_state.position["heading"] % 360

    def _is_simulation(self) -> bool:
        """Simülasyon modunda mı kontrol et"""
        try:
            import board
            return False
        except (ImportError, RuntimeError):
            # ImportError: paket yok
            # RuntimeError: donanım yoksa RuntimeError atabilir
            return True

    def _load_simulation_data(self) -> Dict[str, Any]:
        """Simülasyon verilerini yükle"""
        try:
            with open('.devcontainer/simulator_data/config.json', 'r') as f:
                data = json.load(f)
                return data.get('simulation_values', {})
        except FileNotFoundError:
            self.logger.warning("⚠️ Simülasyon verisi bulunamadı, varsayılan değerler kullanılıyor")
            return {
                "battery_voltage": 12.5,
                "battery_current": 1.2,
                "gps_coordinates": {"lat": 39.9334, "lon": 32.8597},
                "imu_orientation": {"roll": 0, "pitch": 0, "yaw": 0}
            }

    def _load_config_simulation_data(self) -> Dict[str, Any]:
        """Config'ten simülasyon verilerini yükle"""
        # Öncelikle akıllı config'ten al
        if hasattr(self, 'smart_config') and self.smart_config:
            sensors_config = self.smart_config.get('sensors', {})
            simulation_sensors = sensors_config.get('simulation_sensors', [])

            # Simülasyon sensörlerini parse et
            parsed_data = {}

            for sensor in simulation_sensors:
                sensor_type = sensor.get('type', '')
                sensor_name = sensor.get('name', '')

                if sensor_type == 'imu':
                    # IMU sensör config'ini al
                    parsed_data['imu_config'] = {
                        'update_rate': sensor.get('update_rate', 100),
                        'name': sensor_name
                    }
                elif sensor_type == 'battery':
                    # Batarya sensör config'ini al
                    parsed_data['battery_config'] = {
                        'initial_level': sensor.get('initial_level', 85),
                        'drain_rate': sensor.get('drain_rate', 0.1),
                        'name': sensor_name
                    }

            # Varsayılan değerlerle birleştir
            default_data = {
                "battery_voltage": 12.5,
                "battery_current": 1.2,
                "gps_coordinates": {"lat": 39.9334, "lon": 32.8597},
                "imu_orientation": {"roll": 0, "pitch": 0, "yaw": 0}
            }

            # Battery config'ten voltage hesapla
            battery_config = parsed_data.get('battery_config', {})
            if battery_config:
                initial_level = battery_config.get('initial_level', 85)
                default_data['battery_voltage'] = 12.6 * (initial_level / 100.0)

            # Parsed data ile varsayılan değerleri birleştir
            default_data.update(parsed_data)

            self.logger.info(f"📊 Config'ten simülasyon verileri yüklendi: {len(parsed_data)} sensor config")
            return default_data

        # Fallback to old method
        return self._load_simulation_data()

    def _init_sensors(self):
        """Sensörleri başlat"""
        if self.simulation_mode:
            self._init_simulation_sensors()
        else:
            self._init_real_sensors()

    def _init_simulation_sensors(self):
        """Simülasyon sensörlerini başlat"""
        self.logger.info("🔧 Simülasyon sensörleri başlatılıyor...")
        self.sensors_aktif = True
        self.logger.info("✅ Simülasyon sensörleri hazır!")

    def _init_real_sensors(self):
        """Gerçek sensörleri başlat - Config'ten ayarları kullan"""
        self.logger.info("🔧 Fiziksel sensörler başlatılıyor...")
        try:
            import adafruit_gps
            import adafruit_ina219
            import adafruit_mpu6050
            import board
            import busio
            import serial

            # Config'ten sensör ayarlarını al
            mpu_config = self.config.get("mpu6050", {})
            ina_config = self.config.get("ina219", {})
            gps_config = self.config.get("gps", {})
            bumper_config = self.config.get("front_bumper", {})

            # I2C Bus - config'ten pin'leri al
            sda_pin = mpu_config.get("sda_pin", 2)
            scl_pin = mpu_config.get("scl_pin", 3)

            # Board pin'leri kullan (config değerleri bilgi amaçlı)
            i2c = busio.I2C(board.SCL, board.SDA)
            self.logger.info(f"✅ I2C Bus başlatıldı (SDA:{sda_pin}, SCL:{scl_pin})")

            # MPU-6050 IMU - config'ten adres al
            mpu_address = mpu_config.get("i2c_address", 0x68)
            self.sample_rate = mpu_config.get("sample_rate", 50)

            self.mpu = adafruit_mpu6050.MPU6050(i2c, address=mpu_address)
            self.logger.info(f"✅ MPU-6050 IMU başlatıldı (Adres: 0x{mpu_address:02X}, Rate: {self.sample_rate}Hz)")

            # INA219 Güç sensörü - config'ten adres al
            ina_address = ina_config.get("i2c_address", 0x40)
            self.ina219 = adafruit_ina219.INA219(i2c, addr=ina_address)
            self.logger.info(f"✅ INA219 güç sensörü başlatıldı (Adres: 0x{ina_address:02X})")

            # GPS UART - config'ten ayarları al
            uart_tx = gps_config.get("uart_tx", 14)
            uart_rx = gps_config.get("uart_rx", 15)
            baud_rate = gps_config.get("baud_rate", 9600)

            uart = serial.Serial(
                "/dev/ttyS0",  # Raspberry Pi UART
                baudrate=baud_rate,
                timeout=10
            )
            self.gps = adafruit_gps.GPS(uart, debug=False)
            self.gps.send_command(b"PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0")
            self.gps.send_command(b"PMTK220,1000")
            self.logger.info(f"✅ GPS NEO-6M başlatıldı (TX:{uart_tx}, RX:{uart_rx}, Baud:{baud_rate})")

            # Ön tampon sensörü - config'ten pin al
            import RPi.GPIO as GPIO
            self.tampon_pin = bumper_config.get("pin", 16)
            pull_up = bumper_config.get("pull_up", True)

            if pull_up:
                GPIO.setup(self.tampon_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            else:
                GPIO.setup(self.tampon_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

            self.logger.info(f"✅ Ön tampon sensörü başlatıldı (Pin:{self.tampon_pin}, Pull-up:{pull_up})")

            # Kamera config'ini kontrol et
            camera_config = self.config.get("camera", {})
            if camera_config:
                camera_port = camera_config.get("port", 0)
                camera_res = camera_config.get("resolution", [640, 480])
                camera_fps = camera_config.get("framerate", 30)
                self.logger.info(f"📷 Kamera config: Port {camera_port}, {camera_res[0]}x{camera_res[1]}, {camera_fps}fps")

            self.sensors_aktif = True
            self.logger.info("✅ Tüm fiziksel sensörler hazır!")

        except Exception as e:
            self.logger.error(f"❌ Sensör başlatma hatası: {e}")
            self.simulation_mode = True
            self._init_simulation_sensors()

    async def tum_verileri_oku(self) -> Dict[str, Any]:
        """
        📊 Tüm sensörlerden veri oku

        Returns:
            Dict: Tüm sensör verileri
        """
        if not self.sensors_aktif:
            return {}

        # Paralel olarak tüm sensörleri oku
        tasks = [
            self.imu_oku(),
            self.gps_oku(),
            self.batarya_oku(),
            self.tampon_oku()
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Sonuçları birleştir
        sensor_data = {
            "timestamp": datetime.now().isoformat(),
            "imu": results[0] if not isinstance(results[0], Exception) else None,
            "gps": results[1] if not isinstance(results[1], Exception) else None,
            "batarya": results[2] if not isinstance(results[2], Exception) else None,
            "tampon": results[3] if not isinstance(results[3], Exception) else None
        }

        # Hataları logla
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                sensor_names = ["IMU", "GPS", "Batarya", "Tampon"]
                self.logger.warning(f"⚠️ {sensor_names[i]} okuma hatası: {result}")

        return sensor_data

    async def imu_oku(self) -> Optional[Dict[str, Any]]:
        """🧭 IMU sensöründen veri oku"""
        try:
            if self.simulation_mode:
                return await self._simulation_imu_oku()
            else:
                return await self._real_imu_oku()
        except Exception as e:
            self.logger.error(f"❌ IMU okuma hatası: {e}")
            return None

    async def _simulation_imu_oku(self) -> Dict[str, Any]:
        """🧠 Akıllı IMU simülasyonu - Robot durumuna göre"""
        current_time = time.time()
        t = current_time - self.simulation_time_start

        # Config'ten IMU ayarlarını al
        imu_config = self.simulation_data.get("imu_config", {})
        update_rate = imu_config.get('update_rate', 100)  # Hz
        freq_multiplier = update_rate / 100.0

        # Robot durumuna göre IMU verisi
        if self.robot_state.state == "bekleme":
            # Bekleme modunda minimal titreşim
            imu_data = IMUData(
                accel_x=0.02 * math.sin(t * 0.1),  # Çok küçük titreşim
                accel_y=0.02 * math.cos(t * 0.1),
                accel_z=9.81 + 0.01 * math.sin(t * 0.05),  # Gravity + minimal noise
                gyro_x=0.005 * math.sin(t * 0.2),  # Minimal dönme
                gyro_y=0.005 * math.cos(t * 0.2),
                gyro_z=0.002 * math.sin(t * 0.1),
                roll=0.2 * math.sin(t * 0.05),    # Çok küçük roll
                pitch=0.1 * math.cos(t * 0.05),   # Çok küçük pitch
                yaw=self.robot_state.position["heading"],  # Sabit yaw
                temperature=25.0 + 0.5 * math.sin(t * 0.02)  # Minimal sıcaklık değişimi
            )

        elif self.robot_state.state in ["hareket", "gorev"]:
            # Hareket modunda gerçekçi IMU verileri
            linear_vel = self.robot_state.linear_velocity
            angular_vel = self.robot_state.angular_velocity

            # Hızlanma simülasyonu
            accel_magnitude = abs(linear_vel) * 2.0  # m/s²

            imu_data = IMUData(
                accel_x=accel_magnitude * math.cos(math.radians(self.robot_state.position["heading"])) + 0.1 * math.sin(t * freq_multiplier),
                accel_y=accel_magnitude * math.sin(math.radians(self.robot_state.position["heading"])) + 0.1 * math.cos(t * freq_multiplier),
                accel_z=9.81 + 0.2 * math.sin(t * 0.5),  # Gravity + hareket gürültüsü
                gyro_x=angular_vel * 0.5 + 0.1 * math.sin(t * freq_multiplier),
                gyro_y=0.05 * math.cos(t * freq_multiplier),
                gyro_z=angular_vel + 0.02 * math.sin(t * freq_multiplier),
                roll=5 * math.sin(t * 0.3) * (abs(linear_vel) / 2.0),  # Hıza göre roll
                pitch=3 * math.cos(t * 0.4) * (abs(linear_vel) / 2.0),  # Hıza göre pitch
                yaw=self.robot_state.position["heading"],
                temperature=25.0 + 3 * math.sin(t * 0.1)  # Hareket sıcaklığı
            )

        elif self.robot_state.state == "sarj":
            # Şarj modunda tamamen sabit
            imu_data = IMUData(
                accel_x=0.0,
                accel_y=0.0,
                accel_z=9.81,  # Sadece gravity
                gyro_x=0.0,
                gyro_y=0.0,
                gyro_z=0.0,
                roll=0.0,
                pitch=0.0,
                yaw=self.robot_state.position["heading"],
                temperature=25.0 + 0.2 * math.sin(t * 0.01)  # Çok minimal sıcaklık
            )

        else:
            # Varsayılan durum
            base_data = self.simulation_data.get("imu_orientation", {})
            imu_data = IMUData(
                accel_x=0.05 * math.sin(t * 0.5),
                accel_y=0.05 * math.cos(t * 0.3),
                accel_z=9.81 + 0.02 * math.sin(t),
                gyro_x=0.01 * math.sin(t * 0.8),
                gyro_y=0.01 * math.cos(t * 0.6),
                gyro_z=0.005 * math.sin(t * 0.4),
                roll=base_data.get("roll", 0) + 1 * math.sin(t * 0.2),
                pitch=base_data.get("pitch", 0) + 0.5 * math.cos(t * 0.3),
                yaw=base_data.get("yaw", 0) + 0.2 * t % 360,
                temperature=25.0 + 1 * math.sin(t * 0.1)
            )

        return asdict(imu_data)

    async def _real_imu_oku(self) -> Dict[str, Any]:
        """Gerçek IMU verisi"""
        # MPU-6050'den veri oku
        accel_x, accel_y, accel_z = self.mpu.acceleration
        gyro_x, gyro_y, gyro_z = self.mpu.gyro
        temp = self.mpu.temperature

        # Kalibrasyon uygula
        accel_x -= self.imu_kalibrasyon["accel_offset"]["x"]
        accel_y -= self.imu_kalibrasyon["accel_offset"]["y"]
        accel_z -= self.imu_kalibrasyon["accel_offset"]["z"]

        gyro_x -= self.imu_kalibrasyon["gyro_offset"]["x"]
        gyro_y -= self.imu_kalibrasyon["gyro_offset"]["y"]
        gyro_z -= self.imu_kalibrasyon["gyro_offset"]["z"]

        # Roll, pitch, yaw hesapla
        roll = math.atan2(accel_y, accel_z) * 180 / math.pi
        pitch = math.atan2(-accel_x, math.sqrt(accel_y**2 + accel_z**2)) * 180 / math.pi
        yaw = 0.0  # Magnetometre olmadığı için yaw hesaplanamıyor

        imu_data = IMUData(
            accel_x=accel_x,
            accel_y=accel_y,
            accel_z=accel_z,
            gyro_x=gyro_x,
            gyro_y=gyro_y,
            gyro_z=gyro_z,
            roll=roll,
            pitch=pitch,
            yaw=yaw,
            temperature=temp
        )

        return asdict(imu_data)

    async def gps_oku(self) -> Optional[Dict[str, Any]]:
        """🗺️ GPS sensöründen veri oku"""
        try:
            if self.simulation_mode:
                return await self._simulation_gps_oku()
            else:
                return await self._real_gps_oku()
        except Exception as e:
            self.logger.error(f"❌ GPS okuma hatası: {e}")
            return None

    async def _simulation_gps_oku(self) -> Dict[str, Any]:
        """🧠 Akıllı GPS simülasyonu - Robot durumuna göre"""
        current_time = time.time()
        dt = current_time - self.robot_state.timestamp

        # Konum güncelleme
        self._update_position_simulation(dt)
        self.robot_state.timestamp = current_time

        # Robot durumuna göre GPS verisi
        if self.robot_state.state == "bekleme":
            # Bekleme modunda konum sabit, sadece minimal gürültü
            noise_lat = 0.000001 * math.sin(current_time * 0.01)  # Çok küçük gürültü
            noise_lon = 0.000001 * math.cos(current_time * 0.01)

            gps_data = GPSData(
                latitude=self.current_position["lat"] + noise_lat,
                longitude=self.current_position["lon"] + noise_lon,
                altitude=850.0 + 0.5 * math.sin(current_time * 0.02),  # Minimal yükseklik değişimi
                satellites=8,
                fix_quality=1,
                speed=0.0,  # Bekleme modunda hız sıfır
                course=self.robot_state.position["heading"],
                timestamp=datetime.now().isoformat()
            )

        elif self.robot_state.state in ["hareket", "gorev"]:
            # Hareket modunda gerçekçi konum değişimi
            # GPS hassasiyetine göre hafif gürültü ekle
            noise_lat = 0.00001 * math.sin(current_time * 0.5)
            noise_lon = 0.00001 * math.cos(current_time * 0.7)

            # Hız simülasyonu - robot hızına göre
            simulated_speed = abs(self.robot_state.linear_velocity) * 3.6  # m/s to km/h

            gps_data = GPSData(
                latitude=self.current_position["lat"] + noise_lat,
                longitude=self.current_position["lon"] + noise_lon,
                altitude=850.0 + 2 * math.sin(current_time * 0.1),
                satellites=7 + int(math.sin(current_time * 0.3)),  # 7-8 uydu
                fix_quality=1,
                speed=simulated_speed,
                course=self.robot_state.position["heading"],
                timestamp=datetime.now().isoformat()
            )

        elif self.robot_state.state == "sarj":
            # Şarj modunda konum tamamen sabit
            gps_data = GPSData(
                latitude=self.current_position["lat"],
                longitude=self.current_position["lon"],
                altitude=850.0,
                satellites=8,
                fix_quality=1,
                speed=0.0,
                course=self.robot_state.position["heading"],
                timestamp=datetime.now().isoformat()
            )

        else:
            # Varsayılan durum
            gps_data = GPSData(
                latitude=self.current_position["lat"],
                longitude=self.current_position["lon"],
                altitude=850.0,
                satellites=6,
                fix_quality=0,
                speed=0.0,
                course=0.0,
                timestamp=datetime.now().isoformat()
            )

        return asdict(gps_data)

    async def _real_gps_oku(self) -> Dict[str, Any]:
        """Gerçek GPS verisi"""
        self.gps.update()

        if not self.gps.has_fix:
            return {
                "latitude": 0.0,
                "longitude": 0.0,
                "altitude": 0.0,
                "satellites": self.gps.satellites,
                "fix_quality": 0,
                "speed": 0.0,
                "course": 0.0,
                "timestamp": datetime.now().isoformat()
            }

        gps_data = GPSData(
            latitude=self.gps.latitude,
            longitude=self.gps.longitude,
            altitude=self.gps.altitude_m or 0.0,
            satellites=self.gps.satellites or 0,
            fix_quality=self.gps.fix_quality or 0,
            speed=self.gps.speed_knots or 0.0,
            course=self.gps.track_angle_deg or 0.0,
            timestamp=datetime.now().isoformat()
        )

        return asdict(gps_data)

    async def batarya_oku(self) -> Optional[Dict[str, Any]]:
        """🔋 Batarya sensöründen veri oku"""
        try:
            if self.simulation_mode:
                return await self._simulation_batarya_oku()
            else:
                return await self._real_batarya_oku()
        except Exception as e:
            self.logger.error(f"❌ Batarya okuma hatası: {e}")
            return None

    async def _simulation_batarya_oku(self) -> Dict[str, Any]:
        """🧠 Akıllı batarya simülasyonu - Robot durumuna göre"""
        current_time = time.time()
        t = current_time - self.simulation_time_start

        # Config'ten batarya ayarlarını al
        battery_config = self.simulation_data.get('battery_config', {})
        initial_level = battery_config.get('initial_level', 85)
        base_drain_rate = battery_config.get('drain_rate', 0.1)  # %/hour
        base_current = self.simulation_data.get("battery_current", 1.2)

        # Robot durumuna göre batarya tüketimi
        if self.robot_state.state == "bekleme":
            # Bekleme modunda minimal tüketim
            drain_multiplier = 0.3  # %30 normal tüketim
            current_multiplier = 0.5  # %50 normal akım

        elif self.robot_state.state in ["hareket", "gorev"]:
            # Hareket modunda yüksek tüketim
            speed_factor = abs(self.robot_state.linear_velocity) + abs(self.robot_state.angular_velocity)
            drain_multiplier = 1.0 + speed_factor * 0.5  # Hıza göre artış
            current_multiplier = 1.0 + speed_factor * 0.3

        elif self.robot_state.state == "sarj":
            # Şarj modunda batarya seviyesi artıyor
            drain_multiplier = -2.0  # Negatif = şarj oluyor
            current_multiplier = -0.8  # Negatif akım = şarj akımı

        else:
            # Varsayılan normal tüketim
            drain_multiplier = 1.0
            current_multiplier = 1.0

        # Batarya seviyesi hesapla
        hours_passed = t / 3600  # saniye -> saat
        effective_drain = base_drain_rate * drain_multiplier * hours_passed
        current_level = initial_level - effective_drain

        # Şarj durumunda batarya seviyesini sınırla
        if self.robot_state.state == "sarj":
            current_level = min(100.0, current_level)  # %100'ü geçmesin
        else:
            current_level = max(10.0, current_level)  # %10'un altına düşmesin

        # Voltage ve current hesapla
        voltage = 12.6 * (current_level / 100) + 0.05 * math.sin(t * 0.2)
        current = base_current * current_multiplier + 0.1 * math.sin(t * 0.5)

        # Şarj durumunda voltage biraz daha yüksek
        if self.robot_state.state == "sarj":
            voltage += 0.5  # Şarj voltajı

        power_data = PowerData(
            voltage=max(10.0, voltage),  # Minimum 10V
            current=current,
            power=voltage * abs(current),
            level=current_level
        )

        return asdict(power_data)

    async def _real_batarya_oku(self) -> Dict[str, Any]:
        """Gerçek batarya verisi"""
        bus_voltage = self.ina219.bus_voltage
        shunt_voltage = self.ina219.shunt_voltage
        current = self.ina219.current / 1000  # mA to A
        power = self.ina219.power / 1000  # mW to W

        # Batarya seviyesi tahmin et (12V sistemi için)
        voltage = bus_voltage + shunt_voltage
        level = max(0, min(100, (voltage - 10.5) / (12.6 - 10.5) * 100))

        power_data = PowerData(
            voltage=voltage,
            current=current,
            power=power,
            level=level
        )

        return asdict(power_data)

    async def tampon_oku(self) -> Dict[str, bool]:
        """🚧 Ön tampon sensörü oku"""
        try:
            if self.simulation_mode:
                # Simülasyonda bazen engel var
                t = time.time()
                engel_var = (int(t) % 10) == 0  # Her 10 saniyede bir engel
                return {"front_bumper": engel_var}
            else:
                import RPi.GPIO as GPIO

                # Pull-up resistor kullanıldığı için False = basılı
                basili = not GPIO.input(self.tampon_pin)
                return {"front_bumper": basili}
        except Exception as e:
            self.logger.error(f"❌ Tampon okuma hatası: {e}")
            return {"front_bumper": False}

    async def kalibrasyon_yap(self):
        """🎯 Sensör kalibrasyonu yap"""
        self.logger.info("🎯 Sensör kalibrasyonu başlatılıyor...")

        if self.simulation_mode:
            self.logger.info("✅ Simülasyon kalibrasyonu tamamlandı")
            return

        try:
            # IMU kalibrasyonu için 100 örnek al
            accel_sum = {"x": 0, "y": 0, "z": 0}
            gyro_sum = {"x": 0, "y": 0, "z": 0}

            samples = 100
            for i in range(samples):
                accel_x, accel_y, accel_z = self.mpu.acceleration
                gyro_x, gyro_y, gyro_z = self.mpu.gyro

                accel_sum["x"] += accel_x
                accel_sum["y"] += accel_y
                accel_sum["z"] += accel_z - 9.81  # Gravity compensation

                gyro_sum["x"] += gyro_x
                gyro_sum["y"] += gyro_y
                gyro_sum["z"] += gyro_z

                await asyncio.sleep(0.01)  # 10ms bekleme

            # Ortalama hesapla
            self.imu_kalibrasyon["accel_offset"] = {
                "x": accel_sum["x"] / samples,
                "y": accel_sum["y"] / samples,
                "z": accel_sum["z"] / samples
            }
            self.imu_kalibrasyon["gyro_offset"] = {
                "x": gyro_sum["x"] / samples,
                "y": gyro_sum["y"] / samples,
                "z": gyro_sum["z"] / samples
            }

            self.logger.info("✅ IMU kalibrasyonu tamamlandı")
            self.logger.info(f"📊 Accel offset: {self.imu_kalibrasyon['accel_offset']}")
            self.logger.info(f"📊 Gyro offset: {self.imu_kalibrasyon['gyro_offset']}")

        except Exception as e:
            self.logger.error(f"❌ Kalibrasyon hatası: {e}")

    def get_sensor_durumu(self) -> Dict[str, Any]:
        """Sensör durumu bilgisi"""
        return {
            "aktif": self.sensors_aktif,
            "simülasyon": self.simulation_mode,
            "kalibrasyon": self.imu_kalibrasyon,
            "son_okuma": self.son_okuma_zamani.copy()
        }

    def __del__(self):
        """Sensör okuyucu kapatılıyor"""
        if hasattr(self, 'logger'):
            self.logger.info("👋 Sensör okuyucu kapatılıyor...")

        if not self.simulation_mode:
            try:
                import RPi.GPIO as GPIO
                GPIO.cleanup()
            except Exception:
                pass
