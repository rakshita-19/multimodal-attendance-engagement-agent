import cv2
import numpy as np
import pytest
import tempfile
from pathlib import Path
from backend.services.vision.detector import PersonDetector, MotionAnalyzer
from backend.services.vision.tracker import ParticipantTracker
from backend.services.vision.attendance_service import VisionAttendanceService

def create_synthetic_classroom_video(filepath: Path, duration_seconds: float = 3.0, fps: int = 20) -> Path:
    """Generate a clean synthetic video containing simulated participant shapes for deterministic testing."""
    width, height = 320, 240
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(filepath), fourcc, fps, (width, height))

    total_frames = int(duration_seconds * fps)
    for i in range(total_frames):
        frame = np.full((height, width, 3), 220, dtype=np.uint8)  # Light classroom wall background
        
        # Draw desk line
        cv2.line(frame, (0, 180), (width, 180), (100, 100, 100), 2)

        # Draw Person 1 (present throughout, subtle natural movement)
        p1_x = int(80 + 5 * np.sin(i * 0.2))
        p1_y = 110
        cv2.circle(frame, (p1_x, p1_y), 20, (60, 60, 180), -1)  # Head
        cv2.rectangle(frame, (p1_x - 22, p1_y + 20), (p1_x + 22, 175), (40, 120, 60), -1) # Body

        # Draw Person 2 (enters halfway at frame 30)
        if i >= 30:
            p2_x = 220
            p2_y = 115
            cv2.circle(frame, (p2_x, p2_y), 18, (180, 80, 60), -1) # Head
            cv2.rectangle(frame, (p2_x - 20, p2_y + 18), (p2_x + 20, 175), (140, 90, 40), -1)

        out.write(frame)

    out.release()
    return filepath

def test_tracker_iou_and_centroid():
    """Verify tracker IoU computation and association."""
    tracker = ParticipantTracker(max_disappeared_frames=5, iou_threshold=0.20)
    
    # Frame 1: Detection at (100, 100, 40, 80)
    tracks_f1 = tracker.update([(100, 100, 40, 80)], timestamp=0.0)
    assert len(tracks_f1) == 1
    t1_id = tracks_f1[0].track_id

    # Frame 2: Slight movement to (105, 102, 40, 80)
    tracks_f2 = tracker.update([(105, 102, 40, 80)], timestamp=0.1)
    assert len(tracks_f2) == 1
    assert tracks_f2[0].track_id == t1_id
    assert tracks_f2[0].frames_visible == 2

    # Frame 3: Missed detection (occlusion)
    tracks_f3 = tracker.update([], timestamp=0.2)
    assert len(tracks_f3) == 1  # Track still preserved during temporary occlusion
    assert tracks_f3[0].disappeared_frames == 1

    # Frame 4: Reappearance at (108, 104, 40, 80)
    tracks_f4 = tracker.update([(108, 104, 40, 80)], timestamp=0.3)
    assert len(tracks_f4) == 1
    assert tracks_f4[0].track_id == t1_id
    assert tracks_f4[0].disappeared_frames == 0

def test_motion_analyzer():
    """Verify motion analyzer detects difference between identical and changed frames."""
    analyzer = MotionAnalyzer()
    frame1 = np.zeros((100, 100, 3), dtype=np.uint8)
    frame2 = np.zeros((100, 100, 3), dtype=np.uint8)
    
    # First frame initializes
    m1 = analyzer.compute_motion(frame1)
    assert m1 == 0.0

    # Identical frame gives zero motion
    m2 = analyzer.compute_motion(frame2)
    assert m2 == 0.0

    # Altered frame gives non-zero motion
    frame3 = np.full((100, 100, 3), 255, dtype=np.uint8)
    m3 = analyzer.compute_motion(frame3)
    assert m3 > 0.0

def test_vision_attendance_service_on_synthetic_video():
    """Test full vision pipeline on synthetic video."""
    with tempfile.TemporaryDirectory() as tmpdir:
        video_file = Path(tmpdir) / "test_classroom.mp4"
        create_synthetic_classroom_video(video_file, duration_seconds=3.0, fps=20)
        assert video_file.exists()

        service = VisionAttendanceService(min_presence_seconds=1.0, frame_sample_rate=1, window_size_seconds=1.0)
        result = service.process_video(str(video_file), session_id="test-vision-session")

        assert "attendance_records" in result
        assert "video_summary" in result
        assert "vision_intervals" in result

        summary = result["video_summary"]
        assert summary["total_frames"] == 60
        assert summary["duration_seconds"] >= 2.9
        assert summary["fps"] == 20.0
        assert len(result["vision_intervals"]) >= 3
