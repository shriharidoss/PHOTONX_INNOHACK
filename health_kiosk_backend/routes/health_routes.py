from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)


@health_bp.route("/api/health")
def health_check():
    return jsonify({
        "status": "success",
        "backend": "online"
    })