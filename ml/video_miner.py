"""
YouTube video'dan egzersiz form verisi cikaran araç.

Gereksinimler:
  pip install yt-dlp opencv-python mediapipe pandas numpy

Kullanim:
  python ml/video_miner.py --url "https://youtu.be/..." --exercise biceps_curl --label correct
  python ml/video_miner.py --file path/to/video.mp4   --exercise squat         --label wrong
  python ml/video_miner.py --file path/to/video.mp4   --exercise biceps_curl   --auto

--auto: Tum video uzerinde otomatik rep tespit (gelismis; hata olursa --label kullan)
"""

import argparse
import sys
import os
import tempfile
from pathlib import Path
from typing import Optional, List, Dict, Tuple

import numpy as np
import cv2
import pandas as pd

from ml.feature_extractor import landmarks_to_angles, extract_rep_features, FEATURE_NAMES
from ml.data_collector import DataCollector, VALID_LABELS

DATA_DIR = Path(__file__).parent.parent / "data" / "form_data"

# MediaPipe pose
try:
    import mediapipe as mp
    _mp_pose = mp.solutions.pose
    _MP_OK   = True
except ImportError:
    _MP_OK = False


# ─── Yardimci ──────────────────────────────────────────────────────────────────

def _download_video(url: str) -> Optional[str]:
    """yt-dlp ile videoyu indirip gecici dosyaya kaydeder. Doner: dosya yolu."""
    try:
        import yt_dlp
    except ImportError:
        print("yt-dlp bulunamadi. Yukle: pip install yt-dlp")
        return None

    tmp = tempfile.mktemp(suffix=".mp4")
    ydl_opts = {
        # ffmpeg gerektirmeyen tek-dosya format (merge yok)
        "format": "best[height<=720][ext=mp4]/best[height<=720]/best",
        "outtmpl": tmp,
        "quiet": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    if Path(tmp).exists():
        return tmp
    # yt-dlp bazen uzanti ekler
    for ext in (".mp4", ".mkv", ".webm"):
        candidate = tmp + ext
        if Path(candidate).exists():
            return candidate
    return None


def _process_video(
    video_path: str,
    exercise: str,
    label: str,
    skip_frames: int = 2,
    min_rep_frames: int = 20,
    verbose: bool = True,
) -> int:
    """
    Videoyu kareteker isler, ropleri ayirir, ozellikleri cikarir,
    data/form_data/{exercise}.csv dosyasina ekler.
    Doner: kaydedilen rep sayisi.
    """
    if not _MP_OK:
        print("mediapipe yuklu degil.")
        return 0

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Video acilamadi: {video_path}")
        return 0

    fps      = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total    = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if verbose:
        print(f"Video: {Path(video_path).name}  fps={fps:.1f}  kare={total}")

    all_reps: List[List[Dict[str, float]]] = []
    cur_rep:  List[Dict[str, float]] = []

    # Basit rep tespiti: birincil aci (l_elbow) medyan etrafinda gecis sayma
    primary_key   = "l_elbow"
    angle_history: List[float] = []
    last_cross    = "none"    # "above" / "below"
    cross_count   = 0

    pose = _mp_pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    frame_idx = 0
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

        angles = landmarks_to_angles(results.pose_landmarks.landmark)
        if not angles:
            continue

        cur_rep.append(angles)
        pval = angles.get(primary_key)
        if pval is not None:
            angle_history.append(pval)

        # Medyan guncelleme
        if len(angle_history) >= 30:
            med = float(np.median(angle_history[-60:]))
            state = "above" if pval > med else "below"
            if state != last_cross:
                cross_count += 1
                last_cross = state
                if cross_count % 2 == 0 and len(cur_rep) >= min_rep_frames:
                    all_reps.append(cur_rep.copy())
                    cur_rep = []

    # Son birikmiş kareyi ekle
    if len(cur_rep) >= min_rep_frames:
        all_reps.append(cur_rep)

    cap.release()
    pose.close()

    if verbose:
        print(f"  Bulunan rep: {len(all_reps)}")

    if not all_reps:
        return 0

    dc = DataCollector(exercise, primary=primary_key)
    saved = 0
    for rep_frames in all_reps:
        dc.start_rep()
        for f in rep_frames:
            dc.add_frame(f)
        if dc.finish_rep(label):
            saved += 1
    written = dc.save()
    if verbose:
        print(f"  Kaydedilen rep: {written}")
    return written


# ─── Otomatik rep/sinif tahmini (gelismis, opsiyonel) ─────────────────────────

def _auto_label(video_path: str, exercise: str, verbose: bool = True) -> int:
    """
    Model varsa her bulunan rep icin form kalite tahmini yapar ve CSV'ye ekler.
    Model yoksa tum repleri 'correct' olarak kaydeder (manuel duzeltme icin).
    """
    try:
        from ml.form_classifier import FormClassifier
        fc = FormClassifier(exercise)
        has_model = fc.is_available
    except Exception:
        has_model = False

    if not _MP_OK:
        print("mediapipe yuklu degil.")
        return 0

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Video acilamadi: {video_path}")
        return 0

    dc = DataCollector(exercise)
    primary_key = "l_elbow"
    angle_history: List[float] = []
    last_cross = "none"
    cur_frames: List[Dict] = []
    saved = 0

    pose = _mp_pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_idx += 1
        if frame_idx % 3 != 0:
            continue

        rgb     = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb)
        if not results.pose_landmarks:
            continue

        angles = landmarks_to_angles(results.pose_landmarks.landmark)
        if not angles:
            continue

        cur_frames.append(angles)
        pval = angles.get(primary_key)
        if pval is None:
            continue

        angle_history.append(pval)
        if len(angle_history) < 30:
            continue

        med   = float(np.median(angle_history[-60:]))
        state = "above" if pval > med else "below"
        if state != last_cross:
            last_cross = state
            if len(cur_frames) >= 20:
                # Tahmini yap veya varsayilan label kullan
                if has_model:
                    for f in cur_frames:
                        fc.add_frame(f)
                    lbl, conf = fc.finalize_rep()
                    fc.reset()
                    if lbl is None or conf < 0.55:
                        lbl = "correct"
                else:
                    lbl = "correct"

                dc.start_rep()
                for f in cur_frames:
                    dc.add_frame(f)
                if dc.finish_rep(lbl):
                    saved += 1
                cur_frames = []

    cap.release()
    pose.close()
    written = dc.save()
    if verbose:
        print(f"  Otomatik etiket: {written} rep kaydedildi")
    return written


