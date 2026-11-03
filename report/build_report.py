"""Build the Lab 1 report (HTML + PDF) from committed results only.

    .venv/bin/python report/build_report.py

Reads results/*.json|csv, registers every number printed in the report in a registry
(key -> text, raw value, source or formula), renders report/template.html.j2 with Jinja2
(StrictUndefined: a missing key fails the build) and writes
  report/SEC635_Lab1_Report.html, report/SEC635_Lab1_Report.pdf, results/report_registry.json
The raw data is not needed.
"""
import json, math, os, re, sys
import pandas as pd
import jinja2

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RES = os.path.join(ROOT, "results")
FIG = "../figures"


def jl(name):
    with open(os.path.join(RES, name)) as f:
        return json.load(f)


# ----------------------------------------------------------------------------- registry
class Reg(str):
    """Formatted text of a registered number; also carries its raw value and a p-value rendering."""
    value = None

    @property
    def p(self):                       # "p < 0.001" or "p = 0.01"
        return ("p < " if getattr(self, "lt", False) else "p = ") + str(self)


REGISTRY = {}


def _fmt(kind, v):
    if kind == "int": return f"{int(round(v)):,}"
    if kind in ("f1", "f2", "f3", "f4", "f5"): return f"{v:.{kind[1]}f}"
    if kind == "pct0": return f"{100 * v:.0f}%"
    if kind == "pct1": return f"{100 * v:.1f}%"
    if kind == "pct2": return f"{100 * v:.2f}%"
    if kind == "hours1": return f"{v:.1f}"
    if kind == "hours2": return f"{v:.2f}"
    if kind == "raw": return str(v)
    raise ValueError(kind)


def reg(key, value, fmt, source, text=None):
    assert key not in REGISTRY, f"duplicate registry key {key}"
    t = Reg(text if text is not None else _fmt(fmt, value))
    t.value = value
    REGISTRY[key] = {"text": str(t), "value": value if not hasattr(value, "item") else value.item(), "fmt": fmt, "source": source, "obj": t}
    return t


def derived(key, value, fmt, formula, srcs, text=None):
    return reg(key, value, fmt, f"derived: {formula} from {', '.join(srcs)}", text)


def R(key):
    return REGISTRY[key]["obj"]


def val(key):
    return REGISTRY[key]["value"]


# ----------------------------------------------------------------------------- load
T1 = jl("task1_results.json")
TIM = jl("task1_timing.json")
P = {"wed": jl("prep_wed.json"), "thu": jl("prep_thu.json")}
T2 = {"wed": jl("task2_wed.json"), "thu": jl("task2_thu.json")}
MS = {"wed": jl("task2_dbscan_ms_check_wed.json"), "thu": jl("task2_dbscan_ms_check_thu.json")}
SW = {d: pd.read_csv(os.path.join(RES, f"task2_extra_sweeps_{d}.csv")) for d in ("wed", "thu")}
GR = {d: pd.read_csv(os.path.join(RES, f"task2_grid_{d}.csv")) for d in ("wed", "thu")}
SENS = pd.read_csv(os.path.join(RES, "task1_sensitivity.csv"))
SPL = T1["splits"]
SIDS = ("wed70", "wed80", "thu70")
MODELS = ("LogReg", "RandomForest", "MLP")
MK = {"LogReg": "lr", "RandomForest": "rf", "MLP": "mlp"}
DAYS = ("wed", "thu")
ALGOS = ("kmeans", "gmm", "dbscan")
F1 = "results/task1_results.json"


def hhmm(ts):
    return str(ts)[11:16]


# ----------------------------------------------------------------------------- split names and global config
for sid in SIDS:
    pct = int(re.search(r"\d+", SPL[sid]["split_ids"]).group())
    reg(f"frac_{sid}", pct, "raw", f"{F1}#splits.{sid}.split_ids", text=f"{pct}%")
    reg(f"sp_{sid}", pct, "raw", f"{F1}#splits.{sid}.split_ids", text=f"{'Wed' if sid.startswith('wed') else 'Thu'} {pct}%")
derived("frac_30", 100 - val("frac_wed70"), "raw", "100 - 70", ["frac_wed70"], text=f"{100 - val('frac_wed70')}")
derived("frac_20", 100 - val("frac_wed80"), "raw", "100 - 80", ["frac_wed80"], text=f"{100 - val('frac_wed80')}")

C = T1["config"]
reg("c_boot", C["n_boot"], "int", f"{F1}#config.n_boot")
reg("c_block", C["block_minutes"], "int", f"{F1}#config.block_minutes")
reg("c_seed", C["seed"], "int", f"{F1}#config.seed")
reg("c_minatk", C["min_attacks_for_tuning"], "int", f"{F1}#config.min_attacks_for_tuning")
reg("c_budget", C["budget_fa_per_day"], "int", f"{F1}#config.budget_fa_per_day")
reg("c_tunestep", C["tune_step"], "int", f"{F1}#config.tune_step")
reg("c_ci", 95, "int", "convention: 95% intervals throughout", text="95%")
reg("c_thr", 0.5, "f1", "convention: decision threshold 0.5 (src/lab1/task1.py)")
reg("c_valfrac", 0.2, "pct0", "convention: last 20% of the training rows form the validation window (src/lab1/task1.py)")
reg("c_mcn", 25, "int", "convention: McNemar exact when b + c < 25 (src/lab1/common.py)")
reg("c_day", 24, "int", "assumption: alert counts are scaled to 24 h")
reg("c_min", 1, "int", "assumption: one analyst-minute per alert (brief: each flagged flow is an alert an analyst must clear)")
reg("c_shift", 8, "int", "assumption: one analyst works an 8-hour shift")
reg("c_minpermin", 60, "int", "unit conversion: 60 minutes per hour")
dflt = C["defaults"]
reg("cfg_rf_trees", dflt["RandomForest"]["n_estimators"], "int", f"{F1}#config.defaults.RandomForest.n_estimators")
reg("cfg_rf_leaf", dflt["RandomForest"]["min_samples_leaf"], "int", f"{F1}#config.defaults.RandomForest.min_samples_leaf")
reg("cfg_lr_c", dflt["LogReg"]["C"], "f1", f"{F1}#config.defaults.LogReg.C", text=f"{dflt['LogReg']['C']:g}")
for i, w in enumerate(dflt["MLP"]["hidden"]):
    reg(f"cfg_mlp_def{i}", w, "int", f"{F1}#config.defaults.MLP.hidden[{i}]")
G = C["grid"]
lr_grid = [g["C"] for g in G["LogReg"]]
rf_trees_grid = sorted({g["n_estimators"] for g in G["RandomForest"]})
rf_leaf_grid = sorted({g["min_samples_leaf"] for g in G["RandomForest"]})
mlp_grid = [g["hidden"] for g in G["MLP"]]
for i, c in enumerate(lr_grid): reg(f"g_lr{i}", c, "raw", f"{F1}#config.grid.LogReg", text=f"{c:g}")
for i, c in enumerate(rf_trees_grid): reg(f"g_rft{i}", c, "int", f"{F1}#config.grid.RandomForest.n_estimators")
for i, c in enumerate(rf_leaf_grid): reg(f"g_rfl{i}", c, "int", f"{F1}#config.grid.RandomForest.min_samples_leaf")
reg("g_mlp_a", mlp_grid[0][0], "int", f"{F1}#config.grid.MLP[0]")
reg("g_mlp_b", mlp_grid[1][0], "int", f"{F1}#config.grid.MLP[1]")
reg("g_mlp_b2", mlp_grid[1][1], "int", f"{F1}#config.grid.MLP[1]")
reg("g_mlp_c", mlp_grid[2][0], "int", f"{F1}#config.grid.MLP[2]")
reg("g_mlp_c2", mlp_grid[2][1], "int", f"{F1}#config.grid.MLP[2]")

