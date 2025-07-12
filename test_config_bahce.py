#!/usr/bin/env python3
"""
🧪 RotaPlanlayici Config Test
Hacı Abi'nin bahçe koordinatları yükleme testini yapalım!
"""

import os
import sys

sys.path.append('/workspaces/oba/src')

import yaml

from navigation.rota_planlayici import RotaPlanlayici


def test_config_bahce_koordinatlari():
    """🧪 Config'ten bahçe koordinatları yükleme testi"""

    print("🧪 ===== ROTA PLANLAYICI CONFIG TEST =====")

    # Config dosyasını yükle
    try:
        with open('/workspaces/oba/config/robot_config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        print("✅ Config dosyası yüklendi")
    except Exception as e:
        print(f"❌ Config yükleme hatası: {e}")
        return

    # Navigation config'i al
    nav_config = config.get('navigation', {})
    print(f"🧭 Navigation config bulundu: {bool(nav_config)}")

    # Bahçe koordinatlarını kontrol et
    boundary_coords = nav_config.get('boundary_coordinates', [])
    print(f"🏡 Bahçe koordinatları: {len(boundary_coords)} nokta")

    for i, coord in enumerate(boundary_coords):
        lat = coord.get('latitude')
        lon = coord.get('longitude')
        print(f"  📍 Nokta {i+1}: {lat:.6f}, {lon:.6f}")

    # RotaPlanlayici'yı oluştur ve test et
    try:
        print("\n🤖 RotaPlanlayici oluşturuluyor...")
        rota_planlayici = RotaPlanlayici(nav_config)

        # Çalışma alanı kontrolü
        if rota_planlayici.calisma_alani:
            alan = rota_planlayici.calisma_alani
            genislik = alan.sag_ust.x - alan.sol_alt.x
            yukseklik = alan.sag_ust.y - alan.sol_alt.y

            print(f"✅ Çalışma alanı başarıyla ayarlandı:")
            print(f"   📏 Boyutlar: {genislik:.1f}m x {yukseklik:.1f}m")
            print(f"   � Toplam alan: {(genislik * yukseklik):.0f} m²")
            print(f"   �📍 Sol-Alt: ({alan.sol_alt.x:.2f}, {alan.sol_alt.y:.2f})")
            print(f"   📍 Sağ-Üst: ({alan.sag_ust.x:.2f}, {alan.sag_ust.y:.2f})")
            print(f"   🚧 Engel sayısı: {len(alan.engeller)}")

            # Grid bilgileri
            print(f"   🔢 Grid boyutu: {rota_planlayici.grid_genislik} x {rota_planlayici.grid_yukseklik}")
            print(f"   📐 Grid çözünürlüğü: {rota_planlayici.grid_resolution}m")
            print(f"   💾 Toplam grid hücresi: {rota_planlayici.grid_genislik * rota_planlayici.grid_yukseklik:,}")

        else:
            print("❌ Çalışma alanı ayarlanamadı!")

    except Exception as e:
        print(f"❌ RotaPlanlayici oluşturma hatası: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_config_bahce_koordinatlari()
