import cv2
import numpy as np
from config import GREEN, RED, YELLOW, WHITE, BLACK, CYAN, GRAY, ORANGE

# ── Palette ───────────────────────────────────────────────────────────────────
_BG    = (14, 14, 20)
_PANEL = (28, 28, 42)
_BORD  = (60, 60, 85)
_TXT1  = (228, 228, 238)
_TXT2  = (128, 128, 148)
_TXT3  = (70,  70,  90)
_TEAL  = (200, 220, 50)
_GOLD  = (30, 210, 255)
_PURP  = (220, 80, 200)
_GRN   = (55, 220, 55)
_RED   = (55, 55, 220)
_WARN  = (30, 165, 255)
_CYAN  = (255, 230, 30)
_GRN2  = (60, 180, 60)

TABS = ["Egzersiz", "Vucut", "Guc"]

EX_COLORS = {
    "biceps_curl":    (255, 180, 0),
    "triceps":        (0, 200, 255),
    "shoulder_press": (180, 100, 255),
    "lateral_raise":  (0, 255, 180),
    "fly":            (0, 160, 255),
    "bench_press":    ORANGE,
}
EX_LABELS = {
    "biceps_curl":    "Biceps",
    "triceps":        "Triceps",
    "shoulder_press": "Omuz",
    "lateral_raise":  "Yan Kaldirma",
    "fly":            "Fly",
    "bench_press":    "Gogus Press",
}


def _blend(frame, x, y, w, h, color=_PANEL, alpha=0.88):
    x, y, w, h = int(x), int(y), int(w), int(h)
    if w <= 0 or h <= 0:
        return
    y2, x2 = min(y+h, frame.shape[0]), min(x+w, frame.shape[1])
    sub = frame[y:y2, x:x2]
    bg  = np.full_like(sub, color)
    cv2.addWeighted(bg, alpha, sub, 1-alpha, 0, sub)
    frame[y:y2, x:x2] = sub


def _panel(frame, x, y, w, h, color=_PANEL, alpha=0.90, border=None, bthick=1):
    _blend(frame, x, y, w, h, color, alpha)
    if border is not None:
        cv2.rectangle(frame, (int(x), int(y)), (int(x+w), int(y+h)), border, bthick)


def _txt(frame, text, x, y, color=_TXT1, scale=0.50, thick=1):
    cv2.putText(frame, text, (int(x), int(y)), cv2.FONT_HERSHEY_SIMPLEX,
                scale, BLACK, thick+2, cv2.LINE_AA)
    cv2.putText(frame, text, (int(x), int(y)), cv2.FONT_HERSHEY_SIMPLEX,
                scale, color, thick, cv2.LINE_AA)


