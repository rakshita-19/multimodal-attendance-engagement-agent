import pytest
from backend.services.agent.alignment import SignalAligner
from backend.services.agent.multimodal_agent import MultimodalEngagementAgent

def test_signal_aligner():
    """Verify alignment of mismatched or missing interval lengths."""
    aligner = SignalAligner(window_size_seconds=5.0)
    
    vision_intervals = [
        {"interval_index": 0, "visible_participants": 4, "motion_intensity": 0.20},
        {"interval_index": 1, "visible_participants": 4, "motion_intensity": 0.25}
    ]
    audio_intervals = [
        {"interval_index": 0, "audio_rms": 0.03, "speech_activity_ratio": 0.60},
        {"interval_index": 1, "audio_rms": 0.02, "speech_activity_ratio": 0.40},
        {"interval_index": 2, "audio_rms": 0.01, "speech_activity_ratio": 0.10}  # extra audio interval
    ]
    
    aligned = aligner.align(vision_intervals, audio_intervals, session_duration_seconds=15.0)
    assert len(aligned) == 3
    assert aligned[0]["has_vision"] is True
    assert aligned[0]["has_audio"] is True
    assert aligned[0]["confidence_score"] == 0.95
    # Window 2 should have audio only
    assert aligned[2]["has_vision"] is False
    assert aligned[2]["has_audio"] is True
    assert aligned[2]["confidence_score"] == 0.60

def test_multimodal_rule_inferences():
    """Test deterministic rule activations."""
    agent = MultimodalEngagementAgent(window_size_seconds=5.0)
    
    # 1. High speech + calm room => Active Discussion
    score, level, mode, rule, exp = agent._evaluate_window_rules(
        visible_participants=5, motion_intensity=0.10, audio_rms=0.03, speech_ratio=0.55,
        has_vision=True, has_audio=True
    )
    assert mode == "Active Discussion"
    assert level == "High"
    assert "ACTIVE_DISCUSSION" in rule
    assert score >= 80.0

    # 2. High motion + High speech => Collaborative Group Work
    score, level, mode, rule, exp = agent._evaluate_window_rules(
        visible_participants=3, motion_intensity=0.35, audio_rms=0.03, speech_ratio=0.45,
        has_vision=True, has_audio=True
    )
    assert mode == "Collaborative Group Work"
    assert level == "High"

    # 3. High motion + low speech => Transition / Restlessness
    score, level, mode, rule, exp = agent._evaluate_window_rules(
        visible_participants=4, motion_intensity=0.50, audio_rms=0.005, speech_ratio=0.05,
        has_vision=True, has_audio=True
    )
    assert mode == "Transition / Restlessness"
    assert level == "Disrupted/Restless"

    # 4. Low motion + low speech => Passive / Lull
    score, level, mode, rule, exp = agent._evaluate_window_rules(
        visible_participants=4, motion_intensity=0.05, audio_rms=0.004, speech_ratio=0.05,
        has_vision=True, has_audio=True
    )
    assert mode == "Passive / Lull"
    assert level == "Low"

def test_agent_analyze_session():
    """Test full session analysis pipeline in MultimodalEngagementAgent."""
    agent = MultimodalEngagementAgent(window_size_seconds=5.0)
    v_intervals = [
        {"interval_index": 0, "visible_participants": 5, "motion_intensity": 0.15},
        {"interval_index": 1, "visible_participants": 5, "motion_intensity": 0.18}
    ]
    a_intervals = [
        {"interval_index": 0, "audio_rms": 0.02, "speech_activity_ratio": 0.50},
        {"interval_index": 1, "audio_rms": 0.02, "speech_activity_ratio": 0.30}
    ]
    
    result = agent.analyze_session("test-sess-multimodal", v_intervals, a_intervals, 10.0)
    assert "intervals" in result
    assert len(result["intervals"]) == 2
    assert "session_engagement_index" in result
    assert 0 <= result["session_engagement_index"] <= 100
    assert "dominant_mode" in result
    assert "mode_distribution" in result
    assert result["data_quality_confidence"] > 0.8
