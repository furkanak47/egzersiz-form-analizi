"""
Toplu video isleyici — egzersiz videolarini CSV'ye donusturur ve model egitir.

Her video icin:
  - MediaPipe ile iskelet cikarilir
  - Egzersiz motoru (analyze) ile rep tespiti ve form kalitesi belirlenir
  - Her rep: framelerin %60'i dogru ise "correct", yoksa "wrong" etiketi
  - Ozellikler data/form_data/{exercise}.csv dosyasina eklenir

Kullanim:
  python tools/batch_video_processor.py
  python tools/batch_video_processor.py --video-dir "C:/yol/videolar" --retrain
  python tools/batch_video_processor.py --exercise biceps_curl --retrain
  python tools/batch_video_processor.py --clear-existing --retrain
"""

import argparse
import sys
import time
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Type

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import cv2
import numpy as np

from ml.feature_extractor import landmarks_to_angles
from ml.data_collector import DataCollector

try:
    import mediapipe as mp
    _MP_OK = True
except ImportError:
    _MP_OK = False
    print("HATA: mediapipe yuklu degil. Yukle: pip install mediapipe")

# ─── Video dizini ──────────────────────────────────────────────────────────────

DEFAULT_VIDEO_DIR = ROOT / "veri" / "egzersiz_videolari"
DATA_DIR          = ROOT / "data" / "form_data"
VIDEO_EXTS        = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".MOV"}

# ─── Egzersiz sinif yukleme ────────────────────────────────────────────────────

def _load_exercise_map() -> Dict[str, Tuple[str, type]]:
    """
    Doner: {video_klasor_adi: (exercise_id, ExerciseClass)}
    TIME_BASED egzersizler (Plank) dahil edilmez.
    """
    m: Dict[str, Tuple[str, type]] = {}

    def _try(folder: str, ex_id: str, module: str, cls: str):
        try:
            mod = __import__(f"exercises.{module}", fromlist=[cls])
            klass = getattr(mod, cls)
            if not getattr(klass, "TIME_BASED", False):
                m[folder] = (ex_id, klass)
        except Exception:
            pass

    _try("barbell biceps curl",  "biceps_curl",         "biceps_curl",         "BicepsCurl")
    _try("bench press",          "bench_press",          "bench_press",         "BenchPress")
    _try("chest fly machine",    "fly",                  "fly",                 "Fly")
    _try("deadlift",             "deadlift",             "deadlift",            "Deadlift")
    _try("decline bench press",  "decline_bench_press",  "decline_bench_press", "DeclineBenchPress")
    _try("hammer curl",          "hammer_curl",           "hammer_curl",         "HammerCurl")
    _try("hip thrust",           "hip_thrust",            "hip_thrust",          "HipThrust")
    _try("incline bench press",  "incline_bench_press",  "incline_bench_press", "InclineBenchPress")
    _try("lat pulldown",         "lat_pulldown",          "lat_pulldown",        "LatPulldown")
    _try("lateral raise",        "lateral_raise",         "lateral_raise",       "LateralRaise")
    _try("leg extension",        "leg_extension",         "leg_extension",       "LegExtension")
    _try("leg raises",           "leg_raises",            "leg_raises",          "LegRaises")
    _try("pull Up",              "pull_up",              "pull_up",             "PullUp")
    _try("push-up",              "push_up",              "push_up",             "PushUp")
    _try("romanian deadlift",    "romanian_deadlift",    "romanian_deadlift",   "RomanianDeadlift")
    _try("russian twist",        "russian_twist",        "russian_twist",       "RussianTwist")
    _try("shoulder press",       "shoulder_press",       "shoulder_press",      "ShoulderPress")
    _try("squat",                "squat",                "squat",               "Squat")
    _try("t bar row",            "t_bar_row",             "t_bar_row",           "TBarRow")
    _try("tricep dips",          "tricep_dips",           "tricep_dips",         "TricepDips")
    _try("tricep Pushdown",      "triceps",              "triceps",             "Triceps")
    return m


# ─── Egzersiz basi birincil aci anahtari ──────────────────────────────────────
# Medyan-kesisim rep tespiti icin hangi acinin izlenecegini belirler.

_PRIMARY_KEY: Dict[str, str] = {
    "biceps_curl":        "l_elbow",
    "hammer_curl":        "l_elbow",
    "triceps":            "l_elbow",
    "bench_press":        "l_elbow",
    "incline_bench_press":"l_elbow",
    "decline_bench_press":"l_elbow",
    "shoulder_press":     "l_elbow",
    "fly":                "l_elbow",
    "lat_pulldown":       "l_elbow",
    "pull_up":            "l_elbow",
    "t_bar_row":          "l_elbow",
    "push_up":            "l_elbow",
    "tricep_dips":        "l_elbow",
    "lateral_raise":      "l_shoulder",
    "squat":              "l_knee",
    "deadlift":           "l_knee",
    "romanian_deadlift":  "l_knee",
    "leg_extension":      "l_knee",
    "hip_thrust":         "l_knee",
    "leg_raises":         "l_hip",
    "russian_twist":      "l_shoulder",
}

