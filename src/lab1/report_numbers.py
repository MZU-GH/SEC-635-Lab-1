"""Stage 6a: collect every number the report prints, formatted exactly as printed -> results/report_numbers.json"""
import glob
from lab1.common import *
import lab1.task1 as t1, lab1.task2 as t2

N = {}


def put(key, value, text, source):
    assert key not in N, key
    N[key] = {"value": value, "text": str(text), "source": source}


def f_met(x):                      # precision / recall / F1 / AP
    x = float(x)
    if 0 < x < 0.001: return f"{x:.4f}"
    s = f"{x:.4f}" if x >= 0.995 else f"{x:.3f}"
    return "1.000" if s == "1.0000" else s


FMT = {"cnt": lambda x: f"{int(round(x)):,}", "f3": lambda x: f"{x:.3f}", "f4": lambda x: f"{x:.4f}", "met": f_met,
       "pct0": lambda x: f"{100*x:.0f}", "pct1": lambda x: f"{100*x:.1f}", "pct2": lambda x: f"{100*x:.2f}",
       "h1": lambda x: f"{x:.1f}", "h2": lambda x: f"{x:.2f}", "x0": lambda x: f"{x:.0f}", "x1": lambda x: f"{x:.1f}", "s0": lambda x: f"{x:.0f}",
       "raw": lambda x: str(x), "ts": lambda x: x}


def num(key, v, kind, source):
    put(key, v, FMT[kind](v), source)


def hhmm(ts): return str(ts)[11:16]


def pval(key, p, source):
    put(key, p, "0.001" if p < 0.001 else f"{p:.2f}", source); N[key]["lt"] = bool(p < 0.001)


