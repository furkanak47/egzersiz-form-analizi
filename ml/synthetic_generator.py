"""
Sentetik form verisi uretici.

Her egzersiz icin 5 sinif (correct + 4 hata tipi) veri uretir.
Verileri data/form_data/{egzersiz}.csv dosyasina kaydeder.

Kullanim:
  python ml/synthetic_generator.py --exercise biceps_curl --samples 300
  python ml/synthetic_generator.py --all --samples 300
"""

import argparse
import numpy as np
import pandas as pd
from pathlib import Path

from ml.feature_extractor import extract_rep_features, FEATURE_NAMES

DATA_DIR = Path(__file__).parent.parent / "data" / "form_data"

LABELS = ['correct', 'insufficient_range', 'asymmetric', 'too_fast', 'incomplete_extension']

# --- Egzersiz profilleri ---
# down_angle: baslangic pozisyonu (genellikle kol/bacak uzatilmis)
# up_angle  : bitiis pozisyonu  (genellikle kas kontrakte)
# inverted  : True ise UP = buyuk aci (shoulder press, hip thrust vb.)
# primary   : birincil aci anahtari
# pair      : simetri cifti (sol, sag)

PROFILES = {
    # ---- Kol egzersizleri ----
    "biceps_curl": dict(
        primary="l_elbow", pair=("l_elbow","r_elbow"),
        down_angle=150.0, up_angle=40.0, inverted=False,
        rest=dict(l_shoulder=30, r_shoulder=30, l_hip=170, r_hip=170, l_knee=170, r_knee=170),
    ),
    "hammer_curl": dict(
        primary="l_elbow", pair=("l_elbow","r_elbow"),
        down_angle=150.0, up_angle=40.0, inverted=False,
        rest=dict(l_shoulder=30, r_shoulder=30, l_hip=170, r_hip=170, l_knee=170, r_knee=170),
    ),
    "triceps": dict(
        primary="l_elbow", pair=("l_elbow","r_elbow"),
        down_angle=65.0, up_angle=155.0, inverted=True,
        rest=dict(l_shoulder=60, r_shoulder=60, l_hip=170, r_hip=170, l_knee=170, r_knee=170),
    ),
    "shoulder_press": dict(
        primary="l_elbow", pair=("l_elbow","r_elbow"),
        down_angle=80.0, up_angle=160.0, inverted=True,
        rest=dict(l_shoulder=90, r_shoulder=90, l_hip=170, r_hip=170, l_knee=170, r_knee=170),
    ),
    "lateral_raise": dict(
        primary="l_shoulder", pair=("l_shoulder","r_shoulder"),
        down_angle=20.0, up_angle=75.0, inverted=True,
        rest=dict(l_elbow=170, r_elbow=170, l_hip=170, r_hip=170, l_knee=170, r_knee=170),
    ),
    # ---- Gögüs egzersizleri ----
    "bench_press": dict(
        primary="l_elbow", pair=("l_elbow","r_elbow"),
        down_angle=150.0, up_angle=80.0, inverted=False,
        rest=dict(l_shoulder=90, r_shoulder=90, l_hip=170, r_hip=170, l_knee=170, r_knee=170),
    ),
    "incline_bench_press": dict(
        primary="l_elbow", pair=("l_elbow","r_elbow"),
        down_angle=155.0, up_angle=80.0, inverted=False,
        rest=dict(l_shoulder=80, r_shoulder=80, l_hip=170, r_hip=170, l_knee=170, r_knee=170),
    ),
    "decline_bench_press": dict(
        primary="l_elbow", pair=("l_elbow","r_elbow"),
        down_angle=155.0, up_angle=75.0, inverted=False,
        rest=dict(l_shoulder=100, r_shoulder=100, l_hip=170, r_hip=170, l_knee=170, r_knee=170),
    ),
    "fly": dict(
        primary="l_shoulder", pair=("l_shoulder","r_shoulder"),
        down_angle=150.0, up_angle=60.0, inverted=False,
        rest=dict(l_elbow=160, r_elbow=160, l_hip=170, r_hip=170, l_knee=170, r_knee=170),
    ),
    # ---- Siirt / cekim ----
    "lat_pulldown": dict(
        primary="l_elbow", pair=("l_elbow","r_elbow"),
        down_angle=155.0, up_angle=65.0, inverted=False,
        rest=dict(l_shoulder=150, r_shoulder=150, l_hip=170, r_hip=170, l_knee=170, r_knee=170),
    ),
    "t_bar_row": dict(
        primary="l_elbow", pair=("l_elbow","r_elbow"),
        down_angle=155.0, up_angle=65.0, inverted=False,
        rest=dict(l_shoulder=60, r_shoulder=60, l_hip=120, r_hip=120, l_knee=170, r_knee=170),
    ),
    "pull_up": dict(
        primary="l_elbow", pair=("l_elbow","r_elbow"),
        down_angle=155.0, up_angle=70.0, inverted=False,
        rest=dict(l_shoulder=150, r_shoulder=150, l_hip=170, r_hip=170, l_knee=170, r_knee=170),
    ),
    # ---- Bacak / kalca ----
    "squat": dict(
        primary="l_knee", pair=("l_knee","r_knee"),
        down_angle=165.0, up_angle=90.0, inverted=False,
        rest=dict(l_elbow=170, r_elbow=170, l_shoulder=30, r_shoulder=30, l_hip=160, r_hip=160),
    ),
    "leg_extension": dict(
        primary="l_knee", pair=("l_knee","r_knee"),
        down_angle=85.0, up_angle=165.0, inverted=True,
        rest=dict(l_elbow=170, r_elbow=170, l_shoulder=30, r_shoulder=30, l_hip=90, r_hip=90),
    ),
    "leg_raises": dict(
        primary="l_hip", pair=("l_hip","r_hip"),
        down_angle=160.0, up_angle=65.0, inverted=False,
        rest=dict(l_elbow=170, r_elbow=170, l_shoulder=175, r_shoulder=175, l_knee=170, r_knee=170),
    ),
    "hip_thrust": dict(
        primary="l_hip", pair=("l_hip","r_hip"),
        down_angle=100.0, up_angle=165.0, inverted=True,
        rest=dict(l_elbow=170, r_elbow=170, l_shoulder=160, r_shoulder=160, l_knee=90, r_knee=90),
    ),
    # ---- Hip hinge ----
    "deadlift": dict(
        primary="l_hip", pair=("l_hip","r_hip"),
        down_angle=165.0, up_angle=70.0, inverted=False,
        rest=dict(l_elbow=170, r_elbow=170, l_shoulder=30, r_shoulder=30, l_knee=170, r_knee=170),
    ),
    "romanian_deadlift": dict(
        primary="l_hip", pair=("l_hip","r_hip"),
        down_angle=165.0, up_angle=75.0, inverted=False,
        rest=dict(l_elbow=170, r_elbow=170, l_shoulder=30, r_shoulder=30, l_knee=170, r_knee=170),
    ),
    # ---- Vucut agirlik ----
    "push_up": dict(
        primary="l_elbow", pair=("l_elbow","r_elbow"),
        down_angle=155.0, up_angle=85.0, inverted=False,
        rest=dict(l_shoulder=60, r_shoulder=60, l_hip=175, r_hip=175, l_knee=175, r_knee=175),
    ),
    "tricep_dips": dict(
        primary="l_elbow", pair=("l_elbow","r_elbow"),
        down_angle=155.0, up_angle=80.0, inverted=False,
        rest=dict(l_shoulder=30, r_shoulder=30, l_hip=170, r_hip=170, l_knee=170, r_knee=170),
    ),
}


