#!/usr/bin/env bash
# Push refreshed web/data to GitHub — triggers Pages deploy only (no local research).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

if [[ ! -f web/data/strategies.json ]]; then
  echo "Missing web/data/strategies.json — run web/scripts/daily_update.sh locally first." >&2
  exit 1
fi

echo "==> Staging dashboard assets (web/ only)..."
git add web/

if git diff --cached --quiet; then
  echo "No web changes to publish."
  exit 0
fi

git commit -m "$(cat <<'EOF'
Publish strategy dashboard data.

EOF
)"

if ! git remote get-url origin &>/dev/null; then
  echo ""
  echo "No git remote 'origin' configured."
  echo "  git remote add origin git@github.com:mapledong/china_stock_strategy.git"
  echo "  git push -u origin main"
  exit 1
fi

echo "==> Pushing to origin (GitHub Pages will redeploy)..."
git push origin HEAD

echo ""
echo "Live site: https://mapledong.github.io/china_stock_strategy/"
