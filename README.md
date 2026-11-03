# SEC-635 Lab 1: AI-driven intrusion detection on CSE-CIC-IDS2018 (revision repo)

Supervised (Task 1) and unsupervised (Task 2) detection on Wednesday 14-02-2018 (FTP/SSH brute force) and Thursday 01-03-2018 (infiltration).
Every number comes from code in this repo. Start with `RESULTS_SUMMARY.md` (values, sources, and the list of results that contradict or weaken the first report) and `CHANGES.md` (old -> new values).
Status: experiments, figures and the PDF report are done. The report is built from `results/` by `report/build_report.py` (WeasyPrint); `report/original/` keeps the first docx version for reference.

Clone: `git clone https://github.com/MZU-GH/SEC-635-Lab-1`

## Setup
```
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt   # pinned versions; Python 3.13, 4 CPUs, 15 GB RAM used
scripts/download_data.sh                                              # downloads both CSVs into data/raw/ (not committed), writes results/data_manifest.json
```
## Run everything
`./run_all.sh` runs download, prep, task1, timing, task2 (both days in parallel), the DBSCAN min_samples edge check, figures and `results/report_numbers.json`. Per-stage wall times go to `logs/stage_times.log`, the environment to `results/environment.json`.
The last two stages build the PDF (`report`) and check its numbers (`check`). Individual stages: `cd src && ../.venv/bin/python -m lab1.<prep|task1|timing|task2 wed|task2 thu|task2 merge|dbscan_ms_check wed|figures|report_numbers|summary>`.

## Run times (the stages were run one by one, partly concurrently, so times are inflated; `run_all.sh` itself was not run end to end)
| Stage | Wall time |
|---|---|
| download | seconds |
| prep (both days) | about 2 min |
| task1 (tuning, 3 splits, random split, clock demo) | about 93 min (shared the 4 CPUs with task2; MLP on 730k rows alone took 31 min) |
| timing (clean re-timing of chosen models, Wed 80% and Thu 70%) | about 7 min |
| task2 Wednesday / Thursday (in parallel) | 7,262 s / 5,380 s (`runtime_s` in `results/task2_*.json`) |
| DBSCAN min_samples edge check | about 10 to 30 min per day |
| figures, report_numbers, summary | about 1 min |

## File map
- `src/lab1/common.py` load, clean, clock repair, features, metrics, Poisson CI, block bootstrap, McNemar
- `src/lab1/prep.py` -> `results/prep_{wed,thu}.json` (cleaning counts per step, constant columns, clock evidence per label before/after)
- `src/lab1/task1.py` -> `results/task1_results.json`, `task1_sensitivity.csv` (tuning grid), `timing.py` -> `task1_timing.json`
- `src/lab1/task2.py` -> `results/task2_{wed,thu}.json`, `task2_grid*.csv` (every grid point), `task2_extra_sweeps*.csv` (PCA dims, sample size, triage size, analyst error x seeds)
- `src/lab1/dbscan_ms_check.py` -> `results/task2_dbscan_ms_check_*.json`, `task2_dbscan_ms_extension_*.csv`
- `src/lab1/rules.py` port 21/22 rule and zero-payload/short-duration rule
- `src/lab1/figures.py` -> `figures/fig1..fig5*.png` (6.5 in wide, fonts >= 8 pt, 300 dpi)
- `src/lab1/report_numbers.py` -> `results/report_numbers.json` (flat `{key: {value, text, source}}`)
- `src/lab1/summary.py` -> `RESULTS_SUMMARY.md`, `CHANGES.md`
- `report/original/SEC635_Lab1_Report_v1.docx` baseline, unchanged.

## Method notes and deviations (details in RESULTS_SUMMARY.md)
- Tuning only when the validation window and the fit part each hold >= 100 attack flows (the plan only required the validation window); tuning fits use every 4th row.
- The published attack schedule on the UNB page could not be fetched (proxy refused), so only data-internal clock evidence is given.
- Task 2 false alerts/day: the experiment code reports sample FPR x benign flows x 24/12 (brief's 12 h capture). The report rescales to the measured span, `reported x 12 / span_hours_measured` (9.0 h Wed, 9.5 h Thu), so both tasks use the traffic rate in the data. `results/task2_*.json` still hold the 12 h values.
- GMM grid extended to 120 components on Wednesday; BIC never turned. DBSCAN min_samples is at the grid edge on both days; extension to 100/200 is reported.
- Raw data and `.venv/` are not committed.

## Report
Notes on the docx-to-PDF move, the Task 2 false-alert convention change (old and new values) and display choices: see `REPORT_NOTES.md`.
```
.venv/bin/python report/build_report.py        # -> report/SEC635_Lab1_Report.pdf (+ .html), results/report_registry.json
.venv/bin/python scripts/check_report_numbers.py   # -> results/evidence_map.csv, exit 1 on any unmatched number
```
- `report/template.html.j2` holds the prose and contains no data numbers; every number is `{{ n.key }}` from a registry built in `report/build_report.py` from `results/*.json|csv` (derived values carry their formula and sources). A missing key fails the build. `report/style.css` holds all styling (A4, Inter font).
- `results/report_registry.json` lists every printed number: key, text, raw value, source or formula. The check script extracts the PDF text, ignores course code, dates, IDs, table/figure/section numbers, citations, TOC and footer, and requires every other number to equal a registry entry; `results/evidence_map.csv` maps each token to its key and source.
- The build needs only `results/` and `figures/`, not the raw data. Fonts: Inter must be installed system-wide.
- Convention for Task 2 false alerts/day: see the measured-span note above. Task 1 and Task 2 false-alert numbers are never compared in one table row.