# ----------------------------------------------------------------------------- data preparation
for d in DAYS:
    p = P[d]; src = f"results/prep_{d}.json"
    for k, key in (("rows_in_file", "rows"), ("header_lines", "hdr"), ("rows_1970", "r1970"), ("rows_infinity", "inf"),
                   ("rows_nan_after_inf", "nanafter"), ("rows_nan_total_before_inf_removal", "nanbefore"),
                   ("rows_kept", "kept"), ("duplicate_rows_kept", "dups"), ("n_features", "nfeat"),
                   ("attack_flows", "attack"), ("benign_flows", "benign"), ("flows_moved_by_clock_fix", "moved")):
        reg(f"p_{d}_{key}", p[k], "int", f"{src}#{k}")
    reg(f"p_{d}_nconst", len(p["constant_columns"]), "int", f"{src}#constant_columns (length)")
    reg(f"p_{d}_share", p["attack_share"], "pct1", f"{src}#attack_share")
    reg(f"p_{d}_span", p["span_hours_fixed"], "hours1", f"{src}#span_hours_fixed")
    for lab, n in p["labels"].items():
        reg(f"p_{d}_lab_{lab.split('-')[0].lower()}", n, "int", f"{src}#labels.{lab}")
    for lab, e in p["clock_evidence"].items():
        for k, kk in (("raw_first", "rf"), ("raw_last", "rl"), ("fixed_first", "ff"), ("fixed_last", "fl")):
            reg(f"clk_{d}_{lab.split('-')[0].lower()}_{kk}", e[k], "raw", f"{src}#clock_evidence.{lab}.{k}", text=hhmm(e[k]))
    # consistency: rows removed add up
    assert p["rows_in_file"] - p["header_lines"] - p["rows_1970"] - p["rows_infinity"] == p["rows_kept"], d
    assert p["rows_nan_after_inf"] == 0, "template states that NaN rows also held Infinity"
derived("p_all_hdr", P["wed"]["header_lines"] + P["thu"]["header_lines"], "int", "sum of header repeats", ["p_wed_hdr", "p_thu_hdr"])

# clock repair evidence: raw hour histogram (Wednesday)
hh = sorted(int(h) for h in P["wed"]["hour_hist_raw"])
blocks, cur = [], [hh[0], hh[0]]
for h in hh[1:]:
    if h == cur[1] + 1: cur[1] = h
    else: blocks.append(tuple(cur)); cur = [h, h]
blocks.append(tuple(cur))
assert len(blocks) == 2 and set(range(blocks[0][1] + 1, blocks[1][0])) == {6, 7}, blocks
assert sorted(int(h) for h in P["thu"]["hour_hist_raw"]) == hh, "Thursday raw hours differ from Wednesday"
for key, h in (("h_a1", blocks[0][0]), ("h_a2", blocks[0][1]), ("h_g1", blocks[0][1] + 1), ("h_g2", blocks[1][0] - 1), ("h_b1", blocks[1][0]), ("h_b2", blocks[1][1])):
    reg(key, h, "raw", "results/prep_wed.json#hour_hist_raw (hours holding traffic)", text=f"{h:02d}")
moved_by_hist = sum(v for h, v in P["wed"]["hour_hist_raw"].items() if int(h) <= blocks[0][1])
assert moved_by_hist == P["wed"]["flows_moved_by_clock_fix"]
ssh = P["wed"]["clock_evidence"]["SSH-Bruteforce"]
shift = (pd.Timestamp(ssh["fixed_first"]) - pd.Timestamp(ssh["raw_first"])).total_seconds() / 3600
derived("clk_shift", shift, "raw", "(SSH fixed_first - SSH raw_first) in hours", ["clk_wed_ssh_ff", "clk_wed_ssh_rf"], text=f"{shift:.0f}")
reg("p_wed_hist_hours_n", len(hh), "int", "results/prep_wed.json#hour_hist_raw (number of hours with traffic)")
reg("p_wed_back", P["wed"]["fileorder_backward_steps_fixed"], "int", "results/prep_wed.json#fileorder_backward_steps_fixed")
reg("p_thu_back", P["thu"]["fileorder_backward_steps_fixed"], "int", "results/prep_thu.json#fileorder_backward_steps_fixed")

# ----------------------------------------------------------------------------- Task 1
def fdig(values, lo_d=3, hi_d=5):
    """Smallest decimals in [lo_d, hi_d] such that no value in the group rounds to 0 or 1 unless exactly so,
    and values that differ by at least 2e-5 print differently."""
    vs = [float(v) for v in values]
    for dgt in range(lo_d, hi_d + 1):
        txt = [f"{v:.{dgt}f}" for v in vs]
        sat = any((0 < v < 1) and (t in (f"{0:.{dgt}f}", f"{1:.{dgt}f}")) for v, t in zip(vs, txt))
        clash = any(abs(a - b) >= 2e-5 and ta == tb for (a, ta) in zip(vs, txt) for (b, tb) in zip(vs, txt))
        if not sat and not clash:
            return dgt
    return hi_d


def metric_text(v, dgt):
    if v in (0, 1) or v == 0.0:
        return f"{v:.3f}"
    t = f"{v:.{dgt}f}"
    if 0 < v < 1 and t == f"{1:.{dgt}f}":
        return f">{1 - 10 ** -dgt:.{dgt}f}"
    return t


T1ROWS = {}                                   # (sid, who) -> dict of raw numbers
for sid in SIDS:
    s = SPL[sid]
    for m in MODELS:
        x = s["models"][m]
        T1ROWS[(sid, MK[m])] = dict(precision=x["precision"], recall=x["recall"], f1=x["f1"], ap=x["ap"], fp=x["fp"], tp=x["tp"], fn=x["fn"], tn=x["tn"],
                                    f1_lo=x["f1_ci"][0], f1_hi=x["f1_ci"][1], fa=x["fa"]["value"], fa_lo=x["fa"]["lo"], fa_hi=x["fa"]["hi"],
                                    src=f"{F1}#splits.{sid}.models.{m}")
    pr = s["port_rule"]
    T1ROWS[(sid, "port")] = dict(precision=pr["precision"], recall=pr["recall"], f1=pr["f1"], ap=None, fp=pr["fp"], tp=pr["tp"], fn=pr["fn"], tn=pr["tn"],
                                 f1_lo=None, f1_hi=None, fa=pr["fa"]["value"], fa_lo=pr["fa"]["lo"], fa_hi=pr["fa"]["hi"], src=f"{F1}#splits.{sid}.port_rule")
    if sid == "thu70":
        pl = s["payload_rule"]
        T1ROWS[(sid, "pay")] = dict(precision=pl["precision"], recall=pl["recall"], f1=pl["f1"], ap=None, fp=pl["fp"], tp=pl["tp"], fn=pl["fn"], tn=pl["tn"],
                                    f1_lo=None, f1_hi=None, fa=pl["fa"]["value"], fa_lo=pl["fa"]["lo"], fa_hi=pl["fa"]["hi"], src=f"{F1}#splits.{sid}.payload_rule")
    reg(f"t1_{sid}_hours", s["test_hours"], "hours1", f"{F1}#splits.{sid}.test_hours")
    reg(f"t1_{sid}_cut", s["cut_time"], "raw", f"{F1}#splits.{sid}.cut_time", text=hhmm(s["cut_time"]))
    reg(f"t1_{sid}_end", s["test_end"], "raw", f"{F1}#splits.{sid}.test_end", text=hhmm(s["test_end"]))
    reg(f"t1_{sid}_testatk", s["test_attack"], "int", f"{F1}#splits.{sid}.test_attack")
    reg(f"t1_{sid}_testben", s["test_benign"], "int", f"{F1}#splits.{sid}.test_benign")
    reg(f"t1_{sid}_valatk", s["val_attack"], "int", f"{F1}#splits.{sid}.val_attack")
    reg(f"t1_{sid}_fitatk", s["fit_attack"], "int", f"{F1}#splits.{sid}.fit_attack")
    for lab, n in s["train_labels"].items():
        if lab != "Benign": reg(f"t1_{sid}_train_{lab.split('-')[0].lower()}", n, "int", f"{F1}#splits.{sid}.train_labels.{lab}")
    for lab, n in s["test_labels"].items():
        if lab != "Benign": reg(f"t1_{sid}_test_{lab.split('-')[0].lower()}", n, "int", f"{F1}#splits.{sid}.test_labels.{lab}")
    derived(f"t1_{sid}_chance", s["test_attack"] / (s["test_attack"] + s["test_benign"]), "f3",
            "test_attack / (test_attack + test_benign)", [f"t1_{sid}_testatk", f"t1_{sid}_testben"])
    for m in MODELS:
        ch = s["chosen"][m]
        if m == "LogReg": reg(f"t1_{sid}_ch_lr", ch["C"], "raw", f"{F1}#splits.{sid}.chosen.LogReg.C", text=f"{ch['C']:g}")
        if m == "RandomForest":
            reg(f"t1_{sid}_ch_rft", ch["n_estimators"], "int", f"{F1}#splits.{sid}.chosen.RandomForest.n_estimators")
        if m == "MLP":
            reg(f"t1_{sid}_ch_mlp", "-".join(str(h) for h in ch["hidden"]), "raw", f"{F1}#splits.{sid}.chosen.MLP.hidden")
    rng_all = {m: s["sensitivity"][m]["range"] for m in MODELS}
    reg(f"t1_{sid}_sens_max", max(rng_all.values()), "f3", f"{F1}#splits.{sid}.sensitivity.*.range (max over the three families)")
    reg(f"t1_{sid}_sens_rf", rng_all["RandomForest"], "f3", f"{F1}#splits.{sid}.sensitivity.RandomForest.range")
    reg(f"t1_{sid}_sens_top", max(s["sensitivity"][m]["max"] for m in MODELS), "f4", f"{F1}#splits.{sid}.sensitivity.*.max (largest validation F1 of any setting)")
    reg(f"t1_{sid}_sens_rfmin", s["sensitivity"]["RandomForest"]["min"], "f3", f"{F1}#splits.{sid}.sensitivity.RandomForest.min")
    reg(f"t1_{sid}_sens_rfmax", s["sensitivity"]["RandomForest"]["max"], "f3", f"{F1}#splits.{sid}.sensitivity.RandomForest.max")
    # McNemar
    for pair, x in s["pairs"].items():
        a, b = pair.split("|")
        key = f"mc_{sid}_{MK[a]}_{MK[b]}"
        reg(key + "_b", x["b"], "int", f"{F1}#splits.{sid}.pairs.{pair}.b")
        reg(key + "_c", x["c"], "int", f"{F1}#splits.{sid}.pairs.{pair}.c")
        pv = x["p"]; t = reg(key + "_p", pv, "raw", f"{F1}#splits.{sid}.pairs.{pair}.p ({x['test']} McNemar)", text="0.001" if pv < 0.001 else f"{pv:.2f}"); t.lt = pv < 0.001
    for other in ("port_rule_vs_RF", "port_rule_vs_MLP"):
        x = s[other]; key = f"mc_{sid}_" + ("port_rf" if other.endswith("RF") else "port_mlp")
        reg(key + "_b", x["b"], "int", f"{F1}#splits.{sid}.{other}.b")
        reg(key + "_c", x["c"], "int", f"{F1}#splits.{sid}.{other}.c")
        pv = x["p"]; t = reg(key + "_p", pv, "raw", f"{F1}#splits.{sid}.{other}.p ({x['test']} McNemar)", text="0.001" if pv < 0.001 else f"{pv:.2f}"); t.lt = pv < 0.001
    reg(f"t1_{sid}_tuned", s["tuned"], "raw", f"{F1}#splits.{sid}.tuned", text=str(s["tuned"]))

