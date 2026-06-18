import cv2
import numpy as np
from config import GREEN, RED, YELLOW, WHITE, BLACK, ORANGE, CYAN, GRAY, DARK

# ── Palette ───────────────────────────────────────────────────────────────────
_BG    = (14, 14, 20)
_PANEL = (28, 28, 42)
_PANL2 = (36, 36, 52)
_BORD  = (60, 60, 85)
_BORDB = (80, 80, 110)
_CYAN  = (255, 230, 30)     # BGR: bright cyan
_GRN   = (55, 220, 55)      # bright green
_RED   = (55, 55, 220)      # bright red
_WARN  = (30, 165, 255)     # orange
_GOLD  = (30, 210, 255)     # gold
_TXT1  = (228, 228, 238)    # primary text
_TXT2  = (128, 128, 148)    # secondary text
_TXT3  = (70,  70,  90)     # dim text
_GRND  = (30, 100, 30)      # dark green bg
_REDD  = (30, 30, 100)      # dark red bg


# ── Primitives ────────────────────────────────────────────────────────────────

def _blend(frame, x, y, w, h, color=_PANEL, alpha=0.85):
    x, y, w, h = int(x), int(y), int(w), int(h)
    if w <= 0 or h <= 0:
        return
    y2, x2 = min(y+h, frame.shape[0]), min(x+w, frame.shape[1])
    sub = frame[y:y2, x:x2]
    bg  = np.full_like(sub, color)
    cv2.addWeighted(bg, alpha, sub, 1-alpha, 0, sub)
    frame[y:y2, x:x2] = sub


def _panel(frame, x, y, w, h, color=_PANEL, alpha=0.88, border=None, bthick=1):
    _blend(frame, x, y, w, h, color, alpha)
    if border is not None:
        cv2.rectangle(frame, (int(x), int(y)), (int(x+w), int(y+h)), border, bthick)


def _txt(frame, text, x, y, color=_TXT1, scale=0.60, thick=1):
    cv2.putText(frame, text, (int(x), int(y)), cv2.FONT_HERSHEY_SIMPLEX,
                scale, BLACK, thick + 2, cv2.LINE_AA)
    cv2.putText(frame, text, (int(x), int(y)), cv2.FONT_HERSHEY_SIMPLEX,
                scale, color, thick, cv2.LINE_AA)


