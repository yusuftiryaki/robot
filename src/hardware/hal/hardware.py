"""
🔧 Gerçek Donanım HAL - Raspberry Pi Implementation
Hacı Abi'nin gerçek donanım magic'i burada!

Bu modül, Raspberry Pi üzerinde gerçek donanım bileşenlerini kontrol eder.
Simülasyon implementasyonu ile aynı arayüzü kullanır.
"""

import asyncio
import logging
import math
import os
import time
from datetime import datetime
from typing import Any, Dict, Optional

from .interfaces import (
    AcilDurmaInterface,
    AcilDurmaVeri,
    EnkoderInterface,
    EnkoderVeri,
    GPSInterface,
    GPSVeri,
    GucInterface,
    GucVeri,
    HardwareFactory,
    IMUInterface,
    IMUVeri,
    MotorDurumuVeri,
    MotorInterface,
    TamponInterface,
    TamponVeri,
)

# Gerçek donanım importları - conditionally import
try:
    # RPi.GPIO sadece gerçek Raspberry Pi'de import edilecek
    import os
    if os.path.exists('/sys/class/gpio'):
        import RPi.GPIO as GPIO
        import serial
        import smbus
        GPIO_AVAILABLE = True
    else:
        GPIO_AVAILABLE = False
        raise ImportError("Raspberry Pi GPIO not detected")

    # Adafruit kütüphaneleri
    try:
        import adafruit_gps
        import adafruit_ina219
        import adafruit_mpu6050
        ADAFRUIT_AVAILABLE = True
    except ImportError:
        ADAFRUIT_AVAILABLE = False

except ImportError:
    GPIO_AVAILABLE = False
    ADAFRUIT_AVAILABLE = False
    print("⚠️ GPIO kütüphaneleri yüklü değil - sadece simülasyon modunda çalışabilir")


