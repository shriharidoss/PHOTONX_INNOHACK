import os
import sys
import json
import time
import subprocess

import serial


# ============================================================
# CONFIGURATION
# ============================================================

SERIAL_PORT = "COM15"

BAUD_RATE = 115200

# ESP32 measurement is 10 seconds
MEASUREMENT_TIME = 10


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_DIR = os.path.dirname(
    os.path.abspath(__file__)
)


# ============================================================
# FLASK BACKEND PATH
# ============================================================
#
# IMPORTANT:
# patient_session.json is created by the Flask backend,
# NOT inside medical_sensor_backend.
#
# Your structure is:
#
# PycharmProjects/
# └── health_kiosk_backend/
#     └── data/
#         └── patient_session.json
#
# AND:
#
# OneDrive/Desktop/kiosk innohack/
# └── medical_sensor_backend/
#     └── sensor_controller.py
#
# ============================================================

FLASK_BACKEND_DIR = os.path.join(
    os.path.expanduser("~"),
    "PycharmProjects",
    "health_kiosk_backend"
)


SESSION_FILE = os.path.join(
    FLASK_BACKEND_DIR,
    "data",
    "patient_session.json"
)


# ============================================================
# MEDICAL SENSOR BACKEND PATHS
# ============================================================

DATA_DIR = os.path.join(
    PROJECT_DIR,
    "data"
)


RAW_DIR = os.path.join(
    DATA_DIR,
    "raw"
)


PPG_FILE = os.path.join(
    RAW_DIR,
    "ppg_recording.csv"
)


VITALS_FILE = os.path.join(
    DATA_DIR,
    "vitals_result.json"
)


ANALYZE_SCRIPT = os.path.join(
    PROJECT_DIR,
    "processing",
    "analyze_vitals.py"
)


SEND_SCRIPT = os.path.join(
    PROJECT_DIR,
    "send_to_backend.py"
)


# ============================================================
# CREATE DIRECTORIES
# ============================================================

os.makedirs(
    DATA_DIR,
    exist_ok=True
)


os.makedirs(
    RAW_DIR,
    exist_ok=True
)


# ============================================================
# HEADER
# ============================================================

print()

print(
    "================================"
)

print(
    " MEDICAL SENSOR CONTROLLER"
)

print(
    "================================"
)

print()


# ============================================================
# CHECK SESSION FILE
# ============================================================

if not os.path.exists(
    SESSION_FILE
):

    print(
        "ERROR: patient_session.json not found."
    )

    print()

    print(
        "Expected location:"
    )

    print(
        SESSION_FILE
    )

    print()

    print(
        "Start the health check from the patient"
    )

    print(
        "frontend first."
    )

    sys.exit(1)


# ============================================================
# LOAD CURRENT PATIENT SESSION
# ============================================================

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

    print(
        "ERROR: Could not read patient_session.json"
    )

    print(
        str(error)
    )

    sys.exit(1)


# ============================================================
# GET CURRENT PATIENT ID
# ============================================================

patient_id = session.get(
    "patient_id"
)


if patient_id is None:

    print(
        "ERROR: patient_id missing from patient_session.json"
    )

    sys.exit(1)


try:

    patient_id = int(
        patient_id
    )

except (
    ValueError,
    TypeError
):

    print(
        "ERROR: Invalid patient_id:"
    )

    print(
        patient_id
    )

    sys.exit(1)


# ============================================================
# DISPLAY CURRENT PATIENT
# ============================================================

print(
    "CURRENT PATIENT ID:",
    patient_id
)

print()

print(
    "Session file:"
)

print(
    SESSION_FILE
)

print()


# ============================================================
# CONNECT TO ESP32
# ============================================================

print(
    "Connecting to ESP32..."
)

print(
    "Serial port:",
    SERIAL_PORT
)

print(
    "Baud rate:",
    BAUD_RATE
)

print()


try:

    esp32 = serial.Serial(

        port=SERIAL_PORT,

        baudrate=BAUD_RATE,

        timeout=1

    )


except serial.SerialException as error:

    print()

    print(
        "ERROR: Could not connect to ESP32."
    )

    print()

    print(
        str(error)
    )

    print()

    print(
        "Check:"
    )

    print(
        "1. ESP32 is connected."
    )

    print(
        "2. Correct COM port is selected."
    )

    print(
        "3. Arduino Serial Monitor is CLOSED."
    )

    sys.exit(1)


# ============================================================
# ALLOW ESP32 TO RESET
# ============================================================

time.sleep(2)


# Clear old serial data

esp32.reset_input_buffer()

esp32.reset_output_buffer()


# ============================================================
# WAIT FOR ESP32 READY
# ============================================================

print(
    "Waiting for ESP32..."
)

print()


ready = False

start_wait = time.time()


while (
    time.time() - start_wait
    < 10
):

    line = (
        esp32.readline()
        .decode(
            "utf-8",
            errors="ignore"
        )
        .strip()
    )


    if not line:

        continue


    print(
        "[ESP32]",
        line
    )


    if line == "READY":

        ready = True

        break


if not ready:

    print()

    print(
        "WARNING: ESP32 READY message not received."
    )

    print(
        "Continuing anyway..."
    )

    print()


# ============================================================
# START MEASUREMENT
# ============================================================

print()

print(
    "================================"
)

print(
    " STARTING SENSOR MEASUREMENT"
)

print(
    "================================"
)

print()

print(
    "CURRENT PATIENT ID:",
    patient_id
)

print()

print(
    "Place your finger on MAX30102."
)

print(
    "Keep your finger completely still."
)

print()


# ============================================================
# SEND COMMAND TO ESP32
# ============================================================

