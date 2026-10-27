# GB Wind Forecast Monitor

A web app for a UK utility's day-ahead trading team. It shows:

1. **The latest wind forecast available at decision time** (the day before delivery) for any delivery day, next to what actually happened.
2. **How accurate those forecasts are**: typical miss, bias, P10/P90 error range, error by lead time / hour / day, and how much a simple bias correction would help.

Data: Elexon BMRS, national GB wind only. [FUELHH](https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream) (actuals, `fuelType=WIND`) and [WINDFOR](https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/WINDFOR/stream) (forecasts). Scope: purchase decisions made in January 2026, so delivery days 2 Jan to 1 Feb 2026.

**Live app:** _<add Vercel URL here>_

**Video walkthrough:** _<add unlisted YouTube URL here>_

## Key results (decision time 10:00 the day before)

| | |
|---|---|
| Average miss (MAE) | 1,996 MW (17.7% of average wind output) |
| Bias | −1,728 MW: the forecast is usually **too high** |
| 80% error range | −4,184 MW to +503 MW |
| Simple walk-forward bias correction | MAE 1,991 → 1,464 MW (26.5% better) |

## How to run

### Option 1: Docker (recommended)
```bash
docker compose up --build
```
- App: http://localhost:8080
- API docs (Swagger): http://localhost:8000/docs

### Option 2: Without Docker
Requires Python 3.10+ and Node 20+.
```bash
# Terminal 1: backend
cd backend
pip install -r requirements-dev.txt
uvicorn app.main:app --reload            # http://localhost:8000

# Terminal 2: frontend
cd frontend
npm install
npm run dev                              # http://localhost:5173 (proxies /api to :8000)
```

### Run the tests
```bash
cd backend
pytest
```

### Refresh the data snapshot (optional)
The CSVs in `backend/data/` are already committed. To download them again from Elexon:
```bash
cd backend
python -m scripts.fetch_data
```

## Files and directories

| Path | What it is |
|---|---|
| `backend/app/config.py` | Constants: delivery date range, default decision hour, file paths |
| `backend/app/data_store.py` | Loads the CSV snapshot into pandas once |
| `backend/app/forecast.py` | **Core rule**: for each hour, the latest forecast published before the decision time |
| `backend/app/metrics.py` | MAE, RMSE, bias, percentiles, by-hour / by-day / by-horizon, histogram, bias correction |
| `backend/app/main.py` | FastAPI routes: `/api/health`, `/api/meta`, `/api/day-ahead`, `/api/accuracy` |
| `backend/data/` | Snapshot of Elexon data (forecasts and actuals, CSV) |
| `backend/scripts/fetch_data.py` | Downloads the data from the Elexon API |
| `backend/tests/` | pytest tests: selection rule (no look-ahead), metrics, API |
| `backend/Dockerfile` | Backend container |
| `frontend/src/App.jsx` | Page layout, decision-time selector, tabs |
| `frontend/src/components/DayAheadView.jsx` | Tab 1: forecast vs actual for one delivery day |
| `frontend/src/components/AccuracyView.jsx` | Tab 2: forecast accuracy analysis |
| `frontend/src/components/KpiCard.jsx`, `ChartCard.jsx` | Small reusable UI pieces |
| `frontend/src/api.js` | API calls and the `useApi` loading hook |
| `frontend/src/theme.js` | Chart colours (light/dark) and number formatting |
| `frontend/Dockerfile`, `frontend/nginx.conf` | Frontend container (build with Node, serve with nginx) |
| `docker-compose.yml` | Runs both containers together |
| `vercel.json` | Vercel deployment: two services (`backend` at `/api/*`, `frontend` at `/`) |
| `backend/.python-version` | Python version used by Vercel (3.12) |
| `ARCHITECTURE.md` | Design, data flow, domain notes and findings |
| `IMPLEMENTATION_PLAN.md` | The phase-by-phase build plan |

## Tech stack
React 18 + Vite + Recharts · Python 3.12 + FastAPI + pandas · Docker · Vercel

## Use of AI tools
This project was built with the help of **Claude Code (Anthropic)**, an AI coding assistant. It was used for
planning, researching the Elexon datasets, writing code, tests and documentation. I reviewed, ran and verified
all the code and results.
