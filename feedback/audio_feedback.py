import threading
import time

try:
    import winsound
    _HAS_WINSOUND = True
except ImportError:
    _HAS_WINSOUND = False


class AudioFeedback:
    ERROR_FREQ    = 800
    WARNING_FREQ  = 1200
    SUCCESS_FREQ  = 1600
    DURATION_MS   = 150

    ALERT_COOLDOWN = 1.5   # error / warning arasi minimum sure
    REP_COOLDOWN   = 0.8   # rep sesi icin daha kisa sure

    def __init__(self):
        self._last_error   = 0.0
        self._last_warning = 0.0
        self._last_rep     = 0.0
        self._enabled = _HAS_WINSOUND

    def _beep(self, freq, duration_ms=None):
        if not self._enabled:
            return
        dur = duration_ms or self.DURATION_MS
        threading.Thread(
            target=winsound.Beep,
            args=(freq, dur),
            daemon=True,
        ).start()

    def error(self):
        now = time.time()
        if now - self._last_error >= self.ALERT_COOLDOWN:
            self._last_error = now
            self._beep(self.ERROR_FREQ)

    def warning(self):
        now = time.time()
        if now - self._last_warning >= self.ALERT_COOLDOWN:
            self._last_warning = now
            self._beep(self.WARNING_FREQ)

    def rep_counted(self):
        now = time.time()
        if now - self._last_rep >= self.REP_COOLDOWN:
            self._last_rep = now
            self._beep(self.SUCCESS_FREQ, duration_ms=200)

    def set_enabled(self, enabled: bool):
        self._enabled = enabled and _HAS_WINSOUND
