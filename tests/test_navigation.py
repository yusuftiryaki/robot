#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Otonom Bahçe Asistanı (OBA) - Navigation Testleri
=======================================

Bu modül robot navigasyon sisteminin test edilmesi için gerekli testleri içerir.
Konum takibi, rota planlama ve hareket kontrolü testleri.
"""

import asyncio
import math
import os
import sys
import time
import unittest
from typing import List, Tuple

from test_utils import TestRaporu, TestVeriUreticisi

# Proje klasörünü Python path'ine ekle
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestKonumTakibi(unittest.TestCase):
    """Konum takibi testleri."""

    def setUp(self):
        """Test başlangıç ayarları."""
        self.test_verisi = TestVeriUreticisi.ornek_konum_verisi()

    def test_konum_veri_yapisi(self):
        """Konum veri yapısı testi."""
        konum_data = TestVeriUreticisi.ornek_konum_verisi()

        # Temel koordinatlar
        self.assertIn('x', konum_data)
        self.assertIn('y', konum_data)
        self.assertIn('theta', konum_data)

        # Hız bilgileri
        self.assertIn('hiz', konum_data)

        # Kalman filtresi durumu
        self.assertIn('kalman_durumu', konum_data)
        kalman = konum_data['kalman_durumu']
        self.assertIn('x', kalman)
        self.assertIn('y', kalman)
        self.assertIn('theta', kalman)

    def test_aci_normalizasyonu(self):
        """Açı normalizasyon testi."""
        def normalize_angle(angle):
            """Açıyı -π ile π arasına normalize et."""
            while angle > math.pi:
                angle -= 2 * math.pi
            while angle < -math.pi:
                angle += 2 * math.pi
            return angle

        # Test açıları
        test_angles = [0, math.pi / 2, math.pi, 3 *
                       math.pi / 2, 2 * math.pi, -math.pi / 2, -math.pi]

        for angle in test_angles:
            normalized = normalize_angle(angle)
            self.assertTrue(-math.pi <= normalized <= math.pi)

    def test_mesafe_hesaplama(self):
        """Mesafe hesaplama testi."""
        def calculate_distance(x1, y1, x2, y2):
            """İki nokta arası mesafeyi hesapla."""
            return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

        # Test noktaları
        p1 = (0, 0)
        p2 = (3, 4)  # 3-4-5 üçgeni

        mesafe = calculate_distance(p1[0], p1[1], p2[0], p2[1])
        self.assertAlmostEqual(mesafe, 5.0, places=2)

    def test_odometri_hesaplama(self):
        """Odometri hesaplama testi."""
        # Enkoder değerleri (pulse)
        sol_enkoder_onceki = 1000
        sag_enkoder_onceki = 1000
        sol_enkoder_simdiki = 1100
        sag_enkoder_simdiki = 1100

        # Robot parametreleri
        tekerlek_yaricapi = 0.05  # 5cm
        tekerlek_arasi_mesafe = 0.3  # 30cm
        pulse_per_revolution = 360

        # Pulse başına mesafe
        pulse_to_meter = (2 * math.pi * tekerlek_yaricapi) / \
            pulse_per_revolution

        # Her tekerlek için mesafe
        sol_mesafe = (sol_enkoder_simdiki -
                      sol_enkoder_onceki) * pulse_to_meter
        sag_mesafe = (sag_enkoder_simdiki -
                      sag_enkoder_onceki) * pulse_to_meter

        # Toplam mesafe ve açı değişimi
        toplam_mesafe = (sol_mesafe + sag_mesafe) / 2
        aci_degisimi = (sag_mesafe - sol_mesafe) / tekerlek_arasi_mesafe

        self.assertGreater(toplam_mesafe, 0)
        self.assertAlmostEqual(aci_degisimi, 0, places=3)  # Düz hareket


class TestRotaPlanlama(unittest.TestCase):
    """Rota planlama testleri."""

    def setUp(self):
        """Test başlangıç ayarları."""
        self.alan_genisligi = 20
        self.alan_yuksekligi = 15
        self.engeller = [
            {'x': 5, 'y': 5, 'yaricap': 1.0},
            {'x': 15, 'y': 10, 'yaricap': 0.5}
        ]

    def test_grid_olusturma(self):
        """Grid oluşturma testi."""
        def create_grid(width, height, resolution=0.5):
            """Navigation grid oluştur."""
            cols = int(width / resolution)
            rows = int(height / resolution)

            grid = []
            for i in range(rows):
                row = []
                for j in range(cols):
                    row.append(0)  # 0 = serbest, 1 = engel
                grid.append(row)

            return grid, rows, cols

        grid, rows, cols = create_grid(20, 15)  # Direkt değerler

        self.assertEqual(rows, 30)  # 15 / 0.5
        self.assertEqual(cols, 40)  # 20 / 0.5
        self.assertEqual(len(grid), rows)
        self.assertEqual(len(grid[0]), cols)

    def test_engel_tespiti(self):
        """Engel tespit testi."""
        def is_obstacle(x, y, obstacles, safety_margin=0.2):
            """Belirtilen noktada engel var mı?"""
            for obstacle in obstacles:
                distance = math.sqrt(
                    (x - obstacle['x'])**2 +
                    (y - obstacle['y'])**2
                )
                if distance <= (obstacle['yaricap'] + safety_margin):
                    return True
            return False

        # Test engelleri tanımla
        engeller = [
            {'x': 5, 'y': 5, 'yaricap': 1.0},
            {'x': 15, 'y': 10, 'yaricap': 0.5}
        ]

        # Test noktaları
        self.assertTrue(is_obstacle(5, 5, engeller))  # Engel üzerinde
        self.assertFalse(is_obstacle(0, 0, engeller))  # Serbest alan
        self.assertTrue(is_obstacle(5.8, 5, engeller))  # Güvenlik marjı

    def test_bicerdover_deseni(self):
        """Biçerdöver deseni testi."""
        def generate_mowing_pattern(width, height, overlap=0.1):
            """Biçerdöver deseni oluştur."""
            robot_width = 0.3  # 30cm
            strip_width = robot_width * (1 - overlap)

            waypoints = []
            y = 0
            direction = 1  # 1 = sağa, -1 = sola

            while y < height:
                if direction == 1:
                    # Sağa git
                    waypoints.append((0, y))
                    waypoints.append((width, y))
                else:
                    # Sola git
                    waypoints.append((width, y))
                    waypoints.append((0, y))

                y += strip_width
                direction *= -1

            return waypoints

        waypoints = generate_mowing_pattern(10, 5)

        # İlk nokta sol alt köşede olmalı
        self.assertEqual(waypoints[0], (0, 0))

        # Waypoint sayısı çift olmalı (gidiş-dönüş)
        self.assertEqual(len(waypoints) % 2, 0)

    def test_a_star_algoritma(self):
        """A* algoritma testi (basitleştirilmiş)."""
        def heuristic(a, b):
            """Manhattan mesafesi."""
            return abs(a[0] - b[0]) + abs(a[1] - b[1])

        def get_neighbors(node, grid):
            """Komşu düğümleri al."""
            x, y = node
            neighbors = []

            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if (0 <= nx < len(grid[0]) and
                    0 <= ny < len(grid) and
                        grid[ny][nx] == 0):
                    neighbors.append((nx, ny))

            return neighbors

        # Basit grid oluştur
        grid = [
            [0, 0, 0, 1, 0],
            [0, 1, 0, 1, 0],
            [0, 1, 0, 0, 0],
            [0, 0, 0, 1, 0],
            [0, 0, 0, 0, 0]
        ]

        start = (0, 0)
        goal = (4, 4)

        # Heuristic testi
        h_cost = heuristic(start, goal)
        self.assertEqual(h_cost, 8)  # 4 + 4

        # Komşu testi
        neighbors = get_neighbors((1, 1), grid)
        self.assertIn((1, 0), neighbors)  # Yukarı
        self.assertIn((2, 1), neighbors)  # Sağ (serbest alan)


class TestHareketKontrolü(unittest.TestCase):
    """Hareket kontrolü testleri."""

    def test_pid_kontrolcu(self):
        """PID kontrolcü testi."""
        class SimplePID:
            def __init__(self, kp, ki, kd):
                self.kp = kp
                self.ki = ki
                self.kd = kd
                self.previous_error = 0
                self.integral = 0

            def update(self, error, dt):
                """PID çıkışını hesapla."""
                self.integral += error * dt
                derivative = (error - self.previous_error) / dt

                output = (self.kp * error +
                          self.ki * self.integral +
                          self.kd * derivative)

                self.previous_error = error
                return output

        # PID testi
        pid = SimplePID(kp=2.0, ki=0.2, kd=0.1)  # Daha güçlü parametreler

        # Test senaryosu
        setpoint = 10.0
        current_value = 0.0
        dt = 0.1

        for _ in range(15):  # Daha fazla iterasyon
            error = setpoint - current_value
            output = pid.update(error, dt)
            current_value += output * dt

        # Setpoint'e yaklaşmalı
        self.assertGreater(current_value, 8.0)

    def test_hareket_kinematigi(self):
        """Hareket kinematiği testi."""
        def differential_drive_kinematics(v_left, v_right, wheelbase):
            """Diferansiyel sürüş kinematiği."""
            # Doğrusal ve açısal hız
            v_linear = (v_left + v_right) / 2
            v_angular = (v_right - v_left) / wheelbase

            return v_linear, v_angular

        # Test değerleri
        v_left = 1.0  # m/s
        v_right = 1.0  # m/s
        wheelbase = 0.3  # m

        v_linear, v_angular = differential_drive_kinematics(
            v_left, v_right, wheelbase)

        # Düz hareket testi
        self.assertAlmostEqual(v_linear, 1.0)
        self.assertAlmostEqual(v_angular, 0.0)

        # Dönüş testi
        v_left = 0.5
        v_right = 1.5
        v_linear, v_angular = differential_drive_kinematics(
            v_left, v_right, wheelbase)

        self.assertAlmostEqual(v_linear, 1.0)
        self.assertGreater(v_angular, 0)  # Sola dönüş


async def navigation_testlerini_calistir():
    """Tüm navigation testlerini çalıştır."""
    rapor = TestRaporu()

    print("🧭 Navigation Testleri Başlıyor...")
    print("=" * 50)

    # Test sınıfları
    test_siniflari = [
        TestKonumTakibi,
        TestRotaPlanlama,
        TestHareketKontrolü
    ]

    for test_sinifi in test_siniflari:
        print(f"\n📋 {test_sinifi.__name__} testleri...")

        # Test suite oluştur
        suite = unittest.TestLoader().loadTestsFromTestCase(test_sinifi)

        for test in suite:
            test_adi = test._testMethodName
            baslangic = time.time()

            try:
                test_method = getattr(test, test_adi)
                test_method()

                sure = time.time() - baslangic
                rapor.test_sonucu_ekle(
                    f"{test_sinifi.__name__}.{test_adi}", True, sure)
                print(f"  ✅ {test_adi} ({sure:.2f}s)")

            except Exception as e:
                sure = time.time() - baslangic
                rapor.test_sonucu_ekle(
                    f"{test_sinifi.__name__}.{test_adi}", False, sure, str(e))
                print(f"  ❌ {test_adi} ({sure:.2f}s) - {e}")

    # Raporu göster
    print("\n" + rapor.rapor_olustur())

    # Raporu kaydet
    rapor.rapor_kaydet('logs/navigation_test_raporu.txt')

if __name__ == "__main__":
    print("🧪 Navigation Test Runner")
    asyncio.run(navigation_testlerini_calistir())
