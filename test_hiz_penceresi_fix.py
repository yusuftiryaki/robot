#!/usr/bin/env python3
"""
🧪 Hız Penceresi Fix Test
Hacı Abi'nin dinamik pencere hesaplaması düzgün çalışıyor mu test edelim!
"""

import logging
import os
import sys

# Proje kök dizinini ekle
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from navigation.dinamik_engel_kacinici import DinamikEngelKacinici
from navigation.rota_planlayici import Nokta

# Test konfigürasyonu
robot_config = {
    "max_linear_speed": 0.5,      # 50 cm/s
    "max_angular_speed": 1.0,     # 1 rad/s
    "max_linear_accel": 0.5,      # 50 cm/s²
    "max_angular_accel": 1.0,     # 1 rad/s²
    "robot_radius": 0.3,          # 30cm
    "safety_distance": 0.5,       # 50cm
    "lookahead_distance": 2.0     # 2m
}


def test_hiz_penceresi_problemli_durumlar():
    """Problematik durumları test et"""
    logging.basicConfig(level=logging.DEBUG)

    kacinici = DinamikEngelKacinici(robot_config)

    test_cases = [
        # (mevcut_v, mevcut_w, açıklama)
        (0.0, 0.0, "Başlangıç durumu - durgun"),
        (0.5, 0.0, "Maksimum hızda düz gidiş"),
        (0.6, 0.0, "Maksimum hızdan fazla - sınırlanmalı"),
        (-0.1, 0.0, "Negatif hız - sıfırlanmalı"),
        (0.1, 1.2, "Maksimum açısal hızdan fazla"),
        (0.001, 0.001, "Çok küçük hızlar"),
    ]

    print("🧪 Hız Penceresi Test Senaryoları")
    print("=" * 50)

    for mevcut_v, mevcut_w, aciklama in test_cases:
        print(f"\n📊 Test: {aciklama}")
        print(f"   Giriş: v={mevcut_v:.3f} m/s, w={mevcut_w:.3f} rad/s")

        hiz_penceresi = kacinici._dynamic_window_hesapla(mevcut_v, mevcut_w)

        print(f"   Sonuç: doğrusal={len(hiz_penceresi['dogrusal'])} eleman, "
              f"açısal={len(hiz_penceresi['acisal'])} eleman")

        if len(hiz_penceresi['dogrusal']) == 0:
            print("   ❌ HATA: Doğrusal hız penceresi boş!")
        else:
            print(f"   ✅ Doğrusal aralık: {hiz_penceresi['dogrusal'][0]:.3f} - "
                  f"{hiz_penceresi['dogrusal'][-1]:.3f}")

        if len(hiz_penceresi['acisal']) == 0:
            print("   ❌ HATA: Açısal hız penceresi boş!")
        else:
            print(f"   ✅ Açısal aralık: {hiz_penceresi['acisal'][0]:.3f} - "
                  f"{hiz_penceresi['acisal'][-1]:.3f}")


def test_hiz_asimi_senaryosu():
    """🚨 Hız aşımı senaryolarını test et"""
    print("\n\n🚨 Hız Aşımı Test Senaryoları")
    print("=" * 50)

    kacinici = DinamikEngelKacinici(robot_config)

    aşım_senaryoları = [
        # (mevcut_v, mevcut_w, açıklama)
        (0.6, 0.0, "Hafif doğrusal hız aşımı"),
        (0.8, 0.0, "Ciddi doğrusal hız aşımı - acil müdahale"),
        (0.4, 1.5, "Hafif açısal hız aşımı"),
        (0.4, 2.0, "Ciddi açısal hız aşımı - acil müdahale"),
        (0.7, 1.8, "Hem doğrusal hem açısal aşım"),
    ]

    for mevcut_v, mevcut_w, aciklama in aşım_senaryoları:
        print(f"\n📊 Test: {aciklama}")
        print(f"   Giriş: v={mevcut_v:.3f} m/s, w={mevcut_w:.3f} rad/s")

        # Hız aşımı kontrolü
        hiz_kontrol = kacinici.hiz_asimi_kontrol(mevcut_v, mevcut_w)

        print(f"   Doğrusal aşım: {hiz_kontrol['dogrusal_asim']}")
        print(f"   Açısal aşım: {hiz_kontrol['acisal_asim']}")
        print(f"   Acil müdahale: {hiz_kontrol['acil_mudahale_gerekli']}")

        if hiz_kontrol['acil_mudahale_gerekli']:
            komutlar = hiz_kontrol['onerilen_komutlar']
            print(f"   🛑 Acil komutlar: v={komutlar['dogrusal_hiz']:.3f}, "
                  f"w={komutlar['acisal_hiz']:.3f}")

        # Gerçek hareket komutları testi
        mevcut_konum = Nokta(0.0, 0.0)
        mevcut_hiz = (mevcut_v, mevcut_w)
        hedef_nokta = Nokta(2.0, 2.0)

        hareket_komutlari = kacinici.en_iyi_hareket_bul(
            mevcut_konum, mevcut_hiz, hedef_nokta
        )

        if hareket_komutlari:
            print(f"   ✅ Sonuç komutlar: v={hareket_komutlari.dogrusal_hiz:.3f}, "
                  f"w={hareket_komutlari.acisal_hiz:.3f}")
        else:
            print("   ❌ Hareket komutu bulunamadı!")


def test_tam_hareket_senaryo():
    """Tam hareket senaryosu test et"""
    print("\n\n🎯 Tam Hareket Senaryo Testi")
    print("=" * 50)

    kacinici = DinamikEngelKacinici(robot_config)

    # Test senaryosu
    mevcut_konum = Nokta(0.0, 0.0)
    mevcut_hiz = (0.0, 0.0)  # Durgun başlangıç
    hedef_nokta = Nokta(2.0, 2.0)

    print(f"🚀 Robot başlangıç: ({mevcut_konum.x}, {mevcut_konum.y})")
    print(f"🎯 Hedef nokta: ({hedef_nokta.x}, {hedef_nokta.y})")
    print(f"⚡ Mevcut hız: v={mevcut_hiz[0]:.2f}, w={mevcut_hiz[1]:.2f}")

    hareket_komutlari = kacinici.en_iyi_hareket_bul(
        mevcut_konum, mevcut_hiz, hedef_nokta
    )

    if hareket_komutlari:
        print("✅ Hareket komutu bulundu:")
        print(f"   Doğrusal hız: {hareket_komutlari.dogrusal_hiz:.3f} m/s")
        print(f"   Açısal hız: {hareket_komutlari.acisal_hiz:.3f} rad/s")
        print(f"   Güvenlik skoru: {hareket_komutlari.guvenlik_skoru:.3f}")
    else:
        print("❌ Hareket komutu bulunamadı!")


if __name__ == "__main__":
    test_hiz_penceresi_problemli_durumlar()
    test_hiz_asimi_senaryosu()
    test_tam_hareket_senaryo()
    print("\n🎉 Test tamamlandı!")