# register the Table 3 numbers with per-(group, column) decimals
T3DIG = {}
for sid in SIDS:
    who_list = [w for (g, w) in T1ROWS if g == sid]
    for col in ("precision", "recall", "f1", "ap"):
        vals = [T1ROWS[(sid, w)][col] for w in who_list if T1ROWS[(sid, w)][col] is not None]
        if col == "f1":
            vals += [T1ROWS[(sid, w)][c] for w in who_list for c in ("f1_lo", "f1_hi") if T1ROWS[(sid, w)][c] is not None]
        T3DIG[(sid, col)] = fdig(vals[: len(vals)] if col != "f1" else vals[:len(who_list)] + [v for v in vals[len(who_list):]])
    for w in who_list:
        r = T1ROWS[(sid, w)]
        for col in ("precision", "recall", "f1", "ap", "f1_lo", "f1_hi"):
            v = r[col]
            if v is None: continue
            base = "f1" if col.startswith("f1") else col
            reg(f"t3_{sid}_{w}_{col}", v, "raw", f"{r['src']}.{col if col in ('precision','recall','f1','ap') else 'f1_ci'}", text=metric_text(v, T3DIG[(sid, base)]))
        for col in ("fp", "tp", "fn", "tn"):
            reg(f"t3_{sid}_{w}_{col}", r[col], "int", f"{r['src']}.{col}")
        for col in ("fa", "fa_lo", "fa_hi"):
            reg(f"t3_{sid}_{w}_{col}", r[col], "int", f"{r['src']}.fa.{ {'fa':'value','fa_lo':'lo','fa_hi':'hi'}[col] } (benign flows flagged / test hours x 24, exact Poisson CI)")

# Task 1 derived: analyst cost
fa = val("t3_wed80_rf_fa")
derived("w80_hours", fa * val("c_min") / val("c_minpermin"), "hours1", "FA/day x 1 min / 60", ["t3_wed80_rf_fa", "c_min", "c_minpermin"], text=f"{fa / 60:.1f}")
derived("w80_hours_hi", val("t3_wed80_rf_fa_hi") / 60, "hours1", "FA/day CI upper x 1 min / 60", ["t3_wed80_rf_fa_hi"], text=f"{val('t3_wed80_rf_fa_hi') / 60:.1f}")
derived("w80_shift", fa / 60 / val("c_shift"), "pct0", "analyst-hours per day / 8-hour shift", ["w80_hours", "c_shift"])
derived("w80_recall", val("t3_wed80_rf_recall"), "pct2", "RF recall Wed 80%", ["t3_wed80_rf_recall"])
derived("w80_mlp_gap", val("t3_wed80_lr_fa") / val("t3_wed80_rf_fa"), "f1", "LogReg FA/day / RF FA/day", ["t3_wed80_lr_fa", "t3_wed80_rf_fa"], text=f"{val('t3_wed80_lr_fa') / val('t3_wed80_rf_fa'):.0f}")
ta = val("t3_thu70_rf_fa")
derived("thu_hours", ta / 60, "int", "FA/day x 1 min / 60", ["t3_thu70_rf_fa", "c_min", "c_minpermin"])
derived("thu_analysts", ta / 60 / val("c_shift"), "int", "analyst-hours per day / 8-hour shift", ["thu_hours", "c_shift"])
derived("thu_per_analyst", val("c_shift") * val("c_minpermin") / val("c_min"), "int", "8 h x 60 / 1 min per alert", ["c_shift", "c_minpermin", "c_min"])
derived("thu_recall", val("t3_thu70_rf_recall"), "pct1", "RF recall Thu 70%", ["t3_thu70_rf_recall"])
derived("thu_miss", 1 - val("t3_thu70_rf_recall"), "pct0", "1 - RF recall Thu 70%", ["t3_thu70_rf_recall"])
derived("thu_benign_flagged", val("t3_thu70_rf_fp") / (val("t3_thu70_rf_fp") + val("t3_thu70_rf_tn")), "pct0", "RF FP / (FP + TN) Thu 70%", ["t3_thu70_rf_fp", "t3_thu70_rf_tn"])
op = SPL["thu70"]["models"]["RandomForest"]["operating_point"]
reg("thu_op_fa", op["fa"]["value"], "int", f"{F1}#splits.thu70.models.RandomForest.operating_point.fa.value")
reg("thu_op_recall", op["recall"], "pct0", f"{F1}#splits.thu70.models.RandomForest.operating_point.recall")
reg("thu_op_val_fa", op["val_fa"], "int", f"{F1}#splits.thu70.models.RandomForest.operating_point.val_fa")
derived("thu_op_x", op["fa"]["value"] / C["budget_fa_per_day"], "int", "operating-point test FA/day / budget", ["thu_op_fa", "c_budget"])
reg("thu_op_mlp_fa", SPL["thu70"]["models"]["MLP"]["operating_point"]["fa"]["value"], "int", f"{F1}#splits.thu70.models.MLP.operating_point.fa.value")
reg("thu_op_mlp_recall", SPL["thu70"]["models"]["MLP"]["operating_point"]["recall"], "pct0", f"{F1}#splits.thu70.models.MLP.operating_point.recall")
reg("thu_op_lr_fa", SPL["thu70"]["models"]["LogReg"]["operating_point"]["fa"]["value"], "int", f"{F1}#splits.thu70.models.LogReg.operating_point.fa.value")
reg("thu_op_lr_recall", SPL["thu70"]["models"]["LogReg"]["operating_point"]["recall"], "pct1", f"{F1}#splits.thu70.models.LogReg.operating_point.recall")
for sid in ("wed70", "thu70"):
    for m in MODELS:
        br = SPL[sid]["models"][m]["budget_recall"]
        for b in ("1000", "10000"):
            reg(f"br_{sid}_{MK[m]}_{b}", br[b], "pct1", f"{F1}#splits.{sid}.models.{m}.budget_recall.{b}")
reg("br_budget_hi", 10000, "int", f"{F1}#splits.*.models.*.budget_recall (keys: 100 / 1,000 / 10,000 FA/day)")
reg("rf_rec_unseen_pct", SPL["wed70"]["models"]["RandomForest"]["recall"], "pct2", f"{F1}#splits.wed70.models.RandomForest.recall")
# fraction of unseen-SSH test flows the three models miss
derived("w70_unseen_miss", 1 - SPL["wed70"]["models"]["LogReg"]["recall"], "pct2", "1 - recall (identical for all three models)", ["t3_wed70_lr_recall"])
assert len({SPL["wed70"]["models"][m]["tp"] for m in MODELS}) == 1
# clean timings
for k, v in TIM.items():
    a, b = k.split("|")
    reg(f"tim_{a}_{MK[b]}", v["train_s"], "int", f"results/task1_timing.json#{k}.train_s")

