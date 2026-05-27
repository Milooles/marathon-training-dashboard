"""9-week marathon plan to July 4. Target pace 5:30/km.
Tuesday = basketball game, Wednesday = basketball training.
Easy/zone-2 pace assumed ~6:15/km. Long runs build toward race distance.
"""
from datetime import date, timedelta

RACE_DATE = date(2026, 7, 4)
TARGET_PACE_S = 5 * 60 + 30  # 5:30/km in seconds
EASY_PACE_S = 6 * 60 + 15    # zone-2 easy pace
ZONE2_HR_MAX = 155           # rough upper bound; edit to your tested zone

# Day index: Mon=0 ... Sun=6
# Fixed weekly anchors:
#   Tue (1) = basketball game (no run)
#   Wed (2) = basketball training (no run)
# Plan template per week: list of (weekday, type, km, note)
WEEK_TEMPLATE = {
    1: [(0, "easy", 6, "Push pull legs after"), (3, "tempo", 6, "3km @ 5:30"),
        (5, "long", 14, "Zone 2"), (6, "easy", 5, "Recovery jog")],
    2: [(0, "easy", 7, ""), (3, "tempo", 7, "4km @ 5:30"),
        (5, "long", 16, "Zone 2"), (6, "easy", 5, "")],
    3: [(0, "easy", 7, ""), (3, "intervals", 7, "5x800 @ 5:00"),
        (5, "long", 18, "Zone 2"), (6, "easy", 6, "")],
    4: [(0, "easy", 6, "Cutback week"), (3, "tempo", 6, "3km @ 5:30"),
        (5, "long", 14, "Easy effort"), (6, "easy", 5, "")],
    5: [(0, "easy", 8, ""), (3, "tempo", 8, "5km @ 5:30"),
        (5, "long", 22, "Race pace last 5km"), (6, "easy", 6, "")],
    6: [(0, "easy", 8, ""), (3, "intervals", 8, "6x800 @ 5:00"),
        (5, "long", 26, "Zone 2"), (6, "easy", 6, "")],
    7: [(0, "easy", 8, ""), (3, "tempo", 8, "6km @ 5:30"),
        (5, "long", 30, "Long fuel practice"), (6, "easy", 6, "")],
    8: [(0, "easy", 6, "Taper begins"), (3, "tempo", 6, "3km @ 5:30"),
        (5, "long", 18, "Easy"), (6, "easy", 5, "")],
    9: [(0, "easy", 5, "Taper"), (3, "easy", 4, "Shakeout @ race pace strides"),
        (4, "rest", 0, "Rest + carb load"), (6, "race", 42.2, "MARATHON 5:30/km")],
}


def _week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())


def current_week_number(today: date = None) -> int:
    today = today or date.today()
    race_week_start = _week_start(RACE_DATE)
    plan_start = race_week_start - timedelta(weeks=8)
    delta_weeks = (_week_start(today) - plan_start).days // 7
    wk = delta_weeks + 1
    return max(1, min(9, wk))


def pace_str(seconds: float) -> str:
    if not seconds:
        return "—"
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m}:{s:02d}/km"


def session_for(today: date = None) -> dict:
    today = today or date.today()
    wk = current_week_number(today)
    weekday = today.weekday()

    # Fixed basketball anchors
    if weekday == 1:
        return {"type": "basketball", "title": "Basketball game",
                "km": 0, "note": "Game day. No run.", "week": wk}
    if weekday == 2:
        return {"type": "basketball", "title": "Basketball training",
                "km": 0, "note": "Training. No run.", "week": wk}

    for wd, typ, km, note in WEEK_TEMPLATE[wk]:
        if wd == weekday:
            target = TARGET_PACE_S if typ in ("tempo", "race") else EASY_PACE_S
            return {
                "type": typ,
                "title": typ.capitalize() + (f" {km}km" if km else ""),
                "km": km,
                "note": note,
                "target_pace": pace_str(target),
                "week": wk,
            }
    return {"type": "rest", "title": "Rest day", "km": 0,
            "note": "Recover. Mobility + stretch.", "week": wk}


def week_plan(wk: int = None, today: date = None) -> list:
    today = today or date.today()
    wk = wk or current_week_number(today)
    names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    out = []
    sessions = {wd: (typ, km, note) for wd, typ, km, note in WEEK_TEMPLATE[wk]}
    for i, name in enumerate(names):
        if i == 1:
            out.append({"day": name, "type": "basketball", "km": 0, "note": "Game"})
        elif i == 2:
            out.append({"day": name, "type": "basketball", "km": 0, "note": "Training"})
        elif i in sessions:
            typ, km, note = sessions[i]
            out.append({"day": name, "type": typ, "km": km, "note": note})
        else:
            out.append({"day": name, "type": "rest", "km": 0, "note": ""})
    return out


def days_to_race(today: date = None) -> int:
    today = today or date.today()
    return (RACE_DATE - today).days
