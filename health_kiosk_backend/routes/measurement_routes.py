from flask import Blueprint, jsonify, request
from pathlib import Path
import json
import os
import sys
import subprocess
import threading
import logging


# ============================================================
# MEASUREMENT BLUEPRINT
# ============================================================

measurement_bp = Blueprint(
    "measurement",
    __name__
)


# ============================================================
# SAFE LOGGER
# ============================================================

logger = logging.getLogger(
    "measurement_routes"
)

if not logger.handlers:

    handler = logging.StreamHandler()

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s"
    )

    handler.setFormatter(
        formatter
    )

    logger.addHandler(
        handler
    )

    logger.setLevel(
        logging.INFO
    )


def safe_log(*messages):

    """
    Logging must never be allowed to crash Flask.
    """

    try:

        logger.info(
            " ".join(
                str(message)
                for message in messages
            )
        )

    except Exception:

        pass


# ============================================================
# FLASK BACKEND DIRECTORY
# ============================================================

BASE_DIR = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)


# ============================================================
# FLASK DATA DIRECTORY
# ============================================================

BACKEND_DATA_DIR = (
    BASE_DIR / "data"
)

BACKEND_DATA_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# MEDICAL SENSOR BACKEND
# ============================================================

SENSOR_BACKEND_DIR = Path(
    r"C:\Users\shrih\OneDrive\Documents\PHOTONX_INNOHACK\medical_sensor_backend"
)


# ============================================================
# SENSOR DATA DIRECTORY
# ============================================================

SENSOR_DATA_DIR = (
    SENSOR_BACKEND_DIR / "data"
)

SENSOR_DATA_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# PATIENT SESSION FILE
# ============================================================

PATIENT_SESSION_FILE = (
    SENSOR_DATA_DIR /
    "patient_session.json"
)


# ============================================================
# SENSOR LOG FILE
# ============================================================

SENSOR_LOG_FILE = (
    SENSOR_DATA_DIR /
    "sensor_controller.log"
)


# ============================================================
# SENSOR CONTROLLER
# ============================================================

SENSOR_CONTROLLER = (
    SENSOR_BACKEND_DIR /
    "sensor_controller.py"
)


# ============================================================
# PYTHON EXECUTABLE
# ============================================================

SENSOR_PYTHON = Path(
    os.environ.get(
        "SENSOR_PYTHON",
        r"C:\Users\shrih\AppData\Local\Programs\Python\Python313\python.exe"
    )
)


# ============================================================
# FALLBACK TO CURRENT PYTHON
# ============================================================

if not SENSOR_PYTHON.exists():

    SENSOR_PYTHON = Path(
        sys.executable
    )


# ============================================================
# GLOBAL MEASUREMENT STATE
# ============================================================

sensor_process = None

current_measurement_patient_id = None

last_finished_patient_id = None

last_return_code = None

measurement_state = "idle"

measurement_lock = threading.Lock()


# ============================================================
# READ PATIENT SESSION
# ============================================================