def _txc(frame, text, cx, y, color=_TXT1, scale=0.60, thick=1):
    tw = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, thick)[0][0]
    _txt(frame, text, int(cx - tw // 2), int(y), color, scale, thick)


def _bar(frame, x, y, w, h, ratio, fg=_GRN, bg=(35, 35, 50)):
    x, y, w, h = int(x), int(y), int(w), int(h)
    cv2.rectangle(frame, (x, y), (x+w, y+h), bg, -1)
    fill = int(w * max(0.0, min(1.0, ratio)))
    if fill > 0:
        cv2.rectangle(frame, (x, y), (x+fill, y+h), fg, -1)
    cv2.rectangle(frame, (x, y), (x+w, y+h), _BORD, 1)


def _divider(frame, x, y, w, color=_BORD):
    cv2.line(frame, (int(x), int(y)), (int(x+w), int(y)), color, 1)


def _pill(frame, cx, cy, text, bg_color, text_color, scale=0.55, thick=1, px=14, py=7):
    """Centered pill/badge."""
    tw, th = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, thick)[0]
    bw, bh = tw + px*2, th + py*2
    bx, by = cx - bw//2, cy - bh//2
    _blend(frame, bx, by, bw, bh, bg_color, 0.92)
    cv2.rectangle(frame, (bx, by), (bx+bw, by+bh), text_color, 1)
    _txt(frame, text, bx + px, by + py + th, text_color, scale, thick)


def _icon_dot(frame, x, y, r, color):
    cv2.circle(frame, (int(x), int(y)), r, color, -1)


# ── Session Summary ───────────────────────────────────────────────────────────

def draw_session_summary(frame, data):
    H, W = frame.shape[:2]

    # Full-screen dark overlay
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (W, H), _BG, -1)
    cv2.addWeighted(overlay, 0.78, frame, 0.22, 0, frame)

    # Card
    cw, ch = 560, 370
    cx, cy = W//2 - cw//2, H//2 - ch//2
    _panel(frame, cx, cy, cw, ch, _PANEL, 0.96, _BORD, 1)

    # Accent top bar
    ex_name = data.get("ex_name", "Egzersiz")
    reps    = data.get("reps", 0)
    dur_sec = data.get("dur_sec", 0)
    quality = data.get("quality", 0)
    tb      = data.get("time_based", False)

    q_color = (_GRN if quality >= 75 else _WARN if quality >= 50 else _RED)
    q_bg    = (_GRND if quality >= 75 else (0, 50, 80) if quality >= 50 else _REDD)

    _blend(frame, cx, cy, cw, 48, q_bg, 0.95)
    _txc(frame, "ANTRENMAN TAMAMLANDI", cx + cw//2, cy + 32, _TXT1, 0.78, 2)

    _divider(frame, cx + 16, cy + 52, cw - 32)

    # Exercise name
    _txc(frame, ex_name.upper(), cx + cw//2, cy + 88, _CYAN, 0.85, 2)

    # Three stat cards
    card_w, card_h = 148, 100
    gap = 18
    total_row = 3 * card_w + 2 * gap
    row_x = cx + (cw - total_row) // 2
    row_y = cy + 105

    stats = [
        ("SNY" if tb else "TEKRAR", str(reps),          _GRN,   _GRND),
        ("SURE",  f"{int(dur_sec)//60:02d}:{int(dur_sec)%60:02d}", _TXT1,  _PANEL),
        ("FORM",  f"%{quality}",       q_color, q_bg),
    ]
    for i, (lbl, val, vc, bc) in enumerate(stats):
        sx = row_x + i * (card_w + gap)
        _panel(frame, sx, row_y, card_w, card_h, bc, 0.92, _BORD)
        _txc(frame, lbl, sx + card_w//2, row_y + 20, _TXT2, 0.46, 1)
        _txc(frame, val, sx + card_w//2, row_y + 75, vc,   1.40, 3)

    _divider(frame, cx + 16, row_y + card_h + 12, cw - 32)

    msg = ("Mukemmel! Harika antrenman!" if quality >= 85
           else "Iyi gidiyorsun, devam et!" if quality >= 65
           else "Forma dikkat et, pratik yap!" if quality >= 40
           else "Daha fazla pratik gerekiyor!")
    _txc(frame, msg, cx + cw//2, row_y + card_h + 42, q_color, 0.62, 1)

    _txc(frame, "Herhangi bir tusa bas  |  Menuye don",
         cx + cw//2, cy + ch - 18, _TXT3, 0.46, 1)

    return frame


# ── Calibration overlay ───────────────────────────────────────────────────────

def draw_calibration(frame, n_done: int, n_total: int):
    H, W = frame.shape[:2]
    bh = 76
    _panel(frame, 0, H-bh, W, bh, (0, 22, 44), 0.92, (0, 180, 220), 2)
    title = f"KALIBRASYON: {n_done}/{n_total} tekrar tamamlandi"
    _txc(frame, title, W//2, H-bh+24, _CYAN, 0.66, 2)
    ratio = min(1.0, n_done / max(n_total, 1))
    _bar(frame, 40, H-bh+36, W-80, 12, ratio, (0, 200, 100))
    hint = "Normal tempo ve tam hareket araliginda egzersiz yapin.  ESC = iptal"
    _txc(frame, hint, W//2, H-10, _TXT2, 0.44, 1)
    return frame


# ── AI Recognition overlay ────────────────────────────────────────────────────

def draw_recognition_overlay(frame, detected_ex):
    if not detected_ex:
        return frame
    H, W = frame.shape[:2]
    label = detected_ex.replace("_", " ").upper()
    bw, bh = 240, 44
    bx, by = W - bw - 10, 10
    _panel(frame, bx, by, bw, bh, (20, 14, 36), 0.85, _CYAN, 1)
    _txt(frame, "AI  ", bx+10, by+28, _TXT3, 0.40, 1)
    _txt(frame, label,  bx+38, by+28, _CYAN,  0.52, 1)
    return frame


# ── Form label dict ───────────────────────────────────────────────────────────

FORM_LABEL_TR = {
    "correct":               "Form OK",
    "insufficient_range":    "Aralik Kisa",
    "asymmetric":            "Asimetri",
    "too_fast":              "Cok Hizli",
    "incomplete_extension":  "Eksik Uzanma",
}


# ── HUD (exercise screen) ─────────────────────────────────────────────────────

def draw_hud(frame, result, exercise_name, fps, audio_on, time_based=False,
             form_label=None, form_conf=0.0, data_collect=False, last_rep_ok=None):
    H, W = frame.shape[:2]
    p = 14

    # Colored border
    border_col = _GRN if result.is_correct else _RED
    cv2.rectangle(frame, (0, 0), (W-1, H-1), border_col, 5)

    # ── Top bar ───────────────────────────────────────────────────────────────
    top_bg = _GRND if result.is_correct else _REDD
    _blend(frame, 0, 0, W, 48, top_bg, 0.90)
    _divider(frame, 0, 48, W, _BORD)

    _txt(frame, exercise_name.upper(), p, 33, _CYAN, 0.72, 2)

    status_txt   = "DOGRU FORM" if result.is_correct else "HATALI FORM"
    status_col   = _GRN if result.is_correct else _RED
    _txc(frame, status_txt, W//2, 34, status_col, 0.78, 2)

    ses_txt = "SES: ON" if audio_on else "SES: OFF"
    _txt(frame, f"{ses_txt}   {fps:.0f} FPS", W - 185, 33, _TXT2, 0.48, 1)

    # ── Left panel: rep counter ───────────────────────────────────────────────
    pw, ph = 160, 210
    px, py = p, 58
    _panel(frame, px, py, pw, ph, _PANEL, 0.92, _BORD)

    _txt(frame, "SNY" if time_based else "TEKRAR", px+12, py+24, _TXT2, 0.48, 1)

    rep_col = _GRN if result.is_correct else _RED
    rep_str = str(result.rep_count)
    _txc(frame, rep_str, px + pw//2, py + 120, rep_col, 3.0, 5)

    phase_colors = {"UP": _GRN, "DOWN": _WARN, "IDLE": _TXT3}
    phase_col = phase_colors.get(result.phase, _TXT2)
    _txc(frame, result.phase, px + pw//2, py + 148, phase_col, 0.55, 1)

    # Phase indicator dots
    dot_y = py + 165
    dot_active = result.phase == "UP"
    _icon_dot(frame, px + pw//2 - 14, dot_y, 5, _GRN if dot_active else _TXT3)
    _icon_dot(frame, px + pw//2 + 14, dot_y, 5, _WARN if not dot_active and result.phase=="DOWN" else _TXT3)

    # Angle bar
    if result.primary_angle is not None:
        lo, hi = result.primary_range or (0, 180)
        ratio = max(0.0, min(1.0, (result.primary_angle - lo) / max(hi - lo, 1)))
        bar_col = _GRN if result.is_correct else (_WARN if result.warnings else _RED)
        _bar(frame, px+10, py+178, pw-20, 8, ratio, bar_col)
        _txt(frame, f"{result.primary_angle:.0f}", px+12, py+205, _TXT2, 0.44, 1)

    # ── Right panel: errors / warnings ───────────────────────────────────────
    n = len(result.errors) + len(result.warnings)
    if n > 0:
        ep_w, ep_x = 360, W - 374 - p
        ep_y = 58
        ep_h = n * 32 + 20
        _panel(frame, ep_x, ep_y, ep_w, ep_h, _PANEL, 0.92, _BORD)
        yo = ep_y + 26
        for e in result.errors:
            short = e[:46] + "..." if len(e) > 46 else e
            _icon_dot(frame, ep_x + 16, yo - 5, 5, _RED)
            _txt(frame, short, ep_x + 30, yo, _RED, 0.53, 1)
            yo += 32
        for w_ in result.warnings:
            short = w_[:46] + "..." if len(w_) > 46 else w_
            _icon_dot(frame, ep_x + 16, yo - 5, 5, _WARN)
            _txt(frame, short, ep_x + 30, yo, _WARN, 0.53, 1)
            yo += 32

    # ── Last rep result badge (4 sec) ─────────────────────────────────────────
    if last_rep_ok is True:
        bw2, bh2 = 210, 36
        bx2, by2 = W - bw2 - p, 58
        _panel(frame, bx2, by2, bw2, bh2, _GRND, 0.94, _GRN, 2)
        _txc(frame, "TEKRAR: DOGRU FORM", bx2 + bw2//2, by2 + 25, _GRN, 0.56, 1)
    elif last_rep_ok is False:
        bw2, bh2 = 210, 36
        bx2, by2 = W - bw2 - p, 58
        _panel(frame, bx2, by2, bw2, bh2, _REDD, 0.94, _RED, 2)
        _txc(frame, "TEKRAR: HATALI FORM", bx2 + bw2//2, by2 + 25, _RED, 0.56, 1)

    # ── Bottom bar: angles + hints ────────────────────────────────────────────
    _blend(frame, 0, H-52, W, 52, _BG, 0.88)
    _divider(frame, 0, H-52, W, _BORD)

    hint = "M:Menu  R:Sifirla  D:Veri  S:Ses  Q:Cikis"
    _txt(frame, hint, p, H-32, _TXT3, 0.44, 1)

    if result.angles:
        astr = "   |   ".join(f"{k}: {v:.1f}" for k, v in result.angles.items())
        _txt(frame, astr, p, H-10, _TXT2, 0.44, 1)

    if data_collect:
        _panel(frame, W-155, H-56, 148, 24, (0, 40, 0), 0.90, _GRN, 1)
        _txc(frame, "VERI TOPLANIYOR", W-155+74, H-38, _GRN, 0.46, 1)

    return frame


# ── Menu ──────────────────────────────────────────────────────────────────────

_EX_ICONS = {
    "biceps_curl":    "B",
    "triceps":        "T",
    "shoulder_press": "S",
    "lateral_raise":  "L",
    "fly":            "F",
    "bench_press":    "G",
}

_CARD_COLORS = [
    (255, 160, 20),   # blue-cyan
    (200, 80, 255),   # purple
    (50,  200, 255),  # orange
    (80,  255, 80),   # green
    (255, 80,  180),  # pink-blue
    (30,  210, 255),  # gold
]


def draw_menu(frame, exercises, selected=None, detected_ex=None,
              menu_detect_ex=None, menu_detect_hold=0, menu_detect_threshold=8):
    H, W = frame.shape[:2]

    # Dark overlay
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (W, H), _BG, -1)
    cv2.addWeighted(overlay, 0.65, frame, 0.35, 0, frame)

    # ── Title bar ─────────────────────────────────────────────────────────────
    _blend(frame, 0, 0, W, 58, (20, 14, 36), 0.92)
    _divider(frame, 0, 58, W, _BORD)
    _txc(frame, "EGZERSIZ FORM ANALIZI", W//2, 38, _CYAN, 0.92, 2)

    # ── AI detection bar ──────────────────────────────────────────────────────
    if menu_detect_ex:
        label = menu_detect_ex.replace("_", " ").upper()
        ratio = min(1.0, menu_detect_hold / max(menu_detect_threshold, 1))
        _blend(frame, W//2-200, 68, 400, 50, (20, 30, 50), 0.90)
        cv2.rectangle(frame, (W//2-200, 68), (W//2+200, 118), _CYAN, 1)
        _txc(frame, f"Algilandi: {label}", W//2, 88, _GRN, 0.58, 1)
        _bar(frame, W//2-180, 100, 360, 8, ratio, _GRN)
    else:
        _txc(frame, "Hareket yapin  |  AI otomatik baslatir", W//2, 82, _TXT2, 0.50, 1)
        _txc(frame, "veya asagidan bir egzersiz secin", W//2, 102, _TXT3, 0.44, 1)

    # ── Exercise card grid (2 columns) ────────────────────────────────────────
    ex_list = list(exercises.items())
    cols = 3
    card_w = (W - 80) // cols
    card_h = 64
    grid_x = 40
    grid_y = 128
    gap    = 8

    for idx, (key, (ex_id, name)) in enumerate(ex_list):
        col = idx % cols
        row = idx // cols
        cx_ = grid_x + col * (card_w + gap)
        cy_ = grid_y + row * (card_h + gap)

        sel = (key == selected)
        acc = _CARD_COLORS[idx % len(_CARD_COLORS)]
        bg  = (40, 40, 60) if not sel else (50, 40, 80)
        bord = acc if sel else _BORD

        _panel(frame, cx_, cy_, card_w, card_h, bg, 0.92, bord, 2 if sel else 1)

        # Key badge
        _blend(frame, cx_+8, cy_+10, 30, 28, acc if sel else (60,60,80), 0.88)
        cv2.rectangle(frame, (cx_+8, cy_+10), (cx_+38, cy_+38), acc, 1)
        _txc(frame, key, cx_+23, cy_+31, _TXT1 if not sel else WHITE, 0.55, 2 if sel else 1)

        # Name
        _txt(frame, name, cx_+48, cy_+38, acc if sel else _TXT1, 0.62, 2 if sel else 1)

    # ── Utility buttons row ───────────────────────────────────────────────────
    rows_used = (len(ex_list) + cols - 1) // cols
    util_y = grid_y + rows_used * (card_h + gap) + 16

    util_items = [
        ("B", "Vucut",      (255, 160, 80)),
        ("G", "Guc",        (30, 215, 255)),
        ("N", "Beslenme",   (80, 200, 80)),
        ("P", "Ilerleme",   (255, 80, 200)),
    ]
    uw = (W - 80) // len(util_items)
    for i, (k, lbl, col) in enumerate(util_items):
        ux = 40 + i * (uw + gap)
        _panel(frame, ux, util_y, uw, 48, (30, 30, 46), 0.90, col, 1)
        _txc(frame, f"[{k}] {lbl}", ux + uw//2, util_y + 30, col, 0.55, 1)

    # ── Bottom hint ────────────────────────────────────────────────────────────
    _blend(frame, 0, H-36, W, 36, _BG, 0.90)
    _divider(frame, 0, H-36, W, _BORD)
    _txc(frame, "M: Menuye don   Q: Cikis", W//2, H-10, _TXT3, 0.50, 1)

    return frame
