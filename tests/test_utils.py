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

import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict

# Proje klasörünü Python path'ine ekle
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# GPS dataclass'ını import et
from hardware.hal.interfaces import GPSVeri

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
                'ivme_x': 0.1, 'ivme_y': 0.05, 'ivme_z': 9.8,
                'gyro_x': 0.01, 'gyro_y': 0.02, 'gyro_z': 0.0,
                'compass_baslik': 45.0,
                'sicaklik': 25.0,
                'kalibrasyon_durumu': True,
                'hata_mesaji': None
            },
            'gps': GPSVeri(
                timestamp=datetime.now().isoformat(),
                gecerli=True,
                enlem=41.0082,
                boylam=28.9784,
                yukseklik=50.0,
                uydu_sayisi=8,
                fix_kalitesi=3,
                hiz=0.0,
                yön=0.0
            ),
            'guc': {
                'voltaj': 12.5,
                'akim': 2.1,
                'guc': 26.25,
                'sarj_durumu': 85,
                'sarj_oluyor': False,
                'sicaklik': 35.0,
                'hata_mesaji': None
            },
            'tampon': {
                'on_sol': False,
                'on_sag': False,
                'sol': False,
                'sag': False,
                'arka': False,
                'hata_mesaji': None
            },
            'enkoder': {
                'sol_tekerlek_sayac': 1234,
                'sag_tekerlek_sayac': 1240,
                'sol_tekerlek_hiz': 50.0,
                'sag_tekerlek_hiz': 52.0,
                'hata_mesaji': None
            },
            'acil_durma': {
                'durum': False,
                'hata_mesaji': None
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
    print(f"   IMU: {sensor_data['imu']['ivme_x']:.2f}, {sensor_data['imu']['ivme_y']:.2f}, {sensor_data['imu']['ivme_z']:.2f}")
    print(f"   GPS: {sensor_data['gps'].enlem:.4f}, {sensor_data['gps'].boylam:.4f}")
    print(f"   Güç: {sensor_data['guc']['sarj_durumu']}%")

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

    print("\n✅ Test araçları hazır!")
