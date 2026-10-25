# Multimodal Attendance & Engagement Agent: System Architecture

## 1. System Overview
The **Multimodal Attendance & Engagement Agent** is a privacy-first, locally-hosted classroom intelligence platform designed to:
1. Objectively record participant presence over time without biometric facial surveillance.
2. Quantify acoustic activity patterns without speech transcription or eavesdropping.
3. Align synchronized video and audio streams using deterministic multimodal fusion.
4. Generate explainable, rule-based pedagogical insights for teachers.
5. Provide actionable dashboards, time-series visualizations, and CSV exports.

## 2. Privacy & Ethical Boundaries (Core Design Tenet)
- **No Face Recognition as Ground Truth Identity:** Vision tracks use transient IDs (`track_id`). Teacher review / manual mapping is provided to correlate tracks with student names.
- **No Mental Attention or Psychological Inference Claims:** Observable metrics (movement, presence, acoustic energy) indicate *behavioral classroom activity patterns*, NOT internal mental cognitive attention or learning comprehension.
- **Privacy-Preserving Audio Analysis:** Operates purely on short-time RMS energy, bandpass spectral energy (300Hz-3400Hz), and zero-crossing rates. No speech-to-text, no speaker identification, no raw conversational storage.
- **Temporary Media Storage & Retention:** Raw video and audio files are uploaded to ephemeral local paths, processed, and cleaned up automatically according to retention policy. Only extracted numerical aggregates and indicators are persisted in SQLite.

## 3. High-Level Pipeline Architecture

```
   +----------------------+        +-----------------------+
   |   Classroom Video    |        |    Classroom Audio    |
   | (MP4 / AVI / Webcam) |        | (WAV / MP3 / Mic-In)  |
   +----------+-----------+        +-----------+-----------+
              |                                |
              v                                v
   +----------------------+        +-----------------------+
   |   Vision Pipeline    |        |    Audio Pipeline     |
   | - Frame Sampling     |        | - 16kHz Normalization |
   | - Person Detection   |        | - Short-time RMS      |
   |   (HOG + Cascade)    |        | - Speech-band Energy  |
   | - Centroid + IoU     |        | - Zero-Crossing Rate  |
   |   Tracking           |        | - Silence/Voice Ratio |
   | - Sustained Presence |        |                       |
   +----------+-----------+        +-----------+-----------+
              |                                |
              |      Synchronized Intervals    |
              +--------------+-----------------+
                             |
                             v
               +---------------------------+
               |  Multimodal Agent Engine  |
               | - Timestamp Alignment     |
               | - Window Aggregation (5s) |
               | - Deterministic Fusion    |
               | - Mode Classification     |
               | - Data Quality Confidence |
               +-------------+-------------+
                             |
                             v
               +---------------------------+
               |  Pedagogical Recommender  |
               | - Rule-Based Triggers     |
               | - Pacing & Break Alerts   |
               | - Explainable Evidences   |
               +-------------+-------------+
                             |
                             v
               +---------------------------+
               |  SQLite Local Persistence |
               |  Sessions, Attendance,    |
               |  Summaries, Intervals     |
               +-------------+-------------+
                             |
                             v
               +---------------------------+
               |   Flask REST API Layer    |
               | /api/sessions, /upload... |
               +-------------+-------------+
                             |
                             v
               +---------------------------+
               |     Teacher Dashboard     |
               | Modern UI, Chart.js,      |
               | Attendance Table, CSV     |
               +---------------------------+
```

## 4. Module Interfaces
1. **Vision Module (`backend/services/vision/`)**:
   - Inputs: Video filepath or webcam stream, configuration parameters (`min_presence_seconds`, `sample_rate`).
   - Outputs: `attendance_records` (track ID, entry, exit, duration, status), `video_summary` (frames, FPS, avg headcount, motion intensity), `frame_intervals` (visible headcount and motion per time window).
2. **Audio Module (`backend/services/audio/`)**:
   - Inputs: Audio filepath, configuration parameters (`window_size`, `energy_threshold`).
   - Outputs: `audio_summary` (RMS, silence %, speech-like %, noise floor), `audio_intervals` (RMS energy and speech activity ratio per time window).
3. **Multimodal Agent (`backend/services/agent/`)**:
   - Inputs: Aligned time-series windows from Vision and Audio.
   - Outputs: Aligned composite engagement records with inferred modes (`Active Discussion`, `Attentive Listening`, `Collaborative Group Work`, `Passive / Lull`, `Transition / Restless`).
4. **Analytics & Recommendations (`backend/services/analytics/`)**:
   - Inputs: Complete session aggregates and interval sequences.
   - Outputs: Actionable pedagogical advice with transparent evidence chains and session analytics KPIs.
