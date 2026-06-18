"""
Kamera silüeti + kullanici bilgileriyle vucut yag orani tahmini.

Olcum kaynagi: MediaPipe segmentasyon maskesi (silüet kenarlari)
  - Landmark degil, pikselden piksel gercek vücut genisligi olculur
  - Gercek genislik + BMI-duzeltmeli katsayi = cevre tahmini

Yag modeli: 12 ozellik (height, weight, bmi, age, sex,
             arm, chest, waist, hip, neck, WHR, WHtR)
  SimpleImputer -> StandardScaler -> GradientBoostingRegressor
  Eksik olcumler NaN olarak gonderilir, imputer doldurur.

Populasyon: 74,511 kisilik NHANES+ANSUR2+Kaggle verisinden persentil.
"""

import numpy as np
import joblib
import pandas as pd
from pathlib import Path
from collections import deque
import mediapipe as mp

FAT_MODEL_PATH   = Path(__file__).parent.parent / "veri" / "vucut_yagi" / "fat_model.joblib"
NORMS_PATH       = Path(__file__).parent.parent / "veri" / "vucut_yagi" / "population_norms.csv"

BUFFER_SIZE = 25

_lm = mp.solutions.pose.PoseLandmark
NOSE       = _lm.NOSE.value
L_SHOULDER = _lm.LEFT_SHOULDER.value
R_SHOULDER = _lm.RIGHT_SHOULDER.value
L_HIP      = _lm.LEFT_HIP.value
R_HIP      = _lm.RIGHT_HIP.value
L_ANKLE    = _lm.LEFT_ANKLE.value
R_ANKLE    = _lm.RIGHT_ANKLE.value


BODY_TYPE_MALE = [
    (6,  "Estetik Sporcu"),
    (14, "Atletik"),
    (18, "Fit"),
    (25, "Ortalama"),
    (100,"Yuksek Yag"),
]
BODY_TYPE_FEMALE = [
    (14, "Estetik Sporcu"),
    (21, "Atletik"),
    (25, "Fit"),
    (32, "Ortalama"),
    (100,"Yuksek Yag"),
]

# Modelin beklediği ozellik sirasina tam uyuyor olmali
FEATURES = [
    "height_cm", "weight_kg", "bmi", "age", "sex_num",
    "arm_cm", "chest_cm", "waist_cm", "hip_cm", "neck_cm",
    "waist_hip_ratio", "WHtR",
]


def classify_body_type(fat_pct, sex="M"):
    table = BODY_TYPE_MALE if sex == "M" else BODY_TYPE_FEMALE
    for threshold, label in table:
        if fat_pct < threshold:
            return label
    return "Yuksek Yag"


def bmi_category(bmi):
    if bmi < 18.5: return "Zayif"
    if bmi < 25.0: return "Normal"
    if bmi < 30.0: return "Fazla Kilolu"
    return "Obez"


def distance_status(body_height_px, frame_h):
    ratio = body_height_px / frame_h
    if ratio > 0.90: return "COK YAKIN", (0, 0, 255)
    if ratio > 0.70: return "YAKIN",     (0, 165, 255)
    if ratio > 0.45: return "IYI",       (0, 255, 0)
    if ratio > 0.25: return "UZAK",      (0, 165, 255)
    return "COK UZAK", (0, 0, 255)


def _mask_width_cm(mask_bin, y, scale):
    H, W = mask_bin.shape
    rows = []
    for dy in range(-3, 4):
        yy = int(y) + dy
        if 0 <= yy < H:
            row = mask_bin[yy, :]
            cols = np.where(row > 0)[0]
            if len(cols) >= 20:
                rows.append((cols[-1] - cols[0]) * scale)
    if not rows:
        return None
    return float(np.median(rows))


