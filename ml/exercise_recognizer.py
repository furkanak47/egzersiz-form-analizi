"""
Egzersiz Tanima Sistemi
-----------------------
Kullanim:
  1. Veri cikartma + egitim (bir kez calistir):
       python ml/exercise_recognizer.py --train

  2. Uygulama icinden tahmin:
       recognizer = ExerciseRecognizer()
       recognizer.load()
       ex_id = recognizer.predict(landmarks)
"""

import cv2
import numpy as np
import mediapipe as mp
import pandas as pd
import joblib
from pathlib import Path
from typing import Optional, List, Tuple
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report

# ── Sabitler ──────────────────────────────────────────────────────────────────

KAGGLE_DIR  = Path(__file__).parent.parent / "veri" / "egzersiz_videolari"
DATA_CSV    = Path(__file__).parent / "recognition_data.csv"
MODEL_PATH  = Path(__file__).parent / "models" / "exercise_recognizer.joblib"

# Kaggle klasor adi → egzersiz etiket
FOLDER_MAP = {
    "barbell biceps curl":  "biceps_curl",
    "bench press":          "bench_press",
    "chest fly machine":    "fly",
    "deadlift":             "deadlift",
    "decline bench press":  "decline_bench_press",
    "hammer curl":          "hammer_curl",
    "hip thrust":           "hip_thrust",
    "incline bench press":  "incline_bench_press",
    "lat pulldown":         "lat_pulldown",
    "lateral raise":        "lateral_raise",
    "leg extension":        "leg_extension",
    "leg raises":           "leg_raises",
    "plank":                "plank",
    "pull up":              "pull_up",
    "pull Up":              "pull_up",
    "push-up":              "push_up",
    "romanian deadlift":    "romanian_deadlift",
    "russian twist":        "russian_twist",
    "shoulder press":       "shoulder_press",
    "squat":                "squat",
    "t bar row":            "t_bar_row",
    "tricep dips":          "tricep_dips",
    "tricep Pushdown":      "triceps",
}

# Kritik landmark indexleri (MediaPipe Pose — 33 nokta)
_KEY = [0, 11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28]
#       burun omuz omuz dirs dirs bilk bilk kalca kalca diz  diz  ayak ayak

FRAME_SKIP = 8   # her 8 frame'de bir ornek al (30fps → ~3-4 ornek/sn)
MIN_VIS    = 0.5  # bu gorununurluk altindaki landmark'li frame'leri atla


# ── Ozellik cikarma ───────────────────────────────────────────────────────────

def _angle(a, b, c):
    """b noktasindaki aci (derece)."""
    ba = np.array([a[0] - b[0], a[1] - b[1]])
    bc = np.array([c[0] - b[0], c[1] - b[1]])
    n  = np.linalg.norm(ba) * np.linalg.norm(bc)
    if n < 1e-8:
        return 0.0
    cos = np.dot(ba, bc) / n
    return float(np.degrees(np.arccos(np.clip(cos, -1.0, 1.0))))


def extract_features(landmarks) -> Optional[np.ndarray]:
    """
    MediaPipe landmark listesinden ozellik vektoru cikarir.
    Doner: (34,) float32 array  veya  None (gorununurluk dusukse)
    """
    # Gorunurluk kontrolu — kritik omuz/dirsek/bilek
    for idx in [11, 12, 13, 14, 15, 16]:
        if landmarks[idx].visibility < MIN_VIS:
            return None

    # Normalize koordinatlar (x, y) — kalca ortasina gore merkezle
    hip_x = (landmarks[23].x + landmarks[24].x) / 2
    hip_y = (landmarks[23].y + landmarks[24].y) / 2
    sh_dist = abs(landmarks[11].x - landmarks[12].x) + 1e-8   # olcekleme

    coords = []
    for idx in _KEY:
        lm = landmarks[idx]
        coords.append((lm.x - hip_x) / sh_dist)
        coords.append((lm.y - hip_y) / sh_dist)

    # Acilar
    def pt(i):
        return (landmarks[i].x, landmarks[i].y)

    angles = [
        _angle(pt(11), pt(13), pt(15)),   # sol dirsek
        _angle(pt(12), pt(14), pt(16)),   # sag dirsek
        _angle(pt(13), pt(11), pt(23)),   # sol omuz
        _angle(pt(14), pt(12), pt(24)),   # sag omuz
        _angle(pt(11), pt(23), pt(25)),   # sol kalca
        _angle(pt(12), pt(24), pt(26)),   # sag kalca
        _angle(pt(23), pt(25), pt(27)),   # sol diz
        _angle(pt(24), pt(26), pt(28)),   # sag diz
    ]

    feat = np.array(coords + angles, dtype=np.float32)
    return feat


