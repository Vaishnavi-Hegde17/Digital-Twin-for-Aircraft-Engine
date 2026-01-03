import numpy as np
import pandas as pd
from datetime import datetime, timedelta

np.random.seed(42)

# ================= CONFIG =================
AIRCRAFT_IDS = [f"HAL-HJT-{i:02d}" for i in range(1, 7)]
ENGINE_MODEL = "Adour Mk-821"

PHASES = ["IDLE", "TAKEOFF", "CRUISE", "DESCENT"]
PHASE_WEIGHTS = [0.25, 0.15, 0.45, 0.15]

SAMPLING_MINUTES = [10, 15]
TOTAL_SAMPLES_PER_AIRCRAFT = 600   # manageable size

# Target distribution (stable!)
HEALTH_STATES = ["NORMAL", "WARNING", "CRITICAL"]
HEALTH_PROB = [0.48, 0.32, 0.20]

records = []

# ================= HELPERS =================
def add_noise(x, pct):
    return x + np.random.normal(0, abs(x) * pct)

def throttle_for_phase(p):
    return {
        "IDLE": np.random.uniform(0.25, 0.35),
        "TAKEOFF": np.random.uniform(0.9, 1.0),
        "CRUISE": np.random.uniform(0.65, 0.75),
        "DESCENT": np.random.uniform(0.4, 0.5)
    }[p]

def severity_from_health(health):
    if health == "NORMAL":
        return np.random.uniform(0.0, 0.3)
    elif health == "WARNING":
        return np.random.uniform(0.3, 0.7)
    else:
        return np.random.uniform(0.7, 1.0)

# ================= DATA GENERATION =================
for ac in AIRCRAFT_IDS:

    # Aircraft individuality
    base_rpm = np.random.uniform(3000, 3300)
    base_egt = np.random.uniform(500, 530)
    base_oil_t = np.random.uniform(58, 65)
    base_oil_p = np.random.uniform(52, 58)
    base_vib = np.random.uniform(1.0, 1.5)
    base_fuel = np.random.uniform(470, 520)

    timestamp = datetime.now()
    flight_hours = 0.0

    for i in range(TOTAL_SAMPLES_PER_AIRCRAFT):

        step = int(np.random.choice(SAMPLING_MINUTES))
        timestamp += timedelta(minutes=step)
        flight_hours += step / 60

        phase = np.random.choice(PHASES, p=PHASE_WEIGHTS)
        throttle = throttle_for_phase(phase)

        # Choose health FIRST (stable distribution)
        health = np.random.choice(HEALTH_STATES, p=HEALTH_PROB)
        severity = severity_from_health(health)

        # -------- Physics-inspired sensors --------
        rpm = base_rpm * throttle * (1 - 0.15 * severity)
        egt = base_egt + (rpm / 9000) * 320 + severity * 120
        fuel = base_fuel + throttle * 850 + severity * 100
        oil_t = base_oil_t + throttle * 40 + severity * 45
        oil_p = base_oil_p - severity * 25
        vib = base_vib + throttle * 0.5 + severity * 3.5

        # -------- Noise (causes overlap) --------
        rpm = add_noise(rpm, 0.01)
        egt = add_noise(egt, 0.02)
        fuel = add_noise(fuel, 0.02)
        oil_t = add_noise(oil_t, 0.02)
        oil_p = add_noise(oil_p, 0.02)
        vib = add_noise(vib, 0.12)

        records.append({
            "Timestamp": timestamp,
            "Aircraft_ID": ac,
            "Engine_Model": ENGINE_MODEL,
            "Flight_Hours": round(flight_hours, 2),
            "Phase": phase,
            "Throttle": round(throttle, 2),
            "RPM": round(rpm, 1),
            "FuelFlow": round(fuel, 1),
            "EGT": round(egt, 1),
            "OilTemp": round(oil_t, 1),
            "OilPressure": round(oil_p, 1),
            "Vibration": round(vib, 2),
            "Severity": round(severity, 2),
            "Health": health
        })

# ================= FINAL DATAFRAME =================
df = pd.DataFrame(records)
df.to_csv("adour_engine_stable_ml_dataset.csv", index=False)

print(df["Health"].value_counts(normalize=True) * 100)
df.head()
