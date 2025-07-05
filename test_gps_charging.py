#!/usr/bin/env python3
"""
🧪 GPS Destekli Şarj İstasyonu Test Scripti
Hacı Abi'nin test aracı!

Bu script GPS koordinatları ile şarj sistemi fonksiyonlarını test eder.
"""

import asyncio
import os
import sys

# Proje kök dizinini sys.path'e ekle
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.navigation.konum_takipci import KonumTakipci
from src.navigation.rota_planlayici import RotaPlanlayici


async def test_gps_sarj_sistemi():
    """🔋 GPS destekli şarj sistemi test"""
    print("🧪 GPS Destekli Şarj Sistemi Test Başlatılıyor...")
    print("=" * 60)

    # Test konfigürasyonu
    nav_config = {
        "wheel_diameter": 0.065,
        "wheel_base": 0.235,
        "kalman": {
            "process_noise": 0.1,
            "measurement_noise": 0.5
        },
        "path_planning": {
            "grid_resolution": 0.1,
            "obstacle_padding": 0.2
        }
    }

    # Şarj istasyonu GPS konfigürasyonu (Ankara Kızılay örneği)
    gps_dock_config = {
        "latitude": 39.933400,
        "longitude": 32.859742,
        "altitude": 850.0,
        "accuracy_radius": 3.0
    }

    # Test senaryoları
    test_scenarios = [
        {
            "name": "🎯 Hassas Mesafe (2m)",
            "robot_lat": 39.933420,  # ~2m uzak
            "robot_lon": 32.859760
        },
        {
            "name": "🧭 Orta Mesafe (8m)",
            "robot_lat": 39.933480,  # ~8m uzak
            "robot_lon": 32.859820
        },
        {
            "name": "🗺️ Uzak Mesafe (50m)",
            "robot_lat": 39.933850,  # ~50m uzak
            "robot_lon": 32.860200
        },
        {
            "name": "❌ Çok Uzak (500m)",
            "robot_lat": 39.938000,  # ~500m uzak
            "robot_lon": 32.865000
        }
    ]

    try:
        # Konum takipçi başlat
        konum_takipci = KonumTakipci(nav_config)

        # GPS referans noktası ayarla (robot başlangıç konumu)
        await konum_takipci.ilk_konum_belirle()

        print("✅ Konum takipçi hazır")
        print()

        # Rota planlayıcı başlat
        rota_planlayici = RotaPlanlayici(nav_config)

        print("✅ Rota planlayıcı hazır")
        print()

        # Test senaryolarını çalıştır
        for i, senaryo in enumerate(test_scenarios, 1):
            print(f"📍 TEST {i}: {senaryo['name']}")
            print("-" * 40)

            # Robot konumunu simüle et
            konum_takipci.mevcut_konum.latitude = senaryo["robot_lat"]
            konum_takipci.mevcut_konum.longitude = senaryo["robot_lon"]

            # GPS doğruluk analizi
            gps_analiz = konum_takipci.gps_hedef_dogrulugu(
                gps_dock_config["latitude"],
                gps_dock_config["longitude"],
                gps_dock_config["accuracy_radius"]
            )

            print(f"📏 Mesafe: {gps_analiz['mesafe']:.1f} metre")
            print(f"🧭 Yön: {gps_analiz['bearing']:.1f}°")
            print(f"🎯 Doğruluk: {gps_analiz['dogruluk_seviyesi']}")
            print(f"📊 Güvenilirlik: {gps_analiz['guvenilirlik']:.0%}")

            # Rota planlaması test
            try:
                sarj_rota = await rota_planlayici.sarj_istasyonu_rotasi(
                    konum_takipci=konum_takipci,
                    gps_dock_config=gps_dock_config
                )

                if sarj_rota:
                    print(f"✅ Rota oluşturuldu: {len(sarj_rota)} waypoint")

                    # İlk ve son waypoint'i göster
                    if len(sarj_rota) > 0:
                        ilk_wp = sarj_rota[0]
                        son_wp = sarj_rota[-1]
                        print(f"   🚀 Başlangıç: ({ilk_wp.nokta.x:.1f}, {ilk_wp.nokta.y:.1f}) @ {ilk_wp.hiz:.2f}m/s")
                        print(f"   🏁 Son nokta: ({son_wp.nokta.x:.1f}, {son_wp.nokta.y:.1f}) @ {son_wp.hiz:.2f}m/s")
                else:
                    print("❌ Rota oluşturulamadı")

            except Exception as e:
                print(f"❌ Rota planlama hatası: {e}")

            print()

        # Performans testi
        print("⚡ PERFORMANS TESTİ")
        print("-" * 40)

        import time
        start_time = time.time()

        # 100 kez mesafe hesaplama
        for _ in range(100):
            mesafe = konum_takipci.get_mesafe_to_gps(
                gps_dock_config["latitude"],
                gps_dock_config["longitude"]
            )

        elapsed = time.time() - start_time
        print(f"📊 100 mesafe hesaplama: {elapsed:.3f} saniye")
        print(f"⚡ Ortalama: {elapsed/100*1000:.1f} ms/hesaplama")

        # Haversine doğruluk testi
        print()
        print("🌍 HARVERSİNE DOĞRULUK TESTİ")
        print("-" * 40)

        # Bilinen mesafeli koordinatlar (Ankara merkez)
        test_coords = [
            {"lat": 39.933400, "lon": 32.859742, "expected": 0, "name": "Aynı nokta"},
            {"lat": 39.934400, "lon": 32.859742, "expected": 111, "name": "1' kuzey (yaklaşık)"},
            {"lat": 39.933400, "lon": 32.860742, "expected": 78, "name": "1' doğu (yaklaşık)"}
        ]

        for test in test_coords:
            hesaplanan = konum_takipci.get_mesafe_to_gps(test["lat"], test["lon"])
            hata = abs(hesaplanan - test["expected"])
            hata_yuzde = (hata / max(test["expected"], 1)) * 100

            print(f"📍 {test['name']}: {hesaplanan:.0f}m (beklenen: {test['expected']}m, hata: {hata_yuzde:.1f}%)")

        print()
        print("🎉 Tüm testler tamamlandı!")

    except Exception as e:
        print(f"❌ Test hatası: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🤖 OBA - GPS Şarj İstasyonu Test Aracı")
    print("Hacı Abi'nin yazdığı test scripti çalışıyor...")
    print()

    asyncio.run(test_gps_sarj_sistemi())
