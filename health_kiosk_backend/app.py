from flask import Flask, jsonify
from flask_cors import CORS

from routes.health_routes import health_bp
from routes.vitals_routes import vitals_bp
from routes.patient_routes import patient_bp
from routes.report_routes import report_bp
from routes.video_call_routes import video_call_bp
from routes.measurement_routes import measurement_bp


# ============================================================
# CREATE FLASK APP
# ============================================================

app = Flask(__name__)


# ============================================================
# ENABLE CORS
# ============================================================

CORS(app)


# ============================================================
# REGISTER EXISTING API ROUTES
# ============================================================

app.register_blueprint(
    health_bp
)

app.register_blueprint(
    vitals_bp
)

app.register_blueprint(
    patient_bp
)

app.register_blueprint(
    report_bp
)


# ============================================================
# VIDEO CONSULTATION ROUTES
# ============================================================

app.register_blueprint(
    video_call_bp
)


# ============================================================
# MEASUREMENT SESSION ROUTES
# ============================================================

app.register_blueprint(
    measurement_bp
)


# ============================================================
# HOME / TEST ROUTE
# ============================================================

@app.route("/")
def home():

    return jsonify({

        "status": "success",

        "message":
            "Health Kiosk Flask Backend is running"

    })


# ============================================================
# RUN SERVER
# ============================================================

if __name__ == "__main__":

    app.run(

        debug=True,

        host="0.0.0.0",

        port=5000

    )