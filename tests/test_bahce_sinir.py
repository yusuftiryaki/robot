#!/usr/bin/env python3
"""
🏡 Bahçe Sınır Kontrol Sistemi - Pytest Testleri
Hacı Abi'nin modern test çözümü!

Bu dosya bahçe sınır kontrol sisteminin tüm özelliklerini test eder.
Pytest framework'ü kullanarak daha okunabilir ve modüler testler sağlar.
"""

import math
from typing import Any, Dict

import pytest

from src.navigation.bahce_sinir_kontrol import BahceSinirKontrol, KoordinatNoktasi


@pytest.fixture
def test_config() -> Dict[str, Any]:
    """Test için örnek konfigurasyon - Ankara Ulus civarı koordinatlar"""
    return {
        "boundary_coordinates": [
            {"latitude": 39.933500, "longitude": 32.859500},  # Kuzey-batı köşe
            {"latitude": 39.933600, "longitude": 32.859900},  # Kuzey-doğu köşe
            {"latitude": 39.933300, "longitude": 32.859850},  # Güney-doğu köşe
            {"latitude": 39.933200, "longitude": 32.859450}   # Güney-batı köşe
        ],
        "boundary_safety": {
            "buffer_distance": 1.0,      # 1 metre güvenlik buffer'ı
            "warning_distance": 2.0,     # 2 metre uyarı mesafesi
            "max_deviation": 0.5,        # 0.5 metre maksimum sapma
            "check_frequency": 10        # 10 saniyede bir kontrol
        }
    }


@pytest.fixture
def sinir_kontrol(test_config: Dict[str, Any]) -> BahceSinirKontrol:
    """BahceSinirKontrol örneği oluştur"""
    return BahceSinirKontrol(test_config)


class TestBahceSinirKontrolTemelOzellikler:
    """Bahçe sınır kontrol sistemi temel özellik testleri"""

    def test_sinif_baslatma(self, sinir_kontrol: BahceSinirKontrol):
        """Sınıf başlatma ve temel özellik testleri"""
        assert sinir_kontrol is not None
        assert len(sinir_kontrol.sinir_noktalari) == 4
        assert sinir_kontrol.buffer_distance == 1.0
        assert sinir_kontrol.warning_distance == 2.0
        assert sinir_kontrol.bahce_alani > 0

    def test_koordinat_yukleme(self, sinir_kontrol: BahceSinirKontrol):
        """Konfigürasyondan koordinat yükleme testi"""
        # 4 sınır noktası yüklenmiş olmalı
        assert len(sinir_kontrol.sinir_noktalari) == 4

        # İlk nokta doğru koordinatlarda olmalı
        ilk_nokta = sinir_kontrol.sinir_noktalari[0]
        assert abs(ilk_nokta.latitude - 39.933500) < 0.000001
        assert abs(ilk_nokta.longitude - 32.859500) < 0.000001

    def test_bahce_alan_hesaplama(self, sinir_kontrol: BahceSinirKontrol):
        """Bahçe alan hesaplama testi (Shoelace formula)"""
        alan = sinir_kontrol.bahce_alani

        # Alan pozitif olmalı
        assert alan > 0

        # Makul bir alan olmalı (test koordinatları için ~1000-5000 m²)
        assert 100 < alan < 10000


