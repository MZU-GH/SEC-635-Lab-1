"""Stage 4: unsupervised experiments for one day: python -m lab1.task2 wed|thu   (python -m lab1.task2 merge)"""
import sys, warnings
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans, DBSCAN
from sklearn.mixture import GaussianMixture
from sklearn.metrics import silhouette_score
from sklearn.neighbors import NearestNeighbors
from lab1.common import *
from lab1.rules import port_rule, payload_rule
warnings.filterwarnings("ignore")

N_SAMPLE, N_PCA, N_TRIAGE, SIL_N = 40000, 10, 20, 10000
KM_K = list(range(2, 41)); KM_SEEDS = [42, 43, 44, 45, 46]
GMM_COMPS = list(range(2, 21)) + list(range(22, 61, 2)); GMM_EXT_STEP, GMM_MAX = 10, 120
DB_MS = [5, 10, 25, 50]; DB_NEPS = 16; NOISE_CAP = 0.25
SWEEP_SEEDS = [42, 43, 44]
PCA_DIMS = [5, 10, 15, 20, "var95"]; SAMPLE_SIZES = [10000, 20000, 40000, 80000]
TRIAGE_N = [5, 10, 20, 50]; ERR_RATES = [0.0, 0.05, 0.10]


# ------------------------------------------------------------------ embedding
def systematic_sample(df, n):
    step = max(1, len(df) // n)
    return df.iloc[::step].iloc[:n]


def embed(smp, feats, dims):
    X = slog(smp[feats].values)
    X = StandardScaler().fit_transform(X)
    if dims == "var95":
        full = PCA(random_state=SEED).fit(X)
        k = int(np.searchsorted(np.cumsum(full.explained_variance_ratio_), 0.95) + 1)
        return PCA(k, random_state=SEED).fit_transform(X), k
    p = PCA(dims, random_state=SEED); Z = p.fit_transform(X)
    return Z, int(dims)


# ------------------------------------------------------------------ triage + metrics
def triage(cl, y, n, seed, err=0.0):
    """Simulated analyst: n random flows per cluster (all if smaller), each label flipped with prob err,
    cluster gets the majority label (ties -> attack). Noise (-1) is one cluster of its own."""
    rng = np.random.default_rng(seed); pred = np.zeros(len(y), int); used = 0
    order = np.argsort(cl, kind="stable"); cs = cl[order]
    bounds = np.flatnonzero(np.diff(cs)) + 1; groups = np.split(order, bounds)
    for g in groups:
        pick = g if len(g) <= n else rng.choice(g, n, replace=False)
        lab = y[pick].copy()
        if err > 0: lab = np.where(rng.random(len(lab)) < err, 1 - lab, lab)
        used += len(pick); pred[g] = int(lab.mean() >= 0.5)
    return pred, used


def score(pred, y, used, benign_day):
    r = prf(y, pred); nb = max(1, int((y == 0).sum()))
    r["labels_used"] = used; r["fpr"] = r["fp"] / nb
    r["fa_day"] = r["fpr"] * benign_day * 24 / CAPTURE_HOURS
    return r


# ------------------------------------------------------------------ algorithms
def km(Z, k, seed): return KMeans(k, n_init=1, random_state=seed).fit_predict(Z)
REG_LADDER = [1e-4, 1e-3, 1e-2]       # reg_covar; escalated only if a component collapses on duplicate flows
GMM_REG_USED = {}
def gmm(Z, k, cov, seed):
    Z = np.asarray(Z, dtype="float64")
    for reg in REG_LADDER:
        try:
            g = GaussianMixture(k, covariance_type=cov, random_state=seed, max_iter=100, reg_covar=reg).fit(Z)
            GMM_REG_USED[(k, cov, seed)] = reg
            return g.predict(Z), g.bic(Z)
        except ValueError:
            continue
    raise RuntimeError(f"GMM failed for k={k} {cov}")
def dbs(Z, eps, ms): return DBSCAN(eps=eps, min_samples=ms, n_jobs=4).fit_predict(Z)


def sil(Z, cl, sub, ignore_noise=False):
    c = cl[sub]; Zs = Z[sub]
    if ignore_noise:
        m = c >= 0; c, Zs = c[m], Zs[m]
    if len(np.unique(c)) < 2 or len(c) < 50: return float("nan")
    return float(silhouette_score(Zs, c))


def edge_info(vals, chosen):
    i = vals.index(chosen); return {"index": i, "n": len(vals), "at_lower_edge": i == 0, "at_upper_edge": i == len(vals) - 1}


def kdist(Z, ms_list):
    nn = NearestNeighbors(n_neighbors=max(ms_list)).fit(Z)
    d, _ = nn.kneighbors(Z)          # column 0 is the point itself (distance 0)
    return {m: d[:, m - 1] for m in ms_list}


def eps_grid(kd, n=DB_NEPS):
    pos = kd[5][kd[5] > 0]
    lo = max(1e-3, float(np.quantile(pos, 0.10))); hi = float(np.quantile(kd[50], 0.995))
    return list(np.geomspace(lo, hi, n))


# ------------------------------------------------------------------ main per-day run
def run(key):
    t0 = time.time(); df, info = load_day(key); feats = feats_of(df); benign_day = info["benign_flows"]
    smp = systematic_sample(df, N_SAMPLE); y = smp["y"].values
    Z, _ = embed(smp, feats, N_PCA)
    sub = np.random.default_rng(SEED).choice(len(Z), SIL_N, replace=False)
    out = {"day": key, "n_sample": len(smp), "sample_step": len(df) // N_SAMPLE, "sample_attack": int(y.sum()),
           "benign_day": benign_day, "n_pca": N_PCA, "triage_n": N_TRIAGE, "silhouette_subsample": SIL_N,
           "capture_hours_assumed": CAPTURE_HOURS, "span_hours_measured": info["span_hours_fixed"]}
    rows = []

    # ---- K-Means
    kmres = {}; kmc = os.path.join(INTERIM, f"km_cache_{key}.pkl")
    import pickle
    cached = pickle.load(open(kmc, "rb")) if os.path.exists(kmc) else None
    for k in KM_K:
        for s in KM_SEEDS:
            if cached is not None: sc, r = cached[(k, s)]
            else:
                cl = km(Z, k, s); sc = sil(Z, cl, sub); pred, used = triage(cl, y, N_TRIAGE, s); r = score(pred, y, used, benign_day)
            kmres[(k, s)] = (sc, r); rows.append(dict(algo="kmeans", param=k, aux="", seed=s, crit=sc, n_clusters=k, noise=0.0, **{q: r[q] for q in ("precision", "recall", "f1", "labels_used", "fa_day")}))
    if cached is None: pickle.dump(kmres, open(kmc, "wb"))
    km_mean = {k: np.mean([kmres[(k, s)][0] for s in KM_SEEDS]) for k in KM_K}
    km_f1 = {k: np.mean([kmres[(k, s)][1]["f1"] for s in KM_SEEDS]) for k in KM_K}
    kbest = max(KM_K, key=lambda k: km_mean[k])
    out["kmeans"] = {"k": kbest, "silhouette": km_mean[kbest], "edge": edge_info(KM_K, kbest),
                     "stability_f1_pm1": [km_f1[k] for k in KM_K if abs(k - kbest) <= 1], "seeds": KM_SEEDS,
                     "grid": KM_K, "best_f1_in_grid_seedmean": max(km_f1.values()), "best_f1_k": max(KM_K, key=lambda k: km_f1[k])}
    print(key, "kmeans k", kbest, round(time.time() - t0), "s", flush=True)

    # ---- GMM (extend the grid while BIC is still falling at the edge)
    gres = {}; comps = list(GMM_COMPS)
    def gmm_cov(cov):
        i = 0
        while i < len(comps):
            k = comps[i]; cl, bic = gmm(Z, k, cov, SEED); pred, used = triage(cl, y, N_TRIAGE, SEED); r = score(pred, y, used, benign_day)
            gres[(cov, k)] = (bic, r, len(np.unique(cl)))
            rows.append(dict(algo="gmm", param=k, aux=cov, seed=SEED, crit=bic, n_clusters=len(np.unique(cl)), noise=0.0, **{q: r[q] for q in ("precision", "recall", "f1", "labels_used", "fa_day")}))
            i += 1
            if i == len(comps) and k < GMM_MAX:                       # BIC still lowest at the last point?
                ks = [kk for (c, kk) in gres if c == cov]
                if min(ks, key=lambda kk: gres[(cov, kk)][0]) == k: comps.append(min(k + GMM_EXT_STEP, GMM_MAX))
        print(key, "gmm", cov, "done", round(time.time() - t0), "s", flush=True)
    for cov in ("full", "diag"): gmm_cov(cov)
    gbest = min(gres, key=lambda ck: gres[ck][0]); gcov, gk = gbest
    gl = sorted(k for (c, k) in gres if c == gcov); gi = gl.index(gk)
    out["gmm"] = {"components": gk, "cov": gcov, "bic": gres[gbest][0], "edge": edge_info(gl, gk), "grid_max": max(gl), "grid": gl,
                  "stability_f1_pm1": [gres[(gcov, gl[j])][1]["f1"] for j in range(max(0, gi - 1), min(len(gl), gi + 2))],
                  "reg_covar_escalated": sorted({v for v in GMM_REG_USED.values()}), "bic_min_at_grid_max": bool(gk == max(gl)),
                  "best_f1_in_grid": max(v[1]["f1"] for v in gres.values()),
                  "bic_by_cov_min": {c: min(v[0] for (cc, k), v in gres.items() if cc == c) for c in ("full", "diag")}}
    print(key, "gmm", gk, gcov, round(time.time() - t0), "s", flush=True)

    # ---- DBSCAN
    kd = kdist(Z, DB_MS); egrid = eps_grid(kd); dres = {}
    def dbs_run(eps_list):
        for ms in DB_MS:
            for e in eps_list:
                if (ms, e) in dres: continue
                cl = dbs(Z, e, ms); noise = float((cl == -1).mean()); ncl = len(set(cl) - {-1})
                pred, used = triage(cl, y, N_TRIAGE, SEED); r = score(pred, y, used, benign_day)
                sc = sil(Z, cl, sub, ignore_noise=True) if noise <= NOISE_CAP else float("nan")
                dres[(ms, e)] = (sc, r, noise, ncl)
                rows.append(dict(algo="dbscan", param=e, aux=ms, seed=SEED, crit=sc, n_clusters=ncl, noise=noise, **{q: r[q] for q in ("precision", "recall", "f1", "labels_used", "fa_day")}))
    dbs_run(egrid); print(key, "dbscan grid done", round(time.time() - t0), "s", flush=True)
    for _ in range(3):                                                  # widen if the choice sits on an edge
        valid = {k: v for k, v in dres.items() if not np.isnan(v[0])}
        if not valid: break
        ms_b, e_b = max(valid, key=lambda k: valid[k][0])
        if e_b == egrid[0]: egrid = [egrid[0] / 1.5 ** (i + 1) for i in range(4)][::-1] + egrid
        elif e_b == egrid[-1]: egrid = egrid + [egrid[-1] * 1.4 ** (i + 1) for i in range(4)]
        else: break
        dbs_run(egrid)
    valid = {k: v for k, v in dres.items() if not np.isnan(v[0])}
    ms_b, e_b = max(valid, key=lambda k: valid[k][0]); ei = egrid.index(e_b); mi = DB_MS.index(ms_b)
    nb = [dres[(ms_b, egrid[j])][1]["f1"] for j in (ei - 1, ei, ei + 1) if 0 <= j < len(egrid)] + \
         [dres[(DB_MS[j], e_b)][1]["f1"] for j in (mi - 1, mi + 1) if 0 <= j < len(DB_MS)]
    allf = [v[1]["f1"] for v in dres.values()]
    out["dbscan"] = {"eps": e_b, "min_samples": ms_b, "silhouette": valid[(ms_b, e_b)][0], "n_clusters": valid[(ms_b, e_b)][3], "noise": valid[(ms_b, e_b)][2],
                     "eps_grid": egrid, "eps_edge": edge_info(egrid, e_b), "ms_edge": edge_info(DB_MS, ms_b), "stability_f1_neighbours": nb,
                     "f1_min_all": min(allf), "f1_max_all": max(allf), "n_settings": len(dres), "n_valid_settings": len(valid),
                     "kdist_quantile_of_eps": float((kd[ms_b] <= e_b).mean())}
    pd.DataFrame(rows).assign(day=key).to_csv(os.path.join(RES, f"task2_grid_{key}.csv"), index=False)
    print(key, "dbscan", e_b, ms_b, round(time.time() - t0), "s", flush=True)

    # ---- final evaluation of chosen configs, SWEEP_SEEDS (init seed + triage seed vary)
    def run_cfg(algo, Zx, yx, s, n=N_TRIAGE, err=0.0, cfg=None, q=None):
        cfg = cfg or out[algo]
        if algo == "kmeans": cl = km(Zx, cfg["k"], s)
        elif algo == "gmm": cl, _ = gmm(Zx, cfg["components"], cfg["cov"], s)
        else:
            e = float(np.quantile(kdist(Zx, [cfg["min_samples"]])[cfg["min_samples"]], q)) if q is not None else cfg["eps"]
            cl = dbs(Zx, e, cfg["min_samples"])
        pred, used = triage(cl, yx, n, s, err); return score(pred, yx, used, benign_day), cl, pred
    ALG = ["kmeans", "gmm", "dbscan"]; erows = []
    final = {}
    for a in ALG:
        rs = []
        for s in SWEEP_SEEDS if a != "kmeans" else KM_SEEDS:
            r, cl, pred = run_cfg(a, Z, y, s); rs.append(r)
            erows.append(dict(day=key, algo=a, sweep="final", value="chosen", seed=s, **{q: r[q] for q in ("precision", "recall", "f1", "labels_used", "fa_day")}))
        final[a] = {q: float(np.mean([r[q] for r in rs])) for q in ("precision", "recall", "f1", "labels_used", "fa_day")}
        final[a].update(f1_min=min(r["f1"] for r in rs), f1_max=max(r["f1"] for r in rs), n_seeds=len(rs))
    out["final"] = final; print(key, "final", round(time.time() - t0), "s", flush=True)

    # ---- extra sweeps
    for a in ALG:
        for dims in PCA_DIMS:
            Zx, kk = embed(smp, feats, dims)
            for s in SWEEP_SEEDS:
                r, _, _ = run_cfg(a, Zx, y, s, q=out["dbscan"]["kdist_quantile_of_eps"] if a == "dbscan" else None)
                erows.append(dict(day=key, algo=a, sweep="pca_dims", value=str(kk if dims == "var95" else dims) + ("*" if dims == "var95" else ""), seed=s, **{q: r[q] for q in ("precision", "recall", "f1", "labels_used", "fa_day")}))
        print(key, a, "pca sweep", round(time.time() - t0), "s", flush=True)
        for n in SAMPLE_SIZES:
            sm = systematic_sample(df, n); yy = sm["y"].values; Zx, _ = embed(sm, feats, N_PCA)
            for s in SWEEP_SEEDS:
                r, _, _ = run_cfg(a, Zx, yy, s, q=out["dbscan"]["kdist_quantile_of_eps"] if a == "dbscan" else None)
                erows.append(dict(day=key, algo=a, sweep="sample_size", value=n, seed=s, **{q: r[q] for q in ("precision", "recall", "f1", "labels_used", "fa_day")}))
        print(key, a, "size sweep", round(time.time() - t0), "s", flush=True)
        for sw, vals in (("triage_n", TRIAGE_N), ("analyst_error", ERR_RATES)):
            for v in vals:
                for s in SWEEP_SEEDS:
                    r, _, _ = run_cfg(a, Z, y, s, n=v if sw == "triage_n" else N_TRIAGE, err=v if sw == "analyst_error" else 0.0)
                    erows.append(dict(day=key, algo=a, sweep=sw, value=v, seed=s, **{q: r[q] for q in ("precision", "recall", "f1", "labels_used", "fa_day")}))
    pd.DataFrame(erows).to_csv(os.path.join(RES, f"task2_extra_sweeps_{key}.csv"), index=False)
    pca_k95 = embed(smp, feats, "var95")[1]; out["pca_k95"] = pca_k95

    # ---- seed-42 predictions for found/missed analysis, rules, figures
    preds = {}
    for a in ALG: _, cl, pr = run_cfg(a, Z, y, SEED); preds[a] = pr
    found = {a: (preds[a] == 1) & (y == 1) for a in ALG}
    anyf = np.logical_or.reduce([found[a] for a in ALG]); cnt = sum(found[a].astype(int) for a in ALG)
    groups = {"benign": y == 0, "found_any": anyf, "missed_all": (y == 1) & ~anyf, "all_attack": y == 1}
    for a in ALG: groups[f"only_{a}"] = found[a] & (cnt == 1)
    cols = ["Flow Duration", "TotLen Fwd Pkts", "TotLen Bwd Pkts", "Flow Pkts/s", "Init Fwd Win Byts"]
    pr_s, pl_s = port_rule(smp), payload_rule(smp)
    fm = {"counts": {g: int(m.sum()) for g, m in groups.items()}, "medians": {}, "top_ports_missed": {}, "rules_on_groups": {}}
    for g, m in groups.items():
        fm["medians"][g] = {c: float(smp.loc[m, c].median()) if m.any() else None for c in cols}
        fm["rules_on_groups"][g] = {"port_rule": int(pr_s[m].sum()), "payload_rule": int(pl_s[m].sum())}
    miss = smp[groups["missed_all"]]
    vc = miss["dport"].value_counts().head(6); fm["top_ports_missed"] = {str(k): int(v) for k, v in vc.items()}
    fm["top_ports_missed_share"] = {str(k): float(v / max(1, len(miss))) for k, v in vc.items()}
    fm["found_by_detector"] = {a: int(found[a].sum()) for a in ALG}
    # ordinary-traffic checks
    allfeat = df[feats]
    hh = pd.util.hash_pandas_object(allfeat.astype("float64"), index=False).values
    benign_hash = set(hh[df["y"].values == 0])
    smp_hash = pd.util.hash_pandas_object(smp[feats].astype("float64"), index=False).values
    nn = NearestNeighbors(n_neighbors=11).fit(Z); _, ind = nn.kneighbors(Z); ind = ind[:, 1:]
    benign_nb = (y[ind] == 0).sum(axis=1)
    def chk(m):
        n = int(m.sum())
        if n == 0: return {"n": 0}
        return {"n": n, "dup_of_benign": int(sum(h in benign_hash for h in smp_hash[m])),
                "mostly_benign_nn": int((benign_nb[m] > 5).sum())}
    fm["ordinary_checks"] = {"missed_all": chk(groups["missed_all"]), "found_any": chk(groups["found_any"]), "all_attack": chk(groups["all_attack"]),
                              "benign": chk(groups["benign"])}
    fm["nn_k"] = 10; fm["nn_rule"] = "more than 5 of 10 nearest PCA-space neighbours (within the 40,000-flow sample) are benign"
    fm["dup_rule"] = "all model features (same set the detectors use) identical to a benign flow anywhere in the same day"
    out["found_missed"] = fm
    # rules on sample and on the full day
    def rule_eval(fn, name):
        rs = score(fn(smp), y, 0, benign_day)
        full = fn(df); yf = df["y"].values; rf = prf(yf, full); rf["fa_day"] = rf["fp"] * 24 / CAPTURE_HOURS
        return {"sample": rs, "full_day": rf}
    out["rules"] = {"port": rule_eval(port_rule, "port")}
    if key == "thu": out["rules"]["payload"] = rule_eval(payload_rule, "payload")
    # arrays for figures
    rng = np.random.default_rng(SEED); fs = rng.choice(len(Z), 5000, replace=False)
    np.savez_compressed(os.path.join(INTERIM, f"task2_fig_{key}.npz"), z=Z[fs, :2], y=y[fs], label=smp["label"].values[fs].astype(str),
                        kmeans=preds["kmeans"][fs], gmm=preds["gmm"][fs], dbscan=preds["dbscan"][fs])
    out["runtime_s"] = time.time() - t0
    jdump(out, f"task2_{key}.json"); print(key, "done", round(time.time() - t0), "s", flush=True)


def merge():
    pd.concat([pd.read_csv(os.path.join(RES, f"task2_extra_sweeps_{k}.csv")) for k in DAYS]).to_csv(os.path.join(RES, "task2_extra_sweeps.csv"), index=False)
    pd.concat([pd.read_csv(os.path.join(RES, f"task2_grid_{k}.csv")) for k in DAYS]).to_csv(os.path.join(RES, "task2_grid.csv"), index=False)


if __name__ == "__main__":
    run(sys.argv[1]) if sys.argv[1] in DAYS else merge()
