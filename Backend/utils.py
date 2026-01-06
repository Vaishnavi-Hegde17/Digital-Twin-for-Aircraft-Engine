import numpy as np
from datetime import datetime

np.random.seed(42)

PHASES = ["IDLE", "TAKEOFF", "CRUISE", "DESCENT"]
PHASE_WEIGHTS = [0.25, 0.15, 0.45, 0.15]


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


def generate_sample(aircraft_id="HAL-HJT-01", live=False):
    """Generate a single synthetic sensor sample dict similar to training data.

    Args:
        aircraft_id: aircraft identifier
        live: when True, use a lower probability of WARNING/CRITICAL to better
              reflect live operation while still occasionally producing anomalies.
    """
    base_rpm = np.random.uniform(3000, 3300)
    base_egt = np.random.uniform(500, 530)
    base_oil_t = np.random.uniform(58, 65)
    base_oil_p = np.random.uniform(52, 58)
    base_vib = np.random.uniform(1.0, 1.5)
    base_fuel = np.random.uniform(470, 520)

    phase = np.random.choice(PHASES, p=PHASE_WEIGHTS)
    throttle = throttle_for_phase(phase)

    # health distribution: reduce anomalies for live/demo streaming
    if live:
        health = np.random.choice(["NORMAL", "WARNING", "CRITICAL"], p=[0.80, 0.15, 0.05])
    else:
        # match training distribution
        health = np.random.choice(["NORMAL", "WARNING", "CRITICAL"], p=[0.48, 0.32, 0.20])
    severity = severity_from_health(health)

    rpm = base_rpm * throttle * (1 - 0.15 * severity)
    egt = base_egt + (rpm / 9000) * 320 + severity * 120
    fuel = base_fuel + throttle * 850 + severity * 100
    oil_t = base_oil_t + throttle * 40 + severity * 45
    oil_p = base_oil_p - severity * 25
    vib = base_vib + throttle * 0.5 + severity * 3.5

    # add noise
    rpm = add_noise(rpm, 0.01)
    egt = add_noise(egt, 0.02)
    fuel = add_noise(fuel, 0.02)
    oil_t = add_noise(oil_t, 0.02)
    oil_p = add_noise(oil_p, 0.02)
    vib = add_noise(vib, 0.12)

    sample = {
        "Timestamp": datetime.now().isoformat(),
        "Aircraft_ID": aircraft_id,
        "Engine_Model": "Adour Mk-821",
        "Phase": phase,
        "Throttle": round(throttle, 2),
        "RPM": round(rpm, 1),
        "FuelFlow": round(fuel, 1),
        "EGT": round(egt, 1),
        "OilTemp": round(oil_t, 1),
        "OilPressure": round(oil_p, 1),
        "Vibration": round(vib, 2),
    }
    return sample