# Task 1 random split, unrepaired clock, Table 4
RS = T1["random_split"]; UC = T1["unrepaired_clock"]
T4 = {}
for day, sid in (("wed", "wed80"), ("thu", "thu70")):
    for m in MODELS:
        T4[(day, "rand", MK[m])] = RS[day][m]["f1"]
        T4[(day, "time", MK[m])] = SPL[sid]["models"][m]["f1"]
T4DIG = {day: fdig([T4[(day, k, MK[m])] for k in ("rand", "time") for m in MODELS], 3, 5) for day in DAYS}
for (day, k, m), v in T4.items():
    src = f"{F1}#random_split.{day}.{ {'lr':'LogReg','rf':'RandomForest','mlp':'MLP'}[m] }.f1" if k == "rand" else f"{F1}#splits.{'wed80' if day=='wed' else 'thu70'}.models.{ {'lr':'LogReg','rf':'RandomForest','mlp':'MLP'}[m] }.f1"
    reg(f"t4_{day}_{k}_{m}", v, "raw", src, text=metric_text(v, T4DIG[day]))
for day in DAYS:
    v = UC[day]["f1"]
    reg(f"t4_{day}_unrep_rf", v, "raw", f"{F1}#unrepaired_clock.{day}.f1", text=metric_text(v, T4DIG[day]))
sid_t = "thu70"
for m, name in (("lr", "LogReg"), ("rf", "RandomForest"), ("mlp", "MLP")):
    lo, hi = SPL[sid_t]["models"][name]["f1_ci"]
    reg(f"t4_thu_ci_{m}_lo", lo, "f3", f"{F1}#splits.thu70.models.{name}.f1_ci[0]")
    reg(f"t4_thu_ci_{m}_hi", hi, "f3", f"{F1}#splits.thu70.models.{name}.f1_ci[1]")
    d_ = T4[("thu", "rand", m)] - T4[("thu", "time", m)]
    derived(f"t4_thu_delta_{m}", d_, "f3", "random-split F1 - time-split F1 (Thu)", [f"t4_thu_rand_{m}", f"t4_thu_time_{m}"])
    assert lo <= T4[("thu", "rand", m)] <= hi, f"random F1 outside time-split CI for {m}"
    d2 = T4[("wed", "rand", m)] - T4[("wed", "time", m)]
    derived(f"t4_wed_delta_{m}", abs(d2), "f4", "|random-split F1 - time-split F1| (Wed 80%)", [f"t4_wed_rand_{m}", f"t4_wed_time_{m}"])
assert max(val(f"t4_wed_delta_{m}") for m in ("lr", "rf", "mlp")) == val("t4_wed_delta_lr")
assert UC["thu"]["f1"] > SPL["thu70"]["models"]["RandomForest"]["f1_ci"][1], "unrepaired Thu RF F1 must lie outside the CI"
reg("t4_wed70_rf", SPL["wed70"]["models"]["RandomForest"]["f1"], "f4", f"{F1}#splits.wed70.models.RandomForest.f1")
# unrepaired-clock windows
reg("uc_wed_train_a", hhmm(UC["wed"]["train_raw_clock"][0]), "raw", f"{F1}#unrepaired_clock.wed.train_raw_clock[0]", text=hhmm(UC["wed"]["train_raw_clock"][0]))
reg("uc_wed_train_b", hhmm(UC["wed"]["train_raw_clock"][1]), "raw", f"{F1}#unrepaired_clock.wed.train_raw_clock[1]", text=hhmm(UC["wed"]["train_raw_clock"][1]))
reg("uc_wed_test_b", hhmm(UC["wed"]["test_raw_clock"][1]), "raw", f"{F1}#unrepaired_clock.wed.test_raw_clock[1]", text=hhmm(UC["wed"]["test_raw_clock"][1]))

# ----------------------------------------------------------------------------- Task 2
t2s = "results/task2_{d}.json"
reg("t2_n", T2["wed"]["n_sample"], "int", "results/task2_wed.json#n_sample")
assert T2["wed"]["n_sample"] == T2["thu"]["n_sample"]
reg("t2_npca", T2["wed"]["n_pca"], "int", "results/task2_wed.json#n_pca")
reg("t2_triage", T2["wed"]["triage_n"], "int", "results/task2_wed.json#triage_n")
reg("t2_sil", T2["wed"]["silhouette_subsample"], "int", "results/task2_wed.json#silhouette_subsample")
reg("t2_cap", T2["wed"]["capture_hours_assumed"], "int", "results/task2_wed.json#capture_hours_assumed")
for d in DAYS:
    t = T2[d]; s_ = t2s.format(d=d)
    reg(f"t2_{d}_step", t["sample_step"], "int", f"{s_}#sample_step")
    reg(f"t2_{d}_span", t["span_hours_measured"], "hours1", f"{s_}#span_hours_measured")
    reg(f"t2_{d}_attack", t["sample_attack"], "int", f"{s_}#sample_attack")
    reg(f"t2_{d}_benignsample", t["found_missed"]["counts"]["benign"], "int", f"{s_}#found_missed.counts.benign")
    reg(f"t2_{d}_pca95", t["pca_k95"], "int", f"{s_}#pca_k95")
    reg(f"t2_{d}_km_k", t["kmeans"]["k"], "int", f"{s_}#kmeans.k")
    reg(f"t2_{d}_gmm_k", t["gmm"]["components"], "int", f"{s_}#gmm.components")
    reg(f"t2_{d}_gmm_cov", t["gmm"]["cov"], "raw", f"{s_}#gmm.cov")
    reg(f"t2_{d}_gmm_max", t["gmm"]["grid_max"], "int", f"{s_}#gmm.grid_max")
    reg(f"t2_{d}_db_eps", t["dbscan"]["eps"], "f3", f"{s_}#dbscan.eps")
    reg(f"t2_{d}_db_ms", t["dbscan"]["min_samples"], "int", f"{s_}#dbscan.min_samples")
    reg(f"t2_{d}_db_ncl", t["dbscan"]["n_clusters"], "int", f"{s_}#dbscan.n_clusters")
    reg(f"t2_{d}_db_noise", t["dbscan"]["noise"], "pct0", f"{s_}#dbscan.noise")
    reg(f"t2_{d}_db_valid", t["dbscan"]["n_valid_settings"], "int", f"{s_}#dbscan.n_valid_settings")
    reg(f"t2_{d}_db_all", t["dbscan"]["n_settings"], "int", f"{s_}#dbscan.n_settings")
    reg(f"t2_{d}_db_fmin", t["dbscan"]["f1_min_all"], "f3", f"{s_}#dbscan.f1_min_all")
    reg(f"t2_{d}_db_fmax", t["dbscan"]["f1_max_all"], "f3", f"{s_}#dbscan.f1_max_all")
    reg(f"t2_{d}_ext_sil0", MS[d]["old_best_sil"], "f3", f"results/task2_dbscan_ms_check_{d}.json#old_best_sil")
    reg(f"t2_{d}_ext_sil1", MS[d]["ext_best_sil"], "f3", f"results/task2_dbscan_ms_check_{d}.json#ext_best_sil")
    reg(f"t2_{d}_ext_ms", MS[d]["ext_best_ms"], "int", f"results/task2_dbscan_ms_check_{d}.json#ext_best_ms")
    reg(f"t2_{d}_ext_f0", MS[d]["old_best_f1"], "f3", f"results/task2_dbscan_ms_check_{d}.json#old_best_f1")
    reg(f"t2_{d}_ext_f1", MS[d]["ext_best_f1"], "f3", f"results/task2_dbscan_ms_check_{d}.json#ext_best_f1")
    reg(f"t2_{d}_km_sil", t["kmeans"]["silhouette"], "f3", f"{s_}#kmeans.silhouette")
    # measured-span convention
    conv = f"fa_day_reported x {t['capture_hours_assumed']} / span_hours_measured"
    for a in ALGOS:
        f_ = t["final"][a]
        reg(f"t2_{d}_{a}_labels", f_["labels_used"], "int", f"{s_}#final.{a}.labels_used")
        reg(f"t2_{d}_{a}_seeds", f_["n_seeds"], "int", f"{s_}#final.{a}.n_seeds")
        reg(f"t2_{d}_{a}_fa_rep", f_["fa_day"], "int", f"{s_}#final.{a}.fa_day (12 h convention, reported only for the change log)")
        derived(f"t2_{d}_{a}_fa", f_["fa_day"] * t["capture_hours_assumed"] / t["span_hours_measured"], "int", conv, [f"t2_{d}_{a}_fa_rep", f"t2_{d}_span", "t2_cap"])
    for rname in (("port", "sample"), ("port", "full_day"), ("payload", "sample"), ("payload", "full_day")):
        if rname[0] not in t["rules"]: continue
        r_ = t["rules"][rname[0]][rname[1]]
        reg(f"t2_{d}_{rname[0]}_{rname[1]}_fa_rep", r_["fa_day"], "int", f"{s_}#rules.{rname[0]}.{rname[1]}.fa_day (12 h convention)")
        derived(f"t2_{d}_{rname[0]}_{rname[1]}_fa", r_["fa_day"] * t["capture_hours_assumed"] / t["span_hours_measured"], "int", conv,
                [f"t2_{d}_{rname[0]}_{rname[1]}_fa_rep", f"t2_{d}_span", "t2_cap"])

