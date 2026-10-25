import numpy as np
from typing import List, Dict, Any, Tuple
from backend.services.agent.alignment import SignalAligner
from backend.config import Config

class MultimodalEngagementAgent:
    """
    Transparent, rule-based reasoning agent that fuses video and audio streams
    into explainable classroom engagement levels and observable dynamic modes.
    Enforces ethical non-surveillance principles.
    """
    def __init__(self, window_size_seconds: float = Config.WINDOW_SIZE_SECONDS):
        self.aligner = SignalAligner(window_size_seconds=window_size_seconds)

    def analyze_session(self, 
                        session_id: str,
                        vision_intervals: List[Dict[str, Any]], 
                        audio_intervals: List[Dict[str, Any]],
                        session_duration_seconds: float) -> Dict[str, Any]:
        """
        Perform deterministic multimodal alignment, inference, and summary generation.
        """
        # Step 1: Align signals across time windows
        aligned_windows = self.aligner.align(
            vision_intervals=vision_intervals,
            audio_intervals=audio_intervals,
            session_duration_seconds=session_duration_seconds
        )

        processed_intervals = []
        mode_counts: Dict[str, int] = {}
        composite_scores: List[float] = []

        # Step 2: Apply rule-based reasoning on each aligned window
        for window in aligned_windows:
            idx = window["interval_index"]
            start_s = window["start_seconds"]
            end_s = window["end_seconds"]
            v_count = window["visible_participants"]
            motion = window["motion_intensity"]
            rms = window["audio_rms"]
            speech_ratio = window["speech_activity_ratio"]
            confidence = window["confidence_score"]

            score, level, mode, rule, explanation = self._evaluate_window_rules(
                v_count, motion, rms, speech_ratio, window["has_vision"], window["has_audio"]
            )

            composite_scores.append(score)
            mode_counts[mode] = mode_counts.get(mode, 0) + 1

            processed_intervals.append({
                "session_id": session_id,
                "interval_index": idx,
                "start_seconds": start_s,
                "end_seconds": end_s,
                "visible_participants": v_count,
                "motion_intensity": motion,
                "audio_rms": rms,
                "speech_activity_ratio": speech_ratio,
                "composite_engagement_score": round(score, 1),
                "engagement_level": level,
                "inferred_mode": mode,
                "confidence_score": confidence,
                "rule_applied": rule,
                "explanation": explanation
            })

        # Step 3: Session-level synthesis
        avg_score = float(np.mean(composite_scores)) if composite_scores else 50.0
        dominant_mode = max(mode_counts, key=mode_counts.get) if mode_counts else "Attentive Listening / Lecture"
        
        # Calculate percentage distribution of interaction modes
        total_intervals = len(processed_intervals)
        mode_percentages = {
            m: round((c / max(1, total_intervals)) * 100.0, 1) for m, c in mode_counts.items()
        }

        return {
            "intervals": processed_intervals,
            "session_engagement_index": round(avg_score, 1),
            "dominant_mode": dominant_mode,
            "mode_distribution": mode_percentages,
            "total_intervals": total_intervals,
            "data_quality_confidence": round(float(np.mean([w["confidence_score"] for w in aligned_windows])), 2) if aligned_windows else 0.5
        }

    @staticmethod
    def _evaluate_window_rules(visible_participants: int,
                               motion_intensity: float,
                               audio_rms: float,
                               speech_ratio: float,
                               has_vision: bool,
                               has_audio: bool) -> Tuple[float, str, str, str, str]:
        """
        Auditable, deterministic decision tree for classroom engagement inference.
        Returns: (score [0-100], level, mode, rule_id, explanation)
        """
        # Rule Set 1: Both modalities available
        if has_vision and has_audio:
            # High movement + High speech = Collaborative group work or active debate
            if motion_intensity >= 0.30 and speech_ratio >= 0.35 and visible_participants >= 2:
                score = min(96.0, 75.0 + (speech_ratio * 15.0) + (motion_intensity * 10.0))
                return (
                    score, "High", "Collaborative Group Work", "RULE_COLLABORATIVE_ACTIVE",
                    "Co-occurring physical motion and vocal interaction indicates energetic group collaboration."
                )

            # High speech + Low/Medium motion = Active Discussion / Q&A
            if speech_ratio >= 0.40 and audio_rms >= 0.015:
                score = min(94.0, 70.0 + (speech_ratio * 25.0))
                return (
                    score, "High", "Active Discussion", "RULE_ACTIVE_DISCUSSION",
                    "Elevated speech activity with calm physical presence reflects focused teacher-student dialogue."
                )

            # Low/Moderate motion + Moderate speech = Attentive lecture delivery
            if speech_ratio >= 0.15 and motion_intensity <= 0.25 and visible_participants >= 1:
                score = 72.0 + (speech_ratio * 10.0)
                return (
                    score, "Moderate", "Attentive Listening / Lecture", "RULE_LECTURE_ATTENTIVE",
                    "Steady vocal instructional flow accompanied by settled classroom seating indicates lecture listening."
                )

            # High motion + Low speech = Classroom transition or restlessness
            if motion_intensity >= 0.38 and speech_ratio < 0.20:
                score = max(35.0, 55.0 - (motion_intensity * 25.0))
                return (
                    score, "Disrupted/Restless", "Transition / Restlessness", "RULE_TRANSITION_RESTLESS",
                    "Elevated physical movement without corresponding speech suggests room transition, fidgeting, or packing up."
                )

            # Low motion + Low speech = Silent individual work or instructional lull
            if speech_ratio < 0.15 and motion_intensity < 0.18:
                score = 48.0
                return (
                    score, "Low", "Passive / Lull", "RULE_PASSIVE_LULL",
                    "Quiet classroom environment with minimal movement. Characterizes silent reading, exams, or a pause."
                )

            # Balanced default
            score = 65.0
            return (
                score, "Moderate", "Attentive Listening / Lecture", "RULE_GENERAL_CLASSROOM_STEADY",
                "Observable audio-visual signals align with customary classroom dynamics."
            )

        # Rule Set 2: Vision-only modality
        elif has_vision:
            if motion_intensity >= 0.40:
                return (
                    58.0, "Moderate", "Transition / Restlessness", "RULE_VISION_HIGH_MOTION",
                    "Vision-only inference: scene movement indicates physical activity or transition."
                )
            elif visible_participants >= 1:
                return (
                    68.0, "Moderate", "Attentive Listening / Lecture", "RULE_VISION_SETTLED_PRESENCE",
                    "Vision-only inference: seated participants observed with low room agitation."
                )
            else:
                return (
                    30.0, "Low", "Passive / Lull", "RULE_VISION_NO_ATTENDEES",
                    "Vision-only inference: no visible attendees detected in the camera frame."
                )

        # Rule Set 3: Audio-only modality
        elif has_audio:
            if speech_ratio >= 0.45:
                return (
                    82.0, "High", "Active Discussion", "RULE_AUDIO_HIGH_SPEECH",
                    "Audio-only inference: sustained vocal-band activity indicates interactive dialogue."
                )
            elif speech_ratio >= 0.15:
                return (
                    70.0, "Moderate", "Attentive Listening / Lecture", "RULE_AUDIO_MODERATE_SPEECH",
                    "Audio-only inference: continuous vocal stream characteristic of lecture presentation."
                )
            else:
                return (
                    40.0, "Low", "Passive / Lull", "RULE_AUDIO_SILENCE_LULL",
                    "Audio-only inference: prolonged silence or low acoustic presence."
                )

        # Fallback when both modalities missing
        return (
            50.0, "Moderate", "Passive / Lull", "RULE_MISSING_DATA_FALLBACK",
            "Insufficient sensor data available to classify classroom interaction."
        )
