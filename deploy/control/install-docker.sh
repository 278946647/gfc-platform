#!/usr/bin/env bash
# Control plane one-shot install on Ubuntu 20.04+ (Docker + docker-compose).
#
# Usage (repo already at /opt/gfc):
#   cd /opt/gfc && sudo bash deploy/control/install-docker.sh
#
# Or clone from GitHub:
#   sudo bash deploy/control/install-docker.sh --clone https://github.com/USER/gfc-platform.git /opt/gfc
set -euo pipefail

REPO=""
CLONE_URL=""
CLONE_DIR="/opt/gfc"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --clone)
      CLONE_URL=${2:-}
      CLONE_DIR=${3:-/opt/gfc}
      shift 3
      ;;
    -h|--help)
      echo "Usage: sudo bash deploy/control/install-docker.sh [--clone URL DIR]"
      exit 0
      ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

if [[ $EUID -ne 0 ]]; then
  echo "Run as root: sudo bash $0"
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq git curl ca-certificates docker.io docker-compose

systemctl enable --now docker

if [[ -n "$CLONE_URL" ]]; then
  mkdir -p "$(dirname "$CLONE_DIR")"
  if [[ -d "$CLONE_DIR/.git" ]]; then
    echo "==> git pull $CLONE_DIR"
    git -C "$CLONE_DIR" pull --ff-only
  else
    echo "==> git clone $CLONE_URL -> $CLONE_DIR"
    git clone "$CLONE_URL" "$CLONE_DIR"
  fi
fi

if [[ ! -f "${CLONE_DIR}/docker-compose.yml" ]]; then
  SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
  CLONE_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
fi

cd "$CLONE_DIR"

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "==> Created $CLONE_DIR/.env — edit secrets before production use"
fi

if docker compose version >/dev/null 2>&1; then
  COMPOSE=(docker compose)
else
  COMPOSE=(docker-compose)
fi

echo "==> Building and starting control plane..."
"${COMPOSE[@]}" up -d --build

echo ""
echo "==> Done"
"${COMPOSE[@]}" ps
echo ""
echo "API:  http://$(hostname -I | awk '{print $1}'):8080/healthz"
echo "Web:  http://$(hostname -I | awk '{print $1}'):5173"
echo ""
echo "Verify:"
echo "  curl -fsS http://127.0.0.1:8080/healthz"
echo "  ${COMPOSE[*]} exec api printenv GFC_BOOTSTRAP_TOKENS"
echo "  ${COMPOSE[*]} exec api curl -fsS https://api.ipify.org"
