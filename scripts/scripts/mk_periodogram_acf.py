#!/usr/bin/env python3
"""
Make periodogram (Figure 16 + Tables 9/9b) and ACF (Figure 17 + Tables 10/10b)
from APPI pulses binned at 1 ms.
Input CSV must have columns time_s, pulse_width_us.
Usage:
  python mk_periodogram_acf.py --in data/fig1_pulse_train.csv --outdir figures
"""
import argparse, os, numpy as np, pandas as pd
import matplotlib.pyplot as plt

def build_binned_signal(df, bin_ms=1.0):
    t = df["time_s"].to_numpy()
    w_us = df["pulse_width_us"].to_numpy()
    t_end = float(np.max(t) + np.max(w_us)*1e-6) if len(t) else 0.0
    fs = 1000.0 / bin_ms  # Hz
    n = int(np.ceil(t_end * fs)) + 1
    diff = np.zeros(n+1, dtype=np.int32)
    for ti, w in zip(t, w_us):
        start = int(np.floor(ti * fs))
        stop = int(np.ceil((ti + w*1e-6) * fs))
        stop = max(stop, start+1)
        diff[start] += 1
        diff[stop] -= 1
    x = np.cumsum(diff[:-1]).astype(float)
    return x, fs

def periodogram(x, fs):
    x0 = x - np.mean(x)
    X = np.fft.rfft(x0)
    P = (np.abs(X)**2) / len(x0)
    f = np.fft.rfftfreq(len(x0), d=1.0/fs)
    return f, P

def acf(x, max_lag=None):
    x0 = x - np.mean(x)
    denom = np.sum(x0*x0)
    if denom <= 0: 
        return np.array([0.0]), np.array([1.0])
    c = np.correlate(x0, x0, mode="full")
    mid = len(c)//2
    r = c[mid:]/denom
    if max_lag is not None:
        r = r[:max_lag+1]
    lags = np.arange(len(r))
    return lags, r

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="in_csv", required=True)
    ap.add_argument("--outdir", dest="outdir", required=True)
    ap.add_argument("--bin-ms", dest="bin_ms", type=float, default=1.0)
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    df = pd.read_csv(args.in_csv)
    x, fs = build_binned_signal(df, args.bin_ms)
    f, P = periodogram(x, fs)

    # Figure 16
    plt.figure(figsize=(6,4))
    plt.semilogy(f[1:], P[1:] + 1e-18)  # skip DC
    plt.xlabel("Frequency [Hz]"); plt.ylabel("Power")
    plt.title("Figure 16. Periodogram of APPI pulse-train (bin=1 ms)")
    plt.grid(True, which="both", alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(args.outdir, "fig16_periodogram.png"), dpi=300)
    plt.close()

    # Table 9
    pd.DataFrame({"freq_Hz": f, "power": P}).to_csv(os.path.join(args.outdir, "table9_psd.csv"), index=False)

    # Table 9b (summary)
    mask = f > 0
    if np.any(mask):
        f_dom = float(f[mask][np.argmax(P[mask])])
        max_to_mean = float(np.max(P[mask]) / (np.mean(P[mask]) + 1e-18))
    else:
        f_dom, max_to_mean = np.nan, np.nan
    pd.DataFrame([{
        "fs_Hz": fs, "N_bins": len(x),
        "dominant_freq_Hz": f_dom, "max_to_mean_power_ratio": max_to_mean
    }]).to_csv(os.path.join(args.outdir, "table9b_psd_summary.csv"), index=False)

    # ACF (Figure 17 + Tables 10/10b)
    lags, r = acf(x, max_lag=int(2*fs))  # first 2 seconds
    ms = lags * (1000.0 / fs)
    plt.figure(figsize=(6,4))
    plt.plot(ms, r, lw=1)
    plt.xlabel("Lag [ms]"); plt.ylabel("ACF")
    plt.title("Figure 17. Autocorrelation (first 2 s)")
    plt.grid(True, alpha=0.3); plt.tight_layout()
    plt.savefig(os.path.join(args.outdir, "fig17_acf.png"), dpi=300)
    plt.close()

    pd.DataFrame({"lag_ms": ms, "acf": r}).to_csv(os.path.join(args.outdir, "table10_acf.csv"), index=False)

    try:
        idx = np.where(np.abs(r) < 0.05)[0]
        decor_ms = ms[int(idx[0])] if len(idx)>0 else np.nan
    except Exception:
        decor_ms = np.nan
    mean_abs = float(np.mean(np.abs(r)))
    pd.DataFrame([{
        "decorrelation_lag_ms(<0.05)": decor_ms,
        "mean_abs_acf_first_2s": mean_abs
    }]).to_csv(os.path.join(args.outdir, "table10b_acf_summary.csv"), index=False)

    print("Done. Outputs in:", args.outdir)

if __name__ == "__main__":
    main()
