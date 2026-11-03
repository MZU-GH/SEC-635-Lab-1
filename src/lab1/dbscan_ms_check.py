"""Edge check: the chosen DBSCAN min_samples (50) sits at the top of {5,10,25,50}. Extend to 100 and 200 on the same eps grid."""
import sys
from lab1.task2 import *

if __name__ == "__main__":
    key = sys.argv[1]; df, info = load_day(key); feats = feats_of(df); smp = systematic_sample(df, N_SAMPLE); y = smp["y"].values
    Z, _ = embed(smp, feats, N_PCA); sub = np.random.default_rng(SEED).choice(len(Z), SIL_N, replace=False)
    T = jload(f"task2_{key}.json"); egrid = T["dbscan"]["eps_grid"]; out = []
    for ms in (100, 200):
        for e in egrid:
            cl = dbs(Z, e, ms); noise = float((cl == -1).mean())
            sc = sil(Z, cl, sub, ignore_noise=True) if noise <= NOISE_CAP else float("nan")
            pred, used = triage(cl, y, N_TRIAGE, SEED); r = score(pred, y, used, info["benign_flows"])
            out.append(dict(ms=ms, eps=e, sil=sc, noise=noise, n_clusters=len(set(cl) - {-1}), f1=r["f1"], labels=used)); print(key, ms, round(e, 3), sc, r["f1"], flush=True)
    G = pd.read_csv(os.path.join(RES, f"task2_grid_{key}.csv")); g = G[(G.algo == "dbscan") & G.crit.notna()]
    best_old = g.loc[g.crit.idxmax()]; ext = pd.DataFrame(out); ext_ok = ext[ext.sil.notna()]
    best_new = ext_ok.loc[ext_ok.sil.idxmax()] if len(ext_ok) else None
    res = {"old_best_sil": float(best_old.crit), "old_best_ms": int(best_old.aux), "old_best_f1": float(best_old.f1),
           "ext_best_sil": None if best_new is None else float(best_new.sil), "ext_best_ms": None if best_new is None else int(best_new.ms),
           "ext_best_f1": None if best_new is None else float(best_new.f1), "ext_valid": int(len(ext_ok)),
           "ext_improves_silhouette": bool(best_new is not None and best_new.sil > best_old.crit)}
    ext.to_csv(os.path.join(RES, f"task2_dbscan_ms_extension_{key}.csv"), index=False); jdump(res, f"task2_dbscan_ms_check_{key}.json"); print(res)
