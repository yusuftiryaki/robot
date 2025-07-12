"""
🧭 Konum Takipçi - Robot'un GPS'i ve Odometresi
Hacı Abi'nin navigasyon sistemi burada!

Bu sınıf robot'un konumunu takip eder:
- GPS koordinatları
- Enkoder tabanlı odometri (dead reckoning)
- IMU destekli konum düzeltme
- Kalman filtresi ile veri füzyonu
"""

import logging
import math
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Tuple

import numpy as np


@dataclass
class Konum:
    """Robot konumu"""
    x: float  # metre (local koordinat)
    y: float  # metre (local koordinat)
    theta: float  # radyan (yön)
    latitude: float  # GPS koordinatı
    longitude: float  # GPS koordinatı
    timestamp: str

    def __eq__(self, other):
        """Eşitlik kontrolü - A* algoritması için"""
        if not isinstance(other, Konum):
            return False
        return (abs(self.x - other.x) < 0.01 and
                abs(self.y - other.y) < 0.01)

    def __hash__(self):
        """Hash metodu - set ve dictionary kullanımı için"""
        return hash((round(self.x, 2), round(self.y, 2)))


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
        if "enkoder" in sensor_data and sensor_data["enkoder"].gecerli:
            await self._enkoder_guncelle(sensor_data["enkoder"], dt)

        # GPS verisi ile konum düzeltme
        if sensor_data.get("gps") and sensor_data["gps"].gecerli and sensor_data["gps"].enlem != 0:
            await self._gps_guncelle(sensor_data["gps"])

        # IMU verisi ile yön düzeltme
        if sensor_data.get("imu") and sensor_data["imu"].gecerli:
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

    async def _enkoder_guncelle(self, enkoder_data, dt: float):
        """⚙️ Enkoder verisi ile odometri hesaplama"""
        try:
            # EnkoderVeri dataclass'ından veri al
            sol_enkoder = enkoder_data.sol_teker  # sol_teker = enkoder sayacı
            sag_enkoder = enkoder_data.sag_teker  # sag_teker = enkoder sayacı

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

    async def _gps_guncelle(self, gps_data):
        """🗺️ GPS verisi ile konum düzeltme"""
        try:
            lat = gps_data.enlem
            lon = gps_data.boylam

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

    async def _imu_guncelle(self, imu_data):
        """🧭 IMU verisi ile yön düzeltme ve stabilizasyon"""
        try:
            # IMUVeri dataclass'ından verileri al
            gyro_z = imu_data.acisal_hiz_z  # Yaw açısal hızı (Z ekseni)

            # İvme verileri - eğim ve titreşim tespiti için
            accel_x = imu_data.ivme_x  # X ekseni ivme
            accel_y = imu_data.ivme_y  # Y ekseni ivme
            accel_z = imu_data.ivme_z  # Z ekseni ivme (gravity)

            # Roll ve pitch değerleri direkt IMU'dan alınabilir
            roll = imu_data.roll  # IMU'dan gelen roll
            pitch = imu_data.pitch  # IMU'dan gelen pitch
            # Yaw değeri genelde 0, çünkü MPU-6050'de magnetometre yok

            # Sıcaklık kontrolü - sensör aşırı ısınmış mı?
            sicaklik = imu_data.sicaklik
            if sicaklik > 60.0:  # 60°C üstü kritik
                self.logger.warning(f"🌡️ IMU aşırı ısınmış: {sicaklik:.1f}°C")
                return  # Bu güncellemeyi atla

            # Kalman filtresinin hız vektörlerini güncelle (jiroskop ile)
            current_time = time.time()
            dt = current_time - getattr(self, '_last_imu_update', current_time)
            self._last_imu_update = current_time

            if dt > 0 and dt < 1.0:  # Makul zaman aralığı kontrolü
                # Jiroskop verisiyle açısal hız güncellemesi
                # Kalman filtresinin hız state'lerini güncelle
                self.kalman.state[5] = gyro_z  # vtheta = gyro_z

                # Jiroskop drift'i çok fazlaysa kompanzasyon yap
                if abs(gyro_z) < 0.01:  # Durgun durumdaysa (0.01 rad/s threshold)
                    # Hafif drift düzeltmesi - enkoder bazlı açıya yakınlaştır
                    self.kalman.state[5] *= 0.95  # %5 azalt

                # Yüksek ivme durumunda ekstra güncelleme
                total_accel = math.sqrt(accel_x**2 + accel_y**2 + accel_z**2)
                if abs(total_accel - 9.81) > 2.0:  # 2 m/s² üstü ivme
                    # Robot hızla hareket ediyor - IMU verilerine daha çok güven
                    self.logger.debug(f"🚀 Yüksek ivme tespit edildi: {total_accel:.2f} m/s²")

                    # Pozisyon düzeltmesi için basit ivme entegrasyonu
                    # Bu sadece yüksek dinamik hareketlerde kullanılır
                    if hasattr(self, '_last_accel_time'):
                        accel_dt = current_time - self._last_accel_time
                        if accel_dt > 0 and accel_dt < 0.1:  # 100ms'den kısa
                            # Basit ivme entegrasyonu (çok kısa süreli)
                            v_delta_x = accel_x * accel_dt
                            v_delta_y = accel_y * accel_dt

                            # Kalman filtresinin hız state'lerini güncelle
                            self.kalman.state[3] += v_delta_x * 0.1  # Düşük ağırlık
                            self.kalman.state[4] += v_delta_y * 0.1

                    self._last_accel_time = current_time

                # Eğim kontrolü - robot dengesiz mi?
                roll_degrees = math.degrees(roll)
                pitch_degrees = math.degrees(pitch)

                if abs(roll_degrees) > 20 or abs(pitch_degrees) > 20:
                    self.logger.warning(f"⚠️ Robot dengesiz! Roll: {roll_degrees:.1f}°, Pitch: {pitch_degrees:.1f}°")

                    # Dengesizlik durumunda konum güvenilirliğini azalt
                    # Kalman filtresinin ölçüm gürültüsünü artır
                    instability_factor = min(abs(roll_degrees) + abs(pitch_degrees), 45) / 45
                    self.kalman.R_encoder *= (1 + instability_factor * 0.5)

                elif abs(roll_degrees) > 10 or abs(pitch_degrees) > 10:
                    self.logger.debug(f"🔶 Hafif eğim: Roll: {roll_degrees:.1f}°, Pitch: {pitch_degrees:.1f}°")

                # Titreşim tespiti (yüksek frekanslı gyro değişimi)
                if hasattr(self, '_prev_gyro_z'):
                    gyro_change = abs(gyro_z - self._prev_gyro_z)
                    if gyro_change > 1.0:  # 1 rad/s'den fazla ani değişim
                        self.logger.debug(f"📳 Titreşim/ani hareket tespit edildi: {gyro_change:.2f} rad/s")

                self._prev_gyro_z = gyro_z

                # IMU health check - değerler makul aralıkta mı?
                if abs(gyro_z) > 10.0:  # 10 rad/s üstü anormal
                    self.logger.warning(f"⚠️ Anormal gyro_z değeri: {gyro_z:.2f} rad/s")
                    return  # Bu güncellemeyi atla

                if total_accel > 50.0 or total_accel < 1.0:  # Anormal ivme
                    self.logger.warning(f"⚠️ Anormal ivme değeri: {total_accel:.2f} m/s²")
                    return  # Bu güncellemeyi atla

                self.logger.debug(f"🧭 IMU güncellendi - Gyro_Z: {gyro_z:.3f} rad/s, Roll: {roll_degrees:.1f}°, Pitch: {pitch_degrees:.1f}°, Sıcaklık: {sicaklik:.1f}°C")

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

    def get_mesafe_to_gps(self, hedef_lat: float, hedef_lon: float) -> float:
        """
        🌍 GPS koordinatlarına göre mesafe hesapla (Haversine formula)

        Args:
            hedef_lat: Hedef enlem
            hedef_lon: Hedef boylam

        Returns:
            Mesafe (metre)
        """
        if not self.gps_reference or self.mevcut_konum.latitude == 0:
            self.logger.debug("🧭 GPS referansı yok, local mesafe hesaplanıyor")  # WARNING -> DEBUG
            # GPS olmadığında local koordinat kullan
            hedef_x, hedef_y = self._gps_to_local(hedef_lat, hedef_lon)
            return self.get_mesafe_to(hedef_x, hedef_y)

        # Haversine formula - Dünya üzerinde iki nokta arası mesafe
        lat1, lon1 = math.radians(self.mevcut_konum.latitude), math.radians(self.mevcut_konum.longitude)
        lat2, lon2 = math.radians(hedef_lat), math.radians(hedef_lon)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = (math.sin(dlat / 2)**2 +
             math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2)
        c = 2 * math.asin(math.sqrt(a))

        # Dünya yarıçapı (metre)
        R = 6371000
        mesafe = R * c

        self.logger.debug(f"🌍 GPS mesafe: {mesafe:.2f}m ({hedef_lat:.6f}, {hedef_lon:.6f})")
        return mesafe

    def get_bearing_to_gps(self, hedef_lat: float, hedef_lon: float) -> float:
        """
        🧭 GPS koordinatlarına göre yön hesapla (bearing)

        Returns:
            Yön (radyan, 0=Kuzey)
        """
        if self.mevcut_konum.latitude == 0:
            # GPS olmadığında local koordinat kullan
            hedef_x, hedef_y = self._gps_to_local(hedef_lat, hedef_lon)
            return self.get_aci_to(hedef_x, hedef_y)

        lat1, lon1 = math.radians(self.mevcut_konum.latitude), math.radians(self.mevcut_konum.longitude)
        lat2, lon2 = math.radians(hedef_lat), math.radians(hedef_lon)

        dlon = lon2 - lon1

        y = math.sin(dlon) * math.cos(lat2)
        x = (math.cos(lat1) * math.sin(lat2) -
             math.sin(lat1) * math.cos(lat2) * math.cos(dlon))

        bearing = math.atan2(y, x)

        # 0-2π aralığına normalize et
        bearing = (bearing + 2 * math.pi) % (2 * math.pi)

        return bearing

    def gps_hedef_dogrulugu(self, hedef_lat: float, hedef_lon: float, hata_payi: float = 3.0) -> Dict[str, Any]:
        """
        🎯 GPS hedef doğruluğunu değerlendir

        Args:
            hedef_lat: Hedef enlem
            hedef_lon: Hedef boylam
            hata_payi: GPS hata payı (metre)

        Returns:
            Doğruluk analizi
        """
        mesafe = self.get_mesafe_to_gps(hedef_lat, hedef_lon)
        bearing = self.get_bearing_to_gps(hedef_lat, hedef_lon)

        # GPS doğruluk seviyeleri
        if mesafe <= hata_payi:
            dogruluk_seviyesi = "HASSAS"  # GPS hata payı içinde
            guvenilirlik = 0.95
        elif mesafe <= hata_payi * 2:
            dogruluk_seviyesi = "IYI"  # 2x hata payı içinde
            guvenilirlik = 0.80
        elif mesafe <= 10.0:
            dogruluk_seviyesi = "KABUL_EDILEBILIR"  # 10m içinde
            guvenilirlik = 0.60
        else:
            dogruluk_seviyesi = "UZAK"  # 10m'den uzak
            guvenilirlik = 0.30

        return {
            "mesafe": mesafe,
            "bearing": math.degrees(bearing),
            "dogruluk_seviyesi": dogruluk_seviyesi,
            "guvenilirlik": guvenilirlik,
            "gps_aktif": self.mevcut_konum.latitude != 0,
            "hedef_koordinatlari": {"lat": hedef_lat, "lon": hedef_lon},
            "mevcut_koordinatlari": {
                "lat": self.mevcut_konum.latitude,
                "lon": self.mevcut_konum.longitude
            }
        }

    def gps_referans_ayarla(self, lat: float, lon: float):
        """
        🗺️ GPS referans noktasını manuel olarak ayarla

        Simülasyon modunda veya başlangıçta GPS referansını ayarlamak için kullanılır.
        """
        self.gps_reference = {"lat": lat, "lon": lon}
        self.logger.info(f"🗺️ GPS referans noktası manuel ayarlandı: ({lat:.6f}, {lon:.6f})")
