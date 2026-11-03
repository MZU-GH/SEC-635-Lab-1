"""Writes RESULTS_SUMMARY.md and CHANGES.md from results/report_numbers.json (no hand-typed result values)."""
from lab1.common import *
N = jload("report_numbers.json")
def v(k): return N[k]["text"]
def src(k): return N[k]["source"]
def raw(k): return N[k]["value"]
L = []
def h(t): L.append(f"\n## {t}\n")
def table(rows, head=("Metric", "Value", "Source (file#key)")):
    L.append("| " + " | ".join(head) + " |"); L.append("|" + "---|" * len(head))
    for r in rows: L.append("| " + " | ".join(r) + " |")
    L.append("")
def R(label, key, suffix=""): return [label, v(key) + suffix, f"`{src(key)}` (`{key}`)"]
MN = {"LogReg": "Logistic Regression", "RandomForest": "Random Forest", "MLP": "MLP"}

def main():
    L.append("# RESULTS_SUMMARY\n\nEvery value below is read from `results/report_numbers.json` (written by `src/lab1/report_numbers.py` from the result files); the last column gives the file and the JSON key. "
             "Task 1 false alerts/day = benign flagged / test-window hours x 24 (exact Poisson 95% CI). Task 2 false alerts/day = sample FPR x day's benign flows x 24/12 (brief's 12 h capture). The two conventions are not comparable. "
             "Task 1 train times in `task1_results.json` were measured while other jobs shared the 4 CPUs; clean re-timings for Wed 80% and Thu 70% are in `task1_timing.json`.")
    # ---------------- flags
    h("Flags: results that contradict or weaken v1 claims (read first)")
    F = [
     f"1. **Leakage claim was confounded.** v1: random split F1 1.000 vs time split 0.000. Like for like the RF gap is small: Wed random {v('rand.wed.RandomForest.f1')} vs Wed 80% time split {v('t1.wed80.RandomForest.f1')} (gap {v('leak.wed.gap')}); Thu random {v('rand.thu.RandomForest.f1')} vs Thu 70% {v('t1.thu70.RandomForest.f1')} (gap {v('leak.thu.gap')}), and the random value is **{v('leak.thu.inside')}** the time-split block-bootstrap CI [{v('t1.thu70.RandomForest.f1_lo')}, {v('t1.thu70.RandomForest.f1_hi')}]. The Wed 70% comparison (RF F1 {v('t1.wed70.RandomForest.f1')}) mixes leakage with an unseen attack type. Source: `task1_results.json#random_split`, `#splits`.",
     f"2. **Clock defect demo.** Unrepaired clock, RF 70/30: Wed F1 {v('unrep.wed.f1')} (trains on raw {v('unrep.wed.train_raw_start')}-{v('unrep.wed.train_raw_end')}, tests on raw {v('unrep.wed.test_raw_start')}-{v('unrep.wed.test_raw_end')}); Thu F1 {v('unrep.thu.f1')} (higher than the honest {v('t1.thu70.RandomForest.f1')}). `task1_results.json#unrepaired_clock`.",
     f"3. **Port 21/22 rule vs RF on the Task 1 windows.** Wed 70% (SSH unseen): rule recall {v('t1.wed70.port_rule.recall')}, F1 {v('t1.wed70.port_rule.f1')}, {v('t1.wed70.port_rule.fa_value')} FA/day [{v('t1.wed70.port_rule.fa_lo')}-{v('t1.wed70.port_rule.fa_hi')}] versus RF recall {v('t1.wed70.RandomForest.recall')}. Wed 80% (seen): rule F1 {v('t1.wed80.port_rule.f1')}, {v('t1.wed80.port_rule.fa_value')} FA/day [{v('t1.wed80.port_rule.fa_lo')}-{v('t1.wed80.port_rule.fa_hi')}] vs RF F1 {v('t1.wed80.RandomForest.f1')}, {v('t1.wed80.RandomForest.fa_value')} FA/day [{v('t1.wed80.RandomForest.fa_lo')}-{v('t1.wed80.RandomForest.fa_hi')}]; the intervals do not overlap and McNemar rule-vs-RF p={v('t1.wed80.port_rule_vs_RF.p')} (b={v('t1.wed80.port_rule_vs_RF.b')}, c={v('t1.wed80.port_rule_vs_RF.c')}). **The rule roughly matches RF on detection; RF's measured advantage is ~{v('t1.wed80.rule_minus_rf_fa')} fewer false alerts/day, and the rule is the only one catching unseen SSH.** Thu 70%: rule recall {v('t1.thu70.port_rule.recall_pct')}% at {v('t1.thu70.port_rule.fa_value')} FA/day. `task1_results.json#splits.*.port_rule`.",
     f"4. **49/day rests on {v('t1.wed80.RandomForest.fp')} false positives.** Reproduced: {v('t1.wed80.RandomForest.fa_value')}/day, exact Poisson 95% CI [{v('t1.wed80.RandomForest.fa_lo')}, {v('t1.wed80.RandomForest.fa_hi')}] (MLP {v('t1.wed80.MLP.fa_value')} [{v('t1.wed80.MLP.fa_lo')}-{v('t1.wed80.MLP.fa_hi')}]). Wed 80% shares one SSH campaign between train and test, so it is an optimistic bound. `#splits.wed80.models.*.fa`.",
     f"5. **RF vs MLP on Wed 80% is a tie, not a win.** McNemar p={v('t1.wed80.mc.RandomForest.MLP.p')} (b={v('t1.wed80.mc.RandomForest.MLP.b')}, c={v('t1.wed80.mc.RandomForest.MLP.c')}), FA CIs overlap, clean train times {v('timing.wed80.RandomForest.train_s')} s vs {v('timing.wed80.MLP.train_s')} s. Only Thursday separates them slightly (F1 {v('t1.thu70.RandomForest.f1')} vs {v('t1.thu70.MLP.f1')}; recall at 1,000/day budget {v('t1.thu70.RandomForest.budget_recall_1000')}% vs {v('t1.thu70.MLP.budget_recall_1000')}%).",
     f"6. **Tuning outcome.** Wed 70% validation window holds **{v('t1.wed70.val_attack')} attack flows (>= {v('config.min_attacks')}, all FTP; fit part {v('t1.wed70.fit_attack')})**, so it WAS tuned (the plan expected it would not be). Chosen: LogReg C={v('t1.wed70.LogReg.C')}, MLP {v('t1.wed70.MLP.hid1')}-{v('t1.wed70.MLP.hid2')} (differ from defaults), RF unchanged; val F1 varies by <= {v('t1.wed70.sens_max')}. Wed 80%: validation holds {v('t1.wed80.val_attack')} SSH flows that the fit part ({v('t1.wed80.fit_attack')} FTP) has never seen, every setting scores val F1 <= {v('t1.wed80.LogReg.val_f1_max')}, defaults kept by tie-break (the plan's >=100 rule alone would have tuned it; I added the fit-part condition). Thu 70%: tuned, LogReg C={v('t1.thu70.LogReg.C')}, RF {v('t1.thu70.RandomForest.n_estimators')} trees, MLP default; val F1 range <= {v('t1.thu70.sens_max')}. `task1_results.json#splits.*.chosen/tuned/sensitivity`, `task1_sensitivity.csv`.",
     f"7. **No deployable Thursday option.** Threshold chosen on validation for <= {v('config.budget')} FA/day gives on test: RF {v('t1.thu70.RandomForest.op_fa')}/day ({v('t1.thu70.RandomForest.op_fa_ratio')}x budget, recall {v('t1.thu70.RandomForest.op_recall')}%), MLP {v('t1.thu70.MLP.op_fa')}/day ({v('t1.thu70.MLP.op_recall')}%), LogReg {v('t1.thu70.LogReg.op_fa')}/day ({v('t1.thu70.LogReg.op_recall')}%). Test-curve reading at 1,000/day: RF {v('t1.thu70.RandomForest.budget_recall_1000')}%, MLP {v('t1.thu70.MLP.budget_recall_1000')}%, LogReg {v('t1.thu70.LogReg.budget_recall_1000')}% (optimistic, not deployable).",
     f"8. **Payload rule matches the clusters (clustering-vs-rule claim weakened).** Thu zero-payload & duration<1,000 us rule, full day: precision {v('t2.thu.rule.payload.full_day.precision')}, recall {v('t2.thu.rule.payload.full_day.recall')}, F1 {v('t2.thu.rule.payload.full_day.f1')} (best detector F1 {v('t2.thu.km.final.f1')}), {v('t2.thu.rule.payload.full_day.fa')} FA/day. It catches {v('fm.thu.found_any.payload_rule')} of {v('fm.thu.found_any.n')} detector-found flows ({v('fm.thu.found_any.payload_rule_share')}%); port rule catches {v('fm.thu.found_any.port_rule')}. Only GMM-only ({v('fm.thu.only_gmm.n')}) and DBSCAN-only ({v('fm.thu.only_dbscan.n')}) flows (long, near-silent) escape it ({v('fm.thu.only_gmm.payload_rule')} and {v('fm.thu.only_dbscan.payload_rule')} caught). `task2_thu.json#found_missed.rules_on_groups`, `#rules`.",
     f"9. **Wednesday clustering is no longer beaten by the rule.** F1 K-Means {v('t2.wed.km.final.f1')}, GMM {v('t2.wed.gmm.final.f1')}, DBSCAN {v('t2.wed.db.final.f1')} vs port rule {v('t2.wed.rule.port.sample.f1')}; FA/day (Task 2 conv.) {v('t2.wed.km.final.fa')} / {v('t2.wed.gmm.final.fa')} / {v('t2.wed.db.final.fa')} vs rule {v('t2.wed.rule.port.sample.fa')} (DBSCAN lower than the rule, at {v('t2.wed.db.final.labels')} analyst labels). v1 said the rule does better and quoted 57,353-70,230 FA/day for detectors; those do not reproduce (K-Means is now " + v('t2.wed.km.final.fa') + ", GMM and DBSCAN far lower).",
     f"10. **Grid edges.** Wed GMM: BIC still lowest at {v('t2.wed.gmm.grid_max')} components (grid extended from 60, never turned): edge, not an interior optimum; F1 plateau {v('t2.wed.gmm.stab_lo')}. Thu GMM interior at {v('t2.thu.gmm.k')} ({v('t2.thu.gmm.cov')}). K-Means interior (k={v('t2.wed.km.k')} Wed, {v('t2.thu.km.k')} Thu). DBSCAN eps interior on both days but **min_samples = {v('t2.thu.db.ms')} is the top of {{5,10,25,50}} on both days**. Extension check (min_samples 100, 200): Thu silhouette {v('t2.thu.msx.old_best_sil')} -> {v('t2.thu.msx.ext_best_sil')} at {v('t2.thu.msx.ext_best_ms')} (F1 {v('t2.thu.msx.old_best_f1')} -> {v('t2.thu.msx.ext_best_f1')}); Wed {v('t2.wed.msx.old_best_sil')} -> {v('t2.wed.msx.ext_best_sil')} at {v('t2.wed.msx.ext_best_ms')} (F1 {v('t2.wed.msx.old_best_f1')} -> {v('t2.wed.msx.ext_best_f1')}). So silhouette keeps rising past the grid and the label-free choice is not settled; F1 falls when it moves. `task2_dbscan_ms_check_*.json`, `task2_dbscan_ms_extension_*.csv`.",
     f"11. **DBSCAN is not flat.** v1: Thursday F1 0.348-0.419 over 24 settings. Now {v('t2.thu.db.nvalid')} of {v('t2.thu.db.nsettings')} settings meet the noise cap; F1 over all {v('t2.thu.db.nsettings')} spans {v('t2.thu.db.f1_min')}-{v('t2.thu.db.f1_max')}; within one grid step of the choice {v('t2.thu.db.stab_lo')}-{v('t2.thu.db.stab_hi')}. K-Means Thu seed range {v('t2.thu.km.final.f1_min')}-{v('t2.thu.km.final.f1_max')}. Thu detectors lie within {v('t2.thu.spread')} F1: cannot be ranked.",
     f"12. **'Missed flows look like ordinary traffic' is partly measured.** Thu missed-by-all {v('fm.thu.missed_all.n')} of {v('fm.thu.all_attack.n')} ({v('fm.thu.missed_share_of_attack')}%): {v('oc.thu.missed_all.dup_share')}% exactly duplicate a benign flow's features (but so do {v('oc.thu.found_any.dup_share')}% of the found flows, so this does not separate them); {v('oc.thu.missed_all.nn_share')}% have >5 of 10 benign PCA neighbours vs {v('oc.thu.found_any.nn_share')}% of found flows and {v('oc.thu.benign.nn_share')}% of benign flows. Top missed ports {v('fm.thu.missed_port1')}/{v('fm.thu.missed_port2')}/{v('fm.thu.missed_port3')} ({v('fm.thu.missed_port1_share')}/{v('fm.thu.missed_port2_share')}/{v('fm.thu.missed_port3_share')}%). Wed: no attack flow missed by all detectors. The label-error citation was NOT added (could not fetch/confirm the paper).",
     f"13. **Clock evidence limits.** The UNB schedule page was unreachable from this machine (proxy 403), so agreement with the published schedule is NOT verified; only the data-internal evidence below. File row order is not chronological (backward steps: Wed {raw_prep('wed','fileorder_backward_steps_fixed')}, Thu {raw_prep('thu','fileorder_backward_steps_fixed')}), so it is no independent evidence. Thursday contains no 1970 rows (brief says each file has some).",
     f"14. **Capture length.** Brief says 12 h; measured spans after repair are {v('prep.wed.span_hours')} h (Wed) and {v('prep.thu.span_hours')} h (Thu). Task 2 FA/day uses 12 h as planned, so is lower than a measured-span scaling would give.",
     "15. **Not done / deviations.** `run_all.sh` was not executed end to end in one go (stages were run individually, some concurrently; total >3 h); task1 train times in `task1_results.json` are contended (MLP wed70 ~31 min), clean ones in `task1_timing.json` for Wed 80% and Thu 70% only. Task 1 random-split runs use the day's 70%-split tuned settings. GMM grid used one seed; K-Means 5 seeds; sweeps 3 seeds (no seeds cut). DBSCAN sweeps at other PCA dims / sample sizes keep the same k-distance quantile of eps instead of the same eps. Report build is out of scope (docx work stopped on instruction)."]
    L.extend(f"{x}\n" for x in F)
    # ---------------- sec 3
    h("PLAN section 3: data preparation (`results/prep_{wed,thu}.json`)")
    rows = []
    for d, nm in (("wed", "Wednesday"), ("thu", "Thursday")):
        for k_, lab in (("rows_in_file", "rows in file"), ("header_lines", "repeated header lines removed"), ("rows_1970", "1970-dated rows removed"), ("rows_infinity", "rows with +-Infinity removed"),
                        ("rows_nan_after_inf", "NaN rows remaining after Infinity removal"), ("rows_nan_total_before_inf_removal", "rows with any NaN before removal (all also had Infinity)"), ("duplicate_rows_kept", "duplicate rows (counted, kept)"),
                        ("rows_kept", "rows kept"), ("n_constant", "constant columns removed"), ("n_features", "final feature count"), ("attack_flows", "attack flows"), ("flows_moved_by_clock_fix", "flows moved by clock repair")):
            rows.append(R(f"{nm}: {lab}", f"prep.{d}.{k_}"))
        rows.append(R(f"{nm}: attack share %", f"prep.{d}.attack_share")); rows.append(R(f"{nm}: repaired span (h)", f"prep.{d}.span_hours"))
        P = jload(f"prep_{d}.json"); rows.append([f"{nm}: constant column names", ", ".join(P["constant_columns"]), f"`results/prep_{d}.json#constant_columns`"])
        for lab, e in P["clock_evidence"].items():
            rows.append([f"{nm} {lab}: first/last raw -> repaired", f"{e['raw_first']} / {e['raw_last']} -> {e['fixed_first']} / {e['fixed_last']}", f"`results/prep_{d}.json#clock_evidence.{lab}`"])
    table(rows)
    L.append("Interpretation: hours 01-07 move +12 h, 08-12 unchanged; repaired series is one daytime window with compact attack windows. `Protocol` kept; `Timestamp`, `Dst Port` dropped; duplicates kept.\n")
    # ---------------- sec 4
    h("PLAN section 4: Task 1 (`results/task1_results.json`, `task1_sensitivity.csv`, `task1_timing.json`)")
    for sid, nm in (("wed70", "Wednesday 70%"), ("wed80", "Wednesday 80%"), ("thu70", "Thursday 70%")):
        L.append(f"### {nm}\n")
        rows = [R("cut time", f"t1.{sid}.cut"), R("test window start", f"t1.{sid}.test_start"), R("test window end", f"t1.{sid}.test_end"), R("test hours", f"t1.{sid}.hours"), R("test attack flows", f"t1.{sid}.test_attack"),
                R("test benign flows", f"t1.{sid}.test_benign"), R("validation attack flows", f"t1.{sid}.val_attack"), R("fit-part attack flows", f"t1.{sid}.fit_attack")]
        for m in ("LogReg", "RandomForest", "MLP"):
            p = f"t1.{sid}.{m}"
            rows += [[f"{MN[m]}: precision / recall / F1 / AP", f"{v(p+'.precision')} / {v(p+'.recall')} / {v(p+'.f1')} / {v(p+'.ap')}", f"`#splits.{sid}.models.{m}`"],
                     [f"{MN[m]}: F1 95% block-bootstrap CI", f"[{v(p+'.f1_lo')}, {v(p+'.f1_hi')}] ({v('config.boot_n')} resamples, {v('config.block_min')}-min blocks)", f"`#splits.{sid}.models.{m}.f1_ci`"],
                     [f"{MN[m]}: TP/FP/FN/TN", f"{v(p+'.tp')} / {v(p+'.fp')} / {v(p+'.fn')} / {v(p+'.tn')}", f"`#splits.{sid}.models.{m}`"],
                     [f"{MN[m]}: false alerts/day [Poisson 95% CI]", f"{v(p+'.fa_value')} [{v(p+'.fa_lo')}, {v(p+'.fa_hi')}]", f"`#splits.{sid}.models.{m}.fa`"],
                     [f"{MN[m]}: recall at 100 / 1,000 / 10,000 FA/day (test-curve reading, %)", f"{v(p+'.budget_recall_100')} / {v(p+'.budget_recall_1000')} / {v(p+'.budget_recall_10000')}", f"`#splits.{sid}.models.{m}.budget_recall`"]]
        for pair in (("LogReg", "RandomForest"), ("LogReg", "MLP"), ("RandomForest", "MLP")):
            q = f"t1.{sid}.mc.{pair[0]}.{pair[1]}"; rows.append([f"McNemar {pair[0]} vs {pair[1]}", f"b={v(q+'.b')}, c={v(q+'.c')}, p={'<' if N[q+'.p']['lt'] else '='} {v(q+'.p')}", f"`#splits.{sid}.pairs`"])
        p = f"t1.{sid}.port_rule"
        rows += [["Port 21/22 rule: precision / recall / F1", f"{v(p+'.precision')} / {v(p+'.recall')} / {v(p+'.f1')}", f"`#splits.{sid}.port_rule`"], ["Port rule: false alerts/day [CI]", f"{v(p+'.fa_value')} [{v(p+'.fa_lo')}, {v(p+'.fa_hi')}]", f"`#splits.{sid}.port_rule.fa`"],
                 ["McNemar port rule vs RF", f"b={v(f't1.{sid}.port_rule_vs_RF.b')}, c={v(f't1.{sid}.port_rule_vs_RF.c')}, p={v(f't1.{sid}.port_rule_vs_RF.p')}", f"`#splits.{sid}.port_rule_vs_RF`"]]
        table(rows)
    L.append("Clean timings (s, train / predict): " + "; ".join(f"{k_}: {v('timing.'+k_.replace('|','.')+'.train_s')} / {v('timing.'+k_.replace('|','.')+'.predict_s')}" for k_ in ("wed80|LogReg", "wed80|RandomForest", "wed80|MLP", "thu70|LogReg", "thu70|RandomForest", "thu70|MLP")) + " (`task1_timing.json`).\n")
    L.append("### Thursday operating points (threshold from validation window, budget <= 1,000 FA/day)\n")
    rows = []
    for m in ("LogReg", "RandomForest", "MLP"):
        p = f"t1.thu70.{m}"; rows.append([MN[m], f"test recall {v(p+'.op_recall')}%, precision {v(p+'.op_precision')}, test FA/day {v(p+'.op_fa')} (validation {v(p+'.op_val_fa')})", f"`#splits.thu70.models.{m}.operating_point`"])
    p = "t1.thu70.payload_rule"; rows.append(["Payload rule on Thu test window", f"recall {v(p+'.recall_pct')}%, precision {v(p+'.precision')}, FA/day {v(p+'.fa_value')}", "`#splits.thu70.payload_rule`"])
    table(rows)
    L.append("### Leakage and clock demos\n")
    rows = []
    for d in DAYS:
        for m in ("LogReg", "RandomForest", "MLP"): rows.append([f"{d} random stratified 70/30, {MN[m]}: F1 / AP", f"{v(f'rand.{d}.{m}.f1')} / {v(f'rand.{d}.{m}.ap')} (gap to time split {v(f'leak.{d}.{m}.gap')})", f"`#random_split.{d}.{m}`"])
        rows.append([f"{d} unrepaired clock RF: F1", v(f"unrep.{d}.f1"), f"`#unrepaired_clock.{d}`"])
    table(rows)
    # ---------------- sec 5
    h("PLAN section 5: Task 2 (`results/task2_{wed,thu}.json`, `task2_grid.csv`, `task2_extra_sweeps.csv`)")
    for d, nm in (("wed", "Wednesday"), ("thu", "Thursday")):
        L.append(f"### {nm}\n")
        rows = [R("sample size / step", f"t2.{d}.n_sample"), R("sample step", f"t2.{d}.sample_step"), R("PCA components for 95% variance", f"t2.{d}.pca_k95"),
                [ "K-Means chosen k / mean silhouette / position", f"{v(f't2.{d}.km.k')} / {v(f't2.{d}.km.sil')} / {v(f't2.{d}.km.edge')}", f"`task2_{d}.json#kmeans`"],
                ["K-Means F1 at k-1, k, k+1 (seed means) range", f"{v(f't2.{d}.km.stab_lo')}-{v(f't2.{d}.km.stab_hi')}", f"`task2_{d}.json#kmeans.stability_f1_pm1`"],
                ["GMM chosen components / covariance / position", f"{v(f't2.{d}.gmm.k')} / {v(f't2.{d}.gmm.cov')} / {v(f't2.{d}.gmm.edge')} (grid max {v(f't2.{d}.gmm.grid_max')})", f"`task2_{d}.json#gmm`"],
                ["GMM F1 within one grid step range", f"{v(f't2.{d}.gmm.stab_lo')}-{v(f't2.{d}.gmm.stab_hi')}", f"`task2_{d}.json#gmm.stability_f1_pm1`"],
                ["DBSCAN chosen eps / min_samples / clusters / noise %", f"{v(f't2.{d}.db.eps')} / {v(f't2.{d}.db.ms')} / {v(f't2.{d}.db.clusters')} / {v(f't2.{d}.db.noise')}", f"`task2_{d}.json#dbscan`"],
                ["DBSCAN eps position; min_samples position", f"eps {v(f't2.{d}.db.edge')}; min_samples at upper edge", f"`task2_{d}.json#dbscan.eps_edge/ms_edge`"],
                ["DBSCAN F1 at eps +-1 and min_samples +-1 range", f"{v(f't2.{d}.db.stab_lo')}-{v(f't2.{d}.db.stab_hi')}", f"`task2_{d}.json#dbscan.stability_f1_neighbours`"],
                ["DBSCAN F1 over all settings; valid settings", f"{v(f't2.{d}.db.f1_min')}-{v(f't2.{d}.db.f1_max')}; {v(f't2.{d}.db.nvalid')} of {v(f't2.{d}.db.nsettings')}", f"`task2_{d}.json#dbscan`"],
                ["min_samples extension (100, 200): silhouette old -> new (ms), F1 old -> new", f"{v(f't2.{d}.msx.old_best_sil')} -> {v(f't2.{d}.msx.ext_best_sil')} (ms {v(f't2.{d}.msx.ext_best_ms')}); {v(f't2.{d}.msx.old_best_f1')} -> {v(f't2.{d}.msx.ext_best_f1')}", f"`task2_dbscan_ms_check_{d}.json`"]]
        for nm_, a in (("K-Means", "km"), ("GMM", "gmm"), ("DBSCAN", "db")):
            p = f"t2.{d}.{a}.final"
            rows.append([f"{nm_}: precision / recall / F1 [min-max over {v(p+'.nseeds')} seeds]", f"{v(p+'.precision')} / {v(p+'.recall')} / {v(p+'.f1')} [{v(p+'.f1_min')}-{v(p+'.f1_max')}]", f"`task2_{d}.json#final`"])
            rows.append([f"{nm_}: analyst labels / FA per day (Task 2 conv.)", f"{v(p+'.labels')} / {v(p+'.fa')}", f"`task2_{d}.json#final`"])
        rows.append(["K-Means / GMM / DBSCAN best F1 anywhere in grid", f"{v(f't2.{d}.km.best_grid')} / {v(f't2.{d}.gmm.best_grid')} / {v(f't2.{d}.db.f1_max')}", f"`task2_{d}.json`"])
        for rn in (("port",) if d == "wed" else ("port", "payload")):
            for part in ("sample", "full_day"):
                p = f"t2.{d}.rule.{rn}.{part}"; rows.append([f"{rn} rule ({part}): P / R / F1 / FA per day", f"{v(p+'.precision')} / {v(p+'.recall')} / {v(p+'.f1')} / {v(p+'.fa')}", f"`task2_{d}.json#rules.{rn}.{part}`"])
        for g in ("benign", "found_any", "only_kmeans", "only_gmm", "only_dbscan", "missed_all"):
            kk = f"fm.{d}.{g}.n"
            if kk in N:
                med = " | ".join(f"{c}: {v(f'fm.{d}.{g}.med.{c}')}" for c in ("Flow Duration", "TotLen Fwd Pkts", "TotLen Bwd Pkts", "Flow Pkts/s", "Init Fwd Win Byts") if f"fm.{d}.{g}.med.{c}" in N)
                rows.append([f"group {g}: flows; rules catching (port / payload); medians", f"{v(kk)}; {v(f'fm.{d}.{g}.port_rule')} / {v(f'fm.{d}.{g}.payload_rule')}; {med}", f"`task2_{d}.json#found_missed`"])
        table(rows)
    L.append("Sweeps (PCA dims, sample size, triage flows, analyst error): per-value seed-mean F1 are keys `sw.{day}.{algo}.{sweep}.v{value}` in `report_numbers.json`, raw rows in `results/task2_extra_sweeps.csv`; grid in `results/task2_grid.csv`.\n")
    rows = []
    for sw in ("pca_dims", "sample_size", "triage_n", "analyst_error"):
        for d in DAYS:
            rows.append([f"{sw} {d}: F1 range K-Means / GMM / DBSCAN", " / ".join(f"{v(f'sw.{d}.{a}.{sw}.min')}-{v(f'sw.{d}.{a}.{sw}.max')}" for a in ("km", "gmm", "db")), "`results/task2_extra_sweeps_*.csv`"])
    rows.append(R("max |F1(10% analyst error) - F1(0)| over all algos/days", "sw.maxshift_error"))
    table(rows)
    L.append("Interpretation: analyst error up to 10% barely moves F1 (majority vote over 20 flows absorbs it); more flows per cluster raises label cost without F1 gain; PCA 5 hurts K-Means on Thursday.\n")
    open(os.path.join(ROOT, "RESULTS_SUMMARY.md"), "w").write("\n".join(L))