_ANGLE_FALLBACK_ORDER = [
    "l_elbow", "r_elbow", "l_knee", "r_knee", "l_shoulder", "r_shoulder",
    "l_hip", "r_hip",
]


def _pick_primary(exercise_id: str, angles: Dict[str, float]) -> Optional[str]:
    """Egzersiz icin en uygun aci anahtarini dondurur."""
    preferred = _PRIMARY_KEY.get(exercise_id)
    if preferred and preferred in angles:
        return preferred
    for k in _ANGLE_FALLBACK_ORDER:
        if k in angles:
            return k
    return None


# ─── Tek video isleme ──────────────────────────────────────────────────────────

def process_video(
    video_path: Path,
    exercise_id: str,
    ExerciseClass: type,
    dc: DataCollector,
    skip_frames: int = 2,
    min_rep_frames: int = 10,
    correct_threshold: float = 0.6,
    verbose: bool = True,
) -> Tuple[int, int]:
    """
    Bir videoyu isler, ropleri DataCollector'a ekler.

    Rep tespiti: medyan-kesisim yontemi (adaptif esik — katı acı esiklerinden bagimsiz).
    Etiketleme : exercise.analyze() ile her frame icin is_correct oylama.
    Doner      : (correct_count, wrong_count)
    """
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        if verbose:
            print(f"    [HATA] Video acilamadi: {video_path.name}")
        return 0, 0

    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    if w == 0 or h == 0:
        w, h = 640, 480

    exercise = ExerciseClass()
    exercise.reset()

    pose = mp.solutions.pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    angle_history: List[float] = []   # birincil aci gecmisi (medyan icin)
    last_cross    = "none"            # "above" / "below"
    cross_count   = 0
    primary_key: Optional[str] = None

    cur_frames: List[Dict[str, float]] = []
    cur_votes:  List[bool]             = []
    correct_cnt = wrong_cnt = 0
    frame_idx   = 0

    def _flush_rep():
        nonlocal correct_cnt, wrong_cnt
        if len(cur_frames) < min_rep_frames:
            return
        ratio = sum(cur_votes) / max(len(cur_votes), 1)
        label = "correct" if ratio >= correct_threshold else "wrong"
        dc.start_rep()
        for f in cur_frames:
            dc.add_frame(f)
        if dc.finish_rep(label):
            if label == "correct":
                correct_cnt += 1
            else:
                wrong_cnt += 1

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_idx += 1
        if frame_idx % (skip_frames + 1) != 0:
            continue

        rgb     = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb)
        if not results.pose_landmarks:
            continue

        lm     = results.pose_landmarks.landmark
        angles = landmarks_to_angles(lm)
        if not angles:
            continue

        # Birincil aciyi ilk basarili frame'den al
        if primary_key is None:
            primary_key = _pick_primary(exercise_id, angles)

        # is_correct oylama — uyari da yanlış sayilir (katı form kriteri)
        try:
            form_result = exercise.analyze(lm, w, h)
            is_ok = (len(form_result.errors) == 0 and len(form_result.warnings) == 0)
        except Exception:
            is_ok = True   # hata durumunda tarafsiz say

        cur_frames.append(angles)
        cur_votes.append(is_ok)

        # Medyan-kesisim rep tespiti
        pval = angles.get(primary_key) if primary_key else None
        if pval is None:
            continue

        angle_history.append(pval)
        if len(angle_history) < 20:
            continue

        med   = float(np.median(angle_history[-60:]))
        state = "above" if pval > med else "below"

        if state != last_cross:
            cross_count += 1
            last_cross   = state

            # Her iki kesisim = 1 tam rep (asagi-yukari veya yukari-asagi)
            if cross_count % 2 == 0:
                _flush_rep()
                cur_frames = []
                cur_votes  = []

    cap.release()
    pose.close()
    return correct_cnt, wrong_cnt


# ─── Egzersiz toplu isleme ─────────────────────────────────────────────────────

