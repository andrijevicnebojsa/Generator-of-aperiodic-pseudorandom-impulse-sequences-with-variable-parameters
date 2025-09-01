#!/usr/bin/env python3
"""
Učitava datasets/fig1_pulse_train.csv i radi:
- MLE λ iz ISI
- K–S testovi za ISI~Exp(λ) i PW~Uniform[min,max]
- QQ dijagrami i CDF (PNG)
- Tabele: tables/table07_params_descriptives.csv, tables/table08_ks_results.csv
"""
import os, csv, math
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt

os.makedirs("tables", exist_ok=True)
os.makedirs("figures", exist_ok=True)

df = pd.read_csv("datasets/fig1_pulse_train.csv")
t = df["t_schedule_s"].values
pw = df["pulse_width_us"].values
isi = np.diff(np.concatenate([[0.0], t]))

# MLE lambda = 1/mean(isi)
lam_mle = 1.0/np.mean(isi)
pw_min, pw_max = int(pw.min()), int(pw.max())
pw_mean, pw_std = float(np.mean(pw)), float(np.std(pw, ddof=1))

# Deskriptive
with open("tables/table07_params_descriptives.csv","w",newline="",encoding="utf-8") as f:
    w=csv.writer(f)
    w.writerow(["lambda_mle_Hz","isi_mean_s","isi_std_s","pw_min_us","pw_max_us","pw_mean_us","pw_std_us","duration_s","num_events"])
    w.writerow([lam_mle, np.mean(isi), np.std(isi, ddof=1), pw_min, pw_max, pw_mean, pw_std, t[-1], len(df)])

# KS: ISI vs Exp(lam_mle)
D1, p1 = stats.kstest(isi, 'expon', args=(0, 1.0/lam_mle))
# KS: PW vs Uniform[min,max]
D2, p2 = stats.kstest(pw, 'uniform', args=(pw_min, pw_max - pw_min))

with open("tables/table08_ks_results.csv","w",newline="",encoding="utf-8") as f:
    w=csv.writer(f)
    w.writerow(["test","D","p_value","n"])
    w.writerow(["KS ISI vs Exp(lam_mle)", D1, p1, len(isi)])
    w.writerow(["KS PW vs Uniform[min,max]", D2, p2, len(pw)])

# ISI CDF emp vs theory
x = np.sort(isi)
cdf_emp = np.arange(1, len(x)+1)/len(x)
cdf_the = 1 - np.exp(-lam_mle * x)
plt.figure()
plt.plot(x, cdf_emp, label="Empirical")
plt.plot(x, cdf_the, label=f"Theory Exp(λ={lam_mle:.3f})")
plt.xlabel("ISI [s]"); plt.ylabel("CDF"); plt.legend(); plt.grid(True)
plt.title("ISI CDF: empirical vs theoretical")
plt.savefig("figures/fig13_isi_cdf_emp_vs_theory.png", dpi=160)

# QQ ISI vs Exp
q_emp = np.quantile(x, np.linspace(0.01,0.99,99))
q_the = stats.expon.ppf(np.linspace(0.01,0.99,99), scale=1.0/lam_mle)
plt.figure()
plt.scatter(q_the, q_emp, s=8)
lims=[0,max(q_the.max(), q_emp.max())]
plt.plot(lims, lims, 'k--')
plt.xlabel("Theoretical quantiles (Exp)"); plt.ylabel("Empirical quantiles (ISI)")
plt.title("ISI QQ vs Exponential")
plt.grid(True)
plt.savefig("figures/fig14_isi_qq_exp.png", dpi=160)

# QQ PW vs Uniform
q_emp_pw = np.quantile(pw, np.linspace(0.01,0.99,99))
q_the_pw = stats.uniform.ppf(np.linspace(0.01,0.99,99), loc=pw_min, scale=pw_max-pw_min)
plt.figure()
plt.scatter(q_the_pw, q_emp_pw, s=8)
lims=[pw_min, pw_max]
plt.plot(lims, lims, 'k--')
plt.xlabel("Theoretical quantiles (Uniform)"); plt.ylabel("Empirical quantiles (PW)")
plt.title("PW QQ vs Uniform")
plt.grid(True)
plt.savefig("figures/fig15_pw_qq_uniform.png", dpi=160)

print("Stats done.")