# Wednesday payload rule on the sample: derived from rules_on_groups
fm = T2["wed"]["found_missed"]
tp = fm["rules_on_groups"]["all_attack"]["payload_rule"]; fp_ = fm["rules_on_groups"]["benign"]["payload_rule"]
n_att = fm["counts"]["all_attack"]; n_ben = fm["counts"]["benign"]
wp = dict(tp=tp, fp=fp_, fn=n_att - tp, precision=tp / (tp + fp_), recall=tp / n_att)
wp["f1"] = 2 * wp["precision"] * wp["recall"] / (wp["precision"] + wp["recall"])
wp["fa_rep"] = fp_ / n_ben * T2["wed"]["benign_day"] * 24 / T2["wed"]["capture_hours_assumed"]
WP_SRC = "results/task2_wed.json#found_missed.rules_on_groups.{all_attack,benign}.payload_rule, counts"
reg("t2_wed_payload_sample_fa_rep", wp["fa_rep"], "int", f"derived: FP / benign sample x benign_day x 24 / 12 from {WP_SRC}, task2_wed.json#benign_day")
derived("t2_wed_payload_sample_fa", wp["fa_rep"] * 12 / T2["wed"]["span_hours_measured"], "int", "fa_day_reported x 12 / span_hours_measured", ["t2_wed_payload_sample_fa_rep", "t2_wed_span", "t2_cap"])

# Table 5 rows: digits per day for precision / recall / f1
T2ROWS = {}
for d in DAYS:
    t = T2[d]
    for a in ALGOS:
        f_ = t["final"][a]
        T2ROWS[(d, a)] = dict(precision=f_["precision"], recall=f_["recall"], f1=f_["f1"], f1_min=f_["f1_min"], f1_max=f_["f1_max"], src=f"results/task2_{d}.json#final.{a}")
    pr = t["rules"]["port"]["sample"]
    T2ROWS[(d, "port")] = dict(precision=pr["precision"], recall=pr["recall"], f1=pr["f1"], f1_min=None, f1_max=None, src=f"results/task2_{d}.json#rules.port.sample")
    if d == "thu":
        pl = t["rules"]["payload"]["sample"]
        T2ROWS[(d, "payload")] = dict(precision=pl["precision"], recall=pl["recall"], f1=pl["f1"], f1_min=None, f1_max=None, src=f"results/task2_{d}.json#rules.payload.sample")
    else:
        T2ROWS[(d, "payload")] = dict(precision=wp["precision"], recall=wp["recall"], f1=wp["f1"], f1_min=None, f1_max=None, src="derived from " + WP_SRC)
for d in DAYS:
    whos = [w for (dd, w) in T2ROWS if dd == d]
    dig = fdig([T2ROWS[(d, w)][c] for w in whos for c in ("precision", "recall", "f1")] + [T2ROWS[(d, w)][c] for w in whos for c in ("f1_min", "f1_max") if T2ROWS[(d, w)][c] is not None], 3, 4)
    for w in whos:
        r = T2ROWS[(d, w)]
        for c in ("precision", "recall", "f1", "f1_min", "f1_max"):
            if r[c] is None: continue
            reg(f"t5_{d}_{w}_{c}", r[c], "raw", f"{r['src']}.{c}", text=metric_text(r[c], dig))
# Table 5: payload rule labels 0
reg("t5_zero_labels", 0, "int", "results/task2_{wed,thu}.json#rules.*.sample.labels_used (rules need no labels)")

# Stability (Table 6)
def sweep_range(d, a, sweep):
    S = SW[d]; q = S[(S.algo == a) & (S.sweep == sweep)].groupby(S.value.astype(str))["f1"].mean()
    return float(q.min()), float(q.max())


STAB = {}
for d in DAYS:
    t = T2[d]
    local = {"kmeans": t["kmeans"]["stability_f1_pm1"], "gmm": t["gmm"]["stability_f1_pm1"],
             "dbscan": t["dbscan"]["stability_f1_neighbours"] + [t["final"]["dbscan"]["f1"]]}
    for a in ALGOS:
        row = {"local": (min(local[a]), max(local[a]))}
        for sw in ("pca_dims", "sample_size", "triage_n", "analyst_error"):
            row[sw] = sweep_range(d, a, sw)
        STAB[(d, a)] = row
        dg = 4 if min(v[0] for v in row.values()) > 0.9 else 3
        for sw, (lo, hi) in row.items():
            srcs = f"results/task2_{d}.json#{a}.stability" if sw == "local" else f"results/task2_extra_sweeps_{d}.csv ({sw}, seed-mean min-max)"
            tl, th = f"{lo:.{dg}f}", f"{hi:.{dg}f}"
            reg(f"t6_{d}_{a}_{sw}_lo", lo, "raw", srcs, text=tl)
            if th != tl: reg(f"t6_{d}_{a}_{sw}_hi", hi, "raw", srcs, text=th)
            else: REGISTRY[f"t6_{d}_{a}_{sw}_hi"] = REGISTRY[f"t6_{d}_{a}_{sw}_lo"]
            reg(f"t6_{d}_{a}_{sw}_span", hi - lo, "f3", f"derived: max - min of {srcs}")
STAB_MAXERR = max(abs(hi - lo) for k, v in STAB.items() for sw, (lo, hi) in [("analyst_error", v["analyst_error"])])
_km = [v for sw, v in STAB[("thu", "kmeans")].items() if sw in ("pca_dims", "sample_size", "triage_n")]
derived("km_thu_lo", min(a for a, b in _km), "f3", "min over PCA, sample-size and triage sweeps of Thursday K-Means seed-mean F1", ["results/task2_extra_sweeps_thu.csv"])
derived("km_thu_hi", max(b for a, b in _km), "f3", "max over PCA, sample-size and triage sweeps of Thursday K-Means seed-mean F1", ["results/task2_extra_sweeps_thu.csv"])
derived("sw_err_max", STAB_MAXERR, "f3", "max over days and algorithms of (max - min F1 over analyst error 0-10%)", ["results/task2_extra_sweeps_*.csv"])
# which sweep moves F1 most
for d in DAYS:
    for a in ALGOS:
        sp = {sw: STAB[(d, a)][sw][1] - STAB[(d, a)][sw][0] for sw in ("pca_dims", "sample_size", "triage_n", "analyst_error")}
        STAB[(d, a)]["argmax"] = max(sp, key=sp.get)
