# 🎯 AprilTag Şarj İstasyonu Yerleşim Rehberi

## 📋 Gerekli Malzemeler
- 3-4 adet AprilTag (36h11 ailesi, 15cm x 15cm)
- Laminasyon filmi (su geçirmez)
- Güçlü yapıştırıcı veya vida
- Cetvel/mezura
- Seviye ölçer

## 📐 Konumlandırma Detayları

### 🎯 Ana Tag (ID: 0) - Merkez
```
Konum: Şarj konektörünün tam üstü
Yükseklik: Zeminden 25-30cm
Açı: Tam düz (0°)
Boyut: 15cm x 15cm
```

## 🎯 **Küçük Tag'ler ile Tek Sayfa Basım Çözümü**

### � **Önerilen Konfigürasyon: Küçük Tag'ler (10cm)**

```
    [Tag-1]         [Tag-2]
       \               /
        \             /
      25cm \         / 25cm
            \       /
             \     /
        [Tag-0] <- Ana tag
           🔌
```

### 🏷️ **Küçük Tag Avantajları:**
- **Tek sayfa basım**: 3 tag A4 kağıda sığar
- **Maliyet**: Daha az mürekkep/kağıt
- **Kurulum**: Daha az yer kaplar
- **Tespit**: 1.5m mesafeden yeterli

### 📄 **Basım Detayları:**
- **Kağıt**: A4 (210x297mm)
- **Tag boyutu**: 10cm x 10cm
- **Çözünürlük**: 300 DPI
- **Margin**: 2cm kenar boşluğu
- **Yerleşim**: Geometrik olarak optimal
```
Tag-1: Sol üst köşe
- Merkez tag'ten 40cm mesafe
- 45° açıyla konumlandırılmış
- Yükseklik: 35cm

Tag-2: Sağ üst köşe
- Merkez tag'ten 40cm mesafe
- 45° açıyla konumlandırılmış
- Yükseklik: 35cm

Tag-3: Alt merkez (opsiyonel)
- Merkez tag'ten 30cm aşağı
- Tam düz (0°)
- Yükseklik: 15cm
```

## 🛠️ Adım Adım Kurulum

### 1️⃣ Hazırlık
```bash
# AprilTag'leri üret (şarj istasyonu için)
cd /workspaces/oba
python scripts/apriltag_generator.py --ids 0 1 2 3 --boyut orta

# Üretilen dosyalar:
# - generated_tags/apriltag_000_orta.png (Ana tag)
# - generated_tags/apriltag_001_orta.png (Sol üst)
# - generated_tags/apriltag_002_orta.png (Sağ üst)
# - generated_tags/apriltag_003_orta.png (Alt destek)
```

### 2️⃣ Yazdırma
- **Boyut**: Tam 15cm x 15cm (orta boyut)
- **Kalite**: 300 DPI minimum
- **Kağıt**: Mat, parlak olmayan
- **Yazıcı**: Lazer yazıcı tercih edilir

### 3️⃣ Laminasyon
- Su geçirmez laminasyon filmi
- Hava kabarcığı bırakma
- Kenarları 1cm boşluk bırak

### 4️⃣ Yerleştirme
```
Ana Tag (ID: 0):
├── Şarj konektörü üstü
├── Zeminden 25-30cm
├── Robot'un yaklaşacağı yöne bakacak
└── Tam düz (0° eğim)

Yardımcı Tag'ler:
├── Ana tag etrafında 40cm mesafe
├── 45° açıyla eğik
├── Birbirinden eşit mesafede
└── Temiz, düz yüzeylerde
```

## 🔍 Kontrol Listesi

### ✅ Kurulum Sonrası Test
- [ ] Ana tag (ID: 0) kameradan görünüyor
- [ ] En az 2 yardımcı tag görünüyor
- [ ] Tag'ler 2 metreden tespit ediliyor
- [ ] Güneş ışığında okunabiliyor
- [ ] Yağmur/nem direnci test edildi

### ⚠️ Dikkat Edilecekler
- **Gölge**: Tag'lerin üstünde gölge yaratacak nesne yok
- **Yansıma**: Parlak yüzeylerde yansıma yok
- **Temizlik**: Düzenli temizlik yapılacak
- **Açı**: Robot yaklaşım yönünden net görünüyor

## 🎯 Optimizasyon İpuçları

### 📊 Performans Ayarları
```yaml
# config/robot_config.yaml
apriltag:
  tespit_mesafesi: 2.0    # 2 metre
  minimum_tag_boyutu: 100 # piksel
  maximum_tag_boyutu: 800 # piksel
  guven_esigi: 0.7        # %70 güven
```

### 🔧 Troubleshooting
```bash
# Test scripti çalıştır
python test_apriltag_system.py --test-detection

# Kamera kalibrasyonu
python scripts/camera_calibration.py
```

## 📱 Test Prosedürü

### 1️⃣ Mesafe Testi
```python
# 2 metre -> 50cm -> 10cm arasında test et
mesafe_listesi = [2.0, 1.5, 1.0, 0.5, 0.3, 0.1]
for mesafe in mesafe_listesi:
    print(f"Mesafe {mesafe}m'de tespit başarılı mı?")
```

### 2️⃣ Açı Testi
```python
# -45° -> +45° arasında test et
aci_listesi = [-45, -30, -15, 0, 15, 30, 45]
for aci in aci_listesi:
    print(f"Açı {aci}°'de tespit başarılı mı?")
```

### 3️⃣ Işık Testi
- Sabah güneşi
- Öğlen güneşi
- Akşam güneşi
- Gece aydınlatma

## 🚀 Sonuç
Bu rehberi takip ettiğinde robot'un mm hassasiyetinde şarj istasyonuna yaklaşabilecek! Herhangi bir sorun olursa test scriptlerini çalıştır ve log'ları kontrol et.

**Hacı Abi'nin Altın Önerisi**: İlk kurulumda biraz fazla tag koy, sonra ihtiyaç olmayan varsa çıkarabilirsin. Güvenlik için redundancy her zaman iyidir! 🎯
