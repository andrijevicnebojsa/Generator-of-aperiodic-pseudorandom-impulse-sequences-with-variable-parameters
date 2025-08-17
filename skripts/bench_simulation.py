# bench_simulation.py
# Reproduces RC|| load waveform for APPI pulses with ideal CCS.
import numpy as np, pandas as pd

V_supply=12.0; I_lim=0.010; Vcomp=10.0; R=1000.0; C=100e-9
dt=1e-6; window=0.5
df=pd.read_csv('fig1_pulse_train.csv')
s=df[df['time_s']<=window].copy()
if s.empty:
    s=pd.DataFrame({'time_s':[0.05],'pulse_width_us':[800]})
N=int(np.ceil(window/dt)); t=np.arange(N)*dt; I=np.zeros(N)
for ts,wus in zip(s['time_s'], s['pulse_width_us']):
    i0=int(ts/dt); w=max(1,int(np.ceil((wus*1e-6)/dt)))
    I[i0:i0+w]=I_lim
v=np.zeros(N)
for k in range(1,N):
    i_drive = I[k-1] if v[k-1] < Vcomp else 0.0
    v[k]=v[k-1]+((i_drive - v[k-1]/R)/C)*dt
pd.DataFrame({'t_s':t,'I_A':I,'V_load_V':v}).to_csv('bench_waveform.csv', index=False)
print('Saved bench_waveform.csv')
