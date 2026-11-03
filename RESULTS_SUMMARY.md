# RESULTS_SUMMARY

Every value below is read from `results/report_numbers.json` (written by `src/lab1/report_numbers.py` from the result files); the last column gives the file and the JSON key. Task 1 false alerts/day = benign flagged / test-window hours x 24 (exact Poisson 95% CI). Task 2 false alerts/day = sample FPR x day's benign flows x 24/12 (brief's 12 h capture). The two conventions are not comparable. Task 1 train times in `task1_results.json` were measured while other jobs shared the 4 CPUs; clean re-timings for Wed 80% and Thu 70% are in `task1_timing.json`.

## Flags: results that contradict or weaken v1 claims (read first)

1. **Leakage claim was confounded.** v1: random split F1 1.000 vs time split 0.000. Like for like the RF gap is small: Wed random 1.000 vs Wed 80% time split 0.9999 (gap 0.000); Thu random 0.489 vs Thu 70% 0.387 (gap 0.102), and the random value is **inside** the time-split block-bootstrap CI [0.231, 0.504]. The Wed 70% comparison (RF F1 0.0003) mixes leakage with an unseen attack type. Source: `task1_results.json#random_split`, `#splits`.

2. **Clock defect demo.** Unrepaired clock, RF 70/30: Wed F1 1.000 (trains on raw 01:00-11:03, tests on raw 11:03-12:59); Thu F1 0.592 (higher than the honest 0.387). `task1_results.json#unrepaired_clock`.

3. **Port 21/22 rule vs RF on the Task 1 windows.** Wed 70% (SSH unseen): rule recall 1.000, F1 0.9998, 429 FA/day [330-549] versus RF recall 0.0002. Wed 80% (seen): rule F1 0.9998, 361 FA/day [263-485] vs RF F1 0.9999, 49 FA/day [18-107]; the intervals do not overlap and McNemar rule-vs-RF p=0.01 (b=22, c=44). **The rule roughly matches RF on detection; RF's measured advantage is ~312 fewer false alerts/day, and the rule is the only one catching unseen SSH.** Thu 70%: rule recall 0.8% at 4,389 FA/day. `task1_results.json#splits.*.port_rule`.

4. **49/day rests on 6 false positives.** Reproduced: 49/day, exact Poisson 95% CI [18, 107] (MLP 74 [34-140]). Wed 80% shares one SSH campaign between train and test, so it is an optimistic bound. `#splits.wed80.models.*.fa`.

5. **RF vs MLP on Wed 80% is a tie, not a win.** McNemar p=1.00 (b=5, c=4), FA CIs overlap, clean train times 92 s vs 96 s. Only Thursday separates them slightly (F1 0.387 vs 0.263; recall at 1,000/day budget 1.5% vs 0.1%).

