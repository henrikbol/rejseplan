# Rejseplan Departure Board

A minimal web app showing upcoming train departures from a fixed set of Copenhagen-area stops. Fetches live data from the Rejseplan public API and auto-refreshes every 60 seconds. Click any departure row to see the vehicle's live position on a map.

**Stations:** Lyngby · Kbh H · Nørreport · Nørrebro · Hellerup

## Prerequisites

- [just](https://github.com/casey/just) — command runner
- [Docker](https://www.docker.com/) — for building and running containers
- [doctl](https://docs.digitalocean.com/reference/doctl/) — DigitalOcean CLI (for deploy)

## Environment variables

| Variable | Description |
|---|---|
| `RPL_ACCESS_ID` | Rejseplan API key |
| `STADIA_API_KEY` | Stadia Maps API key — free tier at [stadiamaps.com](https://stadiamaps.com) |

Create a `.env` file in the project root with these values for local development.

## Local development

```bash
just dev    # Docker Compose → http://localhost:8088
just run    # uv, loads .env automatically → http://localhost:8080
```

## Deploy to DigitalOcean

Build, push, and redeploy in one command:

```bash
just
```

Or run steps individually:

```bash
just build    # Build linux/amd64 image
just push     # Push to DigitalOcean Container Registry
just deploy   # Trigger redeployment on App Platform
```

The app is configured in `.do/app.yaml`. Set `RPL_ACCESS_ID` and `STADIA_API_KEY` as secrets in the DigitalOcean App Platform dashboard.
