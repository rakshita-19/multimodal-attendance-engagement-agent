from flask import Blueprint, jsonify
from backend.database.db import (
    get_session,
    get_complete_session_report
)
from backend.services.analytics.engine import SessionAnalyticsEngine

analytics_bp = Blueprint("analytics", __name__, url_prefix="/api/sessions")

@analytics_bp.route("/<session_id>/analytics", methods=["GET"])
def get_session_analytics(session_id: str):
    """Retrieve full analytics bundle, trend synthesis, and pedagogical recommendations."""
    sess = get_session(session_id)
    if not sess:
        return jsonify({"status": "error", "message": "Session not found"}), 404

    report = get_complete_session_report(session_id)
    if not report:
        return jsonify({"status": "error", "message": "Failed to assemble session report"}), 500

    engine = SessionAnalyticsEngine()
    analytics_payload = engine.generate_full_analytics(
        session_id=session_id,
        session_metadata=report["session"],
        video_summary=report["video_summary"],
        audio_summary=report["audio_summary"],
        intervals=report["intervals"],
        attendance_records=report["attendance"]
    )

    return jsonify({
        "status": "success",
        "session": report["session"],
        "video_summary": report["video_summary"],
        "audio_summary": report["audio_summary"],
        "attendance": report["attendance"],
        "intervals": report["intervals"],
        "recommendations": report["recommendations"],
        "kpis": analytics_payload["attendance_kpis"],
        "trends": analytics_payload["phase_trends"],
        "student_summary": analytics_payload["student_summary"]
    })