# ─── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Video'dan form verisi cikart")
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--url",  help="YouTube URL")
    src.add_argument("--file", help="Yerel video dosyasi")

    parser.add_argument("--exercise", required=True, help="Egzersiz id (ornek: biceps_curl)")
    lbl = parser.add_mutually_exclusive_group(required=True)
    lbl.add_argument("--label", choices=VALID_LABELS, help="Manuel etiket")
    lbl.add_argument("--auto",  action="store_true",  help="Otomatik etiketleme")

    parser.add_argument("--skip", type=int, default=2, help="Atlanan kare sayisi (varsayilan 2)")
    args = parser.parse_args()

    if not _MP_OK:
        print("mediapipe yuklu degil: pip install mediapipe")
        sys.exit(1)

    video_path = args.file
    tmp_file   = None

    if args.url:
        print(f"Video indiriliyor: {args.url}")
        video_path = _download_video(args.url)
        if not video_path:
            print("Indirme basarisiz.")
            sys.exit(1)
        tmp_file = video_path
        print(f"Indirildi: {video_path}")

    if args.auto:
        n = _auto_label(video_path, args.exercise)
    else:
        n = _process_video(video_path, args.exercise, args.label, skip_frames=args.skip)

    print(f"\nToplam kaydedilen rep: {n}")

    if tmp_file and Path(tmp_file).exists():
        os.remove(tmp_file)
