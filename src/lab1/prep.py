"""Stage 2: clean both days, repair the clock, write prep_*.json and results/clock_evidence.json"""
from lab1.common import *
import sys
if __name__ == "__main__":
    out = {}
    for k in DAYS:
        t = time.time(); df, info = load_day(k, force=True)
        print(k, {a: b for a, b in info.items() if a not in ("features", "clock_evidence", "hour_hist_raw", "hour_hist_fixed")}, round(time.time() - t), "s", flush=True)
        for lab, e in info["clock_evidence"].items(): print("  ", lab, e)
        print("  hours raw", info["hour_hist_raw"]); print("  hours fixed", info["hour_hist_fixed"])
