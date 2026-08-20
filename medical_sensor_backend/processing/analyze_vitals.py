import os
import sys
import json

import pandas as pd
import numpy as np

from scipy.signal import butter, filtfilt, find_peaks


# ============================================================
# PROJECT PATHS
# ============================================================

CURRENT_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

PROJECT_DIR = os.path.dirname(
    CURRENT_DIR
)

ML_DIR = os.path.join(
    PROJECT_DIR,
    "ml"
)

DATA_DIR = os.path.join(
    PROJECT_DIR,
    "data"
)

RAW_DIR = os.path.join(
    DATA_DIR,
    "raw"
)


# ============================================================
# FLASK BACKEND SESSION FILE
# ============================================================
#
# The current patient session is created by Flask:
#
# C:\Users\shrih\PycharmProjects\
# health_kiosk_backend\data\patient_session.json
#
# We MUST read this file so that the sensor result belongs
# to the patient currently using the kiosk.
# ============================================================

FLASK_BACKEND_DIR = os.path.join(
    os.path.expanduser("~"),
    "PycharmProjects",
    "health_kiosk_backend"
)

FLASK_SESSION_FILE = os.path.join(
    FLASK_BACKEND_DIR,
    "data",
    "patient_session.json"
)


# ============================================================
# IMPORT BP ML MODEL
# ============================================================

if ML_DIR not in sys.path:

    sys.path.insert(
        0,
        ML_DIR
    )


try:

    from infer_bp import predict_bp

except ImportError as error:

    raise ImportError(
        "Could not import BP model.\n"
        f"Expected infer_bp.py at:\n{ML_DIR}\n\n"
        f"Original error: {error}"
    )


# ============================================================
# FILE PATHS
# ============================================================

INPUT_FILE = os.path.join(
    RAW_DIR,
    "ppg_recording.csv"
)

OUTPUT_FILE = os.path.join(
    DATA_DIR,
    "vitals_result.json"
)


# ============================================================
# START
# ============================================================

print()

print(
    "================================"
)

print(
    " VITAL SIGN ANALYSIS"
)

print(
    "================================"
)

print()


# ============================================================
# CHECK FLASK SESSION
# ============================================================

if not os.path.exists(
    FLASK_SESSION_FILE
):

    raise FileNotFoundError(

        "Patient measurement session not found.\n\n"

        f"Expected file:\n"
        f"{FLASK_SESSION_FILE}\n\n"

        "Start the health check from the "
        "patient frontend first."
    )


# ============================================================
# LOAD CURRENT PATIENT SESSION
# ============================================================