def changes():
    C = ["# CHANGES: v1 -> new (every new value computed by this repo's code; source = file#key via `report_numbers.json`)\n",
         "v1 values are quoted from `report/original/SEC635_Lab1_Report_v1.docx` and were produced by code that is not available; they are only reproduced where noted.\n",
         "| Item | v1 | New | Source |", "|---|---|---|---|"]
    def add(item, old, new, key): C.append(f"| {item} | {old} | {new} | `{src(key)}` |")
    add("Wed 80% RF F1 / false alerts per day", "0.9999 / 49", f"{v('t1.wed80.RandomForest.f1')} / {v('t1.wed80.RandomForest.fa_value')} [CI {v('t1.wed80.RandomForest.fa_lo')}-{v('t1.wed80.RandomForest.fa_hi')}] (reproduced; CI added)", "t1.wed80.RandomForest.fa_value")
    add("Wed 80% LogReg / MLP false alerts per day", "2,588 / 74", f"{v('t1.wed80.LogReg.fa_value')} / {v('t1.wed80.MLP.fa_value')}", "t1.wed80.LogReg.fa_value")
    add("Wed 70% false alerts per day LogReg / RF / MLP", "409 / 27 / 34", f"{v('t1.wed70.LogReg.fa_value')} / {v('t1.wed70.RandomForest.fa_value')} / {v('t1.wed70.MLP.fa_value')} (tuned LogReg C=10, MLP 128-64)", "t1.wed70.LogReg.fa_value")
    add("Wed 70% recall (all models)", "0.0002", f"{v('t1.wed70.RandomForest.recall')}", "t1.wed70.RandomForest.recall")
    add("Wed 70% LogReg AP (cited, not shown)", "0.983", f"{v('t1.wed70.LogReg.ap')} (now shown in the PR curves)", "t1.wed70.LogReg.ap")
    add("Thu 70% F1 LogReg / RF / MLP", "0.336 / 0.383 / 0.259", f"{v('t1.thu70.LogReg.f1')} / {v('t1.thu70.RandomForest.f1')} / {v('t1.thu70.MLP.f1')}", "t1.thu70.RandomForest.f1")
    add("Thu 70% false alerts per day LogReg / RF / MLP", "104,988 / 130,699 / 11,791", f"{v('t1.thu70.LogReg.fa_value')} / {v('t1.thu70.RandomForest.fa_value')} / {v('t1.thu70.MLP.fa_value')}", "t1.thu70.RandomForest.fa_value")
    add("Random-split RF F1 Wed / Thu", "1.000 / 0.492", f"{v('rand.wed.RandomForest.f1')} / {v('rand.thu.RandomForest.f1')}", "rand.thu.RandomForest.f1")
    add("Leakage claim", "1.000 random vs 0.000 time split (Wed 70%)", f"like-for-like Wed gap {v('leak.wed.gap')}; Thu gap {v('leak.thu.gap')}, {v('leak.thu.inside')} the time-split CI", "leak.thu.gap")
    add("Unrepaired-clock F1 (Wed)", "1.000", v("unrep.wed.f1") + f"; Thu {v('unrep.thu.f1')}", "unrep.wed.f1")
    add("Wed rows kept / attack flows", "1,044,746 / FTP 193,354, SSH 187,589", f"{v('prep.wed.rows_kept')} / FTP {v('prep.wed.label.FTP-BruteForce')}, SSH {v('prep.wed.label.SSH-Bruteforce')}", "prep.wed.rows_kept")
    add("Thu removed header / 1970 / Infinity", "25 / 0 / 2,919", f"{v('prep.thu.header_lines')} / {v('prep.thu.rows_1970')} / {v('prep.thu.rows_infinity')}", "prep.thu.rows_infinity")
    add("Features after cleaning", "not stated", f"Wed {v('prep.wed.n_features')}, Thu {v('prep.thu.n_features')}", "prep.wed.n_features")
    add("Flows moved by clock fix Wed / Thu", "377,414 / 163,781", f"{v('prep.wed.flows_moved_by_clock_fix')} / {v('prep.thu.flows_moved_by_clock_fix')}", "prep.wed.flows_moved_by_clock_fix")
    add("Wed split attack counts (80%)", "FTP 193,354 + SSH 69,790; test SSH 117,799", f"FTP {v('t1.wed80.train.FTP-BruteForce')} + SSH {v('t1.wed80.train.SSH-Bruteforce')}; test SSH {v('t1.wed80.test.SSH-Bruteforce')}", "t1.wed80.test.SSH-Bruteforce")
    add("Wed K-Means / GMM / DBSCAN F1 (chosen)", "0.956 / 0.963 / 0.962", f"{v('t2.wed.km.final.f1')} / {v('t2.wed.gmm.final.f1')} / {v('t2.wed.db.final.f1')}", "t2.wed.db.final.f1")
    add("Wed detector choices", "k=19; GMM 20 full; DBSCAN 37 clusters", f"k={v('t2.wed.km.k')}; GMM {v('t2.wed.gmm.k')} {v('t2.wed.gmm.cov')} (edge of grid to 120); DBSCAN {v('t2.wed.db.clusters')} clusters, min_samples {v('t2.wed.db.ms')}", "t2.wed.gmm.k")
    add("Wed port rule F1 on the 40k sample / FA per day", "0.9995 / 797", f"{v('t2.wed.rule.port.sample.f1')} / {v('t2.wed.rule.port.sample.fa')}", "t2.wed.rule.port.sample.f1")
    add("Wed detector false alerts/day K-Means / GMM / DBSCAN (Task 2 conv.)", "70,230 / 57,353 / 59,875", f"{v('t2.wed.km.final.fa')} / {v('t2.wed.gmm.final.fa')} / {v('t2.wed.db.final.fa')}", "t2.wed.db.final.fa")
    add("Thu K-Means / GMM / DBSCAN F1", "0.370 / 0.392 / 0.398", f"{v('t2.thu.km.final.f1')} / {v('t2.thu.gmm.final.f1')} / {v('t2.thu.db.final.f1')}", "t2.thu.km.final.f1")
    add("Thu detector choices", "k=17; GMM 20 full (grid edge); DBSCAN 54 clusters", f"k={v('t2.thu.km.k')}; GMM {v('t2.thu.gmm.k')} {v('t2.thu.gmm.cov')} (interior); DBSCAN {v('t2.thu.db.clusters')} clusters", "t2.thu.gmm.k")
    add("Thu port rule F1 / FA per day (sample)", "0.019 / 3,348", f"{v('t2.thu.rule.port.sample.f1')} / {v('t2.thu.rule.port.sample.fa')}", "t2.thu.rule.port.sample.f1")
    add("Thu DBSCAN stability", "F1 0.348-0.419 over 24 settings (flat)", f"F1 {v('t2.thu.db.f1_min')}-{v('t2.thu.db.f1_max')} over {v('t2.thu.db.nsettings')}; {v('t2.thu.db.stab_lo')}-{v('t2.thu.db.stab_hi')} within one step", "t2.thu.db.f1_min")
    add("Thu K-Means seed range at chosen k", "0.028-0.393", f"{v('t2.thu.km.final.f1_min')}-{v('t2.thu.km.final.f1_max')}", "t2.thu.km.final.f1_min")
    add("Thu infiltration found / rule missed of found", "3,757 found; rule missed 3,697", f"{v('fm.thu.found_any.n')} found; port rule caught {v('fm.thu.found_any.port_rule')}, payload rule {v('fm.thu.found_any.payload_rule')} ({v('fm.thu.found_any.payload_rule_share')}%)", "fm.thu.found_any.n")
    add("Thu share of infiltration missed by all detectors", "67%", f"{v('fm.thu.missed_share_of_attack')}%", "fm.thu.missed_share_of_attack")
    add("Thu DBSCAN-alone / GMM-alone / K-Means-alone finds", "489 / 131 / 14", f"{v('fm.thu.only_dbscan.n')} / {v('fm.thu.only_gmm.n')} / {v('fm.thu.only_kmeans.n')}", "fm.thu.only_dbscan.n")
    add("Thu found-group medians (duration us, packets/s, window)", "239; 8,368; 1,024", f"{v('fm.thu.found_any.med.Flow Duration')}; {v('fm.thu.found_any.med.Flow Pkts/s')}; {v('fm.thu.found_any.med.Init Fwd Win Byts')}", "fm.thu.found_any.med.Flow Duration")
    add("Thu missed-group medians (duration us, packets/s, window)", "30,353; 115; 176", f"{v('fm.thu.missed_all.med.Flow Duration')}; {v('fm.thu.missed_all.med.Flow Pkts/s')}; {v('fm.thu.missed_all.med.Init Fwd Win Byts')}", "fm.thu.missed_all.med.Flow Duration")
    add("Wed SSH vs benign medians (packets/s; init window)", "333,333 and 26,883 vs 114 and 278", f"{v('sep.wed.ssh.pkts')} and {v('sep.wed.ssh.win')} vs {v('sep.wed.benign.pkts')} and {v('sep.wed.benign.win')}", "sep.wed.ssh.pkts")
    add("RF train time (Wed 80%)", "36 s", f"{v('timing.wed80.RandomForest.train_s')} s (clean re-timing)", "timing.wed80.RandomForest.train_s")
    add("Production: RF on Thu cost", "130,699/day = 2,178 h (~90 analysts of 24 h)", f"{v('t1.thu70.RandomForest.fa_value')}/day = {v('t1.thu70.RandomForest.fa_hours0')} h = {v('t1.thu70.RandomForest.fa_analysts0')} analysts on 8 h shifts", "t1.thu70.RandomForest.fa_hours0")
    C += ["", "## Claims changed in wording (no number)", "- 'misses 67% of the rest' -> misses the share above, and a payload rule explains most of what clustering found.",
          "- 'Signed log and scaling are fitted on training data only' -> only the scaling is fitted (the signed log has no parameters).",
          "- 'Published schedule puts SSH at 14:01' -> not verified (UNB page unreachable); only data-internal evidence is claimed.",
          "- 'Port rule does better than clustering on Wednesday' -> DBSCAN matches it (see table); rule vs RF compared on the Task 1 windows for the first time.",
          "- 'DBSCAN is stable' -> not flat; chosen min_samples at the grid edge, silhouette keeps rising when extended.",
          "- 'GMM only works at 20 (grid edge)' -> Thu GMM now interior at 54; Wed GMM BIC never turns by 120.",
          "- Table 6 false-alert conventions must stay separate (Task 1: benign flagged / window hours x 24; Task 2: sample FPR x day's benign x 24/12).",
          "", "## User-supplied (not computed)", "- Cover details supplied by the lead/user: team members and IDs (Ahmed Alnuaimi M80009405, Mansour Alkaabi M80009410, Ahmed Almansoori M80009548), instructor Dr. Ahmad Samer Wazan, submission date 3 November 2026. A repository URL placeholder is to be filled after upload. The report itself is being written separately; nothing in this repo edits the docx."]
    open(os.path.join(ROOT, "CHANGES.md"), "w").write("\n".join(C) + "\n")


def raw_prep(d, k): return jload(f"prep_{d}.json")[k]


if __name__ == "__main__":
    main(); changes()
