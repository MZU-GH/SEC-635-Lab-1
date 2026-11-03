"""Stage 3: supervised experiments -> results/task1_*.json|csv"""
import itertools, sys, warnings
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import average_precision_score, roc_curve
from sklearn.model_selection import train_test_split
from lab1.common import *
from lab1.rules import port_rule, payload_rule
warnings.filterwarnings("ignore")

SPLITS = [("wed", 0.7), ("wed", 0.8), ("thu", 0.7)]
MODELS = ["LogReg", "RandomForest", "MLP"]
DEFAULTS = {"LogReg": {"C": 1.0}, "RandomForest": {"n_estimators": 100, "min_samples_leaf": 2},
            "MLP": {"hidden": (64, 32)}}
GRID = {"LogReg": [{"C": c} for c in (0.1, 1, 10)],
        "RandomForest": [{"n_estimators": n, "min_samples_leaf": l} for n in (50, 100, 200) for l in (1, 2, 5)],
        "MLP": [{"hidden": h} for h in ((32,), (64, 32), (128, 64))]}
TUNE_STEP = 4          # tuning fits use every 4th training row
MIN_ATTACKS = 100
BUDGET = 1000          # false alerts / day for the operating point


def make(name, p):
    if name == "LogReg":
        return LogisticRegression(C=p["C"], class_weight="balanced", max_iter=1000, random_state=SEED)
    if name == "RandomForest":
        return RandomForestClassifier(n_estimators=p["n_estimators"], min_samples_leaf=p["min_samples_leaf"],
                                      class_weight="balanced", n_jobs=4, random_state=SEED)
    return MLPClassifier(hidden_layer_sizes=tuple(p["hidden"]), early_stopping=True, random_state=SEED, max_iter=200)


def prep_xy(df, feats):
    return slog(df[feats].values)


def fit_scores(name, p, Xtr, ytr, Xte_list):
    sc = StandardScaler().fit(Xtr)                         # scaling fitted on training rows only
    m = make(name, p)
    with Timer() as t1: m.fit(sc.transform(Xtr), ytr)
    outs = []
    with Timer() as t2:
        for X in Xte_list: outs.append(m.predict_proba(sc.transform(X))[:, 1])
    return outs, t1.s, t2.s


def budget_recall(y, s, hours, budget):
    fpr, tpr, thr = roc_curve(y, s)
    nb = int((y == 0).sum()); fa = fpr * nb / hours * 24
    ok = fa <= budget
    return float(tpr[ok].max()) if ok.any() else 0.0


def pick_threshold(y, s, hours, budget):
    """lowest threshold whose false alerts/day on this window is <= budget"""
    cand = np.unique(np.quantile(s, np.linspace(0, 1, 4001)))
    best = 1.0000001
    for t in cand:
        fp = int(((y == 0) & (s >= t)).sum())
        if fp / hours * 24 <= budget:
            best = t; break
    return float(best)