assert STAB[("thu", "kmeans")]["argmax"] == "triage_n" and STAB[("thu", "dbscan")]["argmax"] == "pca_dims" and STAB[("thu", "gmm")]["argmax"] == "sample_size", {k: v["argmax"] for k, v in STAB.items()}
assert STAB[("wed", "dbscan")]["argmax"] in ("sample_size", "pca_dims")
# Thursday detector spread
tf = [T2["thu"]["final"][a]["f1"] for a in ALGOS]
reg("thu_spread", max(tf) - min(tf), "f3", "derived: max - min of results/task2_thu.json#final.*.f1")
seed_lo = max(T2["thu"]["final"][a]["f1_min"] for a in ALGOS); seed_hi = min(T2["thu"]["final"][a]["f1_max"] for a in ALGOS)
assert seed_lo < seed_hi, "Thursday seed ranges must overlap for the text"
reg("thu_overlap_lo", seed_lo, "f3", "derived: max over detectors of results/task2_thu.json#final.*.f1_min")
reg("thu_overlap_hi", seed_hi, "f3", "derived: min over detectors of results/task2_thu.json#final.*.f1_max")
# grid sizes and sweep value lists
kmg = T2["wed"]["kmeans"]["grid"]
reg("g2_k_lo", kmg[0], "int", "results/task2_wed.json#kmeans.grid[0]"); reg("g2_k_hi", kmg[-1], "int", "results/task2_wed.json#kmeans.grid[-1]")
reg("g2_km_seeds", len(T2["wed"]["kmeans"]["seeds"]), "int", "results/task2_wed.json#kmeans.seeds (length)")
reg("g2_gmm_lo", T2["thu"]["gmm"]["grid"][0], "int", "results/task2_thu.json#gmm.grid[0]")
reg("g2_gmm_thu_hi", T2["thu"]["gmm"]["grid_max"], "int", "results/task2_thu.json#gmm.grid_max")
reg("g2_gmm_wed_hi", T2["wed"]["gmm"]["grid_max"], "int", "results/task2_wed.json#gmm.grid_max")
reg("g2_eps_n", len(T2["wed"]["dbscan"]["eps_grid"]), "int", "results/task2_wed.json#dbscan.eps_grid (length)")
ms_vals = sorted(int(float(x)) for x in GR["wed"][GR["wed"].algo == "dbscan"].aux.unique())
for i, v in enumerate(ms_vals): reg(f"g2_ms{i}", v, "int", "results/task2_grid_wed.csv (dbscan aux = min_samples)")
reg("g2_ms_n", len(ms_vals), "int", "results/task2_grid_wed.csv (number of min_samples values)")
reg("g2_noise_cap", 0.25, "pct0", "src/lab1/task2.py#NOISE_CAP (25% noise cap for silhouette-valid DBSCAN settings)")
sv = SW["wed"]
for sw in ("pca_dims", "sample_size", "triage_n", "analyst_error"):
    vals = sorted({float(str(x)) for x in sv[(sv.sweep == sw)].value if not str(x).endswith("*")})
    for i, v in enumerate(vals):
        if sw == "analyst_error": reg(f"sw_{sw}_{i}", v, "pct0", f"results/task2_extra_sweeps_wed.csv ({sw} values)")
        else: reg(f"sw_{sw}_{i}", v, "int", f"results/task2_extra_sweeps_wed.csv ({sw} values)")
reg("sw_seeds", SW["wed"][(SW["wed"].algo == "gmm") & (SW["wed"].sweep == "triage_n")].seed.nunique(), "int", "results/task2_extra_sweeps_wed.csv (seeds per sweep point)")
reg("t2_gmm_seeds", T2["wed"]["final"]["gmm"]["n_seeds"], "int", "results/task2_wed.json#final.gmm.n_seeds")
reg("t2_km_seeds", T2["wed"]["final"]["kmeans"]["n_seeds"], "int", "results/task2_wed.json#final.kmeans.n_seeds")
reg("t2_db_seeds", T2["wed"]["final"]["dbscan"]["n_seeds"], "int", "results/task2_wed.json#final.dbscan.n_seeds")
reg("t2_plot", 5000, "int", "src/lab1/task2.py (figure data: rng.choice(len(Z), 5000), first two PCA components); plotted by src/lab1/figures.py fig4")
reg("epoch", 1970, "raw", "results/prep_{wed,thu}.json#rows_1970 (the year of the invalid timestamps)")
reg("port_21", 21, "raw", "src/lab1/rules.py#port_rule (FTP port)")
reg("port_22", 22, "raw", "src/lab1/rules.py#port_rule (SSH port)")
reg("pl_dur", 1000, "int", "src/lab1/rules.py#payload_rule max_dur_us (duration limit in microseconds)")

# Table 7: found vs missed, Thursday
FMT_ = T2["thu"]["found_missed"]; CNT = FMT_["counts"]; MED = FMT_["medians"]; RG = FMT_["rules_on_groups"]; OC = FMT_["ordinary_checks"]
fsrc = "results/task2_thu.json#found_missed"
GROUPS = [("benign", "benign"), ("found_any", "found"), ("only_kmeans", "onlykm"), ("only_gmm", "onlygmm"), ("only_dbscan", "onlydb"), ("missed_all", "missed"), ("all_attack", "allatk")]
for g, gk in GROUPS:
    reg(f"t7_{gk}_n", CNT[g], "int", f"{fsrc}.counts.{g}")
    reg(f"t7_{gk}_dur", MED[g]["Flow Duration"], "int", f"{fsrc}.medians.{g}.Flow Duration")
    reg(f"t7_{gk}_fwd", MED[g]["TotLen Fwd Pkts"], "int", f"{fsrc}.medians.{g}.TotLen Fwd Pkts")
    reg(f"t7_{gk}_bwd", MED[g]["TotLen Bwd Pkts"], "int", f"{fsrc}.medians.{g}.TotLen Bwd Pkts")
    pps = MED[g]["Flow Pkts/s"]
    reg(f"t7_{gk}_pps", pps, "raw", f"{fsrc}.medians.{g}.Flow Pkts/s", text=f"{pps:,.0f}" if pps >= 10 else f"{pps:.1f}")
    reg(f"t7_{gk}_win", MED[g]["Init Fwd Win Byts"], "int", f"{fsrc}.medians.{g}.Init Fwd Win Byts")
    for rule, rk in (("payload_rule", "pay"), ("port_rule", "port")):
        reg(f"t7_{gk}_{rk}", RG[g][rule], "int", f"{fsrc}.rules_on_groups.{g}.{rule}")
        derived(f"t7_{gk}_{rk}_pct", RG[g][rule] / CNT[g], "pct0", f"rules_on_groups.{g}.{rule} / counts.{g}", [f"t7_{gk}_{rk}", f"t7_{gk}_n"])
    if g in OC and "dup_of_benign" in OC[g]:
        derived(f"t7_{gk}_dup", OC[g]["dup_of_benign"] / OC[g]["n"], "pct0", "ordinary_checks.dup_of_benign / n", [f"{fsrc}.ordinary_checks.{g}"])
        derived(f"t7_{gk}_nn", OC[g]["mostly_benign_nn"] / OC[g]["n"], "pct0", "ordinary_checks.mostly_benign_nn / n", [f"{fsrc}.ordinary_checks.{g}"])
derived("t7_found_pay_share", RG["found_any"]["payload_rule"] / CNT["found_any"], "pct0", "payload-rule catches / found_any", ["t7_found_pay", "t7_found_n"])
derived("t7_missed_share", CNT["missed_all"] / CNT["all_attack"], "pct0", "missed_all / all_attack", ["t7_missed_n", "t7_allatk_n"])
derived("t7_found_share", CNT["found_any"] / CNT["all_attack"], "pct0", "found_any / all_attack", ["t7_found_n", "t7_allatk_n"])
for p_, k_ in (("53", "p53"), ("443", "p443"), ("3389", "p3389")):
    reg(f"port_{k_}", int(p_), "raw", f"{fsrc}.top_ports_missed_share (port number)", text=p_)
    reg(f"port_{k_}_share", FMT_["top_ports_missed_share"][p_], "pct0", f"{fsrc}.top_ports_missed_share.{p_}")
reg("t7_nnk", FMT_["nn_k"], "int", f"{fsrc}.nn_k")
reg("t7_nnhalf", 5, "int", f"{fsrc}.nn_rule (more than 5 of 10 neighbours benign)")
for k_ in ("kmeans", "gmm", "dbscan"):
    reg(f"t7_by_{k_}", FMT_["found_by_detector"][k_], "int", f"{fsrc}.found_by_detector.{k_}")
