import cv2
import numpy as np
import soundfile as sf
from pathlib import Path
from typing import Tuple

def generate_sample_classroom_media(video_dest: Path, audio_dest: Path, duration_sec: float = 15.0) -> Tuple[Path, Path]:
    """
    Generate realistic synthetic classroom video and audio for demonstration and evaluation.
    - Video: classroom lecture scene with 4 seated students at individual desks, natural movement, whiteboard.
    - Audio: speech bursts (lecture presentation) and interactive Q&A segments with ambient background.
    """
    video_dest.parent.mkdir(parents=True, exist_ok=True)
    audio_dest.parent.mkdir(parents=True, exist_ok=True)

    # 1. Generate Video
    fps = 20
    total_frames = int(duration_sec * fps)
    width, height = 480, 360
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(video_dest), fourcc, fps, (width, height))

    # Participant setup (4 simulated students at individual desks)
    students = [
        {"x": 90, "y": 170, "name": "Student A", "color": (190, 80, 50)},
        {"x": 190, "y": 170, "name": "Student B", "color": (50, 160, 80)},
        {"x": 290, "y": 170, "name": "Student C", "color": (40, 80, 200)},
        {"x": 390, "y": 170, "name": "Student D", "color": (160, 60, 180)}
    ]

    for frame_i in range(total_frames):
        t_sec = frame_i / fps
        frame = np.full((height, width, 3), 235, dtype=np.uint8)  # Classroom wall

        # Whiteboard on wall
        cv2.rectangle(frame, (100, 25), (380, 85), (255, 255, 255), -1)
        cv2.rectangle(frame, (100, 25), (380, 85), (120, 120, 120), 2)
        cv2.putText(frame, "CS401: AI Multimodal Lecture", (115, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (40, 40, 40), 1)
        cv2.putText(frame, "Active Presence & Dynamics", (125, 72), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (80, 80, 80), 1)

        # Draw students at individual desks with subtle natural motion
        for idx, s in enumerate(students):
            # Student D leaves temporarily between seconds 7.0 and 10.5
            if idx == 3 and (7.0 <= t_sec <= 10.5):
                # Empty desk
                cv2.rectangle(frame, (s["x"] - 35, 240), (s["x"] + 35, 275), (140, 100, 60), -1)
                cv2.rectangle(frame, (s["x"] - 35, 240), (s["x"] + 35, 275), (90, 60, 30), 2)
                continue

            jitter_x = int(2 * np.sin(frame_i * 0.15 + idx))
            jitter_y = int(2 * np.cos(frame_i * 0.12 + idx))
            
            hx = s["x"] + jitter_x
            hy = s["y"] + jitter_y

            # Individual student desk
            cv2.rectangle(frame, (s["x"] - 35, 240), (s["x"] + 35, 275), (140, 100, 60), -1)
            cv2.rectangle(frame, (s["x"] - 35, 240), (s["x"] + 35, 275), (90, 60, 30), 2)

            # Student Head
            cv2.circle(frame, (hx, hy), 22, (200, 180, 160), -1)
            cv2.circle(frame, (hx, hy), 22, (80, 80, 80), 1)

            # Hair/Cap
            cv2.ellipse(frame, (hx, hy - 8), (22, 14), 0, 180, 360, s["color"], -1)

            # Torso / Upper body
            cv2.rectangle(frame, (hx - 25, hy + 22), (hx + 25, 240), s["color"], -1)

        out.write(frame)

    out.release()

    # 2. Generate Audio (16kHz WAV)
    sr = 16000
    t = np.linspace(0, duration_sec, int(sr * duration_sec), endpoint=False)
    audio = np.random.normal(0, 0.003, len(t))  # Ambient room noise

    # Speech segment 1 (0.5 to 6.0 seconds: teacher lecture)
    s1_mask = (t >= 0.5) & (t <= 6.0)
    audio[s1_mask] += 0.28 * np.sin(2 * np.pi * 500 * t[s1_mask]) + 0.15 * np.sin(2 * np.pi * 1200 * t[s1_mask])

    # Speech segment 2 (7.5 to 14.0 seconds: interactive discussion with vocal modulation)
    s2_mask = (t >= 7.5) & (t <= 14.0)
    audio[s2_mask] += 0.35 * np.sin(2 * np.pi * 750 * t[s2_mask]) + 0.22 * np.sin(2 * np.pi * 1650 * t[s2_mask])

    sf.write(str(audio_dest), audio, sr)
    return video_dest, audio_dest