def _sim_rep(down: float, up: float, n_frames: int,
             noise: float = 3.0, asym: float = 0.0) -> tuple:
    """
    Tek taraf icin yumusak bir tekrar simulasyonu.
    Doner: (l_seq, r_seq) — her biri uzunlugu n_frames olan numpy dizisi.
    """
    half = n_frames // 2
    # Cikis: DOWN → UP
    go_up   = np.linspace(down, up,   max(half, 2))
    # Donus: UP → DOWN
    go_down = np.linspace(up,   down, max(n_frames - half, 2))
    seq     = np.concatenate([go_up, go_down])[:n_frames]
    # Gauss gurultu
    seq_l = seq + np.random.normal(0, noise, n_frames)
    seq_r = seq + np.random.normal(0, noise, n_frames) + asym
    return seq_l, seq_r


def _build_frames(profile: dict, label: str, n_frames: int) -> list:
    """Bir tekrara ait frame listesi olusturur."""
    p   = profile
    d0  = p['down_angle']
    u0  = p['up_angle']
    lk, rk = p['pair']
    rest    = p.get('rest', {})

    # Hata parametrelerini uygula
    d, u, asym_offset, frames_n = d0, u0, 0.0, n_frames

    if label == 'insufficient_range':
        gap = abs(u0 - d0)
        if not p['inverted']:
            u = u0 + gap * 0.45     # UP'a tam ulasmiyor
        else:
            u = u0 - gap * 0.45
    elif label == 'asymmetric':
        asym_offset = 25.0          # bir taraf 25 derece geride
    elif label == 'too_fast':
        frames_n = max(8, n_frames // 3)
    elif label == 'incomplete_extension':
        gap = abs(d0 - u0)
        if not p['inverted']:
            d = d0 - gap * 0.35     # DOWN'a tam donmuyor
        else:
            d = d0 + gap * 0.35

    seq_l, seq_r = _sim_rep(d, u, frames_n, noise=3.5, asym=asym_offset)

    # Kisa repleri n_frames'e uzat
    if frames_n < n_frames:
        seq_l = np.pad(seq_l, (0, n_frames - frames_n), mode='edge')
        seq_r = np.pad(seq_r, (0, n_frames - frames_n), mode='edge')

    frames = []
    for i in range(n_frames):
        f = {k: v + np.random.normal(0, 1.5) for k, v in rest.items()}
        f[lk] = float(np.clip(seq_l[i], 0, 180))
        f[rk] = float(np.clip(seq_r[i], 0, 180))
        frames.append(f)
    return frames


def generate(exercise: str, samples_per_class: int = 300,
             noise_seed: int = 42) -> pd.DataFrame:
    """
    Bir egzersiz icin sentetik veri uretir.
    Doner: (N, N_FEATURES + 1) DataFrame, son sutun = 'label'
    """
    np.random.seed(noise_seed)
    profile = PROFILES.get(exercise)
    if profile is None:
        raise ValueError(f"Profil tanimli degil: {exercise}")

    rows, labels = [], []
    for label in LABELS:
        for _ in range(samples_per_class):
            n_frames = int(np.random.uniform(25, 65))
            frames   = _build_frames(profile, label, n_frames)
            feat     = extract_rep_features(frames, primary=profile['primary'])
            if feat is not None:
                rows.append(feat)
                labels.append(label)

    df = pd.DataFrame(rows, columns=FEATURE_NAMES)
    df['label'] = labels
    return df


def save(exercise: str, df: pd.DataFrame):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / f"{exercise}.csv"
    if path.exists():
        existing = pd.read_csv(path)
        df = pd.concat([existing, df], ignore_index=True)
    df.to_csv(path, index=False)
    print(f"  {exercise}: {len(df)} ornek kaydedildi → {path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--exercise", default=None)
    parser.add_argument("--all",      action="store_true")
    parser.add_argument("--samples",  type=int, default=300)
    args = parser.parse_args()

    targets = list(PROFILES.keys()) if args.all else (
              [args.exercise] if args.exercise else [])

    if not targets:
        print("--exercise <isim> veya --all kullan")
    else:
        for ex in targets:
            print(f"Uretiliyor: {ex}")
            try:
                df = generate(ex, samples_per_class=args.samples)
                save(ex, df)
                print(f"  Sinif dagilimi:\n{df['label'].value_counts().to_string()}\n")
            except ValueError as e:
                print(f"  ATLA: {e}")
