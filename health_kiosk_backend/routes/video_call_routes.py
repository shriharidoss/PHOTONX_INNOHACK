from flask import Blueprint, jsonify, request
import uuid
from datetime import datetime

video_call_bp = Blueprint("video_call", __name__, url_prefix="/api/video-call")

# Temporary storage for prototype
video_requests = []


@video_call_bp.route("/request", methods=["POST"])
def request_video_call():
    data = request.get_json()

    patient_id = data.get("patient_id")
    reason = data.get("reason", "General consultation")

    if not patient_id:
        return jsonify({
            "success": False,
            "message": "patient_id is required"
        }), 400

    call_request = {
        "id": len(video_requests) + 1,
        "patient_id": patient_id,
        "doctor_id": None,
        "reason": reason,
        "status": "pending",
        "room_id": None,
        "created_at": datetime.now().isoformat()
    }

    video_requests.append(call_request)

    return jsonify({
        "success": True,
        "message": "Video consultation request sent",
        "request": call_request
    }), 201


@video_call_bp.route("/requests", methods=["GET"])
def get_video_requests():
    pending_requests = [
        req for req in video_requests
        if req["status"] == "pending"
    ]

    return jsonify({
        "success": True,
        "requests": pending_requests
    })


@video_call_bp.route("/<int:request_id>/accept", methods=["POST"])
def accept_video_call(request_id):
    data = request.get_json() or {}
    doctor_id = data.get("doctor_id")

    for req in video_requests:
        if req["id"] == request_id:

            if req["status"] != "pending":
                return jsonify({
                    "success": False,
                    "message": "Request is no longer pending"
                }), 400

            room_id = "ROOM-" + uuid.uuid4().hex[:8].upper()

            req["doctor_id"] = doctor_id
            req["status"] = "accepted"
            req["room_id"] = room_id
            req["accepted_at"] = datetime.now().isoformat()

            return jsonify({
                "success": True,
                "message": "Video consultation accepted",
                "request": req
            })

    return jsonify({
        "success": False,
        "message": "Video consultation request not found"
    }), 404


@video_call_bp.route("/<int:request_id>/reject", methods=["POST"])
def reject_video_call(request_id):

    for req in video_requests:
        if req["id"] == request_id:

            if req["status"] != "pending":
                return jsonify({
                    "success": False,
                    "message": "Request is no longer pending"
                }), 400

            req["status"] = "rejected"

            return jsonify({
                "success": True,
                "message": "Video consultation rejected",
                "request": req
            })

    return jsonify({
        "success": False,
        "message": "Video consultation request not found"
    }), 404


@video_call_bp.route("/patient/<patient_id>", methods=["GET"])
def get_patient_call_status(patient_id):

    patient_requests = [
        req for req in video_requests
        if str(req["patient_id"]) == str(patient_id)
    ]

    return jsonify({
        "success": True,
        "requests": patient_requests
    })