def measure_from_segmentation(mask, landmarks, W, H, height_cm, weight_kg):
    def lm_vis(idx):
        return landmarks[idx].visibility

    key_lm = [NOSE, L_SHOULDER, R_SHOULDER, L_HIP, R_HIP, L_ANKLE, R_ANKLE]
    if any(lm_vis(i) < 0.4 for i in key_lm):
        return None

    def lm_y(idx): return landmarks[idx].y * H
    def lm_x(idx): return landmarks[idx].x * W

    nose_y  = lm_y(NOSE)
    ankle_y = (lm_y(L_ANKLE) + lm_y(R_ANKLE)) / 2
    body_h  = ankle_y - nose_y
    if body_h < 80:
        return None

    dist_str, dist_color = distance_status(body_h, H)
    body_ratio = body_h / H
    if body_ratio > 0.75 or body_ratio < 0.25:
        return {
            "waist_cm": None, "hip_cm": None,
            "shoulder_width_cm": None, "shoulder_hip_ratio": None,
            "body_height_px": round(body_h, 0),
            "dist_status": dist_str, "dist_color": dist_color,
        }

    scale  = height_cm / body_h
    hip_y  = (lm_y(L_HIP)      + lm_y(R_HIP))      / 2
    sh_y   = (lm_y(L_SHOULDER) + lm_y(R_SHOULDER))  / 2
    waist_y = sh_y + (hip_y - sh_y) * 0.60

    sh_w_px    = abs(lm_x(R_SHOULDER) - lm_x(L_SHOULDER))
    shoulder_cm = sh_w_px * scale

    mask_bin = (mask > 0.45).astype(np.uint8)
    hip_w_cm   = _mask_width_cm(mask_bin, hip_y,   scale)
    waist_w_cm = _mask_width_cm(mask_bin, waist_y, scale)

    if hip_w_cm is None or waist_w_cm is None:
        return None

    bmi = weight_kg / (height_cm / 100) ** 2

    MAX_HIP_W   = height_cm * 0.31
    MAX_WAIST_W = height_cm * 0.27
    if hip_w_cm > MAX_HIP_W or waist_w_cm > MAX_WAIST_W:
        return {
            "waist_cm": None, "hip_cm": None,
            "shoulder_width_cm":  round(shoulder_cm, 1),
            "shoulder_hip_ratio": round(sh_w_px / max(abs(lm_x(R_HIP) - lm_x(L_HIP)), 1), 2),
            "body_height_px": round(body_h, 0),
            "dist_status": dist_str, "dist_color": dist_color,
            "mask_invalid": True,
        }

    # NHANES'ten kalibre edilmis cevre/gorünen-genislik katsayilari
    hip_factor   = 1.856 + 0.0255 * bmi
    waist_factor = 1.580 + 0.0350 * bmi

    hip_cm   = float(np.clip(hip_w_cm   * hip_factor,   55, 165))
    waist_cm = float(np.clip(waist_w_cm * waist_factor, 40, 140))

    shoulder_hip_ratio = sh_w_px / max(abs(lm_x(R_HIP) - lm_x(L_HIP)), 1)

    return {
        "waist_cm":           round(waist_cm, 1),
        "hip_cm":             round(hip_cm, 1),
        "shoulder_width_cm":  round(shoulder_cm, 1),
        "shoulder_hip_ratio": round(shoulder_hip_ratio, 2),
        "body_height_px":     round(body_h, 0),
        "dist_status":        dist_str,
        "dist_color":         dist_color,
        "mask_invalid":       False,
    }


