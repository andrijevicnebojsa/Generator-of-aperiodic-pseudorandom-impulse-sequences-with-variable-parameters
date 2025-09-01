#!/usr/bin/env python3
"""
Robusnost po semenu: 5 semena ~30 s; K–S p-vrednosti za ISI i PW.
Out: tables/table23_robustness_by_seed.csv, figures/fig28_robustness_pvals.png
"""
import os, csv, math, random
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt

os.makedirs("tables", exist_ok=True)
os.makedirs("figures", exist_ok=True)

def gen(lam_hz, pw_min, pw_max, duration_s, seed):
    random.seed(seed)
    t=0.0; rows=[]
    while t<duration_s:
        u = 1.0 - random.random()
        dt = -math.log(u)/lam_hz
        t += dt
        if t>=duration_s: break
        pw = random.randint(pw_min,pw_max)
        rows.append((t,pw))
    return rows

seeds=[1001,1002,1003,1004,1005]
records=[]
for s in seeds:
    rows=gen(2.0,50,1000,30.0,s)
    t=np.array([r[0] for r in rows]); pw=np.array([r[1] for r in rows])
    isi=np.diff(np.concatenate([[0.0], t]))
    lam_mle=1.0/np.mean(isi)
    D1,p1=stats.kstest(isi,'expon', args=(0,1.0/lam_mle))
    a,b=int(pw.min()),int(pw.max())
    D2,p2=stats.kstest(pw,'uniform', args=(a,b-a))
    records.append((s, len(rows), lam_mle, D1,p1,D2,p2))

with open("tables/table23_robustness_by_seed.csv","w",newline="",encoding="utf-8") as f:
    w=csv.writer(f); w.writerow(["seed","n_events","lambda_mle_Hz","KS_ISI_D","KS_ISI_p","KS_PW_D","KS_PW_p"])
    for r in records: w.writerow(r)

plt.figure()
plt.plot(seeds, [r[4] for r in records], marker='o', label="p(ISI)")
plt.plot(seeds, [r[6] for r in records], marker='s', label="p(PW)")
plt.axhline(0.05, color='r', linestyle='--', label='α=0.05')
plt.xlabel("seed"); plt.ylabel("p-value"); plt.grid(True); plt.legend()
plt.title("Robustness by seed")
plt.savefig("figures/fig28_robustness_pvals.png", dpi=160)
print("Robustness done.")
