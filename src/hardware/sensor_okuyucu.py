"""
📡 Sensör Okuyucu - Robot'un Duyuları
Hacı Abi'nin sensör yönetimi burada!

Bu sınıf robot'un tüm sensörlerini okur:
- MPU-6050 IMU (ivmeölçer, jiroskop)
- GPS NEO-6M
- INA219 akım/voltaj sensörü
- Ön tampon sensörü
- Ultrasonik sensörler
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
class UltrasonikData:
    """Ultrasonik sensör verisi"""
    front: float
    left: float
    right: float
    back: float


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

                if sensor_type == 'ultrasonic':
                    # Ultrasonik sensör config'ini al
                    parsed_data[f'ultrasonic_{sensor_name}'] = {
                        'min_range': sensor.get('min_range', 0.02),
                        'max_range': sensor.get('max_range', 4.0),
                        'field_of_view': sensor.get('field_of_view', 15)
                    }
                elif sensor_type == 'imu':
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
            self.tampon_oku(),
            self.ultrasonik_oku()
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Sonuçları birleştir
        sensor_data = {
            "timestamp": datetime.now().isoformat(),
            "imu": results[0] if not isinstance(results[0], Exception) else None,
            "gps": results[1] if not isinstance(results[1], Exception) else None,
            "batarya": results[2] if not isinstance(results[2], Exception) else None,
            "tampon": results[3] if not isinstance(results[3], Exception) else None,
            "ultrasonik": results[4] if not isinstance(results[4], Exception) else None
        }

        # Hataları logla
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                sensor_names = ["IMU", "GPS", "Batarya", "Tampon", "Ultrasonik"]
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
        """Simülasyon IMU verisi - Config'ten alınan değerlerle"""
        # Zamanla biraz salınım ekle
        t = time.time() - self.simulation_time_start

        # Config'ten IMU ayarlarını al
        imu_config = self.simulation_data.get("imu_config", {})
        update_rate = imu_config.get('update_rate', 100)  # Hz

        # Update rate'e göre salınım frekansını ayarla
        freq_multiplier = update_rate / 100.0  # 100Hz'e göre normalize et

        # Simülasyon değerleri
        base_data = self.simulation_data.get("imu_orientation", {})

        imu_data = IMUData(
            accel_x=0.1 * math.sin(t * 0.5 * freq_multiplier),
            accel_y=0.1 * math.cos(t * 0.3 * freq_multiplier),
            accel_z=9.81 + 0.05 * math.sin(t * freq_multiplier),
            gyro_x=0.02 * math.sin(t * 0.8 * freq_multiplier),
            gyro_y=0.02 * math.cos(t * 0.6 * freq_multiplier),
            gyro_z=0.01 * math.sin(t * 0.4 * freq_multiplier),
            roll=base_data.get("roll", 0) + 2 * math.sin(t * 0.2 * freq_multiplier),
            pitch=base_data.get("pitch", 0) + 1 * math.cos(t * 0.3 * freq_multiplier),
            yaw=base_data.get("yaw", 0) + 0.5 * t % 360,
            temperature=25.0 + 2 * math.sin(t * 0.1 * freq_multiplier)
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
        """Simülasyon GPS verisi"""
        base_coords = self.simulation_data.get("gps_coordinates", {})
        t = time.time() - self.simulation_time_start

        # Rastgele hareket simülasyonu
        lat_offset = 0.0001 * math.sin(t * 0.1)
        lon_offset = 0.0001 * math.cos(t * 0.1)

        gps_data = GPSData(
            latitude=base_coords.get("lat", 39.9334) + lat_offset,
            longitude=base_coords.get("lon", 32.8597) + lon_offset,
            altitude=850.0 + 5 * math.sin(t * 0.05),
            satellites=8,
            fix_quality=1,
            speed=0.5 + 0.2 * math.sin(t * 0.3),
            course=45.0 + 10 * math.sin(t * 0.2),
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
        """Simülasyon batarya verisi - Config'ten alınan değerlerle"""
        t = time.time() - self.simulation_time_start

        # Config'ten batarya ayarlarını al
        battery_config = self.simulation_data.get('battery_config', {})
        initial_level = battery_config.get('initial_level', 85)
        drain_rate = battery_config.get('drain_rate', 0.1)  # %/hour

        # Batarya yavaş yavaş azalır
        base_current = self.simulation_data.get("battery_current", 1.2)

        # Batarya seviyesi zamanla azalır (drain_rate kullanılıyor)
        hours_passed = t / 3600  # saniye -> saat
        current_level = max(20.0, initial_level - (hours_passed * drain_rate))

        # Voltage seviyeye göre hesapla
        voltage = 12.6 * (current_level / 100) + 0.1 * math.sin(t * 0.2)
        current = base_current + 0.3 * math.sin(t * 0.5)

        power_data = PowerData(
            voltage=voltage,
            current=current,
            power=voltage * current,
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

    async def ultrasonik_oku(self) -> Optional[Dict[str, Any]]:
        """📏 Ultrasonik sensörlerden mesafe oku"""
        try:
            if self.simulation_mode:
                return await self._simulation_ultrasonik_oku()
            else:
                return await self._real_ultrasonik_oku()
        except Exception as e:
            self.logger.error(f"❌ Ultrasonik okuma hatası: {e}")
            return None

    async def _simulation_ultrasonik_oku(self) -> Dict[str, Any]:
        """Simülasyon ultrasonik verisi - Config'den alınan değerlerle"""
        t = time.time() - self.simulation_time_start

        # Config'ten sensör ayarlarını al
        front_config = self.simulation_data.get('ultrasonic_front', {})
        left_config = self.simulation_data.get('ultrasonic_left', {})
        right_config = self.simulation_data.get('ultrasonic_right', {})

        # Varsayılan değerler
        default_min = 0.02
        default_max = 4.0

        # Her sensör için dinamik mesafe hesapla
        front_min = front_config.get('min_range', default_min)
        front_max = front_config.get('max_range', default_max)
        front_distance = front_min + (front_max - front_min) * (0.5 + 0.3 * math.sin(t * 0.3))

        left_min = left_config.get('min_range', default_min)
        left_max = left_config.get('max_range', default_max)
        left_distance = left_min + (left_max - left_min) * (0.4 + 0.2 * math.cos(t * 0.4))

        right_min = right_config.get('min_range', default_min)
        right_max = right_config.get('max_range', default_max)
        right_distance = right_min + (right_max - right_min) * (0.45 + 0.25 * math.sin(t * 0.2))

        # Simülasyonda back sensörü yok config'de, varsayılan değerler kullan
        back_distance = 3.0 + 0.2 * math.cos(t * 0.1)

        ultrasonik_data = UltrasonikData(
            front=front_distance,
            left=left_distance,
            right=right_distance,
            back=back_distance
        )

        return asdict(ultrasonik_data)

    async def _real_ultrasonik_oku(self) -> Dict[str, Any]:
        """Gerçek ultrasonik verisi - Config'ten pin'leri al"""
        try:
            # Config'ten ultrasonik sensör ayarlarını al
            distances = {}

            # Config'ten ultrasonik sensör pin'lerini al
            ultrasonic_sensors = self.config.get("ultrasonic_sensors", {})

            # Varsayılan HC-SR04 sensör pin konfigürasyonu
            default_pins = {
                'front': {'trigger': 23, 'echo': 24},
                'left': {'trigger': 25, 'echo': 8},
                'right': {'trigger': 7, 'echo': 1},
                'back': {'trigger': 12, 'echo': 16}
            }

            # Config'ten pin'leri al, yoksa varsayılan değerleri kullan
            ultrasonic_config = {}
            for position, default_config in default_pins.items():
                sensor_config = ultrasonic_sensors.get(position, {})
                ultrasonic_config[position] = {
                    'trigger': sensor_config.get('trigger_pin', default_config['trigger']),
                    'echo': sensor_config.get('echo_pin', default_config['echo'])
                }

            import RPi.GPIO as GPIO
            import time

            # Her sensör için mesafe ölç
            for position, pins in ultrasonic_config.items():
                try:
                    trigger_pin = pins['trigger']
                    echo_pin = pins['echo']

                    # Pin'leri ayarla
                    GPIO.setup(trigger_pin, GPIO.OUT)
                    GPIO.setup(echo_pin, GPIO.IN)

                    # Trigger sinyali gönder
                    GPIO.output(trigger_pin, True)
                    await asyncio.sleep(0.00001)  # 10 microsecond
                    GPIO.output(trigger_pin, False)

                    # Echo'yu bekle
                    start_time = time.time()
                    timeout = start_time + 0.1  # 100ms timeout

                    # Echo yüksek olana kadar bekle
                    while GPIO.input(echo_pin) == 0:
                        start_time = time.time()
                        if start_time > timeout:
                            raise TimeoutError("Echo başlangıcı timeout")

                    # Echo alçak olana kadar bekle
                    while GPIO.input(echo_pin) == 1:
                        stop_time = time.time()
                        if stop_time > timeout:
                            raise TimeoutError("Echo bitişi timeout")

                    # Mesafe hesapla (ses hızı: 343 m/s)
                    time_elapsed = stop_time - start_time
                    distance = (time_elapsed * 343) / 2  # Gidip gelme mesafesi

                    # Mesafe sınırları (2cm - 400cm)
                    if distance < 0.02:
                        distance = 0.02
                    elif distance > 4.0:
                        distance = 4.0

                    distances[position] = distance

                    self.logger.debug(f"📏 {position} ultrasonik: {distance:.2f}m (Trigger:{trigger_pin}, Echo:{echo_pin})")

                except Exception as e:
                    self.logger.warning(f"⚠️ {position} ultrasonik sensör hatası: {e}")
                    # Hata durumunda max mesafe kullan
                    distances[position] = 4.0

            ultrasonik_data = UltrasonikData(
                front=distances.get('front', 4.0),
                left=distances.get('left', 4.0),
                right=distances.get('right', 4.0),
                back=distances.get('back', 4.0)
            )

            return asdict(ultrasonik_data)

        except Exception as e:
            self.logger.error(f"❌ Ultrasonik okuma hatası: {e}")
            # Hata durumunda simülasyon verisi dön
            return await self._simulation_ultrasonik_oku()

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