6. **Tuning outcome.** Wed 70% validation window holds **10,683 attack flows (>= 100, all FTP; fit part 182,671)**, so it WAS tuned (the plan expected it would not be). Chosen: LogReg C=10, MLP 128-64 (differ from defaults), RF unchanged; val F1 varies by <= 0.003. Wed 80%: validation holds 69,794 SSH flows that the fit part (193,354 FTP) has never seen, every setting scores val F1 <= 0.0009, defaults kept by tie-break (the plan's >=100 rule alone would have tuned it; I added the fit-part condition). Thu 70%: tuned, LogReg C=10, RF 50 trees, MLP default; val F1 range <= 0.010. `task1_results.json#splits.*.chosen/tuned/sensitivity`, `task1_sensitivity.csv`.

7. **No deployable Thursday option.** Threshold chosen on validation for <= 1,000 FA/day gives on test: RF 12,009/day (12x budget, recall 15.3%), MLP 10,968/day (15.6%), LogReg 2,090/day (1.4%). Test-curve reading at 1,000/day: RF 1.5%, MLP 0.1%, LogReg 1.2% (optimistic, not deployable).

8. **Payload rule matches the clusters (clustering-vs-rule claim weakened).** Thu zero-payload & duration<1,000 us rule, full day: precision 0.461, recall 0.334, F1 0.387 (best detector F1 0.388), 72,268 FA/day. It catches 2,923 of 3,482 detector-found flows (84%); port rule catches 54. Only GMM-only (85) and DBSCAN-only (97) flows (long, near-silent) escape it (1 and 0 caught). `task2_thu.json#found_missed.rules_on_groups`, `#rules`.

9. **Wednesday clustering is no longer beaten by the rule.** F1 K-Means 0.940, GMM 0.9980, DBSCAN 0.9994 vs port rule 0.9995; FA/day (Task 2 conv.) 97,775 / 888 / 261 vs rule 731 (DBSCAN lower than the rule, at 700 analyst labels). v1 said the rule does better and quoted 57,353-70,230 FA/day for detectors; those do not reproduce (K-Means is now 97,775, GMM and DBSCAN far lower).

10. **Grid edges.** Wed GMM: BIC still lowest at 120 components (grid extended from 60, never turned): edge, not an interior optimum; F1 plateau 0.9980. Thu GMM interior at 54 (full). K-Means interior (k=16 Wed, 17 Thu). DBSCAN eps interior on both days but **min_samples = 50 is the top of {5,10,25,50} on both days**. Extension check (min_samples 100, 200): Thu silhouette 0.751 -> 0.758 at 100 (F1 0.331 -> 0.299); Wed 0.817 -> 0.876 at 200 (F1 0.9994 -> 0.964). So silhouette keeps rising past the grid and the label-free choice is not settled; F1 falls when it moves. `task2_dbscan_ms_check_*.json`, `task2_dbscan_ms_extension_*.csv`.

11. **DBSCAN is not flat.** v1: Thursday F1 0.348-0.419 over 24 settings. Now 29 of 64 settings meet the noise cap; F1 over all 64 spans 0.019-0.447; within one grid step of the choice 0.331-0.406. K-Means Thu seed range 0.372-0.406. Thu detectors lie within 0.041 F1: cannot be ranked.

12. **'Missed flows look like ordinary traffic' is partly measured.** Thu missed-by-all 8,076 of 11,558 (70%): 23% exactly duplicate a benign flow's features (but so do 80% of the found flows, so this does not separate them); 86% have >5 of 10 benign PCA neighbours vs 7% of found flows and 89% of benign flows. Top missed ports 53/443/3389 (39/18/14%). Wed: no attack flow missed by all detectors. The label-error citation was NOT added (could not fetch/confirm the paper).

13. **Clock evidence limits.** The UNB schedule page was unreachable from this machine (proxy 403), so agreement with the published schedule is NOT verified; only the data-internal evidence below. File row order is not chronological (backward steps: Wed 289263, Thu 37695), so it is no independent evidence. Thursday contains no 1970 rows (brief says each file has some).

14. **Capture length.** Brief says 12 h; measured spans after repair are 9.0 h (Wed) and 9.5 h (Thu). Task 2 FA/day uses 12 h as planned, so is lower than a measured-span scaling would give.

15. **Not done / deviations.** `run_all.sh` was not executed end to end in one go (stages were run individually, some concurrently; total >3 h); task1 train times in `task1_results.json` are contended (MLP wed70 ~31 min), clean ones in `task1_timing.json` for Wed 80% and Thu 70% only. Task 1 random-split runs use the day's 70%-split tuned settings. GMM grid used one seed; K-Means 5 seeds; sweeps 3 seeds (no seeds cut). DBSCAN sweeps at other PCA dims / sample sizes keep the same k-distance quantile of eps instead of the same eps. Report build is out of scope (docx work stopped on instruction).


## PLAN section 3: data preparation (`results/prep_{wed,thu}.json`)

| Metric | Value | Source (file#key) |
|---|---|---|
| Wednesday: rows in file | 1,048,575 | `results/prep_wed.json#rows_in_file` (`prep.wed.rows_in_file`) |
| Wednesday: repeated header lines removed | 0 | `results/prep_wed.json#header_lines` (`prep.wed.header_lines`) |
| Wednesday: 1970-dated rows removed | 5 | `results/prep_wed.json#rows_1970` (`prep.wed.rows_1970`) |
| Wednesday: rows with +-Infinity removed | 3,824 | `results/prep_wed.json#rows_infinity` (`prep.wed.rows_infinity`) |
| Wednesday: NaN rows remaining after Infinity removal | 0 | `results/prep_wed.json#rows_nan_after_inf` (`prep.wed.rows_nan_after_inf`) |
| Wednesday: rows with any NaN before removal (all also had Infinity) | 2,277 | `results/prep_wed.json#rows_nan_total_before_inf_removal` (`prep.wed.rows_nan_total_before_inf_removal`) |
| Wednesday: duplicate rows (counted, kept) | 373,613 | `results/prep_wed.json#duplicate_rows_kept` (`prep.wed.duplicate_rows_kept`) |
| Wednesday: rows kept | 1,044,746 | `results/prep_wed.json#rows_kept` (`prep.wed.rows_kept`) |
| Wednesday: constant columns removed | 10 | `results/prep_wed.json#constant_columns` (`prep.wed.n_constant`) |
| Wednesday: final feature count | 67 | `results/prep_wed.json#n_features` (`prep.wed.n_features`) |
| Wednesday: attack flows | 380,943 | `results/prep_wed.json#attack_flows` (`prep.wed.attack_flows`) |
| Wednesday: flows moved by clock repair | 377,414 | `results/prep_wed.json#flows_moved_by_clock_fix` (`prep.wed.flows_moved_by_clock_fix`) |
| Wednesday: attack share % | 36.5 | `results/prep_wed.json#attack_share` (`prep.wed.attack_share`) |
| Wednesday: repaired span (h) | 9.0 | `results/prep_wed.json#span_hours_fixed` (`prep.wed.span_hours`) |
| Wednesday: constant column names | Bwd PSH Flags, Fwd URG Flags, Bwd URG Flags, CWE Flag Count, Fwd Byts/b Avg, Fwd Pkts/b Avg, Fwd Blk Rate Avg, Bwd Byts/b Avg, Bwd Pkts/b Avg, Bwd Blk Rate Avg | `results/prep_wed.json#constant_columns` |
| Wednesday Benign: first/last raw -> repaired | 2018-02-14 01:00:00 / 2018-02-14 12:59:59 -> 2018-02-14 08:28:20 / 2018-02-14 17:30:48 | `results/prep_wed.json#clock_evidence.Benign` |
| Wednesday FTP-BruteForce: first/last raw -> repaired | 2018-02-14 10:33:26 / 2018-02-14 12:10:31 -> 2018-02-14 10:33:26 / 2018-02-14 12:10:31 | `results/prep_wed.json#clock_evidence.FTP-BruteForce` |
| Wednesday SSH-Bruteforce: first/last raw -> repaired | 2018-02-14 02:01:21 / 2018-02-14 03:32:30 -> 2018-02-14 14:01:21 / 2018-02-14 15:32:30 | `results/prep_wed.json#clock_evidence.SSH-Bruteforce` |
| Thursday: rows in file | 331,125 | `results/prep_thu.json#rows_in_file` (`prep.thu.rows_in_file`) |
| Thursday: repeated header lines removed | 25 | `results/prep_thu.json#header_lines` (`prep.thu.header_lines`) |
| Thursday: 1970-dated rows removed | 0 | `results/prep_thu.json#rows_1970` (`prep.thu.rows_1970`) |
| Thursday: rows with +-Infinity removed | 2,919 | `results/prep_thu.json#rows_infinity` (`prep.thu.rows_infinity`) |
| Thursday: NaN rows remaining after Infinity removal | 0 | `results/prep_thu.json#rows_nan_after_inf` (`prep.thu.rows_nan_after_inf`) |
| Thursday: rows with any NaN before removal (all also had Infinity) | 1,834 | `results/prep_thu.json#rows_nan_total_before_inf_removal` (`prep.thu.rows_nan_total_before_inf_removal`) |
| Thursday: duplicate rows (counted, kept) | 40,154 | `results/prep_thu.json#duplicate_rows_kept` (`prep.thu.duplicate_rows_kept`) |
| Thursday: rows kept | 328,181 | `results/prep_thu.json#rows_kept` (`prep.thu.rows_kept`) |
| Thursday: constant columns removed | 8 | `results/prep_thu.json#constant_columns` (`prep.thu.n_constant`) |
| Thursday: final feature count | 69 | `results/prep_thu.json#n_features` (`prep.thu.n_features`) |
| Thursday: attack flows | 92,403 | `results/prep_thu.json#attack_flows` (`prep.thu.attack_flows`) |
| Thursday: flows moved by clock repair | 163,781 | `results/prep_thu.json#flows_moved_by_clock_fix` (`prep.thu.flows_moved_by_clock_fix`) |
| Thursday: attack share % | 28.2 | `results/prep_thu.json#attack_share` (`prep.thu.attack_share`) |
| Thursday: repaired span (h) | 9.5 | `results/prep_thu.json#span_hours_fixed` (`prep.thu.span_hours`) |
| Thursday: constant column names | Bwd PSH Flags, Bwd URG Flags, Fwd Byts/b Avg, Fwd Pkts/b Avg, Fwd Blk Rate Avg, Bwd Byts/b Avg, Bwd Pkts/b Avg, Bwd Blk Rate Avg | `results/prep_thu.json#constant_columns` |
| Thursday Benign: first/last raw -> repaired | 2018-03-01 01:00:00 / 2018-03-01 12:59:59 -> 2018-03-01 08:16:28 / 2018-03-01 17:45:28 | `results/prep_thu.json#clock_evidence.Benign` |
| Thursday Infilteration: first/last raw -> repaired | 2018-03-01 02:00:00 / 2018-03-01 10:54:59 -> 2018-03-01 09:57:00 / 2018-03-01 15:36:59 | `results/prep_thu.json#clock_evidence.Infilteration` |

Interpretation: hours 01-07 move +12 h, 08-12 unchanged; repaired series is one daytime window with compact attack windows. `Protocol` kept; `Timestamp`, `Dst Port` dropped; duplicates kept.


## PLAN section 4: Task 1 (`results/task1_results.json`, `task1_sensitivity.csv`, `task1_timing.json`)

### Wednesday 70%

| Metric | Value | Source (file#key) |
|---|---|---|
| cut time | 13:59 | `results/task1_results.json#splits.wed70.cut_time` (`t1.wed70.cut`) |
| test window start | 13:59 | `results/task1_results.json#splits.wed70.test_start` (`t1.wed70.test_start`) |
| test window end | 17:30 | `results/task1_results.json#splits.wed70.test_end` (`t1.wed70.test_end`) |
| test hours | 3.5 | `results/task1_results.json#splits.wed70.test_hours` (`t1.wed70.hours`) |
| test attack flows | 187,589 | `results/task1_results.json#splits.wed70.test_attack` (`t1.wed70.test_attack`) |
| test benign flows | 125,835 | `results/task1_results.json#splits.wed70.test_benign` (`t1.wed70.test_benign`) |
| validation attack flows | 10,683 | `results/task1_results.json#splits.wed70.val_attack` (`t1.wed70.val_attack`) |
| fit-part attack flows | 182,671 | `results/task1_results.json#splits.wed70.fit_attack` (`t1.wed70.fit_attack`) |
| Logistic Regression: precision / recall / F1 / AP | 0.400 / 0.0002 / 0.0003 / 0.964 | `#splits.wed70.models.LogReg` |
| Logistic Regression: F1 95% block-bootstrap CI | [0.000, 0.001] (1,000 resamples, 5-min blocks) | `#splits.wed70.models.LogReg.f1_ci` |
| Logistic Regression: TP/FP/FN/TN | 30 / 45 / 187,559 / 125,790 | `#splits.wed70.models.LogReg` |
| Logistic Regression: false alerts/day [Poisson 95% CI] | 306 [223, 410] | `#splits.wed70.models.LogReg.fa` |
| Logistic Regression: recall at 100 / 1,000 / 10,000 FA/day (test-curve reading, %) | 0.0 / 0.0 / 50.2 | `#splits.wed70.models.LogReg.budget_recall` |
| Random Forest: precision / recall / F1 / AP | 0.882 / 0.0002 / 0.0003 / 0.790 | `#splits.wed70.models.RandomForest` |
| Random Forest: F1 95% block-bootstrap CI | [0.000, 0.001] (1,000 resamples, 5-min blocks) | `#splits.wed70.models.RandomForest.f1_ci` |
| Random Forest: TP/FP/FN/TN | 30 / 4 / 187,559 / 125,831 | `#splits.wed70.models.RandomForest` |
| Random Forest: false alerts/day [Poisson 95% CI] | 27 [7, 70] | `#splits.wed70.models.RandomForest.fa` |
| Random Forest: recall at 100 / 1,000 / 10,000 FA/day (test-curve reading, %) | 0.0 / 47.8 / 47.8 | `#splits.wed70.models.RandomForest.budget_recall` |
| MLP: precision / recall / F1 / AP | 0.714 / 0.0002 / 0.0003 / 0.769 | `#splits.wed70.models.MLP` |
| MLP: F1 95% block-bootstrap CI | [0.000, 0.001] (1,000 resamples, 5-min blocks) | `#splits.wed70.models.MLP.f1_ci` |
| MLP: TP/FP/FN/TN | 30 / 12 / 187,559 / 125,823 | `#splits.wed70.models.MLP` |
| MLP: false alerts/day [Poisson 95% CI] | 82 [42, 143] | `#splits.wed70.models.MLP.fa` |
| MLP: recall at 100 / 1,000 / 10,000 FA/day (test-curve reading, %) | 0.0 / 0.0 / 0.0 | `#splits.wed70.models.MLP.budget_recall` |
| McNemar LogReg vs RandomForest | b=0, c=41, p=< 0.001 | `#splits.wed70.pairs` |
| McNemar LogReg vs MLP | b=0, c=33, p=< 0.001 | `#splits.wed70.pairs` |
| McNemar RandomForest vs MLP | b=8, c=0, p== 0.01 | `#splits.wed70.pairs` |
| Port 21/22 rule: precision / recall / F1 | 0.9997 / 1.000 / 0.9998 | `#splits.wed70.port_rule` |
| Port rule: false alerts/day [CI] | 429 [330, 549] | `#splits.wed70.port_rule.fa` |
| McNemar port rule vs RF | b=187,563, c=63, p=0.001 | `#splits.wed70.port_rule_vs_RF` |

### Wednesday 80%

| Metric | Value | Source (file#key) |
|---|---|---|
| cut time | 14:35 | `results/task1_results.json#splits.wed80.cut_time` (`t1.wed80.cut`) |
| test window start | 14:35 | `results/task1_results.json#splits.wed80.test_start` (`t1.wed80.test_start`) |
| test window end | 17:30 | `results/task1_results.json#splits.wed80.test_end` (`t1.wed80.test_end`) |
| test hours | 2.9 | `results/task1_results.json#splits.wed80.test_hours` (`t1.wed80.hours`) |
| test attack flows | 117,795 | `results/task1_results.json#splits.wed80.test_attack` (`t1.wed80.test_attack`) |
| test benign flows | 91,155 | `results/task1_results.json#splits.wed80.test_benign` (`t1.wed80.test_benign`) |
| validation attack flows | 69,794 | `results/task1_results.json#splits.wed80.val_attack` (`t1.wed80.val_attack`) |
| fit-part attack flows | 193,354 | `results/task1_results.json#splits.wed80.fit_attack` (`t1.wed80.fit_attack`) |
| Logistic Regression: precision / recall / F1 / AP | 0.9985 / 0.9999 / 0.9992 / 1.000 | `#splits.wed80.models.LogReg` |
| Logistic Regression: F1 95% block-bootstrap CI | [0.9991, 0.9993] (1,000 resamples, 5-min blocks) | `#splits.wed80.models.LogReg.f1_ci` |
| Logistic Regression: TP/FP/FN/TN | 117,788 / 173 / 7 / 90,982 | `#splits.wed80.models.LogReg` |
| Logistic Regression: false alerts/day [Poisson 95% CI] | 1,421 [1,217, 1,650] | `#splits.wed80.models.LogReg.fa` |
| Logistic Regression: recall at 100 / 1,000 / 10,000 FA/day (test-curve reading, %) | 100.0 / 100.0 / 100.0 | `#splits.wed80.models.LogReg.budget_recall` |
| Random Forest: precision / recall / F1 / AP | 0.9999 / 0.9999 / 0.9999 / 1.000 | `#splits.wed80.models.RandomForest` |
| Random Forest: F1 95% block-bootstrap CI | [0.9998, 1.000] (1,000 resamples, 5-min blocks) | `#splits.wed80.models.RandomForest.f1_ci` |
| Random Forest: TP/FP/FN/TN | 117,779 / 6 / 16 / 91,149 | `#splits.wed80.models.RandomForest` |
| Random Forest: false alerts/day [Poisson 95% CI] | 49 [18, 107] | `#splits.wed80.models.RandomForest.fa` |
| Random Forest: recall at 100 / 1,000 / 10,000 FA/day (test-curve reading, %) | 100.0 / 100.0 / 100.0 | `#splits.wed80.models.RandomForest.budget_recall` |
| MLP: precision / recall / F1 / AP | 0.9999 / 0.9999 / 0.9999 / 1.000 | `#splits.wed80.models.MLP` |
| MLP: F1 95% block-bootstrap CI | [0.9998, 1.000] (1,000 resamples, 5-min blocks) | `#splits.wed80.models.MLP.f1_ci` |
| MLP: TP/FP/FN/TN | 117,781 / 9 / 14 / 91,146 | `#splits.wed80.models.MLP` |
| MLP: false alerts/day [Poisson 95% CI] | 74 [34, 140] | `#splits.wed80.models.MLP.fa` |
| MLP: recall at 100 / 1,000 / 10,000 FA/day (test-curve reading, %) | 100.0 / 100.0 / 100.0 | `#splits.wed80.models.MLP.budget_recall` |
| McNemar LogReg vs RandomForest | b=9, c=167, p=< 0.001 | `#splits.wed80.pairs` |
| McNemar LogReg vs MLP | b=7, c=164, p=< 0.001 | `#splits.wed80.pairs` |
| McNemar RandomForest vs MLP | b=5, c=4, p== 1.00 | `#splits.wed80.pairs` |
| Port 21/22 rule: precision / recall / F1 | 0.9996 / 1.000 / 0.9998 | `#splits.wed80.port_rule` |
| Port rule: false alerts/day [CI] | 361 [263, 485] | `#splits.wed80.port_rule.fa` |
| McNemar port rule vs RF | b=22, c=44, p=0.01 | `#splits.wed80.port_rule_vs_RF` |

### Thursday 70%

| Metric | Value | Source (file#key) |
|---|---|---|
| cut time | 14:40 | `results/task1_results.json#splits.thu70.cut_time` (`t1.thu70.cut`) |
| test window start | 14:40 | `results/task1_results.json#splits.thu70.test_start` (`t1.thu70.test_start`) |
| test window end | 17:45 | `results/task1_results.json#splits.thu70.test_end` (`t1.thu70.test_end`) |
| test hours | 3.1 | `results/task1_results.json#splits.thu70.test_hours` (`t1.thu70.hours`) |
| test attack flows | 29,058 | `results/task1_results.json#splits.thu70.test_attack` (`t1.thu70.test_attack`) |
| test benign flows | 69,397 | `results/task1_results.json#splits.thu70.test_benign` (`t1.thu70.test_benign`) |
| validation attack flows | 24,808 | `results/task1_results.json#splits.thu70.val_attack` (`t1.thu70.val_attack`) |
| fit-part attack flows | 38,537 | `results/task1_results.json#splits.thu70.fit_attack` (`t1.thu70.fit_attack`) |
| Logistic Regression: precision / recall / F1 / AP | 0.385 / 0.305 / 0.341 / 0.398 | `#splits.thu70.models.LogReg` |
| Logistic Regression: F1 95% block-bootstrap CI | [0.174, 0.462] (1,000 resamples, 5-min blocks) | `#splits.thu70.models.LogReg.f1_ci` |
| Logistic Regression: TP/FP/FN/TN | 8,877 / 14,184 / 20,181 / 55,213 | `#splits.thu70.models.LogReg` |
| Logistic Regression: false alerts/day [Poisson 95% CI] | 110,177 [108,371, 112,005] | `#splits.thu70.models.LogReg.fa` |
| Logistic Regression: recall at 100 / 1,000 / 10,000 FA/day (test-curve reading, %) | 0.0 / 1.2 / 10.7 | `#splits.thu70.models.LogReg.budget_recall` |
| Random Forest: precision / recall / F1 / AP | 0.394 / 0.380 / 0.387 / 0.439 | `#splits.thu70.models.RandomForest` |
| Random Forest: F1 95% block-bootstrap CI | [0.231, 0.504] (1,000 resamples, 5-min blocks) | `#splits.thu70.models.RandomForest.f1_ci` |
| Random Forest: TP/FP/FN/TN | 11,040 / 16,954 / 18,018 / 52,443 | `#splits.thu70.models.RandomForest` |
| Random Forest: false alerts/day [Poisson 95% CI] | 131,693 [129,718, 133,691] | `#splits.thu70.models.RandomForest.fa` |
| Random Forest: recall at 100 / 1,000 / 10,000 FA/day (test-curve reading, %) | 0.0 / 1.5 / 14.4 | `#splits.thu70.models.RandomForest.budget_recall` |
| MLP: precision / recall / F1 / AP | 0.749 / 0.159 / 0.263 / 0.430 | `#splits.thu70.models.MLP` |
| MLP: F1 95% block-bootstrap CI | [0.040, 0.443] (1,000 resamples, 5-min blocks) | `#splits.thu70.models.MLP.f1_ci` |
| MLP: TP/FP/FN/TN | 4,630 / 1,553 / 24,428 / 67,844 | `#splits.thu70.models.MLP` |
| MLP: false alerts/day [Poisson 95% CI] | 12,063 [11,471, 12,678] | `#splits.thu70.models.MLP.fa` |
| MLP: recall at 100 / 1,000 / 10,000 FA/day (test-curve reading, %) | 0.0 / 0.1 / 15.3 | `#splits.thu70.models.MLP.budget_recall` |
| McNemar LogReg vs RandomForest | b=13,186, c=12,579, p=< 0.001 | `#splits.thu70.pairs` |
| McNemar LogReg vs MLP | b=4,740, c=13,124, p=< 0.001 | `#splits.thu70.pairs` |
| McNemar RandomForest vs MLP | b=6,537, c=15,528, p=< 0.001 | `#splits.thu70.pairs` |
| Port 21/22 rule: precision / recall / F1 | 0.286 / 0.008 / 0.015 | `#splits.thu70.port_rule` |
| Port rule: false alerts/day [CI] | 4,389 [4,034, 4,766] | `#splits.thu70.port_rule.fa` |
| McNemar port rule vs RF | b=16,886, c=11,311, p=0.001 | `#splits.thu70.port_rule_vs_RF` |

Clean timings (s, train / predict): wed80|LogReg: 8 / 0.1; wed80|RandomForest: 92 / 0.6; wed80|MLP: 96 / 0.7; thu70|LogReg: 102 / 0.1; thu70|RandomForest: 38 / 1.7; thu70|MLP: 64 / 0.2 (`task1_timing.json`).

### Thursday operating points (threshold from validation window, budget <= 1,000 FA/day)

| Metric | Value | Source (file#key) |
|---|---|---|
| Logistic Regression | test recall 1.4%, precision 0.606, test FA/day 2,090 (validation 814) | `#splits.thu70.models.LogReg.operating_point` |
| Random Forest | test recall 15.3%, precision 0.742, test FA/day 12,009 (validation 981) | `#splits.thu70.models.RandomForest.operating_point` |
| MLP | test recall 15.6%, precision 0.762, test FA/day 10,968 (validation 957) | `#splits.thu70.models.MLP.operating_point` |
| Payload rule on Thu test window | recall 22.9%, precision 0.379, FA/day 85,002 | `#splits.thu70.payload_rule` |

### Leakage and clock demos

| Metric | Value | Source (file#key) |
|---|---|---|
| wed random stratified 70/30, Logistic Regression: F1 / AP | 0.9999 / 1.000 (gap to time split 0.001) | `#random_split.wed.LogReg` |
| wed random stratified 70/30, Random Forest: F1 / AP | 1.000 / 1.000 (gap to time split 0.000) | `#random_split.wed.RandomForest` |
| wed random stratified 70/30, MLP: F1 / AP | 1.000 / 1.000 (gap to time split 0.000) | `#random_split.wed.MLP` |
| wed unrepaired clock RF: F1 | 1.000 | `#unrepaired_clock.wed` |
| thu random stratified 70/30, Logistic Regression: F1 / AP | 0.438 / 0.503 (gap to time split 0.097) | `#random_split.thu.LogReg` |
| thu random stratified 70/30, Random Forest: F1 / AP | 0.489 / 0.575 (gap to time split 0.102) | `#random_split.thu.RandomForest` |
| thu random stratified 70/30, MLP: F1 / AP | 0.389 / 0.568 (gap to time split 0.127) | `#random_split.thu.MLP` |
| thu unrepaired clock RF: F1 | 0.592 | `#unrepaired_clock.thu` |


## PLAN section 5: Task 2 (`results/task2_{wed,thu}.json`, `task2_grid.csv`, `task2_extra_sweeps.csv`)

### Wednesday

| Metric | Value | Source (file#key) |
|---|---|---|
| sample size / step | 40,000 | `results/task2_wed.json#n_sample` (`t2.wed.n_sample`) |
| sample step | 26 | `results/task2_wed.json#sample_step` (`t2.wed.sample_step`) |
| PCA components for 95% variance | 11 | `results/task2_wed.json#pca_k95` (`t2.wed.pca_k95`) |
| K-Means chosen k / mean silhouette / position | 16 / 0.752 / interior | `task2_wed.json#kmeans` |
| K-Means F1 at k-1, k, k+1 (seed means) range | 0.940-0.940 | `task2_wed.json#kmeans.stability_f1_pm1` |
| GMM chosen components / covariance / position | 120 / full / at the grid edge (grid max 120) | `task2_wed.json#gmm` |
| GMM F1 within one grid step range | 0.9980-0.9980 | `task2_wed.json#gmm.stability_f1_pm1` |
| DBSCAN chosen eps / min_samples / clusters / noise % | 0.284 / 50 / 34 / 17 | `task2_wed.json#dbscan` |
| DBSCAN eps position; min_samples position | eps interior; min_samples at upper edge | `task2_wed.json#dbscan.eps_edge/ms_edge` |
| DBSCAN F1 at eps +-1 and min_samples +-1 range | 0.964-0.9994 | `task2_wed.json#dbscan.stability_f1_neighbours` |
| DBSCAN F1 over all settings; valid settings | 0.000-0.9998; 37 of 64 | `task2_wed.json#dbscan` |
| min_samples extension (100, 200): silhouette old -> new (ms), F1 old -> new | 0.817 -> 0.876 (ms 200); 0.9994 -> 0.964 | `task2_dbscan_ms_check_wed.json` |
| K-Means: precision / recall / F1 [min-max over 5 seeds] | 0.886 / 1.000 / 0.940 [0.939-0.940] | `task2_wed.json#final` |
| K-Means: analyst labels / FA per day (Task 2 conv.) | 320 / 97,775 | `task2_wed.json#final` |
| GMM: precision / recall / F1 [min-max over 3 seeds] | 0.9988 / 0.9972 / 0.9980 [0.9980-0.9981] | `task2_wed.json#final` |
| GMM: analyst labels / FA per day (Task 2 conv.) | 2,218 / 888 | `task2_wed.json#final` |
| DBSCAN: precision / recall / F1 [min-max over 3 seeds] | 0.9997 / 0.9992 / 0.9994 [0.9994-0.9994] | `task2_wed.json#final` |
| DBSCAN: analyst labels / FA per day (Task 2 conv.) | 700 / 261 | `task2_wed.json#final` |
| K-Means / GMM / DBSCAN best F1 anywhere in grid | 0.979 / 0.9996 / 0.9998 | `task2_wed.json` |
| port rule (sample): P / R / F1 / FA per day | 0.9990 / 1.000 / 0.9995 / 731 | `task2_wed.json#rules.port.sample` |
| port rule (full_day): P / R / F1 / FA per day | 0.9991 / 1.000 / 0.9995 / 720 | `task2_wed.json#rules.port.full_day` |
| group benign: flows; rules catching (port / payload); medians | 25,421; 14 / 4,004; Flow Duration: 31,724 | TotLen Fwd Pkts: 49 | TotLen Bwd Pkts: 119 | Flow Pkts/s: 111 | Init Fwd Win Byts: 278 | `task2_wed.json#found_missed` |
| group found_any: flows; rules catching (port / payload); medians | 14,579; 14,579 / 10,971; Flow Duration: 6 | TotLen Fwd Pkts: 0 | TotLen Bwd Pkts: 0 | Flow Pkts/s: 333,333 | Init Fwd Win Byts: 26,883 | `task2_wed.json#found_missed` |
| group only_kmeans: flows; rules catching (port / payload); medians | 12; 12 / 12; Flow Duration: 65 | TotLen Fwd Pkts: 0 | TotLen Bwd Pkts: 0 | Flow Pkts/s: 47,056 | Init Fwd Win Byts: 241 | `task2_wed.json#found_missed` |
| group only_gmm: flows; rules catching (port / payload); medians | 0; 0 / 0;  | `task2_wed.json#found_missed` |
| group only_dbscan: flows; rules catching (port / payload); medians | 0; 0 / 0;  | `task2_wed.json#found_missed` |
| group missed_all: flows; rules catching (port / payload); medians | 0; 0 / 0;  | `task2_wed.json#found_missed` |

### Thursday

| Metric | Value | Source (file#key) |
|---|---|---|
| sample size / step | 40,000 | `results/task2_thu.json#n_sample` (`t2.thu.n_sample`) |
| sample step | 8 | `results/task2_thu.json#sample_step` (`t2.thu.sample_step`) |
| PCA components for 95% variance | 13 | `results/task2_thu.json#pca_k95` (`t2.thu.pca_k95`) |
| K-Means chosen k / mean silhouette / position | 17 / 0.646 / interior | `task2_thu.json#kmeans` |
| K-Means F1 at k-1, k, k+1 (seed means) range | 0.384-0.388 | `task2_thu.json#kmeans.stability_f1_pm1` |
| GMM chosen components / covariance / position | 54 / full / interior (grid max 60) | `task2_thu.json#gmm` |
| GMM F1 within one grid step range | 0.337-0.385 | `task2_thu.json#gmm.stability_f1_pm1` |
| DBSCAN chosen eps / min_samples / clusters / noise % | 0.333 / 50 / 52 / 16 | `task2_thu.json#dbscan` |
| DBSCAN eps position; min_samples position | eps interior; min_samples at upper edge | `task2_thu.json#dbscan.eps_edge/ms_edge` |
| DBSCAN F1 at eps +-1 and min_samples +-1 range | 0.331-0.406 | `task2_thu.json#dbscan.stability_f1_neighbours` |
| DBSCAN F1 over all settings; valid settings | 0.019-0.447; 29 of 64 | `task2_thu.json#dbscan` |
| min_samples extension (100, 200): silhouette old -> new (ms), F1 old -> new | 0.751 -> 0.758 (ms 100); 0.331 -> 0.299 | `task2_dbscan_ms_check_thu.json` |
| K-Means: precision / recall / F1 [min-max over 5 seeds] | 0.594 / 0.293 / 0.388 [0.372-0.406] | `task2_thu.json#final` |
| K-Means: analyst labels / FA per day (Task 2 conv.) | 340 / 41,601 | `task2_thu.json#final` |
| GMM: precision / recall / F1 [min-max over 3 seeds] | 0.816 / 0.231 / 0.355 [0.336-0.391] | `task2_thu.json#final` |
| GMM: analyst labels / FA per day (Task 2 conv.) | 1,080 / 12,567 | `task2_thu.json#final` |
| DBSCAN: precision / recall / F1 [min-max over 3 seeds] | 0.831 / 0.224 / 0.347 [0.324-0.386] | `task2_thu.json#final` |
| DBSCAN: analyst labels / FA per day (Task 2 conv.) | 1,060 / 11,655 | `task2_thu.json#final` |
| K-Means / GMM / DBSCAN best F1 anywhere in grid | 0.395 / 0.404 / 0.447 | `task2_thu.json` |
| port rule (sample): P / R / F1 / FA per day | 0.357 / 0.009 / 0.018 / 3,250 | `task2_thu.json#rules.port.sample` |
| port rule (full_day): P / R / F1 / FA per day | 0.327 / 0.009 / 0.017 / 3,244 | `task2_thu.json#rules.port.full_day` |
| payload rule (sample): P / R / F1 / FA per day | 0.467 / 0.336 / 0.391 / 73,547 | `task2_thu.json#rules.payload.sample` |
| payload rule (full_day): P / R / F1 / FA per day | 0.461 / 0.334 / 0.387 / 72,268 | `task2_thu.json#rules.payload.full_day` |
| group benign: flows; rules catching (port / payload); medians | 28,442; 196 / 4,436; Flow Duration: 18,684 | TotLen Fwd Pkts: 43 | TotLen Bwd Pkts: 89 | Flow Pkts/s: 157 | Init Fwd Win Byts: 256 | `task2_thu.json#found_missed` |
| group found_any: flows; rules catching (port / payload); medians | 3,482; 54 / 2,923; Flow Duration: 250 | TotLen Fwd Pkts: 0 | TotLen Bwd Pkts: 0 | Flow Pkts/s: 8,000 | Init Fwd Win Byts: 1,024 | `task2_thu.json#found_missed` |
| group only_kmeans: flows; rules catching (port / payload); medians | 984; 2 / 931; Flow Duration: 2 | TotLen Fwd Pkts: 0 | TotLen Bwd Pkts: 0 | Flow Pkts/s: 1,000,000 | Init Fwd Win Byts: 1,024 | `task2_thu.json#found_missed` |
| group only_gmm: flows; rules catching (port / payload); medians | 85; 8 / 1; Flow Duration: 687,489 | TotLen Fwd Pkts: 0 | TotLen Bwd Pkts: 0 | Flow Pkts/s: 4.9 | Init Fwd Win Byts: 128 | `task2_thu.json#found_missed` |
| group only_dbscan: flows; rules catching (port / payload); medians | 97; 0 / 0; Flow Duration: 9,014,173 | TotLen Fwd Pkts: 0 | TotLen Bwd Pkts: 0 | Flow Pkts/s: 0.3 | Init Fwd Win Byts: 8,192 | `task2_thu.json#found_missed` |
| group missed_all: flows; rules catching (port / payload); medians | 8,076; 55 / 960; Flow Duration: 17,882 | TotLen Fwd Pkts: 46 | TotLen Bwd Pkts: 105 | Flow Pkts/s: 158 | Init Fwd Win Byts: 237 | `task2_thu.json#found_missed` |

Sweeps (PCA dims, sample size, triage flows, analyst error): per-value seed-mean F1 are keys `sw.{day}.{algo}.{sweep}.v{value}` in `report_numbers.json`, raw rows in `results/task2_extra_sweeps.csv`; grid in `results/task2_grid.csv`.

| Metric | Value | Source (file#key) |
|---|---|---|
| pca_dims wed: F1 range K-Means / GMM / DBSCAN | 0.933-0.949 / 0.9980-0.9987 / 0.964-0.9996 | `results/task2_extra_sweeps_*.csv` |
| pca_dims thu: F1 range K-Means / GMM / DBSCAN | 0.318-0.398 / 0.355-0.369 / 0.323-0.380 | `results/task2_extra_sweeps_*.csv` |
| sample_size wed: F1 range K-Means / GMM / DBSCAN | 0.940-0.942 / 0.9976-0.9986 / 0.962-0.9994 | `results/task2_extra_sweeps_*.csv` |
| sample_size thu: F1 range K-Means / GMM / DBSCAN | 0.384-0.398 / 0.355-0.393 / 0.333-0.366 | `results/task2_extra_sweeps_*.csv` |
| triage_n wed: F1 range K-Means / GMM / DBSCAN | 0.940-0.940 / 0.9980-0.9980 / 0.9994-0.9994 | `results/task2_extra_sweeps_*.csv` |
| triage_n thu: F1 range K-Means / GMM / DBSCAN | 0.294-0.398 / 0.355-0.380 / 0.328-0.366 | `results/task2_extra_sweeps_*.csv` |
| analyst_error wed: F1 range K-Means / GMM / DBSCAN | 0.940-0.940 / 0.9980-0.9980 / 0.9994-0.9994 | `results/task2_extra_sweeps_*.csv` |
| analyst_error thu: F1 range K-Means / GMM / DBSCAN | 0.398-0.408 / 0.345-0.355 / 0.347-0.354 | `results/task2_extra_sweeps_*.csv` |
| max |F1(10% analyst error) - F1(0)| over all algos/days | 0.010 | `results/task2_extra_sweeps_*.csv (analyst_error sweep)` (`sw.maxshift_error`) |

Interpretation: analyst error up to 10% barely moves F1 (majority vote over 20 flows absorbs it); more flows per cluster raises label cost without F1 gain; PCA 5 hurts K-Means on Thursday.
