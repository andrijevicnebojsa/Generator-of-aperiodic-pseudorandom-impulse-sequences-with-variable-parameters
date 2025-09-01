#!/usr/bin/env python3
"""
Bench-level simulation of CCS driving R||C with APPI pulse train (unipolar current during pulse).
Inputs: CSV of APPI events with columns time_s, pulse_width_us, or synthetic generation.
Outputs: bench_waveform.csv with columns time_s, v_V, i_A; plus Figure 19/20 style plots.

Usage examples:
  python bench_rc_load_sim.py --in data/fig1_pulse_train.csv --I-limit 0.01 --V-comp 10 \
      --R 1000 --C 1e-7 --dt-us 10 --duration 0.5 --outdir figures

  python bench_rc_load_sim.py --lambda 2 --duration 0.5 --pw-min 50 --pw-max 1000 \
      --I-limit 0.01 --V-comp 10 --R 1000 --C 1e-7 --dt-us 10 --outdir figures --seed 1
"""
import argparse, os, numpy as np, pandas as pd
import matplotlib.pyplot as plt

def load_or_generate(args):
    if args.in_csv:
        df = pd.read_csv(args.in_csv)
        return df[["time_s","pulse_width_us"]].to_numpy()
    # generate
    rng = np.random.default_rng(args.seed)
    t=0.0; T=[]; W=[]
    while t<args.duration:
        isi=rng.exponential(1.0/args.lambda_hz)
        t+=isi
        if t>args.duration: break
        W.append(int(rng.integers(args.pw_min_us, args.pw_max_us+1)))
        T.append(t)
    return np.column_stack([np.array(T), np.array(W)])

def simulate_waveform(events, I_limit, V_comp, R, C, dt_us, duration_s):
    dt = dt_us*1e-6
    N = int(np.ceil(duration_s/dt))+1
    t = np.arange(N)*dt
    i = np.zeros(N, dtype=float)
    for te, w_us in events:
        start = int(np.floor(te/dt))
        n = int(np.maximum(1, np.round(w_us*1e-6/dt)))
        i[start:start+n] += I_limit
    v = np.zeros(N, dtype=float)
    a = np.exp(-dt/(R*C)); b = R*(1.0 - a)
    for n in range(1, N):
        v[n] = a*v[n-1] + b*i[n-1]
        if v[n] > V_comp:
            v[n] = V_comp
    return t, i, v

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="in_csv", type=str, default=None)
    ap.add_argument("--lambda", dest="lambda_hz", type=float, default=None)
    ap.add_argument("--duration", dest="duration", type=float, required=True)
    ap.add_argument("--pw-min", dest="pw_min_us", type=int, default=None)
    ap.add_argument("--pw-max", dest="pw_max_us", type=int, default=None)
    ap.add_argument("--I-limit", dest="I_limit", type=float, required=True)
    ap.add_argument("--V-comp", dest="V_comp", type=float, required=True)
    ap.add_argument("--R", dest="R", type=float, required=True)
    ap.add_argument("--C", dest="C", type=float, required=True)
    ap.add_argument("--dt-us", dest="dt_us", type=float, default=10.0)
    ap.add_argument("--outdir", dest="outdir", required=True)
    ap.add_argument("--seed", dest="seed", type=int, default=1)
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    events = load_or_generate(args)
    t, i, v = simulate_waveform(events, args.I_limit, args.V_comp, args.R, args.C, args.dt_us, args.duration)
    pd.DataFrame({"time_s": t, "v_V": v, "i_A": i}).to_csv(os.path.join(args.outdir, "bench_waveform.csv"), index=False)

    plt.figure(figsize=(7,3)); plt.plot(t, v, lw=1)
    plt.xlabel("Time [s]"); plt.ylabel("Voltage [V]")
    plt.title("Figure 19. Load voltage v(t) under APPI")
    plt.grid(True, alpha=0.3); plt.tight_layout()
    plt.savefig(os.path.join(args.outdir, "fig19_load_voltage.png"), dpi=300); plt.close()

    plt.figure(figsize=(7,2.5)); plt.step(t, i, where="post", lw=1)
    plt.xlabel("Time [s]"); plt.ylabel("Current [A]")
    plt.title("Figure 20. Injected current I_in(t)")
    plt.grid(True, alpha=0.3); plt.tight_layout()
    plt.savefig(os.path.join(args.outdir, "fig20_injected_current.png"), dpi=300); plt.close()

    print("Done. Outputs in:", args.outdir)

if __name__ == "__main__":
    main()
