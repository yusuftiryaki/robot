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
import logging
import time
import json
import math
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


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
    
    def __init__(self, sensor_config: Dict[str, Any]):
        self.config = sensor_config
        self.logger = logging.getLogger("SensorOkuyucu")
        
        # Simülasyon modu kontrolü
        self.simulation_mode = self._is_simulation()
        
        # Sensör durumları
        self.sensors_aktif = False
        self.son_okuma_zamani = {}
        
        # Kalibrasyon verileri
        self.imu_kalibrasyon = {
            "accel_offset": {"x": 0, "y": 0, "z": 0},
            "gyro_offset": {"x": 0, "y": 0, "z": 0}
        }
        
        # Simülasyon verileri
        self.simulation_data = self._load_simulation_data()
        self.simulation_time_start = time.time()
        
        self.logger.info(f"📡 Sensör okuyucu başlatıldı (Simülasyon: {self.simulation_mode})")
        self._init_sensors()
    
    def _is_simulation(self) -> bool:
        """Simülasyon modunda mı kontrol et"""
        try:
            import board
            return False
        except ImportError:
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
        """Gerçek sensörleri başlat"""
        self.logger.info("🔧 Fiziksel sensörler başlatılıyor...")
        try:
            import board
            import busio
            import adafruit_mpu6050
            import adafruit_ina219
            import adafruit_gps
            import serial
            
            # I2C Bus
            i2c = busio.I2C(board.SCL, board.SDA)
            
            # MPU-6050 IMU
            self.mpu = adafruit_mpu6050.MPU6050(i2c)
            self.logger.info("✅ MPU-6050 IMU başlatıldı")
            
            # INA219 Güç sensörü
            self.ina219 = adafruit_ina219.INA219(i2c)
            self.logger.info("✅ INA219 güç sensörü başlatıldı")
            
            # GPS UART
            uart = serial.Serial(
                "/dev/ttyS0",  # Raspberry Pi UART
                baudrate=9600,
                timeout=10
            )
            self.gps = adafruit_gps.GPS(uart, debug=False)
            self.gps.send_command(b"PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0")
            self.gps.send_command(b"PMTK220,1000")
            self.logger.info("✅ GPS NEO-6M başlatıldı")
            
            # Ön tampon sensörü
            import RPi.GPIO as GPIO
            self.tampon_pin = self.config.get("front_bumper", {}).get("pin", 16)
            GPIO.setup(self.tampon_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            self.logger.info(f"✅ Ön tampon sensörü başlatıldı (Pin {self.tampon_pin})")
            
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
        """Simülasyon IMU verisi"""
        # Zamanla biraz salınım ekle
        t = time.time() - self.simulation_time_start
        
        # Simülasyon değerleri
        base_data = self.simulation_data.get("imu_orientation", {})
        
        imu_data = IMUData(
            accel_x=0.1 * math.sin(t * 0.5),
            accel_y=0.1 * math.cos(t * 0.3),
            accel_z=9.81 + 0.05 * math.sin(t),
            gyro_x=0.02 * math.sin(t * 0.8),
            gyro_y=0.02 * math.cos(t * 0.6),
            gyro_z=0.01 * math.sin(t * 0.4),
            roll=base_data.get("roll", 0) + 2 * math.sin(t * 0.2),
            pitch=base_data.get("pitch", 0) + 1 * math.cos(t * 0.3),
            yaw=base_data.get("yaw", 0) + 0.5 * t % 360,
            temperature=25.0 + 2 * math.sin(t * 0.1)
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
        """Simülasyon batarya verisi"""
        t = time.time() - self.simulation_time_start
        
        # Batarya yavaş yavaş azalır
        base_voltage = self.simulation_data.get("battery_voltage", 12.5)
        base_current = self.simulation_data.get("battery_current", 1.2)
        
        # Batarya seviyesi zamanla azalır
        discharge_rate = 0.001  # %0.1 per dakika
        level = max(20.0, 100.0 - (t / 60) * discharge_rate)
        
        voltage = base_voltage * (level / 100) + 0.1 * math.sin(t * 0.2)
        current = base_current + 0.3 * math.sin(t * 0.5)
        
        power_data = PowerData(
            voltage=voltage,
            current=current,
            power=voltage * current,
            level=level
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
        """Simülasyon ultrasonik verisi"""
        t = time.time() - self.simulation_time_start
        
        # Rastgele engel mesafeleri
        ultrasonik_data = UltrasonikData(
            front=2.0 + 0.5 * math.sin(t * 0.3),
            left=1.5 + 0.3 * math.cos(t * 0.4),
            right=1.8 + 0.4 * math.sin(t * 0.2),
            back=3.0 + 0.2 * math.cos(t * 0.1)
        )
        
        return asdict(ultrasonik_data)
    
    async def _real_ultrasonik_oku(self) -> Dict[str, Any]:
        """Gerçek ultrasonik verisi"""
        # Bu fonksiyon ultrasonik sensör bağlandığında tamamlanacak
        # Şimdilik simülasyon verisi dön
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
            except:
                pass