class GercekIMU(IMUInterface):
    """Gerçek MPU6050 IMU sensörü"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger("GercekIMU")
        self.aktif = False
        self.mpu6050 = None
        self.i2c_bus = None
        self.kalibrasyon_verisi = {
            "ivme_offset": {"x": 0.0, "y": 0.0, "z": 0.0},
            "gyro_offset": {"x": 0.0, "y": 0.0, "z": 0.0}
        }

    async def baslat(self) -> bool:
        """IMU sensörünü başlat"""
        if not ADAFRUIT_AVAILABLE:
            self.logger.error("❌ Adafruit kütüphaneleri mevcut değil")
            return False

        try:
            # I2C bus başlat
            import board
            import busio
            self.i2c_bus = busio.I2C(board.SCL, board.SDA)

            # MPU6050 başlat
            self.mpu6050 = adafruit_mpu6050.MPU6050(self.i2c_bus)

            self.aktif = True
            self.logger.info("✅ Gerçek MPU6050 IMU başlatıldı")
            return True

        except Exception as e:
            self.logger.error(f"❌ IMU başlatma hatası: {e}")
            return False

    async def durdur(self):
        """IMU sensörünü durdur"""
        try:
            if self.i2c_bus:
                self.i2c_bus.deinit()
            self.aktif = False
            self.logger.info("🛑 Gerçek IMU durduruldu")
        except Exception as e:
            self.logger.error(f"⚠️ IMU durdurma hatası: {e}")

    async def veri_oku(self) -> Optional[IMUVeri]:
        """IMU verisi oku"""
        if not self.aktif or not self.mpu6050:
            return None

        try:
            # MPU6050'den veri oku
            accel = self.mpu6050.acceleration
            gyro = self.mpu6050.gyro
            temp = self.mpu6050.temperature

            # Kalibrasyon uygula
            accel_x = accel[0] - self.kalibrasyon_verisi["ivme_offset"]["x"]
            accel_y = accel[1] - self.kalibrasyon_verisi["ivme_offset"]["y"]
            accel_z = accel[2] - self.kalibrasyon_verisi["ivme_offset"]["z"]

            gyro_x = gyro[0] - self.kalibrasyon_verisi["gyro_offset"]["x"]
            gyro_y = gyro[1] - self.kalibrasyon_verisi["gyro_offset"]["y"]
            gyro_z = gyro[2] - self.kalibrasyon_verisi["gyro_offset"]["z"]

            # Roll, pitch, yaw hesapla (basit)
            import math
            roll = math.atan2(accel_y, accel_z) * 180 / math.pi
            pitch = math.atan2(-accel_x, math.sqrt(accel_y**2 + accel_z**2)) * 180 / math.pi
            # Yaw için magnetometre gerekli, şimdilik 0
            yaw = 0.0

            return IMUVeri(
                timestamp=datetime.now().isoformat(),
                gecerli=True,
                ivme_x=accel_x,
                ivme_y=accel_y,
                ivme_z=accel_z,
                acisal_hiz_x=gyro_x,
                acisal_hiz_y=gyro_y,
                acisal_hiz_z=gyro_z,
                roll=roll,
                pitch=pitch,
                yaw=yaw,
                sicaklik=temp
            )

        except Exception as e:
            self.logger.error(f"❌ IMU veri okuma hatası: {e}")
            return IMUVeri(
                timestamp=datetime.now().isoformat(),
                gecerli=False,
                hata_mesaji=str(e),
                ivme_x=0.0, ivme_y=0.0, ivme_z=0.0,
                acisal_hiz_x=0.0, acisal_hiz_y=0.0, acisal_hiz_z=0.0,
                roll=0.0, pitch=0.0, yaw=0.0, sicaklik=0.0
            )

    async def kalibrasyon_yap(self) -> bool:
        """IMU kalibrasyonu yap"""
        if not self.aktif or not self.mpu6050:
            return False

        try:
            self.logger.info("🎯 IMU kalibrasyonu başlatılıyor...")

            # 100 örnek al
            accel_sum = {"x": 0, "y": 0, "z": 0}
            gyro_sum = {"x": 0, "y": 0, "z": 0}

            samples = 100
            for i in range(samples):
                accel = self.mpu6050.acceleration
                gyro = self.mpu6050.gyro

                accel_sum["x"] += accel[0]
                accel_sum["y"] += accel[1]
                accel_sum["z"] += accel[2] - 9.81  # Yerçekimi kompansasyonu

                gyro_sum["x"] += gyro[0]
                gyro_sum["y"] += gyro[1]
                gyro_sum["z"] += gyro[2]

                await asyncio.sleep(0.01)  # 10ms bekleme

            # Ortalama hesapla
            self.kalibrasyon_verisi["ivme_offset"] = {
                "x": accel_sum["x"] / samples,
                "y": accel_sum["y"] / samples,
                "z": accel_sum["z"] / samples
            }
            self.kalibrasyon_verisi["gyro_offset"] = {
                "x": gyro_sum["x"] / samples,
                "y": gyro_sum["y"] / samples,
                "z": gyro_sum["z"] / samples
            }

            self.logger.info("✅ IMU kalibrasyonu tamamlandı")
            self.logger.info(f"📊 Accel offset: {self.kalibrasyon_verisi['ivme_offset']}")
            self.logger.info(f"📊 Gyro offset: {self.kalibrasyon_verisi['gyro_offset']}")
            return True

        except Exception as e:
            self.logger.error(f"❌ IMU kalibrasyon hatası: {e}")
            return False

    def saglikli_mi(self) -> bool:
        """IMU sağlıklı mı?"""
        return self.aktif and self.mpu6050 is not None


class GercekGPS(GPSInterface):
    """Gerçek GPS NEO-6M sensörü"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger("GercekGPS")
        self.aktif = False
        self.gps = None
        self.serial_port = None

    async def baslat(self) -> bool:
        """GPS sensörünü başlat"""
        if not ADAFRUIT_AVAILABLE:
            self.logger.error("❌ Adafruit kütüphaneleri mevcut değil")
            return False

        try:
            # Seri port başlat
            port = self.config.get("device", "/dev/ttyS0")
            baudrate = self.config.get("baud_rate", 9600)

            self.serial_port = serial.Serial(port, baudrate, timeout=10)
            self.gps = adafruit_gps.GPS(self.serial_port, debug=False)

            # GPS ayarları
            self.gps.send_command(b"PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0")
            self.gps.send_command(b"PMTK220,1000")  # 1 Hz güncelleme

            self.aktif = True
            self.logger.info(f"✅ Gerçek GPS {port} üzerinde başlatıldı")
            return True

        except Exception as e:
            self.logger.error(f"❌ GPS başlatma hatası: {e}")
            return False

    async def durdur(self):
        """GPS sensörünü durdur"""
        try:
            if self.serial_port:
                self.serial_port.close()
            self.aktif = False
            self.logger.info("🛑 Gerçek GPS durduruldu")
        except Exception as e:
            self.logger.error(f"⚠️ GPS durdurma hatası: {e}")

    async def veri_oku(self) -> Optional[GPSVeri]:
        """GPS verisi oku"""
        if not self.aktif or not self.gps:
            return None

        try:
            # GPS verisi güncelle
            self.gps.update()

            if self.gps.has_fix:
                return GPSVeri(
                    timestamp=datetime.now().isoformat(),
                    gecerli=True,
                    enlem=self.gps.latitude,
                    boylam=self.gps.longitude,
                    yukseklik=self.gps.altitude_m or 0.0,
                    uydu_sayisi=self.gps.satellites or 0,
                    fix_kalitesi=self.gps.fix_quality or 0,
                    hiz=self.gps.speed_knots or 0.0,
                    yön=self.gps.track_angle_deg or 0.0
                )
            else:
                return GPSVeri(
                    timestamp=datetime.now().isoformat(),
                    gecerli=False,
                    hata_mesaji="GPS fix yok",
                    enlem=0.0, boylam=0.0, yukseklik=0.0,
                    uydu_sayisi=0, fix_kalitesi=0, hiz=0.0, yön=0.0
                )

        except Exception as e:
            self.logger.error(f"❌ GPS veri okuma hatası: {e}")
            return GPSVeri(
                timestamp=datetime.now().isoformat(),
                gecerli=False,
                hata_mesaji=str(e),
                enlem=0.0, boylam=0.0, yukseklik=0.0,
                uydu_sayisi=0, fix_kalitesi=0, hiz=0.0, yön=0.0
            )

    def saglikli_mi(self) -> bool:
        """GPS sağlıklı mı?"""
        return self.aktif and self.gps is not None


