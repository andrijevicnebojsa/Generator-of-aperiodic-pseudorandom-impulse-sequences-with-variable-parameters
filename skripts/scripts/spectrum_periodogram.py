#!/usr/bin/env python3
"""
Periodogram binned pulse-train (1 ms raster)
I/O:
  in: datasets/fig1_pulse_train.csv
  out: figures/fig16_periodogram_1msbin.png, tables/table09_psd_samples.csv, tables/table09b_psd_summary.csv
"""
import os, csv
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from numpy.fft import rfft, rfftfreq

os.makedirs("tables", exist_ok=True)
os.makedirs("figures", exist_ok=True)

df = pd.read_csv("datasets/fig1_pulse_train.csv")
t = df["t_schedule_s"].values
pw_us = df["pulse_width_us"].values

# 1 kHz raster, trajanje
fs = 1000.0
dt = 1.0/fs
T = float(t[-1])
N = int(np.ceil(T*fs))+1
x = np.zeros(N, dtype=float)

# popuni binove tokom trajanja impulsa (min 1 bin)
for ti, pwu in zip(t, pw_us):
  start = int(np.floor(ti*fs))
  bins = max(1, int(np.ceil((pwu/1e6)*fs)))
  end = min(N, start+bins)
  x[start:end] += 1.0

# ukloni DC
x = x - np.mean(x)

# periodogram
X = np.abs(rfft(x))**2
f = rfftfreq(N, d=dt)

# snimi nekoliko uzoraka za tabelu i sažetak
sel_idx = np.linspace(0, len(f)-1, num=min(600, len(f)), dtype=int)
with open("tables/table09_psd_samples.csv","w",newline="",encoding="utf-8") as fcsv:
  w=csv.writer(fcsv); w.writerow(["freq_Hz","power"])
  for i in sel_idx:
    w.writerow([f[i], X[i]])

dom_idx = np.argmax(X[1:]) + 1 if len(X)>1 else 0
summary = {
  "fs_Hz": fs,
  "N_bins": N,
  "dominant_freq_Hz": f[dom_idx] if len(f)>dom_idx else 0.0,
  "max_to_mean_power_ratio": float(np.max(X)/ (np.mean(X)+1e-12))
}
with open("tables/table09b_psd_summary.csv","w",newline="",encoding="utf-8") as fcsv:
  w=csv.writer(fcsv); w.writerow(["fs_Hz","N_bins","dominant_freq_Hz","max_to_mean_power_ratio"])
  w.writerow([summary["fs_Hz"], summary["N_bins"], summary["dominant_freq_Hz"], summary["max_to_mean_power_ratio"]])

plt.figure()
plt.semilogy(f[1:], X[1:])
plt.xlabel("Frequency [Hz]"); plt.ylabel("Power")
plt.title("Periodogram (1 ms binning)")
plt.grid(True)
plt.savefig("figures/fig16_periodogram_1msbin.png", dpi=160)
print("Periodogram done.")