def build_task1_prep():
    for d in DAYS:
        P = jload(f"prep_{d}.json"); src = f"results/prep_{d}.json"
        for k in ("rows_in_file", "header_lines", "rows_1970", "rows_infinity", "rows_nan_after_inf", "rows_nan_total_before_inf_removal", "rows_kept",
                  "duplicate_rows_kept", "n_features", "attack_flows", "benign_flows", "flows_moved_by_clock_fix"):
            num(f"prep.{d}.{k}", P[k], "cnt", f"{src}#{k}")
        num(f"prep.{d}.n_constant", len(P["constant_columns"]), "cnt", f"{src}#constant_columns")
        num(f"prep.{d}.attack_share", P["attack_share"], "pct1", f"{src}#attack_share")
        num(f"prep.{d}.span_hours", P["span_hours_fixed"], "h1", f"{src}#span_hours_fixed")
        for lab, n in P["labels"].items(): num(f"prep.{d}.label.{lab}", n, "cnt", f"{src}#labels.{lab}")
        for lab, e in P["clock_evidence"].items():
            for k in ("raw_first", "raw_last", "fixed_first", "fixed_last"):
                put(f"clock.{d}.{lab}.{k}", e[k], hhmm(e[k]), f"{src}#clock_evidence.{lab}.{k}")
    # task 1
    R = jload("task1_results.json"); C = R["config"]; src = "results/task1_results.json"
    num("config.boot_n", C["n_boot"], "cnt", f"{src}#config.n_boot"); num("config.block_min", C["block_minutes"], "cnt", f"{src}#config.block_minutes")
    num("config.tune_step", C["tune_step"], "cnt", f"{src}#config.tune_step"); num("config.min_attacks", C["min_attacks_for_tuning"], "cnt", f"{src}#config.min_attacks_for_tuning")
    num("config.budget", C["budget_fa_per_day"], "cnt", f"{src}#config.budget_fa_per_day"); num("config.seed", C["seed"], "cnt", f"{src}#config.seed")
    num("config.rf_trees", 100, "cnt", "src/lab1/task1.py DEFAULTS"); num("config.rf_leaf", 2, "cnt", "src/lab1/task1.py DEFAULTS")
    num("config.mlp_l1", 64, "cnt", "src/lab1/task1.py DEFAULTS"); num("config.mlp_l2", 32, "cnt", "src/lab1/task1.py DEFAULTS")
    num("config.thr", 0.5, "f3", "src/lab1/task1.py"); num("config.ci_level", 95, "cnt", "src/lab1/common.py"); num("config.val_frac", 0.2, "pct0", "src/lab1/task1.py")
    num("config.mcnemar_switch", 25, "cnt", "src/lab1/common.py mcnemar"); num("config.hours_day", 24, "cnt", "src/lab1/common.py"); num("config.shift_hours", 8, "cnt", "assumption")
    num("config.min_per_alert", 1, "cnt", "assumption (explicit)"); num("config.capture_hours", CAPTURE_HOURS, "cnt", "brief: each day is a 12-hour capture")
    for g, tr in (("rf_trees", t1.GRID["RandomForest"]),):
        pass
    num("config.grid_rf_trees_a", 50, "cnt", "task1.GRID"); num("config.grid_rf_trees_b", 200, "cnt", "task1.GRID"); num("config.grid_rf_leaf_a", 1, "cnt", "task1.GRID"); num("config.grid_rf_leaf_b", 5, "cnt", "task1.GRID")
    num("config.grid_lr_a", 0.1, "raw", "task1.GRID"); num("config.grid_lr_b", 10, "cnt", "task1.GRID"); num("config.mlp_g1", 32, "cnt", "task1.GRID"); num("config.mlp_g2a", 128, "cnt", "task1.GRID"); num("config.mlp_g2b", 64, "cnt", "task1.GRID")
    num("config.budget_100", 100, "cnt", "task1.py"); num("config.budget_10000", 10000, "cnt", "task1.py")
    for sid, S in R["splits"].items():
        s = f"{src}#splits.{sid}"
        put(f"t1.{sid}.cut", S["cut_time"], hhmm(S["cut_time"]), f"{s}.cut_time")
        put(f"t1.{sid}.test_start", S["test_start"], hhmm(S["test_start"]), f"{s}.test_start"); put(f"t1.{sid}.test_end", S["test_end"], hhmm(S["test_end"]), f"{s}.test_end")
        put(f"t1.{sid}.val_start", S["val_start"], hhmm(S["val_start"]), f"{s}.val_start"); put(f"t1.{sid}.val_end", S["val_end"], hhmm(S["val_end"]), f"{s}.val_end")
        num(f"t1.{sid}.hours", S["test_hours"], "h1", f"{s}.test_hours"); num(f"t1.{sid}.val_hours", S["val_hours"], "h1", f"{s}.val_hours")
        for k in ("test_attack", "test_benign", "val_attack", "fit_attack", "train_rows", "test_rows"): num(f"t1.{sid}.{k}", S[k], "cnt", f"{s}.{k}")
        for lab, n in S["train_labels"].items(): num(f"t1.{sid}.train.{lab}", n, "cnt", f"{s}.train_labels.{lab}")
        for lab, n in S["test_labels"].items(): num(f"t1.{sid}.test.{lab}", n, "cnt", f"{s}.test_labels.{lab}")
        if "sensitivity" in S:
            for m, v in S["sensitivity"].items(): num(f"t1.{sid}.{m}.sens_range", v["range"], "f3", f"{s}.sensitivity.{m}.range")
            num(f"t1.{sid}.sens_max", max(v["range"] for v in S["sensitivity"].values()), "f3", f"{s}.sensitivity")
        for m, ch in S["chosen"].items():
            for k, v in ch.items():
                if k == "hidden": num(f"t1.{sid}.{m}.hid1", v[0], "cnt", f"{s}.chosen.{m}"); num(f"t1.{sid}.{m}.hid2", v[1] if len(v) > 1 else 0, "cnt", f"{s}.chosen.{m}")
                else: num(f"t1.{sid}.{m}.{k}", v, "raw", f"{s}.chosen.{m}.{k}")
        for m, x in S["models"].items():
            b = f"{s}.models.{m}"; k_ = f"t1.{sid}.{m}"
            for k in ("precision", "recall", "f1", "ap"): num(f"{k_}.{k}", x[k], "met", f"{b}.{k}")
            num(f"{k_}.recall_pct", x["recall"], "pct2", f"{b}.recall"); num(f"{k_}.miss_pct", 1 - x["recall"], "pct1", f"{b}.recall")
            for k in ("tp", "fp", "fn", "tn"): num(f"{k_}.{k}", x[k], "cnt", f"{b}.{k}")
            num(f"{k_}.f1_lo", x["f1_ci"][0], "met", f"{b}.f1_ci"); num(f"{k_}.f1_hi", x["f1_ci"][1], "met", f"{b}.f1_ci")
            for k in ("value", "lo", "hi"): num(f"{k_}.fa_{k}", x["fa"][k], "cnt", f"{b}.fa.{k}")
            num(f"{k_}.fa_hours_per_day", x["fa"]["value"] * C_MIN / 60, "h1", f"{b}.fa.value * 1 min/alert")
            num(f"{k_}.train_s", x["train_s"], "s0", f"{b}.train_s")
            for bd, v in x["budget_recall"].items(): num(f"{k_}.budget_recall_{bd}", v, "pct1", f"{b}.budget_recall.{bd}")
            if "operating_point" in x:
                o = x["operating_point"]; ob = f"{b}.operating_point"
                num(f"{k_}.op_recall", o["recall"], "pct1", f"{ob}.recall"); num(f"{k_}.op_precision", o["precision"], "met", f"{ob}.precision")
                num(f"{k_}.op_fa", o["fa"]["value"], "cnt", f"{ob}.fa.value"); num(f"{k_}.op_val_fa", o["val_fa"], "cnt", f"{ob}.val_fa")
                num(f"{k_}.op_fa_ratio", o["fa"]["value"] / o["val_fa"], "x0", f"{ob}.fa.value / val_fa")
        for pair, v in S["pairs"].items():
            a, b_ = pair.split("|"); pval(f"t1.{sid}.mc.{a}.{b_}.p", v["p"], f"{s}.pairs.{pair}.p")
            num(f"t1.{sid}.mc.{a}.{b_}.b", v["b"], "cnt", f"{s}.pairs.{pair}.b"); num(f"t1.{sid}.mc.{a}.{b_}.c", v["c"], "cnt", f"{s}.pairs.{pair}.c")
        for nm in ("port_rule", "payload_rule"):
            x = S[nm]; b = f"{s}.{nm}"; k_ = f"t1.{sid}.{nm}"
            for k in ("precision", "recall", "f1"): num(f"{k_}.{k}", x[k], "met", f"{b}.{k}")
            num(f"{k_}.recall_pct", x["recall"], "pct1", f"{b}.recall")
            for k in ("tp", "fp", "fn"): num(f"{k_}.{k}", x[k], "cnt", f"{b}.{k}")
            for k in ("value", "lo", "hi"): num(f"{k_}.fa_{k}", x["fa"][k], "cnt", f"{b}.fa.{k}")
            num(f"{k_}.fa_hours_per_day", x["fa"]["value"] * C_MIN / 60, "h1", f"{b}.fa.value * 1 min/alert")
        for nm in ("port_rule_vs_RF", "port_rule_vs_MLP"):
            pval(f"t1.{sid}.{nm}.p", S[nm]["p"], f"{s}.{nm}.p"); num(f"t1.{sid}.{nm}.b", S[nm]["b"], "cnt", f"{s}.{nm}.b"); num(f"t1.{sid}.{nm}.c", S[nm]["c"], "cnt", f"{s}.{nm}.c")
        # ratios used in the text
        num(f"t1.{sid}.rule_over_rf_fa", S["port_rule"]["fa"]["value"] / max(1, S["models"]["RandomForest"]["fa"]["value"]), "x0", f"{s}")
    for d, v in R["random_split"].items():
        for m, x in v.items():
            for k in ("f1", "ap"): num(f"rand.{d}.{m}.{k}", x[k], "met", f"{src}#random_split.{d}.{m}.{k}")
    for d, x in R["unrepaired_clock"].items():
        s = f"{src}#unrepaired_clock.{d}"
        num(f"unrep.{d}.f1", x["f1"], "met", s)
        for w in ("train", "test"):
            put(f"unrep.{d}.{w}_raw_start", x[f"{w}_raw_clock"][0], hhmm(x[f"{w}_raw_clock"][0]), s); put(f"unrep.{d}.{w}_raw_end", x[f"{w}_raw_clock"][1], hhmm(x[f"{w}_raw_clock"][1]), s)
            put(f"unrep.{d}.{w}_true_start", x[f"{w}_true_clock"][0], hhmm(x[f"{w}_true_clock"][0]), s); put(f"unrep.{d}.{w}_true_end", x[f"{w}_true_clock"][1], hhmm(x[f"{w}_true_clock"][1]), s)
            for lab, n in x[f"{w}_labels"].items(): num(f"unrep.{d}.{w}.{lab}", n, "cnt", s)
    if os.path.exists(os.path.join(RES, "task1_timing.json")):
        for k, v in jload("task1_timing.json").items():
            sid, m = k.split("|"); num(f"timing.{sid}.{m}.train_s", v["train_s"], "s0", "results/task1_timing.json"); num(f"timing.{sid}.{m}.predict_s", v["predict_s"], "h1", "results/task1_timing.json")