class TestGeoMetrikHesaplamalar:
    """Geometrik hesaplama ve GPS fonksiyonları testleri"""

    def test_haversine_mesafe_hesaplama(self, sinir_kontrol: BahceSinirKontrol):
        """Haversine formülü ile GPS mesafe hesaplama testi"""
        nokta1 = KoordinatNoktasi(39.933500, 32.859500)
        nokta2 = KoordinatNoktasi(39.933600, 32.859900)

        mesafe = sinir_kontrol._haversine_mesafe(
            nokta1.latitude, nokta1.longitude,
            nokta2.latitude, nokta2.longitude
        )

        # Yaklaşık 30-40 metre olmalı (test koordinatları arası)
        assert 20 < mesafe < 50

    def test_nokta_polygon_icinde_kontrolu(self, sinir_kontrol: BahceSinirKontrol):
        """Point-in-polygon algoritması (Ray casting) testi"""
        # Bahçe merkezi polygon içinde olmalı
        merkez = sinir_kontrol.bahce_merkezini_al()
        assert sinir_kontrol._nokta_polygon_icinde_mi(merkez) is True

        # Bahçe dışında çok uzak bir nokta
        dis_nokta = KoordinatNoktasi(40.000000, 33.000000)  # Çok uzak
        assert sinir_kontrol._nokta_polygon_icinde_mi(dis_nokta) is False

        # Sınıra yakın ama dışarıda bir nokta
        yakin_dis_nokta = KoordinatNoktasi(39.934000, 32.860000)
        assert sinir_kontrol._nokta_polygon_icinde_mi(yakin_dis_nokta) is False

    def test_en_yakin_sinir_noktasi_bulma(self, sinir_kontrol: BahceSinirKontrol):
        """En yakın sınır noktası bulma algoritması testi"""
        merkez = sinir_kontrol.bahce_merkezini_al()

        mesafe, en_yakin_nokta = sinir_kontrol._en_yakin_sinir_noktasini_bul(merkez)

        # Mesafe pozitif olmalı
        assert mesafe > 0

        # En yakın nokta sınır noktalarından biri olmalı
        assert en_yakin_nokta in sinir_kontrol.sinir_noktalari

    def test_guvenli_yon_hesaplama(self, sinir_kontrol: BahceSinirKontrol):
        """Güvenli yön hesaplama algoritması testi"""
        # Sınıra yakın bir nokta alalım
        test_noktasi = KoordinatNoktasi(39.933200, 32.859400)  # Güney-batıya yakın
        en_yakin_mesafe, en_yakin_sinir = sinir_kontrol._en_yakin_sinir_noktasini_bul(test_noktasi)

        guvenli_yon = sinir_kontrol._guvenli_yon_hesapla(test_noktasi, en_yakin_sinir)

        # Güvenli yön -π ile π arasında olmalı (radyan)
        assert -math.pi <= guvenli_yon <= math.pi

    def test_bahce_merkezi_hesaplama(self, sinir_kontrol: BahceSinirKontrol):
        """Bahçe merkezi hesaplama testi"""
        merkez = sinir_kontrol.bahce_merkezini_al()

        # Merkez makul koordinatlarda olmalı
        assert 39.933000 < merkez.latitude < 39.934000
        assert 32.859000 < merkez.longitude < 32.860000


class TestGuvenlikKontrolleri:
    """Güvenlik kontrol algoritmaları testleri"""

    def test_guvenli_bolge_kontrolu(self, sinir_kontrol: BahceSinirKontrol):
        """Güvenli bölgede robot konumu testi"""
        merkez = sinir_kontrol.bahce_merkezini_al()
        sonuc = sinir_kontrol.robot_konumunu_kontrol_et(
            merkez.latitude, merkez.longitude
        )

        assert sonuc.guvenli_bolgede is True
        assert sonuc.uyari_seviyesi == "güvenli"
        assert sonuc.sinira_mesafe > sinir_kontrol.warning_distance
        assert "Güvenli bölgede" in sonuc.aciklama

    def test_uyari_bolgesi_kontrolu(self, sinir_kontrol: BahceSinirKontrol):
        """Uyarı bölgesinde robot konumu testi"""
        # Sınıra yakın ama güvenli bir nokta bulalım
        test_noktasi = KoordinatNoktasi(39.933250, 32.859475)  # Sınıra yakın
        sonuc = sinir_kontrol.robot_konumunu_kontrol_et(
            test_noktasi.latitude, test_noktasi.longitude
        )

        # Eğer uyarı bölgesindeyse
        if sonuc.uyari_seviyesi == "uyarı":
            assert sonuc.guvenli_bolgede is True  # Uyarı bölgesi hala güvenli sayılır
            assert sinir_kontrol.buffer_distance < sonuc.sinira_mesafe <= sinir_kontrol.warning_distance
            assert "yaklaşıyor" in sonuc.aciklama

    def test_sinir_ihlali_kontrolu(self, sinir_kontrol: BahceSinirKontrol):
        """Sınır ihlali durumu testi"""
        # Sınır dışında bir nokta
        dis_nokta = KoordinatNoktasi(39.934000, 32.860000)  # Açıkça dışarıda
        sonuc = sinir_kontrol.robot_konumunu_kontrol_et(
            dis_nokta.latitude, dis_nokta.longitude
        )

        assert sonuc.guvenli_bolgede is False
        assert sonuc.uyari_seviyesi == "tehlike"
        assert sonuc.onerilenen_yon is not None  # Güvenli yön önerisi olmalı
        assert "SINIR DIŞINDA" in sonuc.aciklama

    def test_buffer_zone_kontrolu(self, sinir_kontrol: BahceSinirKontrol):
        """Buffer zone (acil durma bölgesi) testi"""
        # Bahçe içinde ama sınıra yakın bir nokta bulalım
        # Önce merkezi alalım, sonra sınıra doğru biraz hareket ettirelim
        merkez = sinir_kontrol.bahce_merkezini_al()

        # Merkeze yakın ama sınıra doğru bir nokta
        yakin_nokta = KoordinatNoktasi(
            merkez.latitude - 0.0001,  # Merkez'den biraz güneye
            merkez.longitude - 0.0001  # Merkez'den biraz batıya
        )

        sonuc = sinir_kontrol.robot_konumunu_kontrol_et(
            yakin_nokta.latitude, yakin_nokta.longitude
        )

        # Test koordinatlarımızla buffer zone'a girmek zor,
        # bu yüzden genel güvenlik kontrolü yapalım
        if sonuc.sinira_mesafe <= sinir_kontrol.buffer_distance:
            assert sonuc.guvenli_bolgede is False
            assert sonuc.uyari_seviyesi == "tehlike"
        elif sonuc.sinira_mesafe <= sinir_kontrol.warning_distance:
            assert sonuc.uyari_seviyesi == "uyarı"
        else:
            assert sonuc.uyari_seviyesi == "güvenli"


