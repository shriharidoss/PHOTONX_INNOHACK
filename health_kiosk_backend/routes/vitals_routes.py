from flask import Blueprint, jsonify, request

from db import save_health_reading, get_health_readings

vitals_bp = Blueprint("vitals", __name__)


# ============================================================
# RECEIVE SENSOR VITALS AND SAVE TO DATABASE
# ============================================================

@vitals_bp.route("/api/vitals", methods=["POST"])
def receive_vitals():

    data = request.get_json()

    if not data:
        return jsonify({
            "status": "error",
            "message": "No JSON data received"
        }), 400

    # --------------------------------------------------------
    # Get values from JSON
    # --------------------------------------------------------

    patient_id = data.get("patient_id")
    temperature = data.get("temperature")
    heart_rate = data.get("heart_rate")
    spo2 = data.get("spo2")
    systolic_bp = data.get("systolic_bp")
    diastolic_bp = data.get("diastolic_bp")

    # --------------------------------------------------------
    # Patient ID is required
    # --------------------------------------------------------

    if patient_id is None:
        return jsonify({
            "status": "error",
            "message": "patient_id is required"
        }), 400

    # --------------------------------------------------------
    # SAVE TO MYSQL
    # --------------------------------------------------------

    try:

        reading_id = save_health_reading(
            patient_id=patient_id,
            temperature=temperature,
            spo2=spo2,
            heart_rate=heart_rate,
            systolic_bp=systolic_bp,
            diastolic_bp=diastolic_bp
        )

    except Exception as error:

        print()
        print("================================")
        print(" DATABASE ERROR")
        print("================================")
        print(error)

        return jsonify({
            "status": "error",
            "message": "Failed to save health reading",
            "error": str(error)
        }), 500

    # --------------------------------------------------------
    # SUCCESS
    # --------------------------------------------------------

    print()
    print("================================")
    print(" VITALS SAVED TO DATABASE")
    print("================================")

    print("Reading ID:", reading_id)
    print("Patient ID:", patient_id)
    print("Temperature:", temperature)
    print("Heart Rate:", heart_rate)
    print("SpO2:", spo2)
    print("Systolic BP:", systolic_bp)
    print("Diastolic BP:", diastolic_bp)

    return jsonify({
        "status": "success",
        "message": "Vitals saved to database",
        "reading_id": reading_id,
        "data": {
            "patient_id": patient_id,
            "temperature": temperature,
            "heart_rate": heart_rate,
            "spo2": spo2,
            "systolic_bp": systolic_bp,
            "diastolic_bp": diastolic_bp
        }
    }), 200


# ============================================================
# GET PATIENT VITALS
# ============================================================

@vitals_bp.route(
    "/api/vitals/<int:patient_id>",
    methods=["GET"]
)
def get_patient_vitals(patient_id):

    try:

        readings = get_health_readings(
            patient_id
        )

        return jsonify({
            "status": "success",
            "patient_id": patient_id,
            "readings": readings
        }), 200

    except Exception as error:

        print("DATABASE ERROR:")
        print(error)

        return jsonify({
            "status": "error",
            "message": "Failed to retrieve health readings",
            "error": str(error)
        }), 500