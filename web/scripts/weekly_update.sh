#!/usr/bin/env bash
# Friday weekly job: refresh all strategies → publish GitHub Pages → email holdings report.
# Suggested schedule: Friday 17:00 Asia/Shanghai (see com.mapledong.china-stock-strategy-weekly.plist.example).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

PYTHON="${PYTHON:-$ROOT/.venv/bin/python}"
if [[ ! -x "$PYTHON" ]]; then
  PYTHON="$(command -v python3)"
fi

mkdir -p "$ROOT/results"
LOG="$ROOT/results/weekly_update.log"
exec > >(tee -a "$LOG") 2>&1

echo "========================================"
echo "Weekly update started: $(date '+%Y-%m-%d %H:%M:%S %z')"
echo "Root: $ROOT"
echo "========================================"

# Refresh research + web/data, then push public site.
web/scripts/daily_update.sh --publish

echo ""
echo "==> Building / sending weekly email report..."
"$PYTHON" web/scripts/weekly_report.py --send

echo ""
echo "Weekly update finished: $(date '+%Y-%m-%d %H:%M:%S %z')"
echo "Live site: https://mapledong.github.io/china_stock_strategy/"
