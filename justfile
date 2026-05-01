image := "registry.digitalocean.com/uggiuggi/tog"
app   := "tog"
tag   := `git rev-parse --short HEAD`

# Build, push, and deploy in one step
all: login build deploy

# Login to DigitalOcean Container Registry
login:
    doctl registry login

# Build linux/amd64 image and push directly to registry
build:
    docker buildx build --platform linux/amd64 \
        --provenance=false \
        --tag {{image}}:{{tag}} \
        --tag {{image}}:latest \
        --push .

# Trigger a new deployment — pulls the latest image without touching the spec or secrets
deploy:
    #!/usr/bin/env bash
    set -euo pipefail
    APP_ID=$(doctl apps list --no-header --format ID,Spec.Name | awk '$2 == "{{app}}" {print $1}')
    if [[ -z "$APP_ID" ]]; then
        echo "Could not find app '{{app}}'. Available apps:"
        doctl apps list --format ID,Spec.Name
        exit 1
    fi
    doctl apps create-deployment "$APP_ID"

# Push secrets from .env to the DO app spec
set-env:
    #!/usr/bin/env bash
    set -euo pipefail
    set -a; source .env; set +a
    APP_ID=$(doctl apps list --no-header --format ID,Spec.Name | awk '$2 == "{{app}}" {print $1}')
    if [[ -z "$APP_ID" ]]; then
        echo "Could not find app '{{app}}'."
        exit 1
    fi
    awk -v RPL="$RPL_ACCESS_ID" -v STADIA="$STADIA_API_KEY" '
        /key: RPL_ACCESS_ID/  { print; print "    value: " RPL;    next }
        /key: STADIA_API_KEY/ { print; print "    value: " STADIA; next }
        { print }
    ' .do/app.yaml | doctl apps update "$APP_ID" --spec /dev/stdin
    echo "Secrets synced to DO."

# Show status of the latest deployment
status:
    #!/usr/bin/env bash
    APP_ID=$(doctl apps list --no-header --format ID,Spec.Name | awk '$2 == "{{app}}" {print $1}')
    doctl apps list-deployments "$APP_ID" --no-header --format ID,Phase,Progress,CreatedAt | head -5

# Format, lint, and type-check
fmt:
    uv run ruff format .

lint:
    uv run ruff check --fix .

check:
    uv run ty check app/app.py app/services/

# Run all code quality checks
qa: fmt lint check

# Run locally with Docker Compose
dev:
    docker compose up --build app

# Run locally with uv (no Docker), loads env vars from .env
run:
    #!/usr/bin/env bash
    cd app && uv run --env-file ../.env uvicorn app:app --reload --host 0.0.0.0 --port 8080
