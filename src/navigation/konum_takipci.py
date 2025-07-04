"""
🧭 Konum Takipçi - Robot'un GPS'i ve Odometresi
Hacı Abi'nin navigasyon sistemi burada!

Bu sınıf robot'un konumunu takip eder:
- GPS koordinatları
- Enkoder tabanlı odometri (dead reckoning)
- IMU destekli konum düzeltme
- Kalman filtresi ile veri füzyonu
"""

import math
import logging
import time
import numpy as np
from typing import Dict, Any, Tuple, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Konum:
    """Robot konumu"""
    x: float  # metre (local koordinat)
    y: float  # metre (local koordinat)
    theta: float  # radyan (yön)
    latitude: float  # GPS koordinatı
    longitude: float  # GPS koordinatı
    timestamp: str


@dataclass
class Hareket:
    """Robot hareket verisi"""
    linear_velocity: float  # m/s
    angular_velocity: float  # rad/s
    distance_traveled: float  # metre
    heading_change: float  # radyan


class KalmanFilter:
    """
    🎯 Konum tahmini için Kalman Filtresi
    
    Enkoder ve GPS verilerini birleştirerek daha doğru konum hesaplar
    """
    
    def __init__(self, process_noise: float = 0.1, measurement_noise: float = 0.5):
        # Durum vektörü: [x, y, theta, vx, vy, vtheta]
        self.state = np.zeros(6)
        
        # Kovaryans matrisleri
        self.P = np.eye(6) * 1.0  # Durum kovaryansı
        self.Q = np.eye(6) * process_noise  # Süreç gürültüsü
        self.R_gps = np.eye(2) * measurement_noise  # GPS ölçüm gürültüsü
        self.R_encoder = np.eye(3) * (measurement_noise * 0.1)  # Enkoder ölçüm gürültüsü
        
        # Geçiş matrisi (dt ile güncellenecek)
        self.F = np.eye(6)
        
        # Ölçüm matrisleri
        self.H_gps = np.zeros((2, 6))
        self.H_gps[0, 0] = 1  # x için
        self.H_gps[1, 1] = 1  # y için
        
        self.H_encoder = np.zeros((3, 6))
        self.H_encoder[0, 0] = 1  # x için
        self.H_encoder[1, 1] = 1  # y için
        self.H_encoder[2, 2] = 1  # theta için
        
        self.last_update_time = time.time()
    
    def predict(self, dt: float):
        """Tahmin adımı"""
        # Geçiş matrisini güncelle
        self.F[0, 3] = dt  # x += vx * dt
        self.F[1, 4] = dt  # y += vy * dt
        self.F[2, 5] = dt  # theta += vtheta * dt
        
        # Tahmin
        self.state = self.F @ self.state
        self.P = self.F @ self.P @ self.F.T + self.Q
    
    def update_gps(self, gps_x: float, gps_y: float):
        """GPS ölçümü ile güncelle"""
        z = np.array([gps_x, gps_y])
        
        # Kalman gain
        S = self.H_gps @ self.P @ self.H_gps.T + self.R_gps
        K = self.P @ self.H_gps.T @ np.linalg.inv(S)
        
        # Güncelleme
        y = z - self.H_gps @ self.state
        self.state = self.state + K @ y
        self.P = (np.eye(6) - K @ self.H_gps) @ self.P
    
    def update_encoder(self, odom_x: float, odom_y: float, odom_theta: float):
        """Enkoder ölçümü ile güncelle"""
        z = np.array([odom_x, odom_y, odom_theta])
        
        # Kalman gain
        S = self.H_encoder @ self.P @ self.H_encoder.T + self.R_encoder
        K = self.P @ self.H_encoder.T @ np.linalg.inv(S)
        
        # Güncelleme
        y = z - self.H_encoder @ self.state
        # Theta için açı normalizasyonu
        y[2] = self._normalize_angle(y[2])
        
        self.state = self.state + K @ y
        self.P = (np.eye(6) - K @ self.H_encoder) @ self.P
        
        # Theta'yı normalize et
        self.state[2] = self._normalize_angle(self.state[2])
    
    def _normalize_angle(self, angle: float) -> float:
        """Açıyı -pi ile pi arasına normalize et"""
        while angle > math.pi:
            angle -= 2 * math.pi
        while angle < -math.pi:
            angle += 2 * math.pi
        return angle
    
    def get_position(self) -> Tuple[float, float, float]:
        """Mevcut konum tahminini al"""
        return float(self.state[0]), float(self.state[1]), float(self.state[2])