# ── Veri cikarma ──────────────────────────────────────────────────────────────

def build_dataset():
    """
    kagglefitnes/ altindaki tum videolari isle, ozellikleri cikart,
    ml/recognition_data.csv dosyasina kaydet.
    """
    if not KAGGLE_DIR.exists():
        print("HATA: kagglefitnes/ klasoru bulunamadi.")
        return False

    mp_pose = mp.solutions.pose.Pose(
        static_image_mode=False,
        model_complexity=0,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.4,
    )

    rows    = []
    skipped = []

    for folder in sorted(KAGGLE_DIR.iterdir()):
        if not folder.is_dir():
            continue

        label = FOLDER_MAP.get(folder.name)
        if label is None:
            print("  [ATLA] bilinmeyen klasor: %s" % folder.name)
            skipped.append(folder.name)
            continue

        videos = list(folder.glob("*.mp4")) + list(folder.glob("*.MOV")) + \
                 list(folder.glob("*.mov")) + list(folder.glob("*.avi"))

        print("%-30s → %-22s  %d video" % (folder.name, label, len(videos)))

        for vid_path in videos:
            cap   = cv2.VideoCapture(str(vid_path))
            frame_idx = 0
            hit   = 0

            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                frame_idx += 1
                if frame_idx % FRAME_SKIP != 0:
                    continue

                rgb  = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                res  = mp_pose.process(rgb)
                if not res.pose_landmarks:
                    continue

                feat = extract_features(res.pose_landmarks.landmark)
                if feat is None:
                    continue

                rows.append(list(feat) + [label])
                hit += 1

            cap.release()

        if rows:
            ex_count = sum(1 for r in rows if r[-1] == label)
            print("    toplam ornek: %d" % ex_count)

    mp_pose.close()

    if not rows:
        print("HATA: Hic ornek cikarilamadi.")
        return False

    n_feat = len(rows[0]) - 1
    col_names = (
        [("coord_%d" % i) for i in range(n_feat - 8)] +
        ["ang_l_dirsek", "ang_r_dirsek", "ang_l_omuz", "ang_r_omuz",
         "ang_l_kalca",  "ang_r_kalca",  "ang_l_diz",  "ang_r_diz",
         "label"]
    )
    df = pd.DataFrame(rows, columns=col_names)
    df.to_csv(DATA_CSV, index=False)

    print("\nKaydedildi: %s" % DATA_CSV)
    print("Toplam ornek : %d" % len(df))
    print("Egzersiz sayisi: %d" % df["label"].nunique())
    print(df["label"].value_counts().to_string())
    return True


# ── Model egitimi ─────────────────────────────────────────────────────────────