C_MIN = 1.0     # assumed minutes of analyst time per alert (explicit assumption in the report)


def build_derived():
    R = jload("task1_results.json"); src = "results/task1_results.json"
    for d, sid in (("wed", "wed80"), ("thu", "thu70")):
        rf = R["random_split"][d]["RandomForest"]["f1"]; tf = R["splits"][sid]["models"]["RandomForest"]
        num(f"leak.{d}.gap", rf - tf["f1"], "f3", f"{src}#random_split.{d} - splits.{sid}")
        put(f"leak.{d}.inside", bool(tf["f1_ci"][0] <= rf <= tf["f1_ci"][1]), "inside" if tf["f1_ci"][0] <= rf <= tf["f1_ci"][1] else "outside", f"{src}")
    for d in DAYS:
        for m in ("LogReg", "RandomForest", "MLP"):
            sid = "wed80" if d == "wed" else "thu70"
            num(f"leak.{d}.{m}.gap", R["random_split"][d][m]["f1"] - R["splits"][sid]["models"][m]["f1"], "f3", f"{src}")
    for sid in ("wed70", "wed80", "thu70"):
        for m in ("LogReg", "RandomForest", "MLP"):
            x = R["splits"][sid]["models"][m]; num(f"t1.{sid}.{m}.fpr", x["fp"] / (x["fp"] + x["tn"]), "pct0", f"{src}#splits.{sid}.models.{m}")
            num(f"t1.{sid}.{m}.fa_analysts", x["fa"]["value"] / 60 / 8, "h1", f"{src} fa.value / 60 min / 8 h")
        for nm in ("port_rule",):
            x = R["splits"][sid][nm]; num(f"t1.{sid}.{nm}.fa_analysts", x["fa"]["value"] / 60 / 8, "h1", f"{src}")
    for m in ("LogReg", "RandomForest", "MLP"):
        o = R["splits"]["thu70"]["models"][m]["operating_point"]["fa"]["value"]
        num(f"t1.thu70.{m}.op_fa_hours", o / 60, "x0", f"{src} op fa / 60"); num(f"t1.thu70.{m}.op_fa_analysts", o / 60 / 8, "x1", f"{src} op fa / 60 / 8")
        fv = R["splits"]["thu70"]["models"][m]["fa"]["value"]; num(f"t1.thu70.{m}.fa_hours0", fv / 60, "cnt", f"{src}"); num(f"t1.thu70.{m}.fa_analysts0", fv / 60 / 8, "cnt", f"{src}")
    ra = R["splits"]["wed80"]; num("t1.wed80.rule_minus_rf_fa", ra["port_rule"]["fa"]["value"] - ra["models"]["RandomForest"]["fa"]["value"], "cnt", src)
    num("t1.wed80.rf_fa_share_of_shift", ra["models"]["RandomForest"]["fa"]["value"] / 60 / 8, "h1", src)
    num("t1.wed80.rule_fa_share_of_shift", ra["port_rule"]["fa"]["value"] / 60 / 8, "h1", src)
    for f in ("wed", "thu"):
        p_ = os.path.join(RES, f"task2_dbscan_ms_check_{f}.json")
        if os.path.exists(p_):
            C_ = jload(f"task2_dbscan_ms_check_{f}.json")
            for kk in ("old_best_sil", "ext_best_sil", "old_best_f1", "ext_best_f1"):
                if C_.get(kk) is not None: num(f"t2.{f}.msx.{kk}", C_[kk], "f3" if "sil" in kk else "met", f"results/task2_dbscan_ms_check_{f}.json#{kk}")
            if C_.get("ext_best_ms") is not None: num(f"t2.{f}.msx.ext_best_ms", C_["ext_best_ms"], "cnt", f"results/task2_dbscan_ms_check_{f}.json")
            put(f"t2.{f}.msx.improves", C_["ext_improves_silhouette"], "does" if C_["ext_improves_silhouette"] else "does not", f"results/task2_dbscan_ms_check_{f}.json")
            (num("config.t2.msx_a", 100, "cnt", "src/lab1/dbscan_ms_check.py"), num("config.t2.msx_b", 200, "cnt", "src/lab1/dbscan_ms_check.py")) if f == "wed" else None
    # separability of SSH vs benign on Wednesday (full day medians)
    df, _ = load_day("wed"); s_ = df[df["label"] == "SSH-Bruteforce"]; b_ = df[df["label"] == "Benign"]
    for c, nm in (("Flow Pkts/s", "pkts"), ("Init Fwd Win Byts", "win")):
        num(f"sep.wed.ssh.{nm}", s_[c].median(), "cnt", "data/interim/wed.pkl median"); num(f"sep.wed.benign.{nm}", b_[c].median(), "cnt", "data/interim/wed.pkl median")


