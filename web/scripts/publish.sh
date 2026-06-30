#!/usr/bin/env bash
# Regenerate dashboard data and push to GitHub (triggers Pages deploy).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

REPO="${GITHUB_REPO:-mapledong/china_stock_strategy}"
DEFAULT_BRANCH="${DEFAULT_BRANCH:-main}"

echo "==> Building dashboard data..."
.venv/bin/python web/scripts/build_data.py

echo "==> Staging web assets..."
git add web/ .github/workflows/deploy-dashboard.yml

if git diff --cached --quiet; then
  echo "No web changes to commit."
else
  git commit -m "$(cat <<'EOF'
Update strategy dashboard for public Pages deploy.

EOF
)"
fi

if ! git remote get-url origin &>/dev/null; then
  echo ""
  echo "No git remote 'origin' configured."
  echo "Create a GitHub repo, then run:"
  echo "  git remote add origin git@github.com:<USER>/<REPO>.git"
  echo "  git push -u origin main"
  echo ""
  echo "Then enable GitHub Pages: Settings → Pages → Source: GitHub Actions"
  exit 0
fi

echo "==> Pushing to origin..."
git push origin HEAD

echo ""
echo "Deploy workflow will run on GitHub Actions."
echo "After it finishes, open: https://mapledong.github.io/china_stock_strategy/"
