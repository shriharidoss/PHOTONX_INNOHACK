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
# IMPORT BP MODEL
# ============================================================

if ML_DIR not in sys.path:
    sys.path.insert(0, ML_DIR)


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

TEMPERATURE_FILE = os.path.join(
    DATA_DIR,
    "temperature.json"
)

SESSION_FILE = os.path.join(
    DATA_DIR,
    "patient_session.json"
)


# ============================================================
# CONFIGURATION
# ============================================================

MINIMUM_PPG_SAMPLES = 210

MINIMUM_SAMPLING_RATE = 8.0

LOW_CUTOFF = 0.5

MAX_HIGH_CUTOFF = 4.0


# ============================================================
# ERROR FUNCTION
# ============================================================

def fail(message):

    print()
    print("==============================================")
    print(" ERROR: VITAL ANALYSIS FAILED")
    print("==============================================")
    print()
    print(message)
    print()

    sys.exit(1)


# ============================================================
# HEADER
# ============================================================

print()
print("==============================================")
print("       VITAL SIGN ANALYSIS")
print("==============================================")
print()


# ============================================================
# GET PATIENT ID
# ============================================================

patient_id = None


# ============================================================
# COMMAND-LINE PATIENT ID
# ============================================================

if len(sys.argv) >= 2:

    try:

        patient_id = int(
            sys.argv[1]
        )

    except (
        ValueError,
        TypeError
    ):

        fail(
            "Invalid patient ID passed to "
            "analyze_vitals.py:\n"
            + str(sys.argv[1])
        )

    print(
        "Patient ID received from sensor controller:"
    )

    print(
        patient_id
    )

    print()


# ============================================================
# PATIENT SESSION FALLBACK
# ============================================================