try:

    with open(
        FLASK_SESSION_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        session = json.load(
            file
        )

except Exception as error:

    raise RuntimeError(
        "Could not read patient_session.json.\n"
        f"File: {FLASK_SESSION_FILE}\n"
        f"Error: {error}"
    )


# ============================================================
# GET CURRENT PATIENT ID
# ============================================================

patient_id = session.get(
    "patient_id"
)


if patient_id is None:

    raise ValueError(
        "patient_id is missing from "
        "patient_session.json"
    )


try:

    patient_id = int(
        patient_id
    )

except (
    ValueError,
    TypeError
):

    raise ValueError(
        "Invalid patient_id in "
        "patient_session.json"
    )


if patient_id <= 0:

    raise ValueError(
        "patient_id must be greater than 0."
    )


# ============================================================
# DISPLAY CURRENT PATIENT
# ============================================================

print(
    "Current Patient ID:",
    patient_id
)

print()

print(
    "Session file:"
)

print(
    FLASK_SESSION_FILE
)

print()


# ============================================================
# CHECK PPG INPUT
# ============================================================

if not os.path.exists(
    INPUT_FILE
):

    raise FileNotFoundError(

        "PPG recording not found.\n\n"

        f"Expected file:\n{INPUT_FILE}\n\n"

        "Collect PPG data from ESP32 first."
    )


print(
    "Input file:"
)

print(
    INPUT_FILE
)

print()


# ============================================================
# LOAD CSV
# ============================================================

df = pd.read_csv(
    INPUT_FILE
)


print(
    "CSV loaded."
)

print(
    "Total samples:",
    len(df)
)

print()


# ============================================================
# CHECK REQUIRED COLUMNS
# ============================================================

required_columns = [
    "timestamp",
    "ir",
    "red"
]


missing_columns = [

    column

    for column in required_columns

    if column not in df.columns

]


if missing_columns:

    raise ValueError(

        "Missing CSV columns: "
        + ", ".join(
            missing_columns
        )
    )


# ============================================================
# CONVERT TO NUMERIC
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


# ============================================================
# REMOVE INVALID ROWS
# ============================================================

df = df.dropna()


print(
    "Valid samples:",
    len(df)
)

print()


# ============================================================
# MINIMUM SAMPLE CHECK
# ============================================================

if len(df) < 210:

    raise ValueError(

        "Not enough PPG samples.\n"

        "Required: at least 210 samples.\n"

        f"Available: {len(df)} samples."
    )


# ============================================================
# EXTRACT SIGNALS
# ============================================================

timestamp = df[
    "timestamp"
].values.astype(float)


ir = df[
    "ir"
].values.astype(float)


red = df[
    "red"
].values.astype(float)


# ============================================================
# ESTIMATE SAMPLING RATE
# ============================================================

time_difference = np.diff(
    timestamp
)


time_difference = time_difference[
    time_difference > 0
]


if len(time_difference) == 0:

    raise ValueError(
        "Invalid timestamps in PPG data."
    )


median_difference = np.median(
    time_difference
)


if median_difference <= 0:

    raise ValueError(
        "Invalid timestamp interval."
    )


# ESP32 timestamp is milliseconds.

fs = 1000.0 / median_difference


print(
    "Estimated sampling rate:",
    round(fs, 2),
    "Hz"
)

print()


# ============================================================
# CHECK SAMPLING RATE
# ============================================================

if fs < 20:

    raise ValueError(

        "Sampling rate is too low.\n"

        f"Detected: {fs:.2f} Hz\n"

        "Collect a new PPG recording."
    )


# ============================================================
# BANDPASS FILTER
# ============================================================

low_cutoff = 0.5

high_cutoff = 5.0

nyquist = fs / 2.0


if high_cutoff >= nyquist:

    raise ValueError(

        "Sampling rate is too low "
        "for the selected filter."
    )


b, a = butter(

    3,

    [
        low_cutoff / nyquist,
        high_cutoff / nyquist
    ],

    btype="band"
)


# ============================================================
# FILTER IR
# ============================================================

filtered_ir = filtfilt(
    b,
    a,
    ir
)


# ============================================================
# FILTER RED
# ============================================================

filtered_red = filtfilt(
    b,
    a,
    red
)


# ============================================================
# HEART RATE
# ============================================================

print(
    "================================"
)

print(
    " HEART RATE"
)

print(
    "================================"
)


minimum_distance = max(
    1,
    int(0.4 * fs)
)


prominence = (
    np.std(filtered_ir)
    * 0.5
)


peaks, properties = find_peaks(

    filtered_ir,

    distance=minimum_distance,

    prominence=prominence
)


print(
    "Pulse peaks detected:",
    len(peaks)
)


heart_rate = None


if len(peaks) >= 2:

    intervals = (
        np.diff(peaks) / fs
    )


    median_interval = np.median(
        intervals
    )


    if median_interval > 0:

        heart_rate = (
            60.0 /
            median_interval
        )


        print(
            "Heart Rate:",
            round(
                heart_rate,
                2
            ),
            "BPM"
        )

    else:

        print(
            "Invalid pulse interval."
        )

else:

    print(
        "Unable to calculate Heart Rate."
    )


print()


# ============================================================
# SpO2
# ============================================================

print(
    "================================"
)

print(
    " SpO2"
)

print(
    "================================"
)


# DC components

dc_ir = np.mean(
    ir
)

dc_red = np.mean(
    red
)


# AC components

ac_ir = np.std(
    filtered_ir
)

ac_red = np.std(
    filtered_red
)


print(
    "DC IR :",
    dc_ir
)

print(
    "DC RED:",
    dc_red
)

print(
    "AC IR :",
    ac_ir
)

print(
    "AC RED:",
    ac_red
)


spo2 = None


if (

    dc_ir > 0

    and dc_red > 0

    and ac_ir > 0

    and ac_red > 0

):

    ratio = (

        (ac_red / dc_red)

        /

        (ac_ir / dc_ir)

    )


    print(
        "R ratio:",
        ratio
    )


    # Approximate empirical equation.
    #
    # This is an estimation and must be
    # validated against a reference pulse
    # oximeter before clinical use.

    spo2_value = (

        -45.060 * ratio * ratio

        + 30.354 * ratio

        + 94.845

    )


    spo2 = float(

        np.clip(
            spo2_value,
            70,
            100
        )

    )


    print(
        "Estimated SpO2:",
        round(
            spo2,
            2
        ),
        "%"
    )

else:

    print(
        "Unable to calculate SpO2."
    )


print()


# ============================================================
# BLOOD PRESSURE - ML MODEL
# ============================================================

print(
    "================================"
)

print(
    " BLOOD PRESSURE - ML"
)

print(
    "================================"
)


systolic_bp = None

diastolic_bp = None


try:

    print(
        "Running BP ML model..."
    )


    systolic_bp, diastolic_bp = predict_bp(
        ir
    )


    systolic_bp = round(
        float(
            systolic_bp
        ),
        2
    )


    diastolic_bp = round(
        float(
            diastolic_bp
        ),
        2
    )


    print(
        "Estimated SBP:",
        systolic_bp,
        "mmHg"
    )


    print(
        "Estimated DBP:",
        diastolic_bp,
        "mmHg"
    )


except Exception as error:

    print()

    print(
        "BP calculation failed."
    )

    print(
        "Error:",
        str(error)
    )


print()


# ============================================================
# CREATE FINAL VITALS
# ============================================================

vitals = {

    "patient_id":
        patient_id,

    "heart_rate":
        (
            round(
                float(
                    heart_rate
                ),
                2
            )

            if heart_rate is not None

            else None
        ),

    "spo2":
        (
            round(
                float(
                    spo2
                ),
                2
            )

            if spo2 is not None

            else None
        ),

    "systolic_bp":
        (
            systolic_bp

            if systolic_bp is not None

            else None
        ),

    "diastolic_bp":
        (
            diastolic_bp

            if diastolic_bp is not None

            else None
        ),

    "temperature":
        None
}


# ============================================================
# CREATE DATA DIRECTORY
# ============================================================

os.makedirs(
    DATA_DIR,
    exist_ok=True
)


# ============================================================
# SAVE VITALS JSON
# ============================================================

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        vitals,
        file,
        indent=4
    )


# ============================================================
# DISPLAY FINAL RESULT
# ============================================================

print(
    "================================"
)

print(
    " FINAL VITALS"
)

print(
    "================================"
)

print()


print(
    json.dumps(
        vitals,
        indent=4
    )
)


print()

print(
    "JSON saved:"
)

print(
    OUTPUT_FILE
)


print()

print(
    "================================"
)

print(
    " ANALYSIS COMPLETE"
)

print(
    "================================"
)