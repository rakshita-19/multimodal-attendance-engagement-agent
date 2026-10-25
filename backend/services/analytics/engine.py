import numpy as np
from typing import List, Dict, Any, Optional
from backend.services.analytics.recommendations import RecommendationEngine

class SessionAnalyticsEngine:
    """
    Computes high-level pedagogical analytics, phase-based trend breakdowns,
    and student-facing ethical summaries from session multimodal data.
    """
    def __init__(self):
        self.recommender = RecommendationEngine()

    def generate_full_analytics(self,
                                session_id: str,
                                session_metadata: Dict[str, Any],
                                video_summary: Optional[Dict[str, Any]],
                                audio_summary: Optional[Dict[str, Any]],
                                intervals: List[Dict[str, Any]],
                                attendance_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate comprehensive analytics bundle for dashboard visualization and reporting.
        """
        # 1. Attendance KPIs
        att_kpis = self._compute_attendance_kpis(attendance_records, session_metadata.get("duration_seconds", 0.0))

        # 2. Phase-Based Temporal Trends
        trends = self._compute_phase_trends(intervals)

        # 3. Actionable Pedagogical Recommendations
        recommendations = self.recommender.generate_recommendations(
            session_id=session_id,
            video_summary=video_summary,
            audio_summary=audio_summary,
            intervals=intervals,
            attendance_records=attendance_records
        )

        # 4. Student-Facing Ethical Summary
        student_summary = self._generate_student_facing_summary(
            session_metadata.get("title", "Class Session"),
            att_kpis,
            trends,
            len(intervals)
        )

        return {
            "session_id": session_id,
            "attendance_kpis": att_kpis,
            "phase_trends": trends,
            "recommendations": recommendations,
            "student_summary": student_summary
        }

    @staticmethod
    def _compute_attendance_kpis(records: List[Dict[str, Any]], session_duration: float) -> Dict[str, Any]:
        """Calculate cohort attendance metrics."""
        total = len(records)
        if total == 0:
            return {
                "total_tracked": 0,
                "present_count": 0,
                "partial_count": 0,
                "insufficient_count": 0,
                "attendance_rate_percentage": 0.0,
                "average_presence_duration_seconds": 0.0,
                "average_presence_percentage": 0.0
            }

        present = sum(1 for r in records if r["sustained_presence_status"] == "present")
        partial = sum(1 for r in records if r["sustained_presence_status"] == "partial")
        insufficient = sum(1 for r in records if r["sustained_presence_status"] == "insufficient_presence")

        durations = [r["presence_duration_seconds"] for r in records]
        percentages = [r["presence_percentage"] for r in records]

        return {
            "total_tracked": total,
            "present_count": present,
            "partial_count": partial,
            "insufficient_count": insufficient,
            "attendance_rate_percentage": round((present / total) * 100.0, 1),
            "average_presence_duration_seconds": round(float(np.mean(durations)), 1),
            "average_presence_percentage": round(float(np.mean(percentages)), 1)
        }

    @staticmethod
    def _compute_phase_trends(intervals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Partition session into sequential thirds to analyze instructional trajectory."""
        if not intervals:
            return {"phases": [], "overall_trend": "No data"}

        n = len(intervals)
        chunk_size = max(1, n // 3)

        phases = []
        phase_names = ["Phase 1 (Opening / Setup)", "Phase 2 (Core Instruction / Activity)", "Phase 3 (Review / Closing)"]

        for p_idx in range(3):
            start_i = p_idx * chunk_size
            end_i = (p_idx + 1) * chunk_size if p_idx < 2 else n
            phase_intervals = intervals[start_i:end_i]

            if phase_intervals:
                scores = [it["composite_engagement_score"] for it in phase_intervals]
                avg_score = round(float(np.mean(scores)), 1)
                
                # Mode breakdown in phase
                modes = [it["inferred_mode"] for it in phase_intervals]
                dominant_mode = max(set(modes), key=modes.count)
                
                start_sec = phase_intervals[0]["start_seconds"]
                end_sec = phase_intervals[-1]["end_seconds"]
            else:
                avg_score = 0.0
                dominant_mode = "N/A"
                start_sec = 0.0
                end_sec = 0.0

            phases.append({
                "phase_name": phase_names[p_idx],
                "start_seconds": start_sec,
                "end_seconds": end_sec,
                "interval_count": len(phase_intervals),
                "avg_engagement_score": avg_score,
                "dominant_mode": dominant_mode
            })

        # Determine trajectory direction
        if len(phases) >= 3 and phases[0]["avg_engagement_score"] > 0:
            p1_score = phases[0]["avg_engagement_score"]
            p2_score = phases[1]["avg_engagement_score"]
            p3_score = phases[2]["avg_engagement_score"]

            if p2_score >= p1_score and p2_score >= p3_score:
                overall_trend = "Peak engagement achieved during core instruction with steady closing."
            elif p3_score >= p2_score:
                overall_trend = "Engagement exhibited an upward momentum toward session conclusion."
            elif p1_score > p2_score and p2_score > p3_score:
                overall_trend = "Gradual decline in classroom activity observed; mid-session interactive breaks recommended."
            else:
                overall_trend = "Steady and consistent classroom participation throughout all phases."
        else:
            overall_trend = "Stable session trajectory."

        return {
            "phases": phases,
            "overall_trend": overall_trend
        }

    @staticmethod
    def _generate_student_facing_summary(title: str,
                                         att_kpis: Dict[str, Any],
                                         trends: Dict[str, Any],
                                         interval_count: int) -> Dict[str, str]:
        """
        Produce a transparent, non-evaluative summary suitable for student review.
        Maintains strict privacy and pedagogical ethics (no individual attention labels).
        """
        attendance_rate = att_kpis.get("attendance_rate_percentage", 0.0)
        overall_trend = trends.get("overall_trend", "Standard session progression.")

        return {
            "title": f"Classroom Session Summary: {title}",
            "cohort_attendance_note": f"{attendance_rate}% of tracked participants maintained verified sustained presence.",
            "dynamic_summary": overall_trend,
            "ethical_notice": (
                "Notice of Privacy & Pedagogical Intent: This system tracks cohort-level room acoustics "
                "and aggregate visual presence to assist teaching pace. It does NOT analyze speech content, "
                "perform facial recognition, or evaluate individual student mental comprehension."
            )
        }
