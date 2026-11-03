"""Shared code: loading, cleaning, clock repair, features, splits, metrics, CIs, tests."""
import json, os, time
import numpy as np, pandas as pd
from scipy import stats

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RAW = os.path.join(ROOT, "data", "raw")
INTERIM = os.path.join(ROOT, "data", "interim")
RES = os.path.join(ROOT, "results")
FIG = os.path.join(ROOT, "figures")
SEED = 42
DAYS = {"wed": "Wednesday-14-02-2018", "thu": "Thursday-01-03-2018"}
CAPTURE_HOURS = 12          # brief: "Each day is a 12-hour capture" (Task 2 convention)
BLOCK_MIN = 5               # bootstrap block length in minutes
N_BOOT = 1000
os.makedirs(INTERIM, exist_ok=True); os.makedirs(RES, exist_ok=True)


def jdump(obj, name):
    with open(os.path.join(RES, name), "w") as f:
        json.dump(obj, f, indent=2, default=lambda o: o.item() if hasattr(o, "item") else str(o))


def jload(name):
    with open(os.path.join(RES, name)) as f:
        return json.load(f)


# ------------------------------------------------------------------ loading / cleaning
def repair_clock(ts):
    """Files use a 12-hour clock without AM/PM. Capture runs ~08:00-18:00:
    hours 08-12 are morning/noon (unchanged), hours 01-07 are afternoon (+12 h)."""
    h = ts.dt.hour
    moved = (h >= 1) & (h <= 7)
    return ts + pd.to_timedelta(np.where(moved, 12, 0), unit="h"), moved.values


def load_day(key, force=False):
    """Return (df, info). df is sorted (stable) by repaired time. Columns: feature columns
    (float32), plus meta columns: ts, ts_raw, label, y, dport, fileorder."""
    pk = os.path.join(INTERIM, f"{key}.pkl"); ik = os.path.join(RES, f"prep_{key}.json")
    if os.path.exists(pk) and os.path.exists(ik) and not force:
        return pd.read_pickle(pk), jload(f"prep_{key}.json")
    path = os.path.join(RAW, f"{DAYS[key]}_TrafficForML_CICFlowMeter.csv")
    raw = pd.read_csv(path, dtype=str)
    info = {"day": DAYS[key], "rows_in_file": int(len(raw))}
    hdr = raw["Dst Port"] == "Dst Port"
    info["header_lines"] = int(hdr.sum()); raw = raw[~hdr].copy()
    raw["fileorder"] = np.arange(len(raw))
    ts_raw = pd.to_datetime(raw["Timestamp"], format="%d/%m/%Y %H:%M:%S")
    y1970 = (ts_raw.dt.year == 1970).values
    info["rows_1970"] = int(y1970.sum()); raw, ts_raw = raw[~y1970], ts_raw[~y1970]
    num = raw.drop(columns=["Timestamp", "Label", "fileorder"]).apply(pd.to_numeric).astype("float64")
    info["rows_nan_total_before_inf_removal"] = int(num.isna().any(axis=1).sum())
    inf = np.isinf(num.values).any(axis=1)
    info["rows_infinity"] = int(inf.sum())
    num, raw, ts_raw = num[~inf], raw[~inf], ts_raw[~inf]
    nan = num.isna().any(axis=1).values
    info["rows_nan_after_inf"] = int(nan.sum())
    info["nan_columns"] = [c for c in num.columns if num[c].isna().any()]
    num, raw, ts_raw = num[~nan], raw[~nan], ts_raw[~nan]
    info["rows_kept"] = int(len(num))
    info["duplicate_rows_kept"] = int(num.assign(l=raw["Label"].values).duplicated().sum())
    info["duplicate_policy"] = "counted, not dropped (flow records can legitimately repeat; dropping would delete real traffic)"
    const = [c for c in num.columns if c not in ("Dst Port",) and num[c].nunique() <= 1]
    info["constant_columns"] = const
    feats = [c for c in num.columns if c not in ("Dst Port",) and c not in const]
    info["n_features"] = len(feats); info["features"] = feats
    info["protocol_kept"] = "Protocol" in feats
    ts_fix, moved = repair_clock(ts_raw)
    info["flows_moved_by_clock_fix"] = int(moved.sum())
    df = num[feats].astype("float32").copy()
    df["dport"] = num["Dst Port"].values.astype("int32")
    df["label"] = raw["Label"].values
    df["y"] = (df["label"] != "Benign").astype("int8")
    df["ts_raw"] = ts_raw.values; df["ts"] = ts_fix.values
    df["fileorder"] = raw["fileorder"].values
    # extra raw columns needed by rules (kept inside feats already) ; nothing else
    df = df.sort_values("ts", kind="stable").reset_index(drop=True)
    info["labels"] = {k: int(v) for k, v in df["label"].value_counts().items()}
    info["attack_flows"] = int(df["y"].sum()); info["attack_share"] = float(df["y"].mean())
    info["benign_flows"] = int((df["y"] == 0).sum())
    # clock evidence
    ev = {}
    for lab, g in df.groupby("label"):
        ev[lab] = {"raw_first": str(g["ts_raw"].min()), "raw_last": str(g["ts_raw"].max()),
                   "fixed_first": str(g["ts"].min()), "fixed_last": str(g["ts"].max()), "n": int(len(g))}
    info["clock_evidence"] = ev
    info["hour_hist_raw"] = {int(k): int(v) for k, v in df["ts_raw"].dt.hour.value_counts().sort_index().items()}
    info["hour_hist_fixed"] = {int(k): int(v) for k, v in df["ts"].dt.hour.value_counts().sort_index().items()}
    fo = df.sort_values("fileorder")
    d_fix = fo["ts"].diff().dt.total_seconds().dropna(); d_raw = fo["ts_raw"].diff().dt.total_seconds().dropna()
    info["fileorder_backward_steps_fixed"] = int((d_fix < 0).sum()); info["fileorder_backward_steps_raw"] = int((d_raw < 0).sum())
    info["fileorder_adjacent_pairs"] = int(len(d_fix))
    info["span_hours_fixed"] = float((df["ts"].max() - df["ts"].min()).total_seconds() / 3600)
    info["first_ts_fixed"] = str(df["ts"].min()); info["last_ts_fixed"] = str(df["ts"].max())
    df.to_pickle(pk); jdump(info, f"prep_{key}.json")
    return df, info