class GercekGuc(GucInterface):
    """Gerçek INA219 güç sensörü"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger("GercekGuc")
        self.aktif = False
        self.ina219 = None
        self.i2c_bus = None

    async def baslat(self) -> bool:
        """Güç sensörünü başlat"""
        if not ADAFRUIT_AVAILABLE:
            self.logger.error("❌ Adafruit kütüphaneleri mevcut değil")
            return False

        try:
            # I2C bus başlat
            import board
            import busio
            self.i2c_bus = busio.I2C(board.SCL, board.SDA)

            # INA219 başlat
            self.ina219 = adafruit_ina219.INA219(self.i2c_bus)

            self.aktif = True
            self.logger.info("✅ Gerçek INA219 güç sensörü başlatıldı")
            return True

        except Exception as e:
            self.logger.error(f"❌ Güç sensörü başlatma hatası: {e}")
            return False

    async def durdur(self):
        """Güç sensörünü durdur"""
        try:
            if self.i2c_bus:
                self.i2c_bus.deinit()
            self.aktif = False
            self.logger.info("🛑 Gerçek güç sensörü durduruldu")
        except Exception as e:
            self.logger.error(f"⚠️ Güç sensörü durdurma hatası: {e}")

    async def veri_oku(self) -> Optional[GucVeri]:
        """Güç verisi oku"""
        if not self.aktif or not self.ina219:
            return None

        try:
            # INA219'dan veri oku
            voltage = self.ina219.bus_voltage + self.ina219.shunt_voltage
            current = self.ina219.current
            power = self.ina219.power

            # Batarya seviyesi hesapla (12V sistemi için)
            min_volt = self.config.get("min_voltage", 10.5)
            max_volt = self.config.get("max_voltage", 12.6)
            level = max(0, min(100, (voltage - min_volt) / (max_volt - min_volt) * 100))

            return GucVeri(
                timestamp=datetime.now().isoformat(),
                gecerli=True,
                voltaj=voltage,
                akim=current,
                guc=power,
                batarya_seviyesi=level
            )

        except Exception as e:
            self.logger.error(f"❌ Güç veri okuma hatası: {e}")
            return GucVeri(
                timestamp=datetime.now().isoformat(),
                gecerli=False,
                hata_mesaji=str(e),
                voltaj=0.0, akim=0.0, guc=0.0, batarya_seviyesi=0.0
            )

    def saglikli_mi(self) -> bool:
        """Güç sensörü sağlıklı mı?"""
        return self.aktif and self.ina219 is not None


class GercekTampon(TamponInterface):
    """Gerçek tampon sensörü (GPIO)"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger("GercekTampon")
        self.aktif = False
        self.pin = self.config.get("pin", 16)

    async def baslat(self) -> bool:
        """Tampon sensörünü başlat"""
        if not GPIO_AVAILABLE:
            self.logger.error("❌ RPi.GPIO mevcut değil")
            return False

        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

            self.aktif = True
            self.logger.info(f"✅ Gerçek tampon sensörü pin {self.pin} üzerinde başlatıldı")
            return True

        except Exception as e:
            self.logger.error(f"❌ Tampon sensörü başlatma hatası: {e}")
            return False

    async def durdur(self):
        """Tampon sensörünü durdur"""
        try:
            if GPIO_AVAILABLE:
                GPIO.cleanup(self.pin)
            self.aktif = False
            self.logger.info("🛑 Gerçek tampon sensörü durduruldu")
        except Exception as e:
            self.logger.error(f"⚠️ Tampon sensörü durdurma hatası: {e}")

    async def veri_oku(self) -> Optional[TamponVeri]:
        """Tampon verisi oku"""
        if not self.aktif or not GPIO_AVAILABLE:
            return None

        try:
            # Pull-up resistor kullanıldığı için False = basılı
            basildi = not GPIO.input(self.pin)

            return TamponVeri(
                timestamp=datetime.now().isoformat(),
                gecerli=True,
                basildi=basildi
            )

        except Exception as e:
            self.logger.error(f"❌ Tampon veri okuma hatası: {e}")
            return TamponVeri(
                timestamp=datetime.now().isoformat(),
                gecerli=False,
                hata_mesaji=str(e),
                basildi=False
            )

    def saglikli_mi(self) -> bool:
        """Tampon sensörü sağlıklı mı?"""
        return self.aktif


