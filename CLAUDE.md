# Egzersiz Form Analizi — Proje Kılavuzu

## Proje Amacı

Gerçek zamanlı egzersiz form analizi sistemi. Kullanıcı kameraya bakarak egzersiz yaparken MediaPipe ile vücut iskeletini takip eder, eklem açılarını hesaplar, hatalı formu tespit eder ve sesli/görsel geri bildirim verir. Aynı zamanda kullanıcının kendi verileriyle eğitilebilen bir scikit-learn sınıflandırma modeli içerir. Tez projesi — Python, MediaPipe, OpenCV, scikit-learn stack'i.

---

## Klasör Yapısı

```
egzersiz-form-analizi/
│
├── exercises/          Egzersiz analiz motorları. Her egzersizin form kuralları ve
│                       açı eşikleri burada. BaseExercise temel sınıfından türer.
│
├── ml/                 Makine öğrenmesi alt sistemi. Model eğitimi, özellik çıkarma,
│                       dinamik eşik yönetimi ve veri toplama kodu burada.
│
├── feedback/           Kullanıcıya geri bildirim. Kamera görüntüsü üzerine çizilen
│                       HUD katmanı (visual_feedback.py) ve ses uyarıları (audio_feedback.py).
│
├── utils/              Matematiksel yardımcılar. Açı ve mesafe hesaplama, landmark
│                       koordinat dönüşümleri.
│
├── tools/              Offline veri hazırlama araçları. Video'dan CSV üretme, toplu
│                       işlem, sentetik veri üretme. main.py'den bağımsız çalışır.
│
├── data/               Eğitim verileri. Her egzersiz için correct/ ve wrong/ alt
│                       klasörleri. Her CSV = bir tekrar, her satır = bir frame.
│                       ŞU AN BOŞTUR.
│
├── main.py             Ana program döngüsü. Kamera akışı, PoseWorker thread,
│                       tuş kontrolleri, egzersiz seçimi.
│
├── pose_detector.py    MediaPipe Pose API sarmalayıcı. Frame işleme ve iskelet çizimi.
│
├── gesture_detector.py MediaPipe Hands API. Parmak sayısıyla egzersiz seçimi.
│
└── config.py           Proje geneli sabitler: kamera çözünürlüğü, renkler (BGR),
                        egzersiz listesi, MediaPipe güven eşikleri.
```

---

## Önemli Dosya Yolları ve Görevleri

### Ana Akış

| Dosya | Görev | Kritik Sembol |
|---|---|---|
| `main.py` | Kamera döngüsü, egzersiz seçimi, tuş kontrolü | `PoseWorker` (thread-safe pose işleme) |
| `pose_detector.py` | MediaPipe Pose sarmalayıcı | `process_frame()` → normalize landmark listesi |
| `gesture_detector.py` | El jesti ile egzersiz seçimi | 1.5 sn hold mantığı |
| `config.py` | Proje geneli sabitler | `EXERCISES`, `COLOR_*`, `CAMERA_WIDTH/HEIGHT` |

### Egzersiz Motorları (`exercises/`)

| Dosya | Egzersiz | Ana Metrik |
|---|---|---|
| `base_exercise.py` | Temel sınıf | `FormResult` dataclass, `analyze()` arayüzü |
| `biceps_curl.py` | Biceps Curl | Dirsek açısı (bilateral) |
| `triceps.py` | Triceps Extension | Dirsek açısı (ters faz: uzatılı = DOWN) |
| `shoulder_press.py` | Shoulder Press | Dirsek açısı + bilek hizası |
| `lateral_raise.py` | Lateral Raise | `elevation_angle` (omuz yükselmesi) |
| `fly.py` | Pec Fly | İki bilek arası açılma açısı |
| `bench_press.py` | Bench Press | Dirsek açısı + flare + simetri |

### ML Alt Sistemi (`ml/`)

| Dosya | Görev |
|---|---|
| `classifier.py` | Tekrar-bazlı model (`ExerciseClassifier`). Tekrar bitince "correct/wrong" tahmini. |
| `frame_classifier.py` | Frame-bazlı model. Her karede anlık tahmin. |
| `feature_extractor.py` | Her açı için istatistik çıkarır (~30-40 özellik). |
| `trainer.py` | `python ml/trainer.py --exercise biceps_curl` → model eğitir. |
| `thresholds.py` | `ml/thresholds.json` varsa dinamik eşikler, yoksa hard-coded fallback. |
| `data_collector.py` | Uygulama içi veri toplama (D → C/E tuşları). |
| `models/` | Eğitilmiş modeller: `{exercise}_model.joblib`. ŞU AN BOŞTUR. |

### Geri Bildirim (`feedback/`)

| Dosya | Görev |
|---|---|
| `visual_feedback.py` | `draw_hud()` ile ekrana 4 panel çizer. |
| `audio_feedback.py` | `play_sound(sound_type)`, 1.5 sn cooldown, Windows-only. |

### Yardımcılar (`utils/`)

| Dosya | Görev |
|---|---|
| `angle_calculator.py` | `calculate_angle(a,b,c)`, `calculate_distance(a,b)`, `vertical_angle(a,b)` |
| `landmark_utils.py` | `get_px()`, `get_norm()`, `visibility()` |

