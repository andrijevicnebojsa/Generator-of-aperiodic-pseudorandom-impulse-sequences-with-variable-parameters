#!/usr/bin/env python3
"""
Compliance kriva: isporučena struja vs R, uz limit I_limit i V_comp (DC aproksimacija).
Out: tables/table14_compliance_curve.csv, figures/fig21_compliance_curve.png
"""
import os, csv, numpy as np, matplotlib.pyplot as plt
os.makedirs("tables", exist_ok=True); os.makedirs("figures", exist_ok=True)

I_limit = 0.01
V_comp = 10.0
# log-raspon 100 Ω – 100 kΩ
Rvals = np.logspace(2,5, num=200)
Idel = np.minimum(I_limit, V_comp/Rvals)

with open("tables/table14_compliance_curve.csv","w",newline="",encoding="utf-8") as f:
  w=csv.writer(f); w.writerow(["R_load_ohm","I_delivered_A"])
  for R, I in zip(Rvals, Idel):
    w.writerow([R, I])

plt.figure()
plt.loglog(Rvals, Idel)
plt.xlabel("R_load [Ω]"); plt.ylabel("I_delivered [A]"); plt.grid(True, which="both")
plt.title("Compliance curve (delivered current vs R)")
plt.savefig("figures/fig21_compliance_curve.png", dpi=160)
print("Compliance curve done.")
