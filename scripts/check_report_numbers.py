#!/usr/bin/env python3
"""Check that every number printed in the report PDF is a registered number.

    .venv/bin/python scripts/check_report_numbers.py

Extracts the PDF text (pdftotext -layout), tokenises numbers, drops the allowed
non-data tokens (course code, dates, student IDs, table/figure/section numbers,
citations, TOC and footer page numbers, the References section) and requires every
remaining token to occur in the text of a registry entry (results/report_registry.json).
Writes results/evidence_map.csv and exits non-zero on any unmatched token.
"""
import csv, json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF = os.path.join(ROOT, "report", "SEC635_Lab1_Report.pdf")
REG = os.path.join(ROOT, "results", "report_registry.json")
OUT = os.path.join(ROOT, "results", "evidence_map.csv")

TOKEN = re.compile(r"(?<![A-Za-z0-9.])(\d{1,2}:\d{2}|\d+(?:,\d{3})*(?:\.\d+)?)%?")
IGNORE = [
    r"SEC-635", r"CSE-CIC-IDS2018", r"IDS2018", r"M8000\d+",
    r"\d{2}-\d{2}-2018", r"3 November 2026", r"Fall 2026", r"\b2018\b",
    r"\b(?:Task|Lab|Table|Figure|Section)s? \d+(?:\.\d+)?(?:[,–-]\d+)?", r"\[\d+(?:[,–-]\s*\d+)*\]",
    r"21/22", r"\bPC\d\b", r"Page \d+ of \d+", r"\b[Ff]\d\b",
]
IGN = re.compile("|".join(IGNORE))
HEAD = re.compile(r"^\s*\d(?:\.\d)?\s{1,3}(?=[A-Z])")
LEADER = re.compile(r"(\. ){3,}|\.{4,}")


def tokens(s):
    s = IGN.sub(" ", s)
    return [m.group(1) for m in TOKEN.finditer(s)]


def main():
    reg = json.load(open(REG))
    known = {}
    for k, v in reg.items():
        for t in tokens(str(v["text"])):
            known.setdefault(t, []).append(k)
    raw = subprocess.run(["pdftotext", "-layout", PDF, "-"], capture_output=True, text=True, check=True).stdout
    pages = raw.split("\f")
    cover = pages[0]
    for need in ("SEC-635 – AI for Cybersecurity", "Fall 2026", "Lab 1 — AI-Driven Detection", "Ahmed Alnuaimi", "M80009405", "Mansour Alkaabi", "M80009410",
                 "Ahmed Almansoori", "M80009548", "Instructor", "Dr. Ahmad Samer Wazan", "3 November 2026", "github.com/MZU-GH/SEC-635-Lab-1"):
        if need.lower() not in cover.lower():
            print("COVER MISSING:", need); sys.exit(1)
    body = "\n".join(pages[1:])
    lines = body.splitlines()
    cut = max(i for i, l in enumerate(lines) if l.strip() == "References")
    lines = lines[:cut]
    rows, bad, n = [], [], 0
    for ln in lines:
        if "AI-Driven Detection" in ln and "Page" in ln: continue
        if LEADER.search(ln): continue
        l2 = HEAD.sub("", ln)
        for t in tokens(l2):
            n += 1
            key = known.get(t)
            if key is None and t.rstrip(",") in known: key = known[t.rstrip(",")]
            rows.append((t, ln.strip()[:140], key[0] if key else "", reg[key[0]]["source"] if key else ""))
            if key is None: bad.append((t, ln.strip()))
    with open(OUT, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["token", "context", "key", "source"]); w.writerows(rows)
    if bad:
        print(f"FAIL: {len(bad)} unmatched of {n} tokens")
        for t, l in bad: print(f"  {t!r}: {l[:150]}")
        sys.exit(1)
    print(f"PASS: {n} number tokens checked against {len(reg)} registry entries; evidence map in results/evidence_map.csv")


if __name__ == "__main__":
    main()
