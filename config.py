CAMERA_INDEX  = 0
CAMERA_WIDTH  = 1280
CAMERA_HEIGHT = 720

# MediaPipe işlem çözünürlüğü — ekranda tam boyut gösterilir
PROCESS_WIDTH  = 480
PROCESS_HEIGHT = 270

# 0=hızlı, 1=orta, 2=hassas
MODEL_COMPLEXITY = 0

MIN_DETECTION_CONFIDENCE = 0.6
MIN_TRACKING_CONFIDENCE  = 0.5

EXERCISES = {
    "1": ("biceps_curl", "Biceps Curl"),
    "2": ("triceps", "Triceps Extension"),
    "3": ("shoulder_press", "Shoulder Press"),
    "4": ("lateral_raise", "Lateral Raise"),
    "5": ("fly", "Fly / Pec Fly"),
    "6": ("bench_press", "Gogus Press"),
}

EXERCISE_NAMES = {
    "biceps_curl":         "Biceps Curl",
    "triceps":             "Triceps Extension",
    "shoulder_press":      "Shoulder Press",
    "lateral_raise":       "Lateral Raise",
    "fly":                 "Fly / Pec Fly",
    "bench_press":         "Gogus Press",
    "squat":               "Squat",
    "push_up":             "Push Up",
    "deadlift":            "Deadlift",
    "pull_up":             "Pull Up",
    "plank":               "Plank",
    "leg_raises":          "Leg Raises",
    "romanian_deadlift":   "Romanian Deadlift",
    "hammer_curl":         "Hammer Curl",
    "hip_thrust":          "Hip Thrust",
    "lat_pulldown":        "Lat Pulldown",
    "incline_bench_press": "Incline Bench Press",
    "decline_bench_press": "Decline Bench Press",
    "tricep_dips":         "Tricep Dips",
    "leg_extension":       "Leg Extension",
    "russian_twist":       "Russian Twist",
    "t_bar_row":           "T-Bar Row",
}

# BGR
GREEN   = (0, 255, 0)
RED     = (0, 0, 255)
YELLOW  = (0, 255, 255)
WHITE   = (255, 255, 255)
BLACK   = (0, 0, 0)
ORANGE  = (0, 165, 255)
CYAN    = (255, 255, 0)
GRAY    = (150, 150, 150)
DARK    = (30, 30, 30)
