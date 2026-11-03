"""Stage 5: all figures at final print width (6.5 in), every font >= 8 pt, 300 dpi."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from sklearn.metrics import precision_recall_curve
from lab1.common import *

plt.rcParams.update({"font.size": 8, "axes.titlesize": 8, "axes.labelsize": 8, "xtick.labelsize": 8, "ytick.labelsize": 8,
                     "legend.fontsize": 8, "figure.dpi": 100, "savefig.dpi": 300, "font.family": "DejaVu Sans",
                     "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": 0.6})
C = {"Benign": "#7f8c8d", "FTP-BruteForce": "#0072B2", "SSH-Bruteforce": "#D55E00", "Infilteration": "#CC79A7",
     "LogReg": "#E69F00", "RandomForest": "#0072B2", "MLP": "#009E73", "kmeans": "#E69F00", "gmm": "#0072B2", "dbscan": "#009E73"}
NAME = {"LogReg": "LogReg", "RandomForest": "RF", "MLP": "MLP"}
SPLIT_TITLE = {"wed70": "Wed 70%", "wed80": "Wed 80%", "thu70": "Thu 70%"}
W = 6.5


def save(fig, name):
    fig.savefig(os.path.join(FIG, name), bbox_inches="tight", pad_inches=0.03); plt.close(fig); print("wrote", name)


def fig1():
    fig, axs = plt.subplots(2, 1, figsize=(W, 3.7))
    for ax, key, cuts in zip(axs, ("wed", "thu"), ([0.7, 0.8], [0.7])):
        df, _ = load_day(key); t = df["ts"]; h = t.dt.hour + t.dt.minute / 60
        bins = np.arange(8, 18.01, 5 / 60)
        for lab in ("Benign",) + tuple(l for l in df["label"].unique() if l != "Benign"):
            ax.hist(h[df["label"] == lab], bins=bins, histtype="stepfilled", alpha=0.75, color=C[lab], label=lab)
        ax.set_yscale("log"); ax.set_ylim(0.8, 6e5)
        for i, f in enumerate(cuts):
            ct = df["ts"].iloc[int(len(df) * f)]; x = ct.hour + ct.minute / 60
            ax.axvline(x, color="k", ls="--", lw=0.8, ymax=0.76)
            ax.text(x + (-0.08 if (key == "wed" and i == 0) else 0.08), 1.4 if i == 0 else 4, f"{int(f*100)}% cut {ct:%H:%M}", fontsize=8, va="bottom", ha="right" if (key == "wed" and i == 0) else "left")
        ax.set_xlim(8, 18); ax.set_ylabel("Flows per 5 min"); ax.legend(loc="upper right", ncol=3, frameon=False, borderaxespad=0.2)
        ax.set_title({"wed": "Wednesday 14-02-2018", "thu": "Thursday 01-03-2018"}[key] + " (repaired clock)", loc="left")
    axs[1].set_xlabel("Hour of day (repaired clock)")
    fig.tight_layout(); save(fig, "fig1_timeline.png")


def fig2():
    R = jload("task1_results.json")["splits"]
    fig, axs = plt.subplots(3, 3, figsize=(W, 2.9))
    for r, sid in enumerate(("wed70", "wed80", "thu70")):
        for c, m in enumerate(("LogReg", "RandomForest", "MLP")):
            ax = axs[r, c]; x = R[sid]["models"][m]; M = np.array([[x["tn"], x["fp"]], [x["fn"], x["tp"]]])
            ax.imshow(np.log1p(M), cmap="Blues", vmin=0, vmax=np.log1p(M.max()) * 1.25, aspect="auto")
            for (i, j), v in np.ndenumerate(M): ax.text(j, i, f"{v:,}", ha="center", va="center", fontsize=8, color="k" if np.log1p(v) < 0.6 * np.log1p(M.max()) else "w")
            ax.set_title(f"{SPLIT_TITLE[sid]} · {NAME[m]}", pad=2); ax.tick_params(length=0)
            ax.set_xticks([0, 1], ["pred. benign", "pred. attack"] if r == 2 else ["", ""])
            ax.set_yticks([0, 1], ["true benign", "true attack"] if c == 0 else ["", ""], va="center")
    fig.tight_layout(pad=0.3, h_pad=0.4, w_pad=0.4); save(fig, "fig2_confusion.png")


def fig3():
    Z = np.load(os.path.join(INTERIM, "task1_scores.npz")); R = jload("task1_results.json")["splits"]
    fig, axs = plt.subplots(1, 3, figsize=(W, 2.4), sharey=True)
    for ax, sid in zip(axs, ("wed70", "wed80", "thu70")):
        y = Z[f"{sid}__y"]
        for m in ("LogReg", "RandomForest", "MLP"):
            p, r, _ = precision_recall_curve(y, Z[f"{sid}__{m}"]); ax.plot(r, p, color=C[m], lw=1.2, label=f"{NAME[m]} AP={R[sid]['models'][m]['ap']:.3f}")
        ax.axhline(y.mean(), color="k", ls=":", lw=0.8, label=f"chance {y.mean():.3f}")
        ax.set_title(SPLIT_TITLE[sid]); ax.set_xlabel("Recall (attack)"); ax.set_xlim(0, 1); ax.set_ylim(0, 1.02)
        ax.legend(loc={"wed70": "lower left", "wed80": "lower left", "thu70": "upper right"}[sid], frameon=False, handlelength=1.2, labelspacing=0.2, bbox_to_anchor={"wed70": None, "wed80": (0.0, 0.05), "thu70": None}[sid])
    axs[0].set_ylabel("Precision (attack)"); fig.tight_layout(pad=0.4); save(fig, "fig3_pr.png")


def fig4():
    fig, axs = plt.subplots(2, 4, figsize=(W, 3.3))
    for r, key in enumerate(("wed", "thu")):
        d = np.load(os.path.join(INTERIM, f"task2_fig_{key}.npz")); T = jload(f"task2_{key}.json")
        z = d["z"]; y = d["y"]
        ttl = [("True labels", None), (f"K-Means k={T['kmeans']['k']}", "kmeans"), (f"GMM {T['gmm']['components']} {T['gmm']['cov']}", "gmm"), ("DBSCAN", "dbscan")]
        for c, (t, k) in enumerate(ttl):
            ax = axs[r, c]
            if k is None:
                ax.scatter(z[y == 0, 0], z[y == 0, 1], s=1.5, c=C["Benign"], lw=0, rasterized=True); ax.scatter(z[y == 1, 0], z[y == 1, 1], s=1.5, c="#D55E00", lw=0, rasterized=True)
            else:
                p = d[k]; tp = (p == 1) & (y == 1); fp = (p == 1) & (y == 0); fn = (p == 0) & (y == 1); tn = (p == 0) & (y == 0)
                for m_, col in ((tn, "#cfd4d6"), (fn, "#CC79A7"), (fp, "#E69F00"), (tp, "#0072B2")): ax.scatter(z[m_, 0], z[m_, 1], s=1.5, c=col, lw=0, rasterized=True)
            ax.set_title(("Wed · " if key == "wed" else "Thu · ") + t); ax.set_xticks([]); ax.set_yticks([])
            if c == 0: ax.set_ylabel("PC2")
            if r == 1: ax.set_xlabel("PC1")
    from matplotlib.lines import Line2D
    h = [Line2D([], [], marker="o", ls="", ms=4, color=c, label=l) for c, l in (("#7f8c8d", "benign (true label)"), ("#D55E00", "attack (true label)"))]
    h2 = [Line2D([], [], marker="o", ls="", ms=4, color=c, label=l) for c, l in (("#0072B2", "attack found"), ("#CC79A7", "attack missed"), ("#E69F00", "false alert"), ("#cfd4d6", "benign, correct"))]
    fig.legend(handles=h + h2, loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.02), columnspacing=1.2, handletextpad=0.2)
    fig.tight_layout(rect=(0, 0.09, 1, 1), pad=0.4); save(fig, "fig4_clusters.png")


def fig5():
    fig, axs = plt.subplots(2, 3, figsize=(W, 3.4), sharey=True)
    for r, key in enumerate(("wed", "thu")):
        G = pd.read_csv(os.path.join(RES, f"task2_grid_{key}.csv")); G["aux"] = G["aux"].astype(str); T = jload(f"task2_{key}.json")
        ax = axs[r, 0]; g = G[G.algo == "kmeans"].groupby("param")["f1"].agg(["mean", "min", "max"])
        ax.fill_between(g.index, g["min"], g["max"], color=C["kmeans"], alpha=0.25, lw=0); ax.plot(g.index, g["mean"], color=C["kmeans"], lw=1.2)
        k = T["kmeans"]["k"]; ax.plot([k], [g.loc[k, "mean"]], "k*", ms=8); ax.set_xlim(2, 40)
        ax.set_title(f"{key.title()[:3]} · K-Means (5 seeds)"); ax.set_xlabel("k" if r == 1 else "")
        ax = axs[r, 1]; g = G[G.algo == "gmm"]
        for cov, ls in (("full", "-"), ("diag", "--")):
            q = g[g.aux == cov].sort_values("param"); ax.plot(q.param, q.f1, ls, color=C["gmm"], lw=1.2, label=cov)
        q = g[(g.aux == T["gmm"]["cov"]) & (g.param == T["gmm"]["components"])]; ax.plot(q.param, q.f1, "k*", ms=8)
        ax.legend(frameon=False, loc="lower right" if r == 0 else "upper right"); ax.set_title(f"{key.title()[:3]} · GMM"); ax.set_xlabel("components" if r == 1 else "")
        ax = axs[r, 2]; g = G[G.algo == "dbscan"]
        for ms, col in zip((5, 10, 25, 50), ("#999999", "#56B4E9", "#009E73", "#D55E00")):
            q = g[g.aux == str(ms)].sort_values("param"); ax.plot(q.param, q.f1, color=col, lw=1.0, label=f"min_s={ms}")
        q = g[(g.aux == str(T["dbscan"]["min_samples"])) & (np.isclose(g.param, T["dbscan"]["eps"]))]; ax.plot(q.param, q.f1, "k*", ms=8)
        ax.set_xscale("log"); ax.set_title(f"{key.title()[:3]} · DBSCAN"); ax.set_xlabel("eps" if r == 1 else "")
        if r == 0: ax.legend(frameon=False, ncol=2, loc="lower center", handlelength=1, columnspacing=0.6)
    for r in range(2): axs[r, 0].set_ylabel("Attack F1 after triage")
    fig.tight_layout(pad=0.4); save(fig, "fig5_sweeps.png")


if __name__ == "__main__":
    os.makedirs(FIG, exist_ok=True)
    for f in (fig1, fig2, fig3, fig4, fig5):
        try: f()
        except Exception as e: print("FAILED", f.__name__, repr(e))
