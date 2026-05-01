image := "registry.digitalocean.com/uggiuggi/tog"
app   := "rejseplan-app"

# Build, push, and deploy in one step
all: build push deploy

# Build the image for linux/amd64
build:
    docker buildx build --platform linux/amd64 --tag tog .
    docker tag tog {{image}}

# Push image to DigitalOcean Container Registry
push:
    doctl registry login
    docker push {{image}}

# Trigger a redeployment on DigitalOcean App Platform
deploy:
    doctl apps list --format ID,Spec.Name --no-header \
        | awk '/{{app}}/ {print $1}' \
        | xargs -I{} doctl apps create-deployment {}

# Run locally with Docker Compose
dev:
    docker compose up --build app

# Run locally with uv (no Docker)
run:
    uv run uvicorn app:app --reload --host 0.0.0.0 --port 8080 --app-dir app
