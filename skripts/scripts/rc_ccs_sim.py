#!/usr/bin/env python3
"""
RC (R||C) + idealni CCS (I_limit, V_comp) simulacija s korakom dt=1 µs, prozor=0.5 s.
Ulaz: datasets/fig1_pulse_train.csv
Izlaz: figures/fig19_rc_voltage_apppi.png, figures/fig20_ccs_current_apppi.png,
       tables/table11_load_ccs_params.csv, tables/table12_waveform_metrics_first_pulse.csv
"""
import os, csv
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

os.makedirs("tables", exist_ok=True)
os.makedirs("figures", exist_ok=True)

# parametri iz rada
Vsupply = 12.0
I_limit = 0.01    # 10 mA
V_comp = 10.0
R = 1000.0
C = 1e-7
dt = 1e-6
window_s = 0.5

# snimi parametre
with open("tables/table11_load_ccs_params.csv","w",newline="",encoding="utf-8") as f:
  w=csv.writer(f); w.writerow(["V_supply_V","I_limit_A","V_compliance_V","R_load_ohm","C_load_F","dt_us","sim_window_s"])
  w.writerow([Vsupply, I_limit, V_comp, R, C, 1.0, window_s])

df = pd.read_csv("datasets/fig1_pulse_train.csv")
events = list(zip(df["t_schedule_s"].values, df["pulse_width_us"].values))

N = int(window_s/dt)
t = np.arange(N)*dt
i_in = np.zeros(N, dtype=float)

# upis struje (0 ili I_limit) tokom trajanja impulsa
for ts, pwu in events:
  start = int(ts/dt)
  dur = max(1, int((pwu/1e6)/dt))
  if start >= N: break
  end = min(N, start+dur)
  i_in[start:end] = I_limit

# simulacija napona na R||C: i_in ide kroz CCS -> node V ograničen V_comp
v = np.zeros(N, dtype=float)
for k in range(1, N):
  # idealni CCS pokušava I_limit, ali ako R||C traži veći napon od komplians, ograniči
  # Jednostavna Eulerska integracija: C*dv/dt + v/R = i_in
  dv = (i_in[k] - v[k-1]/R) * (dt / C)
  v[k] = v[k-1] + dv
  if v[k] > V_comp: v[k] = V_comp
  if v[k] < 0: v[k] = 0.0

# metrika prvog impulsa
first = None
for ts, pwu in events:
  if ts < window_s:
    first = (ts, pwu); break
if first is not None:
  s = int(first[0]/dt); e = min(N, s+max(1,int((first[1]/1e6)/dt)))
  vmax = float(np.max(v[s:e]))
  # rise 10-90%
  v10 = 0.1*vmax; v90 = 0.9*vmax
  def find_cross(arr, start, end, thr):
    for kk in range(start, end):
      if arr[kk] >= thr: return kk
    return end
  k10 = find_cross(v, s, e, v10); k90 = find_cross(v, s, e, v90)
  rise_us = (k90 - k10)*dt*1e6
  droop_v = float(v[s] - v[e-1]) if e-1 > s else 0.0
  energy_mJ = float(np.sum( v[s:e]**2 / R * dt )*1000.0)
  with open("tables/table12_waveform_metrics_first_pulse.csv","w",newline="",encoding="utf-8") as f:
    w=csv.writer(f); w.writerow(["pulse_start_s","pulse_width_us","v_max_V","rise_time_10_90_us","droop_V","energy_pulse_mJ"])
    w.writerow([first[0], first[1], vmax, rise_us, droop_v, energy_mJ])

# crteži
plt.figure(); plt.plot(t, v); plt.xlim(0, window_s)
plt.xlabel("t [s]"); plt.ylabel("v(t) [V]"); plt.grid(True)
plt.title("Load voltage v(t) under APPI")
plt.savefig("figures/fig19_rc_voltage_apppi.png", dpi=160)

plt.figure(); plt.step(t, i_in, where="post"); plt.xlim(0, window_s)
plt.xlabel("t [s]"); plt.ylabel("I_in(t) [A]"); plt.grid(True)
plt.title("Injected current (CCS)")
plt.savefig("figures/fig20_ccs_current_apppi.png", dpi=160)
print("RC+CCS sim done.")
