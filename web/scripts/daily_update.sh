#!/usr/bin/env bash
# Local daily job: refresh Tushare data → rerun strategies → export web/data.
# Does NOT push to GitHub. Run publish.sh when you are ready to update the public site.
# Suggested schedule: every day 18:00 Asia/Shanghai (see com.mapledong.china-stock-strategy-daily.plist.example).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

PYTHON="${PYTHON:-$ROOT/.venv/bin/python}"
if [[ ! -x "$PYTHON" ]]; then
  PYTHON="$(command -v python3)"
fi

EVENT_STUDY=0
SKIP_RESEARCH=0
PUBLISH=0
for arg in "$@"; do
  case "$arg" in
    --event-study) EVENT_STUDY=1 ;;
    --skip-research) SKIP_RESEARCH=1 ;;
    --publish) PUBLISH=1 ;;
  esac
done

ARGS=()
[[ "$EVENT_STUDY" -eq 1 ]] && ARGS+=(--event-study)
[[ "$SKIP_RESEARCH" -eq 1 ]] && ARGS+=(--skip-research)

echo "==> Local strategy update (research + web/data)..."
"$PYTHON" web/scripts/daily_update.py "${ARGS[@]}"

echo ""
echo "Local dashboard refreshed: web/data/"
echo "Review locally: cd web && python3 -m http.server 8777"

if [[ "$PUBLISH" -eq 1 ]]; then
  echo ""
  echo "==> Publishing to GitHub..."
  web/scripts/publish.sh
else
  echo "When ready for the public site: web/scripts/publish.sh"
fi