else:

    print(
        "No patient ID argument received."
    )

    print(
        "Reading patient_session.json..."
    )

    print()


    if not os.path.exists(
        SESSION_FILE
    ):

        fail(
            "patient_session.json not found.\n"
            f"Expected:\n{SESSION_FILE}"
        )


    try:

        with open(
            SESSION_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            session = json.load(
                file
            )

    except Exception as error:

        fail(
            "Could not read patient_session.json:\n"
            + str(error)
        )


    patient_id = session.get(
        "patient_id"
    )


    if patient_id is None:

        fail(
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

        fail(
            "Invalid patient_id in "
            "patient_session.json"
        )


# ============================================================
# VALIDATE PATIENT ID
# ============================================================

if patient_id <= 0:

    fail(
        "Patient ID must be greater than 0."
    )


print(
    "=============================================="
)

print(
    " CURRENT PATIENT"
)

print(
    "=============================================="
)

print()

print(
    "CURRENT PATIENT ID:",
    patient_id
)

print()


# ============================================================
# READ TEMPERATURE
# ============================================================

print(
    "=============================================="
)

print(
    " READING TEMPERATURE"
)

print(
    "=============================================="
)

print()

print(
    "Temperature file:"
)

print(
    TEMPERATURE_FILE
)

print()


if not os.path.isfile(
    TEMPERATURE_FILE
):

    fail(
        "temperature.json does not exist.\n"
        f"Expected:\n{TEMPERATURE_FILE}"
    )


try:

    with open(
        TEMPERATURE_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        temperature_json = json.load(
            file
        )

except Exception as error:

    fail(
        "Could not read temperature.json:\n"
        + str(error)
    )


print(
    "Temperature JSON received:"
)

print(
    json.dumps(
        temperature_json,
        indent=4
    )
)

print()


# ============================================================
# GET TEMPERATURE
# ============================================================

raw_temperature = temperature_json.get(
    "temperature"
)


if raw_temperature is None:

    fail(
        "temperature.json contains no "
        "temperature value."
    )


try:

    temperature = float(
        raw_temperature
    )

except (
    ValueError,
    TypeError
):

    fail(
        "Invalid temperature value in "
        "temperature.json."
    )


temperature = round(
    temperature,
    2
)


# ============================================================
# CHECK TEMPERATURE PATIENT ID
# ============================================================

temperature_patient_id = (
    temperature_json.get(
        "patient_id"
    )
)


if temperature_patient_id is None:

    fail(
        "temperature.json does not contain patient_id."
    )


try:

    temperature_patient_id = int(
        temperature_patient_id
    )

except (
    ValueError,
    TypeError
):

    fail(
        "Invalid patient_id in temperature.json."
    )


print(
    "Current patient:",
    patient_id
)

print(
    "Temperature patient:",
    temperature_patient_id
)

print()


# ============================================================
# TEMPERATURE PATIENT SAFETY CHECK
# ============================================================

if temperature_patient_id != patient_id:

    fail(
        "Patient ID mismatch.\n"
        f"Current patient: {patient_id}\n"
        f"Temperature patient: {temperature_patient_id}"
    )


print(
    "Temperature patient ID verified."
)

print(
    "Temperature:",
    temperature,
    "°C"
)

print()


# ============================================================
# CHECK PPG FILE
# ============================================================

if not os.path.isfile(
    INPUT_FILE
):

    fail(
        "PPG recording not found:\n"
        f"{INPUT_FILE}"
    )


print(
    "PPG input file:"
)

print(
    INPUT_FILE
)

print()


# ============================================================
# LOAD PPG CSV
# ============================================================

try:

    df = pd.read_csv(
        INPUT_FILE
    )

except Exception as error:

    fail(
        "Could not load PPG CSV:\n"
        + str(error)
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
# REQUIRED COLUMNS
# ============================================================

required_columns = [
    "timestamp",
    "ir",
    "red"
]


for column in required_columns:

    if column not in df.columns:

        fail(
            f"Missing required column: {column}"
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
# REMOVE INVALID DATA
# ============================================================

df = df.dropna()

df = df[
    np.isfinite(
        df["timestamp"]
    )
    &
    np.isfinite(
        df["ir"]
    )
    &
    np.isfinite(
        df["red"]
    )
]


print(
    "Valid samples:",
    len(df)
)

print()


# ============================================================
# MINIMUM SAMPLE CHECK
# ============================================================

if len(df) < MINIMUM_PPG_SAMPLES:

    fail(
        "Not enough PPG samples.\n"
        f"Collected: {len(df)}\n"
        f"Required: at least {MINIMUM_PPG_SAMPLES}"
    )


# ============================================================
# GET SIGNALS
# ============================================================

timestamp = (
    df["timestamp"]
    .values
    .astype(float)
)

ir = (
    df["ir"]
    .values
    .astype(float)
)

red = (
    df["red"]
    .values
    .astype(float)
)


# ============================================================
# CALCULATE SAMPLE INTERVAL
# ============================================================

time_difference = np.diff(
    timestamp
)

time_difference = (
    time_difference[
        time_difference > 0
    ]
)


if len(
    time_difference
) == 0:

    fail(
        "Invalid timestamps."
    )


median_difference = np.median(
    time_difference
)


if median_difference <= 0:

    fail(
        "Invalid median timestamp difference."
    )


# ============================================================
# CALCULATE SAMPLING RATE
# ============================================================

fs = (
    1000.0
    /
    median_difference
)


print(
    "Estimated sampling rate:",
    round(
        fs,
        2
    ),
    "Hz"
)

print(
    "Median sample interval:",
    round(
        median_difference,
        2
    ),
    "ms"
)

print()


# ============================================================
# SAMPLING RATE CHECK
# ============================================================

if fs < MINIMUM_SAMPLING_RATE:

    fail(
        "Sampling rate is too low for PPG analysis.\n"
        f"Detected: {fs:.2f} Hz\n"
        f"Minimum supported: {MINIMUM_SAMPLING_RATE:.2f} Hz"
    )


# ============================================================
# NYQUIST FREQUENCY
# ============================================================

nyquist = fs / 2.0


print(
    "Nyquist frequency:",
    round(
        nyquist,
        3
    ),
    "Hz"
)

print()


# ============================================================
# ADAPTIVE BANDPASS FILTER
# ============================================================

low_cutoff = LOW_CUTOFF


high_cutoff = min(
    MAX_HIGH_CUTOFF,
    nyquist * 0.65
)


if high_cutoff <= low_cutoff:

    fail(
        "Sampling rate is too low for the PPG filter.\n"
        f"Sampling rate: {fs:.2f} Hz\n"
        f"Nyquist: {nyquist:.2f} Hz"
    )


print(
    "PPG filter:"
)

print(
    "Low cutoff:",
    round(
        low_cutoff,
        3
    ),
    "Hz"
)

print(
    "High cutoff:",
    round(
        high_cutoff,
        3
    ),
    "Hz"
)

print()


# ============================================================
# CREATE BANDPASS FILTER
# ============================================================

try:

    b, a = butter(
        3,
        [
            low_cutoff / nyquist,
            high_cutoff / nyquist
        ],
        btype="band"
    )

except Exception as error:

    fail(
        "Could not create PPG bandpass filter:\n"
        + str(error)
    )


# ============================================================
# FILTER IR
# ============================================================

try:

    filtered_ir = filtfilt(
        b,
        a,
        ir
    )

except Exception as error:

    fail(
        "IR PPG filtering failed:\n"
        + str(error)
    )


# ============================================================
# FILTER RED
# ============================================================

try:

    filtered_red = filtfilt(
        b,
        a,
        red
    )

except Exception as error:

    fail(
        "RED PPG filtering failed:\n"
        + str(error)
    )


# ============================================================
# HEART RATE
# ============================================================

print(
    "=============================================="
)

print(
    " HEART RATE"
)

print(
    "=============================================="
)

print()


# ============================================================
# METHOD 1 - NORMAL / RELAXED PEAK DETECTION
# ============================================================

signal_std = np.std(
    filtered_ir
)

prominence = (
    signal_std * 0.10
)

if prominence <= 0:

    prominence = 1e-9


minimum_distance = max(
    1,
    int(
        0.30 * fs
    )
)


print(
    "Signal standard deviation:",
    round(
        signal_std,
        4
    )
)

print(
    "Peak prominence:",
    round(
        prominence,
        4
    )
)

print()


try:

    peaks, _ = find_peaks(

        filtered_ir,

        distance=minimum_distance,

        prominence=prominence

    )

except Exception as error:

    print(
        "Peak detection failed:"
    )

    print(
        str(error)
    )

    peaks = []


print(
    "Pulse peaks detected:",
    len(peaks)
)

print()


heart_rate = None


# ============================================================
# CALCULATE HR FROM PEAK INTERVALS
# ============================================================

if len(peaks) >= 2:

    intervals = (
        np.diff(
            peaks
        )
        /
        fs
    )


    print(
        "Pulse intervals:"
    )

    print(
        intervals
    )

    print()


    # --------------------------------------------------------
    # 30 - 220 BPM
    # --------------------------------------------------------

    valid_intervals = intervals[
        (
            intervals >= (
                60.0 / 220.0
            )
        )
        &
        (
            intervals <= (
                60.0 / 30.0
            )
        )
    ]


    print(
        "Valid pulse intervals:",
        len(valid_intervals)
    )

    print()


    if len(
        valid_intervals
    ) > 0:

        median_interval = np.median(
            valid_intervals
        )


        if median_interval > 0:

            calculated_hr = (
                60.0
                /
                median_interval
            )


            if (
                30.0
                <=
                calculated_hr
                <=
                220.0
            ):

                heart_rate = round(
                    float(
                        calculated_hr
                    ),
                    2
                )


# ============================================================
# METHOD 2 - MORE RELAXED PEAK DETECTION
# ============================================================

if heart_rate is None:

    print(
        "Trying relaxed heart-rate detection..."
    )

    print()


    relaxed_prominence = (
        signal_std * 0.03
    )


    if relaxed_prominence <= 0:

        relaxed_prominence = 1e-9


    try:

        relaxed_peaks, _ = find_peaks(

            filtered_ir,

            distance=max(
                1,
                int(
                    0.27 * fs
                )
            ),

            prominence=relaxed_prominence

        )

    except Exception:

        relaxed_peaks = []


    print(
        "Relaxed peaks detected:",
        len(relaxed_peaks)
    )

    print()


    if len(
        relaxed_peaks
    ) >= 2:

        relaxed_intervals = (
            np.diff(
                relaxed_peaks
            )
            /
            fs
        )


        print(
            "Relaxed pulse intervals:"
        )

        print(
            relaxed_intervals
        )

        print()


        relaxed_valid = (
            relaxed_intervals[
                (
                    relaxed_intervals
                    >=
                    (
                        60.0 / 220.0
                    )
                )
                &
                (
                    relaxed_intervals
                    <=
                    (
                        60.0 / 30.0
                    )
                )
            ]
        )


        print(
            "Relaxed valid intervals:",
            len(relaxed_valid)
        )

        print()


        if len(
            relaxed_valid
        ) > 0:

            median_interval = np.median(
                relaxed_valid
            )


            if median_interval > 0:

                calculated_hr = (
                    60.0
                    /
                    median_interval
                )


                if (
                    30.0
                    <=
                    calculated_hr
                    <=
                    220.0
                ):

                    heart_rate = round(
                        float(
                            calculated_hr
                        ),
                        2
                    )


# ============================================================
# METHOD 3 - AUTOCORRELATION
# ============================================================

if heart_rate is None:

    print(
        "Trying autocorrelation heart-rate detection..."
    )

    print()


    signal_for_ac = (
        filtered_ir
        -
        np.mean(
            filtered_ir
        )
    )


    signal_std_ac = np.std(
        signal_for_ac
    )


    if signal_std_ac > 0:

        autocorrelation = np.correlate(

            signal_for_ac,

            signal_for_ac,

            mode="full"

        )


        autocorrelation = (
            autocorrelation[
                len(signal_for_ac) - 1:
            ]
        )


        # ----------------------------------------------------
        # 30-220 BPM search range
        # ----------------------------------------------------

        min_lag = max(
            1,
            int(
                60.0
                /
                220.0
                *
                fs
            )
        )


        max_lag = min(
            len(
                autocorrelation
            ) - 1,
            int(
                60.0
                /
                30.0
                *
                fs
            )
        )


        if max_lag > min_lag:

            search_region = (
                autocorrelation[
                    min_lag:
                    max_lag + 1
                ]
            )


            if len(
                search_region
            ) > 0:

                best_index = int(
                    np.argmax(
                        search_region
                    )
                )


                best_lag = (
                    min_lag
                    +
                    best_index
                )


                best_correlation = (
                    search_region[
                        best_index
                    ]
                )


                zero_lag = (
                    autocorrelation[0]
                )


                correlation_ratio = 0.0


                if zero_lag != 0:

                    correlation_ratio = (
                        best_correlation
                        /
                        zero_lag
                    )


                print(
                    "Autocorrelation lag:",
                    best_lag
                )

                print(
                    "Autocorrelation ratio:",
                    round(
                        correlation_ratio,
                        4
                    )
                )

                print()


                # ------------------------------------------------
                # Relaxed threshold
                # ------------------------------------------------

                if (
                    best_lag > 0
                    and
                    correlation_ratio >= 0.07
                ):

                    estimated_hr = (
                        60.0
                        *
                        fs
                        /
                        best_lag
                    )


                    if (
                        30.0
                        <=
                        estimated_hr
                        <=
                        220.0
                    ):

                        heart_rate = round(
                            float(
                                estimated_hr
                            ),
                            2
                        )


# ============================================================
# FINAL HEART RATE
# ============================================================

print(
    "Heart Rate:",
    heart_rate,
    "BPM"
)

print()


# ============================================================
# SpO2
# ============================================================

print(
    "=============================================="
)

print(
    " SpO2"
)

print(
    "=============================================="
)

print()


# ============================================================
# DC COMPONENTS
# ============================================================

dc_ir = np.mean(
    ir
)

dc_red = np.mean(
    red
)


# ============================================================
# AC COMPONENTS
# ============================================================

ac_ir = np.std(
    filtered_ir
)

ac_red = np.std(
    filtered_red
)


spo2 = None


# ============================================================
# CALCULATE RATIO
# ============================================================

if (
    dc_ir > 0
    and
    dc_red > 0
    and
    ac_ir > 0
    and
    ac_red > 0
):

    ratio = (

        (
            ac_red
            /
            dc_red
        )

        /

        (
            ac_ir
            /
            dc_ir
        )
    )


    if np.isfinite(
        ratio
    ):

        spo2_value = (

            -45.060
            * ratio
            * ratio

            + 30.354
            * ratio

            + 94.845
        )


        if np.isfinite(
            spo2_value
        ):

            spo2 = float(
                np.clip(
                    spo2_value,
                    70.0,
                    100.0
                )
            )


            spo2 = round(
                spo2,
                2
            )


print(
    "SpO2:",
    spo2,
    "%"
)

print()


# ============================================================
# BLOOD PRESSURE
# ============================================================

print(
    "=============================================="
)

print(
    " BLOOD PRESSURE - ML"
)

print(
    "=============================================="
)

print()


systolic_bp = None

diastolic_bp = None


try:

    print(
        "Running BP ML model..."
    )

    print()


    systolic_bp, diastolic_bp = (
        predict_bp(
            ir
        )
    )


    if systolic_bp is not None:

        systolic_bp = float(
            systolic_bp
        )


        if np.isfinite(
            systolic_bp
        ):

            systolic_bp = round(
                systolic_bp,
                2
            )

        else:

            systolic_bp = None


    if diastolic_bp is not None:

        diastolic_bp = float(
            diastolic_bp
        )


        if np.isfinite(
            diastolic_bp
        ):

            diastolic_bp = round(
                diastolic_bp,
                2
            )

        else:

            diastolic_bp = None


except Exception as error:

    print(
        "BP calculation failed:"
    )

    print(
        str(error)
    )

    print()

    print(
        "Continuing with other vital signs."
    )

    print()


# ============================================================
# CREATE FINAL RESULT
# ============================================================

vitals = {

    "patient_id":
        patient_id,

    "temperature":
        temperature,

    "heart_rate":
        heart_rate,

    "spo2":
        spo2,

    "systolic_bp":
        systolic_bp,

    "diastolic_bp":
        diastolic_bp
}


# ============================================================
# SAVE RESULT
# ============================================================

os.makedirs(
    DATA_DIR,
    exist_ok=True
)


try:

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

        file.flush()

except Exception as error:

    fail(
        "Could not save vitals_result.json:\n"
        + str(error)
    )


# ============================================================
# VERIFY RESULT
# ============================================================

try:

    with open(
        OUTPUT_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        saved_vitals = json.load(
            file
        )

except Exception as error:

    fail(
        "Could not verify vitals_result.json:\n"
        + str(error)
    )


# ============================================================
# VERIFY PATIENT ID
# ============================================================

try:

    saved_patient_id = int(
        saved_vitals.get(
            "patient_id"
        )
    )

except (
    ValueError,
    TypeError
):

    fail(
        "Invalid patient_id in final result."
    )


if saved_patient_id != patient_id:

    fail(
        "Final result patient ID mismatch.\n"
        f"Expected: {patient_id}\n"
        f"Saved: {saved_patient_id}"
    )


# ============================================================
# FINAL VITALS
# ============================================================

print()

print(
    "=============================================="
)

print(
    " FINAL VITALS"
)

print(
    "=============================================="
)

print()

print(
    "Patient ID:",
    saved_vitals.get(
        "patient_id"
    )
)

print(
    "Temperature:",
    saved_vitals.get(
        "temperature"
    ),
    "°C"
)

print(
    "Heart Rate:",
    saved_vitals.get(
        "heart_rate"
    ),
    "BPM"
)

print(
    "SpO2:",
    saved_vitals.get(
        "spo2"
    ),
    "%"
)

print(
    "Blood Pressure:",
    saved_vitals.get(
        "systolic_bp"
    ),
    "/",
    saved_vitals.get(
        "diastolic_bp"
    ),
    "mmHg"
)

print()

print(
    "Complete JSON:"
)

print(
    json.dumps(
        saved_vitals,
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
    "=============================================="
)

print(
    " ANALYSIS COMPLETE"
)

print(
    "=============================================="
)

print()