def train():
    """recognition_data.csv'den model egit, kaydet."""
    if not DATA_CSV.exists():
        print("Once build_dataset() calistir.")
        return False

    df = pd.read_csv(DATA_CSV)
    X  = df.drop("label", axis=1).values.astype(np.float32)
    y  = df["label"].values

    le = LabelEncoder()
    y_enc = le.fit_transform(y)

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y_enc, test_size=0.2, random_state=42, stratify=y_enc)

    print("Egitim: %d ornek, Test: %d ornek" % (len(X_tr), len(X_te)))
    print("Sinif sayisi:", len(le.classes_))

    clf = RandomForestClassifier(
        n_estimators=200,
        max_depth=None,
        class_weight="balanced",
        n_jobs=-1,
        random_state=42,
    )
    clf.fit(X_tr, y_tr)

    y_pred = clf.predict(X_te)
    acc    = (y_pred == y_te).mean()
    print("\nTest dogrulugu: %.2f%%" % (acc * 100))
    print(classification_report(y_te, y_pred, target_names=le.classes_))

    cv = cross_val_score(clf, X, y_enc, cv=5, scoring="accuracy", n_jobs=-1)
    print("5-Fold CV: %.2f%% (+/- %.2f%%)" % (cv.mean()*100, cv.std()*100))

    MODEL_PATH.parent.mkdir(exist_ok=True)
    joblib.dump({"clf": clf, "le": le}, MODEL_PATH)
    print("\nModel kaydedildi: %s" % MODEL_PATH)
    return True


# ── Tahmin sinifi ─────────────────────────────────────────────────────────────

class ExerciseRecognizer:
    """
    Gercek zamanli egzersiz tanima.
    Her N frame'de bir predict() cagrilir.
    """

    CONFIDENCE_THRESHOLD = 0.55   # bu altindaysa "belirsiz"
    SMOOTH_WINDOW        = 4      # son N tahmin uzerinden oylama

    def __init__(self):
        self._clf    = None
        self._le     = None
        self._loaded = False
        self._history: List[str] = []

    def load(self) -> bool:
        if not MODEL_PATH.exists():
            return False
        bundle       = joblib.load(MODEL_PATH)
        self._clf    = bundle["clf"]
        self._le     = bundle["le"]
        self._loaded = True
        return True

    def predict(self, landmarks) -> Optional[str]:
        """
        landmarks: MediaPipe pose_landmarks.landmark listesi
        Doner: egzersiz_id (str) veya None (belirsiz / model yuklenmemis)
        """
        if not self._loaded:
            return None

        feat = extract_features(landmarks)
        if feat is None:
            return None

        proba = self._clf.predict_proba(feat.reshape(1, -1))[0]
        best  = proba.argmax()
        conf  = proba[best]

        if conf < self.CONFIDENCE_THRESHOLD:
            return None

        label = self._le.inverse_transform([best])[0]

        # Kayan pencere oylama — ani degisimleri duzelt
        self._history.append(label)
        if len(self._history) > self.SMOOTH_WINDOW:
            self._history.pop(0)

        from collections import Counter
        winner = Counter(self._history).most_common(1)[0][0]
        return winner

    def top3(self, landmarks) -> List[Tuple[str, float]]:
        """Hata ayiklama icin — ilk 3 tahmin ve olasiliklari."""
        if not self._loaded:
            return []
        feat = extract_features(landmarks)
        if feat is None:
            return []
        proba  = self._clf.predict_proba(feat.reshape(1, -1))[0]
        top3_i = proba.argsort()[-3:][::-1]
        return [(self._le.inverse_transform([i])[0], float(proba[i])) for i in top3_i]

    @property
    def loaded(self):
        return self._loaded


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    if "--train" in sys.argv:
        print("=== Veri cikarma ===")
        ok = build_dataset()
        if ok:
            print("\n=== Model egitimi ===")
            train()
    elif "--data-only" in sys.argv:
        build_dataset()
    elif "--train-only" in sys.argv:
        train()
    else:
        print("Kullanim:")
        print("  python ml/exercise_recognizer.py --train         # veri + egitim")
        print("  python ml/exercise_recognizer.py --data-only     # sadece veri cikar")
        print("  python ml/exercise_recognizer.py --train-only    # mevcut veri ile egit")
