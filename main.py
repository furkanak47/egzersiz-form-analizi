import cv2
import time
import threading
from datetime import date, timedelta

from config import CAMERA_INDEX, CAMERA_WIDTH, CAMERA_HEIGHT, EXERCISES, EXERCISE_NAMES
from pose_detector import PoseDetector
from gesture_detector import GestureDetector
from exercises import EXERCISE_MAP
from feedback.visual_feedback import (draw_hud, draw_menu, draw_recognition_overlay,
                                       draw_session_summary, _blend, _txt)
from feedback.audio_feedback import AudioFeedback
from bodyfat.estimator import BodyEstimator
from bodyfat.screen import draw_body_hud, draw_profile_input, FIELD_KEYS
from bodyfat.profile_screen import draw_profile_select
from strength.estimator import StrengthEstimator
from strength.screen import draw_strength_hud, draw_strength_input
from nutrition.screen import draw_nutrition_hud, draw_nutrition_search
from nutrition.calculator import profile_targets
from nutrition import food_db as food_db_mod
from nutrition import tracker as nut_tracker
from progress.screen import draw_progress_hud
from progress import tracker as prog_tracker
from ml.exercise_recognizer import ExerciseRecognizer
from ml.form_classifier import FormClassifier
from ml.data_collector import DataCollector
from ml.feature_extractor import landmarks_to_angles
import profiles as prof_store

WINDOW_NAME        = "Egzersiz Form Analizi"
GESTURE_FRAME_SKIP = 3

MODE_MENU            = "menu"
MODE_EXERCISE        = "exercise"
MODE_BODY            = "body"
MODE_PROFILE_SELECT  = "profile_select"
MODE_PROFILE_CREATE  = "profile_create"
MODE_STRENGTH        = "strength"
MODE_STRENGTH_INPUT  = "strength_input"
MODE_NUTRITION        = "nutrition"
MODE_NUTRITION_SEARCH = "nutrition_search"
MODE_PROGRESS         = "progress"
MODE_SESSION_SUMMARY  = "session_summary"

STRENGTH_FIELDS = ['squat', 'bench', 'deadlift']


# ── Asenkron pose işleme ─────────────────────────────────────────────────────

class PoseWorker:
    def __init__(self, detector: PoseDetector):
        self._detector = detector
        self._input   = None
        self._results = None
        self._lock    = threading.Lock()
        self._event   = threading.Event()
        self._running = True
        self._thread  = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _loop(self):
        while self._running:
            self._event.wait(timeout=0.05)
            self._event.clear()
            with self._lock:
                frame = self._input
                self._input = None
            if frame is not None:
                res = self._detector.process(frame)
                with self._lock:
                    self._results = res

    def submit(self, frame):
        with self._lock:
            self._input = frame
        self._event.set()

    def get(self):
        with self._lock:
            return self._results

    def stop(self):
        self._running = False


# ── Asenkron gesture işleme ──────────────────────────────────────────────────

class BodyWorker:
    """body_detector.process() + body_est.analyze() ayri thread'de calistirir."""

    def __init__(self, detector: PoseDetector, estimator):
        self._detector  = detector
        self._estimator = estimator
        self._input     = None
        self._result    = None
        self._lock      = threading.Lock()
        self._event     = threading.Event()
        self._running   = True
        self._thread    = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _loop(self):
        while self._running:
            self._event.wait(timeout=0.05)
            self._event.clear()
            with self._lock:
                data = self._input
                self._input = None
            if data is not None:
                frame, profile = data
                H, W = frame.shape[:2]
                res  = self._detector.process(frame)
                lm   = self._detector.get_landmarks(res)
                mask = self._detector.get_segmentation_mask(res, W, H)
                if lm:
                    result = self._estimator.analyze(lm, W, H, profile, seg_mask=mask)
                    with self._lock:
                        self._result = result

    def submit(self, frame, profile):
        with self._lock:
            self._input = (frame, profile)
        self._event.set()

    def get(self):
        with self._lock:
            return self._result

    def stop(self):
        self._running = False


