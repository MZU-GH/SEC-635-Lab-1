#!/usr/bin/env bash
# Reproduce everything from the raw CSVs to the final PDF. Wall time per stage goes to logs/stage_times.log
set -euo pipefail
cd "$(dirname "$0")"; ROOT=$(pwd)
[ -d .venv ] || { python3 -m venv .venv; .venv/bin/pip install -r requirements.txt; }
PY=.venv/bin/python
mkdir -p logs results figures data/raw
: > "$ROOT/logs/stage_times.log"
stage() { local name="$1"; shift; local t0=$(date +%s); echo "== $name"; "$@" 2>&1 | tee "$ROOT/logs/$name.log"; local dt=$(( $(date +%s) - t0 )); echo "$name ${dt}s" | tee -a "$ROOT/logs/stage_times.log"; }
stage download   scripts/download_data.sh
$PY - <<'P'
import json, platform, os, importlib.metadata as m
env = {"python": platform.python_version(), "cpus": os.cpu_count(), "platform": platform.platform(),
       "packages": {p: m.version(p) for p in ("scikit-learn", "pandas", "numpy", "scipy", "matplotlib")}}
os.makedirs("results", exist_ok=True); json.dump(env, open("results/environment.json", "w"), indent=2)
P
cd src
stage prep       ../$PY -m lab1.prep
stage task1      ../$PY -m lab1.task1
stage timing     ../$PY -m lab1.timing
# Task 2: the two days are independent; run them in parallel
t0=$(date +%s)
( ../$PY -m lab1.task2 wed > ../logs/task2_wed.log 2>&1 & ../$PY -m lab1.task2 thu > ../logs/task2_thu.log 2>&1 & wait )
../$PY -m lab1.task2 merge
stage dbscan_ms_wed ../$PY -m lab1.dbscan_ms_check wed
stage dbscan_ms_thu ../$PY -m lab1.dbscan_ms_check thu
echo "task2 $(( $(date +%s) - t0 ))s" | tee -a ../logs/stage_times.log
stage figures    ../$PY -m lab1.figures
stage numbers    ../$PY -m lab1.report_numbers
# Report: build the PDF from results/ and figures/ only, then check every printed number against the registry
cd ..
stage report     $PY report/build_report.py
stage check      $PY scripts/check_report_numbers.py
