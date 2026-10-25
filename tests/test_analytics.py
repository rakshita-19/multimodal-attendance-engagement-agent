import pytest
from backend.services.analytics.recommendations import RecommendationEngine
from backend.services.analytics.engine import SessionAnalyticsEngine

def test_recommendation_prolonged_lull():
    """Verify recommendation triggered when classroom lull exceeds 3 intervals."""
    engine = RecommendationEngine()
    intervals = [
        {"start_seconds": 0.0, "end_seconds": 5.0, "inferred_mode": "Passive / Lull"},
        {"start_seconds": 5.0, "end_seconds": 10.0, "inferred_mode": "Passive / Lull"},
        {"start_seconds": 10.0, "end_seconds": 15.0, "inferred_mode": "Passive / Lull"},
    ]
    recs = engine.generate_recommendations("sess-lull", None, None, intervals, [])
    rule_ids = [r["rule_id"] for r in recs]
    assert "REC_PROLONGED_LULL" in rule_ids
    assert any("poll" in r["suggestion_text"] or "check-in" in r["suggestion_text"] for r in recs)

def test_recommendation_restlessness():
    """Verify recommendation triggered during restlessness / agitation."""
    engine = RecommendationEngine()
    intervals = [
        {"start_seconds": 0.0, "end_seconds": 5.0, "inferred_mode": "Transition / Restlessness"},
        {"start_seconds": 5.0, "end_seconds": 10.0, "inferred_mode": "Transition / Restlessness"},
    ]
    recs = engine.generate_recommendations("sess-restless", None, None, intervals, [])
    rule_ids = [r["rule_id"] for r in recs]
    assert "REC_RESTLESSNESS_FATIGUE" in rule_ids
    assert any("stretch break" in r["suggestion_text"] for r in recs)

def test_analytics_engine_kpis_and_phases():
    """Verify KPI and 3-phase trend calculation."""
    engine = SessionAnalyticsEngine()
    records = [
        {"sustained_presence_status": "present", "presence_duration_seconds": 60.0, "presence_percentage": 100.0},
        {"sustained_presence_status": "present", "presence_duration_seconds": 55.0, "presence_percentage": 91.6},
        {"sustained_presence_status": "partial", "presence_duration_seconds": 25.0, "presence_percentage": 41.6},
        {"sustained_presence_status": "insufficient_presence", "presence_duration_seconds": 5.0, "presence_percentage": 8.3}
    ]
    kpis = engine._compute_attendance_kpis(records, session_duration=60.0)
    assert kpis["total_tracked"] == 4
    assert kpis["present_count"] == 2
    assert kpis["partial_count"] == 1
    assert kpis["insufficient_count"] == 1
    assert kpis["attendance_rate_percentage"] == 50.0

    # 3-phase trend
    intervals = [
        {"start_seconds": 0.0, "end_seconds": 5.0, "composite_engagement_score": 60.0, "inferred_mode": "Attentive Listening / Lecture"},
        {"start_seconds": 5.0, "end_seconds": 10.0, "composite_engagement_score": 85.0, "inferred_mode": "Active Discussion"},
        {"start_seconds": 10.0, "end_seconds": 15.0, "composite_engagement_score": 70.0, "inferred_mode": "Attentive Listening / Lecture"}
    ]
    trends = engine._compute_phase_trends(intervals)
    assert len(trends["phases"]) == 3
    assert trends["phases"][1]["avg_engagement_score"] == 85.0
    assert "Peak engagement" in trends["overall_trend"]

def test_student_facing_summary():
    """Verify ethical, non-evaluative student summary contents."""
    engine = SessionAnalyticsEngine()
    summary = engine._generate_student_facing_summary(
        "Operating Systems Lecture 4",
        {"attendance_rate_percentage": 88.0},
        {"overall_trend": "High participation during Q&A."},
        interval_count=10
    )
    assert "Operating Systems" in summary["title"]
    assert "88.0%" in summary["cohort_attendance_note"]
    assert "Notice of Privacy" in summary["ethical_notice"]
    assert "does NOT analyze speech content" in summary["ethical_notice"]