def feats_of(df):
    return [c for c in df.columns if c not in ("dport", "label", "y", "ts_raw", "ts", "fileorder")]


def slog(X):
    X = np.asarray(X, dtype="float32")
    return (np.sign(X) * np.log1p(np.abs(X))).astype("float32")


# ------------------------------------------------------------------ splits
def split_index(df, frac):
    return int(len(df) * frac)


def window_hours(ts):
    return float((ts.max() - ts.min()).total_seconds() / 3600)


# ------------------------------------------------------------------ metrics
def prf(y, p):
    y = np.asarray(y); p = np.asarray(p)
    tp = int(((y == 1) & (p == 1)).sum()); fp = int(((y == 0) & (p == 1)).sum())
    fn = int(((y == 1) & (p == 0)).sum()); tn = int(((y == 0) & (p == 0)).sum())
    pr = tp / (tp + fp) if tp + fp else 0.0; rc = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * pr * rc / (pr + rc) if pr + rc else 0.0
    return dict(tp=tp, fp=fp, fn=fn, tn=tn, precision=pr, recall=rc, f1=f1)


def poisson_ci(k, alpha=0.05):
    lo = 0.0 if k == 0 else stats.chi2.ppf(alpha / 2, 2 * k) / 2
    hi = stats.chi2.ppf(1 - alpha / 2, 2 * (k + 1)) / 2
    return float(lo), float(hi)


def fa_per_day(fp, hours):
    """Task 1 convention: benign flagged / window hours * 24, with exact Poisson 95% CI."""
    lo, hi = poisson_ci(int(fp)); s = 24.0 / hours
    return dict(value=fp * s, lo=lo * s, hi=hi * s, fp=int(fp), hours=hours)


def block_bootstrap_f1(y, p, ts, block_min=BLOCK_MIN, n_boot=N_BOOT, seed=SEED):
    """95% CI for F1 by resampling contiguous time blocks of the test window."""
    t = (ts - ts.min()).dt.total_seconds().values
    b = (t // (block_min * 60)).astype(int); b -= b.min()
    nb = b.max() + 1
    y = np.asarray(y); p = np.asarray(p)
    tp = np.bincount(b, weights=((y == 1) & (p == 1)), minlength=nb)
    fp = np.bincount(b, weights=((y == 0) & (p == 1)), minlength=nb)
    fn = np.bincount(b, weights=((y == 1) & (p == 0)), minlength=nb)
    rng = np.random.default_rng(seed); out = np.empty(n_boot)
    for i in range(n_boot):
        ix = rng.integers(0, nb, nb)
        a, c, d = tp[ix].sum(), fp[ix].sum(), fn[ix].sum()
        out[i] = 2 * a / (2 * a + c + d) if 2 * a + c + d else 0.0
    return float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5)), int(nb)


def mcnemar(y, pa, pb):
    ca = (np.asarray(pa) == np.asarray(y)); cb = (np.asarray(pb) == np.asarray(y))
    b = int((ca & ~cb).sum()); c = int((~ca & cb).sum()); n = b + c
    if n == 0:
        return dict(b=b, c=c, p=1.0, test="none")
    if n < 25:
        return dict(b=b, c=c, p=float(min(1.0, 2 * stats.binom.cdf(min(b, c), n, 0.5))), test="exact")
    chi = (abs(b - c) - 1) ** 2 / n
    return dict(b=b, c=c, p=float(stats.chi2.sf(chi, 1)), test="chi2")


class Timer:
    def __enter__(self):
        self.t = time.time(); return self
    def __exit__(self, *a):
        self.s = time.time() - self.t