def read_session_patient():

    try:

        if not PATIENT_SESSION_FILE.exists():

            return None


        with open(
            PATIENT_SESSION_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(
                file
            )


        patient_id = data.get(
            "patient_id"
        )


        if patient_id is None:

            return None


        return int(
            patient_id
        )


    except Exception as error:

        safe_log(
            "WARNING: Could not read patient session:",
            error
        )

        return None


# ============================================================
# SAVE PATIENT SESSION
# ============================================================

def save_patient_session(
    patient_id
):

    session_data = {

        "patient_id":
            int(patient_id)

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

        file.flush()

        os.fsync(
            file.fileno()
        )


# ============================================================
# CLEAN FINISHED SENSOR PROCESS
# ============================================================

def cleanup_finished_process():

    global sensor_process
    global current_measurement_patient_id
    global last_finished_patient_id
    global last_return_code
    global measurement_state


    if sensor_process is None:

        return


    try:

        return_code = (
            sensor_process.poll()
        )

    except Exception:

        return_code = None


    # --------------------------------------------------------
    # PROCESS IS STILL RUNNING
    # --------------------------------------------------------

    if return_code is None:

        return


    # --------------------------------------------------------
    # PROCESS HAS FINISHED
    # --------------------------------------------------------

    finished_patient_id = (
        current_measurement_patient_id
    )


    last_finished_patient_id = (
        finished_patient_id
    )


    last_return_code = (
        return_code
    )


    if return_code == 0:

        measurement_state = "complete"

    else:

        measurement_state = "failed"


    safe_log(
        "=============================================="
    )

    safe_log(
        "SENSOR CONTROLLER FINISHED"
    )

    safe_log(
        "=============================================="
    )

    safe_log(
        "Patient ID:",
        finished_patient_id
    )

    safe_log(
        "Return code:",
        return_code
    )

    safe_log(
        "Measurement state:",
        measurement_state
    )


    # --------------------------------------------------------
    # RELEASE OLD PROCESS
    # --------------------------------------------------------

    sensor_process = None

    current_measurement_patient_id = None


# ============================================================
# CHECK WHETHER SENSOR IS REALLY RUNNING
# ============================================================

def is_sensor_running():

    global sensor_process


    cleanup_finished_process()


    if sensor_process is None:

        return False


    try:

        return (
            sensor_process.poll()
            is None
        )

    except Exception:

        return False


# ============================================================
# START MEASUREMENT
# ============================================================

@measurement_bp.route(
    "/api/measurement-session",
    methods=["POST"]
)
def create_measurement_session():

    global sensor_process
    global current_measurement_patient_id
    global last_finished_patient_id
    global last_return_code
    global measurement_state


    with measurement_lock:

        try:

            # ==================================================
            # CLEAN OLD FINISHED PROCESS
            # ==================================================

            cleanup_finished_process()


            # ==================================================
            # READ FRONTEND JSON
            # ==================================================

            data = request.get_json(
                silent=True
            )


            if not data:

                return jsonify({

                    "status":
                        "error",

                    "message":
                        "No JSON data received"

                }), 400


            # ==================================================
            # GET PATIENT ID
            # ==================================================

            patient_id = data.get(
                "patient_id"
            )


            if patient_id is None:

                return jsonify({

                    "status":
                        "error",

                    "message":
                        "patient_id is required"

                }), 400


            # ==================================================
            # CONVERT PATIENT ID TO INTEGER
            # ==================================================

            try:

                patient_id = int(
                    patient_id
                )

            except (
                ValueError,
                TypeError
            ):

                return jsonify({

                    "status":
                        "error",

                    "message":
                        "Invalid patient_id"

                }), 400


            if patient_id <= 0:

                return jsonify({

                    "status":
                        "error",

                    "message":
                        "Invalid patient_id"

                }), 400


            safe_log(
                "=============================================="
            )

            safe_log(
                "AUTOMATIC HEALTH MEASUREMENT"
            )

            safe_log(
                "=============================================="
            )

            safe_log(
                "PATIENT ID RECEIVED:",
                patient_id
            )


            # ==================================================
            # CHECK SENSOR BACKEND DIRECTORY
            # ==================================================

            if not SENSOR_BACKEND_DIR.exists():

                measurement_state = "failed"

                return jsonify({

                    "status":
                        "error",

                    "message":
                        "Medical sensor backend folder not found",

                    "path":
                        str(SENSOR_BACKEND_DIR)

                }), 500


            # ==================================================
            # CHECK SENSOR CONTROLLER
            # ==================================================

            if not SENSOR_CONTROLLER.exists():

                measurement_state = "failed"

                return jsonify({

                    "status":
                        "error",

                    "message":
                        "sensor_controller.py not found",

                    "path":
                        str(SENSOR_CONTROLLER)

                }), 500


            # ==================================================
            # CHECK PYTHON
            # ==================================================

            if not SENSOR_PYTHON.exists():

                measurement_state = "failed"

                return jsonify({

                    "status":
                        "error",

                    "message":
                        "Python executable not found",

                    "path":
                        str(SENSOR_PYTHON)

                }), 500


            # ==================================================
            # CHECK WHETHER A REAL PROCESS IS RUNNING
            # ==================================================

            if is_sensor_running():

                return jsonify({

                    "status":
                        "error",

                    "message":
                        "A health measurement is already running",

                    "patient_id":
                        current_measurement_patient_id

                }), 409


            # ==================================================
            # RESET STATE FOR NEW MEASUREMENT
            # ==================================================

            sensor_process = None

            current_measurement_patient_id = None

            last_finished_patient_id = None

            last_return_code = None

            measurement_state = "starting"


            # ==================================================
            # SAVE NEW PATIENT
            # ==================================================

            save_patient_session(
                patient_id
            )


            # ==================================================
            # VERIFY PATIENT SESSION
            # ==================================================

            verified_patient_id = (
                read_session_patient()
            )


            if verified_patient_id != patient_id:

                measurement_state = "failed"

                last_finished_patient_id = (
                    patient_id
                )

                last_return_code = 1

                return jsonify({

                    "status":
                        "error",

                    "message":
                        "Patient session verification failed",

                    "expected_patient_id":
                        patient_id,

                    "saved_patient_id":
                        verified_patient_id

                }), 500


            safe_log(
                "Patient session saved successfully."
            )

            safe_log(
                "CURRENT PATIENT ID:",
                verified_patient_id
            )


            # ==================================================
            # SET CURRENT PATIENT
            # ==================================================

            current_measurement_patient_id = (
                patient_id
            )


            # ==================================================
            # DELETE OLD SENSOR LOG
            # ==================================================

            try:

                if SENSOR_LOG_FILE.exists():

                    SENSOR_LOG_FILE.unlink()

            except Exception as error:

                safe_log(
                    "WARNING: Could not delete old sensor log:",
                    error
                )


            # ==================================================
            # OPEN SENSOR LOG
            # ==================================================

            try:

                log_file = open(
                    SENSOR_LOG_FILE,
                    "w",
                    encoding="utf-8"
                )

            except Exception as error:

                sensor_process = None

                current_measurement_patient_id = None

                last_finished_patient_id = (
                    patient_id
                )

                last_return_code = 1

                measurement_state = "failed"

                return jsonify({

                    "status":
                        "error",

                    "message":
                        "Could not create sensor log",

                    "error":
                        str(error)

                }), 500


            # ==================================================
            # SENSOR CONTROLLER COMMAND
            # ==================================================

            command = [

                str(SENSOR_PYTHON),

                str(SENSOR_CONTROLLER),

                str(patient_id)

            ]


            safe_log(
                "Starting sensor controller..."
            )

            safe_log(
                "Patient ID passed to sensor controller:",
                patient_id
            )

            safe_log(
                "Command:",
                " ".join(command)
            )


            # ==================================================
            # START SENSOR CONTROLLER
            # ==================================================

            try:

                if os.name == "nt":

                    creation_flags = (
                        subprocess.CREATE_NO_WINDOW
                    )

                else:

                    creation_flags = 0


                sensor_process = subprocess.Popen(

                    command,

                    cwd=str(
                        SENSOR_BACKEND_DIR
                    ),

                    stdout=log_file,

                    stderr=subprocess.STDOUT,

                    stdin=subprocess.DEVNULL,

                    creationflags=creation_flags

                )


            except Exception as error:

                try:

                    log_file.close()

                except Exception:

                    pass


                sensor_process = None

                current_measurement_patient_id = None

                last_finished_patient_id = (
                    patient_id
                )

                last_return_code = 1

                measurement_state = "failed"


                return jsonify({

                    "status":
                        "error",

                    "message":
                        "Failed to start sensor controller",

                    "error":
                        str(error),

                    "command":
                        command

                }), 500


            # ==================================================
            # CLOSE PARENT LOG HANDLE
            # ==================================================

            try:

                log_file.close()

            except Exception:

                pass


            # ==================================================
            # PROCESS STARTED
            # ==================================================

            measurement_state = "running"


            safe_log(
                "Sensor controller started automatically."
            )

            safe_log(
                "Process ID:",
                sensor_process.pid
            )

            safe_log(
                "Current patient:",
                patient_id
            )


            # ==================================================
            # RETURN SUCCESS TO FRONTEND
            # ==================================================

            return jsonify({

                "status":
                    "success",

                "message":
                    "Health measurement started automatically",

                "patient_id":
                    patient_id,

                "measurement":
                    "running",

                "sensor_process_id":
                    sensor_process.pid

            }), 200


        except Exception as error:

            measurement_state = "failed"

            last_finished_patient_id = (
                patient_id
                if "patient_id" in locals()
                else None
            )

            last_return_code = 1


            safe_log(
                "MEASUREMENT START ERROR:",
                error
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
    global current_measurement_patient_id
    global last_finished_patient_id
    global last_return_code
    global measurement_state


    with measurement_lock:

        # ==================================================
        # CHECK FINISHED PROCESS
        # ==================================================

        cleanup_finished_process()


        # ==================================================
        # PROCESS STILL RUNNING
        # ==================================================

        if sensor_process is not None:

            try:

                return_code = (
                    sensor_process.poll()
                )

            except Exception:

                return_code = None


            if return_code is None:

                return jsonify({

                    "status":
                        "running",

                    "measurement":
                        "in_progress",

                    "patient_id":
                        current_measurement_patient_id

                }), 200


        # ==================================================
        # MEASUREMENT COMPLETE
        # ==================================================
        #
        # IMPORTANT:
        #
        # DO NOT reset measurement_state to "idle" here.
        #
        # The frontend may poll more than once.
        # Keeping "complete" prevents the frontend from
        # missing the completed state.
        #
        # A NEW measurement automatically resets the state.
        #
        # ==================================================

        if measurement_state == "complete":

            finished_patient_id = (
                last_finished_patient_id
            )


            return jsonify({

                "status":
                    "success",

                "measurement":
                    "complete",

                "patient_id":
                    finished_patient_id,

                "return_code":
                    0

            }), 200


        # ==================================================
        # MEASUREMENT FAILED
        # ==================================================
        #
        # IMPORTANT:
        #
        # DO NOT reset measurement_state to "idle" here.
        #
        # The frontend can safely poll multiple times and
        # still receive the failure information.
        #
        # ==================================================

        if measurement_state == "failed":

            finished_patient_id = (
                last_finished_patient_id
            )


            return_code = (
                last_return_code
            )


            error_message = ""


            try:

                if SENSOR_LOG_FILE.exists():

                    error_message = (
                        SENSOR_LOG_FILE.read_text(
                            encoding="utf-8",
                            errors="ignore"
                        )[-6000:]
                    )

            except Exception:

                error_message = ""


            return jsonify({

                "status":
                    "error",

                "measurement":
                    "failed",

                "patient_id":
                    finished_patient_id,

                "return_code":
                    return_code,

                "error_log":
                    error_message

            }), 200


        # ==================================================
        # STARTING
        # ==================================================

        if measurement_state == "starting":

            return jsonify({

                "status":
                    "starting",

                "measurement":
                    "starting",

                "patient_id":
                    current_measurement_patient_id

            }), 200


        # ==================================================
        # IDLE
        # ==================================================

        return jsonify({

            "status":
                "idle",

            "measurement":
                "not_running",

            "patient_id":
                None

        }), 200


# ============================================================
# CURRENT MEASUREMENT PATIENT
# ============================================================

@measurement_bp.route(
    "/api/current-measurement-patient",
    methods=["GET"]
)
def current_measurement_patient():

    session_patient_id = (
        read_session_patient()
    )


    return jsonify({

        "status":
            "success",

        "memory_patient_id":
            current_measurement_patient_id,

        "session_patient_id":
            session_patient_id

    }), 200


# ============================================================
# FORCE RESET MEASUREMENT
# ============================================================

@measurement_bp.route(
    "/api/measurement-reset",
    methods=["POST"]
)
def reset_measurement():

    global sensor_process
    global current_measurement_patient_id
    global last_finished_patient_id
    global last_return_code
    global measurement_state


    with measurement_lock:

        # ==================================================
        # CHECK REAL SENSOR PROCESS
        # ==================================================

        if sensor_process is not None:

            try:

                running = (
                    sensor_process.poll()
                    is None
                )

            except Exception:

                running = False


            if running:

                force = (
                    request.args.get(
                        "force",
                        "false"
                    ).lower()
                    == "true"
                )


                # ==========================================
                # DON'T STOP A REAL MEASUREMENT
                # ==========================================

                if not force:

                    return jsonify({

                        "status":
                            "error",

                        "message":
                            "A real sensor measurement is still running",

                        "patient_id":
                            current_measurement_patient_id

                    }), 409


                # ==========================================
                # FORCE STOP
                # ==========================================

                try:

                    sensor_process.terminate()

                    sensor_process.wait(
                        timeout=5
                    )

                except Exception:

                    try:

                        sensor_process.kill()

                    except Exception:

                        pass


        # ==================================================
        # CLEAR EVERYTHING
        # ==================================================

        sensor_process = None

        current_measurement_patient_id = None

        last_finished_patient_id = None

        last_return_code = None

        measurement_state = "idle"


        safe_log(
            "MEASUREMENT STATE RESET"
        )


        return jsonify({

            "status":
                "success",

            "message":
                "Measurement state reset"

        }), 200