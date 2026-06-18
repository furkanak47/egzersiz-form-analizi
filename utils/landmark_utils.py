def get_px(landmarks, idx, w, h):
    """Return (x_pixel, y_pixel) for a landmark."""
    lm = landmarks[idx]
    return [int(lm.x * w), int(lm.y * h)]


def get_norm(landmarks, idx):
    """Return (x, y, z) normalized coords."""
    lm = landmarks[idx]
    return [lm.x, lm.y, lm.z]


def visibility(landmarks, idx):
    return landmarks[idx].visibility