class GercekEnkoder(EnkoderInterface):
    """Gerçek encoder sensörü (GPIO)"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger("GercekEnkoder")
        self.aktif = False
        self.sol_pin_a = self.config.get("left_pin_a", 18)
        self.sol_pin_b = self.config.get("left_pin_b", 19)
        self.sag_pin_a = self.config.get("right_pin_a", 20)
        self.sag_pin_b = self.config.get("right_pin_b", 21)
        self.sol_sayac = 0
        self.sag_sayac = 0

    async def baslat(self) -> bool:
        """Encoder sensörünü başlat"""
        if not GPIO_AVAILABLE:
            self.logger.error("❌ RPi.GPIO mevcut değil")
            return False

        try:
            GPIO.setmode(GPIO.BCM)

            # Sol encoder
            GPIO.setup(self.sol_pin_a, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.sol_pin_b, GPIO.IN, pull_up_down=GPIO.PUD_UP)

            # Sağ encoder
            GPIO.setup(self.sag_pin_a, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.sag_pin_b, GPIO.IN, pull_up_down=GPIO.PUD_UP)

            # Interrupt handler'ları ekle
            GPIO.add_event_detect(self.sol_pin_a, GPIO.BOTH, callback=self._sol_encoder_callback)
            GPIO.add_event_detect(self.sag_pin_a, GPIO.BOTH, callback=self._sag_encoder_callback)

            self.aktif = True
            self.logger.info("✅ Gerçek encoder sensörleri başlatıldı")
            return True

        except Exception as e:
            self.logger.error(f"❌ Encoder sensörü başlatma hatası: {e}")
            return False

    async def durdur(self):
        """Encoder sensörünü durdur"""
        try:
            if GPIO_AVAILABLE:
                GPIO.remove_event_detect(self.sol_pin_a)
                GPIO.remove_event_detect(self.sag_pin_a)
                GPIO.cleanup([self.sol_pin_a, self.sol_pin_b, self.sag_pin_a, self.sag_pin_b])
            self.aktif = False
            self.logger.info("🛑 Gerçek encoder sensörleri durduruldu")
        except Exception as e:
            self.logger.error(f"⚠️ Encoder sensörü durdurma hatası: {e}")

    def _sol_encoder_callback(self, channel):
        """Sol encoder interrupt handler"""
        try:
            a_state = GPIO.input(self.sol_pin_a)
            b_state = GPIO.input(self.sol_pin_b)

            if a_state != b_state:
                self.sol_sayac += 1
            else:
                self.sol_sayac -= 1
        except Exception as e:
            self.logger.error(f"⚠️ Sol encoder callback hatası: {e}")

    def _sag_encoder_callback(self, channel):
        """Sağ encoder interrupt handler"""
        try:
            a_state = GPIO.input(self.sag_pin_a)
            b_state = GPIO.input(self.sag_pin_b)

            if a_state != b_state:
                self.sag_sayac += 1
            else:
                self.sag_sayac -= 1
        except Exception as e:
            self.logger.error(f"⚠️ Sağ encoder callback hatası: {e}")

    async def veri_oku(self) -> Optional[EnkoderVeri]:
        """Encoder verisi oku"""
        if not self.aktif:
            return None

        try:
            return EnkoderVeri(
                timestamp=datetime.now().isoformat(),
                gecerli=True,
                sol_teker=self.sol_sayac,
                sag_teker=self.sag_sayac
            )

        except Exception as e:
            self.logger.error(f"❌ Encoder veri okuma hatası: {e}")
            return EnkoderVeri(
                timestamp=datetime.now().isoformat(),
                gecerli=False,
                hata_mesaji=str(e),
                sol_teker=0,
                sag_teker=0
            )

    def saglikli_mi(self) -> bool:
        """Encoder sensörü sağlıklı mı?"""
        return self.aktif


class GercekAcilDurma(AcilDurmaInterface):
    """Gerçek acil durdurma butonu"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger("GercekAcilDurma")
        self.saglik_durumu = True

        self.pin = config.get('pin', 22)  # Default GPIO 22

        if GPIO_AVAILABLE:
            try:
                GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                self.logger.info(f"Acil durdurma butonu GPIO {self.pin} başlatıldı")
            except Exception as e:
                self.logger.error(f"Acil durdurma butonu GPIO kurulumu hatası: {e}")
                self.saglik_durumu = False

    async def baslat(self) -> bool:
        """Acil durdurma butonunu başlat"""
        self.logger.debug("Gerçek acil durdurma butonu başlatıldı")
        return self.saglik_durumu

    async def durdur(self):
        """Acil durdurma butonunu durdur"""
        self.logger.debug("Gerçek acil durdurma butonu durduruldu")

    async def veri_oku(self) -> Optional[AcilDurmaVeri]:
        """Acil durdurma verisi oku"""
        try:
            if not GPIO_AVAILABLE:
                return AcilDurmaVeri(
                    timestamp=datetime.now().isoformat(),
                    gecerli=False,
                    hata_mesaji="GPIO kütüphanesi yok"
                )

            # Pull-up direnciyle buton basılı = LOW
            buton_basildi = not GPIO.input(self.pin)

            return AcilDurmaVeri(
                timestamp=datetime.now().isoformat(),
                gecerli=True,
                aktif=buton_basildi
            )

        except Exception as e:
            self.logger.error(f"Acil durdurma verisi okunamadı: {e}")
            return AcilDurmaVeri(
                timestamp=datetime.now().isoformat(),
                gecerli=False,
                hata_mesaji=str(e)
            )

    def saglikli_mi(self) -> bool:
        """Acil durdurma sağlıklı mı?"""
        return self.saglik_durumu and GPIO_AVAILABLE