def process_exercise(
    folder: Path,
    exercise_id: str,
    ExerciseClass: type,
    skip_frames: int,
    clear_existing: bool,
    verbose: bool,
) -> Tuple[int, int]:
    """Bir egzersiz klasorunun tum videolarini isler."""

    videos = [f for f in folder.iterdir() if f.suffix.lower() in {e.lower() for e in VIDEO_EXTS}]
    if not videos:
        if verbose:
            print(f"  [{exercise_id}] Video bulunamadi, atlaniyor.")
        return 0, 0

    if clear_existing:
        csv_path = DATA_DIR / f"{exercise_id}.csv"
        if csv_path.exists():
            csv_path.unlink()
            if verbose:
                print(f"  [{exercise_id}] Mevcut CSV silindi.")

    dc = DataCollector(exercise_id)
    total_correct = total_wrong = 0

    for i, vid in enumerate(sorted(videos), 1):
        if verbose:
            print(f"  [{exercise_id}] ({i}/{len(videos)}) {vid.name} ...", end=" ", flush=True)
        t0 = time.time()
        c, w = process_video(vid, exercise_id, ExerciseClass, dc,
                              skip_frames=skip_frames, verbose=False)
        elapsed = time.time() - t0
        total_correct += c
        total_wrong   += w
        if verbose:
            print(f"correct={c} wrong={w} ({elapsed:.1f}s)")

    saved = dc.save()
    if verbose:
        ratio = f"{total_correct}C / {total_wrong}W"
        print(f"  [{exercise_id}] Toplam {saved} rep kaydedildi ({ratio})\n")
    return total_correct, total_wrong


# ─── Model egitimi ─────────────────────────────────────────────────────────────

def retrain(exercise_ids: List[str], verbose: bool = True):
    from ml.trainer import train_exercise
    ok = 0
    for ex in exercise_ids:
        if train_exercise(ex, verbose=verbose):
            ok += 1
    print(f"\nModel egitimi: {ok}/{len(exercise_ids)} basarili.")


# ─── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Toplu video isleyici")
    parser.add_argument("--video-dir",       default=str(DEFAULT_VIDEO_DIR),
                        help="Video ana klasoru (varsayilan: veri/egzersiz_videolari)")
    parser.add_argument("--exercise",        default=None,
                        help="Sadece bu egzersizi isle (ornek: biceps_curl)")
    parser.add_argument("--skip-frames",     type=int, default=2,
                        help="Her N+1 kareden biri islenir (varsayilan: 2 → her 3. kare)")
    parser.add_argument("--clear-existing",  action="store_true",
                        help="Mevcut CSV verilerini silip sifirdan baslat")
    parser.add_argument("--retrain",         action="store_true",
                        help="CSV'ler olusturulduktan sonra modelleri egit")
    parser.add_argument("-q", "--quiet",     action="store_true")
    args = parser.parse_args()

    if not _MP_OK:
        sys.exit(1)

    video_root = Path(args.video_dir)
    if not video_root.exists():
        print(f"HATA: Video klasoru bulunamadi: {video_root}")
        sys.exit(1)

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    exercise_map = _load_exercise_map()
    verbose      = not args.quiet

    if verbose:
        print(f"Video klasoru : {video_root}")
        print(f"Yuklenen motor: {len(exercise_map)} egzersiz")
        skipped = []
        for f in sorted(video_root.iterdir()):
            if f.is_dir() and f.name not in exercise_map:
                skipped.append(f.name)
        if skipped:
            print(f"Atlanan       : {', '.join(skipped)}")
        print()

    # Hangi egzersizleri isliyoruz?
    if args.exercise:
        # --exercise ile belirtilmis egzersiz ID'sini klasor haritasindan bul
        targets = {
            folder: (ex_id, cls)
            for folder, (ex_id, cls) in exercise_map.items()
            if ex_id == args.exercise
        }
        if not targets:
            print(f"HATA: '{args.exercise}' icin video klasoru bulunamadi.")
            print(f"Bilinen klasorler: {list(exercise_map.keys())}")
            sys.exit(1)
    else:
        targets = exercise_map

    processed_ids: List[str] = []
    grand_correct = grand_wrong = 0

    for folder_name, (ex_id, ExCls) in sorted(targets.items()):
        folder_path = video_root / folder_name
        if not folder_path.exists():
            if verbose:
                print(f"  [{ex_id}] Klasor yok: {folder_path.name}, atlaniyor.\n")
            continue

        if verbose:
            print(f"=== {folder_name} -> {ex_id} ===")

        c, w = process_exercise(
            folder        = folder_path,
            exercise_id   = ex_id,
            ExerciseClass = ExCls,
            skip_frames   = args.skip_frames,
            clear_existing= args.clear_existing,
            verbose       = verbose,
        )
        grand_correct += c
        grand_wrong   += w
        if c + w > 0:
            processed_ids.append(ex_id)

    print(f"\n{'='*50}")
    print(f"Tamamlandi: {len(processed_ids)} egzersiz islendi")
    print(f"Toplam rep : {grand_correct + grand_wrong}  "
          f"(correct={grand_correct}, wrong={grand_wrong})")

    if args.retrain and processed_ids:
        print(f"\nModel egitimi basliyor ({len(processed_ids)} egzersiz)...\n")
        retrain(processed_ids, verbose=verbose)


if __name__ == "__main__":
    main()
