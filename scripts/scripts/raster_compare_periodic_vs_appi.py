#!/usr/bin/env python3
"""
Raster comparison: periodic (2 Hz) vs APPI (~2 Hz) for equal duration.
Outputs:
  - fig27_raster_compare.png
Usage:
  python raster_compare_periodic_vs_appi.py --duration 10 --lambda 2.0 --outdir figures --seed 7
"""
import argparse, os, numpy as np
import matplotlib.pyplot as plt

def make_appi(lam, dur, rng):
    t=0.0; T=[]
    while t<dur:
        isi=rng.exponential(1.0/lam)
        t+=isi
        if t>dur: break
        T.append(t)
    return np.array(T)

def make_periodic(rate_hz, dur):
    return np.arange(1.0/rate_hz, dur+1e-9, 1.0/rate_hz)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--duration", dest="duration_s", type=float, required=True)
    ap.add_argument("--lambda", dest="lambda_hz", type=float, default=2.0)
    ap.add_argument("--outdir", dest="outdir", required=True)
    ap.add_argument("--seed", dest="seed", type=int, default=7)
    args = ap.parse_args()
    os.makedirs(args.outdir, exist_ok=True)
    rng = np.random.default_rng(args.seed)
    T_appi = make_appi(args.lambda_hz, args.duration_s, rng)
    T_per = make_periodic(args.lambda_hz, args.duration_s)

    plt.figure(figsize=(7,3))
    for t in T_per:
        plt.plot([t,t],[0.1,0.9], color="tab:blue", lw=0.8)
    for t in T_appi:
        plt.plot([t,t],[1.1,1.9], color="tab:orange", lw=0.8)
    plt.yticks([0.5,1.5], ["Periodic (2 Hz)","APPI (~2 Hz)"])
    plt.ylim(0,2.2); plt.xlim(0,args.duration_s)
    plt.xlabel("Time [s]"); plt.title("Figure 27. Raster: periodic vs APPI timing")
    plt.grid(True, axis="x", alpha=0.25); plt.tight_layout()
    plt.savefig(os.path.join(args.outdir, "fig27_raster_compare.png"), dpi=300); plt.close()
    print("Done. Outputs in:", args.outdir)

if __name__ == "__main__":
    main()
