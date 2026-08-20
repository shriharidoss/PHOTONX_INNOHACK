import json
import requests
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

VITALS_FILE = (
    BASE_DIR
    / "data"
    / "vitals_result.json"
)

FLASK_URL = (
    "http://127.0.0.1:5000/api/vitals"
)


# ============================================================
# LOAD VITALS JSON
# ============================================================

if not VITALS_FILE.exists():

    raise FileNotFoundError(
        f"Vitals JSON not found:\n{VITALS_FILE}"
    )


with open(
    VITALS_FILE,
    "r",
    encoding="utf-8"
) as file:

    vitals = json.load(file)


print()
print("================================")
print(" MEDICAL SENSOR DATA")
print("================================")
print()

print(
    json.dumps(
        vitals,
        indent=4
    )
)


# ============================================================
# GET PATIENT ID
# ============================================================

patient_id = vitals.get(
    "patient_id"
)


if patient_id is None:

    raise ValueError(
        "patient_id is missing from vitals_result.json"
    )


# ============================================================
# CREATE API PAYLOAD
# ============================================================

payload = {

    "patient_id":
        int(patient_id),

    # DS18B20 not connected yet
    "temperature":
        vitals.get("temperature"),

    "heart_rate":
        vitals.get("heart_rate"),

    "spo2":
        vitals.get("spo2"),

    "systolic_bp":
        vitals.get("systolic_bp"),

    "diastolic_bp":
        vitals.get("diastolic_bp")
}


print()
print("================================")
print(" SENDING TO FLASK")
print("================================")
print()

print(
    json.dumps(
        payload,
        indent=4
    )
)


# ============================================================
# SEND TO FLASK
# ============================================================

try:

    response = requests.post(
        FLASK_URL,
        json=payload,
        timeout=10
    )


except requests.exceptions.ConnectionError:

    print()
    print("ERROR: Flask server is not running.")
    print()
    print(
        "Start Flask first with:"
    )
    print(
        "python app.py"
    )

    raise SystemExit(1)


except requests.exceptions.Timeout:

    print()
    print("ERROR: Flask server timed out.")

    raise SystemExit(1)


# ============================================================
# DISPLAY RESPONSE
# ============================================================

print()
print("================================")
print(" FLASK RESPONSE")
print("================================")
print()

print(
    "HTTP Status:",
    response.status_code
)

print(
    response.text
)


# ============================================================
# CHECK RESULT
# ============================================================

if response.ok:

    print()
    print("================================")
    print(" SUCCESS")
    print("================================")

    print(
        "Vitals successfully sent to Flask."
    )

    print(
        "Patient ID:",
        patient_id
    )

else:

    print()
    print("================================")
    print(" FAILED")
    print("================================")

    print(
        "Flask did not accept the vitals."
    )

    print(
        "HTTP Status:",
        response.status_code
    )