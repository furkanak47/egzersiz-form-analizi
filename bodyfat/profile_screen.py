import cv2
import numpy as np
from config import GREEN, CYAN, GRAY, WHITE, BLACK, YELLOW, RED

_BG    = (14, 14, 20)
_PANEL = (28, 28, 42)
_BORD  = (60, 60, 85)
_TXT1  = (228, 228, 238)
_TXT2  = (128, 128, 148)
_TXT3  = (70,  70,  90)
_CYAN  = (255, 230, 30)
_GRN   = (55, 220, 55)
_RED   = (55, 55, 220)


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


def _txt(frame, text, x, y, color=_TXT1, scale=0.56, thick=1):
    cv2.putText(frame, text, (int(x), int(y)), cv2.FONT_HERSHEY_SIMPLEX,
                scale, BLACK, thick+2, cv2.LINE_AA)
    cv2.putText(frame, text, (int(x), int(y)), cv2.FONT_HERSHEY_SIMPLEX,
                scale, color, thick, cv2.LINE_AA)


def _txc(frame, text, cx, y, color=_TXT1, scale=0.56, thick=1):
    tw = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, thick)[0][0]
    _txt(frame, text, int(cx - tw//2), int(y), color, scale, thick)


def _divider(frame, x, y, w, color=_BORD):
    cv2.line(frame, (int(x), int(y)), (int(x+w), int(y)), color, 1)


def draw_profile_select(frame, profiles, selected_idx, confirm_delete=False, subtitle=''):
    H, W = frame.shape[:2]

    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (W, H), _BG, -1)
    cv2.addWeighted(overlay, 0.80, frame, 0.20, 0, frame)

    # Title bar
    _blend(frame, 0, 0, W, 52, (20, 14, 40), 0.94)
    _divider(frame, 0, 52, W)
    _txc(frame, "PROFIL SEC", W//2, 34, _CYAN, 0.82, 2)
    if subtitle:
        _txc(frame, subtitle, W//2, 50, YELLOW, 0.42, 1)

    if not profiles:
        cw, ch = 420, 80
        _panel(frame, W//2-cw//2, H//2-ch//2, cw, ch, _PANEL, 0.92, _BORD)
        _txc(frame, "Kayitli profil yok.", W//2, H//2-4, YELLOW, 0.62, 1)
        _txc(frame, "N: Yeni profil olustur", W//2, H//2+22, _GRN, 0.54, 1)
        return frame

    visible = profiles[:8]
    top_y   = 60
    card_h  = 52
    gap     = 6
    pad_x   = 40

    for i, prof in enumerate(visible):
        y0  = top_y + i * (card_h + gap)
        sel = (i == selected_idx % len(profiles))
        bg  = (40, 36, 60) if sel else (26, 26, 38)
        bord = _CYAN if sel else _BORD

        _panel(frame, pad_x, y0, W-pad_x*2, card_h, bg, 0.92, bord, 2 if sel else 1)

        if sel:
            _blend(frame, pad_x, y0, W-pad_x*2, 20, _CYAN, 0.10)

        name  = prof.get("name", "?")
        ht    = prof.get("height_cm", "?")
        wt    = prof.get("weight_kg", "?")
        ag    = prof.get("age", "?")
        sx    = "Erkek" if prof.get("sex", "M") == "M" else "Kadin"

        # Index badge
        _blend(frame, pad_x+8, y0+8, 28, 28, _CYAN if sel else (50,50,70), 0.80)
        cv2.rectangle(frame, (pad_x+8, y0+8), (pad_x+36, y0+36),
                      _CYAN if sel else _BORD, 1)
        _txc(frame, str(i+1), pad_x+22, y0+29, WHITE, 0.50, 2 if sel else 1)

        # Name
        _txt(frame, name[:20], pad_x+46, y0+22,
             _CYAN if sel else _TXT1, 0.62, 2 if sel else 1)

        # Info line
        extra = []
        if prof.get("waist_cm"):  extra.append(f"Bel:{prof['waist_cm']}cm")
        if prof.get("arm_cm"):    extra.append(f"Kol:{prof['arm_cm']}cm")
        info = f"{ht}cm  {wt}kg  {ag}y  {sx}"
        if extra:
            info += "  |  " + "  ".join(extra[:2])
        _txt(frame, info, pad_x+46, y0+44, _TXT2, 0.42, 1)

    # Delete confirm overlay
    if confirm_delete and profiles:
        victim = profiles[selected_idx % len(profiles)].get("name", "?")
        cw_, ch_ = 420, 70
        _panel(frame, W//2-cw_//2, H//2-ch_//2, cw_, ch_,
               (30, 10, 10), 0.94, _RED, 2)
        _txc(frame, f"Silinecek: {victim[:22]}?", W//2, H//2-8, _RED, 0.62, 2)
        _txc(frame, "D: Evet sil   |   Diger tus: Iptal",
             W//2, H//2+18, _TXT2, 0.46, 1)

    # Bottom hints
    _blend(frame, 0, H-34, W, 34, _BG, 0.90)
    _divider(frame, 0, H-34, W)
    hints = [
        ("1-9: Sec + Baslat", _CYAN),
        ("N: Yeni Profil",    _GRN),
        ("D: Sil",            (100, 80, 200)),
        ("ESC: Menu",         _TXT3),
    ]
    sp = W // len(hints)
    for j, (text, color) in enumerate(hints):
        _txc(frame, text, sp//2 + j*sp, H-10, color, 0.48, 1)

    return frame
