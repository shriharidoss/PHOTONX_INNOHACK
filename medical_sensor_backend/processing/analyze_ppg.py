import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from scipy.signal import butter, filtfilt, find_peaks


# ============================================================
# 1. LOAD CSV
# ============================================================

FILE = "../data/raw/ppg_recording.csv"

df = pd.read_csv(FILE)

print("CSV loaded successfully.")
print()

print("Number of samples:", len(df))
print()

print("First 5 samples:")
print(df.head())
print()


# ============================================================
# 2. CHECK DATA
# ============================================================

required_columns = ["timestamp", "ir", "red"]

for column in required_columns:

    if column not in df.columns:
        raise ValueError(
            f"Missing column: {column}"
        )

print("Required columns found.")


# ============================================================
# 3. CLEAN DATA
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
print()


# ============================================================
# 4. GET IR SIGNAL
# ============================================================

ir = df["ir"].values

red = df["red"].values


# ============================================================
# 5. ESTIMATE SAMPLING FREQUENCY
# ============================================================

time_ms = df["timestamp"].values

time_difference = np.diff(time_ms)

median_difference = np.median(time_difference)

fs = 1000.0 / median_difference

print("Estimated sampling rate:",
      round(fs, 2),
      "Hz")

print()


# ============================================================
# 6. FILTER IR PPG
# ============================================================

low_cutoff = 0.5
high_cutoff = 5.0

nyquist = fs / 2

b, a = butter(
    3,
    [
        low_cutoff / nyquist,
        high_cutoff / nyquist
    ],
    btype="band"
)

filtered_ir = filtfilt(
    b,
    a,
    ir
)


# ============================================================
# 7. FIND PULSE PEAKS
# ============================================================

minimum_distance = int(
    0.4 * fs
)

prominence = np.std(
    filtered_ir
) * 0.5

peaks, properties = find_peaks(
    filtered_ir,
    distance=minimum_distance,
    prominence=prominence
)

print("Pulse peaks detected:",
      len(peaks))

print()


# ============================================================
# 8. CALCULATE HEART RATE
# ============================================================

if len(peaks) >= 2:

    peak_intervals = np.diff(peaks) / fs

    median_interval = np.median(
        peak_intervals
    )

    heart_rate = 60.0 / median_interval

    print(
        "Estimated Heart Rate:",
        round(heart_rate, 2),
        "BPM"
    )

else:

    heart_rate = None

    print(
        "Not enough pulse peaks to calculate HR."
    )


# ============================================================
# 9. PLOT RAW IR
# ============================================================

plt.figure(figsize=(12, 5))

plt.plot(
    time_ms / 1000,
    ir
)

plt.xlabel("Time (seconds)")
plt.ylabel("IR value")

plt.title(
    "MAX30102 Raw IR PPG"
)

plt.grid()

plt.show()


# ============================================================
# 10. PLOT FILTERED PPG + PEAKS
# ============================================================

plt.figure(figsize=(12, 5))

plt.plot(
    time_ms / 1000,
    filtered_ir,
    label="Filtered PPG"
)

plt.plot(
    time_ms[peaks] / 1000,
    filtered_ir[peaks],
    "x",
    markersize=8,
    label="Detected pulse peaks"
)

plt.xlabel("Time (seconds)")
plt.ylabel("PPG")

plt.title(
    "Filtered PPG and Pulse Peaks"
)

plt.legend()

plt.grid()

plt.show()