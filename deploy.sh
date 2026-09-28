#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

# nvm-managed node isn't on PATH over non-interactive SSH or launchd.
if [ -d "$HOME/.nvm/versions/node" ]; then
  node_bin="$(ls -d "$HOME"/.nvm/versions/node/*/bin 2>/dev/null | sort -V | tail -1 || true)"
  [ -n "$node_bin" ] && export PATH="$node_bin:$PATH"
fi

if [ -z "${SKIP_PULL:-}" ]; then
  echo "==> Updating checkout"
  git fetch origin main
  git reset --hard origin/main
fi

echo "==> Installing dependencies"
if [ -f package-lock.json ]; then
  npm ci
else
  npm install
fi

echo "==> Typechecking"
npm run check

echo "==> Building"
npm run build

# Publish only after a clean build so a failure can't empty the live directory.
echo "==> Publishing to live/"
mkdir -p live
rsync -a --delete dist/ live/

echo "==> Health check"
code="$(curl -sk -o /dev/null -w '%{http_code}' \
  --resolve app.joanchirinos.com:443:127.0.0.1 \
  https://app.joanchirinos.com/ || true)"
if [ "$code" != "200" ]; then
  echo "Health check failed (HTTP $code)" >&2
  exit 1
fi

echo "==> Deployed (HTTP $code)"
