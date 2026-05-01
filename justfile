image := "registry.digitalocean.com/uggiuggi/tog"
app   := "rejseplan-app"
tag   := `git rev-parse --short HEAD`

# Build, push, and deploy in one step
all: build push deploy

# Build the image for linux/amd64, tagged with git SHA and latest
build:
    docker buildx build --platform linux/amd64 --tag tog .
    docker tag tog {{image}}:{{tag}}
    docker tag tog {{image}}:latest

# Push both tags to DigitalOcean Container Registry
push:
    doctl registry login
    docker push {{image}}:{{tag}}
    docker push {{image}}:latest

# Update the app spec with the new image tag — triggers a real redeployment
deploy:
    #!/usr/bin/env bash
    set -euo pipefail
    APP_ID=$(doctl apps list --format ID,Spec.Name --no-header | awk '/{{app}}/ {print $1}')
    sed 's|tag: latest|tag: {{tag}}|' .do/app.yaml | doctl apps update "$APP_ID" --spec /dev/stdin

# Run locally with Docker Compose
dev:
    docker compose up --build app

# Run locally with uv (no Docker), loads env vars from .env
run:
    uv run --env-file .env uvicorn app:app --reload --host 0.0.0.0 --port 8080 --app-dir app
