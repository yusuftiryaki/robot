#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🏷️ AprilTag Generator - Şarj İstasyonu Etiketleri
Hacı Abi'nin AprilTag üretim scripti!

Bu script şarj istasyonu için AprilTag etiketleri oluşturur.
Farklı boyutlarda ve formatlarında basım için hazır dosyalar üretir.
"""

import argparse
import os
from typing import List, Tuple

import cv2
import numpy as np


class AprilTagUretici:
    """🏷️ AprilTag üretici sınıfı"""

    def __init__(self):
        # OpenCV sürüm uyumluluğu
        try:
            # OpenCV 4.7+ için yeni API
            self.aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_APRILTAG_36h11)
        except AttributeError:
            # OpenCV 4.6 ve öncesi için eski API
            self.aruco_dict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_APRILTAG_36h11)

        self.tag_boyutlari = {
            "kucuk": 944,     # 8cm için 944px (300 DPI)
            "orta": 1771,     # 15cm için 1771px (300 DPI)
            "buyuk": 2362,    # 20cm için 2362px (300 DPI)
            "extra": 3543     # 30cm için 3543px (300 DPI)
        }

    def tek_tag_uret(self, tag_id: int, boyut: str = "orta", dosya_adi: str = None) -> str:
        """
        Tek bir AprilTag üret

        Args:
            tag_id: Tag ID numarası
            boyut: Tag boyutu (kucuk, orta, buyuk, extra)
            dosya_adi: Özel dosya adı (opsiyonel)

        Returns:
            str: Oluşturulan dosya yolu
        """
        pixel_boyutu = self.tag_boyutlari.get(boyut, 150)

        # AprilTag görüntüsü üret
        try:
            # OpenCV 4.7+ için yeni API
            tag_image = cv2.aruco.generateImageMarker(self.aruco_dict, tag_id, pixel_boyutu)
        except AttributeError:
            # OpenCV 4.6 ve öncesi için eski API
            tag_image = cv2.aruco.drawMarker(self.aruco_dict, tag_id, pixel_boyutu)

        # Kenar boşluğu ekle (beyaz alan)
        margin = pixel_boyutu // 10  # %10 kenar boşluğu
        bordered_image = cv2.copyMakeBorder(
            tag_image, margin, margin, margin, margin,
            cv2.BORDER_CONSTANT, value=[255, 255, 255]
        )

        # Dosya adı belirle
        if dosya_adi is None:
            dosya_adi = f"apriltag_{tag_id:03d}_{boyut}.png"

        # Dosyayı kaydet
        os.makedirs("generated_tags", exist_ok=True)
        dosya_yolu = os.path.join("generated_tags", dosya_adi)
        cv2.imwrite(dosya_yolu, bordered_image)

        print(f"✅ AprilTag üretildi: {dosya_yolu}")
        return dosya_yolu

    def set_uret(self, tag_ids: List[int], boyut: str = "orta") -> List[str]:
        """
        Birden fazla AprilTag üret

        Args:
            tag_ids: Tag ID listesi
            boyut: Tag boyutu

        Returns:
            List[str]: Oluşturulan dosya yolları
        """
        dosya_yollari = []

        for tag_id in tag_ids:
            dosya_yolu = self.tek_tag_uret(tag_id, boyut)
            dosya_yollari.append(dosya_yolu)

        return dosya_yollari

    def basim_sayfasi_uret(self, tag_ids: List[int], boyut: str = "orta",
                           sayfa_boyutu: Tuple[int, int] = (2480, 3508),
                           geometrik_yerlesim: bool = False) -> str:
        """
        Basım için sayfa düzeni oluştur

        Args:
            tag_ids: Tag ID listesi
            boyut: Tag boyutu
            sayfa_boyutu: Sayfa boyutu (A4: 2480x3508, A3: 3508x4961 px at 300dpi)
            geometrik_yerlesim: Şarj istasyonu geometrik yerleşimi kullan

        Returns:
            str: Oluşturulan basım dosyası yolu
        """
        pixel_boyutu = self.tag_boyutlari.get(boyut, 150)
        margin = pixel_boyutu // 10
        tag_toplam_boyut = pixel_boyutu + 2 * margin

        # Sayfa boyutları
        sayfa_genislik, sayfa_yukseklik = sayfa_boyutu

        # Geometrik yerleşim varsa özel hesaplama
        if geometrik_yerlesim and len(tag_ids) == 3:
            return self._geometrik_basim_sayfasi_uret(tag_ids, boyut, sayfa_boyutu)

        # Sayfa kenar boşlukları
        sayfa_margin = 100
        kullanilabilir_genislik = sayfa_genislik - 2 * sayfa_margin
        kullanilabilir_yukseklik = sayfa_yukseklik - 2 * sayfa_margin

        # Kaç tag sığar hesapla
        tags_per_row = kullanilabilir_genislik // tag_toplam_boyut
        tags_per_col = kullanilabilir_yukseklik // tag_toplam_boyut

        # Beyaz sayfa oluştur
        sayfa = np.full((sayfa_yukseklik, sayfa_genislik), 255, dtype=np.uint8)

        # Tag'leri yerleştir
        for i, tag_id in enumerate(tag_ids):
            row = i // tags_per_row
            col = i % tags_per_row

            # Sayfa sınırlarını kontrol et
            if row >= tags_per_col:
                print(f"⚠️ Sayfa dolu! {i} tag'den sonra duruluyor.")
                break

            # Tag konumunu hesapla
            x = sayfa_margin + col * tag_toplam_boyut
            y = sayfa_margin + row * tag_toplam_boyut

            # Tag üret
            try:
                # OpenCV 4.7+ için yeni API
                tag_image = cv2.aruco.generateImageMarker(self.aruco_dict, tag_id, pixel_boyutu)
            except AttributeError:
                # OpenCV 4.6 ve öncesi için eski API
                tag_image = cv2.aruco.drawMarker(self.aruco_dict, tag_id, pixel_boyutu)
            bordered_tag = cv2.copyMakeBorder(
                tag_image, margin, margin, margin, margin,
                cv2.BORDER_CONSTANT, value=[255, 255, 255]
            )

            # Tag'i sayfaya yerleştir
            sayfa[y:y + tag_toplam_boyut, x:x + tag_toplam_boyut] = bordered_tag

            # Tag bilgisini ekle
            cv2.putText(sayfa, f"ID: {tag_id}", (x, y + tag_toplam_boyut + 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, 0, 1)

        # Dosya adı ve kaydet
        dosya_adi = f"apriltag_basim_sayfasi_{boyut}.png"
        dosya_yolu = os.path.join("generated_tags", dosya_adi)
        cv2.imwrite(dosya_yolu, sayfa)

        print(f"✅ Basım sayfası oluşturuldu: {dosya_yolu}")
        print(f"📄 Sayfa boyutu: {sayfa_genislik}x{sayfa_yukseklik}")
        print(f"🏷️ Tag boyutu: {tag_toplam_boyut}x{tag_toplam_boyut}")
        print(f"📊 Yerleştirilen tag sayısı: {min(len(tag_ids), tags_per_row * tags_per_col)}")

        return dosya_yolu

    def _geometrik_basim_sayfasi_uret(self, tag_ids: List[int], boyut: str = "orta",
                                      sayfa_boyutu: Tuple[int, int] = (3508, 4961)) -> str:
        """
        Şarj istasyonu geometrik yerleşim ile basım sayfası oluştur

        Args:
            tag_ids: Tag ID listesi (3 tag: 0, 1, 2)
            boyut: Tag boyutu
            sayfa_boyutu: Sayfa boyutu (A3: 3508x4961 px at 300dpi)

        Returns:
            str: Oluşturulan basım dosyası yolu
        """
        pixel_boyutu = self.tag_boyutlari.get(boyut, 100)  # küçük=100px=8cm
        margin = pixel_boyutu // 10
        tag_toplam_boyut = pixel_boyutu + 2 * margin

        # Sayfa boyutları
        sayfa_genislik, sayfa_yukseklik = sayfa_boyutu

        # Beyaz sayfa oluştur
        sayfa = np.full((sayfa_yukseklik, sayfa_genislik), 255, dtype=np.uint8)

        # A3 için optimum geometri
        # 300 DPI'da: 8cm = 94.5px, 9.3cm = 110px
        tag_mesafesi_cm = 9.3  # 9.3 cm
        tag_mesafesi_px = int(tag_mesafesi_cm * 300 / 2.54)  # cm'yi pixel'e çevir (300 DPI)

        # Sayfa merkezini hesapla
        merkez_x = sayfa_genislik // 2
        merkez_y = sayfa_yukseklik // 2

        # Tag konumları (şarj istasyonu geometrisi)
        tag_konumlari = {
            0: (merkez_x, merkez_y + tag_mesafesi_px // 2),           # Ana tag (alt merkez)
            1: (merkez_x - tag_mesafesi_px, merkez_y - tag_mesafesi_px // 2),  # Sol üst
            2: (merkez_x + tag_mesafesi_px, merkez_y - tag_mesafesi_px // 2),  # Sağ üst
        }

        # Tag'leri yerleştir
        for tag_id in tag_ids:
            if tag_id in tag_konumlari:
                x, y = tag_konumlari[tag_id]

                # Tag konumunu düzelt (sol üst köşe)
                x -= tag_toplam_boyut // 2
                y -= tag_toplam_boyut // 2

                # Tag üret
                try:
                    tag_image = cv2.aruco.generateImageMarker(self.aruco_dict, tag_id, pixel_boyutu)
                except AttributeError:
                    tag_image = cv2.aruco.drawMarker(self.aruco_dict, tag_id, pixel_boyutu)

                bordered_tag = cv2.copyMakeBorder(
                    tag_image, margin, margin, margin, margin,
                    cv2.BORDER_CONSTANT, value=[255, 255, 255]
                )

                # Tag'i sayfaya yerleştir
                sayfa[y:y + tag_toplam_boyut, x:x + tag_toplam_boyut] = bordered_tag

                # Tag bilgisini ekle
                cv2.putText(sayfa, f"ID: {tag_id}", (x, y + tag_toplam_boyut + 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)

        # Geometrik bilgileri ekle
        cv2.putText(sayfa, "Sarj Istasyonu AprilTag Geometrisi", (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
        cv2.putText(sayfa, f"Tag Boyutu: {pixel_boyutu}px = 8cm", (50, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
        cv2.putText(sayfa, f"Tag Mesafesi: {tag_mesafesi_px}px = 9.3cm", (50, 130),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)

        # Dosya adı ve kaydet
        dosya_adi = f"apriltag_sarj_geometrik_{boyut}_A3.png"
        dosya_yolu = os.path.join("generated_tags", dosya_adi)
        cv2.imwrite(dosya_yolu, sayfa)

        print(f"✅ Geometrik basım sayfası oluşturuldu: {dosya_yolu}")
        print(f"📄 Sayfa boyutu: {sayfa_genislik}x{sayfa_yukseklik} (A3)")
        print(f"🏷️ Tag boyutu: {tag_toplam_boyut}x{tag_toplam_boyut} (8cm)")
        print(f"📐 Tag mesafesi: {tag_mesafesi_px}px (9.3cm)")

        return dosya_yolu

    def sarj_istasyonu_tag_seti_uret(self) -> List[str]:
        """
        Şarj istasyonu için özel tag seti üret

        Returns:
            List[str]: Oluşturulan dosya yolları
        """
        print("🔋 Şarj istasyonu AprilTag seti üretiliyor...")

        # Şarj istasyonu için özel tag'ler
        sarj_tag_ids = [0, 1, 2, 3, 4]  # Ana şarj + yedek tag'ler

        dosya_yollari = []

        # Her boyutta üret
        for boyut in ["kucuk", "orta", "buyuk"]:
            for tag_id in sarj_tag_ids:
                dosya_adi = f"sarj_istasyonu_tag_{tag_id}_{boyut}.png"
                dosya_yolu = self.tek_tag_uret(tag_id, boyut, dosya_adi)
                dosya_yollari.append(dosya_yolu)

        # Basım sayfası da oluştur
        basim_dosyasi = self.basim_sayfasi_uret(sarj_tag_ids, "orta")
        dosya_yollari.append(basim_dosyasi)

        return dosya_yollari


def main():
    """Ana fonksiyon"""
    parser = argparse.ArgumentParser(description="AprilTag üretici - Şarj istasyonu etiketleri")
    parser.add_argument("--tag-id", type=int, default=0, help="Tag ID numarası")
    parser.add_argument("--boyut", choices=["kucuk", "orta", "buyuk", "extra"],
                        default="orta", help="Tag boyutu")
    parser.add_argument("--set", action="store_true", help="Şarj istasyonu tag seti üret")
    parser.add_argument("--basim", action="store_true", help="Basım sayfası oluştur")
    parser.add_argument("--ids", nargs="+", type=int, help="Birden fazla tag ID")
    parser.add_argument("--a3", action="store_true", help="A3 boyutunda basım sayfası")
    parser.add_argument("--geometrik", action="store_true", help="Şarj istasyonu geometrik yerleşim")

    args = parser.parse_args()

    # AprilTag üretici
    uretici = AprilTagUretici()

    print("🏷️ Hacı Abi'nin AprilTag Üretici")
    print("=" * 40)

    if args.set:
        # Şarj istasyonu seti
        dosya_yollari = uretici.sarj_istasyonu_tag_seti_uret()
        print(f"\n✅ Şarj istasyonu tag seti tamamlandı!")
        print(f"📁 Toplam {len(dosya_yollari)} dosya üretildi")

    elif args.basim:
        # Basım sayfası
        if args.ids:
            tag_ids = args.ids
        else:
            tag_ids = [args.tag_id]

        # Sayfa boyutunu belirle
        if args.a3:
            sayfa_boyutu = (3508, 4961)  # A3 at 300dpi
        else:
            sayfa_boyutu = (2480, 3508)  # A4 at 300dpi

        dosya_yolu = uretici.basim_sayfasi_uret(
            tag_ids, args.boyut, sayfa_boyutu, args.geometrik
        )
        print(f"\n✅ Basım sayfası hazır: {dosya_yolu}")

    elif args.ids:
        # Birden fazla tag
        dosya_yollari = uretici.set_uret(args.ids, args.boyut)
        print(f"\n✅ {len(dosya_yollari)} tag üretildi")

    else:
        # Tek tag
        dosya_yolu = uretici.tek_tag_uret(args.tag_id, args.boyut)
        print(f"\n✅ Tag hazır: {dosya_yolu}")

    print("\n📖 KULLANIM ÖRNEKLERİ:")
    print("python scripts/apriltag_generator.py --set  # Şarj istasyonu seti")
    print("python scripts/apriltag_generator.py --tag-id 0 --boyut buyuk  # Tek tag")
    print("python scripts/apriltag_generator.py --ids 0 1 2 --basim --a3 --geometrik  # A3 geometrik")
    print("python scripts/apriltag_generator.py --ids 0 1 2 3 --basim  # A4 basım sayfası")
    print("\n🏷️ Tag boyutları:")
    print("  kucuk: 10cm (100px)")
    print("  orta:  15cm (150px)")
    print("  buyuk: 20cm (200px)")
    print("  extra: 30cm (300px)")


if __name__ == "__main__":
    main()
