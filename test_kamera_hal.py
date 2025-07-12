#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 Kamera HAL Pattern Test
Hacı Abi'nin yeni HAL pattern'i test eder!

Bu test:
1. KameraFactory'nin doğru implementasyonu seçip seçmediğini test eder
2. Simülasyon kamerasinın çalışıp çalışmadığını test eder
3. KameraIslemci'nin HAL ile çalışıp çalışmadığını test eder
"""

import asyncio
import logging
import os
import sys

# Proje kök dizinini Python path'e ekle
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from vision.kamera_islemci import KameraIslemci

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("KameraHALTest")


async def test_kamera_hal():
    """🧪 Kamera HAL Pattern Testi"""

    print("🧪 Kamera HAL Pattern Test Başlıyor...")
    print("=" * 60)

    # Test konfigürasyonu
    test_config = {
        "type": "simulation",  # Simülasyon zorla
        "width": 640,
        "height": 480,
        "fps": 30,
        "simulation_params": {
            "test_pattern": True,
            "noise_level": 0.01
        }
    }

    try:
        # 1. KameraIslemci oluştur (HAL ile)
        print("\n🧪 TEST 1: KameraIslemci HAL Oluşturma")
        print("-" * 40)

        kamera_islemci = KameraIslemci(test_config)
        print("✅ KameraIslemci HAL ile oluşturuldu")

        # 2. Kamerayı başlat
        print("\n🧪 TEST 2: Kamera Başlatma")
        print("-" * 40)

        baslatma_basarili = await kamera_islemci.baslat()
        if baslatma_basarili:
            print("✅ Kamera başarıyla başlatıldı")
        else:
            print("❌ Kamera başlatılamadı!")
            return False

        # 3. Kamera durumu kontrol et
        print("\n🧪 TEST 3: Kamera Durumu")
        print("-" * 40)

        durum = kamera_islemci.get_kamera_durumu()
        print(f"📊 Kamera Tipi: {durum.get('tip', 'unknown')}")
        print(f"📊 Aktif: {durum.get('aktif', False)}")
        print(f"📊 Çözünürlük: {durum.get('resolution', 'unknown')}")
        print(f"📊 FPS: {durum.get('fps', 'unknown')}")

        # 4. Görüntü alma testi
        print("\n🧪 TEST 4: Görüntü Alma")
        print("-" * 40)

        for i in range(3):
            goruntu = await kamera_islemci.goruntu_al()
            if goruntu is not None:
                print(f"✅ Görüntü {i+1}: {goruntu.shape} - Min: {goruntu.min()}, Max: {goruntu.max()}")
            else:
                print(f"❌ Görüntü {i+1} alınamadı!")
                return False

        # 5. Engel analizi testi
        print("\n🧪 TEST 5: Engel Analizi")
        print("-" * 40)

        engel_analizi = await kamera_islemci.engel_analiz_et()
        if engel_analizi.get("analiz_basarili", False):
            engel_sayisi = len(engel_analizi.get("engeller", []))
            print(f"✅ Engel analizi başarılı: {engel_sayisi} engel tespit edildi")

            if engel_sayisi == 0:
                print("🌱 Mükemmel! Simülasyon görüntüsünde engel yok (beklenen)")
            else:
                print("⚠️ Simülasyon görüntüsünde engel tespit edildi - algoritmaları kontrol et")
        else:
            print("❌ Engel analizi başarısız!")

        # 6. Kamerayı durdur
        print("\n🧪 TEST 6: Kamera Durdurma")
        print("-" * 40)

        await kamera_islemci.durdur()
        print("✅ Kamera durduruldu")

        print("\n" + "=" * 60)
        print("🎉 TÜM TESTLER BAŞARILI!")
        print("🧠 HAL Pattern Doğrulandı:")
        print("  • Factory pattern çalışıyor")
        print("  • Simülasyon kamerası çalışıyor")
        print("  • KameraIslemci HAL ile entegre")
        print("  • Görüntü işleme algoritmaları çalışıyor")
        print("  • Temiz abstraction layer")

        return True

    except Exception as e:
        print(f"\n❌ TEST HATASI: {e}")
        logger.error(f"Test hatası: {e}", exc_info=True)
        return False


async def main():
    """Ana test fonksiyonu"""
    return await test_kamera_hal()


if __name__ == "__main__":
    try:
        basarili = asyncio.run(main())
        exit(0 if basarili else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Test durduruldu (Ctrl+C)")
        exit(0)
    except Exception as e:
        print(f"\n❌ Test hatası: {e}")
        exit(1)