class GestureWorker:
    def __init__(self, detector: GestureDetector):
        self._detector  = detector
        self._input     = None
        self._confirmed = None
        self._lock      = threading.Lock()
        self._event     = threading.Event()
        self._running   = True
        self._thread    = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _loop(self):
        while self._running:
            self._event.wait(timeout=0.05)
            self._event.clear()
            with self._lock:
                data = self._input
                self._input = None
            if data is not None:
                frame, now = data
                confirmed = self._detector.update(frame, now)
                if confirmed:
                    with self._lock:
                        self._confirmed = confirmed

    def submit(self, frame, now: float):
        with self._lock:
            self._input = (frame, now)
        self._event.set()

    def get_confirmed(self):
        with self._lock:
            val = self._confirmed
            self._confirmed = None
            return val

    def stop(self):
        self._running = False


# ── Profil oluşturma — tuş işleme ────────────────────────────────────────────

def profile_create_handle_key(key, state):
    """
    state: {"field": str, "values": dict, "input_buf": str}
    Doner: (state, outcome)
      outcome: None devam ediyor | "done" tamamlandi | "cancel" iptal
    """
    field = state["field"]
    buf   = state["input_buf"]
    vals  = state["values"]

    if key == 27:   # ESC
        return state, "cancel"

    if key in (13, 10):  # ENTER
        val, err = prof_store.validate_field(field, buf)
        if err:
            meta = next((f for f in prof_store.FIELDS if f[0] == field), None)
            required = meta[2] if meta else True
            if required or buf.strip():
                # Zorunlu alan, veya opsiyonel ama gecersiz deger girilmis — ayni alanda kal
                return state, None
            # Opsiyonel AND bos — atla
            val = None

        if val is not None:
            vals[field] = val

        idx = FIELD_KEYS.index(field)
        if idx + 1 < len(FIELD_KEYS):
            state = {"field": FIELD_KEYS[idx+1], "values": vals, "input_buf": ""}
            return state, None
        else:
            return state, "done"

    if key == 8:   # Backspace
        state["input_buf"] = buf[:-1]
        return state, None

    if 32 <= key <= 126:
        state["input_buf"] = buf + chr(key)
        return state, None

    return state, None


def _state_to_profile(state_values):
    """profile_create state values'i BodyEstimator'in beklediği profile dict'e donusturur."""
    v = state_values
    p = {
        "name":       v.get("name", "Profil"),
        "height_cm":  float(v.get("height_cm", 170)),
        "weight_kg":  float(v.get("weight_kg",  70)),
        "age":        int(v.get("age", 25)),
        "sex":        str(v.get("sex", "M")).upper(),
    }
    if v.get("activity") is not None:
        p["activity"] = v["activity"]
    for key in ("waist_cm", "hip_cm", "chest_cm", "arm_cm", "neck_cm"):
        if v.get(key) is not None:
            p[key] = float(v[key])
    return p


# ── Kamera açma ──────────────────────────────────────────────────────────────

def open_camera():
    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_MSMF)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    actual = int(cap.get(cv2.CAP_PROP_FOURCC))
    codec  = "".join(chr((actual >> i) & 0xFF) for i in (0, 8, 16, 24))
    print(f"Backend: MSMF | Codec: {codec} | "
          f"Res: {int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}")
    return cap


def window_closed():
    try:
        return cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1
    except Exception:
        return True


# ── Ana döngü ────────────────────────────────────────────────────────────────

