# Rejseplan — Codebase Guide

## What this is

A minimal departure board for Copenhagen-area train stops. Fetches live data from the Rejseplan public API and renders it as a styled HTML table. Auto-refreshes every 60 seconds. Deployed on DigitalOcean App Platform via Docker.

## Tech stack

- **FastAPI** — routing and response rendering
- **pandas** — DataFrame manipulation for API data
- **Jinja2** — HTML templating (`app/static/form.html`)
- **requests.Session** — HTTP client for the Rejseplan API
- **uv** — package management (see global CLAUDE.md)
- **Docker** — containerized build and deployment

## Project layout

```
app/
  app.py                  # Routes, data processing, HTML rendering
  services/rejseplan.py   # Rejseplan API client + time helpers
  static/
    form.html             # Main template: station buttons, departure table
    table.css             # Light/dark mode + delay color classes
    sw.js                 # Service Worker (network-first, cache fallback)
    favicon.ico
    apple-touch-icon.png
Dockerfile
compose.yaml              # Local dev: localhost:8088
pyproject.toml            # Dependencies and tool config
.do/app.yaml              # DigitalOcean App Platform config
```

## Environment variables

| Variable | Purpose |
|---|---|
| `RPL_ACCESS_ID` | API key for the Rejseplan API (required) |

## Stations

Hardcoded list in `app/app.py`:

| Name | ID |
|---|---|
| Lyngby | 8600675 |
| Kbh H | 8600626 |
| Nørreport | 8600646 |
| Nørrebro | 8600642 |
| Hellerup | 8600655 |

## Request flow

```
GET / or /{board_id}
  → validate_board_id()         # 7-digit numeric check
  → RejsePlan.get_departure_board(station_id, max_journeys=45)
      → GET https://www.rejseplanen.dk/api/departureBoard
      → filter ProductAtStop.catOut in ["S-Tog", "Re", "IC"]
      → return DataFrame[stop, name, direction, time, rtTime]
  → get_delay_class()           # "on-time" / "delayed" / "very-delayed"
  → cal_new_time()              # "14:30" or "14:30 (+5)"
  → df.to_html() + string replacement to inject delay CSS classes on <tr>
  → render form.html
```

## Rejseplan API

**Base URL:** `https://www.rejseplanen.dk/api/`  
**Endpoint:** `GET /departureBoard`  
**Auth:** `accessId` query parameter  

Key response fields used:
- `Departure[].stop` — station name
- `Departure[].name` — line identifier (e.g. `S1`, `RE1`)
- `Departure[].direction` — destination
- `Departure[].time` — scheduled departure (`HH:MM:SS`)
- `Departure[].rtTime` — real-time departure (`HH:MM:SS`), absent if on time
- `Departure[].ProductAtStop.catOut` — train category (used to filter)

## Delay CSS classes

Applied as `class` attribute on `<tr>` elements:

| Class | Condition |
|---|---|
| `on-time` | No `rtTime`, or delay = 0 min |
| `delayed` | Delay < 5 min |
| `very-delayed` | Delay ≥ 5 min |

## Known rough edges

- Delay classes are injected via string replacement on the pandas HTML output — fragile but works
- No server-side caching; every request hits the external API
- No retry logic on timeouts
- Stations are hardcoded, not config-driven
- 60s auto-refresh is a `<meta>` tag, not controllable per-tab

## Running locally

```bash
docker compose up --build app
# → http://localhost:8088
```

Or directly (with `RPL_ACCESS_ID` set):

```bash
uv run uvicorn app:app --reload --host 0.0.0.0 --port 8080
```