reg("wed_found_n", T2["wed"]["found_missed"]["counts"]["found_any"], "int", "results/task2_wed.json#found_missed.counts.found_any")
reg("wed_missed_n", T2["wed"]["found_missed"]["counts"]["missed_all"], "int", "results/task2_wed.json#found_missed.counts.missed_all")
wm = T2["wed"]["found_missed"]["medians"]
reg("w_med_pps_att", wm["found_any"]["Flow Pkts/s"], "int", "results/task2_wed.json#found_missed.medians.found_any.Flow Pkts/s")
reg("w_med_win_att", wm["found_any"]["Init Fwd Win Byts"], "int", "results/task2_wed.json#found_missed.medians.found_any.Init Fwd Win Byts")
reg("w_med_pps_ben", wm["benign"]["Flow Pkts/s"], "int", "results/task2_wed.json#found_missed.medians.benign.Flow Pkts/s")
reg("w_med_win_ben", wm["benign"]["Init Fwd Win Byts"], "int", "results/task2_wed.json#found_missed.medians.benign.Init Fwd Win Byts")
# full-day payload rule on Thursday
pf = T2["thu"]["rules"]["payload"]["full_day"]
reg("thu_pay_fd_f1", pf["f1"], "f3", "results/task2_thu.json#rules.payload.full_day.f1")
reg("thu_pay_fd_rec", pf["recall"], "pct0", "results/task2_thu.json#rules.payload.full_day.recall")
reg("thu_pay_fd_prec", pf["precision"], "f3", "results/task2_thu.json#rules.payload.full_day.precision")
derived("thu_best_det_f1", max(tf), "f3", "max of results/task2_thu.json#final.*.f1", ["results/task2_thu.json#final"])
# Thursday dist ranks
reg("thu_km_f1", T2["thu"]["final"]["kmeans"]["f1"], "f3", "results/task2_thu.json#final.kmeans.f1")
reg("thu_gmm_f1", T2["thu"]["final"]["gmm"]["f1"], "f3", "results/task2_thu.json#final.gmm.f1")
reg("thu_db_f1", T2["thu"]["final"]["dbscan"]["f1"], "f3", "results/task2_thu.json#final.dbscan.f1")
reg("wed_db_f1_4", T2["wed"]["final"]["dbscan"]["f1"], "f4", "results/task2_wed.json#final.dbscan.f1")
reg("wed_gmm_f1_4", T2["wed"]["final"]["gmm"]["f1"], "f4", "results/task2_wed.json#final.gmm.f1")
reg("wed_km_f1_3", T2["wed"]["final"]["kmeans"]["f1"], "f3", "results/task2_wed.json#final.kmeans.f1")
reg("wed_port_f1_4", T2["wed"]["rules"]["port"]["sample"]["f1"], "f4", "results/task2_wed.json#rules.port.sample.f1")
reg("thu_port_f1_3", T2["thu"]["rules"]["port"]["sample"]["f1"], "f3", "results/task2_thu.json#rules.port.sample.f1")
reg("thu_port_rec_fd", T2["thu"]["rules"]["port"]["full_day"]["recall"], "pct1", "results/task2_thu.json#rules.port.full_day.recall")
reg("thu_port_rec_t1", SPL["thu70"]["port_rule"]["recall"], "pct1", f"{F1}#splits.thu70.port_rule.recall")

# Table 8 helpers: ranges across the Task 1 windows
fa_port = [SPL[s]["port_rule"]["fa"]["value"] for s in ("wed70", "wed80")]
derived("t8_port_lo", min(fa_port), "int", "min of port-rule FA/day on Wed 70% and Wed 80%", ["t3_wed70_port_fa", "t3_wed80_port_fa"])
derived("t8_port_hi", max(fa_port), "int", "max of port-rule FA/day on Wed 70% and Wed 80%", ["t3_wed70_port_fa", "t3_wed80_port_fa"])
fa_lab = [T2["wed"]["final"][a]["labels_used"] for a in ("gmm", "dbscan")] + [T2["thu"]["final"][a]["labels_used"] for a in ("gmm", "dbscan")]
derived("t8_lab_lo", min(fa_lab), "int", "min analyst labels of GMM and DBSCAN over both days", ["t2_wed_dbscan_labels", "t2_thu_dbscan_labels", "t2_wed_gmm_labels", "t2_thu_gmm_labels"])
derived("t8_lab_hi", max(fa_lab), "int", "max analyst labels of GMM and DBSCAN over both days", ["t2_wed_dbscan_labels", "t2_thu_dbscan_labels", "t2_wed_gmm_labels", "t2_thu_gmm_labels"])
db_fa = [val("t2_wed_dbscan_fa"), val("t2_thu_dbscan_fa")]
derived("t8_dbfa_lo", min(db_fa), "int", "min of DBSCAN FA/day (measured span) Wed, Thu", ["t2_wed_dbscan_fa", "t2_thu_dbscan_fa"])
derived("t8_dbfa_hi", max(db_fa), "int", "max of DBSCAN FA/day (measured span) Wed, Thu", ["t2_wed_dbscan_fa", "t2_thu_dbscan_fa"])
gm_fa = [val("t2_wed_gmm_fa"), val("t2_thu_gmm_fa")]
derived("t8_gmfa_lo", min(gm_fa), "int", "min of GMM FA/day (measured span) Wed, Thu", ["t2_wed_gmm_fa", "t2_thu_gmm_fa"])
derived("t8_gmfa_hi", max(gm_fa), "int", "max of GMM FA/day (measured span) Wed, Thu", ["t2_wed_gmm_fa", "t2_thu_gmm_fa"])
derived("t8_rf_x_rule", val("t3_wed80_port_fa") - val("t3_wed80_rf_fa"), "int", "port-rule FA/day - RF FA/day on Wed 80%", ["t3_wed80_port_fa", "t3_wed80_rf_fa"])
derived("t8_km_wed_fa_x", val("t2_wed_kmeans_fa") / val("t2_wed_dbscan_fa"), "int", "K-Means FA/day / DBSCAN FA/day on Wed (measured span)", ["t2_wed_kmeans_fa", "t2_wed_dbscan_fa"])
derived("t8_thu_pay_fa", val("t2_thu_payload_full_day_fa"), "int", "payload rule full-day FA/day (measured span)", ["t2_thu_payload_full_day_fa"])
derived("t8_thu_pay_hours", val("t2_thu_payload_full_day_fa") * val("c_min") / val("c_minpermin"), "int", "FA/day x 1 min / 60", ["t2_thu_payload_full_day_fa", "c_min", "c_minpermin"])

# DBSCAN Wed edge facts
reg("wed_gmm_bic_edge", T2["wed"]["gmm"]["bic_min_at_grid_max"], "raw", "results/task2_wed.json#gmm.bic_min_at_grid_max", text=str(T2["wed"]["gmm"]["bic_min_at_grid_max"]))
assert T2["wed"]["gmm"]["bic_min_at_grid_max"] and T2["wed"]["dbscan"]["ms_edge"]["at_upper_edge"] and T2["thu"]["dbscan"]["ms_edge"]["at_upper_edge"]
assert not T2["thu"]["gmm"]["edge"]["at_upper_edge"] and not T2["wed"]["kmeans"]["edge"]["at_upper_edge"]

# ----------------------------------------------------------------------------- table row structures
def cellmaker(*parts):
    return list(parts)


def n(key):
    return R(key)


def bold_flags(rows, col, best="max"):
    vals = [r[col] for r in rows]
    tgt = max(vals) if best == "max" else min(vals)
    return [v == tgt for v in vals]


# Table 1 --------------------------------------------------------------
def t1rows():
    rows = []
    def add(label, kk):
        rows.append(dict(label=label, wed=[n(f"p_wed_{kk}")], thu=[n(f"p_thu_{kk}")]))
    add("Rows in file", "rows")
    rows.append(dict(label=["Removed: repeated header lines / rows dated ", n("epoch"), " / rows with ±Infinity"],
                     wed=[n("p_wed_hdr"), " / ", n("p_wed_r1970"), " / ", n("p_wed_inf")], thu=[n("p_thu_hdr"), " / ", n("p_thu_r1970"), " / ", n("p_thu_inf")]))
    add("Rows kept", "kept")
    rows.append(dict(label="Constant columns dropped / features used",
                     wed=[n("p_wed_nconst"), " / ", n("p_wed_nfeat")], thu=[n("p_thu_nconst"), " / ", n("p_thu_nfeat")]))
    add("Duplicate rows (counted, kept)", "dups")
    rows.append(dict(label="Attack flows (share of rows kept)", wed=[n("p_wed_lab_ftp"), " FTP + ", n("p_wed_lab_ssh"), " SSH (", n("p_wed_share"), ")"],
                     thu=[n("p_thu_lab_infilteration"), " Infiltration (", n("p_thu_share"), ")"]))
    return rows


# Table 2 --------------------------------------------------------------
def t2rows():
    rows = []
    rows.append(dict(split=[n("sp_wed70")], cut=[n("t1_wed70_cut")], train=[n("t1_wed70_train_ftp"), " FTP"], test=[n("t1_wed70_test_ssh"), " SSH (unseen)"], hours=[n("t1_wed70_hours")], val=[n("t1_wed70_valatk"), " FTP"]))
    rows.append(dict(split=[n("sp_wed80")], cut=[n("t1_wed80_cut")], train=[n("t1_wed80_train_ftp"), " FTP + ", n("t1_wed80_train_ssh"), " SSH"], test=[n("t1_wed80_test_ssh"), " SSH (seen)"], hours=[n("t1_wed80_hours")], val=[n("t1_wed80_valatk"), " SSH (not in fit part)"]))
    rows.append(dict(split=[n("sp_thu70")], cut=[n("t1_thu70_cut")], train=[n("t1_thu70_train_infilteration"), " Infilteration"], test=[n("t1_thu70_test_infilteration"), " Infilteration"], hours=[n("t1_thu70_hours")], val=[n("t1_thu70_valatk"), " Infilteration"]))
    return rows


