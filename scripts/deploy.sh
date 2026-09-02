#!/usr/bin/env bash
# Deploy Pothi Parivaar from this machine over SSH. Not a GitHub Action.
#
# Usage (from repo root):
#   ./scripts/deploy.sh
#
# Optional env (or source a local file):
#   POTHI_DEPLOY_USER   default: hermes
#   POTHI_DEPLOY_HOST   default: 100.79.172.22
#   POTHI_DEPLOY_PATH   default: /home/hermes/apps/pothi-parivaar
#   POTHI_HEALTH_URL    default: http://127.0.0.1:8000/api/health  (checked on the VPS)
#
# Does not use --delete. SQLite under data/ and the remote .venv are left in place.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ -f "$ROOT/scripts/deploy.env" ]]; then
  # shellcheck disable=SC1091
  source "$ROOT/scripts/deploy.env"
fi

USER_NAME="${POTHI_DEPLOY_USER:-hermes}"
HOST="${POTHI_DEPLOY_HOST:-100.79.172.22}"
REMOTE_PATH="${POTHI_DEPLOY_PATH:-/home/hermes/apps/pothi-parivaar}"
HEALTH_URL="${POTHI_HEALTH_URL:-http://127.0.0.1:8000/api/health}"
REMOTE="${USER_NAME}@${HOST}"

echo "==> Building frontend"
(cd "$ROOT/frontend" && npm run build)

echo "==> Copying files to ${REMOTE}:${REMOTE_PATH}"
ssh -o BatchMode=yes -o ConnectTimeout=20 "$REMOTE" "mkdir -p '${REMOTE_PATH}'"

rsync -az \
  --exclude '.git/' \
  --exclude '.venv/' \
  --exclude 'venv/' \
  --exclude '__pycache__/' \
  --exclude '.pytest_cache/' \
  --exclude 'node_modules/' \
  --exclude '.pnpm-store/' \
  --exclude '.vite/' \
  --exclude '_bmad/' \
  --exclude '_bmad-output/' \
  --exclude '.adal/' \
  --exclude '.agent/' \
  --exclude '.agents/' \
  --exclude '.claude/' \
  --exclude '.cline/' \
  --exclude '.opencode/' \
  --exclude '.cursor/' \
  --exclude 'data/*.db' \
  --exclude 'data/*.db-wal' \
  --exclude 'data/*.db-shm' \
  --exclude 'frontend/pnpm-lock.yaml' \
  --exclude 'frontend/pnpm-workspace.yaml' \
  --exclude 'scripts/deploy.env' \
  "$ROOT/" \
  "${REMOTE}:${REMOTE_PATH}/"

echo "==> Installing Python deps and restarting service"
ssh "$REMOTE" bash -s -- "$REMOTE_PATH" "$HEALTH_URL" <<'REMOTE'
set -euo pipefail
REMOTE_PATH="$1"
HEALTH_URL="$2"
cd "$REMOTE_PATH"
if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -r requirements.txt
systemctl --user daemon-reload
systemctl --user enable --now pothi-parivaar.service
systemctl --user restart pothi-parivaar.service
sleep 2
systemctl --user --no-pager --full status pothi-parivaar.service | head -20
curl -fsS "$HEALTH_URL"
echo
REMOTE

echo "==> Deploy finished"
