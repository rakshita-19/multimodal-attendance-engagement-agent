import time
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional
from backend.services.vision.detector import PersonDetector, MotionAnalyzer
from backend.services.vision.tracker import ParticipantTracker
from backend.config import Config

class VisionAttendanceService:
    """
    Coordinates local video frame ingestion, person detection, multi-object tracking,
    motion energy quantification, and sustained-presence attendance calculation.
    """
    def __init__(self, 
                 min_presence_seconds: float = Config.MIN_PRESENCE_SECONDS,
                 frame_sample_rate: int = Config.FRAME_SAMPLE_RATE,
                 window_size_seconds: float = Config.WINDOW_SIZE_SECONDS):
        self.min_presence_seconds = min_presence_seconds
        self.frame_sample_rate = max(1, frame_sample_rate)
        self.window_size_seconds = window_size_seconds
        self.detector = PersonDetector()
        self.motion_analyzer = MotionAnalyzer()
        self.tracker = ParticipantTracker(max_disappeared_frames=Config.TRACK_MAX_DISAPPEARED_FRAMES)

    def process_video(self, video_path: str, session_id: str) -> Dict[str, Any]:
        """
        Process a recorded classroom video file end-to-end.
        Extracts participant attendance and time-windowed visual engagement statistics.
        """
        path = Path(video_path)
        if not path.exists():
            raise FileNotFoundError(f"Video file not found at: {video_path}")

        cap = cv2.VideoCapture(str(path))
        if not cap.isOpened():
            raise ValueError(f"Unable to open video source at: {video_path}")

        # Validate that OpenCV can decode frames from this container & codec
        ret, first_frame = cap.read()
        if not ret or first_frame is None:
            cap.release()
            raise ValueError(
                f"Video file '{path.name}' could not be decoded. "
                f"0 frames were readable. The codec may be unsupported or the file is corrupted. "
                f"Please ensure you upload a standard H.264 or MPEG-4 MP4/AVI video."
            )
        # Rewind to first frame
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0 or np.isnan(fps):
            fps = 25.0  # Safe standard fallback

        duration_seconds = total_frames / fps if total_frames > 0 else 0.0
        frame_interval_seconds = 1.0 / fps

        start_perf_time = time.time()
        frame_idx = 0

        # Data collection buffers
        per_frame_headcounts: List[int] = []
        per_frame_motion: List[float] = []
        per_frame_timestamps: List[float] = []

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                current_timestamp = frame_idx * frame_interval_seconds

                # Process every Nth frame to optimize CPU throughput while preserving tracking continuity
                if frame_idx % self.frame_sample_rate == 0:
                    effective_interval = frame_interval_seconds * self.frame_sample_rate
                    
                    # 1. Motion energy
                    motion_score = self.motion_analyzer.compute_motion(frame)
                    per_frame_motion.append(motion_score)

                    # 2. Person detection
                    detections = self.detector.detect(frame)
                    
                    # 3. Update tracker
                    active_tracks = self.tracker.update(detections, current_timestamp, effective_interval)
                    headcount = len(active_tracks)
                    
                    per_frame_headcounts.append(headcount)
                    per_frame_timestamps.append(current_timestamp)

                frame_idx += 1
        finally:
            cap.release()

        proc_time = time.time() - start_perf_time

        # If video was empty or unreadable
        if frame_idx == 0:
            duration_seconds = 0.0
            actual_fps = fps
        else:
            duration_seconds = frame_idx * frame_interval_seconds
            actual_fps = fps

        # Compile Attendance Records
        all_tracks = self.tracker.get_all_records()
        attendance_records = []
        sustained_count = 0

        for track in all_tracks:
            # Presence duration is accumulated visible time
            vis_duration = round(track.total_visible_seconds, 2)
            pres_pct = round((vis_duration / max(1.0, duration_seconds)) * 100.0, 1) if duration_seconds > 0 else 100.0
            pres_pct = min(100.0, pres_pct)

            # Determine attendance classification
            if vis_duration >= self.min_presence_seconds and pres_pct >= 50.0:
                status = "present"
                sustained_count += 1
            elif vis_duration >= (self.min_presence_seconds * 0.40) or (pres_pct >= 25.0):
                status = "partial"
                sustained_count += 1
            else:
                status = "insufficient_presence"

            avg_movement = round(track.total_movement / max(1, track.frames_visible), 2)
            confidence = 0.95 if track.frames_visible > 15 else 0.70

            attendance_records.append({
                "session_id": session_id,
                "track_id": track.track_id,
                "student_name": None,  # Open for teacher verification
                "first_seen_seconds": round(track.first_seen_seconds, 2),
                "last_seen_seconds": round(track.last_seen_seconds, 2),
                "presence_duration_seconds": vis_duration,
                "presence_percentage": pres_pct,
                "sustained_presence_status": status,
                "avg_movement_score": avg_movement,
                "confidence_score": confidence,
                "notes": f"Observed in {track.frames_visible} frames (Track #{track.track_id})"
            })

        # Compile Synchronized Vision Windows (e.g. 5-second intervals)
        vision_intervals = self._compute_windowed_vision(
            per_frame_timestamps, per_frame_headcounts, per_frame_motion, duration_seconds
        )

        avg_hc = float(np.mean(per_frame_headcounts)) if per_frame_headcounts else 0.0
        peak_hc = int(np.max(per_frame_headcounts)) if per_frame_headcounts else 0
        avg_motion = float(np.mean(per_frame_motion)) if per_frame_motion else 0.0

        video_summary = {
            "session_id": session_id,
            "total_frames": frame_idx,
            "fps": round(actual_fps, 2),
            "duration_seconds": round(duration_seconds, 2),
            "unique_tracks_detected": len(all_tracks),
            "sustained_attendees_count": sustained_count,
            "avg_headcount_per_frame": round(avg_hc, 2),
            "peak_headcount": peak_hc,
            "avg_motion_energy": round(avg_motion, 4),
            "processing_time_seconds": round(proc_time, 2),
            "quality_note": f"Processed {frame_idx} frames at {self.frame_sample_rate}x sampling."
        }

        return {
            "attendance_records": attendance_records,
            "video_summary": video_summary,
            "vision_intervals": vision_intervals
        }

    def _compute_windowed_vision(self, timestamps: List[float], headcounts: List[int],
                                 motions: List[float], total_duration: float) -> List[Dict[str, Any]]:
        """Group frame statistics into uniform time windows for multimodal alignment."""
        if not timestamps or total_duration <= 0:
            return []

        intervals = []
        num_windows = int(np.ceil(total_duration / self.window_size_seconds))
        ts_arr = np.array(timestamps)
        hc_arr = np.array(headcounts)
        mo_arr = np.array(motions)

        for w_idx in range(num_windows):
            w_start = w_idx * self.window_size_seconds
            w_end = min(total_duration, (w_idx + 1) * self.window_size_seconds)

            mask = (ts_arr >= w_start) & (ts_arr < w_end)
            if np.any(mask):
                w_hc = int(round(np.mean(hc_arr[mask])))
                w_motion = float(np.mean(mo_arr[mask]))
            else:
                w_hc = 0
                w_motion = 0.0

            intervals.append({
                "interval_index": w_idx,
                "start_seconds": round(w_start, 2),
                "end_seconds": round(w_end, 2),
                "visible_participants": w_hc,
                "motion_intensity": round(w_motion, 4)
            })

        return intervals
