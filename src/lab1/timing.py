"""Re-time the chosen models on an otherwise idle machine (task1.py times were taken while other jobs ran)."""
from lab1.task1 import *

if __name__ == "__main__":
    R = jload("task1_results.json")["splits"]; out = {}
    for key, frac in (("wed", 0.8), ("thu", 0.7)):
        sid = f"{key}{int(frac*100)}"; df, _ = load_day(key); feats = feats_of(df); i = split_index(df, frac)
        tr, te = df.iloc[:i], df.iloc[i:]; Xtr, ytr, Xte = prep_xy(tr, feats), tr["y"].values, prep_xy(te, feats)
        for m in MODELS:
            _, tt, tp = fit_scores(m, R[sid]["chosen"][m], Xtr, ytr, [Xte]); out[f"{sid}|{m}"] = {"train_s": tt, "predict_s": tp}; print(sid, m, tt, tp, flush=True)
    jdump(out, "task1_timing.json")