def build_task2():
    import pandas as pd
    for d in DAYS:
        T = jload(f"task2_{d}.json"); src = f"results/task2_{d}.json"
        for k in ("n_sample", "sample_step", "sample_attack", "benign_day", "n_pca", "triage_n", "silhouette_subsample", "pca_k95"):
            num(f"t2.{d}.{k}", T[k], "cnt", f"{src}#{k}")
        K, G, D = T["kmeans"], T["gmm"], T["dbscan"]
        num(f"t2.{d}.km.k", K["k"], "cnt", f"{src}#kmeans.k"); num(f"t2.{d}.km.sil", K["silhouette"], "f3", f"{src}#kmeans.silhouette")
        put(f"t2.{d}.km.edge", K["edge"]["at_lower_edge"] or K["edge"]["at_upper_edge"], "at the grid edge" if (K["edge"]["at_lower_edge"] or K["edge"]["at_upper_edge"]) else "interior", f"{src}#kmeans.edge")
        num(f"t2.{d}.km.stab_lo", min(K["stability_f1_pm1"]), "met", f"{src}#kmeans.stability_f1_pm1"); num(f"t2.{d}.km.stab_hi", max(K["stability_f1_pm1"]), "met", f"{src}#kmeans.stability_f1_pm1")
        num(f"t2.{d}.km.best_grid", K["best_f1_in_grid_seedmean"], "met", f"{src}#kmeans.best_f1_in_grid_seedmean"); num(f"t2.{d}.km.best_k", K["best_f1_k"], "cnt", f"{src}#kmeans.best_f1_k")
        num(f"t2.{d}.km.kmax", max(K["grid"]), "cnt", f"{src}#kmeans.grid")
        num(f"t2.{d}.gmm.k", G["components"], "cnt", f"{src}#gmm.components"); put(f"t2.{d}.gmm.cov", G["cov"], G["cov"], f"{src}#gmm.cov")
        num(f"t2.{d}.gmm.grid_max", G["grid_max"], "cnt", f"{src}#gmm.grid_max")
        put(f"t2.{d}.gmm.edge", G["edge"]["at_upper_edge"], "at the grid edge" if G["edge"]["at_upper_edge"] else "interior", f"{src}#gmm.edge")
        num(f"t2.{d}.gmm.stab_lo", min(G["stability_f1_pm1"]), "met", f"{src}#gmm.stability_f1_pm1"); num(f"t2.{d}.gmm.stab_hi", max(G["stability_f1_pm1"]), "met", f"{src}#gmm.stability_f1_pm1")
        num(f"t2.{d}.gmm.best_grid", G["best_f1_in_grid"], "met", f"{src}#gmm.best_f1_in_grid")
        num(f"t2.{d}.db.eps", D["eps"], "f3", f"{src}#dbscan.eps"); num(f"t2.{d}.db.ms", D["min_samples"], "cnt", f"{src}#dbscan.min_samples")
        num(f"t2.{d}.db.clusters", D["n_clusters"], "cnt", f"{src}#dbscan.n_clusters"); num(f"t2.{d}.db.noise", D["noise"], "pct0", f"{src}#dbscan.noise")
        num(f"t2.{d}.db.neps", len(D["eps_grid"]), "cnt", f"{src}#dbscan.eps_grid"); num(f"t2.{d}.db.eps_lo", min(D["eps_grid"]), "f3", f"{src}#dbscan.eps_grid"); num(f"t2.{d}.db.eps_hi", max(D["eps_grid"]), "f3", f"{src}#dbscan.eps_grid")
        num(f"t2.{d}.db.stab_lo", min(D["stability_f1_neighbours"]), "met", f"{src}#dbscan.stability_f1_neighbours"); num(f"t2.{d}.db.stab_hi", max(D["stability_f1_neighbours"]), "met", f"{src}#dbscan.stability_f1_neighbours")
        num(f"t2.{d}.db.f1_min", D["f1_min_all"], "met", f"{src}#dbscan.f1_min_all"); num(f"t2.{d}.db.f1_max", D["f1_max_all"], "met", f"{src}#dbscan.f1_max_all")
        num(f"t2.{d}.db.nsettings", D["n_settings"], "cnt", f"{src}#dbscan.n_settings"); num(f"t2.{d}.db.nvalid", D["n_valid_settings"], "cnt", f"{src}#dbscan.n_valid_settings")
        put(f"t2.{d}.db.edge", D["eps_edge"]["at_lower_edge"] or D["eps_edge"]["at_upper_edge"], "at the grid edge" if (D["eps_edge"]["at_lower_edge"] or D["eps_edge"]["at_upper_edge"]) else "interior", f"{src}#dbscan.eps_edge")
        for a, nm in (("kmeans", "km"), ("gmm", "gmm"), ("dbscan", "db")):
            F = T["final"][a]
            for k in ("precision", "recall", "f1", "f1_min", "f1_max"): num(f"t2.{d}.{nm}.final.{k}", F[k], "met", f"{src}#final.{a}.{k}")
            num(f"t2.{d}.{nm}.final.labels", F["labels_used"], "cnt", f"{src}#final.{a}.labels_used"); num(f"t2.{d}.{nm}.final.fa", F["fa_day"], "cnt", f"{src}#final.{a}.fa_day")
            num(f"t2.{d}.{nm}.final.nseeds", F["n_seeds"], "cnt", f"{src}#final.{a}.n_seeds")
            num(f"t2.{d}.{nm}.final.fa_hours", F["fa_day"] * C_MIN / 60, "h1", f"{src}#final.{a}.fa_day * 1 min"); num(f"t2.{d}.{nm}.final.fa_analysts", F["fa_day"] * C_MIN / 60 / 8, "h1", f"{src}#final.{a}.fa_day * 1 min / 8 h")
        for nm, R_ in T["rules"].items():
            for part in ("sample", "full_day"):
                x = R_[part]
                for k in ("precision", "recall", "f1"): num(f"t2.{d}.rule.{nm}.{part}.{k}", x[k], "met", f"{src}#rules.{nm}.{part}.{k}")
                num(f"t2.{d}.rule.{nm}.{part}.fa", x["fa_day"], "cnt", f"{src}#rules.{nm}.{part}.fa_day")
                for k in ("tp", "fp", "fn"): num(f"t2.{d}.rule.{nm}.{part}.{k}", x[k], "cnt", f"{src}#rules.{nm}.{part}.{k}")
        FM = T["found_missed"]; s = f"{src}#found_missed"
        for g, n in FM["counts"].items(): num(f"fm.{d}.{g}.n", n, "cnt", f"{s}.counts.{g}")
        for g, v in FM["medians"].items():
            for c, x in v.items():
                if x is not None: num(f"fm.{d}.{g}.med.{c}", x, "cnt" if abs(x) >= 100 else "x0" if float(x).is_integer() else "x1", f"{s}.medians.{g}.{c}")
        for g, v in FM["rules_on_groups"].items():
            for r_, n in v.items():
                num(f"fm.{d}.{g}.{r_}", n, "cnt", f"{s}.rules_on_groups.{g}.{r_}")
                if FM["counts"][g]: num(f"fm.{d}.{g}.{r_}_share", n / FM["counts"][g], "pct0", f"{s}.rules_on_groups.{g}.{r_} / counts.{g}")
        for i, (pt, sh) in enumerate(FM["top_ports_missed_share"].items()):
            put(f"fm.{d}.missed_port{i+1}", int(pt), pt, f"{s}.top_ports_missed"); num(f"fm.{d}.missed_port{i+1}_share", sh, "pct0", f"{s}.top_ports_missed_share.{pt}")
        for a, n in FM["found_by_detector"].items(): num(f"fm.{d}.found.{a}", n, "cnt", f"{s}.found_by_detector.{a}")
        num(f"fm.{d}.missed_share_of_attack", FM["counts"]["missed_all"] / FM["counts"]["all_attack"], "pct0", f"{s}.counts")
        num(f"fm.{d}.found_share_of_attack", FM["counts"]["found_any"] / FM["counts"]["all_attack"], "pct0", f"{s}.counts")
        num(f"fm.{d}.nn_k", FM["nn_k"], "cnt", f"{s}.nn_k"); num(f"fm.{d}.nn_half", 5, "cnt", f"{s}.nn_rule")
        for g, v in FM["ordinary_checks"].items():
            if v["n"]:
                num(f"oc.{d}.{g}.n", v["n"], "cnt", f"{s}.ordinary_checks.{g}.n")
                num(f"oc.{d}.{g}.dup", v["dup_of_benign"], "cnt", f"{s}.ordinary_checks.{g}"); num(f"oc.{d}.{g}.dup_share", v["dup_of_benign"] / v["n"], "pct0", f"{s}.ordinary_checks.{g}")
                num(f"oc.{d}.{g}.nn", v["mostly_benign_nn"], "cnt", f"{s}.ordinary_checks.{g}"); num(f"oc.{d}.{g}.nn_share", v["mostly_benign_nn"] / v["n"], "pct0", f"{s}.ordinary_checks.{g}")
        # sweeps (seed means)
        E_ = pd.read_csv(os.path.join(RES, f"task2_extra_sweeps_{d}.csv")); sc = f"results/task2_extra_sweeps_{d}.csv"
        for (a, sw), g in E_[E_.sweep != "final"].groupby(["algo", "sweep"]):
            m = g.groupby("value", sort=False)["f1"].mean(); nm = {"kmeans": "km", "gmm": "gmm", "dbscan": "db"}[a]
            num(f"sw.{d}.{nm}.{sw}.min", m.min(), "met", sc); num(f"sw.{d}.{nm}.{sw}.max", m.max(), "met", sc)
            for v, x in m.items(): num(f"sw.{d}.{nm}.{sw}.v{str(v).rstrip('*')}", x, "met", sc)
            lab = g.groupby("value", sort=False)["labels_used"].mean()
            num(f"sw.{d}.{nm}.{sw}.labels_min", lab.min(), "cnt", sc); num(f"sw.{d}.{nm}.{sw}.labels_max", lab.max(), "cnt", sc)
    for d in DAYS:
        fs = [N[f"t2.{d}.{a}.final.f1"]["value"] for a in ("km", "gmm", "db")]; num(f"t2.{d}.spread", max(fs) - min(fs), "met", f"results/task2_{d}.json#final")
        num(f"t2.{d}.rule_over_det_fa", N[f"t2.{d}.rule.port.sample.fa"]["value"] and min(N[f"t2.{d}.{a}.final.fa"]["value"] for a in ("km", "gmm", "db")) / N[f"t2.{d}.rule.port.sample.fa"]["value"], "x0", f"results/task2_{d}.json")
        num(f"t2.{d}.rule_over_det_fa_max", max(N[f"t2.{d}.{a}.final.fa"]["value"] for a in ("km", "gmm", "db")) / N[f"t2.{d}.rule.port.sample.fa"]["value"], "x0", f"results/task2_{d}.json")
    sh = []
    for d in DAYS:
        E_ = pd.read_csv(os.path.join(RES, f"task2_extra_sweeps_{d}.csv")); E_ = E_[E_.sweep == "analyst_error"]
        for a, g in E_.groupby("algo"):
            m = g.groupby(g["value"].astype(float))["f1"].mean(); sh.append(abs(m.loc[0.1] - m.loc[0.0]))
    num("sw.maxshift_error", max(sh), "f3", "results/task2_extra_sweeps_*.csv (analyst_error sweep)")
    src = "src/lab1/task2.py"
    for k, v, kind in (("km_seeds", len(t2.KM_SEEDS), "cnt"), ("km_kmin", t2.KM_K[0], "cnt"), ("gmm_min", 2, "cnt"), ("gmm_step_from", 20, "cnt"), ("gmm_max", t2.GMM_MAX, "cnt"),
                       ("gmm_reg", t2.REG_LADDER[0], "raw"), ("noise_cap", t2.NOISE_CAP, "pct0"), ("ms_a", 5, "cnt"), ("ms_b", 10, "cnt"), ("ms_c", 25, "cnt"), ("ms_d", 50, "cnt"),
                       ("sweep_seeds", len(t2.SWEEP_SEEDS), "cnt"), ("n_sample", t2.N_SAMPLE, "cnt"), ("sil_n", t2.SIL_N, "cnt"), ("triage_n", t2.N_TRIAGE, "cnt"),
                       ("pca_dims", t2.N_PCA, "cnt"), ("fig_subsample", 5000, "cnt"), ("pca_a", 5, "cnt"), ("pca_b", 15, "cnt"), ("pca_c", 20, "cnt"), ("size_a", 10000, "cnt"), ("size_b", 20000, "cnt"), ("size_c", 80000, "cnt"),
                       ("triage_a", 5, "cnt"), ("triage_b", 10, "cnt"), ("triage_c", 50, "cnt"), ("err_a", 0.05, "pct0"), ("err_b", 0.10, "pct0"), ("var_target", 0.95, "pct0"),
                       ("payload_us", 1000, "cnt"), ("port_a", 21, "cnt"), ("port_b", 22, "cnt"), ("eps_n", t2.DB_NEPS, "cnt")):
        num(f"config.t2.{k}", v, kind, src)
    for sid, S in jload("task1_results.json")["splits"].items():
        for m, v in S.get("sensitivity", {}).items(): num(f"t1.{sid}.{m}.val_f1_max", v["max"], "met", f"results/task1_results.json#splits.{sid}.sensitivity.{m}")


def main():
    build_task1_prep(); build_derived(); build_task2()
    jdump(N, "report_numbers.json"); print(len(N), "numbers written")


if __name__ == "__main__":
    main()
