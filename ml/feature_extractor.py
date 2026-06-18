"""
Rep-bazli ozellik cikarici.

Bir tekrar boyunca toplanan frame-acilar listesini alir,
40-boyutlu bir ozellik vektoru dondurur.
"""

import numpy as np
from typing import List, Dict, Optional

# 8 standart aci — exercise_recognizer ile ayni sirа
ANGLE_KEYS = [
    'l_elbow', 'r_elbow',
    'l_shoulder', 'r_shoulder',
    'l_hip', 'r_hip',
    'l_knee', 'r_knee',
]

SYMMETRY_PAIRS = [
    ('l_elbow',   'r_elbow'),
    ('l_shoulder','r_shoulder'),
    ('l_hip',     'r_hip'),
    ('l_knee',    'r_knee'),
]

FEATURE_NAMES = (
    [f"{k}_{s}" for k in ANGLE_KEYS for s in ('min', 'max', 'mean', 'std')] +
    [f"sym_{lk[2:]}" for lk, _ in SYMMETRY_PAIRS] +
    ['rom', 'max_speed', 'phase_ratio', 'duration']
)
N_FEATURES = len(FEATURE_NAMES)   # 40


def landmarks_to_angles(landmarks) -> Dict[str, float]:
    """
    MediaPipe landmark listesinden 8 standart aci hesaplar.
    Doner: {'l_elbow': float, 'r_elbow': float, ...}
    """
    import mediapipe as mp
    _lm = mp.solutions.pose.PoseLandmark

    def pt(idx):
        lm = landmarks[idx]
        return (lm.x, lm.y)

    def _angle(a, b, c):
        ax, ay = a[0]-b[0], a[1]-b[1]
        cx, cy = c[0]-b[0], c[1]-b[1]
        n = (ax*ax+ay*ay)**0.5 * (cx*cx+cy*cy)**0.5 + 1e-8
        cos = (ax*cx + ay*cy) / n
        import math
        return math.degrees(math.acos(max(-1.0, min(1.0, cos))))

    L_SH, R_SH = _lm.LEFT_SHOULDER.value,  _lm.RIGHT_SHOULDER.value
    L_EL, R_EL = _lm.LEFT_ELBOW.value,     _lm.RIGHT_ELBOW.value
    L_WR, R_WR = _lm.LEFT_WRIST.value,     _lm.RIGHT_WRIST.value
    L_HI, R_HI = _lm.LEFT_HIP.value,       _lm.RIGHT_HIP.value
    L_KN, R_KN = _lm.LEFT_KNEE.value,      _lm.RIGHT_KNEE.value
    L_AN, R_AN = _lm.LEFT_ANKLE.value,     _lm.RIGHT_ANKLE.value

    def vis(idx):
        return landmarks[idx].visibility

    result = {}
    if min(vis(L_SH), vis(L_EL), vis(L_WR)) > 0.4:
        result['l_elbow']    = _angle(pt(L_SH), pt(L_EL), pt(L_WR))
    if min(vis(R_SH), vis(R_EL), vis(R_WR)) > 0.4:
        result['r_elbow']    = _angle(pt(R_SH), pt(R_EL), pt(R_WR))
    if min(vis(L_EL), vis(L_SH), vis(L_HI)) > 0.4:
        result['l_shoulder'] = _angle(pt(L_EL), pt(L_SH), pt(L_HI))
    if min(vis(R_EL), vis(R_SH), vis(R_HI)) > 0.4:
        result['r_shoulder'] = _angle(pt(R_EL), pt(R_SH), pt(R_HI))
    if min(vis(L_SH), vis(L_HI), vis(L_KN)) > 0.4:
        result['l_hip']      = _angle(pt(L_SH), pt(L_HI), pt(L_KN))
    if min(vis(R_SH), vis(R_HI), vis(R_KN)) > 0.4:
        result['r_hip']      = _angle(pt(R_SH), pt(R_HI), pt(R_KN))
    if min(vis(L_HI), vis(L_KN), vis(L_AN)) > 0.4:
        result['l_knee']     = _angle(pt(L_HI), pt(L_KN), pt(L_AN))
    if min(vis(R_HI), vis(R_KN), vis(R_AN)) > 0.4:
        result['r_knee']     = _angle(pt(R_HI), pt(R_KN), pt(R_AN))

    return result


def extract_rep_features(frames: List[Dict[str, float]],
                         primary: str = 'l_elbow') -> Optional[np.ndarray]:
    """
    frames : her biri {aci_adi: derece} olan frame listesi (bir tekrar boyunca)
    primary: hangi aci birincil metrik (ROM ve hiz icin)
    Doner : (N_FEATURES,) float32 array  veya  None (yetersiz veri)
    """
    if len(frames) < 5:
        return None

    feat: List[float] = []

    # 32 ozellik: her aci icin 4 istatistik
    for key in ANGLE_KEYS:
        vals = np.array([f.get(key, np.nan) for f in frames], dtype=np.float32)
        v    = vals[~np.isnan(vals)]
        if len(v) < 2:
            feat += [0.0, 180.0, 90.0, 0.0]
        else:
            feat += [float(v.min()), float(v.max()),
                     float(v.mean()), float(v.std())]

    # 4 ozellik: simetri (L-R ortalama mutlak fark)
    for lk, rk in SYMMETRY_PAIRS:
        lv = np.array([f.get(lk, np.nan) for f in frames])
        rv = np.array([f.get(rk, np.nan) for f in frames])
        m  = ~(np.isnan(lv) | np.isnan(rv))
        feat.append(float(np.abs(lv[m] - rv[m]).mean()) if m.sum() > 0 else 0.0)

    # ROM — birincil acinin aralik genisligi
    pv = np.array([f.get(primary, np.nan) for f in frames])
    pv = pv[~np.isnan(pv)]
    feat.append(float(pv.max() - pv.min()) if len(pv) > 1 else 0.0)

    # Maks hiz — frame-to-frame en buyuk aci degisimi
    feat.append(float(np.abs(np.diff(pv)).max()) if len(pv) > 1 else 0.0)

    # Faz orani — medyanin altinda gecirilen sure orani
    if len(pv) > 1:
        feat.append(float((pv < float(np.median(pv))).mean()))
    else:
        feat.append(0.5)

    # Sure — normalize edilmis frame sayisi
    feat.append(float(len(frames)) / 60.0)

    arr = np.array(feat, dtype=np.float32)
    if len(arr) != N_FEATURES:
        return None
    return arr