class GercekMotor(MotorInterface):
    """Gerçek motor kontrolcüsü - L298N sürücüler için"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger("GercekMotor")
        self.saglik_durumu = True

        # Motor durumları
        self.motor_durumu = MotorDurumuVeri(
            sol_hiz=0.0,
            sag_hiz=0.0,
            ana_firca=False,
            sol_firca=False,
            sag_firca=False,
            fan=False,
            motorlar_aktif=False
        )

        # GPIO motor nesneleri
        self.gpio_motors = {}

        # Motor fizik parametreleri
        self.max_hiz = config.get("max_linear_speed", 0.5)  # m/s
        self.tekerlek_base = config.get("wheel_base", 0.235)  # metre

        # Motor başlatılırken GPIO'ları kur
        self._init_gpio_motors()

    def _init_gpio_motors(self):
        """GPIO motor objelerini başlat"""
        if not GPIO_AVAILABLE:
            self.logger.error("❌ GPIO kütüphanesi yok - motor başlatılamıyor")
            self.saglik_durumu = False
            return

        try:
            # gpiozero kütüphanesini import et
            from gpiozero import DigitalOutputDevice, Motor, PWMOutputDevice

            # L298N #1 - Tekerlek motorları
            wheels_config = self.config.get('wheels', {})

            # Sol tekerlek (L298N #1 Motor A)
            sol_wheel = wheels_config.get('left', {})
            if sol_wheel and sol_wheel.get('pin_a') and sol_wheel.get('pin_b'):
                self.gpio_motors['sol_tekerlek'] = {
                    'motor_obj': Motor(
                        forward=sol_wheel.get('pin_a'),    # IN1
                        backward=sol_wheel.get('pin_b'),   # IN2
                        pwm=True
                    )
                }

            # Sağ tekerlek (L298N #1 Motor B)
            sag_wheel = wheels_config.get('right', {})
            if sag_wheel and sag_wheel.get('pin_a') and sag_wheel.get('pin_b'):
                self.gpio_motors['sag_tekerlek'] = {
                    'motor_obj': Motor(
                        forward=sag_wheel.get('pin_a'),    # IN3
                        backward=sag_wheel.get('pin_b'),   # IN4
                        pwm=True
                    )
                }

            # L298N #2 & #3 - Fırça ve fan motorları (DigitalOutput olarak)
            brushes_config = self.config.get('brushes', {})
            main_systems = self.config.get('main_systems', {})

            # Ana fırça
            ana_brush = main_systems.get('brush', {})
            if ana_brush and ana_brush.get('pin_a') and ana_brush.get('pin_b'):
                self.gpio_motors['ana_firca'] = {
                    'pin_a_obj': DigitalOutputDevice(ana_brush.get('pin_a')),
                    'pin_b_obj': DigitalOutputDevice(ana_brush.get('pin_b'))
                }

            # Sol yan fırça
            sol_brush = brushes_config.get('side_left', {})
            if sol_brush and sol_brush.get('pin_a') and sol_brush.get('pin_b'):
                self.gpio_motors['sol_firca'] = {
                    'pin_a_obj': DigitalOutputDevice(sol_brush.get('pin_a')),
                    'pin_b_obj': DigitalOutputDevice(sol_brush.get('pin_b'))
                }

            # Sağ yan fırça
            sag_brush = brushes_config.get('side_right', {})
            if sag_brush and sag_brush.get('pin_a') and sag_brush.get('pin_b'):
                self.gpio_motors['sag_firca'] = {
                    'pin_a_obj': DigitalOutputDevice(sag_brush.get('pin_a')),
                    'pin_b_obj': DigitalOutputDevice(sag_brush.get('pin_b'))
                }

            # Fan
            fan_config = main_systems.get('fan', {})
            if fan_config and fan_config.get('pin_a') and fan_config.get('pin_b'):
                self.gpio_motors['fan'] = {
                    'pin_a_obj': DigitalOutputDevice(fan_config.get('pin_a')),
                    'pin_b_obj': DigitalOutputDevice(fan_config.get('pin_b'))
                }

            self.logger.info("✅ Gerçek motor GPIO'ları başarıyla başlatıldı")

        except ImportError:
            self.logger.error("❌ gpiozero kütüphanesi bulunamadı!")
            self.saglik_durumu = False
        except Exception as e:
            self.logger.error(f"❌ Motor GPIO başlatma hatası: {e}")
            self.saglik_durumu = False

    async def baslat(self) -> bool:
        """Motor sistemini başlat"""
        if self.saglik_durumu:
            self.motor_durumu.motorlar_aktif = True
            self.logger.info("⚙️ Gerçek motor sistemi başlatıldı")
        return self.saglik_durumu

    async def durdur(self):
        """Motor sistemini durdur"""
        await self.acil_durdur()
        self.motor_durumu.motorlar_aktif = False

        # GPIO kaynaklarını temizle
        try:
            for motor_name, motor_data in self.gpio_motors.items():
                if isinstance(motor_data, dict):
                    for obj_name, obj in motor_data.items():
                        if hasattr(obj, 'close'):
                            obj.close()
            self.logger.info("GPIO motor kaynakları temizlendi")
        except Exception as e:
            self.logger.error(f"GPIO temizleme hatası: {e}")

        self.logger.info("⚙️ Gerçek motor sistemi durduruldu")

    async def tekerlek_hiz_ayarla(self, sol_hiz: float, sag_hiz: float):
        """Tekerlek motorlarının hızını ayarla"""
        if not self.motor_durumu.motorlar_aktif or not self.saglik_durumu:
            return

        # Hızları sınırla
        sol_hiz = max(-1.0, min(1.0, sol_hiz))
        sag_hiz = max(-1.0, min(1.0, sag_hiz))

        self.motor_durumu.sol_hiz = sol_hiz
        self.motor_durumu.sag_hiz = sag_hiz

        # Sol tekerlek kontrolü
        sol_motor = self.gpio_motors.get('sol_tekerlek')
        if sol_motor and 'motor_obj' in sol_motor:
            try:
                motor_obj = sol_motor['motor_obj']
                if sol_hiz > 0:
                    motor_obj.forward(speed=sol_hiz)
                elif sol_hiz < 0:
                    motor_obj.backward(speed=abs(sol_hiz))
                else:
                    motor_obj.stop()
            except Exception as e:
                self.logger.error(f"Sol tekerlek kontrol hatası: {e}")

        # Sağ tekerlek kontrolü
        sag_motor = self.gpio_motors.get('sag_tekerlek')
        if sag_motor and 'motor_obj' in sag_motor:
            try:
                motor_obj = sag_motor['motor_obj']
                if sag_hiz > 0:
                    motor_obj.forward(speed=sag_hiz)
                elif sag_hiz < 0:
                    motor_obj.backward(speed=abs(sag_hiz))
                else:
                    motor_obj.stop()
            except Exception as e:
                self.logger.error(f"Sağ tekerlek kontrol hatası: {e}")

    async def firca_kontrol(self, ana: bool, sol: bool, sag: bool):
        """Fırça motorlarını kontrol et"""
        self.motor_durumu.ana_firca = ana
        self.motor_durumu.sol_firca = sol
        self.motor_durumu.sag_firca = sag

        # Ana fırça
        self._firca_motor_kontrol('ana_firca', ana)
        # Sol fırça
        self._firca_motor_kontrol('sol_firca', sol)
        # Sağ fırça
        self._firca_motor_kontrol('sag_firca', sag)

    async def fan_kontrol(self, aktif: bool):
        """Fan motorunu kontrol et"""
        self.motor_durumu.fan = aktif
        self._firca_motor_kontrol('fan', aktif)

    def _firca_motor_kontrol(self, motor_adi: str, aktif: bool):
        """Fırça/fan motor kontrolü (L298N forward yönde)"""
        motor_data = self.gpio_motors.get(motor_adi)
        if not motor_data:
            return

        try:
            if aktif:
                # Forward yönde çalıştır
                motor_data['pin_a_obj'].on()   # IN1/IN3 = HIGH
                motor_data['pin_b_obj'].off()  # IN2/IN4 = LOW
            else:
                # Durdur
                motor_data['pin_a_obj'].off()
                motor_data['pin_b_obj'].off()
        except Exception as e:
            self.logger.error(f"'{motor_adi}' kontrol hatası: {e}")

    async def acil_durdur(self):
        """Tüm motorları acil olarak durdur"""
        self.motor_durumu.sol_hiz = 0.0
        self.motor_durumu.sag_hiz = 0.0
        self.motor_durumu.ana_firca = False
        self.motor_durumu.sol_firca = False
        self.motor_durumu.sag_firca = False
        self.motor_durumu.fan = False

        # Tüm motorları fiziksel olarak durdur
        try:
            # Tekerlek motorları
            for tekerlek in ['sol_tekerlek', 'sag_tekerlek']:
                motor_data = self.gpio_motors.get(tekerlek)
                if motor_data and 'motor_obj' in motor_data:
                    motor_data['motor_obj'].stop()

            # Fırça ve fan motorları
            for motor_adi in ['ana_firca', 'sol_firca', 'sag_firca', 'fan']:
                self._firca_motor_kontrol(motor_adi, False)

        except Exception as e:
            self.logger.error(f"Acil durdurma hatası: {e}")

        self.logger.critical("🚨 Gerçek motorlar acil durduruldu!")

    def motor_durumu_al(self) -> MotorDurumuVeri:
        """Mevcut motor durumunu al"""
        return self.motor_durumu

    def saglikli_mi(self) -> bool:
        """Motor sistemi sağlıklı mı?"""
        return self.saglik_durumu and GPIO_AVAILABLE


# === Hardware Factory ===

class GercekHardwareFactory(HardwareFactory):
    """Gerçek donanım fabrikası"""

    def __init__(self):
        self.logger = logging.getLogger("GercekDonanim")

        if not GPIO_AVAILABLE:
            self.logger.warning("⚠️ RPi.GPIO mevcut değil - bazı sensörler çalışmayabilir")

        if not ADAFRUIT_AVAILABLE:
            self.logger.warning("⚠️ Adafruit kütüphaneleri mevcut değil - I2C sensörler çalışmayabilir")

    def imu_olustur(self, config: Dict[str, Any]) -> IMUInterface:
        """Gerçek IMU oluştur"""
        return GercekIMU(config)

    def gps_olustur(self, config: Dict[str, Any]) -> GPSInterface:
        """Gerçek GPS oluştur"""
        return GercekGPS(config)

    def guc_olustur(self, config: Dict[str, Any]) -> GucInterface:
        """Gerçek güç sensörü oluştur"""
        return GercekGuc(config)

    def tampon_olustur(self, config: Dict[str, Any]) -> TamponInterface:
        """Gerçek tampon sensörü oluştur"""
        return GercekTampon(config)

    def enkoder_olustur(self, config: Dict[str, Any]) -> EnkoderInterface:
        """Gerçek encoder sensörü oluştur"""
        return GercekEnkoder(config)

    def acil_durma_olustur(self, config: Dict[str, Any]) -> AcilDurmaInterface:
        """Gerçek acil durdurma butonu oluştur"""
        return GercekAcilDurma(config)

    def motor_olustur(self, config: Dict[str, Any]) -> MotorInterface:
        """Gerçek motor kontrolcüsü oluştur"""
        return GercekMotor(config)
