#!/usr/bin/env python3
"""
Operational envelope: v_peak(λ, PW) heatmap for R||C driven by CCS (periodic, conservative).
We simulate period T=1/λ with ON=PW (I=I_limit), OFF=T-PW, sa tačnim RC rekurentnim ažuriranjem.
Compliance clamp: v capped to V_comp in ON.

Usage:
  python env_map_vpeak.py --I-limit 0.01 --V-comp 10 --R 1000 --C 1e-7 \
      --lambda-min 0.5 --lambda-max 10 --lambda-steps 30 \
      --pw-min 50 --pw-max 1000 --pw-steps 30 \
      --dt-us 50 --periods 200 --outdir figures
"""
import argparse, os, numpy as np, pandas as pd
import matplotlib.pyplot as plt

def simulate_vpeak(I, Vc, R, C, lam, PW_us, dt_us=50, periods=200):
    T = 1.0/lam; PW = PW_us * 1e-6; off = max(0.0, T - PW)
    v = 0.0; vmax = 0.0
    a_dt = lambda dt: np.exp(-dt/(R*C))
    for _ in range(periods):
        t = 0.0
        while t < PW:
            dt = min(PW - t, dt_us*1e-6)
            a = a_dt(dt); v = v*a + I*R*(1.0 - a)
            if v > Vc: v = Vc
            vmax = max(vmax, v); t += dt
        t = 0.0
        while t < off:
            dt = min(off - t, dt_us*1e-6)
            a = a_dt(dt); v = v*a; t += dt
    return vmax

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--I-limit", dest="I", type=float, required=True)
    ap.add_argument("--V-comp", dest="Vc", type=float, required=True)
    ap.add_argument("--R", dest="R", type=float, required=True)
    ap.add_argument("--C", dest="C", type=float, required=True)
    ap.add_argument("--lambda-min", type=float, default=0.5)
    ap.add_argument("--lambda-max", type=float, default=10.0)
    ap.add_argument("--lambda-steps", type=int, default=30)
    ap.add_argument("--pw-min", type=int, default=50)
    ap.add_argument("--pw-max", type=int, default=1000)
    ap.add_argument("--pw-steps", type=int, default=30)
    ap.add_argument("--dt-us", dest="dt_us", type=float, default=50.0)
    ap.add_argument("--periods", dest="periods", type=int, default=200)
    ap.add_argument("--outdir", dest="outdir", required=True)
    args = ap.parse_args()

    lambdas = np.linspace(args.lambda_min, args.lambda_max, args.lambda_steps)
    pws = np.linspace(args.pw_min, args.pw_max, args.pw_steps)
    Z = np.zeros((len(pws), len(lambdas)))
    for i, pw in enumerate(pws):
        for j, lam in enumerate(lambdas):
            Z[i, j] = simulate_vpeak(args.I, args.Vc, args.R, args.C, lam, pw, dt_us=args.dt_us, periods=args.periods)

    os.makedirs(args.outdir, exist_ok=True)
    plt.figure(figsize=(7,4.8))
    im = plt.imshow(Z, origin="lower", aspect="auto",
                    extent=[lambdas.min(), lambdas.max(), pws.min(), pws.max()],
                    cmap="viridis")
    plt.colorbar(im, label="v_peak [V]")
    plt.contour(lambdas, pws, Z, levels=[0.95*args.Vc], colors="w", linewidths=1.0, linestyles="--")
    plt.xlabel("λ [Hz]"); plt.ylabel("PW [μs]")
    plt.title("Figure 23. Operational envelope: v_peak on R||C (CCS)")
    plt.tight_layout(); plt.savefig(os.path.join(args.outdir, "fig23_env_map_vpeak.png"), dpi=300); plt.close()

    df = pd.DataFrame(Z, index=[f"{int(p)}" for p in pws], columns=[f"{l:.3f}" for l in lambdas])
    df.index.name = "PW_us"; df.columns.name = "lambda_Hz"
    df.to_csv(os.path.join(args.outdir, "table18_env_map_vpeak.csv"))
    print("Done. Outputs in:", args.outdir)

if __name__ == "__main__":
    main()
