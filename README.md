# Gercek Zamanli Egzersiz Form Analizi ve Kisisel Performans Rehberlik Sistemi

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)
![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10%2B-green)
![License](https://img.shields.io/badge/License-Academic-orange)

Standart web kamerasi kullanarak egzersiz formunu gercek zamanli analiz eden, vucut yagi tahmin eden, guc profilini hesaplayan ve beslenme takibi yapan masaustu uygulamasi. Ek donanim gerekmez.

**Bursa Uludag Universitesi — YBS Lisans Tezi, 2026**  
**Ogrenci:** Furkan Akdemir (132230044) · **Danisман:** Prof. Dr. Melih Engin

---

## Ozellikler

### Form Analizi
- 19 egzersiz icin gercek zamanli iskelet takibi (MediaPipe Pose)
- Kural tabanli motor: eklem acisi hesabi, hata/uyari bildirimi
- Random Forest siniflandirici: tekrar bittikten sonra correct/wrong tahmini
- Egzersiz tanima: kameradan otomatik egzersiz tespiti (%89.3 dogruluk)
- El jesti ile egzersiz secimi (MediaPipe Hands, parmak sayisi)
- Sesli ve gorsel HUD geri bildirimi

### Vucut Yagi Tahmini
- MediaPipe segmentasyon maskesi + antropometri olculeri
- NHANES (68.011 kisi) + ANSUR II (6.068 kisi) verisiyle egitilmis model
- Yas/cinsiyet persentil karsilastirmasi (MAE: 3.7 pp)

### Guc Profili
- Bench press, squat, deadlift 1RM tahmini
- OpenPowerlifting veritabanindan Dots skoru ve persentil hesabi

### Beslenme Takibi
- 455.100 USDA + 1.357 Turkiye'ye ozgu gida kaydi
- Gunluk kalori ve makro besin takibi

### Ilerleme Kaydedici
- Antrenman gecmisi, vucut olculeri, guc trendleri

---

## Kurulum

### Gereksinimler

- Python 3.9+
- Web kamerasi (720p onerilen)
- RAM: minimum 4 GB (8 GB onerilen)
- Isletim sistemi: Windows (ses sistemi icin); Linux/macOS'ta ses devre disi

### Adimlar

```bash
git clone https://github.com/furkanak47/egzersiz-form-analizi.git
cd egzersiz-form-analizi
pip install -r requirements.txt
python main.py
```

### Bagimliliklar

| Kutuphane | Surum |
|-----------|-------|
| mediapipe | >=0.10.0 |
| opencv-python | >=4.8.0 |
| scikit-learn | >=1.3.0 |
| numpy | >=1.24.0 |
| pandas | >=2.0.0 |

---

## Kullanim

```bash
python main.py
```

### Tus Kontrolleri

| Tus | Islev |
|-----|-------|
| `1–6` | Egzersiz secimi |
| `A` | Otomatik egzersiz tanima |
| `D` | Veri toplama moduna gir |
| `C` | Dogru form olarak etiketle |
| `E` | Hatali form olarak etiketle |
| `B` | Vucut yagi tahmini ekrani |
| `S` | Guc profili ekrani |
| `N` | Beslenme takibi ekrani |
| `P` | Ilerleme ekrani |
| `Q` | Cikis |

El jesti: kameraya parmak sayisi gostererek egzersiz secebilirsiniz (1.5 sn tutun).

---

## Desteklenen Egzersizler

| # | Egzersiz | Ana Metrik |
|---|----------|-----------|
| 1 | Biceps Curl | Dirsek acisi (bilateral) |
| 2 | Triceps Extension | Dirsek acisi (ters faz) |
| 3 | Shoulder Press | Dirsek acisi + bilek hizasi |
| 4 | Lateral Raise | Omuz yukselme acisi |
| 5 | Pec Fly | Iki bilek arasi acilma |
| 6 | Bench Press | Dirsek acisi + flare + simetri |
| 7 | Squat | Diz acisi + kalca derinligi |
| 8 | Deadlift | Sirt hizasi + kalca menjesi |
| 9 | Pull Up | Dirsek acisi + omuz aktivasyonu |
| 10 | Romanian Deadlift | Kalca menezi + sirt durusu |
| 11 | Hammer Curl | Dirsek acisi (neutral) |
| 12 | Hip Thrust | Kalca uzanma acisi |
| 13 | Lat Pulldown | Dirsek acisi + genis kavrama |
| 14 | Incline Bench Press | Dirsek + omuz acisi |
| 15 | Decline Bench Press | Dirsek acisi + omuz pozisyonu |
| 16 | Tricep Dips | Dirsek acisi + govde dikligi |
| 17 | Leg Extension | Diz acisi |
| 18 | Leg Raises | Kalca fleksiyonu |
| 19 | T-Bar Row | Dirsek + sirt acisi |

---

## Model Egitimi

Form siniflandirma modellerini yeniden egitmek icin:

```bash
# Tek egzersiz
python ml/trainer.py --exercise biceps_curl

# Tum egzersizler
python ml/trainer.py --all
```

Egzersiz tanima modeli (`exercise_recognizer`):

```bash
# Windows
araclar\train_recognizer.bat

# veya dogrudan
python ml/exercise_recognizer.py --train
```

Vucut yagi modeli:

```bash
# Once ham veriyi birlestir
python veri/vucut_yagi/build_master_dataset.py

# Sonra modeli egit
python veri/vucut_yagi/train_comprehensive_model.py
```

Beslenme veritabani:

```bash
python veri/beslenme/build_food_db.py
```

---

## Proje Yapisi

```
egzersiz-form-analizi/
|
├── main.py                     # Ana uygulama dongusu, kamera akisi, tus kontrolleri
├── config.py                   # Kamera, renk, esik sabitleri
├── pose_detector.py            # MediaPipe Pose sarmalayici
├── gesture_detector.py         # El jesti ile egzersiz secimi
├── profiles.py                 # Kullanici profil yonetimi
|
├── exercises/                  # 19 egzersiz analiz motoru
│   ├── base_exercise.py        # BaseExercise sinifi, FormResult dataclass
│   └── biceps_curl.py ...      # Her egzersiz kendi dosyasinda
|
├── ml/                         # Makine ogrenimi alt sistemi
│   ├── trainer.py              # Form siniflandirici egitimi
│   ├── form_classifier.py      # Tekrar bazli siniflandirici
│   ├── exercise_recognizer.py  # Egzersiz tanima modeli
│   ├── feature_extractor.py    # Acı istatistikleri (~40 ozellik)
│   ├── data_collector.py       # Uygulama ici veri toplama
│   ├── calibration.py          # Kullanici bazli kalibrasyon
│   └── models/                 # Egitilmis modeller (.joblib)
|
├── bodyfat/                    # Vucut yagi tahmini
├── strength/                   # Guc profili, Dots skoru
├── nutrition/                  # Beslenme takibi
├── progress/                   # Seans gecmisi, ilerleme grafikleri
├── feedback/                   # HUD cizimi, sesli uyari
├── utils/                      # Aci/mesafe hesaplama, landmark araclari
├── tools/                      # Toplu video isleme araclari
|
├── data/form_data/             # 1.139 etiketli tekrar (19 egzersiz CSV)
└── veri/                       # Ham veri setleri ve build scriptleri
    ├── vucut_yagi/             # NHANES, ANSUR II, egitilmis model
    ├── kondisyon/              # OpenPowerlifting normlar
    └── beslenme/               # USDA + Turk gida veritabanlari
```

---

## Veri Kaynaklari

| Kaynak | Kayit | Kullanim |
|--------|-------|----------|
| YouTube (yt-dlp) | 652 video → 1.139 tekrar | Form siniflandirici egitimi |
| NHANES (2003–2018) | 68.011 | Vucut yagi modeli |
| ANSUR II (2012) | 6.068 | Vucut yagi modeli |
| Body Fat Extended | 252 | Vucut yagi modeli |
| OpenPowerlifting | 1.3M+ kayit → 202 satir norm | Guc persentili |
| USDA FoodData Central | 455.100 | Beslenme takibi |
| BEBIS + Open Food Facts | 1.357 Turk gidasi | Beslenme takibi |

---

## Model Performansi

| Model | Dogruluk | Metrik |
|-------|----------|--------|
| Form siniflandirici (ort.) | %76.1 | Cross-val (5-fold) |
| Egzersiz taniyici | %89.3 | Test seti |
| Vucut yagi tahmini | 3.7 pp MAE | NHANES test seti |

---

## Notlar

- `ml/models/exercise_recognizer.joblib` (141 MB) GitHub limitini astigi icin repoya eklenmemistir.
  Yeniden egitmek icin: `araclar\train_recognizer.bat`
- `kullanici_verisi/` klasoru kisisel veri icerdigi icin `.gitignore`'a alinmistir. Ilk calistirmada otomatik olusturulur.
- Egzersiz videolari telif hakki nedeniyle repoya dahil edilmemistir.
- Ses sistemi sadece Windows'ta aktiftir (`winsound`).
