# Rejseplan Departure Board

A minimal web app showing upcoming train departures from a fixed set of Copenhagen-area stops. Fetches live data from the Rejseplan public API and auto-refreshes every 60 seconds.

**Stations:** Lyngby · Kbh H · Nørreport · Nørrebro · Hellerup

## Prerequisites

- [just](https://github.com/casey/just) — command runner
- [Docker](https://www.docker.com/) — for building and running containers
- [doctl](https://docs.digitalocean.com/reference/doctl/) — DigitalOcean CLI (for deploy)
- `RPL_ACCESS_ID` — Rejseplan API key

## Local development

```bash
just dev    # Docker Compose → http://localhost:8088
just run    # uv (no Docker) → http://localhost:8080
```

For `just run`, set the API key first:

```bash
export RPL_ACCESS_ID=your_key_here
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

The app is configured in `.do/app.yaml` for DigitalOcean App Platform.
