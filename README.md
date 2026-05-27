# Marathon Tracker

Mobile PWA for your 9-week build to the July 4 marathon. Pulls runs from
Strava, logs PPL lifts, flags zone-2 drift, tracks calf niggles. Built around
your Tuesday game + Wednesday training.

## Stack
FastAPI + SQLite backend. Mobile-first HTML/JS PWA frontend. Strava OAuth2.

## Run locally
```bash
pip install -r requirements.txt
cp .env.example .env        # fill in Strava client id + secret
uvicorn app.main:app --reload
```
Open http://localhost:8000 — tap Connect Strava once, then Sync.

## Strava setup
1. Go to https://www.strava.com/settings/api
2. Create an app. Authorization Callback Domain = `localhost` (dev) or your
   Render domain (prod).
3. Copy Client ID + Secret into `.env`.
4. Scope used is read-only (`activity:read_all`).

Your Garmin Forerunner already syncs to Strava, so runs flow in automatically.

## Deploy to Render (always on)
1. Push this folder to a GitHub repo.
2. On render.com: New > Blueprint, point at the repo. `render.yaml` is detected.
3. Set env vars: STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET, and
   STRAVA_REDIRECT_URI = `https://YOUR-APP.onrender.com/auth/callback`.
4. Update the Strava app's Callback Domain to your Render domain.
5. Open the URL on your phone > Share > Add to Home Screen.

## Add to phone
Open the live URL on your phone browser, then "Add to Home Screen".
Launches full-screen like a native app, works offline for the shell.

## Customise
- `app/plan.py` — edit weekly sessions, paces, zone-2 HR ceiling.
- Set your real tested zone-2 HR cap; default `ZONE2_HR_MAX = 155`.