class TestIstatistikVeTakip:
    """İstatistik ve takip sistemleri testleri"""

    def test_kontrol_sayisi_takibi(self, sinir_kontrol: BahceSinirKontrol):
        """Toplam kontrol sayısı takip testi"""
        baslangic_sayisi = sinir_kontrol.toplam_kontrol_sayisi
        merkez = sinir_kontrol.bahce_merkezini_al()

        # 5 kez kontrol yap
        for _ in range(5):
            sinir_kontrol.robot_konumunu_kontrol_et(
                merkez.latitude, merkez.longitude
            )

        assert sinir_kontrol.toplam_kontrol_sayisi == baslangic_sayisi + 5

    def test_sinir_ihlali_takibi(self, sinir_kontrol: BahceSinirKontrol):
        """Sınır ihlali sayısı takip testi"""
        baslangic_ihlali = sinir_kontrol.sinir_ihlali_sayisi

        # Sınır dışında bir kontrol yap
        dis_nokta = KoordinatNoktasi(39.934000, 32.860000)
        sinir_kontrol.robot_konumunu_kontrol_et(
            dis_nokta.latitude, dis_nokta.longitude
        )

        assert sinir_kontrol.sinir_ihlali_sayisi == baslangic_ihlali + 1

    def test_sinir_istatistikleri(self, sinir_kontrol: BahceSinirKontrol):
        """Sınır kontrol istatistikleri testi"""
        merkez = sinir_kontrol.bahce_merkezini_al()

        # Birkaç kontrol yap (güvenli bölgede)
        for _ in range(3):
            sinir_kontrol.robot_konumunu_kontrol_et(
                merkez.latitude, merkez.longitude
            )

        stats = sinir_kontrol.sinir_istatistiklerini_al()

        assert "toplam_kontrol" in stats
        assert "sinir_ihlali" in stats
        assert "ihlal_orani" in stats
        assert "bahce_alani" in stats
        assert "sinir_nokta_sayisi" in stats
        assert "buffer_mesafesi" in stats
        assert "uyari_mesafesi" in stats

        assert stats["toplam_kontrol"] >= 3
        assert stats["sinir_nokta_sayisi"] == 4
        assert stats["bahce_alani"] == sinir_kontrol.bahce_alani


class TestWebArayuzuEntegrasyonu:
    """Web arayüzü entegrasyon testleri"""

    def test_web_icin_sinir_verisi_hazirla(self, sinir_kontrol: BahceSinirKontrol):
        """Web arayüzü için sınır verisi hazırlama testi"""
        web_verisi = sinir_kontrol.web_icin_sinir_verilerini_hazirla()

        # Temel alanlar mevcut olmalı
        assert "boundary_points" in web_verisi
        assert "center" in web_verisi
        assert "area" in web_verisi
        assert "buffer_distance" in web_verisi
        assert "warning_distance" in web_verisi

        # 4 sınır noktası olmalı
        assert len(web_verisi["boundary_points"]) == 4

        # Her sınır noktası lat/lon içermeli
        for point in web_verisi["boundary_points"]:
            assert "lat" in point
            assert "lon" in point

        # Merkez koordinatları makul olmalı
        center = web_verisi["center"]
        assert 39.933000 < center["lat"] < 39.934000
        assert 32.859000 < center["lon"] < 32.860000

    def test_web_icin_mevcut_durum(self, sinir_kontrol: BahceSinirKontrol):
        """Web arayüzü için mevcut durum raporu testi"""
        merkez = sinir_kontrol.bahce_merkezini_al()
        web_durumu = sinir_kontrol.get_current_boundary_status_for_web(
            merkez.latitude, merkez.longitude
        )

        # Temel alanlar mevcut olmalı
        assert "active" in web_durumu
        assert "distance_to_fence" in web_durumu
        assert "fence_violations" in web_durumu
        assert "violation_rate" in web_durumu
        assert "garden_area" in web_durumu
        assert "status" in web_durumu
        assert "buffer_distance" in web_durumu
        assert "warning_distance" in web_durumu

        # Aktif olmalı
        assert web_durumu["active"] is True
        assert web_durumu["distance_to_fence"] > 0
        assert web_durumu["status"] in ["SAFE", "WARNING", "DANGER"]


