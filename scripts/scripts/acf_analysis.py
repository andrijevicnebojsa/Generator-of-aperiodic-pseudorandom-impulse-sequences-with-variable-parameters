#!/usr/bin/env python3
"""
ACF analitika nad binned nizom (1 ms), out tabele i slika.
Out:
  figures/fig17_acf_first2s.png
  tables/table10_acf_samples.csv
  tables/table10b_acf_summary.csv
"""
import os, csv
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

os.makedirs("tables", exist_ok=True)
os.makedirs("figures", exist_ok=True)

df = pd.read_csv("datasets/fig1_pulse_train.csv")
t = df["t_schedule_s"].values
pw = df["pulse_width_us"].values

fs = 1000.0; dt=1.0/fs
T=float(t[-1]); N=int(np.ceil(T*fs))+1
x=np.zeros(N, dtype=float)
for ti, pwu in zip(t, pw):
  start=int(np.floor(ti*fs))
  bins=max(1, int(np.ceil((pwu/1e6)*fs)))
  x[start:start+bins] += 1.0

x = x - np.mean(x)
acf_full = np.correlate(x, x, mode='full')
mid = len(acf_full)//2
acf = acf_full[mid:] / (acf_full[mid] + 1e-12)

# snimi uzorke
with open("tables/table10_acf_samples.csv","w",newline="",encoding="utf-8") as f:
  w=csv.writer(f); w.writerow(["lag_ms","acf"])
  for k, val in enumerate(acf[:2001]):  # 0..2000 ms
    w.writerow([k, float(val)])

# metrika
def first_decorrelation(acf, thr=0.05):
  for k in range(1, len(acf)):
    if abs(acf[k]) < thr:
      return k
  return None

dec_lag = first_decorrelation(acf, 0.05)
win = int(2.0*fs)
mean_abs = float(np.mean(np.abs(acf[1:win])))

with open("tables/table10b_acf_summary.csv","w",newline="",encoding="utf-8") as f:
  w=csv.writer(f); w.writerow(["decorrelation_lag_ms(<0.05)","mean_abs_acf_first_2s"])
  w.writerow([dec_lag if dec_lag is not None else -1, mean_abs])

# plot
plt.figure()
tms = np.arange(0, 2001)
plt.plot(tms, acf[:2001])
plt.xlabel("Lag [ms]"); plt.ylabel("ACF")
plt.grid(True); plt.title("Autocorrelation (first 2 s)")
plt.savefig("figures/fig17_acf_first2s.png", dpi=160)
print("ACF done.")
