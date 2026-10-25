import io
import csv
from flask import Blueprint, Response, jsonify
from backend.database.db import (
    get_session,
    get_session_attendance,
    get_engagement_intervals
)

export_bp = Blueprint("export", __name__, url_prefix="/api/sessions")

@export_bp.route("/<session_id>/export/attendance.csv", methods=["GET"])
def export_attendance_csv(session_id: str):
    """Generate and stream attendance records as a standard CSV spreadsheet."""
    sess = get_session(session_id)
    if not sess:
        return jsonify({"status": "error", "message": "Session not found"}), 404

    records = get_session_attendance(session_id)
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "Track ID", "Student Name", "Status", "Presence Duration (s)",
        "Presence %", "First Seen (s)", "Last Seen (s)", "Movement Score", "Confidence", "Notes"
    ])

    for r in records:
        writer.writerow([
            r["track_id"],
            r["student_name"] or f"Unmapped (Track #{r['track_id']})",
            r["sustained_presence_status"],
            r["presence_duration_seconds"],
            r["presence_percentage"],
            r["first_seen_seconds"],
            r["last_seen_seconds"],
            r["avg_movement_score"],
            r["confidence_score"],
            r["notes"] or ""
        ])

    csv_data = output.getvalue()
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=attendance_{session_id}.csv"}
    )

@export_bp.route("/<session_id>/export/analytics.csv", methods=["GET"])
def export_analytics_csv(session_id: str):
    """Generate and stream time-series multimodal engagement intervals as CSV."""
    sess = get_session(session_id)
    if not sess:
        return jsonify({"status": "error", "message": "Session not found"}), 404

    intervals = get_engagement_intervals(session_id)
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "Interval Index", "Start Time (s)", "End Time (s)", "Visible Participants",
        "Motion Intensity", "Audio RMS", "Speech Activity Ratio", "Engagement Score",
        "Engagement Level", "Inferred Mode", "Confidence", "Rule Applied", "Explanation"
    ])

    for it in intervals:
        writer.writerow([
            it["interval_index"],
            it["start_seconds"],
            it["end_seconds"],
            it["visible_participants"],
            it["motion_intensity"],
            it["audio_rms"],
            it["speech_activity_ratio"],
            it["composite_engagement_score"],
            it["engagement_level"],
            it["inferred_mode"],
            it["confidence_score"],
            it["rule_applied"],
            it["explanation"]
        ])

    csv_data = output.getvalue()
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=analytics_{session_id}.csv"}
    )