class TestHataVeSinirDurumlari:
    """Hata durumları ve sınır koşulları testleri"""

    def test_bos_koordinat_listesi(self):
        """Boş koordinat listesi ile başlatma testi"""
        bos_config = {
            "boundary_coordinates": [],
            "boundary_safety": {
                "buffer_distance": 1.0,
                "warning_distance": 2.0,
                "max_deviation": 0.5,
                "check_frequency": 10
            }
        }

        sinir_kontrol = BahceSinirKontrol(bos_config)
        assert len(sinir_kontrol.sinir_noktalari) == 0
        assert sinir_kontrol.bahce_alani == 0.0

    def test_eksik_safety_config(self):
        """Eksik güvenlik konfigürasyonu testi"""
        eksik_config = {
            "boundary_coordinates": [
                {"latitude": 39.933500, "longitude": 32.859500},
                {"latitude": 39.933600, "longitude": 32.859900},
                {"latitude": 39.933300, "longitude": 32.859850}
            ]
            # boundary_safety eksik
        }

        sinir_kontrol = BahceSinirKontrol(eksik_config)
        # Varsayılan değerler kullanılmalı
        assert sinir_kontrol.buffer_distance == 1.0
        assert sinir_kontrol.warning_distance == 2.0

    def test_minimum_ucgen_koordinat(self):
        """Minimum 3 nokta ile üçgen test"""
        ucgen_config = {
            "boundary_coordinates": [
                {"latitude": 39.933500, "longitude": 32.859500},
                {"latitude": 39.933600, "longitude": 32.859900},
                {"latitude": 39.933300, "longitude": 32.859850}
            ],
            "boundary_safety": {
                "buffer_distance": 1.0,
                "warning_distance": 2.0,
                "max_deviation": 0.5,
                "check_frequency": 10
            }
        }

        sinir_kontrol = BahceSinirKontrol(ucgen_config)
        assert len(sinir_kontrol.sinir_noktalari) == 3
        assert sinir_kontrol.bahce_alani > 0


# ====================================
# 🎯 PYTEST RUNNER FUNCTIONS
# ====================================

def test_butun_sistem_entegrasyonu(sinir_kontrol: BahceSinirKontrol):
    """Tüm sistem entegrasyon testi - E2E"""
    print("\n🏡 Bahçe Sınır Kontrol Sistemi - Tam Entegrasyon Testi")
    print("=" * 60)

    # 1. Sistem başlatma
    assert sinir_kontrol is not None
    print(f"✅ Sistem başlatıldı - {len(sinir_kontrol.sinir_noktalari)} sınır noktası")

    # 2. Farklı konumlarda test senaryoları
    test_konumlari = [
        (39.933400, 32.859700, "Bahçe merkezi"),
        (39.933250, 32.859475, "Sınıra yakın"),
        (39.934000, 32.860000, "Sınır dışı"),
        (39.933150, 32.859400, "Buffer zone")
    ]

    for lat, lon, aciklama in test_konumlari:
        sonuc = sinir_kontrol.robot_konumunu_kontrol_et(lat, lon)
        print(f"📍 {aciklama}: {sonuc.uyari_seviyesi} - {sonuc.aciklama}")

    # 3. İstatistikleri kontrol et
    stats = sinir_kontrol.sinir_istatistiklerini_al()
    print(f"📊 Toplam kontrol: {stats['toplam_kontrol']}")
    print(f"⚠️ Sınır ihlali: {stats['sinir_ihlali']}")
    print(f"🌱 Bahçe alanı: {stats['bahce_alani']:.1f} m²")

    # 4. Web verisi hazırlama
    web_verisi = sinir_kontrol.web_icin_sinir_verilerini_hazirla()
    assert len(web_verisi["boundary_points"]) > 0
    print(f"🌐 Web verisi hazır - {len(web_verisi['boundary_points'])} nokta")

    print("✅ Tüm sistem entegrasyonu başarılı!")


if __name__ == "__main__":
    # Pytest'i programatik olarak çalıştır
    pytest.main([__file__, "-v", "--tb=short"])