class BodyEstimator:
    def __init__(self):
        self._fat_model    = None
        self._fat_features = FEATURES
        self._norms        = None
        self._norm_cache   = {}   # {(col, sex_or_None): sorted_np_array}
        self.loaded        = False
        self._waist_buf    = deque(maxlen=BUFFER_SIZE)
        self._hip_buf      = deque(maxlen=BUFFER_SIZE)
        self._fat_buf      = deque(maxlen=BUFFER_SIZE)

    def load(self):
        if FAT_MODEL_PATH.exists():
            raw = joblib.load(FAT_MODEL_PATH)
            if isinstance(raw, dict):
                self._fat_model    = raw["pipeline"]
                self._fat_features = raw.get("features", FEATURES)
            else:
                # eski format: dogrudan pipeline/model
                self._fat_model    = raw
                self._fat_features = FEATURES
            self.loaded = True
        else:
            print(f"Yag modeli bulunamadi: {FAT_MODEL_PATH}")

        if NORMS_PATH.exists():
            try:
                self._norms = pd.read_csv(NORMS_PATH, dtype={"sex": str},
                                          low_memory=False)
                self._build_norm_cache()
            except Exception as e:
                print(f"population_norms yuklenemedi: {e}")

    def _build_norm_cache(self):
        """Hizli persentil hesabi icin sutun bazinda sirali diziler olusturur."""
        if self._norms is None:
            return
        df = self._norms
        for col in ["bmi", "waist_cm", "hip_cm", "arm_cm", "chest_cm", "neck_cm",
                    "waist_hip_ratio", "WHtR"]:
            if col not in df.columns:
                continue
            vals = df[col].dropna().values
            if len(vals) > 0:
                self._norm_cache[(col, None)] = np.sort(vals)
            if "sex" in df.columns:
                for s in ("M", "F"):
                    sub = df[df["sex"] == s][col].dropna().values
                    if len(sub) > 0:
                        self._norm_cache[(col, s)] = np.sort(sub)

    def percentile(self, value, column, sex=None):
        """
        Deger verilen olcum icin populasyonda kacinci persentilde olundugunu dondurur.
        Daha buyuk deger = daha yuksek persentil (bel genisligi icin bu yanilticis olabilir).
        """
        if value is None:
            return None
        key = (column, sex)
        arr = self._norm_cache.get(key)
        if arr is None:
            arr = self._norm_cache.get((column, None))
        if arr is None or len(arr) < 10:
            return None
        return int(round(np.searchsorted(arr, value) / len(arr) * 100))

    def reset_buffers(self):
        self._waist_buf.clear()
        self._hip_buf.clear()
        self._fat_buf.clear()

    def _predict_fat(self, meas: dict):
        """
        meas: height_cm, weight_kg, bmi, age, sex_num, ve opsiyonel: arm/chest/waist/hip/neck
        Eksik olcumler np.nan olarak gonderilir, modelin imputer'i doldurur.
        """
        if not self.loaded:
            return None
        waist = meas.get("waist_cm")
        hip   = meas.get("hip_cm")
        whr   = (waist / max(hip, 1)) if waist and hip else np.nan
        whtr  = (waist / max(meas.get("height_cm", 170), 1)) if waist else np.nan

        row = [
            meas.get("height_cm",  np.nan),
            meas.get("weight_kg",  np.nan),
            meas.get("bmi",        np.nan),
            meas.get("age",        np.nan),
            meas.get("sex_num",    np.nan),
            meas.get("arm_cm",     np.nan),
            meas.get("chest_cm",   np.nan),
            waist if waist else np.nan,
            hip   if hip   else np.nan,
            meas.get("neck_cm",    np.nan),
            whr,
            whtr,
        ]
        X   = pd.DataFrame([row], columns=FEATURES)[self._fat_features]
        fat = float(self._fat_model.predict(X)[0])
        return round(max(3.0, min(60.0, fat)), 1)

    def _deurenberg(self, bmi, age, sex):
        """Fallback: BMI+yas+cinsiyet tahmini (kamera olcumu yokken)."""
        if sex == "M":
            fat = 1.20 * bmi + 0.23 * age - 16.2
        else:
            fat = 1.20 * bmi + 0.23 * age - 5.4
        return round(max(3.0, min(60.0, fat)), 1)

    def analyze(self, landmarks, W, H, profile, seg_mask=None):
        """
        profile: dict — zorunlu: height_cm, weight_kg, age, sex
                         opsiyonel: arm_cm, chest_cm, waist_cm, hip_cm, neck_cm
        seg_mask: float32 [H x W]
        """
        if not self.loaded:
            return None

        h   = float(profile.get("height_cm", 170))
        w   = float(profile.get("weight_kg",  70))
        age = int(profile.get("age", 25))
        sx  = str(profile.get("sex", "M")).upper()
        bmi = round(w / (h / 100) ** 2, 1)
        sex_num = 1.0 if sx == "M" else 0.0

        # Profil olcumleri (kullanici girdisi)
        prof_arm   = profile.get("arm_cm")
        prof_chest = profile.get("chest_cm")
        prof_waist = profile.get("waist_cm")
        prof_hip   = profile.get("hip_cm")
        prof_neck  = profile.get("neck_cm")

        # Kamera olcumleri
        if seg_mask is not None:
            measures = measure_from_segmentation(seg_mask, landmarks, W, H, h, w)
        else:
            measures = None

        if measures is None:
            return None

        dist_status = measures["dist_status"]
        dist_color  = measures["dist_color"]
        shr         = measures.get("shoulder_hip_ratio")
        sh_cm       = measures.get("shoulder_width_cm")

        cam_valid = (
            measures.get("waist_cm") is not None
            and measures.get("hip_cm") is not None
            and not measures.get("mask_invalid", False)
        )

        if cam_valid:
            self._waist_buf.append(measures["waist_cm"])
            self._hip_buf.append(measures["hip_cm"])

        cam_stable = len(self._waist_buf) >= 5

        # Bel/kalca: kamera > profil > None
        if cam_stable:
            used_waist = float(np.median(self._waist_buf))
            used_hip   = float(np.median(self._hip_buf))
            cam_used   = True
        elif prof_waist and prof_hip:
            used_waist = prof_waist
            used_hip   = prof_hip
            cam_used   = False
        else:
            used_waist = None
            used_hip   = None
            cam_used   = False

        # Olusan olcum paketini modele gonder
        meas_dict = {
            "height_cm": h,
            "weight_kg": w,
            "bmi":       bmi,
            "age":       float(age),
            "sex_num":   sex_num,
        }
        if used_waist: meas_dict["waist_cm"] = used_waist
        if used_hip:   meas_dict["hip_cm"]   = used_hip
        if prof_arm:   meas_dict["arm_cm"]   = prof_arm
        if prof_chest: meas_dict["chest_cm"] = prof_chest
        if prof_neck:  meas_dict["neck_cm"]  = prof_neck

        if self._fat_model is not None:
            fat_pct = self._predict_fat(meas_dict)
        else:
            fat_pct = self._deurenberg(bmi, age, sx)

        if fat_pct is None:
            return None

        self._fat_buf.append(fat_pct)
        stable_fat = round(float(np.median(self._fat_buf)), 1)

        # Gosterim icin olcumler
        if used_waist:
            disp_waist = round(used_waist, 1)
            disp_hip   = round(used_hip, 1)
        else:
            disp_waist = round(h * (0.390 + 0.0062 * bmi), 1)
            disp_hip   = round(h * (0.520 + 0.0038 * bmi), 1)

        # Persentiller
        pct_bmi   = self.percentile(bmi,        "bmi",      sx)
        pct_waist = self.percentile(disp_waist,  "waist_cm", sx)
        pct_hip   = self.percentile(disp_hip,    "hip_cm",   sx)
        pct_arm   = self.percentile(prof_arm,    "arm_cm",   sx) if prof_arm else None
        pct_chest = self.percentile(prof_chest,  "chest_cm", sx) if prof_chest else None

        return {
            "fat_pct":            stable_fat,
            "bmi":                bmi,
            "bmi_category":       bmi_category(bmi),
            "body_type":          classify_body_type(stable_fat, sx),
            "waist_cm":           disp_waist,
            "hip_cm":             disp_hip,
            "arm_cm":             prof_arm,
            "chest_cm":           prof_chest,
            "neck_cm":            prof_neck,
            "shoulder_width_cm":  sh_cm,
            "shoulder_hip_ratio": shr,
            "height_cm":          h,
            "weight_kg":          w,
            "dist_status":        dist_status,
            "dist_color":         dist_color,
            "cam_used":           cam_used,
            "stable":             len(self._fat_buf) >= BUFFER_SIZE,
            "pct_bmi":            pct_bmi,
            "pct_waist":          pct_waist,
            "pct_hip":            pct_hip,
            "pct_arm":            pct_arm,
            "pct_chest":          pct_chest,
        }
