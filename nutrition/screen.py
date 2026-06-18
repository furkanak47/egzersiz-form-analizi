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
_TEAL  = (200, 220, 50)    # BGR teal
_PURP  = (220, 80, 200)
_GRN   = (55, 220, 55)
_RED   = (55, 55, 220)
_WARN  = (30, 165, 255)
_CYAN  = (255, 230, 30)

_GOAL_LABELS = {'maintain': 'Kilonu Koru', 'bulk': 'Kas Yap', 'cut': 'Yag Yak'}
_GOAL_COLS   = {'maintain': _CYAN, 'bulk': _GRN, 'cut': _WARN}

_MACRO_COLS = [
    ('Protein', 'protein_g', (80, 200, 255)),
    ('Karb',    'carb_g',    (50, 220, 50)),
    ('Yag',     'fat_g',     _PURP),
    ('Lif',     'fiber_g',   (180, 220, 50)),
]


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


def _txt(frame, text, x, y, color=_TXT1, scale=0.55, thick=1):
    cv2.putText(frame, text, (int(x), int(y)), cv2.FONT_HERSHEY_SIMPLEX,
                scale, BLACK, thick+2, cv2.LINE_AA)
    cv2.putText(frame, text, (int(x), int(y)), cv2.FONT_HERSHEY_SIMPLEX,
                scale, color, thick, cv2.LINE_AA)


def _txc(frame, text, cx, y, color=_TXT1, scale=0.55, thick=1):
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


def _ratio_color(ratio):
    if ratio >= 1.0: return _RED
    if ratio >= 0.85: return _WARN
    return _GRN


