#!/usr/bin/env python3
"""
ISI & pulse analysis for APPR generator logs.
- Loads CSV with columns: t_ms,width_us,isi_ms
- Computes MLE of lambda, plots histograms, runs Kolmogorov-Smirnov test (if SciPy available).
- Saves figures to ./figures by default.
"""

import argparse, os
import numpy as np
import matplotlib.pyplot as plt

def load_csv(path):
    data = np.genfromtxt(path, delimiter=",", names=True, dtype=None, encoding=None)
    return data

def ks_expon(isi_ms):
    try:
        from scipy.stats import kstest, expon
        scale = np.mean(isi_ms)
        D, p = kstest(isi_ms, 'expon', args=(0, scale))
        return D, p
    except Exception:
        return None, None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", help="simulation_data.csv or acquisition log exported as CSV")
    ap.add_argument("--outdir", default="figures", help="output directory for figures")
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    D = load_csv(args.csv)
    isi = np.asarray(D['isi_ms'], dtype=float)

    mean_isi = isi.mean()
    lam_hz = 1000.0 / mean_isi

    # ISI figure
    plt.figure(figsize=(6,4))
    counts,bins,_ = plt.hist(isi, bins=40, density=True, alpha=0.7)
    x = np.linspace(0, max(isi)*0.98, 500)
    pdf = (lam_hz/1000.0) * np.exp(-(lam_hz/1000.0)*x)
    plt.plot(x, pdf, linewidth=2)
    plt.xlabel("Međupulsni razmak (ms)")
    plt.ylabel("Gustina")
    plt.title(f"ISI histogram + eksponencijalni fit (λ≈{lam_hz:.3f} Hz)")
    plt.tight_layout()
    plt.savefig(os.path.join(args.outdir, "isi_hist_fit.png"), dpi=200)
    plt.close()

    widths = np.asarray(D['width_us'], dtype=float)
    plt.figure(figsize=(6,4))
    plt.hist(widths, bins=25, density=True, alpha=0.8)
    plt.xlabel("Širina impulsa (µs)")
    plt.ylabel("Gustina")
    plt.title("Histogram širine impulsa")
    plt.tight_layout()
    plt.savefig(os.path.join(args.outdir, "width_hist.png"), dpi=200)
    plt.close()

    # Stats
    Dstat, pval = ks_expon(isi)
    with open(os.path.join(args.outdir, "stats.txt"), "w") as f:
        f.write(f"λ_MLE (Hz) = {lam_hz:.6f}\n")
        f.write(f"Mean ISI (ms) = {mean_isi:.6f}\n")
        if Dstat is not None:
            f.write(f"KS test vs Exponential: D={Dstat:.6f}, p={pval:.6g}\n")
        else:
            f.write("KS test not available (SciPy not installed).\n")

    print(f"Done. λ≈{lam_hz:.3f} Hz. Figures + stats in {args.outdir}/")

if __name__ == "__main__":
    main()
