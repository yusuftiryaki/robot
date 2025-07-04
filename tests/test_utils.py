#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Otonom Bahçe Asistanı (OBA) - Test Araçları
=================================

Bu modül robot sisteminin test edilmesi için gerekli araçları içerir.
Unit testler, integration testler ve simülasyon testleri sağlar.

Kullanım:
    python -m pytest tests/
    python tests/test_runner.py
"""

import sys
import os
import asyncio
import unittest
import logging
from typing import Dict, List, Any

# Proje klasörünü Python path'ine ekle
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Test logger ayarları
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestVeriUreticisi:
    """Test verileri üreten yardımcı sınıf."""
    
    @staticmethod
    def ornek_sensor_verisi() -> Dict[str, Any]:
        """Örnek sensör verisi üret."""
        return {
            'imu': {
                'ivme': {'x': 0.1, 'y': 0.05, 'z': 9.8},
                'gyro': {'x': 0.01, 'y': 0.02, 'z': 0.0},
                'compass': {'baslik': 45.0}
            },
            'gps': {
                'latitude': 41.0082,
                'longitude': 28.9784,
                'altitude': 50.0,
                'fix_quality': 3
            },
            'batarya': {
                'voltaj': 12.5,
                'akim': 2.1,
                'sicaklik': 35.0,
                'sarj_durumu': 85
            },
            'ultrasonik': {
                'on': 25.0,
                'on_sol': 30.0,
                'on_sag': 28.0,
                'sol': 50.0,
                'sag': 45.0,
                'arka': 100.0
            },
            'tampon': {
                'on_sol': False,
                'on_sag': False,
                'sol': False,
                'sag': False
            }
        }
    
    @staticmethod
    def ornek_motor_verisi() -> Dict[str, Any]:
        """Örnek motor verisi üret."""
        return {
            'sol_tekerlek': {
                'hiz': 50,
                'yon': 'ileri',
                'encoder': 1234,
                'akim': 0.8
            },
            'sag_tekerlek': {
                'hiz': 50,
                'yon': 'ileri', 
                'encoder': 1240,
                'akim': 0.9
            },
            'firca': {
                'hiz': 75,
                'aktif': True,
                'akim': 1.2
            },
            'fan': {
                'hiz': 60,
                'aktif': True,
                'akim': 0.5
            }
        }
    
    @staticmethod
    def ornek_konum_verisi() -> Dict[str, Any]:
        """Örnek konum verisi üret."""
        return {
            'x': 10.5,
            'y': 8.2,
            'theta': 1.57,  # 90 derece
            'hiz': 0.5,
            'acisal_hiz': 0.1,
            'kalman_durumu': {
                'x': 10.48,
                'y': 8.21,
                'theta': 1.56,
                'vx': 0.51,
                'vy': 0.02,
                'vtheta': 0.09
            }
        }
    
    @staticmethod
    def ornek_gorev_verisi() -> Dict[str, Any]:
        """Örnek görev verisi üret."""
        return {
            'id': 'test_gorev_001',
            'tip': 'alan_bicme',
            'durum': 'bekliyor',
            'alan': {
                'baslangic': {'x': 0, 'y': 0},
                'bitis': {'x': 20, 'y': 15},
                'engeller': [
                    {'x': 5, 'y': 5, 'yaricap': 1.0},
                    {'x': 15, 'y': 10, 'yaricap': 0.5}
                ]
            },
            'parametreler': {
                'bicme_yuksekligi': 3.0,
                'bicme_hizi': 0.3,
                'kaplama_orani': 0.8
            }
        }

class TestKonfigurasyonu:
    """Test konfigürasyon sınıfı."""
    
    def __init__(self):
        """Test konfigürasyonunu başlat."""
        self.test_config = {
            'simulation': True,
            'debug': True,
            'test_timeout': 10.0,
            'sensor_test_interval': 0.1,
            'motor_test_interval': 0.1,
            'network_test_timeout': 5.0
        }
    
    def get_config(self, key: str, default=None):
        """Test konfigürasyon değeri al."""
        return self.test_config.get(key, default)

class TestYardimcilari:
    """Test yardımcı fonksiyonları."""
    
    @staticmethod
    def assert_sensor_data_valid(sensor_data: Dict[str, Any]) -> bool:
        """Sensör verisinin geçerli olup olmadığını kontrol et."""
        required_keys = ['imu', 'gps', 'batarya', 'ultrasonik', 'tampon']
        
        for key in required_keys:
            if key not in sensor_data:
                return False
        
        # IMU kontrolü
        imu_data = sensor_data['imu']
        if not all(k in imu_data for k in ['ivme', 'gyro', 'compass']):
            return False
        
        # GPS kontrolü
        gps_data = sensor_data['gps']
        if not all(k in gps_data for k in ['latitude', 'longitude', 'altitude']):
            return False
        
        # Batarya kontrolü
        batarya_data = sensor_data['batarya']
        if not all(k in batarya_data for k in ['voltaj', 'akim', 'sarj_durumu']):
            return False
        
        return True
    
    @staticmethod
    def assert_motor_data_valid(motor_data: Dict[str, Any]) -> bool:
        """Motor verisinin geçerli olup olmadığını kontrol et."""
        required_keys = ['sol_tekerlek', 'sag_tekerlek', 'firca', 'fan']
        
        for key in required_keys:
            if key not in motor_data:
                return False
        
        # Tekerlek kontrolü
        for tekerlek in ['sol_tekerlek', 'sag_tekerlek']:
            tekerlek_data = motor_data[tekerlek]
            if not all(k in tekerlek_data for k in ['hiz', 'yon', 'encoder']):
                return False
        
        return True
    
    @staticmethod
    def assert_konum_data_valid(konum_data: Dict[str, Any]) -> bool:
        """Konum verisinin geçerli olup olmadığını kontrol et."""
        required_keys = ['x', 'y', 'theta', 'hiz']
        
        for key in required_keys:
            if key not in konum_data:
                return False
        
        # Açı kontrolü (-π <= theta <= π)
        theta = konum_data['theta']
        if not (-3.14159 <= theta <= 3.14159):
            return False
        
        return True
    
    @staticmethod
    async def wait_for_condition(condition_func, timeout: float = 5.0, interval: float = 0.1) -> bool:
        """Belirli bir koşul sağlanana kadar bekle."""
        start_time = asyncio.get_event_loop().time()
        
        while True:
            if condition_func():
                return True
            
            current_time = asyncio.get_event_loop().time()
            if current_time - start_time > timeout:
                return False
            
            await asyncio.sleep(interval)

class TestRaporu:
    """Test raporu oluşturan sınıf."""
    
    def __init__(self):
        """Test raporu sınıfını başlat."""
        self.test_sonuclari = []
        self.basari_sayisi = 0
        self.basarisizlik_sayisi = 0
        self.toplam_sure = 0.0
    
    def test_sonucu_ekle(self, test_adi: str, basarili: bool, sure: float, detay: str = ""):
        """Test sonucu ekle."""
        self.test_sonuclari.append({
            'test_adi': test_adi,
            'basarili': basarili,
            'sure': sure,
            'detay': detay
        })
        
        if basarili:
            self.basari_sayisi += 1
        else:
            self.basarisizlik_sayisi += 1
        
        self.toplam_sure += sure
    
    def rapor_olustur(self) -> str:
        """Test raporu oluştur."""
        toplam_test = self.basari_sayisi + self.basarisizlik_sayisi
        basari_orani = (self.basari_sayisi / toplam_test * 100) if toplam_test > 0 else 0
        
        rapor = f"""
