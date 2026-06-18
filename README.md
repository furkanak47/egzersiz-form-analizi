# Gerçek Zamanlı Egzersiz Form Analizi ve Kişisel Performans Rehberlik Sistemi

Bilgisayarlı görü ve makine öğrenmesi kullanarak egzersiz formunu gerçek zamanlı analiz eden, kişisel performans takibi yapan masaüstü uygulama. Standart web kamerası yeterli — ek donanım gerekmez.

**Bursa Uludağ Üniversitesi — YBS Lisans Tezi, 2026**  
**Öğrenci:** Furkan Akdemir · **Danışman:** Prof. Dr. Melih Engin

---

## Özellikler

- **19 egzersiz** için gerçek zamanlı form analizi (biceps curl, squat, deadlift, bench press...)
- **Kural tabanlı motor** — anlık eklem açısı hesabı, hata/uyarı bildirimi
- **Random Forest sınıflandırıcı** — tekrar bittikten sonra correct/wrong tahmini (%76.1 ort. doğruluk)
- **Vücut yağ tahmini** — MediaPipe segmentasyon maskesi + antropometri (MAE: 3.7 pp)
- **Güç profili** — OpenPowerlifting normlarına göre Dots skoru ve persentil
- **Beslenme takibi** — 455,100 USDA + 1,357 Türkiye'ye özgü gıda kaydı
- **İlerleme kaydedicisi** — antrenman geçmişi, vücut ölçümleri, güç trendleri
- **El jesti ile egzersiz seçimi** — MediaPipe Hands, parmak sayısı

---

## Kurulum

```bash
git clone https://github.com/furkanak47/egzersiz-form-analizi.git
cd egzersiz-form-analizi
pip install -r requirements.txt
```

### Gereksinimler

| Kütüphane | Sürüm |
|-----------|-------|
| mediapipe | >=0.10.0 |
| opencv-python | >=4.8.0 |
| scikit-learn | >=1.3.0 |
| numpy | >=1.24.0 |
| pandas | >=2.0.0 |

---

## Kullanım

```bash
python main.py
```

### Tuş kontrolleri

| Tuş | İşlev |
|-----|-------|
| `1–9` | Egzersiz seçimi |
| `D` | Veri toplama modu |
| `C` | Doğru form etiketle |
| `E` | Hatalı form etiketle |
| `Q` | Çıkış |

---

## Model Eğitimi

Eğitim verileri `data/form_data/` klasöründe hazır. Modelleri yeniden eğitmek için:

```bash
python ml/trainer.py --exercise biceps_curl
# veya tümü için:
python ml/trainer.py --all
```

Vücut yağ modeli:
```bash
python veri/vucut_yagi/train_comprehensive_model.py
```

Beslenme veritabanı:
```bash
python veri/beslenme/build_food_db.py
```

---

## Proje Yapısı

```
egzersiz-form-analizi/
├── main.py                 # Ana uygulama döngüsü
├── config.py               # Kamera, renk, eşik sabitleri
├── exercises/              # 19 egzersiz analiz motoru
├── ml/                     # Model eğitimi, özellik çıkarma, veri toplama
├── bodyfat/                # Vücut yağ tahmini ve segmentasyon
├── strength/               # Güç profili, Dots skoru, persentil
├── nutrition/              # Beslenme takibi, kalori hesaplama
├── progress/               # Seans kaydı, ilerleme ekranı
├── feedback/               # HUD çizimi, sesli uyarı
├── utils/                  # Açı/mesafe hesaplama, landmark araçları
├── data/form_data/         # 1,139 etiketli tekrar (19 egzersiz CSV)
└── veri/                   # Ham veri setleri ve build scriptleri
```

---

## Veri Kaynakları

| Kaynak | Kayıt | Kullanım |
|--------|-------|----------|
| YouTube (yt-dlp) | 652 video → 1,139 tekrar | Form sınıflandırıcı |
| NHANES (2003–2018) | 68,011 | Vücut yağ modeli |
| ANSUR II (2012) | 6,068 | Vücut yağ modeli |
| OpenPowerlifting | 1.3M+ kayıt → 202 satır norm | Güç persentili |
| USDA FoodData Central | 455,100 | Beslenme takibi |
| BEBIS + Open Food Facts | 1,357 Türk gıdası | Beslenme takibi |

---

## Sistem Gereksinimleri

- Python 3.9+
- Web kamerası (720p önerilir)
- RAM: minimum 4 GB (8 GB önerilir)
- İşletim sistemi: Windows (ses sistemi için), Linux/macOS'ta ses devre dışı

---

## Notlar

- `ml/models/exercise_recognizer.joblib` (141 MB) GitHub limitini aştığı için repoya eklenmemiştir. Yeniden eğitmek için `ml/trainer.py` kullanın.
- `kullanici_verisi/` klasörü kişisel veri içerdiğinden `.gitignore`'a alınmıştır. İlk çalıştırmada otomatik oluşturulur.
- Egzersiz videoları telif hakkı nedeniyle repoya dahil edilmemiştir.
