#!/usr/bin/env bash
# Download the two CSE-CIC-IDS2018 days and record size + sha256 (results/data_manifest.json)
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p data/raw results
BASE="https://cse-cic-ids2018.s3.ca-central-1.amazonaws.com/Processed%20Traffic%20Data%20for%20ML%20Algorithms"
for f in Wednesday-14-02-2018_TrafficForML_CICFlowMeter.csv Thursday-01-03-2018_TrafficForML_CICFlowMeter.csv; do
  [ -s "data/raw/$f" ] || curl -L --fail -o "data/raw/$f" "$BASE/$f"
done
python3 - <<'P'
import hashlib, json, os
out = {}
d = "data/raw"
for f in sorted(os.listdir(d)):
    p = os.path.join(d, f); h = hashlib.sha256()
    with open(p, "rb") as fh:
        for ch in iter(lambda: fh.read(1 << 20), b""): h.update(ch)
    out[f] = {"bytes": os.path.getsize(p), "sha256": h.hexdigest()}
json.dump(out, open("results/data_manifest.json", "w"), indent=2)
print(out)
P
