#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📷 Kamera Kalibrasyon Scripti - AprilTag İçin Optimize
Hacı Abi'nin kamera kalibrasyon sistemi!

Bu script robot kamerasını AprilTag detection için kalibre eder.
Camera matrix ve distortion coefficients hesaplar.
"""

import argparse
import glob
import os
import pickle
from typing import List, Optional, Tuple

import cv2
import numpy as np


class KameraKalibratoru:
    """📷 Kamera kalibrasyon sınıfı"""

    def __init__(self, satranc_boyutu: Tuple[int, int] = (9, 6)):
        """
        Args:
            satranc_boyutu: Kalibrasyon tahtası boyutu (köşe sayısı)
        """
        self.satranc_boyutu = satranc_boyutu
        self.kare_boyutu = 0.025  # 2.5cm kareler

        # Kalibrasyon parametreleri
        self.criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

        # 3D noktalar (gerçek dünya koordinatları)
        self.objp = np.zeros((satranc_boyutu[0] * satranc_boyutu[1], 3), np.float32)
        self.objp[:, :2] = np.mgrid[0:satranc_boyutu[0], 0:satranc_boyutu[1]].T.reshape(-1, 2)
        self.objp *= self.kare_boyutu

        # Tespit edilen noktaları sakla
        self.objpoints = []  # 3D noktalar
        self.imgpoints = []  # 2D noktalar

    def kalibrasyon_goruntusu_topla(self, kaynak: str = "kamera",
                                    kaydet_klasoru: str = "kalibrasyon_goruntuleri") -> int:
        """
        Kalibrasyon için görüntü topla

        Args:
            kaynak: "kamera" veya "dosya"
            kaydet_klasoru: Görüntülerin kaydedileceği klasör

        Returns:
            Toplanan görüntü sayısı
        """
        os.makedirs(kaydet_klasoru, exist_ok=True)

        if kaynak == "kamera":
            return self._kameradan_goruntu_topla(kaydet_klasoru)
        else:
            return self._dosyadan_goruntu_topla(kaydet_klasoru)

    def _kameradan_goruntu_topla(self, kaydet_klasoru: str) -> int:
        """Kameradan canlı görüntü topla"""
        print("📷 Kamera kalibrasyon görüntü toplama")
        print("📋 KULLANIM:")
        print("  - SPACE: Görüntü kaydet")
        print("  - ESC: Çıkış")
        print("  - En az 20 farklı açıdan görüntü alın")

        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ Kamera açılamadı!")
            return 0

        # Kamera ayarları
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 15)

        görüntü_sayısı = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Satranç tahtası köşelerini bul
            ret_corners, corners = cv2.findChessboardCorners(gray, self.satranc_boyutu, None)

            # Görüntüye çiz
            display_frame = frame.copy()
            if ret_corners:
                cv2.drawChessboardCorners(display_frame, self.satranc_boyutu, corners, ret_corners)
                cv2.putText(display_frame, "SATRANC TAHTASI BULUNDU - SPACE'e basin",
                            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            else:
                cv2.putText(display_frame, "Satranc tahtasini hareket ettirin",
                            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

            cv2.putText(display_frame, f"Toplanan: {görüntü_sayısı}/20",
                        (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

            cv2.imshow('Kamera Kalibrasyon', display_frame)

            key = cv2.waitKey(1) & 0xFF

            if key == 27:  # ESC
                break
            elif key == ord(' ') and ret_corners:  # SPACE
                # Görüntüyü kaydet
                dosya_adi = os.path.join(kaydet_klasoru, f"kalibrasyon_{görüntü_sayısı:03d}.jpg")
                cv2.imwrite(dosya_adi, frame)
                görüntü_sayısı += 1
                print(f"✅ Görüntü kaydedildi: {dosya_adi}")

                if görüntü_sayısı >= 20:
                    print("🎉 Yeterli görüntü toplandı!")
                    break

        cap.release()
        cv2.destroyAllWindows()

        return görüntü_sayısı

    def _dosyadan_goruntu_topla(self, kaydet_klasoru: str) -> int:
        """Mevcut dosyalardan görüntü topla"""
        pattern = os.path.join(kaydet_klasoru, "*.jpg")
        images = glob.glob(pattern)
        return len(images)

    def kalibrasyon_yap(self, goruntu_klasoru: str = "kalibrasyon_goruntuleri") -> Optional[dict]:
        """
        Kamera kalibrasyonu yap

        Args:
            goruntu_klasoru: Kalibrasyon görüntülerinin olduğu klasör

        Returns:
            Kalibrasyon sonuçları (dict)
        """
        print("🔧 Kamera kalibrasyon işlemi başlıyor...")

        # Görüntüleri yükle
        pattern = os.path.join(goruntu_klasoru, "*.jpg")
        images = glob.glob(pattern)

        if len(images) < 10:
            print(f"❌ Yetersiz görüntü! Bulunan: {len(images)}, Minimum: 10")
            return None

        print(f"📁 {len(images)} kalibrasyon görüntüsü bulundu")

        self.objpoints = []
        self.imgpoints = []

        başarılı_görüntü = 0

        for image_path in images:
            img = cv2.imread(image_path)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Satranç tahtası köşelerini bul
            ret, corners = cv2.findChessboardCorners(gray, self.satranc_boyutu, None)

            if ret:
                # 3D ve 2D noktaları ekle
                self.objpoints.append(self.objp)

                # Köşe konumlarını hassaslaştır
                corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), self.criteria)
                self.imgpoints.append(corners2)

                başarılı_görüntü += 1
                print(f"✅ İşlendi: {os.path.basename(image_path)}")
            else:
                print(f"❌ Başarısız: {os.path.basename(image_path)}")

        if başarılı_görüntü < 10:
            print(f"❌ Yetersiz başarılı görüntü! Başarılı: {başarılı_görüntü}, Minimum: 10")
            return None

        print(f"🎯 {başarılı_görüntü} görüntü ile kalibrasyon yapılıyor...")

        # Kalibrasyon hesapla
        img_shape = gray.shape[::-1]
        ret, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
            self.objpoints, self.imgpoints, img_shape, None, None
        )

        if not ret:
            print("❌ Kalibrasyon başarısız!")
            return None

        # Kalibrasyon hatası hesapla
        mean_error = self._kalibrasyon_hatasi_hesapla(camera_matrix, dist_coeffs, rvecs, tvecs)

        # Sonuçları hazırla
        kalibrasyon_sonucu = {
            "camera_matrix": camera_matrix.tolist(),
            "distortion_coefficients": dist_coeffs.tolist(),
            "image_size": img_shape,
            "calibration_error": mean_error,
            "successful_images": başarılı_görüntü,
            "total_images": len(images)
        }

        print(f"✅ Kalibrasyon tamamlandı!")
        print(f"📊 Ortalama hata: {mean_error:.3f} piksel")
        print(f"📷 Görüntü boyutu: {img_shape}")

        return kalibrasyon_sonucu

    def _kalibrasyon_hatasi_hesapla(self, camera_matrix, dist_coeffs, rvecs, tvecs) -> float:
        """Kalibrasyon hatasını hesapla"""
        total_error = 0
        total_points = 0

        for i in range(len(self.objpoints)):
            imgpoints2, _ = cv2.projectPoints(
                self.objpoints[i], rvecs[i], tvecs[i], camera_matrix, dist_coeffs
            )
            error = cv2.norm(self.imgpoints[i], imgpoints2, cv2.NORM_L2) / len(imgpoints2)
            total_error += error
            total_points += 1

        return total_error / total_points

    def sonuclari_kaydet(self, kalibrasyon_sonucu: dict, dosya_adi: str = "kamera_kalibrasyon.pkl"):
        """Kalibrasyon sonuçlarını kaydet"""
        try:
            with open(dosya_adi, 'wb') as f:
                pickle.dump(kalibrasyon_sonucu, f)
            print(f"💾 Kalibrasyon sonuçları kaydedildi: {dosya_adi}")

            # YAML formatında da kaydet
            yaml_dosya = dosya_adi.replace('.pkl', '.yaml')
            self._yaml_formatinda_kaydet(kalibrasyon_sonucu, yaml_dosya)

        except Exception as e:
            print(f"❌ Kaydetme hatası: {e}")

    def _yaml_formatinda_kaydet(self, kalibrasyon_sonucu: dict, dosya_adi: str):
        """YAML formatında robot config için kaydet"""
        try:
            with open(dosya_adi, 'w') as f:
                f.write("# Kamera Kalibrasyon Sonuçları\n")
                f.write("# Bu değerleri robot_config.yaml dosyasına kopyalayın\n\n")
                f.write("apriltag:\n")
                f.write("  kamera_matrix:\n")

                camera_matrix = kalibrasyon_sonucu["camera_matrix"]
                for row in camera_matrix:
                    f.write(f"    - {row}\n")

                f.write("  distortion_coeffs: ")
                f.write(f"{kalibrasyon_sonucu['distortion_coefficients']}\n")

                f.write(f"\n# Kalibrasyon Bilgileri:\n")
                f.write(f"# Ortalama hata: {kalibrasyon_sonucu['calibration_error']:.3f} piksel\n")
                f.write(f"# Başarılı görüntü: {kalibrasyon_sonucu['successful_images']}\n")
                f.write(f"# Görüntü boyutu: {kalibrasyon_sonucu['image_size']}\n")

            print(f"📝 YAML formatı kaydedildi: {dosya_adi}")

        except Exception as e:
            print(f"❌ YAML kaydetme hatası: {e}")

    def apriltag_test_et(self, kalibrasyon_sonucu: dict):
        """Kalibrasyon sonucunu AprilTag ile test et"""
        print("🏷️ AprilTag tespit testi başlıyor...")

        camera_matrix = np.array(kalibrasyon_sonucu["camera_matrix"], dtype=np.float32)
        dist_coeffs = np.array(kalibrasyon_sonucu["distortion_coefficients"], dtype=np.float32)

        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ Kamera açılamadı!")
            return

        # ArUco detector
        aruco_dict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_APRILTAG_36h11)
        detector_params = cv2.aruco.DetectorParameters_create()

        print("📋 KULLANIM:")
        print("  - ESC: Çıkış")
        print("  - AprilTag (ID: 0-10) gösterin")

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # AprilTag tespit et
            corners, ids, _ = cv2.aruco.detectMarkers(gray, aruco_dict, parameters=detector_params)

            if ids is not None:
                # Tag'leri çiz
                cv2.aruco.drawDetectedMarkers(frame, corners, ids)

                # Pose estimation
                for i, corner in enumerate(corners):
                    tag_size = 0.15  # 15cm
                    tag_points = np.array([
                        [-tag_size / 2, -tag_size / 2, 0],
                        [tag_size / 2, -tag_size / 2, 0],
                        [tag_size / 2, tag_size / 2, 0],
                        [-tag_size / 2, tag_size / 2, 0]
                    ], dtype=np.float32)

                    success, rvec, tvec = cv2.solvePnP(
                        tag_points, corner, camera_matrix, dist_coeffs
                    )

                    if success:
                        # 3D eksen çiz
                        cv2.aruco.drawAxis(frame, camera_matrix, dist_coeffs, rvec, tvec, 0.1)

                        # Mesafe ve açı bilgisi
                        distance = np.linalg.norm(tvec)
                        angle = np.degrees(np.arctan2(tvec[0][0], tvec[2][0]))

                        cv2.putText(frame, f"ID:{ids[i][0]} D:{distance:.2f}m A:{angle:.1f}°",
                                    (int(corner[0][0][0]), int(corner[0][0][1]) - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            cv2.imshow('AprilTag Test', frame)

            if cv2.waitKey(1) & 0xFF == 27:  # ESC
                break

        cap.release()
        cv2.destroyAllWindows()


def main():
    """Ana fonksiyon"""
    parser = argparse.ArgumentParser(description="Kamera kalibrasyon scripti")
    parser.add_argument("--topla", action="store_true", help="Kalibrasyon görüntülerini topla")
    parser.add_argument("--kalibrasyon", action="store_true", help="Kalibrasyonu yap")
    parser.add_argument("--test", action="store_true", help="AprilTag testi yap")
    parser.add_argument("--tam", action="store_true", help="Tam işlem (topla + kalibrasyon + test)")
    parser.add_argument("--klasor", default="kalibrasyon_goruntuleri", help="Görüntü klasörü")

    args = parser.parse_args()

    print("📷 Hacı Abi'nin Kamera Kalibrasyon Scripti")
    print("=" * 50)

    kalibrator = KameraKalibratoru()

    if args.tam or args.topla:
        print("\n🔍 AŞAMA 1: Kalibrasyon görüntülerini toplama")
        görüntü_sayısı = kalibrator.kalibrasyon_goruntusu_topla("kamera", args.klasor)

        if görüntü_sayısı < 10:
            print("❌ Yetersiz görüntü toplandı!")
            return

    if args.tam or args.kalibrasyon:
        print("\n🔧 AŞAMA 2: Kamera kalibrasyonu")
        kalibrasyon_sonucu = kalibrator.kalibrasyon_yap(args.klasor)

        if kalibrasyon_sonucu is None:
            print("❌ Kalibrasyon başarısız!")
            return

        # Sonuçları kaydet
        kalibrator.sonuclari_kaydet(kalibrasyon_sonucu)

    if args.tam or args.test:
        print("\n🏷️ AŞAMA 3: AprilTag testi")

        # Kalibrasyon sonucunu yükle
        try:
            with open("kamera_kalibrasyon.pkl", 'rb') as f:
                kalibrasyon_sonucu = pickle.load(f)

            kalibrator.apriltag_test_et(kalibrasyon_sonucu)

        except FileNotFoundError:
            print("❌ Kalibrasyon dosyası bulunamadı! Önce kalibrasyonu yapın.")

    print("\n✅ İşlem tamamlandı!")
    print("\n📝 SONRAKİ ADIMLAR:")
    print("1. kamera_kalibrasyon.yaml dosyasını inceleyin")
    print("2. Değerleri config/robot_config.yaml dosyasına kopyalayın")
    print("3. AprilTag test sistemi ile doğrulayın")


if __name__ == "__main__":
    main()
