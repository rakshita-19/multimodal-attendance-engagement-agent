-- Multimodal Attendance & Engagement Agent SQLite Schema
-- Privacy-Preserving Classroom Intelligence System

PRAGMA foreign_keys = ON;

-- 1. Sessions Table
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    duration_seconds REAL DEFAULT 0.0,
    status TEXT DEFAULT 'created', -- 'created', 'processing_video', 'processing_audio', 'analyzing', 'completed', 'failed'
    notes TEXT,
    video_file_name TEXT,
    audio_file_name TEXT,
    raw_files_retained INTEGER DEFAULT 0 -- 0: cleaned up after processing (privacy default), 1: retained
);

-- 2. Attendance Records Table
-- Stores sustained-presence attendance mapped to temporary tracker IDs
-- Includes manual mapping capabilities for teacher review without automated face biometric surveillance
CREATE TABLE IF NOT EXISTS attendance_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    track_id INTEGER NOT NULL,
    student_name TEXT DEFAULT NULL, -- Teacher-verified / manually mapped name
    first_seen_seconds REAL NOT NULL,
    last_seen_seconds REAL NOT NULL,
    presence_duration_seconds REAL NOT NULL,
    presence_percentage REAL NOT NULL,
    sustained_presence_status TEXT NOT NULL, -- 'present', 'partial', 'insufficient_presence'
    avg_movement_score REAL DEFAULT 0.0,
    confidence_score REAL DEFAULT 1.0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
    UNIQUE(session_id, track_id)
);

-- 3. Video Processing Summaries Table
CREATE TABLE IF NOT EXISTS video_summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL UNIQUE,
    total_frames INTEGER NOT NULL,
    fps REAL NOT NULL,
    duration_seconds REAL NOT NULL,
    unique_tracks_detected INTEGER NOT NULL,
    sustained_attendees_count INTEGER NOT NULL,
    avg_headcount_per_frame REAL NOT NULL,
    peak_headcount INTEGER NOT NULL,
    avg_motion_energy REAL NOT NULL,
    processing_time_seconds REAL NOT NULL,
    quality_note TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

-- 4. Audio Activity Summaries Table
-- Privacy preserving: No transcriptions, no speaker biometric identification
CREATE TABLE IF NOT EXISTS audio_summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL UNIQUE,
    duration_seconds REAL NOT NULL,
    sample_rate INTEGER NOT NULL,
    channels INTEGER NOT NULL,
    avg_rms_energy REAL NOT NULL,
    peak_rms_energy REAL NOT NULL,
    silence_percentage REAL NOT NULL,
    speech_like_percentage REAL NOT NULL,
    active_discussion_percentage REAL NOT NULL,
    noise_floor REAL NOT NULL,
    processing_time_seconds REAL NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

-- 5. Engagement Intervals Table
-- Multimodal aligned time-series windows (e.g. 5-second windows)
CREATE TABLE IF NOT EXISTS engagement_intervals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    interval_index INTEGER NOT NULL,
    start_seconds REAL NOT NULL,
    end_seconds REAL NOT NULL,
    visible_participants INTEGER NOT NULL,
    motion_intensity REAL NOT NULL, -- 0.0 - 1.0
    audio_rms REAL NOT NULL,
    speech_activity_ratio REAL NOT NULL, -- 0.0 - 1.0
    composite_engagement_score REAL NOT NULL, -- 0 - 100
    engagement_level TEXT NOT NULL, -- 'High', 'Moderate', 'Low', 'Disrupted/Restless'
    inferred_mode TEXT NOT NULL, -- 'Active Discussion', 'Attentive Listening / Lecture', 'Collaborative Group Work', 'Passive / Lull', 'Transition / Movement'
    confidence_score REAL NOT NULL, -- 0.0 - 1.0
    rule_applied TEXT,
    explanation TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
    UNIQUE(session_id, interval_index)
);

-- 6. Recommendations Table
-- Deterministic, rule-based explainable pedagogical feedback
CREATE TABLE IF NOT EXISTS recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    category TEXT NOT NULL, -- 'Pacing', 'Interaction', 'Break', 'Pedagogy', 'Classroom Dynamics'
    priority TEXT NOT NULL, -- 'high', 'medium', 'low', 'info'
    suggestion_text TEXT NOT NULL,
    evidence_text TEXT NOT NULL,
    timestamp_reference TEXT,
    rule_id TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

-- Indexes for fast query performance
CREATE INDEX IF NOT EXISTS idx_attendance_session ON attendance_records(session_id);
CREATE INDEX IF NOT EXISTS idx_intervals_session ON engagement_intervals(session_id);
CREATE INDEX IF NOT EXISTS idx_recs_session ON recommendations(session_id);