# Table 3 --------------------------------------------------------------
WHO_LABEL = {"lr": "LogReg", "rf": "RF", "mlp": "MLP", "port": "Port 21/22 rule", "pay": "Zero-payload rule"}


def t3groups():
    groups = []
    for sid in SIDS:
        whos = [w for (g, w) in T1ROWS if g == sid]
        f1s = {w: T1ROWS[(sid, w)]["f1"] for w in whos}; fas = {w: T1ROWS[(sid, w)]["fa"] for w in whos}
        best_f1 = max(f1s.values()); best_fa = min(fas.values())
        rows = []
        for w in whos:
            k = f"t3_{sid}_{w}_"
            r = T1ROWS[(sid, w)]
            f1cell = [n(k + "f1")]
            cicell = ["[", n(k + "f1_lo"), ", ", n(k + "f1_hi"), "]"] if r["f1_lo"] is not None else ["–"]
            rows.append(dict(model=WHO_LABEL[w], rule=w in ("port", "pay"),
                             prec=[n(k + "precision")], rec=[n(k + "recall")], f1=f1cell, ci=cicell, f1_bold=abs(f1s[w] - best_f1) < 5e-5,
                             ap=[n(k + "ap")] if r["ap"] is not None else ["–"], fp=[n(k + "fp")],
                             fa=[n(k + "fa"), " [", n(k + "fa_lo"), "–", n(k + "fa_hi"), "]"], fa_bold=fas[w] == best_fa))
        groups.append(dict(name=n(f"sp_{sid}"), rows=rows))
    return groups


# Table 4 --------------------------------------------------------------
def t4rows():
    rows = []
    for day, nm, sid in (("wed", "Wed", "wed80"), ("thu", "Thu", "thu70")):
        rows.append(dict(label=[f"{nm}: random split, ", n("frac_wed70"), " train"], cells=[[n(f"t4_{day}_rand_{m}")] for m in ("lr", "rf", "mlp")]))
        rows.append(dict(label=[f"{nm}: honest time split (", n(f"sp_{sid}"), ")"],
                         cells=[[n(f"t4_{day}_time_{m}")] + ([" [", n(f"t4_thu_ci_{m}_lo"), ", ", n(f"t4_thu_ci_{m}_hi"), "]"] if day == "thu" else []) for m in ("lr", "rf", "mlp")]))
        if day == "thu": rows.append(dict(label=[f"{nm}: unrepaired clock, ", n("frac_wed70"), " train"], cells=[["not run"], [n(f"t4_{day}_unrep_rf")], ["not run"]]))
    return rows


# Table 5 --------------------------------------------------------------
ALGO_LABEL = {"kmeans": "K-Means", "gmm": "GMM", "dbscan": "DBSCAN"}


def t5groups():
    groups = []
    for d in DAYS:
        rows = []
        whos = ["kmeans", "gmm", "dbscan", "port", "payload"] if d == "thu" else ["kmeans", "gmm", "dbscan", "port"]
        fas = {}
        for w in whos:
            if w in ALGOS: fas[w] = val(f"t2_{d}_{w}_fa")
            elif w == "port": fas[w] = val(f"t2_{d}_port_sample_fa")
            else: fas[w] = val(f"t2_{d}_payload_sample_fa")
        f1s = {w: T2ROWS[(d, w)]["f1"] for w in whos}
        for w in whos:
            k = f"t5_{d}_{w}_"
            cfg = {"kmeans": ["k ", n(f"t2_{d}_km_k")],
                   "gmm": [n(f"t2_{d}_gmm_k"), f", {T2[d]['gmm']['cov']}"],
                   "dbscan": ["eps ", n(f"t2_{d}_db_eps"), ", ms ", n(f"t2_{d}_db_ms"), ", ", n(f"t2_{d}_db_ncl"), " cl."],
                   "port": [], "payload": []}[w]
            name = {"kmeans": "K-Means", "gmm": "GMM", "dbscan": "DBSCAN", "port": "Port rule", "payload": "Zero-payload rule"}[w]
            edge = {"kmeans": "interior", "gmm": ("upper edge" if T2[d]["gmm"]["edge"]["at_upper_edge"] else "interior"),
                    "dbscan": "ms at edge", "port": "–", "payload": "–"}[w]
            f1cell = [n(k + "f1")]
            seedcell = [n(k + "f1_min"), "–", n(k + "f1_max")] if T2ROWS[(d, w)]["f1_min"] is not None else ["–"]
            labels = [n(f"t2_{d}_{w}_labels")] if w in ALGOS else [n("t5_zero_labels")]
            rows.append(dict(model=name, cfg=cfg, prec=[n(k + "precision")], rec=[n(k + "recall")], f1=f1cell, seed=seedcell, f1_bold=f1s[w] == max(f1s.values()),
                             labels=labels, fa=[n({"kmeans": f"t2_{d}_kmeans_fa", "gmm": f"t2_{d}_gmm_fa", "dbscan": f"t2_{d}_dbscan_fa", "port": f"t2_{d}_port_sample_fa", "payload": f"t2_{d}_payload_sample_fa"}[w])],
                             fa_bold=fas[w] == min(fas.values()), edge=edge))
        groups.append(dict(name={"wed": "Wednesday", "thu": "Thursday"}[d], rows=rows))
    return groups


# Table 6 --------------------------------------------------------------
def t6rows():
    rows = []
    for d in DAYS:
        for a in ALGOS:
            cells = []
            for sw in ("local", "pca_dims", "sample_size", "triage_n", "analyst_error"):
                lo, hi = f"t6_{d}_{a}_{sw}_lo", f"t6_{d}_{a}_{sw}_hi"
                cells.append([n(lo)] if REGISTRY[lo]["text"] == REGISTRY[hi]["text"] else [n(lo), "–", n(hi)])
            rows.append(dict(day={"wed": "Wed", "thu": "Thu"}[d], algo=ALGO_LABEL[a], cells=cells))
    return rows


# Table 7 --------------------------------------------------------------
G7 = [("benign", "benign", "Benign (reference)"), ("found", "found", "Found by any detector"), ("onlykm", "onlykm", "K-Means only"), ("onlygmm", "onlygmm", "GMM only"),
      ("onlydb", "onlydb", "DBSCAN only"), ("missed", "missed", "Missed by all"), ("allatk", "allatk", "All infiltration (sampled)")]


def t7rows():
    rows = []
    for gk, _, label in G7:
        pk = lambda s_: [n(f"t7_{gk}_{s_}"), " (", n(f"t7_{gk}_{s_}_pct"), ")"]
        dup = [n(f"t7_{gk}_dup")] if f"t7_{gk}_dup" in REGISTRY and gk != "benign" else ["–"]
        nn = [n(f"t7_{gk}_nn")] if f"t7_{gk}_nn" in REGISTRY else ["–"]
        rows.append(dict(label=label, n=[n(f"t7_{gk}_n")], dur=[n(f"t7_{gk}_dur")], fwdbwd=[n(f"t7_{gk}_fwd"), " / ", n(f"t7_{gk}_bwd")], pps=[n(f"t7_{gk}_pps")],
                         win=[n(f"t7_{gk}_win")], pay=pk("pay"), port=pk("port"), dup=dup, nn=nn, ref=gk in ("benign", "allatk")))
    return rows


# ----------------------------------------------------------------------------- render
def main():
    from weasyprint import HTML
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(HERE), undefined=jinja2.StrictUndefined, autoescape=True)
    N = {k: v["obj"] for k, v in REGISTRY.items()}
    ctx = dict(n=N, T1=t1rows(), T2=t2rows(), T3=t3groups(), T4=t4rows(), T5=t5groups(), T6=t6rows(), T7=t7rows(), FIG=FIG, ROOT=ROOT)
    html = env.get_template("template.html.j2").render(**ctx)
    html_path = os.path.join(HERE, "SEC635_Lab1_Report.html")
    with open(html_path, "w") as f: f.write(html)
    HTML(filename=html_path).write_pdf(os.path.join(HERE, "SEC635_Lab1_Report.pdf"))
    out = {k: {kk: vv for kk, vv in v.items() if kk != "obj"} for k, v in REGISTRY.items()}
    with open(os.path.join(RES, "report_registry.json"), "w") as f: json.dump(out, f, indent=1, default=str)
    print(f"registry entries: {len(REGISTRY)}; wrote report/SEC635_Lab1_Report.pdf")


if __name__ == "__main__":
    main()
