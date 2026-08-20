from flask import Blueprint, jsonify

report_bp = Blueprint("report", __name__)


@report_bp.route("/api/report")
def get_report():
    return jsonify({
        "status": "success",
        "patient": {
            "patient_id": "P001",
            "name": "Test Patient",
            "age": 25,
            "gender": "Male"
        },
        "vitals": {
            "temperature": 36.7,
            "heart_rate": 78,
            "spo2": 98,
            "systolic_bp": 120,
            "diastolic_bp": 80
        },
        "doctor_assessment": {
            "status": "pending",
            "doctor_id": None,
            "doctor_name": None,
            "notes": None,
            "reviewed_at": None
        }
    })