def draw_nutrition_hud(frame, entries, targets, profile, fps, day_str):
    from .tracker import daily_totals
    H, W = frame.shape[:2]
    p = 14

    totals = daily_totals(entries) if entries else \
             {'kcal': 0.0, 'protein_g': 0.0, 'carb_g': 0.0, 'fat_g': 0.0, 'fiber_g': 0.0}

    burned   = sum(abs(e['kcal']) for e in entries if e.get('kcal', 0) < 0)
    consumed = totals['kcal'] + burned
    net      = totals['kcal']

    tgt_kcal  = targets.get('kcal', 2000)
    goal      = targets.get('goal', 'maintain')

    # ── Top bar ───────────────────────────────────────────────────────────────
    _blend(frame, 0, 0, W, 52, (16, 24, 36), 0.94)
    _divider(frame, 0, 52, W)

    _txt(frame, "BESLENME", p, 35, _TEAL, 0.82, 2)
    name = profile.get('name', '')
    if name:
        _txc(frame, name[:18], W//2, 35, _TXT1, 0.54, 1)
    goal_lbl = _GOAL_LABELS.get(goal, 'Kilonu Koru')
    goal_col = _GOAL_COLS.get(goal, _CYAN)
    _txt(frame, f"[H] {goal_lbl}", W - 230, 35, goal_col, 0.46, 1)
    _txt(frame, day_str, W - 380, 35, _TXT3, 0.44, 1)
    _txt(frame, f"{fps:.0f} FPS", W - 58, 35, _TXT3, 0.42, 1)

    top = 60
    # ── Calorie card ──────────────────────────────────────────────────────────
    kcal_ratio = consumed / max(tgt_kcal, 1)
    kcal_col   = _ratio_color(kcal_ratio)
    kal_w, kal_h = 260, 100
    _panel(frame, p, top, kal_w, kal_h, _PANEL, 0.92, kcal_col, 2)

    _txt(frame, "KALORI",  p+12, top+20, _TXT2, 0.46, 1)
    _txt(frame, f"{consumed:.0f}", p+12, top+68, kcal_col, 1.30, 3)
    _txt(frame, f"/ {tgt_kcal:.0f} kcal", p+12+80, top+68, _TXT2, 0.50, 1)
    _bar(frame, p+10, top+78, kal_w-20, 10, kcal_ratio, kcal_col)
    if burned > 0:
        _txt(frame, f"Yakim: -{burned:.0f}  Net: {net:.0f}", p+12, top+96, _WARN, 0.42, 1)

    # ── Macro cards ───────────────────────────────────────────────────────────
    mac_start = p + kal_w + 10
    mac_w     = (W - mac_start - p) // 4
    gap       = 8

    for i, (label, key, col) in enumerate(_MACRO_COLS):
        tgt = targets.get(key, 1)
        val = totals.get(key, 0.0)
        rat = val / max(tgt, 1)
        rc  = _ratio_color(rat)

        mx_ = mac_start + i * (mac_w + gap)
        _panel(frame, mx_, top, mac_w, kal_h, _PANEL, 0.92, col, 1)
        _blend(frame, mx_, top, mac_w, 22, col, 0.18)

        _txc(frame, label,      mx_+mac_w//2, top+16,   col,  0.44, 1)
        _txc(frame, f"{val:.0f}g", mx_+mac_w//2, top+62, rc,   0.88, 2)
        _txc(frame, f"/{tgt:.0f}g",  mx_+mac_w//2, top+80, _TXT3, 0.40, 1)
        _bar(frame, mx_+8, top+86, mac_w-16, 8, rat, rc)

    # ── Food list ─────────────────────────────────────────────────────────────
    list_y = top + kal_h + 12
    list_h = H - list_y - 36
    _panel(frame, p, list_y, W-p*2, list_h, _PANEL, 0.88, _BORD)

    _txt(frame, "BUGUNUN OGUNLERI", p+12, list_y+18, _TXT2, 0.44, 1)
    _divider(frame, p+8, list_y+24, W-p*2-16)

    food_entries = [e for e in entries if e.get('kcal', 0) >= 0]
    if not food_entries:
        _txc(frame, "[A] tusuna basarak yemek ekleyin", W//2, list_y + list_h//2, YELLOW, 0.56, 1)
    else:
        visible = food_entries[-10:]
        row_h   = min(28, (list_h - 34) // max(len(visible), 1))
        for i, e in enumerate(visible):
            ry  = list_y + 32 + i * row_h
            is_last = (i == len(visible)-1)
            col = _TXT1 if is_last else _TXT2
            name_short = e['name'][:44]
            _txt(frame, f"{name_short}  {e.get('grams', 0):.0f}g", p+12, ry, col, 0.42, 1)
            _txt(frame, f"{abs(e['kcal']):.0f} kcal", W-120, ry, col, 0.42, 1)

    # ── Bottom hint ───────────────────────────────────────────────────────────
    _blend(frame, 0, H-30, W, 30, _BG, 0.90)
    _divider(frame, 0, H-30, W)
    _txc(frame, "[A] Ekle   [X] Sil   [H] Hedef   [<][>] Gun   [M] Menu",
         W//2, H-10, _TXT3, 0.46, 1)

    return frame


def draw_nutrition_search(frame, state):
    H, W = frame.shape[:2]

    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (W, H), _BG, -1)
    cv2.addWeighted(overlay, 0.85, frame, 0.15, 0, frame)

    _blend(frame, 0, 0, W, 52, (16, 24, 36), 0.94)
    _divider(frame, 0, 52, W)
    _txc(frame, "YEMEK EKLE", W//2, 34, _TEAL, 0.82, 2)
    _txt(frame, "ESC: Iptal", W-130, 34, _TXT3, 0.46, 1)

    phase = state.get('phase', 'search')

    if phase == 'search':
        query = state.get('query', '')
        # Search box
        _panel(frame, 20, 60, W-40, 40, (28, 36, 28), 0.92, _GRN, 1)
        _txt(frame, f"Ara: {query}|", 34, 86, WHITE, 0.68, 1)

        results = state.get('results', [])
        sel     = state.get('selected', 0)

        if not results and query:
            _txc(frame, "Sonuc bulunamadi", W//2, 140, YELLOW, 0.56, 1)
        elif not results:
            _txc(frame, "Gida adi yazin...", W//2, 140, _TXT2, 0.56, 1)
        else:
            for i, r in enumerate(results[:11]):
                ry  = 108 + i * 36
                sel_row = (i == sel)
                bg   = (32, 44, 32) if sel_row else _PANEL
                bord = _GRN if sel_row else _BORD
                _panel(frame, 20, ry, W-40, 34, bg, 0.90, bord, 2 if sel_row else 1)
                col = _TXT1 if sel_row else _TXT2
                _txt(frame, r['name'][:56], 34, ry+22, col, 0.50, 1)
                mac = (f"{r['kcal']:.0f}kcal  "
                       f"P:{r['protein_g']:.0f}g  "
                       f"K:{r['carb_g']:.0f}g  "
                       f"Y:{r['fat_g']:.0f}g  /100g")
                _txt(frame, mac, W-420, ry+22,
                     _CYAN if sel_row else _TXT3, 0.42, 1)

        _blend(frame, 0, H-36, W, 36, _BG, 0.90)
        _divider(frame, 0, H-36, W)
        _txc(frame, "Ok Yukari/Asagi: Gez   ENTER: Sec   ESC: Iptal",
             W//2, H-12, _TXT3, 0.48, 1)

    else:  # phase == 'grams'
        food = state.get('selected_food', {})
        buf  = state.get('grams_buf', '')
        err  = state.get('error', '')

        cw, ch = 540, 180
        cx, cy = W//2 - cw//2, H//2 - ch//2
        _panel(frame, cx, cy, cw, ch, _PANEL, 0.95, _GRN, 2)
        _blend(frame, cx, cy, cw, 36, _GRN, 0.16)

        _txt(frame, food.get('name', '')[:52], cx+16, cy+26, _TXT1, 0.56, 1)
        mac = (f"100g: {food.get('kcal',0):.0f}kcal  "
               f"P:{food.get('protein_g',0):.1f}g  "
               f"K:{food.get('carb_g',0):.1f}g  "
               f"Y:{food.get('fat_g',0):.1f}g")
        _txt(frame, mac, cx+16, cy+52, _CYAN, 0.46, 1)

        _divider(frame, cx+10, cy+62, cw-20)
        _txt(frame, "Miktar (gram):", cx+16, cy+92, _TXT2, 0.52, 1)
        _txt(frame, f"{buf}|", cx+160, cy+92, WHITE, 0.80, 2)

        if err:
            _panel(frame, cx+16, cy+106, cw-32, 28, (30,10,10), 0.90, _RED, 1)
            _txc(frame, err, cx+cw//2, cy+126, _RED, 0.48, 1)

        _txc(frame, "ENTER: Ekle   ESC: Geri", cx+cw//2, cy+ch-14, _TXT3, 0.48, 1)

    return frame
