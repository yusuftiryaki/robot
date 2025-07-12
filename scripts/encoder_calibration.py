#!/usr/bin/env python3
"""
🔧 Encoder Kalibrasyon Scripti - Hacı Abi'nin Hassas Ölçüm Aracı

Bu script, robotun encoder'larını kalibre eder ve doğru mesafe ölçümü için
gerekli kalibrasyonu yapar. Encoder'lar olmadan robot kör gibi hareket eder!

Kalibrasyon adımları:
1. Fiziksel mesafe ölçümü (metre ile)
2. Encoder pulse sayısı ölçümü
3. Pulse per meter hesaplama
4. Konfigürasyon dosyasını güncelleme
5. Doğrulama testi

Kullanım:
    python encoder_calibration.py --distance 1.0 --test
    python encoder_calibration.py --interactive
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict

import yaml

# Proje kök dizinini path'e ekle
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.smart_config import SmartConfigManager
from src.hardware.motor_kontrolcu import HareketKomut, MotorKontrolcu


class EncoderKalibrator:
    """
    🔧 Encoder Kalibrasyon Sınıfı

    Encoder'ları kalibre eder ve doğru mesafe ölçümü için
    gerekli parametreleri hesaplar.
    """

    def __init__(self, config_path: str = None):
        """Kalibratör başlatma"""
        self.logger = logging.getLogger(__name__)
        self.config_path = config_path or "/workspaces/oba/config/robot_config.yaml"

        # Konfigürasyon yükle
        self.config_manager = SmartConfigManager(self.config_path)
        self.config = self.config_manager.load_config()

        # Motor kontrolcüsü
        self.motor_kontrolcu = None

        # Kalibrasyon sonuçları
        self.kalibrasyon_sonuclari = {}

        # Encoder ayarları
        self.encoder_config = self.config.get("hardware", {}).get("sensors", {}).get("encoders", {})
        self.navigation_config = self.config.get("navigation", {})

        self.logger.info("🔧 Encoder Kalibratör hazır!")

    async def baslat(self):
        """Kalibratör sistemini başlat"""
        try:
            # Motor kontrolcüsünü başlat
            self.motor_kontrolcu = MotorKontrolcu(self.config)

            self.logger.info("✅ Kalibrasyon sistemi hazır!")
            return True

        except Exception as e:
            self.logger.error(f"❌ Kalibrasyon sistemi başlatma hatası: {e}")
            return False

    async def kapat(self):
        """Sistemi temizle"""
        if self.motor_kontrolcu:
            await self.motor_kontrolcu.durdur()

    async def mesafe_kalibrasyonu(self, hedef_mesafe: float = 1.0) -> Dict:
        """
        📏 Mesafe kalibrasyonu yapar

        Args:
            hedef_mesafe: Kalibre edilecek mesafe (metre)

        Returns:
            Kalibrasyon sonuçları
        """
        self.logger.info(f"📏 Mesafe kalibrasyonu başlıyor: {hedef_mesafe}m")

        # Encoder sayaçlarını sıfırla
        await self._encoder_sayaclarini_sifirla()

        # Başlangıç encoder değerleri
        baslangic_encoders = await self._encoder_degerlerini_oku()

        print(f"\n🚀 Robot {hedef_mesafe}m ileri hareket edecek...")
        print("📐 Lütfen fiziksel mesafeyi metre ile ölçün!")
        input("Hazır olduğunuzda Enter'a basın...")

        # İleri hareket et
        hareket = HareketKomut(
            linear_hiz=0.2,  # yavaş hareket
            angular_hiz=0.0,
            sure=hedef_mesafe / 0.2  # süre hesaplama
        )

        await self.motor_kontrolcu.hareket_uygula(hareket)

        # Biraz bekle
        await asyncio.sleep(0.5)

        # Bitiş encoder değerleri
        bitis_encoders = await self._encoder_degerlerini_oku()

        # Fiziksel mesafe ölçümü al
        print("\n📐 Robot hareket etti!")
        fiziksel_mesafe = float(input("Fiziksel mesafeyi metre cinsinden girin: "))

        # Kalibrasyon hesapla
        sonuclar = self._kalibrasyon_hesapla(
            baslangic_encoders,
            bitis_encoders,
            fiziksel_mesafe
        )

        self.kalibrasyon_sonuclari = sonuclar

        # Sonuçları göster
        self._sonuclari_goster(sonuclar)

        return sonuclar

    async def donus_kalibrasyonu(self, hedef_aci: float = 90.0) -> Dict:
        """
        🔄 Dönüş kalibrasyonu yapar

        Args:
            hedef_aci: Kalibre edilecek açı (derece)

        Returns:
            Kalibrasyon sonuçları
        """
        self.logger.info(f"🔄 Dönüş kalibrasyonu başlıyor: {hedef_aci}°")

        # Encoder sayaçlarını sıfırla
        await self._encoder_sayaclarini_sifirla()

        # Başlangıç encoder değerleri
        baslangic_encoders = await self._encoder_degerlerini_oku()

        print(f"\n🔄 Robot {hedef_aci}° sağa dönecek...")
        print("📐 Lütfen fiziksel açıyı derece ile ölçün!")
        input("Hazır olduğunuzda Enter'a basın...")

        # Sağa dönüş
        import math
        angular_hiz = 0.5  # rad/s
        sure = math.radians(hedef_aci) / angular_hiz

        hareket = HareketKomut(
            linear_hiz=0.0,
            angular_hiz=angular_hiz,
            sure=sure
        )

        await self.motor_kontrolcu.hareket_uygula(hareket)

        # Biraz bekle
        await asyncio.sleep(0.5)

        # Bitiş encoder değerleri
        bitis_encoders = await self._encoder_degerlerini_oku()

        # Fiziksel açı ölçümü al
        print("\n🔄 Robot döndü!")
        fiziksel_aci = float(input("Fiziksel açıyı derece cinsinden girin: "))

        # Kalibrasyon hesapla
        sonuclar = self._donus_kalibrasyonu_hesapla(
            baslangic_encoders,
            bitis_encoders,
            fiziksel_aci
        )

        # Sonuçları göster
        self._donus_sonuclari_goster(sonuclar)

        return sonuclar

    async def _encoder_sayaclarini_sifirla(self):
        """Encoder sayaçlarını sıfırla"""
        if self.motor_kontrolcu:
            self.motor_kontrolcu.enkoder_sayaclari = {"sol": 0, "sag": 0}

    async def _encoder_degerlerini_oku(self) -> Dict:
        """Encoder değerlerini oku"""
        if self.motor_kontrolcu:
            return self.motor_kontrolcu.enkoder_sayaclari.copy()
        return {"sol": 0, "sag": 0}

    def _kalibrasyon_hesapla(self, baslangic: Dict, bitis: Dict, fiziksel_mesafe: float) -> Dict:
        """Kalibrasyon değerlerini hesapla"""
        # Encoder farkları
        sol_fark = bitis["sol"] - baslangic["sol"]
        sag_fark = bitis["sag"] - baslangic["sag"]

        # Ortalama pulse sayısı
        ortalama_pulse = (sol_fark + sag_fark) / 2

        # Pulse per meter hesaplama
        pulse_per_meter = ortalama_pulse / fiziksel_mesafe

        # Mevcut tekerlek çapı
        tekerlek_capi = self.navigation_config.get("wheel_diameter", 0.065)

        # Teorik pulse per meter (mevcut config'e göre)
        teorik_pulse_per_rev = self.encoder_config.get("sol_encoder", {}).get("pulses_per_revolution", 360)
        teorik_pulse_per_meter = teorik_pulse_per_rev / (3.14159 * tekerlek_capi)

        # Hata hesaplama
        hata_yuzdesi = ((pulse_per_meter - teorik_pulse_per_meter) / teorik_pulse_per_meter) * 100

        return {
            "fiziksel_mesafe": fiziksel_mesafe,
            "sol_pulse_fark": sol_fark,
            "sag_pulse_fark": sag_fark,
            "ortalama_pulse": ortalama_pulse,
            "pulse_per_meter": pulse_per_meter,
            "teorik_pulse_per_meter": teorik_pulse_per_meter,
            "hata_yuzdesi": hata_yuzdesi,
            "tekerlek_capi": tekerlek_capi,
            "yeni_tekerlek_capi": ortalama_pulse / (teorik_pulse_per_rev / 3.14159),
            "kalibrasyon_faktoru": pulse_per_meter / teorik_pulse_per_meter
        }

    def _donus_kalibrasyonu_hesapla(self, baslangic: Dict, bitis: Dict, fiziksel_aci: float) -> Dict:
        """Dönüş kalibrasyonu hesapla"""
        # Encoder farkları
        sol_fark = bitis["sol"] - baslangic["sol"]
        sag_fark = bitis["sag"] - baslangic["sag"]

        # Tekerlek base mevcut değeri
        tekerlek_base = self.navigation_config.get("wheel_base", 0.235)
        tekerlek_capi = self.navigation_config.get("wheel_diameter", 0.065)

        # Teorik hesaplama
        import math
        fiziksel_radyan = math.radians(fiziksel_aci)

        # Encoder'dan gelen mesafe farkı
        sol_mesafe = sol_fark * (3.14159 * tekerlek_capi / 360)  # encoder pulse'dan mesafeye
        sag_mesafe = sag_fark * (3.14159 * tekerlek_capi / 360)

        # Gerçek tekerlek base hesaplama
        gercek_tekerlek_base = abs(sol_mesafe - sag_mesafe) / fiziksel_radyan

        # Hata hesaplama
        hata_yuzdesi = ((gercek_tekerlek_base - tekerlek_base) / tekerlek_base) * 100

        return {
            "fiziksel_aci": fiziksel_aci,
            "fiziksel_radyan": fiziksel_radyan,
            "sol_pulse_fark": sol_fark,
            "sag_pulse_fark": sag_fark,
            "sol_mesafe": sol_mesafe,
            "sag_mesafe": sag_mesafe,
            "mevcut_tekerlek_base": tekerlek_base,
            "gercek_tekerlek_base": gercek_tekerlek_base,
            "hata_yuzdesi": hata_yuzdesi,
            "kalibrasyon_faktoru": gercek_tekerlek_base / tekerlek_base
        }

    def _sonuclari_goster(self, sonuclar: Dict):
        """Kalibrasyon sonuçlarını göster"""
        print("\n" + "=" * 60)
        print("📊 MESAFE KALİBRASYON SONUÇLARI")
        print("=" * 60)
        print(f"📏 Fiziksel Mesafe: {sonuclar['fiziksel_mesafe']:.3f} m")
        print(f"🔢 Sol Encoder Pulse: {sonuclar['sol_pulse_fark']}")
        print(f"🔢 Sağ Encoder Pulse: {sonuclar['sag_pulse_fark']}")
        print(f"📊 Ortalama Pulse: {sonuclar['ortalama_pulse']:.1f}")
        print(f"📐 Pulse/Meter (Gerçek): {sonuclar['pulse_per_meter']:.1f}")
        print(f"📐 Pulse/Meter (Teorik): {sonuclar['teorik_pulse_per_meter']:.1f}")
        print(f"⚠️  Hata: {sonuclar['hata_yuzdesi']:.1f}%")
        print(f"🔧 Mevcut Tekerlek Çapı: {sonuclar['tekerlek_capi']:.3f} m")
        print(f"🔧 Önerilen Tekerlek Çapı: {sonuclar['yeni_tekerlek_capi']:.3f} m")
        print(f"🔧 Kalibrasyon Faktörü: {sonuclar['kalibrasyon_faktoru']:.3f}")
        print("=" * 60)

        # Tavsiye
        if abs(sonuclar['hata_yuzdesi']) < 2:
            print("✅ Kalibrasyon çok iyi! Hata %2'nin altında.")
        elif abs(sonuclar['hata_yuzdesi']) < 5:
            print("⚠️  Kalibrasyon kabul edilebilir. Hata %5'in altında.")
        else:
            print("❌ Kalibrasyon düzeltilmeli! Hata %5'in üstünde.")

    def _donus_sonuclari_goster(self, sonuclar: Dict):
        """Dönüş kalibrasyon sonuçlarını göster"""
        print("\n" + "=" * 60)
        print("🔄 DÖNÜŞ KALİBRASYON SONUÇLARI")
        print("=" * 60)
        print(f"📐 Fiziksel Açı: {sonuclar['fiziksel_aci']:.1f}°")
        print(f"🔢 Sol Encoder Pulse: {sonuclar['sol_pulse_fark']}")
        print(f"🔢 Sağ Encoder Pulse: {sonuclar['sag_pulse_fark']}")
        print(f"📏 Sol Mesafe: {sonuclar['sol_mesafe']:.3f} m")
        print(f"📏 Sağ Mesafe: {sonuclar['sag_mesafe']:.3f} m")
        print(f"📐 Mevcut Tekerlek Base: {sonuclar['mevcut_tekerlek_base']:.3f} m")
        print(f"📐 Gerçek Tekerlek Base: {sonuclar['gercek_tekerlek_base']:.3f} m")
        print(f"⚠️  Hata: {sonuclar['hata_yuzdesi']:.1f}%")
        print(f"🔧 Kalibrasyon Faktörü: {sonuclar['kalibrasyon_faktoru']:.3f}")
        print("=" * 60)

        # Tavsiye
        if abs(sonuclar['hata_yuzdesi']) < 2:
            print("✅ Dönüş kalibrasyonu çok iyi! Hata %2'nin altında.")
        elif abs(sonuclar['hata_yuzdesi']) < 5:
            print("⚠️  Dönüş kalibrasyonu kabul edilebilir. Hata %5'in altında.")
        else:
            print("❌ Dönüş kalibrasyonu düzeltilmeli! Hata %5'in üstünde.")

    async def konfigurasyonu_guncelle(self):
        """Kalibrasyon sonuçlarını config dosyasına yaz"""
        if not self.kalibrasyon_sonuclari:
            print("⚠️  Önce kalibrasyon yapmanız gerekiyor!")
            return

        print("\n🔧 Konfigürasyon güncelleniyor...")

        # Backup al
        backup_path = self.config_path + ".backup"
        import shutil
        shutil.copy2(self.config_path, backup_path)
        print(f"📋 Backup alındı: {backup_path}")

        # Config yükle
        with open(self.config_path, 'r') as f:
            config_data = yaml.safe_load(f)

        # Yeni değerleri uygula
        sonuclar = self.kalibrasyon_sonuclari

        # Tekerlek çapını güncelle
        if 'yeni_tekerlek_capi' in sonuclar:
            config_data['navigation']['wheel_diameter'] = sonuclar['yeni_tekerlek_capi']
            print(f"✅ Tekerlek çapı güncellendi: {sonuclar['yeni_tekerlek_capi']:.3f}m")

        # Config dosyasını kaydet
        with open(self.config_path, 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)

        print("✅ Konfigürasyon güncellendi!")

    async def dogrulama_testi(self, test_mesafe: float = 0.5):
        """Kalibrasyon doğrulama testi"""
        print(f"\n🧪 Doğrulama testi başlıyor: {test_mesafe}m")

        # Encoder sayaçlarını sıfırla
        await self._encoder_sayaclarini_sifirla()

        # Başlangıç encoder değerleri
        baslangic_encoders = await self._encoder_degerlerini_oku()

        # Hareket et
        hareket = HareketKomut(
            linear_hiz=0.2,
            angular_hiz=0.0,
            sure=test_mesafe / 0.2
        )

        await self.motor_kontrolcu.hareket_uygula(hareket)
        await asyncio.sleep(0.5)

        # Bitiş encoder değerleri
        bitis_encoders = await self._encoder_degerlerini_oku()

        # Fiziksel mesafe ölç
        fiziksel_mesafe = float(input("Fiziksel mesafeyi ölçün (m): "))

        # Hesaplanan mesafe
        pulse_fark = (bitis_encoders["sol"] - baslangic_encoders["sol"] +
                      bitis_encoders["sag"] - baslangic_encoders["sag"]) / 2

        # Kalibre edilmiş değerleri kullan
        tekerlek_capi = self.navigation_config.get("wheel_diameter", 0.065)
        pulse_per_rev = self.encoder_config.get("sol_encoder", {}).get("pulses_per_revolution", 360)

        hesaplanan_mesafe = pulse_fark * (3.14159 * tekerlek_capi / pulse_per_rev)

        # Hata hesaplama
        hata = abs(hesaplanan_mesafe - fiziksel_mesafe)
        hata_yuzdesi = (hata / fiziksel_mesafe) * 100

        print("\n📊 DOĞRULAMA SONUÇLARI")
        print(f"📏 Fiziksel Mesafe: {fiziksel_mesafe:.3f}m")
        print(f"🧮 Hesaplanan Mesafe: {hesaplanan_mesafe:.3f}m")
        print(f"⚠️  Hata: {hata:.3f}m ({hata_yuzdesi:.1f}%)")

        if hata_yuzdesi < 2:
            print("✅ Doğrulama başarılı! Kalibrasyon çok iyi.")
        elif hata_yuzdesi < 5:
            print("⚠️  Doğrulama kabul edilebilir. Kalibrasyon yeterli.")
        else:
            print("❌ Doğrulama başarısız! Kalibrasyon tekrar edilmeli.")

        return hata_yuzdesi < 5


async def interaktif_kalibrasyon():
    """İnteraktif kalibrasyon süreci"""
    print("🔧 Hacı Abi'nin Encoder Kalibrasyon Aracı")
    print("=" * 50)

    kalibrator = EncoderKalibrator()

    try:
        # Sistemi başlat
        if not await kalibrator.baslat():
            print("❌ Sistem başlatılamadı!")
            return

        while True:
            print("\n📋 Kalibrasyon Menüsü:")
            print("1. Mesafe Kalibrasyonu")
            print("2. Dönüş Kalibrasyonu")
            print("3. Konfigürasyon Güncelle")
            print("4. Doğrulama Testi")
            print("5. Çıkış")

            secim = input("\nSeçiminiz (1-5): ").strip()

            if secim == "1":
                mesafe = float(input("Kalibrasyon mesafesi (m) [1.0]: ") or "1.0")
                await kalibrator.mesafe_kalibrasyonu(mesafe)

            elif secim == "2":
                aci = float(input("Kalibrasyon açısı (°) [90]: ") or "90")
                await kalibrator.donus_kalibrasyonu(aci)

            elif secim == "3":
                await kalibrator.konfigurasyonu_guncelle()

            elif secim == "4":
                mesafe = float(input("Test mesafesi (m) [0.5]: ") or "0.5")
                await kalibrator.dogrulama_testi(mesafe)

            elif secim == "5":
                print("👋 Görüşürüz!")
                break

            else:
                print("❌ Geçersiz seçim!")

    except KeyboardInterrupt:
        print("\n⏹️  Kalibrasyon iptal edildi.")

    finally:
        await kalibrator.kapat()


def main():
    """Ana fonksiyon"""
    parser = argparse.ArgumentParser(description="Encoder Kalibrasyon Aracı")
    parser.add_argument("--distance", type=float, default=1.0, help="Kalibrasyon mesafesi (m)")
    parser.add_argument("--angle", type=float, default=90.0, help="Kalibrasyon açısı (°)")
    parser.add_argument("--test", action="store_true", help="Doğrulama testi yap")
    parser.add_argument("--interactive", action="store_true", help="İnteraktif mod")
    parser.add_argument("--config", type=str, help="Konfigürasyon dosyası yolu")

    args = parser.parse_args()

    # Logging kurulumu
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    if args.interactive:
        asyncio.run(interaktif_kalibrasyon())
    else:
        print("🔧 Basit kalibrasyon modu henüz hazır değil.")
        print("Şimdilik --interactive kullanın!")


if __name__ == "__main__":
    main()
