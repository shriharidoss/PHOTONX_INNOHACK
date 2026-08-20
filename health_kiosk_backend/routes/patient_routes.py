from flask import Blueprint, jsonify, request

from db import (
    save_patient,
    get_patient,
    get_all_patients,
    get_patient_by_phone
)


patient_bp = Blueprint(
    "patient",
    __name__
)


# =========================================================
# GET ALL PATIENTS
# =========================================================

@patient_bp.route(
    "/api/patients",
    methods=["GET"]
)
def get_patients():

    try:

        patients = get_all_patients()

        return jsonify({
            "success": True,
            "patients": patients
        })

    except Exception as e:

        print("GET PATIENTS ERROR:", e)

        return jsonify({
            "success": False,
            "message": "Failed to get patients",
            "error": str(e)
        }), 500


# =========================================================
# GET ONE PATIENT
# =========================================================

@patient_bp.route(
    "/api/patients/<int:patient_id>",
    methods=["GET"]
)
def get_single_patient(patient_id):

    try:

        patient = get_patient(
            patient_id
        )

        if patient is None:

            return jsonify({
                "success": False,
                "message": "Patient not found"
            }), 404

        return jsonify({
            "success": True,
            "patient": patient
        })

    except Exception as e:

        print("GET PATIENT ERROR:", e)

        return jsonify({
            "success": False,
            "message": "Failed to get patient",
            "error": str(e)
        }), 500


# =========================================================
# REGISTER / CREATE PATIENT
# =========================================================

@patient_bp.route(
    "/api/patients",
    methods=["POST"]
)
def create_patient():

    try:

        # -------------------------------------------------
        # Get JSON data from frontend
        # -------------------------------------------------

        data = request.get_json()

        if not data:

            return jsonify({
                "success": False,
                "message": "No JSON data received"
            }), 400


        # -------------------------------------------------
        # Read patient information
        # -------------------------------------------------

        name = data.get("name")
        age = data.get("age")
        gender = data.get("gender")
        phone = data.get("phone")


        # -------------------------------------------------
        # Validate name
        # -------------------------------------------------

        if not name:

            return jsonify({
                "success": False,
                "message": "Patient name is required"
            }), 400


        # -------------------------------------------------
        # Validate age
        # -------------------------------------------------

        if age is None:

            return jsonify({
                "success": False,
                "message": "Patient age is required"
            }), 400


        try:

            age = int(age)

        except (ValueError, TypeError):

            return jsonify({
                "success": False,
                "message": "Age must be a number"
            }), 400


        if age < 1 or age > 120:

            return jsonify({
                "success": False,
                "message": "Age must be between 1 and 120"
            }), 400


        # -------------------------------------------------
        # Validate gender
        # -------------------------------------------------

        if not gender:

            return jsonify({
                "success": False,
                "message": "Patient gender is required"
            }), 400


        # =================================================
        # CHECK FOR EXISTING PATIENT
        # =================================================
        #
        # If the phone number already exists,
        # DO NOT create another patient.
        #
        # Return the existing patient ID instead.
        #
        # This prevents:
        #
        # Patient 1 -> Test Patient
        # Patient 4 -> Test Patient   DUPLICATE
        #
        # -------------------------------------------------

        if phone:

            phone = str(phone).strip()

            existing_patient = get_patient_by_phone(
                phone
            )

            if existing_patient:

                print(
                    "Existing patient found:",
                    existing_patient
                )

                return jsonify({

                    "success": True,

                    "existing": True,

                    "message":
                        "Patient already registered",

                    "patient_id":
                        existing_patient["patient_id"],

                    "patient":
                        existing_patient

                }), 200


        # =================================================
        # CREATE NEW PATIENT
        # =================================================

        patient_id = save_patient(

            name=name,

            age=age,

            gender=gender,

            phone=phone

        )


        # -------------------------------------------------
        # Get newly created patient
        # -------------------------------------------------

        patient = get_patient(
            patient_id
        )


        # -------------------------------------------------
        # Return successful response
        # -------------------------------------------------

        return jsonify({

            "success": True,

            "existing": False,

            "message":
                "Patient registered successfully",

            "patient_id":
                patient_id,

            "patient":
                patient

        }), 201


    except Exception as e:

        print(
            "CREATE PATIENT ERROR:",
            e
        )

        return jsonify({

            "success": False,

            "message":
                "Failed to save patient",

            "error":
                str(e)

        }), 500