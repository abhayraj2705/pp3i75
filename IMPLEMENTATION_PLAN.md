# Implementation Plan

Goal: a **simple, correct, well-explained** app, delivered quickly (budget ≤ 16 h). Read `ARCHITECTURE.md` first.

## Status

| Phase | Status |
|---|---|
| 0 Understand data | ✅ done |
| 1 Data snapshot | ✅ done |
| 2 Backend + tests | ✅ done (21 tests) |
| 3 Frontend | ✅ done |
| 4 Docker | ⏳ files ready, verifying build |
| 5 Vercel | ⏳ config ready, deploy needs the owner's Vercel login |
| 6 README/repo | ⏳ README done, public GitHub repo to create |
| 7 Video | ⏳ owner records |
| 8 Submit | ⏳ owner submits |

Note: decisions are *made* in January, so delivery days are **2 Jan → 1 Feb 2026**.

Guiding rule: **build the minimum that answers both questions very clearly.** Polish comes after correctness.

---

## Phase 0 — Understand & verify data (≈1 h)
- [ ] Read the Elexon docs for FUELHH and WINDFOR stream endpoints.
- [ ] Call both APIs by hand (curl / browser) for a few days of Jan 2026 and check:
  - WINDFOR is hourly, with runs about every 2–3 h, looking ~2–3 days ahead.
  - FUELHH is half-hourly. Filter on `fuelType=WIND`.
- [ ] Decide the default cutoff: **D-1 10:00 UK** (configurable).

API URLs:
```
https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELHH/stream?settlementDateFrom=2026-01-01&settlementDateTo=2026-01-31&fuelType=WIND
https://data.elexon.co.uk/bmrs/api/v1/datasets/WINDFOR/stream?publishDateTimeFrom=2025-12-29T00:00:00Z&publishDateTimeTo=2026-02-01T00:00:00Z
```

## Phase 1 — Data snapshot (≈1.5 h)
- [ ] `backend/scripts/fetch_data.py`
  - Download WINDFOR with `publishTime` from **29 Dec 2025 → 31 Jan 2026**, in 1-day chunks so responses stay small.
  - Download FUELHH WIND with `startTime` covering **1 Jan → 1 Feb 2026**.
  - Remove duplicates and save `forecasts_wind.csv` and `actuals_wind.csv`.
- [ ] Quick check in a Python shell: row counts, no gaps, value ranges look sane (wind 0–~22 GW).

## Phase 2 — Backend logic + tests (≈3 h)
- [ ] `config.py`, `data_store.py` (pandas load + `lru_cache`).
- [ ] `forecast.py`: `select_forecast(...)` and `day_ahead_series(date, cutoff_hour)`.
- [ ] `metrics.py`: MAE, RMSE, bias, nMAE, P10/P50/P90, by-hour, by-horizon, daily MAE, histogram bins.
- [ ] `tests/`:
  - forecast published **after** the cutoff is never used (most important test);
  - the latest run before the cutoff is chosen when several exist;
  - metrics on a tiny hand-made DataFrame equal hand-calculated values.
- [ ] `main.py`: `/api/health`, `/api/meta`, `/api/day-ahead`, `/api/accuracy`, with input validation (400 errors).
- [ ] Check in Swagger at `http://localhost:8000/docs`.

## Phase 3 — Frontend (≈4 h)
- [ ] `npm create vite@latest frontend -- --template react`, then `npm i recharts`.
- [ ] `api.js` with `getDayAhead(date, hour)` and `getAccuracy(hour)`.
- [ ] `App.jsx` with two tabs.
- [ ] `DayAheadView`: controls, "forecast used" label, forecast vs actual chart with P10–P90 band, KPI cards.
- [ ] `AccuracyView`: KPI cards, histogram, by-hour bars, by-horizon bars, daily MAE line, "what this means" text.
- [ ] Loading and error states (simple text is fine).
- [ ] Clean, consistent styling: one CSS file, a few colours, responsive enough for a laptop screen.

## Phase 4 — Docker (≈1 h)
- [ ] `backend/Dockerfile` (python:3.12-slim, `uvicorn app.main:app --host 0.0.0.0 --port 8000`).
- [ ] `frontend/Dockerfile` (node:20, `npm run dev -- --host`), or nginx for a build.
- [ ] `docker-compose.yml` with both services. Vite proxy `/api` → `http://backend:8000`.
- [ ] `docker compose up --build` works from a clean clone.

## Phase 5 — Deploy to Vercel (≈1.5 h)
- [ ] `api/index.py` imports the FastAPI app. Add a root `requirements.txt` for Vercel.
- [ ] `vercel.json`: build the frontend, route `/api/(.*)` → Python function, everything else → `index.html`.
- [ ] Make sure CSV paths work inside the serverless function (use paths relative to the file).
- [ ] Deploy and test the live URL in **incognito**.

## Phase 6 — README & repo (≈1 h)
- [ ] Create a **public** GitHub repo with a **random name** (e.g. `qx7m2k`). No personal or company names in the repo name.
- [ ] README: what it does, live link, how to run (Docker + manual), file/folder table, tests command, **AI tools used** (state clearly that Claude Code was used for planning and coding help), screenshots.
- [ ] Commit in small, meaningful steps (this history is part of what the reviewer sees).

## Phase 7 — Video (≈2 h, ≤ 10 min total)
**Part 1 — Client pitch (≤ 5 min)**
1. Their problem in one sentence: buying power the day before, while wind changes with the weather.
2. Live demo, Day-Ahead View: "this is exactly what you saw at 10:00 the day before".
3. Show a calm day and a stormy day (big miss) to show why the error matters.
4. Accuracy View: typical miss is X MW (Y %), bias, and the P10/P90 safety margin.
5. Value: hedge by the P90 margin rather than guessing. Next steps (solar, demand, live feed).

**Part 2 — Tech lead review (≤ 5 min)**
1. Architecture diagram (from this doc).
2. Data: why a snapshot, hourly vs half-hourly alignment.
3. Code walk: `forecast.py` (the cutoff rule) → `metrics.py` → API → React components.
4. Tests (run `pytest` live), Docker, Vercel config.
5. Trade-offs and limitations. Mention AI usage.

Upload as **Unlisted** on YouTube and check it in incognito.

## Phase 8 — Submit (≈0.5 h)
- [ ] Open the YouTube link, GitHub repo and Vercel app in incognito. All three must work without login.
- [ ] Fill the form: https://forms.cloud.microsoft/r/FTX6K2bbnU

---

## Time budget

| Phase | Hours |
|---|---|
| 0 Understand data | 1 |
| 1 Data snapshot | 1.5 |
| 2 Backend + tests | 3 |
| 3 Frontend | 4 |
| 4 Docker | 1 |
| 5 Vercel | 1.5 |
| 6 README/repo | 1 |
| 7 Video | 2 |
| 8 Submit | 0.5 |
| **Total** | **15.5** |

## What we deliberately do NOT build (keep it simple)
- No database (CSV + pandas is enough for ~1 month of data).
- No login, no Redux, no ML model of our own.
- No live Elexon calls on each request.