def _txc(frame, text, cx, y, color=_TXT1, scale=0.50, thick=1):
    tw = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, thick)[0][0]
    _txt(frame, text, int(cx - tw//2), int(y), color, scale, thick)


def _bar(frame, x, y, w, h, ratio, color, bg=(35, 35, 50)):
    x, y, w, h = int(x), int(y), int(w), int(h)
    cv2.rectangle(frame, (x, y), (x+w, y+h), bg, -1)
    fill = int(w * max(0.0, min(1.0, ratio)))
    if fill > 0:
        cv2.rectangle(frame, (x, y), (x+fill, y+h), color, -1)
    cv2.rectangle(frame, (x, y), (x+w, y+h), _BORD, 1)


def _divider(frame, x, y, w, color=_BORD):
    cv2.line(frame, (int(x), int(y)), (int(x+w), int(y)), color, 1)


def _line_chart(frame, points, x, y, w, h, color, label="", unit="", fmt="%.1f"):
    x, y, w, h = int(x), int(y), int(w), int(h)
    cv2.rectangle(frame, (x, y), (x+w, y+h), (38, 38, 52), -1)
    cv2.rectangle(frame, (x, y), (x+w, y+h), _BORD, 1)

    if not points:
        _txc(frame, "Veri yok", x + w//2, y + h//2 + 6, _TXT3, 0.44)
        return

    vals = [v for _, v in points]
    mn, mx_v = min(vals), max(vals)
    if mx_v == mn:
        mn -= 1; mx_v += 1
    span = mx_v - mn

    def to_px(i, v):
        fx = x + 4 + int(i * (w - 8) / max(len(points) - 1, 1))
        fy = y + h - 4 - int((v - mn) / span * (h - 8))
        return (fx, fy)

    # Grid
    for step in [0.25, 0.5, 0.75]:
        gy = y + h - 4 - int(step * (h - 8))
        cv2.line(frame, (x+1, gy), (x+w-1, gy), (48, 48, 64), 1)
        gv = mn + step * span
        _txt(frame, fmt % gv, x+3, gy-2, _TXT3, 0.30, 1)

    # Lines + dots
    for i in range(len(points) - 1):
        cv2.line(frame, to_px(i, vals[i]), to_px(i+1, vals[i+1]), color, 2, cv2.LINE_AA)
    for i, v in enumerate(vals):
        pt = to_px(i, v)
        cv2.circle(frame, pt, 4, color, -1)
        cv2.circle(frame, pt, 4, WHITE, 1)

    # Last value
    lp = to_px(len(points)-1, vals[-1])
    _txt(frame, (fmt+unit) % vals[-1], lp[0]-20, lp[1]-6, color, 0.38, 1)

    if label:
        _txt(frame, label, x+4, y-4, color, 0.40, 1)


def _bar_chart(frame, date_reps, x, y, w, h, color):
    x, y, w, h = int(x), int(y), int(w), int(h)
    cv2.rectangle(frame, (x, y), (x+w, y+h), (38, 38, 52), -1)
    cv2.rectangle(frame, (x, y), (x+w, y+h), _BORD, 1)

    if not date_reps:
        _txc(frame, "Veri yok", x + w//2, y + h//2 + 6, _TXT3, 0.44)
        return

    dates = sorted(date_reps.keys())[-20:]
    vals  = [date_reps[d] for d in dates]
    mx_v  = max(vals) or 1
    bar_w = max(4, (w - 4) // len(dates) - 2)

    for i, (d, v) in enumerate(zip(dates, vals)):
        bx_ = x + 2 + i * (bar_w + 2)
        bh_ = int(v / mx_v * (h - 20))
        by_ = y + h - bh_ - 2
        cv2.rectangle(frame, (bx_, by_), (bx_ + bar_w, y + h - 2), color, -1)
        if v > 0:
            _txt(frame, str(v), bx_, by_ - 2, WHITE, 0.28, 1)

    _txt(frame, dates[0][5:],   x + 2,     y + h + 12, _TXT3, 0.32, 1)
    _txt(frame, dates[-1][5:],  x + w - 35, y + h + 12, _TXT3, 0.32, 1)


# ── Tabs ──────────────────────────────────────────────────────────────────────

def _draw_tabs(frame, W, active):
    tab_w = 160
    tx0   = W//2 - (len(TABS) * tab_w) // 2
    for i, name in enumerate(TABS):
        tx  = tx0 + i * tab_w
        sel = (i == active)
        tab_colors = [_TEAL, _WARN, _GOLD]
        acc = tab_colors[i]
        bg  = (32, 40, 32) if sel else (24, 24, 36)
        _panel(frame, tx, 54, tab_w - 2, 28, bg, 0.92,
               acc if sel else _BORD, 2 if sel else 1)
        _txc(frame, name, tx + tab_w//2, 74, acc if sel else _TXT2,
             0.54, 2 if sel else 1)


# ── Tab content ───────────────────────────────────────────────────────────────

def _draw_exercise_tab(frame, history, W, H):
    p   = 14
    top = 90

    if not history:
        cw, ch = 500, 80
        _panel(frame, W//2-cw//2, H//2-ch//2, cw, ch, _PANEL, 0.92, _BORD)
        _txc(frame, "Henuz egzersiz kaydedilmedi.", W//2, H//2, YELLOW, 0.58, 1)
        _txc(frame, "Rep yapinca otomatik kaydedilir.", W//2, H//2+24, _TXT2, 0.46, 1)
        return

    by_ex = {}
    for e in history:
        ex  = e["exercise_id"]
        day = e["date"]
        by_ex.setdefault(ex, {}).setdefault(day, 0)
        by_ex[ex][day] += e["reps"]

    all_days = {}
    for e in history:
        all_days.setdefault(e["date"], 0)
        all_days[e["date"]] += e["reps"]

    chart_h = 130
    _panel(frame, p, top, W-p*2, chart_h+20, _PANEL, 0.88, _BORD)
    _txt(frame, "TOPLAM REP  (son 20 gun)", p+12, top+16, _TXT2, 0.44, 1)
    _bar_chart(frame, all_days, p+10, top+22, W-p*2-20, chart_h-4, _GRN2)

    summary_y = top + chart_h + 28
    items = [(ex, sum(dr.values())) for ex, dr in by_ex.items()]
    items.sort(key=lambda x_: -x_[1])

    cols = 3
    col_w = (W - p*2) // cols
    row_h = 56

    for i, (ex_id, total) in enumerate(items[:6]):
        c    = i % cols
        r    = i // cols
        bx_  = p + c * col_w
        by_  = summary_y + r * (row_h + 8)
        lbl  = EX_LABELS.get(ex_id, ex_id)
        clr  = EX_COLORS.get(ex_id, _TXT1)

        _panel(frame, bx_, by_, col_w-6, row_h, _PANEL, 0.88, clr, 1)
        _blend(frame, bx_, by_, col_w-6, 18, clr, 0.14)
        _txt(frame, lbl,         bx_+10, by_+14, clr,   0.46, 1)
        _txt(frame, f"{total} rep", bx_+10, by_+44, _TXT1, 0.60, 2)


def _draw_body_tab(frame, history, W, H):
    p   = 14
    top = 90

    if len(history) < 2:
        cw, ch = 500, 80
        _panel(frame, W//2-cw//2, H//2-ch//2, cw, ch, _PANEL, 0.92, _BORD)
        msg = "Yeterli veri yok (en az 2 olcum)." if history else "Vucut analizi yapinca kaydedilir."
        _txc(frame, msg, W//2, H//2+8, YELLOW, 0.56, 1)
        return

    pts_fat = [(e["date"], e["fat_pct"])   for e in history]
    pts_w   = [(e["date"], e["weight_kg"]) for e in history]
    pts_bmi = [(e["date"], e["bmi"])       for e in history]

    half_w = (W - p*3) // 2
    ch_    = (H - top - 52) // 2 - 10

    # Fat chart
    _panel(frame, p, top, half_w, ch_, _PANEL, 0.88, _BORD)
    _line_chart(frame, pts_fat, p+8, top+18, half_w-16, ch_-24,
                _RED, "Yag Orani", "%", "%.1f")

    # Weight chart
    _panel(frame, p*2+half_w, top, half_w, ch_, _PANEL, 0.88, _BORD)
    _line_chart(frame, pts_w, p*2+half_w+8, top+18, half_w-16, ch_-24,
                _CYAN, "Kilo", "kg", "%.1f")

    # BMI chart
    mid_y = top + ch_ + 14
    _panel(frame, p, mid_y, half_w, ch_, _PANEL, 0.88, _BORD)
    _line_chart(frame, pts_bmi, p+8, mid_y+18, half_w-16, ch_-24,
                YELLOW, "BMI", "", "%.1f")

    # Last summary card
    sx = p*2 + half_w
    last = history[-1]
    _panel(frame, sx, mid_y, half_w, ch_, _PANEL, 0.92, _BORD)
    _txt(frame, "SON OLCUM", sx+12, mid_y+18, _TXT2, 0.44, 1)
    _divider(frame, sx+8, mid_y+24, half_w-16)

    rows = [
        ("Tarih",  last["date"],                   _TXT2, 0.46),
        ("Yag",    f"%.1f%%" % last["fat_pct"],    _RED,  0.58),
        ("Kilo",   f"%.1f kg" % last["weight_kg"], _CYAN, 0.58),
        ("BMI",    f"%.1f" % last["bmi"],           YELLOW, 0.58),
    ]
    for j, (lbl, val, col, sc) in enumerate(rows):
        ry = mid_y + 34 + j * 28
        _txt(frame, f"{lbl:<7}", sx+12, ry, _TXT2, 0.44, 1)
        _txt(frame, val, sx+90, ry, col, sc, 2 if j > 0 else 1)

    if len(history) >= 2:
        fat_d = last["fat_pct"] - history[0]["fat_pct"]
        w_d   = last["weight_kg"] - history[0]["weight_kg"]
        cf = _GRN if fat_d < 0 else (_TXT3 if fat_d == 0 else _RED)
        cw_ = _GRN if w_d < 0 else (_TXT3 if w_d == 0 else _RED)
        sf = "+" if fat_d >= 0 else ""
        sw = "+" if w_d   >= 0 else ""
        _txt(frame, f"Yag  : {sf}{fat_d:.1f}%", sx+12, mid_y+ch_-30, cf,  0.44, 1)
        _txt(frame, f"Kilo : {sw}{w_d:.1f}kg",  sx+12, mid_y+ch_-12, cw_, 0.44, 1)


def _draw_strength_tab(frame, history, W, H):
    p   = 14
    top = 90

    if not history:
        cw, ch = 500, 70
        _panel(frame, W//2-cw//2, H//2-ch//2, cw, ch, _PANEL, 0.92, _BORD)
        _txc(frame, "Guc analizi yapinca otomatik kaydedilir.", W//2, H//2+8, YELLOW, 0.56, 1)
        return

    pts_total = [(e["date"], e["squat"]+e["bench"]+e["deadlift"])
                 for e in history if e["squat"]+e["bench"]+e["deadlift"] > 0]
    pts_dots  = [(e["date"], e["dots"]) for e in history if e["dots"] > 0]

    lift_cols = {"squat": _CYAN, "bench": _PURP, "deadlift": _WARN}
    lift_lbls = {"squat": "SQUAT", "bench": "BENCH", "deadlift": "DEADLIFT"}

    ch_   = (H - top - 52) // 2 - 10
    third = (W - p*4) // 3

    # Total trend
    _panel(frame, p, top, third*2+p, ch_, _PANEL, 0.88, _BORD)
    _line_chart(frame, pts_total, p+8, top+18, third*2+p-16, ch_-24,
                _GRN2, "Toplam (S+B+D)", "kg", "%.0f")

    # DOTS
    _panel(frame, p*3+third*2, top, third, ch_, _PANEL, 0.88, _BORD)
    _line_chart(frame, pts_dots, p*3+third*2+8, top+18, third-16, ch_-24,
                _GOLD, "Dots", "", "%.1f")

    # Per-lift trend cards
    mid_y = top + ch_ + 14
    col_w = (W - p*2) // 3
    last  = history[-1]

    for i, lift in enumerate(["squat", "bench", "deadlift"]):
        bx_ = p + i * col_w
        clr = lift_cols[lift]
        _panel(frame, bx_, mid_y, col_w-8, ch_, _PANEL, 0.90, clr, 2)
        _blend(frame, bx_, mid_y, col_w-8, 22, clr, 0.16)
        _txc(frame, lift_lbls[lift], bx_+(col_w-8)//2, mid_y+16, clr, 0.52, 2)

        pts_lift = [(e["date"], e[lift]) for e in history if e[lift] > 0]
        if len(pts_lift) >= 2:
            _line_chart(frame, pts_lift,
                        bx_+8, mid_y+26, col_w-24, ch_-48, clr, "", "kg", "%.0f")

        val = last[lift]
        val_str = f"{val:.0f} kg" if val > 0 else "Girilmedi"
        _txc(frame, val_str, bx_+(col_w-8)//2, mid_y+ch_-10,
             clr if val > 0 else _TXT3, 0.58, 2 if val > 0 else 1)


# ── Main ─────────────────────────────────────────────────────────────────────

def draw_progress_hud(frame, profile, ex_history, body_history, str_history, tab, fps):
    H, W = frame.shape[:2]

    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (W, H), _BG, -1)
    cv2.addWeighted(overlay, 0.65, frame, 0.35, 0, frame)

    # Title bar
    _blend(frame, 0, 0, W, 52, (16, 20, 36), 0.94)
    _divider(frame, 0, 52, W)
    _txt(frame, "ILERLEME", 14, 35, _TEAL, 0.82, 2)
    name = profile.get("name", "")
    if name:
        _txc(frame, name[:20], W//2, 35, _TXT1, 0.54, 1)
    _txt(frame, f"{fps:.0f} FPS", W-58, 35, _TXT3, 0.42, 1)

    _draw_tabs(frame, W, tab)

    if tab == 0:
        _draw_exercise_tab(frame, ex_history, W, H)
    elif tab == 1:
        _draw_body_tab(frame, body_history, W, H)
    elif tab == 2:
        _draw_strength_tab(frame, str_history, W, H)

    _blend(frame, 0, H-30, W, 30, _BG, 0.90)
    _divider(frame, 0, H-30, W)
    _txc(frame, "[<][>] Sekme   [M] Menu   [Q] Cikis", W//2, H-10, _TXT3, 0.46, 1)

    return frame
