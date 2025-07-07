# 🖨️ AprilTag Pixel Perfect Basım Rehberi

## ⚠️ KRİTİK UYARI
**ASLA "sayfaya sığdır" kullanma!** Bu, tag boyutlarını bozar ve robot'un tespit etmesini engeller.

## 🎯 Pixel Perfect Basım Ayarları

### 📋 Temel Gereksinimler
- **Dosya**: `apriltag_sarj_geometrik_kucuk_A3.png`
- **Boyut**: 3508 x 4961 pixel
- **DPI**: 300 x 300
- **Format**: PNG (lossless)

### 🖨️ Yazıcı Ayarları

#### **Windows (Adobe Reader/Acrobat):**
```
1. File → Print
2. Page Sizing: "Actual Size" ✅
3. Auto-Rotate: OFF ❌
4. Choose paper source by PDF page size: ON ✅
5. Paper: A3 (297 x 420 mm)
6. Orientation: Portrait
7. Quality: High/Best (300 DPI+)
```

#### **Windows (Paint/Photo Viewer):**
```
1. File → Print
2. Fit picture to frame: OFF ❌
3. Picture position: Center ✅
4. Paper size: A3
5. Print quality: High
6. Color: Grayscale (için siyah-beyaz)
```

#### **macOS (Preview):**
```
1. File → Print
2. Scale: 100% ✅
3. Auto-Rotate: OFF ❌
4. Paper Size: A3
5. Orientation: Portrait
6. Quality: Best
```

#### **Linux (CUPS/evince):**
```
1. File → Print
2. Page Setup → A3
3. Scale: 100% ✅
4. Fit to page: OFF ❌
5. Resolution: 300 DPI+
```

### 🔧 Printer Driver Ayarları

#### **HP Printers:**
```
Media Type: Plain Paper
Print Quality: Best/Photo
Color: Grayscale
Paper Source: Tray (A3)
Borderless: OFF
Scale: 100%
```

#### **Canon Printers:**
```
Media Type: Plain Paper
Quality: High
Grayscale Printing: ON
Paper Size: A3
Scaling: None (100%)
Auto Fit: OFF
```

#### **Epson Printers:**
```
Media Type: Plain Paper
Quality: Fine/Photo
Print Color: Black
Paper Size: A3
No Scaling: ON
Fit to Page: OFF
```

### 📏 Basım Sonrası Kontrol

#### **1. Boyut Ölçümü:**
```bash
Tag boyutu: 8.0 cm ± 0.1 cm
Tag arası mesafe: 9.3 cm ± 0.1 cm
Toplam genişlik: 26.6 cm ± 0.2 cm
```

#### **2. Cetvel ile Kontrol:**
- Ana tag (ID: 0) boyutu: **tam 8 cm**
- Sol-sağ tag'ler arası: **tam 18.6 cm**
- Ana tag'ten yan tag'lere: **tam 13.1 cm**

#### **3. Hata Toleransı:**
- **✅ Kabul edilebilir**: ±1mm hata
- **⚠️ Dikkat**: ±2mm hata
- **❌ Reddet**: >±3mm hata

### 🚨 Yaygın Hatalar ve Çözümleri

#### **Problem: Tag'ler küçük çıktı**
```
Sebep: "Fit to page" kullanıldı
Çözüm: Actual size (100%) kullan
```

#### **Problem: Sayfa kesildi**
```
Sebep: Margin ayarları yanlış
Çözüm: Borderless OFF, custom margin
```

#### **Problem: Bulanık/pixelated**
```
Sebep: DPI düşük
Çözüm: 300+ DPI, high quality
```

#### **Problem: Renk problemi**
```
Sebep: Color printing
Çözüm: Grayscale/Black only
```

### 📱 Mobil Basım (Son Çare)

#### **Android:**
```
Google Drive → Print → HP Smart/Canon Print
Scale: 100%
Paper: A3
Quality: High
```

#### **iOS:**
```
Files → Share → Print → AirPrint
Scale: Fit to Printable Area: OFF
Paper: A3
```

### 🎯 Test Basımı Önerisi

İlk önce **A4'te test** yap:
```bash
# Test dosyası oluştur (A4)
python scripts/apriltag_generator.py --ids 0 --basim --boyut kucuk

# A4'te test basımı
# Cetvel ile ölç: Tag boyutu 8cm mi?
# Eğer değilse yazıcı ayarlarını düzelt
```

### ✅ Final Checklist

- [ ] Dosya: `apriltag_sarj_geometrik_kucuk_A3.png`
- [ ] Kağıt: A3 (297x420mm)
- [ ] Ölçekleme: %100 (Actual Size)
- [ ] Fit to page: OFF
- [ ] DPI: 300+
- [ ] Kalite: High/Best
- [ ] Renk: Grayscale
- [ ] Tag boyutu: 8.0 cm ±1mm
- [ ] Tag mesafesi: 9.3 cm ±1mm

## 🏆 Başarılı Basım = Mükemmel Robot Performansı!

Pixel perfect basım ile robot'un %95+ tespit başarısı garantili! 🎯
