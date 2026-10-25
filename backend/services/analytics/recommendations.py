from typing import List, Dict, Any, Optional

class RecommendationEngine:
    """
    Deterministic pedagogical advice generator based on empirical classroom patterns.
    Produces actionable teaching suggestions paired with auditable quantitative evidence.
    """
    def __init__(self):
        pass

    def generate_recommendations(self,
                                 session_id: str,
                                 video_summary: Optional[Dict[str, Any]],
                                 audio_summary: Optional[Dict[str, Any]],
                                 intervals: List[Dict[str, Any]],
                                 attendance_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Evaluate rule-based heuristics across session signals and produce recommendations.
        """
        recommendations = []

        if not intervals:
            return [{
                "session_id": session_id,
                "category": "Data Quality",
                "priority": "low",
                "suggestion_text": "Record a longer classroom segment for deep analytical insights.",
                "evidence_text": "Fewer than 1 temporal interval recorded for this session.",
                "timestamp_reference": "Overall Session",
                "rule_id": "REC_INSUFFICIENT_DATA"
            }]

        total_intervals = len(intervals)
        
        # Helper: format seconds to MM:SS
        def fmt_time(seconds: float) -> str:
            m = int(seconds // 60)
            s = int(seconds % 60)
            return f"{m:02d}:{s:02d}"

        # -------------------------------------------------------------
        # Rule 1: Prolonged Silence / Low-Activity Lull Check
        # -------------------------------------------------------------
        lull_streak = 0
        max_lull_streak = 0
        lull_start_sec = 0.0
        lull_time_range = ""

        for it in intervals:
            if it["inferred_mode"] == "Passive / Lull":
                if lull_streak == 0:
                    lull_start_sec = it["start_seconds"]
                lull_streak += 1
                if lull_streak > max_lull_streak:
                    max_lull_streak = lull_streak
                    lull_time_range = f"{fmt_time(lull_start_sec)} - {fmt_time(it['end_seconds'])}"
            else:
                lull_streak = 0

        if max_lull_streak >= 3:
            recommendations.append({
                "session_id": session_id,
                "category": "Pedagogy",
                "priority": "high",
                "suggestion_text": "Introduce a quick formative poll, think-pair-share, or interactive check-in.",
                "evidence_text": f"Continuous passive lull detected for {max_lull_streak * 5} seconds ({lull_time_range}) with near-zero speech and minimal scene motion.",
                "timestamp_reference": lull_time_range,
                "rule_id": "REC_PROLONGED_LULL"
            })

        # -------------------------------------------------------------
        # Rule 2: Classroom Restlessness / Physical Transition Fatigue
        # -------------------------------------------------------------
        restless_intervals = [it for it in intervals if it["inferred_mode"] == "Transition / Restlessness"]
        if len(restless_intervals) >= 2:
            first_restless = restless_intervals[0]
            last_restless = restless_intervals[-1]
            time_ref = f"{fmt_time(first_restless['start_seconds'])} - {fmt_time(last_restless['end_seconds'])}"
            recommendations.append({
                "session_id": session_id,
                "category": "Break",
                "priority": "high",
                "suggestion_text": "Offer a 2-minute physical stretch break or shift instructional pace.",
                "evidence_text": f"Elevated physical room motion observed across {len(restless_intervals)} intervals ({time_ref}) alongside drop in vocal activity.",
                "timestamp_reference": time_ref,
                "rule_id": "REC_RESTLESSNESS_FATIGUE"
            })

        # -------------------------------------------------------------
        # Rule 3: High Continuous Monologue / Lecture Pace Warning
        # -------------------------------------------------------------
        lecture_intervals = [it for it in intervals if it["inferred_mode"] == "Attentive Listening / Lecture"]
        active_disc_intervals = [it for it in intervals if it["inferred_mode"] == "Active Discussion"]

        lecture_ratio = len(lecture_intervals) / max(1, total_intervals)
        disc_ratio = len(active_disc_intervals) / max(1, total_intervals)

        if lecture_ratio > 0.65 and disc_ratio < 0.10:
            recommendations.append({
                "session_id": session_id,
                "category": "Pacing",
                "priority": "medium",
                "suggestion_text": "Incorporate open-ended questioning to prompt student verbal participation.",
                "evidence_text": f"Instructional monologue occupied {round(lecture_ratio * 100, 1)}% of session time with interactive discussion at only {round(disc_ratio * 100, 1)}%.",
                "timestamp_reference": "Overall Session",
                "rule_id": "REC_MONOLOGUE_PACING"
            })

        # -------------------------------------------------------------
        # Rule 4: Active Collaborative Discussion Momentum
        # -------------------------------------------------------------
        if disc_ratio >= 0.25:
            recommendations.append({
                "session_id": session_id,
                "category": "Interaction",
                "priority": "info",
                "suggestion_text": "Synthesize and anchor key student contributions on the board or LMS summary.",
                "evidence_text": f"Vibrant collaborative dialogue observed across {len(active_disc_intervals)} intervals ({round(disc_ratio * 100, 1)}% of total time).",
                "timestamp_reference": "Interactive Segments",
                "rule_id": "REC_DISCUSSION_SYNTHESIS"
            })

        # -------------------------------------------------------------
        # Rule 5: Mid-Session Attendance Discontinuity
        # -------------------------------------------------------------
        if video_summary:
            peak_hc = video_summary.get("peak_headcount", 0)
            sustained_hc = video_summary.get("sustained_attendees_count", 0)
            if peak_hc > 0 and (peak_hc - sustained_hc) >= max(2, int(peak_hc * 0.25)):
                recommendations.append({
                    "session_id": session_id,
                    "category": "Classroom Dynamics",
                    "priority": "medium",
                    "suggestion_text": "Verify classroom access continuity; several participants departed before the minimum presence duration threshold.",
                    "evidence_text": f"Camera observed a peak headcount of {peak_hc}, but only {sustained_hc} attendees achieved sustained presence qualification.",
                    "timestamp_reference": "Throughout Session",
                    "rule_id": "REC_ATTENDANCE_DROP"
                })

        # Fallback positive reinforcement if everything looks balanced
        if not recommendations:
            recommendations.append({
                "session_id": session_id,
                "category": "Pedagogy",
                "priority": "info",
                "suggestion_text": "Maintain current instructional rhythm; classroom demonstrates well-balanced listening and interaction cycles.",
                "evidence_text": "Multimodal signals show balanced transitions between attentive lecture delivery and participant presence.",
                "timestamp_reference": "Overall Session",
                "rule_id": "REC_BALANCED_RHYTHM"
            })

        return recommendations
