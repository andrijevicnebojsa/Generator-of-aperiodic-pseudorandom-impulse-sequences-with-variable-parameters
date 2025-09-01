#!/usr/bin/env python3
"""
Generate biphasic, charge-balanced APPI stimulation and RC load response.
Outputs:
  - ns_biphasic_waveform.csv (t_s, i_A, v_V)
  - Figure 25: fig25_current_biphasic.png
  - Figure 26: fig26_voltage_on_load.png

Usage:
  python neuro_biphasic_waveform.py --lambda 2 --duration 10 --I-phase 0.003 \
      --pw-us 200 --gap-us 50 --R 1000 --C 1e-7 --dt-us 10 --outdir figures --seed 42
"""
import argparse, os, numpy as np, pandas as pd
import matplotlib.pyplot as plt

def make_events(lambda_hz, duration_s, rng):
    t = 0.0; T = []
    while t < duration_s:
        isi = rng.exponential(1.0/lambda_hz); t += isi
        if t > duration_s: break
        T.append(t)
    return np.array(T)

def simulate(lambda_hz, duration_s, I_phase, pw_us, gap_us, R, C, dt_us, seed):
    rng = np.random.default_rng(seed)
    T_events = make_events(lambda_hz, duration_s, rng)
    dt = dt_us * 1e-6
    N = int(np.ceil(duration_s / dt)) + 1
    t = np.arange(N) * dt
    i = np.zeros(N, dtype=float)
    for te in T_events:
        start = int(np.floor(te / dt))
        pw_n = int(np.round(pw_us*1e-6 / dt))
        gap_n = int(np.round(gap_us*1e-6 / dt))
        i[start:start+pw_n] += I_phase        # cathodic
        s2 = start + pw_n + gap_n             # anodic
        i[s2:s2+pw_n] -= I_phase
    v = np.zeros(N, dtype=float)
    a = np.exp(-dt/(R*C)); b = R*(1.0 - a)
    for n in range(1, N): v[n] = a*v[n-1] + b*i[n-1]
    return t, i, v

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lambda", dest="lambda_hz", type=float, required=True)
    ap.add_argument("--duration", dest="duration_s", type=float, required=True)
    ap.add_argument("--I-phase", dest="I_phase", type=float, required=True)
    ap.add_argument("--pw-us", dest="pw_us", type=int, required=True)
    ap.add_argument("--gap-us", dest="gap_us", type=int, required=True)
    ap.add_argument("--R", dest="R", type=float, required=True)
    ap.add_argument("--C", dest="C", type=float, required=True)
    ap.add_argument("--dt-us", dest="dt_us", type=float, default=10.0)
    ap.add_argument("--outdir", dest="outdir", required=True)
    ap.add_argument("--seed", dest="seed", type=int, default=123)
    args = ap.parse_args()

    t, i, v = simulate(args.lambda_hz, args.duration_s, args.I_phase, args.pw_us,
                       args.gap_us, args.R, args.C, args.dt_us, args.seed)
    os.makedirs(args.outdir, exist_ok=True)
    pd.DataFrame({"time_s": t, "i_A": i, "v_V": v}).to_csv(os.path.join(args.outdir, "ns_biphasic_waveform.csv"), index=False)

    plt.figure(figsize=(7,2.6)); plt.plot(t, i, lw=1)
    plt.xlabel("Time [s]"); plt.ylabel("Current [A]")
    plt.title("Figure 25. Biphasic, charge-balanced current (APPI timing)")
    plt.grid(True, alpha=0.3); plt.tight_layout()
    plt.savefig(os.path.join(args.outdir, "fig25_current_biphasic.png"), dpi=300); plt.close()

    plt.figure(figsize=(7,2.6)); plt.plot(t, v, lw=1)
    plt.xlabel("Time [s]"); plt.ylabel("Voltage [V]")
    plt.title("Figure 26. Voltage on R||C during biphasic APPI")
    plt.grid(True, alpha=0.3); plt.tight_layout()
    plt.savefig(os.path.join(args.outdir, "fig26_voltage_on_load.png"), dpi=300); plt.close()
    print("Done. Outputs in:", args.outdir)

if __name__ == "__main__":
    main()
