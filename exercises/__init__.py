from exercises.biceps_curl import BicepsCurl
from exercises.triceps import Triceps
from exercises.shoulder_press import ShoulderPress
from exercises.lateral_raise import LateralRaise
from exercises.fly import Fly
from exercises.bench_press import BenchPress
from exercises.squat import Squat
from exercises.push_up import PushUp
from exercises.deadlift import Deadlift
from exercises.pull_up import PullUp
from exercises.plank import Plank
from exercises.leg_raises import LegRaises
from exercises.romanian_deadlift import RomanianDeadlift
from exercises.hammer_curl import HammerCurl
from exercises.hip_thrust import HipThrust
from exercises.lat_pulldown import LatPulldown
from exercises.incline_bench_press import InclineBenchPress
from exercises.decline_bench_press import DeclineBenchPress
from exercises.tricep_dips import TricepDips
from exercises.leg_extension import LegExtension
from exercises.russian_twist import RussianTwist
from exercises.t_bar_row import TBarRow

EXERCISE_MAP = {
    "biceps_curl":          BicepsCurl,
    "triceps":              Triceps,
    "shoulder_press":       ShoulderPress,
    "lateral_raise":        LateralRaise,
    "fly":                  Fly,
    "bench_press":          BenchPress,
    "squat":                Squat,
    "push_up":              PushUp,
    "deadlift":             Deadlift,
    "pull_up":              PullUp,
    "plank":                Plank,
    "leg_raises":           LegRaises,
    "romanian_deadlift":    RomanianDeadlift,
    "hammer_curl":          HammerCurl,
    "hip_thrust":           HipThrust,
    "lat_pulldown":         LatPulldown,
    "incline_bench_press":  InclineBenchPress,
    "decline_bench_press":  DeclineBenchPress,
    "tricep_dips":          TricepDips,
    "leg_extension":        LegExtension,
    "russian_twist":        RussianTwist,
    "t_bar_row":            TBarRow,
}
