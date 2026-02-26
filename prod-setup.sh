#!/usr/bin/env bash
set -euo pipefail

# ── Validate .env ──────────────────────────────────────────────────────
ENV_FILE="./.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "ERROR: $ENV_FILE not found. Copy .env.template to .env and fill in values."
    exit 1
fi

REQUIRED_VARS=(
    OPENAI_API_KEY
    JUPYTERHUB_URL
    MONGO_INITDB_ROOT_USERNAME
    MONGO_INITDB_ROOT_PASSWORD
    FLASK_SECRET_KEY
)

set -a
source "$ENV_FILE"
set +a

MISSING=0
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var:-}" ]; then
        echo "ERROR: $var is not set in $ENV_FILE"
        MISSING=1
    fi
done

if [ "$MISSING" -ne 0 ]; then
    echo "Fix the missing variables above, then re-run."
    exit 1
fi

echo "All required environment variables are set."

# ── Write secrets files ───────────────────────────────────────────────
SECRETS_DIR="./secrets"
mkdir -p "$SECRETS_DIR"

write_secret() {
    local file="$SECRETS_DIR/$1"
    printf '%s' "$2" > "$file"
    chmod 600 "$file"
}

write_secret "openai_api_key" "$OPENAI_API_KEY"
write_secret "mongo_username" "$MONGO_INITDB_ROOT_USERNAME"
write_secret "mongo_password" "$MONGO_INITDB_ROOT_PASSWORD"
write_secret "flask_secret_key" "$FLASK_SECRET_KEY"

chmod 700 "$SECRETS_DIR"
echo "Secrets written to $SECRETS_DIR/"

# ── Build & deploy ─────────────────────────────────────────────────────
docker compose -f docker-compose.prod.yml build --no-cache
docker compose -f docker-compose.prod.yml up -d

echo "Production deployment complete."