def main():
    out = {"splits": {}, "tuning": {}, "random_split": {}, "unrepaired_clock": {}, "config": {
        "block_minutes": BLOCK_MIN, "n_boot": N_BOOT, "tune_step": TUNE_STEP, "min_attacks_for_tuning": MIN_ATTACKS,
        "budget_fa_per_day": BUDGET, "defaults": DEFAULTS, "grid": GRID, "seed": SEED}}
    data = {k: load_day(k)[0] for k in DAYS}
    sens_rows = []; scores_store = {}
    for key, frac in SPLITS:
        sid = f"{key}{int(frac*100)}"; df = data[key]; feats = feats_of(df)
        i = split_index(df, frac); tr, te = df.iloc[:i], df.iloc[i:]
        j = int(len(tr) * 0.8); fit, val = tr.iloc[:j], tr.iloc[j:]
        Xtr, ytr = prep_xy(tr, feats), tr["y"].values
        Xte, yte = prep_xy(te, feats), te["y"].values
        hours = window_hours(te["ts"]); vh = window_hours(val["ts"])
        S = {"cut_time": str(te["ts"].iloc[0]), "train_rows": len(tr), "test_rows": len(te),
             "train_labels": {k: int(v) for k, v in tr["label"].value_counts().items()},
             "test_labels": {k: int(v) for k, v in te["label"].value_counts().items()},
             "test_hours": hours, "test_start": str(te["ts"].min()), "test_end": str(te["ts"].max()),
             "test_attack": int(yte.sum()), "test_benign": int((yte == 0).sum()),
             "val_attack": int(val["y"].sum()), "fit_attack": int(fit["y"].sum()), "val_hours": vh,
             "val_start": str(val["ts"].min()), "val_end": str(val["ts"].max()), "models": {}, "pairs": {}}
        tune = S["val_attack"] >= MIN_ATTACKS and S["fit_attack"] >= MIN_ATTACKS
        S["tuned"] = bool(tune)
        S["tune_reason"] = (f"validation window holds {S['val_attack']} attack flows and the fit part {S['fit_attack']}"
                            + ("" if tune else f"; need >= {MIN_ATTACKS} in both, so defaults kept"))
        preds = {}; scores = {}
        Xfit = prep_xy(fit.iloc[::TUNE_STEP], feats); yfit = fit["y"].values[::TUNE_STEP]
        Xval = prep_xy(val, feats); yval = val["y"].values
        for m in MODELS:
            chosen = dict(DEFAULTS[m]); tun = []
            if tune:
                for p in GRID[m]:
                    (sv,), _, _ = fit_scores(m, p, Xfit, yfit, [Xval])
                    f1 = prf(yval, (sv >= .5).astype(int))["f1"]
                    tun.append({"params": p, "val_f1": f1}); sens_rows.append(dict(split=sid, model=m, **{k: str(v) for k, v in p.items()}, val_f1=f1))
                    print(sid, m, p, round(f1, 4), flush=True)
                best = max(tun, key=lambda r: (round(r["val_f1"], 6), r["params"] == DEFAULTS[m]))
                chosen = dict(best["params"])
                S.setdefault("sensitivity", {})[m] = {"min": min(r["val_f1"] for r in tun), "max": max(r["val_f1"] for r in tun),
                                                      "range": max(r["val_f1"] for r in tun) - min(r["val_f1"] for r in tun)}
            S.setdefault("chosen", {})[m] = chosen
            S.setdefault("differs_from_default", {})[m] = bool(chosen != DEFAULTS[m])
            (ste, ) , tt, tp_ = fit_scores(m, chosen, Xtr, ytr, [Xte])
            pr = (ste >= .5).astype(int); r = prf(yte, pr)
            lo, hi, nb = block_bootstrap_f1(yte, pr, te["ts"])
            r.update(ap=float(average_precision_score(yte, ste)), f1_ci=[lo, hi], n_blocks=nb, train_s=tt, predict_s=tp_,
                     fa=fa_per_day(r["fp"], hours), params=chosen)
            r["budget_recall"] = {str(b): budget_recall(yte, ste, hours, b) for b in (100, 1000, 10000)}
            # operating point chosen on the validation window (fit-part model), applied to the full-train model
            if key == "thu":
                (sv,), _, _ = fit_scores(m, chosen, prep_xy(fit, feats), fit["y"].values, [Xval])
                th = pick_threshold(yval, sv, vh, BUDGET)
                po = (ste >= th).astype(int); rp = prf(yte, po)
                rp["threshold"] = th; rp["fa"] = fa_per_day(rp["fp"], hours)
                rp["val_fa"] = float(((yval == 0) & (sv >= th)).sum() / vh * 24)
                rp["val_recall"] = float(((yval == 1) & (sv >= th)).sum() / max(1, (yval == 1).sum()))
                r["operating_point"] = rp
            S["models"][m] = r; preds[m] = pr; scores[m] = ste
            print(sid, m, {k: r[k] for k in ("precision", "recall", "f1", "ap", "train_s")}, r["fa"]["fp"], flush=True)
        for a, b in itertools.combinations(MODELS, 2):
            S["pairs"][f"{a}|{b}"] = mcnemar(yte, preds[a], preds[b])
        # rules on the same test window
        pr_ = port_rule(te); rr = prf(yte, pr_); rr["fa"] = fa_per_day(rr["fp"], hours); S["port_rule"] = rr
        S["port_rule_vs_RF"] = mcnemar(yte, pr_, preds["RandomForest"])
        S["port_rule_vs_MLP"] = mcnemar(yte, pr_, preds["MLP"])
        pl = payload_rule(te); rl = prf(yte, pl); rl["fa"] = fa_per_day(rl["fp"], hours); S["payload_rule"] = rl
        S["split_ids"] = sid
        out["splits"][sid] = S
        scores_store[sid] = dict(y=yte.astype("int8"), **{m: scores[m].astype("float32") for m in MODELS})
        jdump(out, "task1_results.json")
    np.savez_compressed(os.path.join(INTERIM, "task1_scores.npz"), **{f"{s}__{k}": v for s, d in scores_store.items() for k, v in d.items()})
    pd.DataFrame(sens_rows).to_csv(os.path.join(RES, "task1_sensitivity.csv"), index=False)

    # ---------------- leakage evidence: random stratified 70/30 split (all models, defaults) ----------------
    for key in DAYS:
        df = data[key]; feats = feats_of(df); X = prep_xy(df, feats); y = df["y"].values
        idx = np.arange(len(df)); itr, ite = train_test_split(idx, test_size=0.3, stratify=y, random_state=SEED)
        R = {}
        for m in MODELS:
            p = out["splits"][f"{key}70"]["chosen"][m]          # same settings as the time split of that day
            (s,), tt, _ = fit_scores(m, p, X[itr], y[itr], [X[ite]])
            pr = (s >= .5).astype(int); r = prf(y[ite], pr); r["ap"] = float(average_precision_score(y[ite], s)); r["train_s"] = tt
            R[m] = r; print("random", key, m, r["f1"], flush=True)
        out["random_split"][key] = R; jdump(out, "task1_results.json")
    # ---------------- unrepaired clock demo (RF, 70/30 by the raw timestamp) ----------------
    for key in DAYS:
        df = data[key]; feats = feats_of(df); d2 = df.sort_values("ts_raw", kind="stable")
        i = split_index(d2, 0.7); tr, te = d2.iloc[:i], d2.iloc[i:]
        p = DEFAULTS["RandomForest"]
        (s,), _, _ = fit_scores("RandomForest", p, prep_xy(tr, feats), tr["y"].values, [prep_xy(te, feats)])
        r = prf(te["y"].values, (s >= .5).astype(int))
        r.update(train_labels={k: int(v) for k, v in tr["label"].value_counts().items()},
                 test_labels={k: int(v) for k, v in te["label"].value_counts().items()},
                 train_true_clock=[str(tr["ts"].min()), str(tr["ts"].max())], test_true_clock=[str(te["ts"].min()), str(te["ts"].max())],
                 train_raw_clock=[str(tr["ts_raw"].min()), str(tr["ts_raw"].max())], test_raw_clock=[str(te["ts_raw"].min()), str(te["ts_raw"].max())])
        out["unrepaired_clock"][key] = r; print("unrepaired", key, r["f1"], flush=True)
    jdump(out, "task1_results.json")


if __name__ == "__main__":
    main()
