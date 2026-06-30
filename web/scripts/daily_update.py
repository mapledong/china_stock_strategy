#!/usr/bin/env python3
"""Local pipeline: refresh strategy research outputs and export dashboard JSON.

Runs on your Mac only. Does not push to GitHub — use web/scripts/publish.sh after review.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
BUILD = ROOT / "web" / "scripts" / "build_data.py"

RESEARCH_STEPS: tuple[tuple[str, Path], ...] = (
    ("ETF momentum (Tushare)", SRC / "qtlight" / "etf_momentum_rotation.py"),
    ("AH discount (Tushare)", SRC / "qtlight" / "ah_tushare_backtest.py"),
    ("Dividend / ChiNext rotation", SRC / "qtlight" / "dividend_chinext_momentum_research.py"),
    ("Equity incentive daily slots", SRC / "qtlight" / "equity_incentive_daily_slot_backtest.py"),
)

EVENT_STUDY_STEP = ("Tushare equity incentive event study", SRC / "qtlight" / "equity_incentive_tushare_event_study.py")


def _env() -> dict[str, str]:
    env = os.environ.copy()
    pythonpath = os.pathsep.join({str(ROOT), str(SRC), env.get("PYTHONPATH", "")}).strip(os.pathsep)
    env["PYTHONPATH"] = pythonpath
    env.setdefault("MPLCONFIGDIR", str(ROOT / ".matplotlib-cache"))
    return env


def _run_step(label: str, script: Path, env: dict[str, str]) -> None:
    if not script.exists():
        raise FileNotFoundError(f"Missing script for {label}: {script}")
    print(f"\n==> {label}")
    subprocess.run([sys.executable, str(script)], cwd=ROOT, env=env, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--event-study",
        action="store_true",
        help="Also refresh Tushare strict-core event study CSVs (slow; run weekly).",
    )
    parser.add_argument(
        "--skip-research",
        action="store_true",
        help="Only rebuild web/data from existing results/ files.",
    )
    args = parser.parse_args()

    started = datetime.now(timezone.utc)
    print(f"Daily strategy update started at {started.isoformat()}")
    print(f"Project root: {ROOT}")

    if not (ROOT / ".env").exists() and not os.getenv("TUSHARE_TOKEN"):
        print(
            "Warning: TUSHARE_TOKEN not set (.env missing). "
            "Tushare steps may fail; set secrets for CI or copy .env locally.",
            file=sys.stderr,
        )

    env = _env()
    (ROOT / "results").mkdir(parents=True, exist_ok=True)
    (ROOT / "data" / "raw").mkdir(parents=True, exist_ok=True)
    (ROOT / ".matplotlib-cache").mkdir(parents=True, exist_ok=True)

    if not args.skip_research:
        for label, script in RESEARCH_STEPS:
            _run_step(label, script, env)
        if args.event_study:
            label, script = EVENT_STUDY_STEP
            _run_step(label, script, env)

    print("\n==> Export dashboard JSON")
    subprocess.run([sys.executable, str(BUILD)], cwd=ROOT, env=env, check=True)

    finished = datetime.now(timezone.utc)
    print(f"\nDone in {(finished - started).total_seconds():.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
