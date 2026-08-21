import os
import sys
import json
import time
import subprocess
import urllib.request
import urllib.error


# ============================================================
# MEDICAL SENSOR CONTROLLER - WIFI VERSION
# ============================================================
#
# COMPLETE FLOW
#
# Patient HTML
#       |
#       v
# Flask /api/measurement-session
#       |
#       v
# sensor_controller.py <patient_id>
#       |
#       v
# ESP32 over Wi-Fi
#       |
#       +---- /start
#       |
#       +---- /status
#       |
#       +---- /data
#       |
#       v
# PPG + TEMPERATURE
#       |
#       v
# ppg_recording.csv
# temperature.json
#       |
#       v
# analyze_vitals.py
#       |
#       v
# vitals_result.json
#       |
#       v
# send_to_backend.py
#       |
#       v
# Flask / MySQL
#
# ============================================================


# ============================================================
# WIFI CONFIGURATION
# ============================================================

ESP32_IP = "10.34.20.179"

ESP32_BASE_URL = (
    f"http://{ESP32_IP}"
)


# ============================================================
# MEASUREMENT SETTINGS
# ============================================================

# ESP32 performs a 10-second measurement.
MEASUREMENT_TIME = 10


# Maximum time Python will wait for ESP32 completion.
#
# This is an emergency safety timeout, NOT the measurement
# duration.
#
# Normal measurement should complete in approximately:
#
# 10 seconds
#
# ============================================================

MEASUREMENT_SAFETY_TIMEOUT = 45


# How often to check ESP32 status.
STATUS_POLL_INTERVAL = 0.5


# HTTP timeout.
HTTP_TIMEOUT = 10


# Minimum PPG samples required by processing pipeline.
MINIMUM_PPG_SAMPLES = 210


# ============================================================
# PROJECT DIRECTORY
# ============================================================

PROJECT_DIR = os.path.dirname(
    os.path.abspath(__file__)
)


# ============================================================
# DATA DIRECTORIES
# ============================================================

DATA_DIR = os.path.join(
    PROJECT_DIR,
    "data"
)

RAW_DIR = os.path.join(
    DATA_DIR,
    "raw"
)


os.makedirs(
    DATA_DIR,
    exist_ok=True
)

os.makedirs(
    RAW_DIR,
    exist_ok=True
)


# ============================================================
# FILE PATHS
# ============================================================

SESSION_FILE = os.path.join(
    DATA_DIR,
    "patient_session.json"
)


PPG_FILE = os.path.join(
    RAW_DIR,
    "ppg_recording.csv"
)


