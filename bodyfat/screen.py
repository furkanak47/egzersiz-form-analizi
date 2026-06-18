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
_CYAN  = (255, 230, 30)
_GRN   = (55, 220, 55)
_RED   = (55, 55, 220)
_WARN  = (30, 165, 255)


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


def _txt(frame, text, x, y, color=_TXT1, scale=0.60, thick=1):
    cv2.putText(frame, text, (int(x), int(y)), cv2.FONT_HERSHEY_SIMPLEX,
                scale, BLACK, thick+2, cv2.LINE_AA)
    cv2.putText(frame, text, (int(x), int(y)), cv2.FONT_HERSHEY_SIMPLEX,
                scale, color, thick, cv2.LINE_AA)


def _txc(frame, text, cx, y, color=_TXT1, scale=0.60, thick=1):
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


def _fat_color(fat_pct, sex="M"):
    if sex == "M":
        if fat_pct < 14: return _GRN
        if fat_pct < 25: return _CYAN
        if fat_pct < 30: return _WARN
    else:
        if fat_pct < 21: return _GRN
        if fat_pct < 32: return _CYAN
        if fat_pct < 38: return _WARN
    return _RED


def _pct_tag(pct):
    return f" %{pct}ile" if pct is not None else ""


def _bad_high_col(pct):
    if pct is None:
        return None
    if pct > 75: return _RED
    if pct > 50: return _WARN
    return _GRN


def _good_high_col(pct):
    if pct is None:
        return None
    if pct > 60: return _GRN
    if pct > 30: return _CYAN
    return GRAY


