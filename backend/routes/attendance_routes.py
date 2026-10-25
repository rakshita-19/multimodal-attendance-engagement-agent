from flask import Blueprint, request, jsonify
from backend.database.db import (
    get_session_attendance,
    update_student_mapping,
    get_session
)

attendance_bp = Blueprint("attendance", __name__, url_prefix="/api/sessions")

@attendance_bp.route("/<session_id>/attendance", methods=["GET"])
def get_attendance(session_id: str):
    """Retrieve participant attendance records for a session."""
    sess = get_session(session_id)
    if not sess:
        return jsonify({"status": "error", "message": "Session not found"}), 404

    records = get_session_attendance(session_id)
    return jsonify({"status": "success", "session_id": session_id, "attendance": records})

@attendance_bp.route("/<session_id>/attendance/<int:track_id>", methods=["PATCH"])
def map_student_identity(session_id: str, track_id: int):
    """
    Teacher review: map temporary track ID to verified real-world student identity.
    Adheres to privacy guidelines: requires manual human confirmation rather than opaque biometric recognition.
    """
    sess = get_session(session_id)
    if not sess:
        return jsonify({"status": "error", "message": "Session not found"}), 404

    data = request.get_json() or {}
    student_name = data.get("student_name", "").strip()
    notes = data.get("notes", "").strip()

    if not student_name:
        return jsonify({"status": "error", "message": "Student name cannot be blank"}), 400

    try:
        update_student_mapping(session_id, track_id, student_name, notes=notes if notes else None)
        updated_records = get_session_attendance(session_id)
        mapped_record = next((r for r in updated_records if r["track_id"] == track_id), None)
        return jsonify({
            "status": "success",
            "message": "Student identity mapped successfully",
            "record": mapped_record
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