TEMPERATURE_FILE = os.path.join(
    DATA_DIR,
    "temperature.json"
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
# LOG FUNCTION
# ============================================================

def log(*messages):

    try:

        print(
            *messages,
            flush=True
        )

    except Exception:

        pass


# ============================================================
# HTTP GET HELPER
# ============================================================

def esp32_get(
    endpoint,
    timeout=HTTP_TIMEOUT
):

    url = (
        ESP32_BASE_URL
        + endpoint
    )


    request = urllib.request.Request(
        url=url,
        method="GET"
    )


    try:

        with urllib.request.urlopen(
            request,
            timeout=timeout
        ) as response:

            raw_data = response.read()


        text = raw_data.decode(
            "utf-8",
            errors="ignore"
        )


        return text


    except urllib.error.HTTPError as error:

        raise RuntimeError(
            f"ESP32 HTTP error {error.code}: {error.reason}"
        )


    except urllib.error.URLError as error:

        raise RuntimeError(
            f"Could not connect to ESP32: {error.reason}"
        )


    except TimeoutError:

        raise RuntimeError(
            "ESP32 request timed out."
        )


    except Exception as error:

        raise RuntimeError(
            f"ESP32 request failed: {error}"
        )


# ============================================================
# ESP32 JSON GET HELPER
# ============================================================

def esp32_get_json(
    endpoint,
    timeout=HTTP_TIMEOUT
):

    response_text = esp32_get(
        endpoint,
        timeout
    )


    try:

        return json.loads(
            response_text
        )


    except json.JSONDecodeError as error:

        raise RuntimeError(
            "ESP32 returned invalid JSON.\n"
            f"Endpoint: {endpoint}\n"
            f"Response: {response_text[:500]}\n"
            f"Error: {error}"
        )


# ============================================================
# HEADER
# ============================================================

log()

log(
    "=============================================="
)

log(
    "       MEDICAL SENSOR CONTROLLER"
)

log(
    "              WIFI VERSION"
)

log(
    "=============================================="
)

log()

log(
    "Project directory:"
)

log(
    PROJECT_DIR
)

log()

log(
    "ESP32 Wi-Fi address:"
)

log(
    ESP32_IP
)

log()


# ============================================================
# GET PATIENT ID
# ============================================================
#
# Priority:
#
# 1. Patient ID passed directly by Flask
# 2. patient_session.json
#
# ============================================================

patient_id = None


# ============================================================
# READ COMMAND-LINE PATIENT ID
# ============================================================

if len(sys.argv) >= 2:

    command_line_patient_id = (
        sys.argv[1]
    )


    try:

        patient_id = int(
            command_line_patient_id
        )


    except (
        ValueError,
        TypeError
    ):

        log()

        log(
            "ERROR: Invalid patient ID passed by Flask:"
        )

        log(
            command_line_patient_id
        )

        log()

        sys.exit(1)


# ============================================================
# FALLBACK TO PATIENT SESSION
# ============================================================

if patient_id is None:

    if not os.path.exists(
        SESSION_FILE
    ):

        log()

        log(
            "ERROR: patient_session.json not found."
        )

        log()

        log(
            "Expected:"
        )

        log(
            SESSION_FILE
        )

        log()

        log(
            "Start the Health Check from the patient page."
        )

        log()

        sys.exit(1)


    log(
        "Using patient session:"
    )

    log(
        SESSION_FILE
    )

    log()


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

        log()

        log(
            "ERROR: Could not read patient_session.json"
        )

        log(
            str(error)
        )

        log()

        sys.exit(1)


    patient_id = session.get(
        "patient_id"
    )


# ============================================================
# VALIDATE PATIENT ID
# ============================================================

if patient_id is None:

    log()

    log(
        "ERROR: patient_id is missing."
    )

    log()

    sys.exit(1)


try:

    patient_id = int(
        patient_id
    )


except (
    ValueError,
    TypeError
):

    log()

    log(
        "ERROR: Invalid patient_id:"
    )

    log(
        patient_id
    )

    log()

    sys.exit(1)


if patient_id <= 0:

    log()

    log(
        "ERROR: Invalid patient ID."
    )

    log()

    sys.exit(1)


# ============================================================
# WRITE CURRENT PATIENT TO SESSION FILE
# ============================================================

session_data = {

    "patient_id":
        patient_id

}


try:

    with open(
        SESSION_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            session_data,
            file,
            indent=4
        )

        file.flush()

        os.fsync(
            file.fileno()
        )


except Exception as error:

    log()

    log(
        "ERROR: Could not update patient_session.json"
    )

    log(
        str(error)
    )

    log()

    sys.exit(1)


# ============================================================
# VERIFY CURRENT PATIENT
# ============================================================

try:

    with open(
        SESSION_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        verified_session = json.load(
            file
        )


    verified_patient_id = int(
        verified_session.get(
            "patient_id"
        )
    )


except Exception as error:

    log()

    log(
        "ERROR: Could not verify patient session."
    )

    log(
        str(error)
    )

    log()

    sys.exit(1)


if verified_patient_id != patient_id:

    log()

    log(
        "=============================================="
    )

    log(
        " PATIENT SESSION MISMATCH"
    )

    log(
        "=============================================="
    )

    log()

    log(
        "Command-line patient:",
        patient_id
    )

    log(
        "Session patient:",
        verified_patient_id
    )

    log()

    sys.exit(1)


# ============================================================
# CURRENT PATIENT
# ============================================================

log(
    "=============================================="
)

log(
    " CURRENT PATIENT"
)

log(
    "=============================================="
)

log()

log(
    "CURRENT PATIENT ID:",
    patient_id
)

log()

log(
    "This measurement belongs to Patient:",
    patient_id
)

log()


# ============================================================
# DELETE OLD RESULT FILES
# ============================================================

for old_file in [

    VITALS_FILE,

    TEMPERATURE_FILE,

    PPG_FILE

]:

    if os.path.exists(
        old_file
    ):

        try:

            os.remove(
                old_file
            )

            log(
                "Old file deleted:",
                old_file
            )


        except Exception as error:

            log()

            log(
                "WARNING: Could not delete old file:"
            )

            log(
                old_file
            )

            log(
                str(error)
            )

            log()


log()


# ============================================================
# CHECK PROCESSING FILES
# ============================================================

if not os.path.exists(
    ANALYZE_SCRIPT
):

    log()

    log(
        "ERROR: analyze_vitals.py not found."
    )

    log(
        ANALYZE_SCRIPT
    )

    log()

    sys.exit(1)


if not os.path.exists(
    SEND_SCRIPT
):

    log()

    log(
        "ERROR: send_to_backend.py not found."
    )

    log(
        SEND_SCRIPT
    )

    log()

    sys.exit(1)


# ============================================================
# TEST ESP32 WIFI CONNECTION
# ============================================================

log(
    "=============================================="
)

log(
    " CONNECTING TO ESP32 OVER WI-FI"
)

log(
    "=============================================="
)

log()

log(
    "ESP32 IP:",
    ESP32_IP
)

log()


try:

    status_before = esp32_get_json(
        "/status",
        timeout=5
    )


except Exception as error:

    log()

    log(
        "ERROR: Could not connect to ESP32 over Wi-Fi."
    )

    log()

    log(
        str(error)
    )

    log()

    log(
        "Check:"
    )

    log(
        "1. ESP32 is powered."
    )

    log(
        "2. ESP32 is connected to DOSS ONEPLUS."
    )

    log(
        "3. Laptop is connected to DOSS ONEPLUS."
    )

    log(
        "4. ESP32 IP is correct:"
    )

    log(
        ESP32_IP
    )

    log()

    sys.exit(1)


log(
    "ESP32 Wi-Fi connection successful."
)

log()

log(
    "ESP32 status:"
)

log(
    json.dumps(
        status_before,
        indent=4
    )
)

log()


# ============================================================
# RESET ESP32 BEFORE NEW MEASUREMENT
# ============================================================
#
# This prevents a previous completed measurement from being
# accidentally reused.
#
# ============================================================

try:

    reset_result = esp32_get_json(
        "/reset",
        timeout=5
    )


    log(
        "ESP32 reset:"
    )

    log(
        json.dumps(
            reset_result,
            indent=4
        )
    )

    log()


except Exception as error:

    log()

    log(
        "WARNING: ESP32 reset request failed."
    )

    log(
        str(error)
    )

    log()

    log(
        "Continuing with measurement attempt..."
    )

    log()


# ============================================================
# START SENSOR MEASUREMENT
# ============================================================

log(
    "=============================================="
)

log(
    " STARTING SENSOR MEASUREMENT"
)

log(
    "=============================================="
)

log()

log(
    "CURRENT PATIENT:",
    patient_id
)

log()

log(
    "Place your finger on MAX30102."
)

log(
    "Keep your finger still."
)

log()

log(
    "Starting PPG + temperature collection..."
)

log()


# ============================================================
# SEND START COMMAND OVER WIFI
# ============================================================

try:

    start_result = esp32_get_json(
        "/start",
        timeout=5
    )


except Exception as error:

    log()

    log(
        "ERROR: Could not start ESP32 measurement."
    )

    log()

    log(
        str(error)
    )

    log()

    sys.exit(1)


log(
    "ESP32 start response:"
)

log(
    json.dumps(
        start_result,
        indent=4
    )
)

log()


# ============================================================
# VERIFY START RESPONSE
# ============================================================

start_status = str(
    start_result.get(
        "status",
        ""
    )
).lower()


if start_status not in [

    "measurement_started",
    "started"

]:

    if start_status == "already_running":

        log()

        log(
            "WARNING: ESP32 reported that a measurement is already running."
        )

        log()

        log(
            "Waiting for that measurement to finish..."
        )

        log()

    else:

        log()

        log(
            "ERROR: ESP32 did not accept measurement start."
        )

        log(
            json.dumps(
                start_result,
                indent=4
            )
        )

        log()

        sys.exit(1)


# ============================================================
# WAIT FOR MEASUREMENT COMPLETE
# ============================================================

log(
    "=============================================="
)

log(
    " COLLECTING SENSOR DATA"
)

log(
    "=============================================="
)

log()

log(
    "Measurement duration:",
    MEASUREMENT_TIME,
    "seconds"
)

log()


measurement_started_at = time.time()

measurement_complete = False

last_status = None


while True:

    elapsed = (
        time.time()
        - measurement_started_at
    )


    # --------------------------------------------------------
    # SAFETY TIMEOUT
    # --------------------------------------------------------

    if (
        elapsed
        >=
        MEASUREMENT_SAFETY_TIMEOUT
    ):

        log()

        log(
            "ERROR: ESP32 measurement safety timeout reached."
        )

        log(
            "ESP32 did not report completion within",
            MEASUREMENT_SAFETY_TIMEOUT,
            "seconds."
        )

        log()

        sys.exit(1)


    # --------------------------------------------------------
    # GET STATUS
    # --------------------------------------------------------

    try:

        status = esp32_get_json(
            "/status",
            timeout=5
        )


    except Exception as error:

        log()

        log(
            "WARNING: Could not read ESP32 status:"
        )

        log(
            str(error)
        )

        log(
            "Retrying..."
        )

        log()

        time.sleep(
            STATUS_POLL_INTERVAL
        )

        continue


    current_measurement = str(
        status.get(
            "measurement",
            ""
        )
    ).lower()


    samples_now = status.get(
        "samples",
        0
    )


    temperature_now = status.get(
        "temperature",
        None
    )


    # --------------------------------------------------------
    # DISPLAY ONLY WHEN STATUS CHANGES OR SAMPLES CHANGE
    # --------------------------------------------------------

    status_signature = (
        current_measurement,
        samples_now,
        temperature_now
    )


    if (
        status_signature
        !=
        last_status
    ):

        log(
            "ESP32:",
            current_measurement,
            "| samples:",
            samples_now,
            "| temperature:",
            temperature_now
        )

        last_status = (
            status_signature
        )


    # --------------------------------------------------------
    # COMPLETE
    # --------------------------------------------------------

    if (
        current_measurement
        == "complete"
    ):

        measurement_complete = True

        log()

        log(
            "=============================================="
        )

        log(
            " ESP32 REPORTED MEASUREMENT COMPLETE"
        )

        log(
            "=============================================="
        )

        log()

        break


    # --------------------------------------------------------
    # WAIT
    # --------------------------------------------------------

    time.sleep(
        STATUS_POLL_INTERVAL
    )


# ============================================================
# DOWNLOAD FINAL SENSOR DATA
# ============================================================

log(
    "=============================================="
)

log(
    " DOWNLOADING SENSOR DATA"
)

log(
    "=============================================="
)

log()


try:

    sensor_data = esp32_get_json(
        "/data",
        timeout=30
    )


except Exception as error:

    log()

    log(
        "ERROR: Could not download sensor data from ESP32."
    )

    log()

    log(
        str(error)
    )

    log()

    sys.exit(1)


# ============================================================
# VERIFY DATA RESPONSE
# ============================================================

data_status = str(
    sensor_data.get(
        "status",
        ""
    )
).lower()


if data_status != "complete":

    log()

    log(
        "ERROR: ESP32 data is not marked complete."
    )

    log()

    log(
        json.dumps(
            sensor_data,
            indent=4
        )[:2000]
    )

    log()

    sys.exit(1)


# ============================================================
# GET PPG SAMPLES
# ============================================================

ppg_samples = sensor_data.get(
    "samples",
    []
)


if not isinstance(
    ppg_samples,
    list
):

    log()

    log(
        "ERROR: ESP32 returned invalid PPG sample list."
    )

    log()

    sys.exit(1)


# ============================================================
# GET TEMPERATURE
# ============================================================

temperature_value = sensor_data.get(
    "temperature"
)


# ============================================================
# VALIDATE TEMPERATURE
# ============================================================

if temperature_value is None:

    log()

    log(
        "ERROR: No temperature value received from ESP32."
    )

    log()

    log(
        "ESP32 must return a valid temperature."
    )

    log()

    sys.exit(1)


try:

    temperature_value = float(
        temperature_value
    )


except (
    ValueError,
    TypeError
):

    log()

    log(
        "ERROR: Invalid temperature received:"
    )

    log(
        temperature_value
    )

    log()

    sys.exit(1)


# ============================================================
# CONVERT PPG SAMPLES
# ============================================================

csv_rows = [

    "timestamp,ir,red"

]


valid_sample_count = 0


for sample in ppg_samples:

    if not isinstance(
        sample,
        dict
    ):

        continue


    try:

        timestamp = int(
            sample.get(
                "timestamp"
            )
        )

        ir = int(
            sample.get(
                "ir"
            )
        )

        red = int(
            sample.get(
                "red"
            )
        )


    except (
        ValueError,
        TypeError
    ):

        continue


    # --------------------------------------------------------
    # BASIC VALIDATION
    # --------------------------------------------------------

    if timestamp < 0:

        continue


    if ir <= 0:

        continue


    if red <= 0:

        continue


    csv_rows.append(
        f"{timestamp},{ir},{red}"
    )


    valid_sample_count += 1


# ============================================================
# SENSOR COLLECTION SUMMARY
# ============================================================

log()

log(
    "=============================================="
)

log(
    " SENSOR COLLECTION COMPLETE"
)

log(
    "=============================================="
)

log()

log(
    "Patient ID:",
    patient_id
)

log(
    "Collected PPG samples:",
    valid_sample_count
)

log(
    "Temperature received:",
    temperature_value
)

log(
    "Measurement complete:",
    measurement_complete
)

log()


# ============================================================
# REQUIRE MEASUREMENT COMPLETE
# ============================================================

if not measurement_complete:

    log()

    log(
        "ERROR: ESP32 measurement is not complete."
    )

    log()

    sys.exit(1)


# ============================================================
# REQUIRE PPG
# ============================================================

if (
    valid_sample_count
    <
    MINIMUM_PPG_SAMPLES
):

    log()

    log(
        "ERROR: Not enough PPG samples collected."
    )

    log()

    log(
        "Collected:",
        valid_sample_count
    )

    log(
        "Required:",
        MINIMUM_PPG_SAMPLES
    )

    log()

    sys.exit(1)


# ============================================================
# SAVE PPG
# ============================================================

try:

    with open(
        PPG_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        for row in csv_rows:

            file.write(
                row + "\n"
            )

        file.flush()

        os.fsync(
            file.fileno()
        )


except Exception as error:

    log()

    log(
        "ERROR: Could not save PPG recording."
    )

    log(
        str(error)
    )

    log()

    sys.exit(1)


log(
    "PPG recording saved:"
)

log(
    PPG_FILE
)

log()


# ============================================================
# SAVE TEMPERATURE
# ============================================================

log(
    "=============================================="
)

log(
    " SAVING TEMPERATURE"
)

log(
    "=============================================="
)

log()


temperature_data = {

    "patient_id":
        patient_id,

    "temperature":
        temperature_value

}


try:

    with open(
        TEMPERATURE_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            temperature_data,
            file,
            indent=4
        )

        file.flush()

        os.fsync(
            file.fileno()
        )


except Exception as error:

    log()

    log(
        "ERROR: Could not create temperature.json"
    )

    log(
        str(error)
    )

    log()

    sys.exit(1)


log(
    "Temperature saved:"
)

log(
    temperature_value,
    "°C"
)

log()


# ============================================================
# VERIFY TEMPERATURE FILE
# ============================================================

try:

    with open(
        TEMPERATURE_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        verified_temperature = json.load(
            file
        )


except Exception as error:

    log()

    log(
        "ERROR: Could not verify temperature.json"
    )

    log(
        str(error)
    )

    log()

    sys.exit(1)


# ============================================================
# VERIFY TEMPERATURE PATIENT
# ============================================================

try:

    temperature_patient_id = int(
        verified_temperature.get(
            "patient_id"
        )
    )


except (
    ValueError,
    TypeError
):

    log()

    log(
        "ERROR: Invalid patient ID in temperature.json."
    )

    log()

    sys.exit(1)


if (
    temperature_patient_id
    !=
    patient_id
):

    log()

    log(
        "=============================================="
    )

    log(
        " TEMPERATURE PATIENT ID MISMATCH"
    )

    log(
        "=============================================="
    )

    log()

    log(
        "Current patient:",
        patient_id
    )

    log(
        "Temperature patient:",
        temperature_patient_id
    )

    log()

    sys.exit(1)


# ============================================================
# RUN VITAL ANALYSIS
# ============================================================

log(
    "=============================================="
)

log(
    " RUNNING VITAL ANALYSIS"
)

log(
    "=============================================="
)

log()

log(
    "Patient ID:",
    patient_id
)

log(
    "PPG samples:",
    valid_sample_count
)

log(
    "Temperature:",
    temperature_value,
    "°C"
)

log()


# ============================================================
# RUN analyze_vitals.py
# ============================================================

try:

    analysis_result = subprocess.run(

        [
            sys.executable,
            ANALYZE_SCRIPT
        ],

        cwd=PROJECT_DIR,

        check=False

    )


except Exception as error:

    log()

    log(
        "ERROR: Could not start analyze_vitals.py"
    )

    log(
        str(error)
    )

    log()

    sys.exit(1)


log()

log(
    "analyze_vitals.py returned:",
    analysis_result.returncode
)

log()


if (
    analysis_result.returncode
    !=
    0
):

    log()

    log(
        "=============================================="
    )

    log(
        " ERROR: VITAL ANALYSIS FAILED"
    )

    log(
        "=============================================="
    )

    log()

    log(
        "analyze_vitals.py returned:",
        analysis_result.returncode
    )

    log()

    sys.exit(
        analysis_result.returncode
    )


# ============================================================
# CHECK VITALS RESULT
# ============================================================

if not os.path.exists(
    VITALS_FILE
):

    log()

    log(
        "ERROR: vitals_result.json was not created."
    )

    log(
        VITALS_FILE
    )

    log()

    sys.exit(1)


# ============================================================
# READ VITALS RESULT
# ============================================================

try:

    with open(
        VITALS_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        vitals = json.load(
            file
        )


except Exception as error:

    log()

    log(
        "ERROR: Could not read vitals_result.json"
    )

    log(
        str(error)
    )

    log()

    sys.exit(1)


# ============================================================
# VERIFY RESULT PATIENT ID
# ============================================================

try:

    result_patient_id = int(
        vitals.get(
            "patient_id"
        )
    )


except (
    ValueError,
    TypeError
):

    log()

    log(
        "ERROR: Invalid patient_id in vitals_result.json."
    )

    log()

    sys.exit(1)


# ============================================================
# FINAL PATIENT SAFETY CHECK
# ============================================================

if (
    result_patient_id
    !=
    patient_id
):

    log()

    log(
        "=============================================="
    )

    log(
        "       PATIENT ID MISMATCH!"
    )

    log(
        "=============================================="
    )

    log()

    log(
        "Current patient:",
        patient_id
    )

    log(
        "Result patient:",
        result_patient_id
    )

    log()

    log(
        "The measurement will NOT be sent."
    )

    log()

    sys.exit(1)


# ============================================================
# FORCE REAL TEMPERATURE INTO FINAL RESULT
# ============================================================

vitals["temperature"] = (
    temperature_value
)


# ============================================================
# SAVE FINAL RESULT AGAIN
# ============================================================

try:

    with open(
        VITALS_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            vitals,
            file,
            indent=4
        )

        file.flush()

        os.fsync(
            file.fileno()
        )


except Exception as error:

    log()

    log(
        "ERROR: Could not update vitals_result.json"
    )

    log(
        str(error)
    )

    log()

    sys.exit(1)


# ============================================================
# DISPLAY FINAL VITALS
# ============================================================

log()

log(
    "=============================================="
)

log(
    " FINAL VITALS"
)

log(
    "=============================================="
)

log()

log(
    "Patient ID:",
    patient_id
)

log()

log(
    "Temperature:",
    vitals.get(
        "temperature"
    ),
    "°C"
)

log(
    "Heart Rate:",
    vitals.get(
        "heart_rate"
    ),
    "BPM"
)

log(
    "SpO2:",
    vitals.get(
        "spo2"
    ),
    "%"
)

log(
    "Blood Pressure:",
    vitals.get(
        "systolic_bp"
    ),
    "/",
    vitals.get(
        "diastolic_bp"
    ),
    "mmHg"
)

log()

log(
    "Complete result:"
)

log(
    json.dumps(
        vitals,
        indent=4
    )
)

log()


# ============================================================
# SEND RESULT TO FLASK / MYSQL
# ============================================================

log(
    "=============================================="
)

log(
    " SENDING RESULT TO FLASK"
)

log(
    "=============================================="
)

log()


try:

    send_result = subprocess.run(

        [
            sys.executable,
            SEND_SCRIPT
        ],

        cwd=PROJECT_DIR,

        check=False

    )


except Exception as error:

    log()

    log(
        "ERROR: Could not start send_to_backend.py"
    )

    log(
        str(error)
    )

    log()

    sys.exit(1)


# ============================================================
# CHECK DATABASE SEND
# ============================================================

if (
    send_result.returncode
    !=
    0
):

    log()

    log(
        "=============================================="
    )

    log(
        " ERROR: FAILED TO SEND VITALS TO FLASK"
    )

    log(
        "=============================================="
    )

    log()

    log(
        "Return code:",
        send_result.returncode
    )

    log()

    sys.exit(
        send_result.returncode
    )


# ============================================================
# ALL DONE
# ============================================================

log()

log(
    "=============================================="
)

log(
    "       HEALTH CHECK COMPLETE"
)

log(
    "=============================================="
)

log()

log(
    "Patient ID:",
    patient_id
)

log(
    "Temperature:",
    vitals.get(
        "temperature"
    ),
    "°C"
)

log(
    "Heart Rate:",
    vitals.get(
        "heart_rate"
    ),
    "BPM"
)

log(
    "SpO2:",
    vitals.get(
        "spo2"
    ),
    "%"
)

log(
    "Blood Pressure:",
    vitals.get(
        "systolic_bp"
    ),
    "/",
    vitals.get(
        "diastolic_bp"
    ),
    "mmHg"
)

log()

log(
    "Data stored in Flask/MySQL."
)

log()

log(
    "=============================================="
)

log(
    "              ALL DONE"
)

log(
    "=============================================="
)

log()


sys.exit(0)