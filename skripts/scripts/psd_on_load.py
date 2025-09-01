#!/usr/bin/env python3
"""
Compute PSD of load voltage (Figure 22 + Table 15) by aggregating into 1 ms bins.
Input CSV is expected to contain columns: time_s, v_V (or 'voltage_V').
Usage:
  python psd_on_load.py --in data/bench_waveform.csv --outdir figures
"""
import argparse, os, numpy as np, pandas as pd
import matplotlib.pyplot as plt

def resample_ms(df):
    if "v_V" not in df.columns and "voltage_V" in df.columns:
        df = df.rename(columns={"voltage_V": "v_V"})
    t = df["time_s"].to_numpy(); v = df["v_V"].to_numpy()
    t0, t1 = float(t.min()), float(t.max())
    fs = 1000.0
    n = int(np.floor((t1 - t0) * fs)) + 1
    s = pd.DataFrame({"time_s": t, "v_V": v})
    s["bin"] = np.floor((s["time_s"] - t0) * fs).astype(int)
    g = s.groupby("bin")["v_V"].mean()
    x = np.zeros(n); idx = g.index.to_numpy()
    idx = idx[(idx >= 0) & (idx < n)]; x[idx] = g.loc[idx]
    return x, fs

def periodogram(x, fs):
    x0 = x - np.mean(x)
    X = np.fft.rfft(x0)
    P = (np.abs(X)**2) / len(x0)
    f = np.fft.rfftfreq(len(x0), d=1.0/fs)
    return f, P

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="in_csv", required=True)
    ap.add_argument("--outdir", dest="outdir", required=True)
    args = ap.parse_args()
    os.makedirs(args.outdir, exist_ok=True)
    df = pd.read_csv(args.in_csv)
    x, fs = resample_ms(df)
    f, P = periodogram(x, fs)
    plt.figure(figsize=(6,4))
    plt.semilogy(f[1:], P[1:] + 1e-24)
    plt.xlabel("Frequency [Hz]"); plt.ylabel("Power")
    plt.title("Figure 22. PSD of load voltage (1 ms bins)")
    plt.grid(True, which="both", alpha=0.3); plt.tight_layout()
    plt.savefig(os.path.join(args.outdir, "fig22_psd_load.png"), dpi=300); plt.close()
    pd.DataFrame({"freq_Hz": f, "power": P}).to_csv(os.path.join(args.outdir, "table15_psd_load.csv"), index=False)
    print("Done. Outputs in:", args.outdir)

if __name__ == "__main__":
    main()
