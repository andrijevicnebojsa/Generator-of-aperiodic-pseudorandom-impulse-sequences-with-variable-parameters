#!/usr/bin/env python3
"""
Compliance curve (Figure 21 + Table 14): delivered current vs load resistance.
Model: I_delivered = min(I_limit, V_comp / R_load).
Usage:
  python compliance_curve.py --I-limit 0.01 --V-comp 10.0 --Rmin 100 --Rmax 100000 \
      --points 200 --outdir figures
"""
import argparse, os, numpy as np, pandas as pd
import matplotlib.pyplot as plt

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--I-limit", dest="I_limit", type=float, required=True)
    ap.add_argument("--V-comp", dest="V_comp", type=float, required=True)
    ap.add_argument("--Rmin", dest="Rmin", type=float, default=100.0)
    ap.add_argument("--Rmax", dest="Rmax", type=float, default=1e5)
    ap.add_argument("--points", dest="points", type=int, default=200)
    ap.add_argument("--outdir", dest="outdir", required=True)
    args = ap.parse_args()

    R = np.logspace(np.log10(args.Rmin), np.log10(args.Rmax), args.points)
    I = np.minimum(args.I_limit, args.V_comp / R)

    os.makedirs(args.outdir, exist_ok=True)
    plt.figure(figsize=(6,4))
    plt.semilogx(R, I, lw=2)
    plt.axhline(args.I_limit, color="k", ls="--", lw=1, label="I_limit")
    plt.xlabel("R_load [Ω]"); plt.ylabel("I_delivered [A]")
    plt.title("Figure 21. Compliance curve")
    plt.grid(True, which="both", alpha=0.3); plt.legend(); plt.tight_layout()
    plt.savefig(os.path.join(args.outdir, "fig21_compliance_curve.png"), dpi=300); plt.close()

    pd.DataFrame({"R_load_ohm": R, "I_delivered_A": I}).to_csv(os.path.join(args.outdir, "table14_compliance_curve.csv"), index=False)
    print("Done. Outputs in:", args.outdir)

if __name__ == "__main__":
    main()
