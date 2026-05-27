"""Marathon Tracker — FastAPI backend + mobile PWA."""
from datetime import date
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import db, strava, plan

app = FastAPI(title="Marathon Tracker")
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
def startup():
    db.init_db()


# ---------- Pages ----------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# ---------- Strava OAuth ----------
@app.get("/auth/login")
def auth_login():
    return RedirectResponse(strava.authorize_url())


@app.get("/auth/callback")
def auth_callback(code: str = None, error: str = None):
    if error or not code:
        return RedirectResponse("/?strava=error")
    strava.exchange_code(code)
    return RedirectResponse("/?strava=connected")


# ---------- API ----------
@app.get("/api/today")
def api_today():
    today = date.today()
    s = plan.session_for(today)
    return {
        "date": today.isoformat(),
        "weekday": today.strftime("%A"),
        "session": s,
        "days_to_race": plan.days_to_race(today),
        "week": s["week"],
        "strava_connected": strava.is_connected(),
        "target_pace": plan.pace_str(plan.TARGET_PACE_S),
    }


@app.get("/api/week")
def api_week(wk: int = None):
    return {"week": wk or plan.current_week_number(),
            "days": plan.week_plan(wk)}


@app.post("/api/sync")
def api_sync():
    if not strava.is_connected():
        return JSONResponse({"error": "not_connected"}, status_code=400)
    try:
        n = strava.sync_activities()
        return {"synced": n}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/runs")
def api_runs():
    runs = db.get_runs(60)
    # weekly mileage rollup
    weekly = {}
    for r in runs:
        wk = r["date"][:7]  # rough month bucket fallback
        weekly[wk] = weekly.get(wk, 0) + (r["distance_km"] or 0)
    for r in runs:
        if r["pace_s_per_km"]:
            r["pace_str"] = plan.pace_str(r["pace_s_per_km"])
            r["in_zone2"] = (r["avg_hr"] is not None
                             and r["avg_hr"] <= plan.ZONE2_HR_MAX)
        else:
            r["pace_str"] = "—"
            r["in_zone2"] = None
    total_km = round(sum(r["distance_km"] or 0 for r in runs), 1)
    return {"runs": runs, "total_km": total_km,
            "zone2_max_hr": plan.ZONE2_HR_MAX}


@app.post("/api/lifts")
def api_add_lift(
    split: str = Form(...),
    exercise: str = Form(...),
    weight_kg: float = Form(...),
    reps: int = Form(...),
    sets: int = Form(...),
):
    lift_id = db.add_lift({
        "date": date.today().isoformat(),
        "split": split, "exercise": exercise,
        "weight_kg": weight_kg, "reps": reps, "sets": sets,
    })
    return {"id": lift_id}


@app.get("/api/lifts")
def api_lifts():
    lifts = db.get_lifts(60)
    for l in lifts:
        l["volume"] = round((l["weight_kg"] or 0) * (l["reps"] or 0) * (l["sets"] or 0), 1)
    return {"lifts": lifts}


@app.post("/api/injuries")
def api_add_injury(
    area: str = Form(...),
    severity: int = Form(...),
    note: str = Form(""),
):
    iid = db.add_injury({
        "date": date.today().isoformat(),
        "area": area, "severity": severity, "note": note,
    })
    return {"id": iid}


@app.get("/api/injuries")
def api_injuries():
    return {"injuries": db.get_injuries(30)}


@app.get("/health")
def health():
    return {"ok": True}