### Veri Araçları (`tools/`)

| Dosya | Kullanım |
|---|---|
| `video_processor.py` | `python tools/video_processor.py --video path.mp4 --exercise biceps_curl --label correct` |
| `batch_from_zip.py` | `python tools/batch_from_zip.py --zip archive.zip --label auto` |
| `generate_synthetic.py` | `python tools/generate_synthetic.py --exercise biceps_curl` |
| `pipeline.py` | `python tools/pipeline.py --videos "C:/video/dir"` (4 aşama: video→eşik→sentetik→model) |
| `import_existing.py` | `C:\Users\Furkan\Desktop\veri\biceps_analiz\egzersiz_verisi_final.csv` → projeye aktarır |

---

## Kullanılan Kütüphaneler

| Kütüphane | Sürüm | Ne İşe Yarıyor |
|---|---|---|
| `mediapipe` | >=0.10.0 | Vücut ve el iskelet tespiti (Google) |
| `opencv-python` | >=4.8.0 | Kamera akışı, görüntü üzerine çizim |
| `scikit-learn` | >=1.3.0 | RandomForest sınıflandırıcı, StandardScaler |
| `numpy` | >=1.24.0 | Açı/koordinat hesaplama |
| `joblib` | scikit-learn ile gelir | Model kaydetme/yükleme (`.joblib`) |
| `pygame` | >=2.5.0 | requirements.txt'te var ama şu an kullanılmıyor |

---

## Bilinmesi Gereken Kurallar

### OpenCV / Görüntü İşleme

- **BGR renk sırası:** OpenCV RGB değil BGR kullanır. `config.py`'deki `COLOR_*` sabitleri BGR formatında. Renk atamasında sıra önemli: `(Blue, Green, Red)`.
- **`cv2.putText` Türkçe karakter göstermez:** ş, ğ, ü, ç, ö, ı karakterleri bozuk çıkar. Tüm UI metinleri ASCII karakterlerle yazılmalı.
- **Koordinat sistemi:** Sol üst köşe `(0,0)`, sağ alt `(width, height)`. Panel sınırları değiştirilirken tüm komşu paneller birlikte güncellenmeli.
- **Çözünürlük farkı:** Kamera görüntüsü `1280×720` gösteriliyor, MediaPipe `480×270`'de işliyor. Çizimler her zaman kamera frame'i (1280×720) üzerine yapılıyor.

### Ses Sistemi

- **`winsound` sadece Windows'ta çalışır.** Mac/Linux için `platform.system()` kontrolü ile `afplay` (macOS) veya `paplay` (Linux) kullanılmalı; ya da `simpleaudio`/`playsound` kütüphanesi eklenmeli.
- Ses frekansları: Hata=800 Hz, Uyarı=1200 Hz, Başarılı rep=1600 Hz.

### MediaPipe Pose

- **33 landmark** döner, normalize koordinatlar (0.0–1.0). Piksel çevriminde `get_px()` kullan.
- Kritik index'ler: Omuz 11/12, Dirsek 13/14, Bilek 15/16, Kalça 23/24.
- **Visibility < 0.5** ise o landmark güvenilir değil, hesaplama yapılmamalı.

### Thread-Safe PoseWorker

- `main.py` içindeki `PoseWorker` pose işlemeyi ayrı thread'de çalıştırır.
- Frame'ler queue ile gönderilir, sonuçlar `result_queue.get_nowait()` ile alınır.
- Bu pattern bozulursa kamera görüntüsü donar.

### ML Sistemi

- **İki model katmanı:** Frame-bazlı (`frame_classifier.py`, anlık) ve tekrar-bazlı (`classifier.py`, tekrar bittikten sonra). İkisi aynı feature vektörünü bekler — birini değiştirince diğerini de güncelle.
- **`thresholds.json` vs hard-coded tutarsızlık:** `thresholds.py` dosyası JSON yoksa kodun içindeki sabit değerlere döner. İkisi arasında büyük fark olursa false positive/negative artar.
- **Class imbalance:** `correct/` genellikle `wrong/`'dan fazla örnek içerir. `RandomForestClassifier(class_weight='balanced')` kullan.
- **Cross-validation < 0.70:** Daha fazla veri toplamadan model yayına alınmamalı.

### Veri

- `data/` ve `ml/models/` şu an **tamamen boş.** Model eğitmeden önce veri toplanmalı.
- Her CSV = bir tekrar, her satır = bir frame. `phase` sütunu `"up"` veya `"down"`.
- Minimum: egzersiz başına 30 correct + 20 wrong tekrar. `correct:wrong` oranı 3:1'i geçmemeli.

### Yeni Egzersiz Ekleme

1. `exercises/` altında yeni dosya oluştur, `BaseExercise`'i miras al.
2. `analyze()` metodunu override et, `FormResult` döndür.
3. `config.py`'deki `EXERCISES` listesine ekle.
4. `data/` altında `{egzersiz}/correct/` ve `{egzersiz}/wrong/` klasörlerini oluştur.
