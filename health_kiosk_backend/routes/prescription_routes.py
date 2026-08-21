from flask import Blueprint, request, jsonify

from db import (
    save_prescription,
    get_prescriptions
)


# ============================================================
# PRESCRIPTION BLUEPRINT
# ============================================================

prescription_bp = Blueprint(
    "prescription",
    __name__,
    url_prefix="/api"
)


# ============================================================
# SAVE PRESCRIPTION
# POST /api/prescriptions
# ============================================================

@prescription_bp.route(
    "/prescriptions",
    methods=["POST"]
)
def create_prescription():

    try:

        data = request.get_json()

        if not data:

            return jsonify({
                "success": False,
                "message": "No prescription data received"
            }), 400


        # ----------------------------------------------------
        # GET DATA FROM REQUEST
        # ----------------------------------------------------

        patient_id = data.get("patient_id")
        doctor_id = data.get("doctor_id")
        medicine = data.get("medicine")
        dosage = data.get("dosage")
        frequency = data.get("frequency")
        duration = data.get("duration")
        instructions = data.get("instructions")


        # ----------------------------------------------------
        # VALIDATE PATIENT ID
        # ----------------------------------------------------

        if patient_id is None or str(patient_id).strip() == "":

            return jsonify({
                "success": False,
                "message": "patient_id is required"
            }), 400


        # ----------------------------------------------------
        # VALIDATE DOCTOR ID
        # ----------------------------------------------------

        if doctor_id is None or str(doctor_id).strip() == "":

            return jsonify({
                "success": False,
                "message": "doctor_id is required"
            }), 400


        # ----------------------------------------------------
        # VALIDATE MEDICINE
        # ----------------------------------------------------

        if medicine is None or str(medicine).strip() == "":

            return jsonify({
                "success": False,
                "message": "medicine is required"
            }), 400


        # ----------------------------------------------------
        # SAVE PRESCRIPTION
        # ----------------------------------------------------

        prescription_id = save_prescription(

            patient_id=patient_id,

            doctor_id=doctor_id,

            medicine=medicine,

            dosage=dosage,

            frequency=frequency,

            duration=duration,

            instructions=instructions

        )


        # ----------------------------------------------------
        # SUCCESS RESPONSE
        # ----------------------------------------------------

        return jsonify({

            "success": True,

            "message":
                "Prescription saved successfully",

            "prescription_id":
                prescription_id

        }), 201


    except Exception as error:

        print(
            "PRESCRIPTION SAVE ERROR:",
            error
        )


        return jsonify({

            "success": False,

            "message":
                "Failed to save prescription",

            "error":
                str(error)

        }), 500


# ============================================================
# GET PATIENT PRESCRIPTIONS
# GET /api/prescriptions/<patient_id>
# ============================================================

@prescription_bp.route(
    "/prescriptions/<int:patient_id>",
    methods=["GET"]
)
def get_patient_prescriptions(
    patient_id
):

    try:

        prescriptions = get_prescriptions(
            patient_id
        )


        return jsonify({

            "success": True,

            "patient_id":
                patient_id,

            "prescriptions":
                prescriptions

        }), 200


    except Exception as error:

        print(
            "PRESCRIPTION GET ERROR:",
            error
        )


        return jsonify({

            "success": False,

            "message":
                "Failed to retrieve prescriptions",

            "error":
                str(error)

        }), 500