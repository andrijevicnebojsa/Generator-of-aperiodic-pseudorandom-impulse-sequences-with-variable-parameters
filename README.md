# Generator of Aperiodic Pseudorandom Impulse Sequences (APPI)

Modular APPI generator based on Arduino Mega 2560, with:
- **Poisson** event schedule (ISI) and **uniform** pulse widths (PW),
- two timing variants (**baseline** and **Timer/ISR (CTC)**),
- **telemetry** in real time and PC tools (logger + Tk GUI),
- safe output chain (**opto** + **CCS**).

## Structure

firmware/
scripts/
figures/
tables/
requirements.txt


## Quick start
1. **Firmware**: In the `Arduino IDE`, import the appropriate `.ino` (baseline or timer_isr) and flash it on the **Arduino Mega**.
2. **PC logger**: 
```bash 
pip install -r requirements.txt 
python scripts/pc_serial_logger.py --port COM5 --baud 115200 --csv logs/events.csv --lambda 2.0 --pwmin 50 --pwmax 1000 --seed analog --start

Hardware (connection)

Arduino D8? optocoupler (6N137), primary side (with serial R and pull-up according to the scheme),

secondary side opta ? CCS/H-bridge driver (TTL inputs: EN, PHASE),

CCS output to R||C load or electrodes (according to operational safety targets),

common returns and shielding, RC snubber as required.

Security

These scripts and firmware are for laboratory use. For biomedical applications, isolation and measurement according to IEC 60601-1/-1-2 is mandatory. Work at your own risk.