# Generator of Aperiodic Pseudorandom Impulse Sequences (APPI)

Modularni APPI generator zasnovan na Arduino Mega 2560, sa:
- **Poisson** rasporedom događaja (ISI) i **uniformnim** širinama impulsa (PW),
- dve varijante tajminga (**baseline** i **Timer/ISR (CTC)**),
- **telemetrijom** u realnom vremenu i PC alatima (logger + Tk GUI),
- bezbednim izlaznim lancem (**opto** + **CCS**).

## Struktura

firmware/
firmware_baseline/firmware_baseline.ino
firmware_timer_isr/firmware_timer_isr.ino
firmware_biphasic_isr/firmware_biphasic_isr.ino
scripts/
gen_reference_dataset.py
pc_serial_logger.py
pc_tk_gui.py
stats_ks_qq.py
spectrum_periodogram.py
acf_analysis.py
rc_ccs_sim.py
compliance_curve.py
operational_envelope_map.py
robust_seeds_eval.py
verify_assets.py
datasets/
figures/
tables/
listings/
assets_manifest.yml
requirements.txt
.gitignore


## Brzi početak
1. **Firmware**: U `Arduino IDE` uvezi odgovarajuću `.ino` (baseline ili timer_isr) i flešuj na **Arduino Mega**.
2. **PC logger**:
   ```bash
   pip install -r requirements.txt
   python scripts/pc_serial_logger.py --port COM5 --baud 115200 --csv logs/events.csv --lambda 2.0 --pwmin 50 --pwmax 1000 --seed analog --start

GUI:
python scripts/pc_tk_gui.py


Reprodukcija analiza
python scripts/gen_reference_dataset.py
python scripts/stats_ks_qq.py
python scripts/spectrum_periodogram.py
python scripts/acf_analysis.py
python scripts/rc_ccs_sim.py
python scripts/compliance_curve.py
python scripts/operational_envelope_map.py
python scripts/robust_seeds_eval.py

Verifikacija asetova
python scripts/verify_assets.py


Hardver (spoj)

Arduino D8 → optokapler (6N137), primarna strana (uz serijski R i pull-up po šemi),

sekundarna strana opta → CCS/H-bridge drajver (TTL ulazi: EN, PHASE),

izlaz CCS na R||C opterećenje ili elektrode (po bezbednosnim metama iz rada),

zajednički povrati i ekranisanje, RC snubber prema potrebi.

Bezbednost

Ove skripte i firmware su za laboratorijsku upotrebu. Za biomedicinske aplikacije obavezna je izolacija i merenje prema IEC 60601-1/-1-2. Radite na sopstvenu odgovornost.

