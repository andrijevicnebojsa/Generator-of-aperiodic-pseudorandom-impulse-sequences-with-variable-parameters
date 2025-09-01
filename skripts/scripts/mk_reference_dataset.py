#!/usr/bin/env python3
"""
Generate a reference APPI dataset: Poisson-distributed inter-spike intervals (ISI)
with rate lambda_Hz and pulse widths uniformly distributed in [pw_min_us, pw_max_us].

Output CSV has columns: time_s, pulse_width_us

Usage:
  python mk_reference_dataset.py --lambda 2.0 --duration 60 \
      --pw-min 50 --pw-max 1000 --seed 123 \
      --out data/fig1_pulse_train.csv
"""
import argparse, numpy as np, pandas as pd, os

def generate(lambda_hz: float, duration_s: float, pw_min_us: int, pw_max_us: int, rng) -> pd.DataFrame:
    times = []
    widths = []
    t = 0.0
    while t < duration_s:
        isi = rng.exponential(1.0 / lambda_hz)
        t += isi
        if t > duration_s:
            break
        w_us = rng.integers(pw_min_us, pw_max_us + 1)
        times.append(t)
        widths.append(int(w_us))
    return pd.DataFrame({"time_s": times, "pulse_width_us": widths})

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lambda", dest="lambda_hz", type=float, required=True)
    ap.add_argument("--duration", dest="duration_s", type=float, required=True)
    ap.add_argument("--pw-min", dest="pw_min_us", type=int, required=True)
    ap.add_argument("--pw-max", dest="pw_max_us", type=int, required=True)
    ap.add_argument("--seed", dest="seed", type=int, default=123)
    ap.add_argument("--out", dest="out_csv", type=str, required=True)
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    df = generate(args.lambda_hz, args.duration_s, args.pw_min_us, args.pw_max_us, rng)
    os.makedirs(os.path.dirname(args.out_csv), exist_ok=True)
    df.to_csv(args.out_csv, index=False)
    print(f"Wrote {len(df)} events to {args.out_csv}")

if __name__ == "__main__":
    main()
