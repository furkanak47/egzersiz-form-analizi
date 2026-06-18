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
_GOLD  = (30, 210, 255)
_GRN   = (55, 220, 55)
_RED   = (55, 55, 220)
_CYAN  = (255, 230, 30)

_LIFT_ACC = {
    'squat':    (255, 200, 50),
    'bench':    (200, 80, 255),
    'deadlift': (30,  180, 255),
}
LIFT_LABELS = {'squat': 'SQUAT', 'bench': 'BENCH', 'deadlift': 'DEADLIFT'}


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


def draw_strength_input(frame, state):
    H, W = frame.shape[:2]

    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (W, H), _BG, -1)
    cv2.addWeighted(overlay, 0.80, frame, 0.20, 0, frame)

    # Title bar
    _blend(frame, 0, 0, W, 52, (20, 14, 40), 0.94)
    _divider(frame, 0, 52, W)
    _txc(frame, "GUC ANALIZI  —  Kaldirislari Gir", W//2, 34, _GOLD, 0.80, 2)
    _txt(frame, "0 = yapilmadi / atla", W-230, 34, _TXT3, 0.44, 1)

    fields = [
        ('squat',    'SQUAT',    'kg'),
        ('bench',    'BENCH',    'kg'),
        ('deadlift', 'DEADLIFT', 'kg'),
    ]

    current = state.get('field', 'squat')
    values  = state.get('values', {})
    buf     = state.get('input_buf', '')
    err     = state.get('error', '')

    card_h = 72
    top    = 72
    gap    = 10

    for i, (key, label, unit) in enumerate(fields):
        y   = top + i * (card_h + gap)
        sel = (key == current)
        acc = _LIFT_ACC[key]
        bg  = (40, 36, 60) if sel else (26, 26, 38)
        bord = acc if sel else _BORD

        _panel(frame, 40, y, W-80, card_h, bg, 0.92, bord, 2 if sel else 1)

        # Lift name badge
        _blend(frame, 50, y+10, 90, 36, acc if sel else (50, 50, 70), 0.85)
        cv2.rectangle(frame, (50, y+10), (140, y+46), acc, 1)
        _txc(frame, label, 95, y+34, WHITE if sel else _TXT2, 0.55, 2 if sel else 1)

        # Input area
        val = values.get(key)
        if sel:
            display = (buf or '') + '|'
            _txt(frame, display, W//2 - 60, y + 46, WHITE, 0.90, 2)
            _txt(frame, unit, W//2 + 30, y + 46, _TXT2, 0.55, 1)
        elif val is not None:
            col = _TXT3 if val == 0 else acc
            disp = '— (atlandi)' if val == 0 else f'{val:.1f} {unit}'
            _txt(frame, disp, W//2 - 60, y + 46, col, 0.72, 1)

        # Right: prev value hint
        if not sel and val and val > 0:
            _txt(frame, "kaydedildi", W - 170, y + 28, _TXT3, 0.40, 1)

    if err:
        ey = top + len(fields) * (card_h + gap) + 10
        _panel(frame, W//2-180, ey, 360, 36, (30, 10, 10), 0.92, _RED, 1)
        _txc(frame, err, W//2, ey + 24, _RED, 0.52, 1)

    hint_y = top + len(fields) * (card_h + gap) + 58
    _panel(frame, W//2-240, hint_y, 480, 36, (26, 26, 38), 0.85, _BORD)
    _txc(frame, "ENTER: onayla    0 + ENTER: atla    ESC: iptal",
         W//2, hint_y + 24, _TXT2, 0.50, 1)

    return frame


def draw_strength_hud(frame, result, profile, fps):
    H, W = frame.shape[:2]
    p = 14

    # Top bar
    _blend(frame, 0, 0, W, 52, (20, 18, 36), 0.92)
    _divider(frame, 0, 52, W)

    _txt(frame, "GUC ANALIZI", p, 35, _GOLD, 0.82, 2)

    name = profile.get('name', '')
    sex  = 'E' if profile.get('sex', 'M') == 'M' else 'K'
    bw   = profile.get('weight_kg', '')
    if name:
        info = f"{name[:16]}  {bw}kg  {sex}" if bw else name[:20]
        _txc(frame, info, W//2, 35, _TXT1, 0.54, 1)

    _txt(frame, f"G:Gir  M:Menu  Q:Cikis", W - 210, 35, _TXT3, 0.46, 1)
    _txt(frame, f"{fps:.0f} FPS", W - 60, 35, _TXT3, 0.44, 1)

    if not result:
        cw, ch = 460, 80
        _panel(frame, W//2-cw//2, H//2-ch//2, cw, ch, _PANEL, 0.92, _BORD)
        _txc(frame, "G tusuna bas ve kaldirislari gir", W//2, H//2 + 8, YELLOW, 0.66, 1)
        return frame

    # ── Lift cards ────────────────────────────────────────────────────────────
    LIFT_ORDER = ['squat', 'bench', 'deadlift']
    gap = 10
    total_w = W - p*2
    cw3 = (total_w - gap*2) // 3

    for i, lift in enumerate(LIFT_ORDER):
        cx = p + i * (cw3 + gap)
        cy = 62
        ch = 215
        acc = _LIFT_ACC[lift]

        if lift not in result:
            _panel(frame, cx, cy, cw3, ch, _PANEL, 0.88, _BORD)
            _txc(frame, LIFT_LABELS[lift], cx+cw3//2, cy+25, _TXT3, 0.55, 1)
            _txc(frame, "—", cx+cw3//2, cy+100, _TXT3, 1.2, 2)
            _txc(frame, "girilmedi", cx+cw3//2, cy+130, _TXT3, 0.46, 1)
            continue

        data = result[lift]
        lc   = data['color']
        pct  = data['pct']

        _panel(frame, cx, cy, cw3, ch, _PANEL, 0.92, acc, 2)

        # Accent header
        _blend(frame, cx, cy, cw3, 32, acc, 0.18)
        _txc(frame, LIFT_LABELS[lift], cx+cw3//2, cy+22, acc, 0.58, 2)

        # Big weight
        _txc(frame, f"{data['kg']:.0f}", cx+cw3//2, cy+100, _TXT1, 1.6, 3)
        _txt(frame, "kg", cx+cw3//2+10, cy+100, _TXT2, 0.50, 1)

        # Level badge
        _blend(frame, cx+16, cy+112, cw3-32, 26, lc, 0.20)
        cv2.rectangle(frame, (cx+16, cy+112), (cx+cw3-16, cy+138), lc, 1)
        _txc(frame, data['level'], cx+cw3//2, cy+130, lc, 0.52, 1)

        _txc(frame, f"%{pct} persentil", cx+cw3//2, cy+158, lc, 0.48, 1)
        _txc(frame, "Raw / Dogal sporcu",  cx+cw3//2, cy+175, _TXT3, 0.38, 1)

        _bar(frame, cx+12, cy+185, cw3-24, 10, pct/100, lc)

    # ── DOTS panel ────────────────────────────────────────────────────────────
    if 'dots' in result:
        d  = result['dots']
        dy = 62 + 215 + 10
        dh = 72
        _panel(frame, p, dy, W-p*2, dh, _PANEL, 0.92, d['color'], 2)

        _txt(frame, "DOTS  |  Vucut agirligina gore normalize toplam kuvvet",
             p+14, dy+22, _TXT3, 0.40, 1)

        score_str = f"{d['score']:.1f}"
        tw = cv2.getTextSize(score_str, cv2.FONT_HERSHEY_SIMPLEX, 1.10, 2)[0][0]
        _txt(frame, score_str, p+14, dy+62, _GOLD, 1.10, 2)
        _txt(frame, d['level'],   p+14+tw+14, dy+62, d['color'], 0.68, 1)
        _txt(frame, f"%{d['pct']} persentil", p+14+tw+160, dy+62, d['color'], 0.56, 1)
        _bar(frame, p+14+tw+300, dy+50, W-p*2-tw-330, 12, d['pct']/100, d['color'])

    # Bottom hint
    _blend(frame, 0, H-32, W, 32, _BG, 0.88)
    _divider(frame, 0, H-32, W)
    _txc(frame, "G: Yeniden gir   M: Menu   Q: Cikis", W//2, H-10, _TXT3, 0.46, 1)

    return frame