esp32.write(
    b"START_MEASUREMENT\n"
)

esp32.flush()


# ============================================================
# COLLECT PPG
# ============================================================

csv_rows = []

collecting = False

measurement_complete = False

measurement_start = time.time()


while (
    time.time() - measurement_start
    < MEASUREMENT_TIME + 5
):

    line = (
        esp32.readline()
        .decode(
            "utf-8",
            errors="ignore"
        )
        .strip()
    )


    if not line:

        continue


    print(
        "[ESP32]",
        line
    )


    # --------------------------------------------------------
    # CSV HEADER
    # --------------------------------------------------------

    if line == "timestamp,ir,red":

        collecting = True

        csv_rows.append(
            line
        )

        continue


    # --------------------------------------------------------
    # COLLECT CSV DATA
    # --------------------------------------------------------

    if collecting:

        parts = line.split(",")


        if len(parts) == 3:

            try:

                timestamp = int(
                    parts[0]
                )

                ir = int(
                    parts[1]
                )

                red = int(
                    parts[2]
                )


                csv_rows.append(

                    f"{timestamp},{ir},{red}"

                )

            except ValueError:

                pass


    # --------------------------------------------------------
    # IMPORTANT:
    # ESP32 sends:
    #
    # MEASUREMENT_COMPLETE
    #
    # NOT:
    #
    # MEASUREMENT COMPLETE
    # --------------------------------------------------------

    if line == "MEASUREMENT_COMPLETE":

        measurement_complete = True

        break


# ============================================================
# CLOSE SERIAL
# ============================================================

esp32.close()


# ============================================================
# CHECK COLLECTION
# ============================================================

print()

print(
    "================================"
)

print(
    " SENSOR COLLECTION COMPLETE"
)

print(
    "================================"
)

print()


sample_count = len(
    csv_rows
) - 1


print(
    "Patient ID:",
    patient_id
)

print(
    "Collected samples:",
    sample_count
)

print()


# ============================================================
# CHECK MINIMUM SAMPLES
# ============================================================

if len(csv_rows) < 211:

    print(
        "ERROR: Not enough PPG samples collected."
    )

    print(
        "Collected:",
        sample_count
    )

    print(
        "Required: at least 210"
    )

    sys.exit(1)


# ============================================================
# SAVE PPG CSV
# ============================================================

with open(
    PPG_FILE,
    "w",
    encoding="utf-8"
) as file:

    for row in csv_rows:

        file.write(
            row + "\n"
        )


print(
    "PPG recording saved:"
)

print(
    PPG_FILE
)

print()


# ============================================================
# RUN VITAL ANALYSIS
# ============================================================

print(
    "================================"
)

print(
    " RUNNING VITAL ANALYSIS"
)

print(
    "================================"
)

print()


analysis_result = subprocess.run(

    [
        sys.executable,
        ANALYZE_SCRIPT
    ],

    cwd=PROJECT_DIR

)


if analysis_result.returncode != 0:

    print()

    print(
        "ERROR: Vital analysis failed."
    )

    sys.exit(
        analysis_result.returncode
    )


# ============================================================
# CHECK VITALS JSON
# ============================================================

if not os.path.exists(
    VITALS_FILE
):

    print(
        "ERROR: vitals_result.json was not created."
    )

    sys.exit(1)


# ============================================================
# LOAD VITALS JSON
# ============================================================

with open(
    VITALS_FILE,
    "r",
    encoding="utf-8"
) as file:

    vitals = json.load(
        file
    )


# ============================================================
# VERIFY PATIENT ID
# ============================================================

result_patient_id = vitals.get(
    "patient_id"
)


if result_patient_id is None:

    print()

    print(
        "ERROR: patient_id missing from vitals_result.json"
    )

    sys.exit(1)


if int(result_patient_id) != patient_id:

    print()

    print(
        "================================"
    )

    print(
        " PATIENT ID MISMATCH!"
    )

    print(
        "================================"
    )

    print()

    print(
        "Session patient:",
        patient_id
    )

    print(
        "Result patient:",
        result_patient_id
    )

    print()

    print(
        "The measurement will NOT be sent."
    )

    print(
        "Check analyze_vitals.py."
    )

    sys.exit(1)


# ============================================================
# DISPLAY VITALS
# ============================================================

print()

print(
    "================================"
)

print(
    " MEASUREMENT RESULT"
)

print(
    "================================"
)

print()

print(
    "Patient ID:",
    patient_id
)

print()

print(
    json.dumps(
        vitals,
        indent=4
    )
)

print()


# ============================================================
# SEND TO FLASK
# ============================================================

print(
    "================================"
)

print(
    " SENDING TO FLASK"
)

print(
    "================================"
)

print()


send_result = subprocess.run(

    [
        sys.executable,
        SEND_SCRIPT
    ],

    cwd=PROJECT_DIR

)


if send_result.returncode != 0:

    print()

    print(
        "ERROR: Failed to send vitals to Flask."
    )

    sys.exit(
        send_result.returncode
    )


# ============================================================
# COMPLETE
# ============================================================

print()

print(
    "================================"
)

print(
    " HEALTH CHECK COMPLETE"
)

print(
    "================================"
)

print()

print(
    "Patient ID:",
    patient_id
)

print(
    "Heart Rate:",
    vitals.get("heart_rate"),
    "BPM"
)

print(
    "SpO2:",
    vitals.get("spo2"),
    "%"
)

print(
    "Blood Pressure:",
    vitals.get("systolic_bp"),
    "/",
    vitals.get("diastolic_bp"),
    "mmHg"
)

print()

print(
    "Data stored in Flask/MySQL."
)

print()