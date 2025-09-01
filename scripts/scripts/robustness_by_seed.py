#!/usr/bin/env python3
"""
Robustness across seeds (Figure 24 + Table 21).
Generates ~30 s per seed with specified λ and PW range, then runs KS tests.

Usage:
  python robustness_by_seed.py --lambda 2.0 --duration 30 --pw-min 50 --pw-max 1000 \
      --seeds 1001 1002 1003 1004 1005 --outdir figures
"""
import argparse, os, numpy as np, pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

def generate(lambda_hz, duration_s, pw_min_us, pw_max_us, rng):
    t = 0.0; T = []; W = []
    while t < duration_s:
        isi = rng.exponential(1.0/lambda_hz)
        t += isi
        if t > duration_s: break
        W.append(int(rng.integers(pw_min_us, pw_max_us+1)))
        T.append(t)
    return np.array(T), np.array(W)

def ks_wrap(isi, w):
    lam = 1.0/np.mean(isi) if len(isi) else np.nan
    scale = 1.0/lam if lam>0 else np.inf
    D1, p1 = stats.kstest(isi, 'expon', args=(0, scale)) if len(isi)>0 and np.isfinite(scale) else (np.nan, np.nan)
    a, b = int(np.min(w)), int(np.max(w))
    D2, p2 = stats.kstest(w, 'uniform', args=(a, (b-a) if b>a else 1)) if len(w)>0 else (np.nan, np.nan)
    return lam, D1, p1, D2, p2

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lambda", dest="lambda_hz", type=float, required=True)
    ap.add_argument("--duration", dest="duration_s", type=float, required=True)
    ap.add_argument("--pw-min", dest="pw_min_us", type=int, required=True)
    ap.add_argument("--pw-max", dest="pw_max_us", type=int, required=True)
    ap.add_argument("--seeds", nargs="+", type=int, required=True)
    ap.add_argument("--outdir", dest="outdir", required=True)
    args = ap.parse_args()

    rows = []
    for s in args.seeds:
        rng = np.random.default_rng(s)
        T, W = generate(args.lambda_hz, args.duration_s, args.pw_min_us, args.pw_max_us, rng)
        isi = np.diff(T)
        lam, D1, p1, D2, p2 = ks_wrap(isi, W)
        rows.append({
            "seed": s, "n_events": len(T), "lambda_mle_Hz": lam,
            "KS_ISI_D": D1, "KS_ISI_p": p1, "KS_PW_D": D2, "KS_PW_p": p2
        })
    df = pd.DataFrame(rows)

    os.makedirs(args.outdir, exist_ok=True)
    df.to_csv(os.path.join(args.outdir, "table21_robustness.csv"), index=False)

    plt.figure(figsize=(6,4))
    plt.plot(df["seed"], df["KS_ISI_p"], "o-", label="ISI p-value")
    plt.plot(df["seed"], df["KS_PW_p"], "s-", label="PW p-value")
    plt.axhline(0.05, color="k", ls="--", lw=1, label="α=0.05")
    plt.xlabel("Seed"); plt.ylabel("p-value"); plt.title("Figure 24. Robustness by seed (KS p-values)")
    plt.grid(True, alpha=0.3); plt.legend(); plt.tight_layout()
    plt.savefig(os.path.join(args.outdir, "fig24_robustness.png"), dpi=300); plt.close()
    print("Done. Outputs in:", args.outdir)

if __name__ == "__main__":
    main()