🧪 TEST RAPORU
{'=' * 50}
📊 Toplam Test: {toplam_test}
✅ Başarılı: {self.basari_sayisi}
❌ Başarısız: {self.basarisizlik_sayisi}
📈 Başarı Oranı: {basari_orani:.1f}%
⏱️ Toplam Süre: {self.toplam_sure:.2f} saniye

📋 DETAYLAR:
{'-' * 50}
"""
        
        for sonuc in self.test_sonuclari:
            durum = "✅" if sonuc['basarili'] else "❌"
            rapor += f"{durum} {sonuc['test_adi']:<30} ({sonuc['sure']:.2f}s)\n"
            if sonuc['detay']:
                rapor += f"   └─ {sonuc['detay']}\n"
        
        rapor += f"\n{'=' * 50}\n"
        return rapor
    
    def rapor_kaydet(self, dosya_yolu: str):
        """Test raporunu dosyaya kaydet."""
        with open(dosya_yolu, 'w', encoding='utf-8') as f:
            f.write(self.rapor_olustur())

# Test yardımcı fonksiyonları
def setup_test_environment():
    """Test ortamını hazırla."""
    # Log klasörünü oluştur
    os.makedirs('logs', exist_ok=True)
    
    # Test data klasörünü oluştur
    os.makedirs('test_data', exist_ok=True)
    
    logger.info("Test ortamı hazırlandı")

def cleanup_test_environment():
    """Test ortamını temizle."""
    logger.info("Test ortamı temizlendi")

if __name__ == "__main__":
    # Test araçlarını demo olarak çalıştır
    print("🧪 Test Araçları Demo")
    print("=" * 50)
    
    # Test verilerini göster
    veri_uretici = TestVeriUreticisi()
    
    print("📊 Örnek Sensör Verisi:")
    sensor_data = veri_uretici.ornek_sensor_verisi()
    print(f"   IMU: {sensor_data['imu']['ivme']}")
    print(f"   GPS: {sensor_data['gps']['latitude']:.4f}, {sensor_data['gps']['longitude']:.4f}")
    print(f"   Batarya: {sensor_data['batarya']['sarj_durumu']}%")
    
    print("\n🚗 Örnek Motor Verisi:")
    motor_data = veri_uretici.ornek_motor_verisi()
    print(f"   Sol Tekerlek: {motor_data['sol_tekerlek']['hiz']} hız")
    print(f"   Sağ Tekerlek: {motor_data['sag_tekerlek']['hiz']} hız")
    print(f"   Fırça: {'Aktif' if motor_data['firca']['aktif'] else 'Pasif'}")
    
    print("\n📍 Örnek Konum Verisi:")
    konum_data = veri_uretici.ornek_konum_verisi()
    print(f"   Pozisyon: ({konum_data['x']:.1f}, {konum_data['y']:.1f})")
    print(f"   Açı: {konum_data['theta']:.2f} radyan")
    print(f"   Hız: {konum_data['hiz']:.1f} m/s")
    
    # Test yardımcılarını göster
    print("\n🔍 Test Yardımcıları:")
    yardimcilar = TestYardimcilari()
    
    print(f"   Sensör verisi geçerli: {yardimcilar.assert_sensor_data_valid(sensor_data)}")
    print(f"   Motor verisi geçerli: {yardimcilar.assert_motor_data_valid(motor_data)}")
    print(f"   Konum verisi geçerli: {yardimcilar.assert_konum_data_valid(konum_data)}")
    
    print("\n✅ Test araçları hazır!")
