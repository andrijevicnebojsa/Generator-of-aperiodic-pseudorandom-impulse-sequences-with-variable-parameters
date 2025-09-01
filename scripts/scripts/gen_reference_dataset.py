#!/usr/bin/env python3
"""
Generiše referentni skup (60 s) sa λ=2 Hz i PW∈[50,1000] µs.
Ispis: datasets/fig1_pulse_train.csv (event, t_schedule_s, pulse_width_us)
"""
import os, csv, math, random

def gen(lam_hz=2.0, pw_min=50, pw_max=1000, duration_s=60.0, seed=1001):
    random.seed(seed)
    t = 0.0
    ev = 0
    rows = []
    while t < duration_s:
        u = 1.0 - random.random()  # (0,1]
        dt = -math.log(u)/lam_hz
        t += dt
        if t >= duration_s: break
        pw = random.randint(pw_min, pw_max)
        ev += 1
        rows.append((ev, t, pw))
    return rows

def main():
    os.makedirs("datasets", exist_ok=True)
    rows = gen()
    with open("datasets/fig1_pulse_train.csv","w",newline="",encoding="utf-8") as f:
        w=csv.writer(f); w.writerow(["event","t_schedule_s","pulse_width_us"])
        for r in rows: w.writerow(r)
    print("Wrote datasets/fig1_pulse_train.csv with", len(rows), "events")

if __name__ == "__main__":
    main()
