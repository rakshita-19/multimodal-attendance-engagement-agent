import numpy as np
from typing import List, Dict, Any, Optional

class SignalAligner:
    """
    Synchronizes vision-derived intervals and audio-derived intervals
    across uniform, configurable time windows.
    Handles single-modality sessions gracefully without crashing.
    """
    def __init__(self, window_size_seconds: float = 5.0):
        self.window_size_seconds = window_size_seconds

    def align(self, vision_intervals: Optional[List[Dict[str, Any]]],
              audio_intervals: Optional[List[Dict[str, Any]]],
              session_duration_seconds: float) -> List[Dict[str, Any]]:
        """
        Merge vision intervals and audio intervals by timestamp index.
        Returns a synchronized sequence of multimodal frames.
        """
        v_map = {item["interval_index"]: item for item in (vision_intervals or [])}
        a_map = {item["interval_index"]: item for item in (audio_intervals or [])}

        all_indices = sorted(set(list(v_map.keys()) + list(a_map.keys())))
        
        # If neither provided or empty
        if not all_indices:
            num_windows = max(1, int(np.ceil(session_duration_seconds / self.window_size_seconds)))
            all_indices = list(range(num_windows))

        aligned_windows = []

        for idx in all_indices:
            v_data = v_map.get(idx)
            a_data = a_map.get(idx)

            start_s = idx * self.window_size_seconds
            end_s = min(session_duration_seconds, (idx + 1) * self.window_size_seconds)
            if end_s <= start_s:
                end_s = start_s + self.window_size_seconds

            # Extract Vision metrics
            if v_data is not None:
                visible_participants = v_data.get("visible_participants", 0)
                motion_intensity = v_data.get("motion_intensity", 0.0)
                has_vision = True
            else:
                visible_participants = 0
                motion_intensity = 0.0
                has_vision = False

            # Extract Audio metrics
            if a_data is not None:
                audio_rms = a_data.get("audio_rms", 0.0)
                speech_activity_ratio = a_data.get("speech_activity_ratio", 0.0)
                has_audio = True
            else:
                audio_rms = 0.0
                speech_activity_ratio = 0.0
                has_audio = False

            # Modality confidence score
            if has_vision and has_audio:
                confidence = 0.95
            elif has_vision:
                confidence = 0.65  # Single modality (vision only)
            elif has_audio:
                confidence = 0.60  # Single modality (audio only)
            else:
                confidence = 0.20  # Missing data

            aligned_windows.append({
                "interval_index": idx,
                "start_seconds": round(start_s, 2),
                "end_seconds": round(end_s, 2),
                "visible_participants": visible_participants,
                "motion_intensity": round(motion_intensity, 4),
                "audio_rms": round(audio_rms, 4),
                "speech_activity_ratio": round(speech_activity_ratio, 2),
                "confidence_score": round(confidence, 2),
                "has_vision": has_vision,
                "has_audio": has_audio
            })

        return aligned_windows
