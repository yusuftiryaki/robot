# 🗺️ Rota Planlayıcı Config Referansı

Bu dokümantasyon, **RotaPlanlayici** sınıfının kullandığı tüm config değerlerini açıklar.

## 📐 Path Planning (Rota Planlama) Ayarları

```yaml
navigation:
  path_planning:
    grid_resolution: 0.1      # Grid çözünürlüğü (metre)
                              # Varsayılan: 0.1m (10cm)
                              # A* algoritması için grid boyutu

    obstacle_padding: 0.2     # Engel etrafında güvenlik mesafesi (metre)
                              # Varsayılan: 0.2m (20cm)
                              # Robot engellere bu mesafeden yaklaşmaz
```

## 🌾 Mowing (Biçme) Görev Ayarları

```yaml
navigation:
  missions:
    mowing:
      overlap: 0.1            # Şeritler arası örtüşme mesafesi (metre)
                              # Varsayılan: 0.1m (10cm)
                              # Boustrophedon algoritması için şerit örtüşmesi

      speed: 0.3              # Biçme hızı (m/s)
                              # Varsayılan: 0.3 m/s (30 cm/s)
                              # Robot'un biçme sırasındaki hareket hızı

      brush_width: 0.25       # Fırça genişliği (metre)
                              # Varsayılan: 0.25m (25cm)
                              # Mi Robot fırça genişliği
```

## 🔋 GPS Şarj İstasyonu Ayarları

```yaml
charging:
  gps_dock:
    latitude: 41.0082         # Şarj istasyonu GPS latitude koordinatı
    longitude: 28.9784        # Şarj istasyonu GPS longitude koordinatı
    accuracy_radius: 3.0      # GPS doğruluk yarıçapı (metre)
                              # Varsayılan: 3.0m

    # 🎯 Yaklaşım Mesafe Eşikleri
    precise_approach_distance: 0.5   # Hassas yaklaşım başlangıç mesafesi (metre)
                                      # Varsayılan: 0.5m (50cm)
                                      # Bu mesafeden sonra AprilTag kullanılır

    medium_distance_threshold: 10.0  # Orta mesafe eşiği (metre)
                                     # Varsayılan: 10.0m
                                     # Bu mesafeden sonra A* algoritması kullanılır

    apriltag_detection_range: 0.5    # AprilTag algılama menzili (metre)
                                     # Varsayılan: 0.5m (50cm)

    # ⚡ Yaklaşım Hızları
    approach_speeds:
      normal: 0.3             # Normal yaklaşım hızı (m/s)
      slow: 0.2               # Yavaş yaklaşım hızı (m/s)
      very_slow: 0.1          # Çok yavaş yaklaşım (m/s)
      ultra_slow: 0.05        # Ultra yavaş yaklaşım (m/s)
      precise: 0.02           # Hassas konumlandırma (m/s)
```

## 🚀 Kullanım Örnekleri

### Hassas Robot için Ayarlar
```yaml
navigation:
  path_planning:
    grid_resolution: 0.05     # 5cm hassasiyet
    obstacle_padding: 0.15    # 15cm güvenlik
  missions:
    mowing:
      overlap: 0.05           # 5cm örtüşme
      speed: 0.2              # 20 cm/s yavaş
```

### Hızlı Robot için Ayarlar
```yaml
navigation:
  path_planning:
    grid_resolution: 0.15     # 15cm daha kaba
    obstacle_padding: 0.25    # 25cm daha güvenli
  missions:
    mowing:
      overlap: 0.15           # 15cm daha fazla örtüşme
      speed: 0.5              # 50 cm/s hızlı
```

### Geniş Alan için Ayarlar
```yaml
navigation:
  path_planning:
    grid_resolution: 0.2      # 20cm kaba grid (performans)
    obstacle_padding: 0.3     # 30cm güvenlik
charging:
  gps_dock:
    medium_distance_threshold: 20.0  # 20m daha geniş alan
    approach_speeds:
      normal: 0.4             # Daha hızlı yaklaşım
```

## 🔧 Performans İpuçları

- **Grid Resolution**: Küçük değerler daha hassas ama yavaş, büyük değerler hızlı ama kaba
- **Obstacle Padding**: Robot boyutuna göre ayarlayın (robot yarıçapı + güvenlik)
- **Overlap**: Fırça kalitesine göre ayarlayın, kötü fırçalar daha fazla örtüşme gerektirir
- **Speed**: Zemin tipine göre ayarlayın, düz çim daha hızlı olabilir

## ⚠️ Önemli Notlar

1. **GPS Koordinatları**: Gerçek şarj istasyonu konumunuzu girin!
2. **Fırça Genişliği**: Robot modeline göre ayarlayın
3. **Hızlar**: Zemin ve güvenlik gereksinimlerine göre test edin
4. **Mesafe Eşikleri**: GPS doğruluğuna göre ayarlayın

## 🎯 Varsayılan Değerler

Tüm config değerleri isteğe bağlıdır. Tanımlanmayan değerler için şu varsayılanlar kullanılır:

```python
# Rota planlama
grid_resolution = 0.1       # 10cm
obstacle_padding = 0.2      # 20cm

# Biçme
overlap = 0.1              # 10cm
speed = 0.3                # 30 cm/s
brush_width = 0.25         # 25cm

# GPS dock
accuracy_radius = 3.0      # 3m
precise_approach_distance = 0.5    # 50cm
medium_distance_threshold = 10.0   # 10m
apriltag_detection_range = 0.5     # 50cm

# Hızlar
normal = 0.3               # 30 cm/s
slow = 0.2                 # 20 cm/s
very_slow = 0.1            # 10 cm/s
ultra_slow = 0.05          # 5 cm/s
precise = 0.02             # 2 cm/s
```

Bu değerler robotun güvenli çalışması için optimize edilmiştir.