class KonumTakipci:
    """
    🧭 Ana Konum Takipçi Sınıfı
    
    Robot'un konumunu çeşitli sensörlerden alarak takip eder.
    Kalman filtresi ile enkoder ve GPS verilerini birleştirir.
    """
    
    def __init__(self, nav_config: Dict[str, Any]):
        self.config = nav_config
        self.logger = logging.getLogger("KonumTakipci")
        
        # Robot fiziksel parametreleri
        self.tekerlek_capi = nav_config.get("wheel_diameter", 0.065)
        self.tekerlek_base = nav_config.get("wheel_base", 0.235)
        self.enkoder_pulse_per_rev = 360
        
        # Kalman filtresi
        kalman_config = nav_config.get("kalman", {})
        self.kalman = KalmanFilter(
            process_noise=kalman_config.get("process_noise", 0.1),
            measurement_noise=kalman_config.get("measurement_noise", 0.5)
        )
        
        # Konum verisi
        self.mevcut_konum = Konum(
            x=0.0, y=0.0, theta=0.0,
            latitude=0.0, longitude=0.0,
            timestamp=datetime.now().isoformat()
        )
        
        # Odometri verisi
        self.onceki_enkoder = {"sol": 0, "sag": 0}
        self.toplam_mesafe = 0.0
        self.toplam_donme = 0.0
        
        # GPS referans noktası (ilk GPS okuması)
        self.gps_reference = None
        self.gps_scale_factor = 111320.0  # metre/derece (yaklaşık)
        
        # Hareket geçmişi
        self.hareket_gecmisi: List[Hareket] = []
        self.konum_gecmisi: List[Konum] = []
        
        self.logger.info("🧭 Konum takipçi başlatıldı")
    
    async def ilk_konum_belirle(self):
        """🏁 Robot'un ilk konumunu belirle"""
        self.logger.info("🏁 İlk konum belirleniyor...")
        
        # Bu fonksiyon başlangıçta çağrılır
        # GPS referans noktasını ayarlamak için kullanılır
        self.mevcut_konum = Konum(
            x=0.0, y=0.0, theta=0.0,
            latitude=0.0, longitude=0.0,
            timestamp=datetime.now().isoformat()
        )
        
        self.logger.info("✅ İlk konum belirlendi: (0, 0, 0°)")
    
    async def konum_guncelle(self, sensor_data: Dict[str, Any]):
        """
        📍 Ana konum güncelleme fonksiyonu
        
        Sensör verilerini kullanarak robot konumunu günceller.
        """
        current_time = time.time()
        dt = current_time - self.kalman.last_update_time
        self.kalman.last_update_time = current_time
        
        # Kalman filtresi tahmin adımı
        self.kalman.predict(dt)
        
        # Enkoder verisi ile odometri güncelleme
        if "motor_durumu" in sensor_data:
            await self._enkoder_guncelle(sensor_data["motor_durumu"], dt)
        
        # GPS verisi ile konum düzeltme
        if sensor_data.get("gps") and sensor_data["gps"].get("latitude", 0) != 0:
            await self._gps_guncelle(sensor_data["gps"])
        
        # IMU verisi ile yön düzeltme
        if sensor_data.get("imu"):
            await self._imu_guncelle(sensor_data["imu"])
        
        # Kalman filtresi sonucu ile konum güncelle
        x, y, theta = self.kalman.get_position()
        
        # Mevcut konumu güncelle
        self.mevcut_konum.x = x
        self.mevcut_konum.y = y
        self.mevcut_konum.theta = theta
        self.mevcut_konum.timestamp = datetime.now().isoformat()
        
        # Konum geçmişini kaydet
        self.konum_gecmisi.append(self.mevcut_konum)
        if len(self.konum_gecmisi) > 1000:  # Son 1000 konumu sakla
            self.konum_gecmisi.pop(0)
        
        self.logger.debug(f"📍 Konum güncellendi: ({x:.2f}, {y:.2f}, {math.degrees(theta):.1f}°)")
    
    async def _enkoder_guncelle(self, motor_data: Dict[str, Any], dt: float):
        """⚙️ Enkoder verisi ile odometri hesaplama"""
        try:
            sol_enkoder = motor_data.get("enkoder", {}).get("sol_enkoder", 0)
            sag_enkoder = motor_data.get("enkoder", {}).get("sag_enkoder", 0)
            
            # Enkoder farkını hesapla
            sol_delta = sol_enkoder - self.onceki_enkoder["sol"]
            sag_delta = sag_enkoder - self.onceki_enkoder["sag"]
            
            # Enkoder sayısını mesafeye çevir
            sol_mesafe = (sol_delta / self.enkoder_pulse_per_rev) * (math.pi * self.tekerlek_capi)
            sag_mesafe = (sag_delta / self.enkoder_pulse_per_rev) * (math.pi * self.tekerlek_capi)
            
            # Differential drive kinematik
            linear_mesafe = (sol_mesafe + sag_mesafe) / 2
            angular_mesafe = (sag_mesafe - sol_mesafe) / self.tekerlek_base
            
            # Hız hesapla
            linear_velocity = linear_mesafe / dt if dt > 0 else 0
            angular_velocity = angular_mesafe / dt if dt > 0 else 0
            
            # Konum hesapla (dead reckoning)
            x_delta = linear_mesafe * math.cos(self.mevcut_konum.theta + angular_mesafe / 2)
            y_delta = linear_mesafe * math.sin(self.mevcut_konum.theta + angular_mesafe / 2)
            
            # Odometri konumunu hesapla
            odom_x = self.mevcut_konum.x + x_delta
            odom_y = self.mevcut_konum.y + y_delta
            odom_theta = self.mevcut_konum.theta + angular_mesafe
            
            # Kalman filtresi ile güncelle
            self.kalman.update_encoder(odom_x, odom_y, odom_theta)
            
            # Hareket verisini kaydet
            hareket = Hareket(
                linear_velocity=linear_velocity,
                angular_velocity=angular_velocity,
                distance_traveled=abs(linear_mesafe),
                heading_change=abs(angular_mesafe)
            )
            self.hareket_gecmisi.append(hareket)
            if len(self.hareket_gecmisi) > 100:
                self.hareket_gecmisi.pop(0)
            
            # Toplam mesafe ve dönme
            self.toplam_mesafe += abs(linear_mesafe)
            self.toplam_donme += abs(angular_mesafe)
            
            # Enkoder değerlerini kaydet
            self.onceki_enkoder["sol"] = sol_enkoder
            self.onceki_enkoder["sag"] = sag_enkoder
            
            self.logger.debug(f"⚙️ Odometri: mesafe={linear_mesafe:.3f}m, dönme={math.degrees(angular_mesafe):.1f}°")
            
        except Exception as e:
            self.logger.error(f"❌ Enkoder güncelleme hatası: {e}")
    
    async def _gps_guncelle(self, gps_data: Dict[str, Any]):
        """🗺️ GPS verisi ile konum düzeltme"""
        try:
            lat = gps_data.get("latitude", 0)
            lon = gps_data.get("longitude", 0)
            
            if lat == 0 or lon == 0:
                return
            
            # GPS referans noktasını ilk okumalarda ayarla
            if self.gps_reference is None:
                self.gps_reference = {"lat": lat, "lon": lon}
                self.logger.info(f"🗺️ GPS referans noktası: ({lat:.6f}, {lon:.6f})")
                return
            
            # GPS koordinatlarını local koordinata çevir
            gps_x, gps_y = self._gps_to_local(lat, lon)
            
            # Kalman filtresi ile güncelle
            self.kalman.update_gps(gps_x, gps_y)
            
            # GPS koordinatlarını kaydet
            self.mevcut_konum.latitude = lat
            self.mevcut_konum.longitude = lon
            
            self.logger.debug(f"🗺️ GPS güncellemesi: ({gps_x:.2f}, {gps_y:.2f})")
            
        except Exception as e:
            self.logger.error(f"❌ GPS güncelleme hatası: {e}")
    
    async def _imu_guncelle(self, imu_data: Dict[str, Any]):
        """🧭 IMU verisi ile yön düzeltme"""
        try:
            # IMU'dan yaw verisi alınabilirse kullan
            # MPU-6050'de magnetometre olmadığı için yaw doğrudan alınamaz
            # Jiroskop verisini entegre ederek yaw hesaplanabilir ama drift olur
            
            gyro_z = imu_data.get("gyro_z", 0)
            
            # Basit jiroskop entegrasyonu (sadece kısa süreli kullanım için)
            # Gerçek uygulamada magnetometre veya görsel odometri gerekli
            
            self.logger.debug(f"🧭 IMU gyro_z: {gyro_z:.3f} rad/s")
            
        except Exception as e:
            self.logger.error(f"❌ IMU güncelleme hatası: {e}")
    
    def _gps_to_local(self, lat: float, lon: float) -> Tuple[float, float]:
        """GPS koordinatlarını local koordinata çevir"""
        if self.gps_reference is None:
            return 0.0, 0.0
        
        # Basit düzlemsel projeksiyon
        # Küçük alanlar için yeterli doğruluk
        ref_lat = self.gps_reference["lat"]
        ref_lon = self.gps_reference["lon"]
        
        # Enlem farkı -> y koordinatı
        y = (lat - ref_lat) * self.gps_scale_factor
        
        # Boylam farkı -> x koordinatı (enlem düzeltmesi ile)
        x = (lon - ref_lon) * self.gps_scale_factor * math.cos(math.radians(ref_lat))
        
        return x, y
    
    def _local_to_gps(self, x: float, y: float) -> Tuple[float, float]:
        """Local koordinatları GPS koordinatına çevir"""
        if self.gps_reference is None:
            return 0.0, 0.0
        
        ref_lat = self.gps_reference["lat"]
        ref_lon = self.gps_reference["lon"]
        
        # Ters hesaplama
        lat = ref_lat + (y / self.gps_scale_factor)
        lon = ref_lon + (x / (self.gps_scale_factor * math.cos(math.radians(ref_lat))))
        
        return lat, lon
    
    def get_mevcut_konum(self) -> Konum:
        """Mevcut konumu al"""
        # GPS koordinatlarını güncelle
        if self.gps_reference:
            lat, lon = self._local_to_gps(self.mevcut_konum.x, self.mevcut_konum.y)
            self.mevcut_konum.latitude = lat
            self.mevcut_konum.longitude = lon
        
        return self.mevcut_konum
    
    def get_mesafe_to(self, hedef_x: float, hedef_y: float) -> float:
        """Hedefe olan mesafeyi hesapla"""
        dx = hedef_x - self.mevcut_konum.x
        dy = hedef_y - self.mevcut_konum.y
        return math.sqrt(dx**2 + dy**2)
    
    def get_aci_to(self, hedef_x: float, hedef_y: float) -> float:
        """Hedefe olan açıyı hesapla"""
        dx = hedef_x - self.mevcut_konum.x
        dy = hedef_y - self.mevcut_konum.y
        return math.atan2(dy, dx)
    
    def get_hareket_istatistikleri(self) -> Dict[str, Any]:
        """Hareket istatistiklerini al"""
        if not self.hareket_gecmisi:
            return {
                "toplam_mesafe": self.toplam_mesafe,
                "toplam_donme": math.degrees(self.toplam_donme),
                "ortalama_hiz": 0.0,
                "max_hiz": 0.0
            }
        
        hizlar = [h.linear_velocity for h in self.hareket_gecmisi]
        
        return {
            "toplam_mesafe": self.toplam_mesafe,
            "toplam_donme": math.degrees(self.toplam_donme),
            "ortalama_hiz": sum(hizlar) / len(hizlar),
            "max_hiz": max(hizlar),
            "hareket_sayisi": len(self.hareket_gecmisi)
        }
    
    def konum_sifirla(self):
        """Konumu sıfırla (yeni görev başlangıcı için)"""
        self.mevcut_konum.x = 0.0
        self.mevcut_konum.y = 0.0
        self.mevcut_konum.theta = 0.0
        self.toplam_mesafe = 0.0
        self.toplam_donme = 0.0
        self.onceki_enkoder = {"sol": 0, "sag": 0}
        self.hareket_gecmisi.clear()
        
        # Kalman filtresini sıfırla
        self.kalman.state = np.zeros(6)
        self.kalman.P = np.eye(6) * 1.0
        
        self.logger.info("🔄 Konum takipçi sıfırlandı")
    
    def get_konum_raporu(self) -> Dict[str, Any]:
        """Detaylı konum raporu"""
        konum = self.get_mevcut_konum()
        
        return {
            "konum": {
                "x": konum.x,
                "y": konum.y,
                "theta": math.degrees(konum.theta),
                "latitude": konum.latitude,
                "longitude": konum.longitude
            },
            "istatistikler": self.get_hareket_istatistikleri(),
            "kalman_durumu": {
                "konum_belirsizligi": float(np.trace(self.kalman.P[:3, :3])),
                "durum": self.kalman.state.tolist()
            },
            "gps_referansi": self.gps_reference,
            "timestamp": konum.timestamp
        }
