import uuid
from flask import Blueprint, request, jsonify
from backend.database.db import (
    create_session,
    get_session,
    list_sessions,
    delete_session
)

session_bp = Blueprint("sessions", __name__, url_prefix="/api/sessions")

@session_bp.route("", methods=["GET"])
def get_all_sessions():
    """List recent classroom sessions."""
    try:
        limit = int(request.args.get("limit", 50))
        sessions = list_sessions(limit=limit)
        return jsonify({"status": "success", "sessions": sessions})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@session_bp.route("", methods=["POST"])
def create_new_session():
    """Create a new session record."""
    data = request.get_json() or {}
    title = data.get("title", "").strip()
    if not title:
        title = f"Classroom Session {uuid.uuid4().hex[:6].upper()}"

    notes = data.get("notes", "").strip()
    session_id = f"sess_{uuid.uuid4().hex[:10]}"

    try:
        new_sess = create_session(session_id=session_id, title=title, notes=notes)
        return jsonify({"status": "success", "session": new_sess}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@session_bp.route("/<session_id>", methods=["GET"])
def get_single_session(session_id: str):
    """Get metadata for a specific session."""
    sess = get_session(session_id)
    if not sess:
        return jsonify({"status": "error", "message": "Session not found"}), 404
    return jsonify({"status": "success", "session": sess})

@session_bp.route("/<session_id>", methods=["DELETE"])
def delete_single_session(session_id: str):
    """Delete a session and all cascading records."""
    success = delete_session(session_id)
    if not success:
        return jsonify({"status": "error", "message": "Session not found or delete failed"}), 404
    return jsonify({"status": "success", "message": "Session deleted successfully"})