def draw_body_hud(frame, result, profile, fps):
    H, W = frame.shape[:2]
    p  = 14
    sx = profile.get("sex", "M")

    # ── Top bar ───────────────────────────────────────────────────────────────
    _blend(frame, 0, 0, W, 52, (20, 14, 36), 0.92)
    _divider(frame, 0, 52, W)

    _txt(frame, "VUCUT ANALIZI", p, 35, _CYAN, 0.82, 2)
    name = profile.get("name", "")
    if name:
        _txc(frame, name[:20], W//2, 35, _TXT1, 0.56, 1)
    _txt(frame, f"M:Menu  B:Profil  Q:Cikis", W - 250, 35, _TXT3, 0.46, 1)
    _txt(frame, f"{fps:.0f} FPS", W - 60, 35, _TXT3, 0.44, 1)

    if result is None:
        cw, ch = 500, 100
        _panel(frame, W//2-cw//2, H//2-ch//2, cw, ch, _PANEL, 0.92, _WARN, 1)
        _txc(frame, "Tam vucut gorunur sekilde durun", W//2, H//2 - 8, YELLOW, 0.66, 1)
        _txc(frame, "Onerillen uzaklik: 1.5 — 2.5 metre", W//2, H//2 + 20, _TXT2, 0.52, 1)
        info = (f"Boy:{profile.get('height_cm',0):.0f}cm  "
                f"Kilo:{profile.get('weight_kg',0):.1f}kg  "
                f"{'Erkek' if sx=='M' else 'Kadin'}")
        _txc(frame, info, W//2, H//2 + 44, _TXT3, 0.46, 1)
        return frame

    fat_pct   = result["fat_pct"]
    fat_color = _fat_color(fat_pct, sx)
    stable    = result.get("stable", False)

    # ── Status strip ──────────────────────────────────────────────────────────
    dist_status = result.get("dist_status", "")
    dist_color  = result.get("dist_color",  _TXT2)
    stab_text   = "STABIL" if stable else "Olcuyor..."
    stab_col    = _GRN if stable else _WARN

    _blend(frame, 0, 52, W, 28, (20, 20, 32), 0.85)
    _txc(frame, dist_status, W//2, 70, dist_color, 0.52, 1)
    _txt(frame, stab_text, W - 120, 70, stab_col, 0.48, 1)
    _divider(frame, 0, 80, W)

    top = 88

    # ── Left panel: Fat % ─────────────────────────────────────────────────────
    lw, lh = 180, 185
    _panel(frame, p, top, lw, lh, _PANEL, 0.92, fat_color, 2)

    _txt(frame, "YAG ORANI", p+12, top+24, _TXT2, 0.48, 1)
    _txc(frame, f"%{fat_pct:.1f}", p + lw//2, top + 110, fat_color, 2.0, 4)
    _txc(frame, result["body_type"], p + lw//2, top + 142, fat_color, 0.56, 1)
    accuracy = "(hesaplaniyor...)" if not stable else "(+/- 4%)"
    _txc(frame, accuracy, p + lw//2, top + 164, _TXT3, 0.38, 1)

    # ── Middle panel: BMI ─────────────────────────────────────────────────────
    mw, mh = 180, 130
    mx = p + lw + 10
    bmi_color = (_GRN if result["bmi"] < 25 else _WARN if result["bmi"] < 30 else _RED)
    _panel(frame, mx, top, mw, mh, _PANEL, 0.92, bmi_color, 2)

    _txt(frame, "BMI", mx+12, top+24, _TXT2, 0.48, 1)
    _txc(frame, f"{result['bmi']:.1f}", mx+mw//2, top+90, bmi_color, 1.7, 3)
    _txc(frame, result["bmi_category"], mx+mw//2, top+116, bmi_color, 0.54, 1)

    pct_b = result.get("pct_bmi")
    if pct_b is not None:
        bmi_pct_col = _bad_high_col(pct_b)
        _panel(frame, mx, top+mh+8, mw, 48, _PANEL, 0.88, _BORD)
        _txc(frame, f"Nufusun %{pct_b}'inden", mx+mw//2, top+mh+28, bmi_pct_col or _TXT2, 0.40, 1)
        _txc(frame, "daha yuksek BMI",          mx+mw//2, top+mh+46, bmi_pct_col or _TXT2, 0.40, 1)

    # ── Right panel: Measurements ─────────────────────────────────────────────
    rw, rh = W - (p + lw + 10 + mw + 10) - p, 250
    rx = mx + mw + 10
    _panel(frame, rx, top, rw, rh, _PANEL, 0.92, _BORD)

    _txt(frame, "OLCUMLER", rx+12, top+24, _TXT2, 0.48, 1)

    cam_used = result.get("cam_used", False)
    src_tag  = "kamera" if cam_used else ("profil" if profile.get("waist_cm") else "tahmin")

    metrics = [
        ("Boy",   f"{result['height_cm']:.0f} cm",  _TXT1, False),
        ("Kilo",  f"{result['weight_kg']:.1f} kg",  _TXT1, False),
    ]

    wc, hc = result["waist_cm"], result["hip_cm"]
    pw, ph = result.get("pct_waist"), result.get("pct_hip")
    metrics.append(("Bel",   f"~{wc:.0f}cm{_pct_tag(pw)}",  _bad_high_col(pw) or _CYAN, False))
    metrics.append(("Kalca", f"~{hc:.0f}cm{_pct_tag(ph)}",  _bad_high_col(ph) or _CYAN, False))

    sc = result.get("shoulder_width_cm")
    if sc:
        metrics.append(("Omuz", f"~{sc:.0f} cm", _CYAN, False))

    ac = result.get("arm_cm")
    if ac:
        pa = result.get("pct_arm")
        metrics.append(("Kol", f"{ac:.0f}cm{_pct_tag(pa)}", _good_high_col(pa) or _CYAN, False))

    cc = result.get("chest_cm")
    if cc:
        pc = result.get("pct_chest")
        metrics.append(("Gogus", f"{cc:.0f}cm{_pct_tag(pc)}", _good_high_col(pc) or _CYAN, False))

    for j, (lbl, val, col, _) in enumerate(metrics):
        my = top + 40 + j * 26
        _txt(frame, f"{lbl:<7}", rx+12,        my, _TXT2, 0.46, 1)
        _txt(frame, val,          rx+12+75, my, col,  0.48, 1)

    shr = result.get("shoulder_hip_ratio") or 0
    if shr > 1.4:   shr_label, shr_col = "V-Sekil",     _GRN
    elif shr > 1.1: shr_label, shr_col = "Dengeli",     _CYAN
    else:           shr_label, shr_col = "Genis Kalca",  _WARN
    if shr > 0:
        _txt(frame, f"Sekil : {shr_label} ({shr:.2f})", rx+12, top+rh-26, shr_col, 0.44, 1)
    _txt(frame, f"~ kaynak: {src_tag}", rx+12, top+rh-8, _TXT3, 0.36, 1)

    # ── Fat % bar (bottom) ───────────────────────────────────────────────────
    bx, by, bw, bh = p, H-60, W-p*2, 18
    _bar(frame, bx, by, bw, bh, fat_pct / 40.0, fat_color)

    max_fat = 40.0
    for val in [10, 20, 30, 40]:
        xpos = bx + int(bw * val / max_fat)
        cv2.line(frame, (xpos, by), (xpos, by+bh), _BORD, 1)
        _txt(frame, f"{val}", xpos - 6, by - 3, _TXT3, 0.36, 1)

    fill = int(bw * min(fat_pct / max_fat, 1.0))
    _txt(frame, f"%{fat_pct:.1f}", bx + max(4, fill - 30), by + 13, WHITE, 0.44, 1)

    _blend(frame, 0, H-28, W, 28, _BG, 0.88)
    _divider(frame, 0, H-28, W)
    _txc(frame, "B: Profil Degistir   M: Menu   Q: Cikis", W//2, H-8, _TXT3, 0.46, 1)

    return frame


# ── Profile screens ───────────────────────────────────────────────────────────

_CREATE_FIELDS = [
    ("name",      "Profil Adi",         "ornek: Furkan",                True),
    ("height_cm", "Boy (cm)",           "ornek: 178",                   True),
    ("weight_kg", "Kilo (kg)",          "ornek: 72.5",                  True),
    ("age",       "Yas",                "ornek: 23",                    True),
    ("sex",       "Cinsiyet (E/K)",     "E=Erkek  K=Kadin",             True),
    ("activity",  "Aktivite",           "1-5  [ATLA]",                  False),
    ("waist_cm",  "Bel cevresi (cm)",   "ornek: 80  [ATLA]",            False),
    ("hip_cm",    "Kalca (cm)",         "ornek: 95  [ATLA]",            False),
    ("chest_cm",  "Gogus (cm)",         "ornek: 98  [ATLA]",            False),
    ("arm_cm",    "Kol (cm)",           "ornek: 33  [ATLA]",            False),
    ("neck_cm",   "Boyun (cm)",         "ornek: 38  [ATLA]",            False),
]

FIELD_KEYS = [f[0] for f in _CREATE_FIELDS]


def draw_profile_input(frame, profile_state):
    H, W = frame.shape[:2]

    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (W, H), _BG, -1)
    cv2.addWeighted(overlay, 0.80, frame, 0.20, 0, frame)

    _blend(frame, 0, 0, W, 52, (20, 14, 40), 0.94)
    _divider(frame, 0, 52, W)
    _txc(frame, "YENI PROFIL OLUSTUR", W//2, 34, _CYAN, 0.80, 2)

    current = profile_state.get("field", "name")
    values  = profile_state.get("values", {})
    buf     = profile_state.get("input_buf", "")

    try:
        cur_idx = FIELD_KEYS.index(current)
    except ValueError:
        cur_idx = 0

    # Progress bar
    ratio = (cur_idx + 1) / len(_CREATE_FIELDS)
    _bar(frame, 40, 56, W - 80, 6, ratio, _CYAN, (30, 30, 44))
    _txt(frame, f"{cur_idx+1}/{len(_CREATE_FIELDS)}", W - 100, 50, _TXT3, 0.42, 1)

    _blend(frame, 0, 64, W, 24, (20, 20, 32), 0.80)
    _txc(frame, "Opsiyonel alanlar bos birakılabilir — kamera olcer.",
         W//2, 78, _TXT3, 0.38, 1)

    top, row, gap = 90, 30, 2

    # Two-column layout (required | optional)
    required_fields = [(k, l, h, r) for k, l, h, r in _CREATE_FIELDS if r]
    optional_fields = [(k, l, h, r) for k, l, h, r in _CREATE_FIELDS if not r]

    col_w = W // 2 - 30

    for col_idx, field_group in enumerate([required_fields, optional_fields]):
        col_x = 20 + col_idx * (col_w + 20)
        col_label = "ZORUNLU ALANLAR" if col_idx == 0 else "OPSIYONEL ALANLAR"
        col_col   = _CYAN if col_idx == 0 else _TXT3
        _txt(frame, col_label, col_x + 8, top + 14, col_col, 0.44, 1)

        for j, (key, label, hint, required) in enumerate(field_group):
            y   = top + 22 + j * (row + gap)
            sel = (key == current)
            val = values.get(key, "")
            acc = _CYAN if required else _TXT2
            bg  = (40, 36, 60) if sel else (26, 26, 38)
            bord = _CYAN if sel else _BORD

            _panel(frame, col_x, y, col_w, row, bg, 0.88, bord, 2 if sel else 1)

            _txt(frame, label, col_x + 8, y + row - 9, acc if sel else _TXT2, 0.46, 1)

            display = (buf + "|") if sel else str(val)
            val_col = WHITE if sel else (_GRN if val else _TXT3)
            _txt(frame, display or ("—" if not required else ""),
                 col_x + col_w - 120, y + row - 9, val_col, 0.50, 1)

    hint_y = top + 22 + max(len(required_fields), len(optional_fields)) * (row + gap) + 12
    _panel(frame, W//2-250, hint_y, 500, 34, (26, 26, 38), 0.85, _BORD)
    _txc(frame, "ENTER: onayla / atla   ESC: iptal   * = zorunlu",
         W//2, hint_y + 23, _TXT2, 0.48, 1)

    return frame


