#!/usr/bin/env python3
"""
ISI/PW analysis with MDPI-style outputs (expanded).
Inputs: CSV with columns time_s, pulse_width_us.
Outputs:
  - Table 7: table7_descriptives.csv
  - Table 8: table8_ks_results.csv
  - Figure 13: fig13_isi_cdf.png (Empirical vs Theoretical CDF)
  - Figure 14: fig14_isi_qq.png (ISI QQ vs Exponential)
  - Figure 15: fig15_pw_qq.png (PW QQ vs Uniform)
Usage:
  python isi_analysis.py --in data/fig1_pulse_train.csv --outdir figures --alpha 0.05
"""
import argparse, os, numpy as np, pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

def compute_stats(df: pd.DataFrame):
    t = np.sort(df["time_s"].to_numpy())
    w_us = df["pulse_width_us"].to_numpy()
    isi = np.diff(t)
    isi = isi[isi > 0]
    lambda_mle = 1.0 / np.mean(isi) if len(isi) else np.nan
    desc = {
        "lambda_mle_Hz": lambda_mle,
        "isi_mean_s": float(np.mean(isi)) if len(isi) else np.nan,
        "isi_std_s": float(np.std(isi, ddof=1)) if len(isi) > 1 else np.nan,
        "pw_min_us": int(np.min(w_us)) if len(w_us) else np.nan,
        "pw_max_us": int(np.max(w_us)) if len(w_us) else np.nan,
        "pw_mean_us": float(np.mean(w_us)) if len(w_us) else np.nan,
        "pw_std_us": float(np.std(w_us, ddof=1)) if len(w_us) > 1 else np.nan,
        "duration_s": float(t[-1]) if len(t) else 0.0,
        "num_events": int(len(t)),
    }
    return isi, w_us, desc

def fig_isi_cdf(isi, lambda_mle, out_png):
    x = np.sort(isi)
    y = np.arange(1, len(x)+1) / len(x)
    x_th = np.linspace(0, max(1e-9, x.max()*1.05), 400)
    y_th = 1.0 - np.exp(-lambda_mle * x_th) if np.isfinite(lambda_mle) else np.zeros_like(x_th)
    plt.figure(figsize=(5,4))
    plt.step(x, y, where="post", label="Empirical CDF (ISI)")
    plt.plot(x_th, y_th, label=f"Theoretical Exp CDF (λ={lambda_mle:.3f} Hz)")
    plt.xlabel("ISI [s]"); plt.ylabel("CDF"); plt.title("Figure 13. ISI CDF: empirical vs. exponential")
    plt.grid(True, alpha=0.3); plt.legend(); plt.tight_layout()
    plt.savefig(out_png, dpi=300); plt.close()

def qq_plot_empirical_vs_exponential(isi, lambda_mle, out_png):
    p = (np.arange(1, len(isi)+1) - 0.5) / len(isi)
    isi_sorted = np.sort(isi)
    scale = 1.0 / lambda_mle if lambda_mle > 0 else np.inf
    th = stats.expon.ppf(p, scale=scale)
    plt.figure(figsize=(5,4))
    plt.plot(th, isi_sorted, ".", ms=3)
    lo = min(th.min(), isi_sorted.min()); hi = max(th.max(), isi_sorted.max())
    plt.plot([lo, hi], [lo, hi], "k--", lw=1)
    plt.xlabel("Theoretical quantiles: Exp(λ) [s]"); plt.ylabel("Empirical quantiles: ISI [s]")
    plt.title("Figure 14. ISI Q–Q vs. Exponential"); plt.grid(True, alpha=0.3); plt.tight_layout()
    plt.savefig(out_png, dpi=300); plt.close()

def qq_plot_pw_vs_uniform(w_us, out_png):
    a = np.min(w_us); b = np.max(w_us)
    p = (np.arange(1, len(w_us)+1) - 0.5) / len(w_us)
    pw_sorted = np.sort(w_us)
    th = stats.uniform.ppf(p, loc=a, scale=(b-a) if b>a else 1.0)
    plt.figure(figsize=(5,4))
    plt.plot(th, pw_sorted, ".", ms=3)
    lo = min(th.min(), pw_sorted.min()); hi = max(th.max(), pw_sorted.max())
    plt.plot([lo, hi], [lo, hi], "k--", lw=1)
    plt.xlabel("Theoretical quantiles: Uniform[a,b] [μs]"); plt.ylabel("Empirical quantiles: PW [μs]")
    plt.title("Figure 15. PW Q–Q vs. Uniform"); plt.grid(True, alpha=0.3); plt.tight_layout()
    plt.savefig(out_png, dpi=300); plt.close()

def ks_tests(isi, w_us, lambda_mle, out_csv, alpha=0.05):
    from scipy import stats
    n_isi, n_pw = len(isi), len(w_us)
    scale = 1.0 / lambda_mle if lambda_mle>0 else np.inf
    D1, p1 = stats.kstest(isi, 'expon', args=(0, scale)) if n_isi>0 and np.isfinite(scale) else (np.nan, np.nan)
    a, b = int(np.min(w_us)), int(np.max(w_us))
    D2, p2 = stats.kstest(w_us, 'uniform', args=(a, (b-a) if b>a else 1)) if n_pw>0 else (np.nan, np.nan)
    df = pd.DataFrame([
        {"test": "KS ISI vs Exp(λ_MLE)", "D": D1, "p_value": p1, "n": n_isi},
        {"test": "KS PW vs Uniform[min,max]", "D": D2, "p_value": p2, "n": n_pw},
    ])
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    df.to_csv(out_csv, index=False)
    return df

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="in_csv", type=str, required=True)
    ap.add_argument("--outdir", dest="outdir", type=str, required=True)
    ap.add_argument("--alpha", dest="alpha", type=float, default=0.05)
    args = ap.parse_args()

    df = pd.read_csv(args.in_csv)
    isi, w_us, desc = compute_stats(df)

    # Tables
    t7 = pd.DataFrame([desc])
    os.makedirs(args.outdir, exist_ok=True)
    t7.to_csv(os.path.join(args.outdir, "table7_descriptives.csv"), index=False)
    ks_tests(isi, w_us, desc["lambda_mle_Hz"], os.path.join(args.outdir, "table8_ks_results.csv"), args.alpha)

    # Figures
    if len(isi) > 0 and np.isfinite(desc["lambda_mle_Hz"]) and desc["lambda_mle_Hz"]>0:
        fig_isi_cdf(isi, desc["lambda_mle_Hz"], os.path.join(args.outdir, "fig13_isi_cdf.png"))
        qq_plot_empirical_vs_exponential(isi, desc["lambda_mle_Hz"], os.path.join(args.outdir, "fig14_isi_qq.png"))
    if len(w_us) > 0:
        qq_plot_pw_vs_uniform(w_us, os.path.join(args.outdir, "fig15_pw_qq.png"))

    print("Done. Outputs in:", args.outdir)

if __name__ == "__main__":
    main()
