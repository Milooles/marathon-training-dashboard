"""Strava OAuth2 + activity sync. Read-only personal use."""
import os
import time
import httpx
from . import db

STRAVA_CLIENT_ID = os.environ.get("STRAVA_CLIENT_ID", "")
STRAVA_CLIENT_SECRET = os.environ.get("STRAVA_CLIENT_SECRET", "")
STRAVA_REDIRECT_URI = os.environ.get("STRAVA_REDIRECT_URI", "http://localhost:8000/auth/callback")

AUTH_URL = "https://www.strava.com/oauth/authorize"
TOKEN_URL = "https://www.strava.com/oauth/token"
ACTIVITIES_URL = "https://www.strava.com/api/v3/athlete/activities"
SCOPE = "read,activity:read_all"


def authorize_url() -> str:
    return (
        f"{AUTH_URL}?client_id={STRAVA_CLIENT_ID}"
        f"&response_type=code&redirect_uri={STRAVA_REDIRECT_URI}"
        f"&approval_prompt=auto&scope={SCOPE}"
    )


def exchange_code(code: str):
    """Swap auth code for tokens after first login."""
    resp = httpx.post(
        TOKEN_URL,
        data={
            "client_id": STRAVA_CLIENT_ID,
            "client_secret": STRAVA_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
        },
    )
    resp.raise_for_status()
    data = resp.json()
    db.save_tokens(data["access_token"], data["refresh_token"], data["expires_at"])
    return data


def _refresh(refresh_token: str):
    resp = httpx.post(
        TOKEN_URL,
        data={
            "client_id": STRAVA_CLIENT_ID,
            "client_secret": STRAVA_CLIENT_SECRET,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
    )
    resp.raise_for_status()
    data = resp.json()
    db.save_tokens(data["access_token"], data["refresh_token"], data["expires_at"])
    return data["access_token"]


def get_access_token():
    """Return a valid token, refreshing if expired."""
    tokens = db.get_tokens()
    if not tokens:
        return None
    if tokens["expires_at"] <= int(time.time()) + 60:
        return _refresh(tokens["refresh_token"])
    return tokens["access_token"]


def is_connected() -> bool:
    return db.get_tokens() is not None


def sync_activities(per_page: int = 50):
    """Pull recent runs from Strava into the local DB."""
    token = get_access_token()
    if not token:
        raise RuntimeError("Not connected to Strava")

    resp = httpx.get(
        ACTIVITIES_URL,
        headers={"Authorization": f"Bearer {token}"},
        params={"per_page": per_page, "page": 1},
    )
    resp.raise_for_status()
    activities = resp.json()

    saved = 0
    for a in activities:
        if a.get("type") not in ("Run", "TrailRun"):
            continue
        dist_km = (a.get("distance") or 0) / 1000
        moving = a.get("moving_time") or 0
        pace = (moving / dist_km) if dist_km > 0 else None
        db.save_run(
            {
                "strava_id": a["id"],
                "date": a["start_date_local"][:10],
                "name": a.get("name"),
                "distance_km": round(dist_km, 2),
                "moving_time_s": moving,
                "pace_s_per_km": round(pace, 1) if pace else None,
                "avg_hr": a.get("average_heartrate"),
                "max_hr": a.get("max_heartrate"),
                "elevation_m": a.get("total_elevation_gain"),
                "source": "strava",
            }
        )
        saved += 1
    return saved
