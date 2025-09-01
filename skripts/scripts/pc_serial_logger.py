#!/usr/bin/env python3
"""
PC Serial Logger: povezuje se na Arduino, šalje SET komande, asinhrono čita EV/BIP log i piše CSV.
Usage:
  python scripts/pc_serial_logger.py --port COM5 --baud 115200 --csv logs/events.csv \
     --lambda 2.0 --pwmin 50 --pwmax 1000 --seed analog --start
"""
import argparse, csv, sys, threading, time
from datetime import datetime
import serial

def reader_thread(ser: serial.Serial, writer):
    for line in ser:
        try:
            s = line.decode('utf-8', errors='replace').strip()
        except Exception:
            continue
        if not s:
            continue
        # print to console
        print(s)
        # try parse EV or BIP
        if s.startswith("EV,") or s.startswith("BIP,"):
            # dump raw line into CSV for simplicity
            writer.writerow([datetime.utcnow().isoformat(), s])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", required=True)
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--csv", required=True)
    ap.add_argument("--lambda", dest="lam", type=float, default=None)
    ap.add_argument("--pwmin", type=int, default=None)
    ap.add_argument("--pwmax", type=int, default=None)
    ap.add_argument("--seed", choices=["analog","fixed"], default=None)
    ap.add_argument("--seed_value", type=int, default=12345)
    ap.add_argument("--start", action="store_true")
    args = ap.parse_args()

    ser = serial.Serial(args.port, args.baud, timeout=1)
    time.sleep(0.3)

    csvfile = open(args.csv, "w", newline="", encoding="utf-8")
    writer = csv.writer(csvfile)
    writer.writerow(["utc_iso", "line"])

    def send(cmd):
        ser.write((cmd + "\n").encode("utf-8"))

    if args.lam is not None:
        send(f"SET,lambda,{args.lam}")
    if args.pwmin is not None:
        send(f"SET,pwmin,{args.pwmin}")
    if args.pwmax is not None:
        send(f"SET,pwmax,{args.pwmax}")
    if args.seed == "analog":
        send("SEED,analog")
    elif args.seed == "fixed":
        send(f"SEED,fixed,{args.seed_value}")

    if args.start:
        send("START")

    t = threading.Thread(target=reader_thread, args=(ser, writer), daemon=True)
    t.start()

    print("Press Ctrl+C to stop...")
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        try:
            send("STOP")
        except Exception:
            pass
        ser.close()
        csvfile.close()

if __name__ == "__main__":
    main()
