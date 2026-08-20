import pandas as pd
import numpy as np

from scipy.signal import butter, filtfilt


# ============================================================
# 1. LOAD DATA
# ============================================================

FILE = "../data/raw/ppg_recording.csv"

df = pd.read_csv(FILE)

print("CSV loaded.")
print("Samples:", len(df))


# ============================================================
# 2. CLEAN DATA
# ============================================================

df["timestamp"] = pd.to_numeric(
    df["timestamp"],
    errors="coerce"
)

df["ir"] = pd.to_numeric(
    df["ir"],
    errors="coerce"
)

df["red"] = pd.to_numeric(
    df["red"],
    errors="coerce"
)

df = df.dropna()

print("Valid samples:", len(df))


# ============================================================
# 3. ESTIMATE SAMPLING RATE
# ============================================================

time_ms = df["timestamp"].values

dt = np.diff(time_ms)

median_dt = np.median(dt)

fs = 1000.0 / median_dt

print("Sampling rate:",
      round(fs, 2),
      "Hz")


# ============================================================
# 4. GET RED AND IR
# ============================================================

ir = df["ir"].values.astype(float)

red = df["red"].values.astype(float)


# ============================================================
# 5. BANDPASS FILTER
# ============================================================

low = 0.5
high = 5.0

nyquist = fs / 2

if high >= nyquist:
    raise ValueError(
        f"Sampling rate is too low: {fs:.2f} Hz. "
        f"Need a sampling rate greater than 10 Hz."
    )

b, a = butter(
    3,
    [
        low / nyquist,
        high / nyquist
    ],
    btype="band"
)

filtered_ir = filtfilt(
    b,
    a,
    ir
)

filtered_red = filtfilt(
    b,
    a,
    red
)


# ============================================================
# 6. AC COMPONENT
# ============================================================

ac_ir = np.max(filtered_ir) - np.min(filtered_ir)

ac_red = np.max(filtered_red) - np.min(filtered_red)


# ============================================================
# 7. DC COMPONENT
# ============================================================

dc_ir = np.mean(ir)

dc_red = np.mean(red)


# ============================================================
# 8. CHECK VALUES
# ============================================================

print()
print("AC IR :", ac_ir)
print("DC IR :", dc_ir)

print("AC RED:", ac_red)
print("DC RED:", dc_red)


# ============================================================
# 9. RATIO OF RATIOS
# ============================================================

if dc_ir == 0 or dc_red == 0:

    raise ValueError(
        "Invalid DC value."
    )

R = (
    (ac_red / dc_red)
    /
    (ac_ir / dc_ir)
)


print()
print("R ratio:", R)


# ============================================================
# 10. SpO2 CALIBRATION EQUATION
# ============================================================

spo2 = (
    -45.060 * R * R
    + 30.354 * R
    + 94.845
)


# ============================================================
# 11. LIMIT RESULT
# ============================================================

spo2 = np.clip(
    spo2,
    70,
    100
)


print()
print(
    "Estimated SpO2:",
    round(spo2, 2),
    "%"
)