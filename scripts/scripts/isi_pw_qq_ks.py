#!/usr/bin/env python3
"""
Wrapper that calls the same analysis as isi_analysis.py but keeps a single entry point
for Figures 13–15 and Tables 7–8.
Usage:
  python isi_pw_qq_ks.py --in data/fig1_pulse_train.csv --outdir figures --alpha 0.05
"""
import argparse, subprocess, sys, os

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="in_csv", required=True)
    ap.add_argument("--outdir", dest="outdir", required=True)
    ap.add_argument("--alpha", dest="alpha", default="0.05")
    args = ap.parse_args()
    cmd = [sys.executable, os.path.join(os.path.dirname(__file__), "isi_analysis.py"),
           "--in", args.in_csv, "--outdir", args.outdir, "--alpha", args.alpha]
    print("Running:", " ".join(cmd))
    subprocess.check_call(cmd)

if __name__ == "__main__":
    main()