def run():
    cap = open_camera()
    if not cap.isOpened():
        print("HATA: Kamera acilamadi.")
        return

    detector       = PoseDetector()
    body_detector  = PoseDetector(enable_segmentation=True, model_complexity=1)
    worker         = PoseWorker(detector)
    gesture_det    = GestureDetector()
    gesture_worker = GestureWorker(gesture_det)
    audio          = AudioFeedback()

    body_est    = BodyEstimator()
    body_est.load()
    body_worker = BodyWorker(body_detector, body_est)

    str_est = StrengthEstimator()
    str_est.load()

    def _start_exercise(ex_id: str):
        """Egzersiz baslat: analyzer olustur, sayaclari sifirla."""
        nonlocal current_ex, analyzer, prev_rep, last_result, _ex_start_time
        nonlocal _form_correct, _form_total, _form_clf, _form_dc
        nonlocal _form_label, _form_conf, _form_label_t, _data_collect_mode, _dc_rep_active
        nonlocal _rep_had_error, _last_rep_ok, _last_rep_ok_t
        current_ex         = ex_id
        analyzer           = EXERCISE_MAP[ex_id]()
        prev_rep           = 0
        last_result        = None
        _ex_start_time     = now
        _form_correct      = 0
        _form_total        = 0
        _form_clf          = FormClassifier(current_ex)
        _form_dc           = DataCollector(current_ex)
        _form_label        = None
        _form_conf         = 0.0
        _form_label_t      = 0.0
        _data_collect_mode = False
        _dc_rep_active     = False
        _rep_had_error     = False
        _last_rep_ok       = None
        _last_rep_ok_t     = 0.0

    recognizer = ExerciseRecognizer()
    if recognizer.load():
        print("Egzersiz tanima modeli yuklendi.")
    else:
        print("Egzersiz tanima modeli bulunamadi — once python ml/exercise_recognizer.py --train")

    food_db_mod.load()

    mode        = MODE_MENU
    current_ex  = None
    analyzer    = None
    prev_rep    = 0
    audio_on    = True
    last_result = None

    body_profile    = {}
    body_result     = None
    profile_state   = None
    select_profiles = []
    select_idx      = 0
    delete_confirm  = False

    strength_result = None
    strength_state  = None   # {'field': str, 'values': dict, 'input_buf': str, 'error': str}
    profile_select_dest = MODE_BODY  # MODE_BODY veya MODE_STRENGTH_INPUT

    nut_search_state = None  # {'query','results','selected','phase','selected_food','grams_buf','error'}
    nut_goal         = 'maintain'
    nut_day_offset   = 0    # 0=bugun, -1=dun, ...
    _NUT_GOALS       = ['maintain', 'bulk', 'cut']

    prog_tab          = 0   # 0=Egzersiz 1=Vucut 2=Guc
    _ex_start_time    = 0.0  # egzersiz moduna giris zamani
    _body_logged      = False  # bu oturumda vucut kaydedildi mi
    _form_correct     = 0      # dogru form frame sayisi
    _form_total       = 0      # toplam analiz frame sayisi
    _session_data     = {}     # oturum ozeti icin gecici veri
    _form_clf         = None   # FormClassifier — rep-bazli form kalite tahmini
    _form_dc          = None   # DataCollector — uygulama ici veri etiketleme
    _form_label       = None   # son tekrarin ML form etiketi
    _form_conf        = 0.0    # son etiketin guven skoru
    _form_label_t     = 0.0    # etiket zamani (HUD icin)
    _data_collect_mode = False # D tusu ile toggle
    _dc_rep_active    = False  # o an bir tekrar toplanıyor mu
    _rep_had_error    = False   # mevcut tekrarda hata var miydi
    _last_rep_ok      = None   # son tekrar dogru muydu (True/False)
    _last_rep_ok_t    = 0.0    # son tekrar sonucu zamani
    detected_ex       = None   # recognizer'dan gelen anlık tahmin
    _recog_fc         = 0      # tanima frame sayaci
    _switch_hold      = 0      # kac ardisik tahmin farkli cikti
    _SWITCH_THRESHOLD = 3      # bu kadar kez farkli cikinca gecis yap
    _auto_switch_msg  = ""     # ekranda kisa sure gosterilecek bilgi
    _auto_switch_t    = 0.0    # mesaj zamani
    _menu_detect_ex   = None   # menu'de algilanan egzersiz
    _menu_detect_hold = 0      # kac ardisik kez ayni tahmin
    _MENU_THRESHOLD   = 8      # oto-baslat esigi (8 × 5 frame ≈ 1-2 sn)

    fps = 0.0
    t0  = time.perf_counter()
    fc  = 0
    gesture_fc = 0

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_NAME, CAMERA_WIDTH, CAMERA_HEIGHT)
    print("Baslatildi. M:Menu  1-6:Egzersiz  B:Vucut Analizi  R:Sifirla  S:Ses  Q:Cikis")

    while True:
        ret, frame = cap.read()
        if not ret or window_closed():
            break

        frame = cv2.flip(frame, 1)
        H, W  = frame.shape[:2]
        now   = time.perf_counter()
        fc += 1;  gesture_fc += 1
        if now - t0 >= 0.5:
            fps = fc / (now - t0);  fc = 0;  t0 = now

        worker.submit(frame)
        if mode == MODE_MENU and gesture_fc % GESTURE_FRAME_SKIP == 0:
            gesture_worker.submit(frame, now)

        key = cv2.waitKey(1) & 0xFF

        # ── Mod bazlı tuş işleme ───────────────────────────────────────
        if mode == MODE_PROFILE_CREATE:
            profile_state, outcome = profile_create_handle_key(key, profile_state)
            if outcome == "done":
                new_p = _state_to_profile(profile_state["values"])
                prof_store.add_profile(new_p)
                body_profile = new_p
                body_est.reset_buffers()
                dest = profile_select_dest
                profile_select_dest = MODE_BODY
                if dest == MODE_STRENGTH_INPUT:
                    strength_state = {'field': STRENGTH_FIELDS[0], 'values': {}, 'input_buf': '', 'error': ''}
                    mode = MODE_STRENGTH_INPUT
                elif dest == MODE_NUTRITION:
                    mode = MODE_NUTRITION
                else:
                    mode = MODE_BODY
                print(f"Profil kaydedildi: {new_p['name']}")
            elif outcome == "cancel":
                mode = MODE_PROFILE_SELECT
                select_profiles = prof_store.load_profiles()

        elif mode == MODE_PROFILE_SELECT:
            if delete_confirm:
                if key == ord("d") and select_profiles:
                    victim = select_profiles[select_idx % len(select_profiles)]
                    prof_store.delete_profile(victim.get("name", ""))
                    select_profiles = prof_store.load_profiles()
                    select_idx = max(0, select_idx - 1)
                delete_confirm = False
            else:
                if key == 27 or key == ord("m"):
                    mode = MODE_MENU
                elif key == ord("n"):
                    profile_state = {"field": FIELD_KEYS[0], "values": {}, "input_buf": ""}
                    mode = MODE_PROFILE_CREATE
                elif key == ord("d") and select_profiles:
                    delete_confirm = True
                elif key in (82, 119, ord("w")):  # Up / w
                    if select_profiles:
                        select_idx = (select_idx - 1) % len(select_profiles)
                elif key in (84, 115, ord("s")):  # Down / s
                    if select_profiles:
                        select_idx = (select_idx + 1) % len(select_profiles)
                elif key in (13, 10) and select_profiles:  # ENTER
                    body_profile  = select_profiles[select_idx % len(select_profiles)]
                    _body_logged  = False
                    body_est.reset_buffers()
                    dest = profile_select_dest
                    profile_select_dest = MODE_BODY
                    if dest == MODE_STRENGTH_INPUT:
                        strength_state = {'field': STRENGTH_FIELDS[0], 'values': {}, 'input_buf': '', 'error': ''}
                        mode = MODE_STRENGTH_INPUT
                    elif dest == MODE_NUTRITION:
                        mode = MODE_NUTRITION
                    else:
                        mode = MODE_BODY
                else:
                    # 1-9 ile hizli secim
                    for num in range(1, 10):
                        if key == ord(str(num)):
                            idx = num - 1
                            if idx < len(select_profiles):
                                body_profile = select_profiles[idx]
                                body_est.reset_buffers()
                                dest = profile_select_dest
                                profile_select_dest = MODE_BODY
                                if dest == MODE_STRENGTH_INPUT:
                                    strength_state = {'field': STRENGTH_FIELDS[0], 'values': {}, 'input_buf': '', 'error': ''}
                                    mode = MODE_STRENGTH_INPUT
                                elif dest == MODE_NUTRITION:
                                    mode = MODE_NUTRITION
                                else:
                                    mode = MODE_BODY
                            break

        elif mode == MODE_STRENGTH_INPUT:
            if key == 27:
                mode = MODE_STRENGTH
            elif key in (13, 10):
                buf = strength_state.get('input_buf', '')
                field = strength_state['field']
                try:
                    val = float(buf.replace(',', '.')) if buf.strip() else 0.0
                    if val < 0 or val > 500:
                        strength_state['error'] = 'Gecersiz deger (0-500kg)'
                    else:
                        strength_state['values'][field] = val
                        strength_state['error'] = ''
                        idx = STRENGTH_FIELDS.index(field)
                        if idx + 1 < len(STRENGTH_FIELDS):
                            strength_state['field'] = STRENGTH_FIELDS[idx + 1]
                            strength_state['input_buf'] = ''
                        else:
                            bw  = float(body_profile.get('weight_kg', 80))
                            sex = str(body_profile.get('sex', 'M')).upper()
                            strength_result = str_est.analyze(
                                strength_state['values'], bw, sex)
                            if body_profile:
                                dots = strength_result.get('dots', {}).get('score', 0) if strength_result else 0
                                prog_tracker.log_strength(
                                    body_profile.get('name', 'Profil'),
                                    strength_state['values'], dots)
                            mode = MODE_STRENGTH
                except ValueError:
                    strength_state['error'] = 'Sayi olmali'
            elif key in (8, 127):   # Backspace veya DEL
                strength_state['input_buf'] = strength_state.get('input_buf', '')[:-1]
            elif 48 <= key <= 57 or key == 46:
                strength_state['input_buf'] = strength_state.get('input_buf', '') + chr(key)

        elif mode == MODE_NUTRITION_SEARCH:
            if key == 27:   # ESC
                if nut_search_state and nut_search_state.get('phase') == 'grams':
                    nut_search_state['phase'] = 'search'
                    nut_search_state['grams_buf'] = ''
                    nut_search_state['error'] = ''
                else:
                    mode = MODE_NUTRITION
            elif nut_search_state and nut_search_state.get('phase') == 'search':
                results = nut_search_state.get('results', [])
                sel     = nut_search_state.get('selected', 0)
                if key in (82, 72):      # ok yukari (platform bagimsiz)
                    nut_search_state['selected'] = max(0, sel - 1)
                elif key in (84, 80):    # ok asagi
                    nut_search_state['selected'] = min(len(results)-1, sel+1) if results else 0
                elif key in (13, 10) and results:  # ENTER — secim yap
                    nut_search_state['phase']         = 'grams'
                    nut_search_state['selected_food'] = results[sel]
                    nut_search_state['grams_buf']     = ''
                    nut_search_state['error']         = ''
                elif key in (8, 127):
                    q = nut_search_state.get('query', '')
                    nut_search_state['query']    = q[:-1]
                    nut_search_state['results']  = food_db_mod.search(nut_search_state['query'])
                    nut_search_state['selected'] = 0
                elif 32 <= key <= 126:   # yazilabilir karakter — hepsi metin girisi
                    nut_search_state['query']   = nut_search_state.get('query', '') + chr(key)
                    nut_search_state['results'] = food_db_mod.search(nut_search_state['query'])
                    nut_search_state['selected'] = 0
            elif nut_search_state and nut_search_state.get('phase') == 'grams':
                if key in (13, 10):
                    buf = nut_search_state.get('grams_buf', '')
                    try:
                        grams = float(buf.replace(',', '.')) if buf.strip() else 0.0
                        if grams <= 0 or grams > 5000:
                            nut_search_state['error'] = 'Gecersiz miktar (1-5000g)'
                        else:
                            pname   = body_profile.get('name', 'Profil')
                            day_str = (date.today() + timedelta(days=nut_day_offset)).isoformat()
                            nut_tracker.add_entry(pname, nut_search_state['selected_food'], grams, day=day_str)
                            nut_search_state = {'query': '', 'results': [], 'selected': 0,
                                                'phase': 'search', 'grams_buf': '', 'error': ''}
                    except ValueError:
                        nut_search_state['error'] = 'Sayi olmali'
                elif key in (8, 127):
                    nut_search_state['grams_buf'] = nut_search_state.get('grams_buf', '')[:-1]
                elif 48 <= key <= 57 or key == 46:
                    nut_search_state['grams_buf'] = nut_search_state.get('grams_buf', '') + chr(key)

        elif mode == MODE_PROGRESS:
            if key in (ord("q"), 27, ord("m")):
                mode = MODE_MENU
            elif key in (ord(","), 44, 81):   # < veya sol ok
                prog_tab = (prog_tab - 1) % 3
            elif key in (ord("."), 46, 83):   # > veya sag ok
                prog_tab = (prog_tab + 1) % 3

        elif mode == MODE_SESSION_SUMMARY:
            if key != 255 and key != -1:      # herhangi bir tusa basinca menu
                mode = MODE_MENU

        else:
            if key in (ord("q"), 27):
                break
            if key == ord("m"):
                if mode == MODE_EXERCISE and analyzer and analyzer.rep_count > 0:
                    dur_sec = now - _ex_start_time
                    quality = int(_form_correct / max(_form_total, 1) * 100)
                    _session_data = {
                        "ex_id":    current_ex,
                        "ex_name":  EXERCISE_NAMES.get(current_ex, current_ex),
                        "reps":     analyzer.rep_count,
                        "dur_sec":  dur_sec,
                        "quality":  quality,
                        "time_based": getattr(analyzer, 'TIME_BASED', False),
                    }
                    if body_profile:
                        prog_tracker.log_exercise(
                            body_profile.get("name", "Profil"),
                            current_ex, analyzer.rep_count, dur_sec / 60.0)
                    mode = MODE_SESSION_SUMMARY
                else:
                    mode = MODE_MENU
            if key == ord("p"):
                prog_tab = 0
                mode = MODE_PROGRESS
            if key == ord("s"):
                audio_on = not audio_on;  audio.set_enabled(audio_on)
            if key == ord("r") and analyzer:
                analyzer.reset();  prev_rep = 0
            if key == ord("d") and mode == MODE_EXERCISE and _form_dc:
                _data_collect_mode = not _data_collect_mode
                if not _data_collect_mode:
                    n = _form_dc.save()
                    if n > 0:
                        print(f"Veri kaydedildi: {n} tekrar  ({current_ex})")
            if key == ord("b"):
                select_profiles     = prof_store.load_profiles()
                select_idx          = 0
                profile_select_dest = MODE_BODY
                mode = MODE_PROFILE_SELECT
            if key == ord("g"):
                if not body_profile:
                    # Profil olmadan Dots hesaplanamaz — once profil sec
                    select_profiles     = prof_store.load_profiles()
                    select_idx          = 0
                    profile_select_dest = MODE_STRENGTH_INPUT
                    mode = MODE_PROFILE_SELECT
                else:
                    strength_state = {'field': STRENGTH_FIELDS[0], 'values': {}, 'input_buf': '', 'error': ''}
                    mode = MODE_STRENGTH_INPUT
            if key == ord("n"):
                if not body_profile:
                    select_profiles     = prof_store.load_profiles()
                    select_idx          = 0
                    profile_select_dest = MODE_NUTRITION
                    mode = MODE_PROFILE_SELECT
                else:
                    mode = MODE_NUTRITION
            if mode == MODE_NUTRITION:
                if key == ord("a"):
                    nut_search_state = {'query': '', 'results': [], 'selected': 0,
                                        'phase': 'search', 'grams_buf': '', 'error': ''}
                    mode = MODE_NUTRITION_SEARCH
                elif key == ord("x"):
                    pname   = body_profile.get('name', 'Profil')
                    day_str = (date.today() + timedelta(days=nut_day_offset)).isoformat()
                    nut_tracker.remove_last(pname, day=day_str)
                elif key == ord("h"):
                    nut_goal = _NUT_GOALS[(_NUT_GOALS.index(nut_goal) + 1) % len(_NUT_GOALS)]
                elif key == ord("["):
                    nut_day_offset -= 1
                elif key == ord("]"):
                    nut_day_offset = min(0, nut_day_offset + 1)

            if mode == MODE_MENU:
                for nk, (ex_id, _) in EXERCISES.items():
                    if key == ord(nk):
                        _start_exercise(ex_id)
                        mode = MODE_EXERCISE
                        break

        confirmed_ex = gesture_worker.get_confirmed()
        if confirmed_ex and mode == MODE_MENU and confirmed_ex in EXERCISE_MAP:
            _start_exercise(confirmed_ex)
            mode = MODE_EXERCISE
            print(f"Jest ile secildi: {confirmed_ex}")


        # ── Pose sonuçları ─────────────────────────────────────────────
        results   = worker.get()
        landmarks = detector.get_landmarks(results) if results else None

        # ── Egzersiz tanima (her 5 frame'de bir) ──────────────────────
        _recog_fc += 1
        if recognizer.loaded and landmarks and _recog_fc % 5 == 0:
            detected_ex = recognizer.predict(landmarks)

            if mode == MODE_MENU and detected_ex and detected_ex in EXERCISE_MAP:
                # Menude aynı egzersiz N kez algilanınca otomatik basla
                if detected_ex == _menu_detect_ex:
                    _menu_detect_hold += 1
                    if _menu_detect_hold >= _MENU_THRESHOLD:
                        _start_exercise(detected_ex)
                        mode              = MODE_EXERCISE
                        _menu_detect_hold = 0
                        _menu_detect_ex   = None
                else:
                    _menu_detect_ex   = detected_ex
                    _menu_detect_hold = 1
            else:
                if mode != MODE_MENU:
                    _menu_detect_ex   = None
                    _menu_detect_hold = 0

            # MODE_EXERCISE'de farkli egzersiz algilayinca otomatik gecis
            if (mode == MODE_EXERCISE and detected_ex and
                    detected_ex != current_ex and detected_ex in EXERCISE_MAP):
                _switch_hold += 1
                if _switch_hold >= _SWITCH_THRESHOLD:
                    _start_exercise(detected_ex)
                    _switch_hold = 0
                    ex_name_new = EXERCISE_NAMES.get(current_ex, current_ex.replace("_", " ").title())
                    _auto_switch_msg = "AI: " + ex_name_new + " algilandi"
                    _auto_switch_t   = now
            else:
                if mode == MODE_EXERCISE:
                    _switch_hold = 0

        # ── Mod işleme ─────────────────────────────────────────────────
        if mode == MODE_EXERCISE and analyzer and landmarks:
            result = analyzer.analyze(landmarks, W, H)
            last_result = result
            _form_total += 1
            if result.is_correct:
                _form_correct += 1
            if result.errors:
                _rep_had_error = True

            # ML: her frame'in acilarini topla
            try:
                _frame_angles = landmarks_to_angles(landmarks)
            except Exception:
                _frame_angles = {}
            if _frame_angles:
                if _form_clf and _form_clf.is_available:
                    _form_clf.add_frame(_frame_angles)
                if _form_dc and _data_collect_mode:
                    if not _dc_rep_active:
                        _form_dc.start_rep()
                        _dc_rep_active = True
                    _form_dc.add_frame(_frame_angles)

            if result.rep_count > prev_rep:
                # Per-rep form kalitesi (kural tabanli)
                _last_rep_ok   = not _rep_had_error
                _last_rep_ok_t = now
                _rep_had_error = False

                # Form kalite tahmini (ML)
                if _form_clf and _form_clf.is_available:
                    lbl, conf = _form_clf.finalize_rep()
                    _form_clf.reset()
                    if lbl and conf >= 0.72:
                        _form_label   = lbl
                        _form_conf    = conf
                        _form_label_t = now
                # Veri etiketleme
                if _form_dc and _data_collect_mode and _dc_rep_active:
                    auto_lbl = _form_label if _form_label else "correct"
                    _form_dc.finish_rep(auto_lbl)
                    _dc_rep_active = False

                if not getattr(analyzer, 'TIME_BASED', False):
                    audio.rep_counted()
                prev_rep = result.rep_count

            if result.errors:
                audio.error()
            elif result.warnings:
                audio.warning()

        if mode == MODE_BODY and body_profile:
            body_worker.submit(frame, body_profile)
            latest = body_worker.get()
            if latest is not None:
                body_result = latest
                if latest.get("stable") and not _body_logged and body_profile:
                    prog_tracker.log_body(
                        body_profile.get("name", "Profil"),
                        latest["fat_pct"],
                        float(body_profile.get("weight_kg", 0)),
                        latest["bmi"])
                    _body_logged = True

        # ── Çizim ──────────────────────────────────────────────────────
        draw_result = (last_result if mode == MODE_EXERCISE else None)
        if results:
            detector.draw_skeleton(
                frame, results,
                draw_result.landmark_colors if draw_result else None
            )

        if mode == MODE_MENU:
            sel = next((k for k, (v, _) in EXERCISES.items() if v == current_ex), None)
            draw_menu(frame, EXERCISES, selected=sel, detected_ex=detected_ex,
                      menu_detect_ex=_menu_detect_ex,
                      menu_detect_hold=_menu_detect_hold,
                      menu_detect_threshold=_MENU_THRESHOLD)

        elif mode == MODE_EXERCISE and (draw_result or last_result):
            dr      = draw_result or last_result
            ex_name = EXERCISE_NAMES.get(current_ex, current_ex.replace("_", " ").title())
            _rep_ok = _last_rep_ok if (now - _last_rep_ok_t) < 4.0 else None
            draw_hud(frame, dr, ex_name, fps, audio_on,
                     time_based=getattr(analyzer, 'TIME_BASED', False),
                     data_collect=_data_collect_mode,
                     last_rep_ok=_rep_ok)

        elif mode == MODE_BODY:
            draw_body_hud(frame, body_result, body_profile, fps)

        elif mode == MODE_PROFILE_SELECT:
            if profile_select_dest == MODE_STRENGTH_INPUT:
                sub = "Guc Analizi icin profil gerekli -- sec veya olustur"
            elif profile_select_dest == MODE_NUTRITION:
                sub = "Beslenme takibi icin profil gerekli -- sec veya olustur"
            else:
                sub = ''
            draw_profile_select(frame, select_profiles, select_idx,
                                confirm_delete=delete_confirm, subtitle=sub)

        elif mode == MODE_PROFILE_CREATE and profile_state:
            draw_profile_input(frame, profile_state)

        elif mode == MODE_STRENGTH:
            draw_strength_hud(frame, strength_result, body_profile, fps)

        elif mode == MODE_STRENGTH_INPUT and strength_state:
            draw_strength_input(frame, strength_state)

        elif mode == MODE_NUTRITION:
            pname   = body_profile.get('name', 'Profil')
            day_str = (date.today() + timedelta(days=nut_day_offset)).isoformat()
            entries = nut_tracker.get_log(pname, day=day_str)
            targets = profile_targets(body_profile, goal=nut_goal)
            draw_nutrition_hud(frame, entries, targets, body_profile, fps, day_str)

        elif mode == MODE_NUTRITION_SEARCH and nut_search_state:
            draw_nutrition_search(frame, nut_search_state)

        elif mode == MODE_PROGRESS:
            pname = body_profile.get("name", "") if body_profile else ""
            draw_progress_hud(
                frame, body_profile or {},
                prog_tracker.get_exercise_history(pname) if pname else [],
                prog_tracker.get_body_history(pname)     if pname else [],
                prog_tracker.get_strength_history(pname) if pname else [],
                prog_tab, fps)

        elif mode == MODE_SESSION_SUMMARY:
            draw_session_summary(frame, _session_data)

        draw_recognition_overlay(frame, detected_ex)

        # Auto-switch bildirimi (2 saniye goster)
        if _auto_switch_msg and (now - _auto_switch_t) < 2.0:
            H2, W2 = frame.shape[:2]
            _blend(frame, W2//2-200, H2//2-30, 400, 52, (10,40,10), 0.80)
            _txt(frame, _auto_switch_msg, W2//2-190, H2//2+10,
                 (80,255,80), 0.65, 2)

        cv2.imshow(WINDOW_NAME, frame)

    # ── Temizlik ────────────────────────────────────────────────────────
    worker.stop()
    gesture_worker.stop()
    body_worker.stop()
    cap.release()
    detector.close()
    body_detector.close()
    gesture_det.close()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    run()
