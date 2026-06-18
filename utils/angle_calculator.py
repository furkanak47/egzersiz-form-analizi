import numpy as np


def calculate_angle(a, b, c):
    """Angle at point b between vectors b→a and b→c (degrees)."""
    a, b, c = np.array(a[:2]), np.array(b[:2]), np.array(c[:2])
    ba = a - b
    bc = c - b
    cosine = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
    return float(np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0))))


def calculate_distance(a, b):
    a, b = np.array(a[:2]), np.array(b[:2])
    return float(np.linalg.norm(a - b))


def vertical_angle(a, b):
    """Angle of vector a→b relative to vertical axis (degrees)."""
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    return float(np.degrees(np.arctan2(abs(dx), abs(dy) + 1e-6)))
