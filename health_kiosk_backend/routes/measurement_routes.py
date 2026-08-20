from flask import Blueprint, jsonify, request
from pathlib import Path
import json
import os
import sys
import subprocess


measurement_bp = Blueprint(
    "measurement",
    __name__
)


# ============================================================
# FLASK BACKEND DATA DIRECTORY
# ============================================================

BASE_DIR = Path(
    __file__
).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"

DATA_DIR.mkdir(
    exist_ok=True
)

PATIENT_SESSION_FILE = (
    DATA_DIR / "patient_session.json"
)


# ============================================================
# MEDICAL SENSOR BACKEND
# ============================================================

SENSOR_BACKEND_DIR = Path(
    r"C:\Users\shrih\OneDrive\Documents\Desktop\kiosk innohack\medical_sensor_backend"
)


SENSOR_CONTROLLER = (
    SENSOR_BACKEND_DIR /
    "sensor_controller.py"
)


# ============================================================
# PYTHON USED TO RUN SENSOR CONTROLLER
# ============================================================

SENSOR_PYTHON = Path(
    os.environ.get(
        "SENSOR_PYTHON",
        r"C:\Users\shrih\AppData\Local\Programs\Python\Python313\python.exe"
    )
)


if not SENSOR_PYTHON.exists():

    SENSOR_PYTHON = Path(
        sys.executable
    )


# ============================================================
# CURRENT SENSOR PROCESS
# ============================================================

sensor_process = None


# ============================================================
# CREATE MEASUREMENT SESSION
# AND AUTOMATICALLY START SENSOR
# ============================================================

@measurement_bp.route(
    "/api/measurement-session",
    methods=["POST"]
)
def create_measurement_session():

    global sensor_process

    try:

        data = request.get_json(
            silent=True
        )

        if not data:

            return jsonify({
                "status": "error",
                "message": "No JSON data received"
            }), 400


        # ----------------------------------------------------
        # CURRENT PATIENT
        # ----------------------------------------------------

        patient_id = data.get(
            "patient_id"
        )


        if patient_id is None:

            return jsonify({
                "status": "error",
                "message": "patient_id is required"
            }), 400


        try:

            patient_id = int(
                patient_id
            )

        except (
            ValueError,
            TypeError
        ):

            return jsonify({
                "status": "error",
                "message": "Invalid patient_id"
            }), 400


        if patient_id <= 0:

            return jsonify({
                "status": "error",
                "message": "Invalid patient_id"
            }), 400


        # ----------------------------------------------------
        # CHECK SENSOR BACKEND
        # ----------------------------------------------------

        if not SENSOR_BACKEND_DIR.exists():

            return jsonify({

                "status": "error",

                "message":
                    "medical_sensor_backend folder not found",

                "path":
                    str(SENSOR_BACKEND_DIR)

            }), 500


        # ----------------------------------------------------
        # CHECK SENSOR CONTROLLER
        # ----------------------------------------------------

        if not SENSOR_CONTROLLER.exists():

            return jsonify({

                "status": "error",

                "message":
                    "sensor_controller.py not found",

                "path":
                    str(SENSOR_CONTROLLER)

            }), 500


        # ----------------------------------------------------
        # CHECK PYTHON
        # ----------------------------------------------------

        if not SENSOR_PYTHON.exists():

            return jsonify({

                "status": "error",

                "message":
                    "Python executable not found",

                "path":
                    str(SENSOR_PYTHON)

            }), 500


        # ----------------------------------------------------
        # DON'T START TWO MEASUREMENTS
        # ----------------------------------------------------

        if sensor_process is not None:

            if sensor_process.poll() is None:

                return jsonify({

                    "status": "error",

                    "message":
                        "A health measurement is already running",

                    "patient_id":
                        patient_id

                }), 409


            sensor_process = None


        # ----------------------------------------------------
        # SAVE CURRENT PATIENT SESSION
        # ----------------------------------------------------

        session_data = {

            "patient_id":
                patient_id

        }


        with open(
            PATIENT_SESSION_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                session_data,
                file,
                indent=4
            )


        print()
        print("================================")
        print(" AUTOMATIC HEALTH CHECK")
        print("================================")

        print(
            "Current Patient ID:",
            patient_id
        )

        print(
            "Session file:",
            PATIENT_SESSION_FILE
        )

        print(
            "Sensor controller:",
            SENSOR_CONTROLLER
        )

        print(
            "Python:",
            SENSOR_PYTHON
        )


        # ----------------------------------------------------
        # START SENSOR CONTROLLER AUTOMATICALLY
        # ----------------------------------------------------

        creation_flags = 0

        if os.name == "nt":

            creation_flags = getattr(
                subprocess,
                "CREATE_NEW_CONSOLE",
                0
            )


        sensor_process = subprocess.Popen(

            [
                str(SENSOR_PYTHON),
                str(SENSOR_CONTROLLER)
            ],

            cwd=str(
                SENSOR_BACKEND_DIR
            ),

            creationflags=creation_flags

        )


        print(
            "Sensor controller started automatically."
        )

        print(
            "Process ID:",
            sensor_process.pid
        )

        print()


        return jsonify({

            "status":
                "success",

            "message":
                "Health measurement started automatically",

            "patient_id":
                patient_id,

            "measurement":
                "running"

        }), 200


    except Exception as error:

        print()
        print("================================")
        print(" MEASUREMENT START ERROR")
        print("================================")

        print(
            str(error)
        )


        return jsonify({

            "status":
                "error",

            "message":
                "Failed to start health measurement",

            "error":
                str(error)

        }), 500


# ============================================================
# MEASUREMENT STATUS
# ============================================================

@measurement_bp.route(
    "/api/measurement-status",
    methods=["GET"]
)
def measurement_status():

    global sensor_process


    # --------------------------------------------------------
    # NO PROCESS
    # --------------------------------------------------------

    if sensor_process is None:

        return jsonify({

            "status":
                "idle",

            "measurement":
                "not_running"

        }), 200


    # --------------------------------------------------------
    # PROCESS STILL RUNNING
    # --------------------------------------------------------

    return_code = sensor_process.poll()


    if return_code is None:

        return jsonify({

            "status":
                "running",

            "measurement":
                "in_progress"

        }), 200


    # --------------------------------------------------------
    # PROCESS FINISHED
    # --------------------------------------------------------

    sensor_process = None


    if return_code == 0:

        return jsonify({

            "status":
                "success",

            "measurement":
                "complete",

            "return_code":
                0

        }), 200


    return jsonify({

        "status":
            "error",

        "measurement":
            "failed",

        "return_code":
            return_code

    }), 200