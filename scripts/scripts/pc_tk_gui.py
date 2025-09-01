#!/usr/bin/env python3
"""
Tkinter GUI: konekcija, SET parametri, live log prikaz, brza statistika.
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import serial, threading, queue, time
import csv, os

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("APPI Controller")
        self.geometry("780x520")
        self.ser = None
        self.rxq = queue.Queue()
        self.running = False
        self.log_writer = None
        self.csvpath = None

        self._build()

    def _build(self):
        frm = ttk.Frame(self); frm.pack(fill="both", expand=True, padx=8, pady=8)

        top = ttk.Frame(frm); top.pack(fill="x")
        ttk.Label(top, text="Port:").pack(side="left")
        self.port = ttk.Entry(top, width=10); self.port.insert(0, "COM5"); self.port.pack(side="left", padx=4)
        ttk.Label(top, text="Baud:").pack(side="left")
        self.baud = ttk.Entry(top, width=8); self.baud.insert(0, "115200"); self.baud.pack(side="left", padx=4)
        ttk.Button(top, text="Connect", command=self.connect).pack(side="left", padx=6)
        ttk.Button(top, text="Disconnect", command=self.disconnect).pack(side="left")

        sep = ttk.Separator(frm); sep.pack(fill="x", pady=6)

        p = ttk.Frame(frm); p.pack(fill="x")
        self.var_lambda = tk.StringVar(value="2.0")
        self.var_pwmin = tk.StringVar(value="50")
        self.var_pwmax = tk.StringVar(value="1000")
        ttk.Label(p, text="λ [Hz]:").grid(row=0, column=0, sticky="e")
        ttk.Entry(p, textvariable=self.var_lambda, width=8).grid(row=0, column=1, sticky="w", padx=4)
        ttk.Label(p, text="PWmin [µs]:").grid(row=0, column=2, sticky="e")
        ttk.Entry(p, textvariable=self.var_pwmin, width=8).grid(row=0, column=3, sticky="w", padx=4)
        ttk.Label(p, text="PWmax [µs]:").grid(row=0, column=4, sticky="e")
        ttk.Entry(p, textvariable=self.var_pwmax, width=8).grid(row=0, column=5, sticky="w", padx=4)
        ttk.Button(p, text="Apply", command=self.apply).grid(row=0, column=6, padx=8)

        p2 = ttk.Frame(frm); p2.pack(fill="x", pady=4)
        ttk.Button(p2, text="Seed (analog)", command=lambda: self.send("SEED,analog")).pack(side="left")
        self.seed_fixed = ttk.Entry(p2, width=12); self.seed_fixed.insert(0, "12345"); self.seed_fixed.pack(side="left", padx=4)
        ttk.Button(p2, text="Seed (fixed)", command=self.seed_fixed_cmd).pack(side="left", padx=4)
        ttk.Button(p2, text="START", command=lambda: self.send("START")).pack(side="left", padx=8)
        ttk.Button(p2, text="STOP", command=lambda: self.send("STOP")).pack(side="left")

        p3 = ttk.Frame(frm); p3.pack(fill="x", pady=4)
        ttk.Button(p3, text="Choose CSV...", command=self.choose_csv).pack(side="left")
        self.csv_label = ttk.Label(p3, text="No CSV"); self.csv_label.pack(side="left", padx=6)

        txtf = ttk.Frame(frm); txtf.pack(fill="both", expand=True, pady=8)
        self.txt = tk.Text(txtf, height=20)
        self.txt.pack(fill="both", expand=True)

        self.after(100, self.poll_rx)

    def connect(self):
        try:
            port = self.port.get()
            baud = int(self.baud.get())
            self.ser = serial.Serial(port, baud, timeout=1)
            self._reader = threading.Thread(target=self.reader, daemon=True); self._reader.start()
            messagebox.showinfo("OK", f"Connected to {port}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def disconnect(self):
        try:
            if self.ser:
                self.ser.close()
                self.ser = None
                messagebox.showinfo("OK", "Disconnected")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def send(self, cmd):
        if not self.ser:
            messagebox.showwarning("No conn", "Not connected")
            return
        self.ser.write((cmd+"\n").encode("utf-8"))

    def apply(self):
        try:
            lam = float(self.var_lambda.get())
            pmin = int(self.var_pwmin.get())
            pmax = int(self.var_pwmax.get())
        except ValueError:
            messagebox.showerror("Bad input", "Numbers expected")
            return
        self.send(f"SET,lambda,{lam}")
        self.send(f"SET,pwmin,{pmin}")
        self.send(f"SET,pwmax,{pmax}")

    def seed_fixed_cmd(self):
        try:
            s = int(self.seed_fixed.get())
        except ValueError:
            messagebox.showerror("Bad seed", "Integer expected")
            return
        self.send(f"SEED,fixed,{s}")

    def choose_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile="events.csv")
        if path:
            self.csvpath = path
            self.csv_label.config(text=os.path.basename(path))
            self.log_file = open(path, "w", newline="", encoding="utf-8")
            self.log_writer = csv.writer(self.log_file)
            self.log_writer.writerow(["utc_iso", "line"])

    def reader(self):
        try:
            for line in self.ser:
                s = line.decode("utf-8", errors="replace").strip()
                self.rxq.put(s)
                if self.log_writer and (s.startswith("EV,") or s.startswith("BIP,")):
                    import datetime as dt
                    self.log_writer.writerow([dt.datetime.utcnow().isoformat(), s])
        except Exception:
            pass

    def poll_rx(self):
        try:
            while True:
                s = self.rxq.get_nowait()
                self.txt.insert("end", s+"\n")
                self.txt.see("end")
        except queue.Empty:
            pass
        self.after(100, self.poll_rx)

if __name__ == "__main__":
    App().mainloop()
