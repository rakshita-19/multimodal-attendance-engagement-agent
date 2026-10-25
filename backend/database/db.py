import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from backend.config import Config

logger = logging.getLogger(__name__)

def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Obtain a SQLite connection with foreign keys enabled and row factory set."""
    path = db_path or Config.DATABASE_PATH
    conn = sqlite3.connect(path, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db(db_path: Optional[str] = None, schema_path: Optional[Path] = None):
    """Initialize database tables using schema.sql."""
    Config.ensure_directories()
    schema = schema_path or Config.SCHEMA_PATH
    
    if not schema.exists():
        raise FileNotFoundError(f"Schema file not found at {schema}")
        
    with open(schema, "r", encoding="utf-8") as f:
        sql = f.read()

    conn = get_connection(db_path)
    try:
        with conn:
            conn.executescript(sql)
        logger.info(f"Database initialized successfully at {db_path or Config.DATABASE_PATH}")
    finally:
        conn.close()

# ----------------- Database Access Utilities ----------------- #

def create_session(session_id: str, title: str, notes: Optional[str] = None, 
                   video_file_name: Optional[str] = None, audio_file_name: Optional[str] = None) -> Dict[str, Any]:
    """Create a new classroom analysis session."""
    conn = get_connection()
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO sessions (id, title, notes, video_file_name, audio_file_name, status)
                VALUES (?, ?, ?, ?, ?, 'created')
                """,
                (session_id, title, notes, video_file_name, audio_file_name)
            )
        return get_session(session_id)
    finally:
        conn.close()

def update_session_status(session_id: str, status: str, duration_seconds: Optional[float] = None,
                          raw_files_retained: Optional[int] = None):
    """Update status, duration, and retention flag of a session."""
    conn = get_connection()
    try:
        with conn:
            if duration_seconds is not None and raw_files_retained is not None:
                conn.execute(
                    "UPDATE sessions SET status = ?, duration_seconds = ?, raw_files_retained = ? WHERE id = ?",
                    (status, duration_seconds, raw_files_retained, session_id)
                )
            elif duration_seconds is not None:
                conn.execute(
                    "UPDATE sessions SET status = ?, duration_seconds = ? WHERE id = ?",
                    (status, duration_seconds, session_id)
                )
            elif raw_files_retained is not None:
                conn.execute(
                    "UPDATE sessions SET status = ?, raw_files_retained = ? WHERE id = ?",
                    (status, raw_files_retained, session_id)
                )
            else:
                conn.execute("UPDATE sessions SET status = ? WHERE id = ?", (status, session_id))
    finally:
        conn.close()

