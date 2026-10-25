import pytest
import sqlite3
import tempfile
from pathlib import Path
from backend.database.db import (
    init_db,
    get_connection,
    create_session,
    get_session,
    list_sessions,
    update_session_status,
    save_attendance_records,
    get_session_attendance,
    update_student_mapping,
    save_video_summary,
    get_video_summary,
    save_audio_summary,
    get_audio_summary,
    save_engagement_intervals,
    get_engagement_intervals,
    save_recommendations,
    get_recommendations,
    get_complete_session_report,
    delete_session
)
from backend.config import Config

@pytest.fixture
def temp_db(monkeypatch):
    """Fixture providing an isolated temporary database for test execution."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_path = f.name
    
    # Initialize schema in temp DB
    init_db(temp_path, Config.SCHEMA_PATH)
    monkeypatch.setattr(Config, "DATABASE_PATH", temp_path)
    
    yield temp_path
    
    # Cleanup
    try:
        Path(temp_path).unlink(missing_ok=True)
    except Exception:
        pass

def test_session_lifecycle(temp_db):
    """Test creating, reading, updating, and listing sessions."""
    sess_id = "test-session-101"
    created = create_session(sess_id, "CS401: Distributed Systems", "Classroom Hall A")
    assert created["id"] == sess_id
    assert created["title"] == "CS401: Distributed Systems"
    assert created["status"] == "created"
    
    update_session_status(sess_id, "completed", duration_seconds=120.5)
    fetched = get_session(sess_id)
    assert fetched["status"] == "completed"
    assert fetched["duration_seconds"] == 120.5

    all_sessions = list_sessions()
    assert len(all_sessions) == 1
    assert all_sessions[0]["id"] == sess_id

def test_attendance_operations(temp_db):
    """Test recording sustained-presence attendance and teacher manual mapping."""
    sess_id = "test-session-att"
    create_session(sess_id, "AI Lab")
    
    records = [
        {
            "track_id": 1,
            "first_seen_seconds": 1.0,
            "last_seen_seconds": 95.0,
            "presence_duration_seconds": 90.0,
            "presence_percentage": 90.0,
            "sustained_presence_status": "present",
            "avg_movement_score": 0.42,
            "confidence_score": 0.95,
            "notes": "Desk 1 row 2"
        },
        {
            "track_id": 2,
            "first_seen_seconds": 10.0,
            "last_seen_seconds": 25.0,
            "presence_duration_seconds": 15.0,
            "presence_percentage": 15.0,
            "sustained_presence_status": "insufficient_presence",
            "avg_movement_score": 0.15,
            "confidence_score": 0.70,
            "notes": "Left early"
        }
    ]
    save_attendance_records(sess_id, records)
    att_list = get_session_attendance(sess_id)
    assert len(att_list) == 2
    assert att_list[0]["sustained_presence_status"] == "present"
    
    # Teacher maps track_id 1 to verified student name
    update_student_mapping(sess_id, 1, "Alex Mercer", notes="Verified by roll call")
    updated_att = get_session_attendance(sess_id)
    alex_rec = [r for r in updated_att if r["track_id"] == 1][0]
    assert alex_rec["student_name"] == "Alex Mercer"
    assert "Verified" in alex_rec["notes"]

def test_multimodal_intervals_and_recommendations(temp_db):
    """Test saving intervals and pedagogical recommendations."""
    sess_id = "test-session-multi"
    create_session(sess_id, "Data Structures")
    
    # Save video summary
    save_video_summary(sess_id, {
        "total_frames": 300,
        "fps": 30.0,
        "duration_seconds": 10.0,
        "unique_tracks_detected": 4,
        "sustained_attendees_count": 3,
        "avg_headcount_per_frame": 3.2,
        "peak_headcount": 4,
        "avg_motion_energy": 0.35,
        "processing_time_seconds": 1.2,
        "quality_note": "Clear lighting"
    })
    
    # Save audio summary
    save_audio_summary(sess_id, {
        "duration_seconds": 10.0,
        "sample_rate": 16000,
        "channels": 1,
        "avg_rms_energy": 0.045,
        "peak_rms_energy": 0.18,
        "silence_percentage": 25.0,
        "speech_like_percentage": 65.0,
        "active_discussion_percentage": 10.0,
        "noise_floor": 0.005,
        "processing_time_seconds": 0.4
    })
    
    # Save intervals
    intervals = [
        {
            "interval_index": 0,
            "start_seconds": 0.0,
            "end_seconds": 5.0,
            "visible_participants": 3,
            "motion_intensity": 0.30,
            "audio_rms": 0.040,
            "speech_activity_ratio": 0.70,
            "composite_engagement_score": 75.0,
            "engagement_level": "High",
            "inferred_mode": "Active Discussion",
            "confidence_score": 0.90,
            "rule_applied": "R1_HIGH_SPEECH_AND_ATTENDANCE",
            "explanation": "High vocal activity with consistent headcount indicates interactive discussion."
        }
    ]
    save_engagement_intervals(sess_id, intervals)
    
    # Save recommendations
    recs = [
        {
            "category": "Pacing",
            "priority": "medium",
            "suggestion_text": "Introduce a quick formative checkpoint.",
            "evidence_text": "Speech activity sustained above 65% for consecutive intervals.",
            "timestamp_reference": "00:00 - 05:00",
            "rule_id": "REC_INTERACTION_CHECKPOINT"
        }
    ]
    save_recommendations(sess_id, recs)
    
    # Verify complete report
    report = get_complete_session_report(sess_id)
    assert report["session"]["title"] == "Data Structures"
    assert report["video_summary"]["total_frames"] == 300
    assert report["audio_summary"]["sample_rate"] == 16000
    assert len(report["intervals"]) == 1
    assert len(report["recommendations"]) == 1
    assert report["recommendations"][0]["rule_id"] == "REC_INTERACTION_CHECKPOINT"

def test_cascade_delete(temp_db):
    """Test that deleting a session cascades and cleans up child tables."""
    sess_id = "test-cascade"
    create_session(sess_id, "Session to delete")
    save_recommendations(sess_id, [{
        "category": "Break", "priority": "low", "suggestion_text": "Take break",
        "evidence_text": "Long session", "timestamp_reference": "end", "rule_id": "R_BREAK"
    }])
    
    assert len(get_recommendations(sess_id)) == 1
    delete_session(sess_id)
    assert get_session(sess_id) is None
    assert len(get_recommendations(sess_id)) == 0
