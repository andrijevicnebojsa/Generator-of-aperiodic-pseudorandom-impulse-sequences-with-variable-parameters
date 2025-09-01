#!/usr/bin/env python3
"""
Mapa v_peak(λ, PW) na R||C sa CCS, konzervativno: periodičan režim.
Simulacija više perioda po tački mreže (brza diskretna).
Out: tables/table18_operational_envelope_grid.csv, figures/fig27_operational_envelope.png
"""
import os, csv
import numpy as np
import matplotlib.pyplot as plt

os.makedirs("tables", exist_ok=True)
os.makedirs("figures", exist_ok=True)

R=1000.0; C=1e-7; V_comp=10.0; I_limit=0.01
dt=1e-6

lams = np.linspace(1, 8, 8)     # Hz
pws  = np.array([50,100,200,300,400,500,800,1000])  # µs

def simulate_periodic(lam, pw_us):
    T = 1.0/max(1e-6, lam)
    samples = int(np.ceil(5*T/dt))  # 5 perioda
    v = 0.0; vmax=0.0
    for k in range(samples):
        t = k*dt
        in_pulse = (t % T) < (pw_us/1e6)
        i_in = I_limit if in_pulse else 0.0
        dv = (i_in - v/R) * (dt/C)
        v = v + dv
        if v > V_comp: v = V_comp
        if v < 0: v = 0.0
        if v > vmax: vmax = v
    return vmax

grid = np.zeros((len(lams), len(pws)))
for i, lam in enumerate(lams):
    for j, pw in enumerate(pws):
        grid[i,j] = simulate_periodic(lam, pw)

with open("tables/table18_operational_envelope_grid.csv","w",newline="",encoding="utf-8") as f:
  w=csv.writer(f); 
  w.writerow(["lambda_Hz"] + [f"PW_{pw}_us" for pw in pws])
  for i, lam in enumerate(lams):
    w.writerow([lam] + [grid[i,j] for j in range(len(pws))])

plt.figure()
extent = [pws.min(), pws.max(), lams.min(), lams.max()]
plt.imshow(grid, origin="lower", aspect="auto", extent=extent, cmap="viridis")
plt.colorbar(label="v_peak [V]")
plt.contour(np.linspace(pws.min(), pws.max(), len(pws)),
            np.linspace(lams.min(), lams.max(), len(lams)),
            grid, levels=[0.95*V_comp], colors="w", linewidths=1.0)
plt.xlabel("PW [µs]"); plt.ylabel("λ [Hz]")
plt.title("Operational envelope: v_peak on R||C")
plt.savefig("figures/fig27_operational_envelope.png", dpi=160)
print("Operational envelope done.")