def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve session metadata by ID."""
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def list_sessions(limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieve list of recent sessions."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM sessions ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

def delete_session(session_id: str) -> bool:
    """Delete a session and all cascading records."""
    conn = get_connection()
    try:
        with conn:
            res = conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            return res.rowcount > 0
    finally:
        conn.close()

# ----------------- Attendance Operations ----------------- #

def save_attendance_records(session_id: str, records: List[Dict[str, Any]]):
    """Save or update attendance records for tracked participants."""
    conn = get_connection()
    try:
        with conn:
            for r in records:
                conn.execute(
                    """
                    INSERT INTO attendance_records 
                    (session_id, track_id, student_name, first_seen_seconds, last_seen_seconds,
                     presence_duration_seconds, presence_percentage, sustained_presence_status,
                     avg_movement_score, confidence_score, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(session_id, track_id) DO UPDATE SET
                        first_seen_seconds=excluded.first_seen_seconds,
                        last_seen_seconds=excluded.last_seen_seconds,
                        presence_duration_seconds=excluded.presence_duration_seconds,
                        presence_percentage=excluded.presence_percentage,
                        sustained_presence_status=excluded.sustained_presence_status,
                        avg_movement_score=excluded.avg_movement_score,
                        confidence_score=excluded.confidence_score,
                        notes=excluded.notes
                    """,
                    (
                        session_id,
                        r["track_id"],
                        r.get("student_name"),
                        r["first_seen_seconds"],
                        r["last_seen_seconds"],
                        r["presence_duration_seconds"],
                        r["presence_percentage"],
                        r["sustained_presence_status"],
                        r.get("avg_movement_score", 0.0),
                        r.get("confidence_score", 1.0),
                        r.get("notes", "")
                    )
                )
    finally:
        conn.close()

def update_student_mapping(session_id: str, track_id: int, student_name: str, notes: Optional[str] = None):
    """Teacher review: map temporary track ID to verified student identity."""
    conn = get_connection()
    try:
        with conn:
            conn.execute(
                """
                UPDATE attendance_records 
                SET student_name = ?, notes = COALESCE(?, notes)
                WHERE session_id = ? AND track_id = ?
                """,
                (student_name, notes, session_id, track_id)
            )
    finally:
        conn.close()

def get_session_attendance(session_id: str) -> List[Dict[str, Any]]:
    """Retrieve all attendance records for a session."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT * FROM attendance_records 
            WHERE session_id = ? 
            ORDER BY sustained_presence_status DESC, track_id ASC
            """,
            (session_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

# ----------------- Vision & Audio Summaries ----------------- #

def save_video_summary(session_id: str, summary: Dict[str, Any]):
    """Insert or update video processing summary."""
    conn = get_connection()
    try:
        with conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO video_summaries
                (session_id, total_frames, fps, duration_seconds, unique_tracks_detected,
                 sustained_attendees_count, avg_headcount_per_frame, peak_headcount,
                 avg_motion_energy, processing_time_seconds, quality_note)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    summary["total_frames"],
                    summary["fps"],
                    summary["duration_seconds"],
                    summary["unique_tracks_detected"],
                    summary["sustained_attendees_count"],
                    summary["avg_headcount_per_frame"],
                    summary["peak_headcount"],
                    summary["avg_motion_energy"],
                    summary.get("processing_time_seconds", 0.0),
                    summary.get("quality_note", "")
                )
            )
    finally:
        conn.close()

def get_video_summary(session_id: str) -> Optional[Dict[str, Any]]:
    """Get video summary for a session."""
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM video_summaries WHERE session_id = ?", (session_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def save_audio_summary(session_id: str, summary: Dict[str, Any]):
    """Insert or update audio processing summary."""
    conn = get_connection()
    try:
        with conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO audio_summaries
                (session_id, duration_seconds, sample_rate, channels, avg_rms_energy,
                 peak_rms_energy, silence_percentage, speech_like_percentage,
                 active_discussion_percentage, noise_floor, processing_time_seconds)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    summary["duration_seconds"],
                    summary["sample_rate"],
                    summary["channels"],
                    summary["avg_rms_energy"],
                    summary["peak_rms_energy"],
                    summary["silence_percentage"],
                    summary["speech_like_percentage"],
                    summary["active_discussion_percentage"],
                    summary["noise_floor"],
                    summary.get("processing_time_seconds", 0.0)
                )
            )
    finally:
        conn.close()

def get_audio_summary(session_id: str) -> Optional[Dict[str, Any]]:
    """Get audio summary for a session."""
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM audio_summaries WHERE session_id = ?", (session_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

# ----------------- Engagement Intervals ----------------- #

def save_engagement_intervals(session_id: str, intervals: List[Dict[str, Any]]):
    """Save multimodal time-series engagement intervals."""
    conn = get_connection()
    try:
        with conn:
            for it in intervals:
                conn.execute(
                    """
                    INSERT INTO engagement_intervals
                    (session_id, interval_index, start_seconds, end_seconds,
                     visible_participants, motion_intensity, audio_rms, speech_activity_ratio,
                     composite_engagement_score, engagement_level, inferred_mode,
                     confidence_score, rule_applied, explanation)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(session_id, interval_index) DO UPDATE SET
                        start_seconds=excluded.start_seconds,
                        end_seconds=excluded.end_seconds,
                        visible_participants=excluded.visible_participants,
                        motion_intensity=excluded.motion_intensity,
                        audio_rms=excluded.audio_rms,
                        speech_activity_ratio=excluded.speech_activity_ratio,
                        composite_engagement_score=excluded.composite_engagement_score,
                        engagement_level=excluded.engagement_level,
                        inferred_mode=excluded.inferred_mode,
                        confidence_score=excluded.confidence_score,
                        rule_applied=excluded.rule_applied,
                        explanation=excluded.explanation
                    """,
                    (
                        session_id,
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
                        it.get("confidence_score", 1.0),
                        it.get("rule_applied", ""),
                        it.get("explanation", "")
                    )
                )
    finally:
        conn.close()

def get_engagement_intervals(session_id: str) -> List[Dict[str, Any]]:
    """Get time-series engagement intervals for charts and analytics."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM engagement_intervals WHERE session_id = ? ORDER BY interval_index ASC",
            (session_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

# ----------------- Recommendations ----------------- #

def save_recommendations(session_id: str, recommendations: List[Dict[str, Any]]):
    """Save pedagogical feedback recommendations."""
    conn = get_connection()
    try:
        with conn:
            # Delete existing recommendations for this session before inserting refreshed ones
            conn.execute("DELETE FROM recommendations WHERE session_id = ?", (session_id,))
            for rec in recommendations:
                conn.execute(
                    """
                    INSERT INTO recommendations
                    (session_id, category, priority, suggestion_text, evidence_text, timestamp_reference, rule_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        session_id,
                        rec["category"],
                        rec["priority"],
                        rec["suggestion_text"],
                        rec["evidence_text"],
                        rec.get("timestamp_reference", "Overall Session"),
                        rec["rule_id"]
                    )
                )
    finally:
        conn.close()

def get_recommendations(session_id: str) -> List[Dict[str, Any]]:
    """Get pedagogical recommendations for a session."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM recommendations WHERE session_id = ? ORDER BY id ASC",
            (session_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

# ----------------- Complete Session Analytics Bundle ----------------- #

def get_complete_session_report(session_id: str) -> Optional[Dict[str, Any]]:
    """Assemble all session data into a unified analytics payload."""
    sess = get_session(session_id)
    if not sess:
        return None

    return {
        "session": sess,
        "video_summary": get_video_summary(session_id),
        "audio_summary": get_audio_summary(session_id),
        "attendance": get_session_attendance(session_id),
        "intervals": get_engagement_intervals(session_id),
        "recommendations": get_recommendations(session_id)
    }
