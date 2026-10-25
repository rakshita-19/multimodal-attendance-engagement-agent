# Multimodal Attendance & Engagement Agent

> **AI-Powered, Privacy-Preserving Classroom Intelligence System**  
> Final-Year B.Tech Computer Science Capstone Project & Board Infinity Evaluation

[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Backend-Flask%203.1-black.svg)](https://flask.palletsprojects.com/)
[![OpenCV](https://img.shields.io/badge/Vision-OpenCV%20Headless-green.svg)](https://opencv.org/)
[![Acoustics](https://img.shields.io/badge/Audio-SciPy%20%26%20SoundFile-orange.svg)](https://scipy.org/)
[![Database](https://img.shields.io/badge/Database-SQLite%203-lightgrey.svg)](https://sqlite.org/)
[![Tests](https://img.shields.io/badge/Tests-21%2F21%20Passing-brightgreen.svg)](https://pytest.org/)

---

### 🔗 Project & Demo Links

* **📺 Video Demonstration Link:** `[Add your Loom / YouTube / Google Drive Video Link Here]`
* **🌐 Live Deployed Application:** `http://127.0.0.1:5000` *(or your deployed public URL)*
* **📂 GitHub Repository:** `[Add your GitHub Repository URL Here]`
* **📑 Board Infinity Milestone Report:** [`docs/BOARD_INFINITY_SUBMISSION.md`](docs/BOARD_INFINITY_SUBMISSION.md)
* **🎯 Step-by-Step Viva & Demo Script:** [`docs/DEMO_GUIDE.md`](docs/DEMO_GUIDE.md)

---

## 1. Project Overview

The **Multimodal Attendance & Engagement Agent** is a privacy-first, locally deployable classroom intelligence platform designed to assist instructors by:
1. **Automated Sustained-Presence Attendance:** Tracking visual participant presence across frames using IoU (Intersection-over-Union) and Centroid distance tracking to qualify students as `present`, `partial`, or `insufficient_presence` without facial biometric recognition.
2. **Privacy-Preserving Acoustic Dynamics:** Measuring Root Mean Square (RMS) energy, Zero Crossing Rate (ZCR), and vocal-band energy (300Hz–3400Hz) to detect active discussion and lecture delivery **without speech transcription, speaker profiling, or conversational eavesdropping**.
3. **Deterministic Multimodal Fusion:** Aligning video-derived presence and scene movement with acoustic indicators across uniform 5-second synchronized time windows.
4. **Explainable Pedagogical Feedback:** Generating transparent, rule-based teaching recommendations (e.g., pace adjustments, formative quizzes, physical stretch breaks) supported by explicit timestamped evidence.
5. **Interactive Teacher Dashboard:** Modern responsive web dashboard with real-time KPI cards, Chart.js time-series graphs, an attendance table with manual student mapping, and one-click CSV report exports.
6. **Zero Cloud Dependency:** 100% local CPU processing with zero external paid API subscriptions or privacy data leakage.

---

## 2. Privacy & Ethical Guardrails (Core Tenets)

* **No Facial Biometric Surveillance:** The computer vision tracker assigns transient identifier tokens (`Track #1`, `Track #2`). The system **does not** automatically associate facial images with identity; an instructor manual review modal allows the teacher to ethically map tracks to roll call names.
* **No Mental State or Psychological Inferences:** Observable physical movements and acoustic signals measure *aggregate classroom dynamics* (e.g., active dialogue, lecture listening, room restlessness), **not** an individual student's internal cognitive attention, intelligence, or learning.
* **No Audio Transcription:** Raw speech content is never transcribed to text or parsed. Signal processing operates strictly on mathematical acoustic features (energy and frequency bands).
* **Automatic Media Retention Cleanup:** Temporary video and audio files are wiped from the server after feature extraction by default.

---

## 3. High-Level Architecture & Pipeline

```
+-----------------------------------------------------------------------------------+
|                              MEDIA INGESTION LAYER                                |
|   - Recorded Classroom Video (MP4 / AVI / MOV)                                    |
|   - Recorded Classroom Audio (WAV / MP3 / OGG)                                    |
|   - One-Click Synthetic Demo Generator (CS401 Sample Lecture)                     |
+----------------------------------------+------------------------------------------+
                                         |
               +-------------------------+-------------------------+
               |                                                   |
               v                                                   v
+-----------------------------+                     +-------------------------------+
|       VISION PIPELINE       |                     |        AUDIO PIPELINE         |
| - Multi-Stage Person        |                     | - 16kHz Normalization         |
|   Detection (HOG + Haar     |                     | - Short-Time RMS Energy       |
|   + Silhouette Fallback)    |                     | - Zero-Crossing Rate (ZCR)    |
| - Centroid & IoU Tracking   |                     | - Vocal Bandpass (300-3400Hz) |
| - Sustained Presence Logic  |                     | - Speech vs. Silence Ratio    |
| - Scene Motion Energy (0-1) |                     | - Dynamic Noise Floor         |
+--------------+--------------+                     +---------------+---------------+
               |                                                    |
               +-------------------------+--------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                             MULTIMODAL AGENT ENGINE                               |
|   - Temporal Window Alignment (Synchronized 5.0-Second Windows)                   |
|   - Data Quality & Single-Modality Confidence Scoring                             |
|   - Deterministic Decision Tree:                                                  |
|     * Active Discussion        (High Speech + Low/Med Motion)                     |
|     * Attentive Lecture        (Med Speech  + Low Motion)                         |
|     * Collaborative Group Work (High Speech + High Motion)                        |
|     * Passive / Lull           (Low Speech  + Low Motion)                         |
|     * Transition / Restless    (Low Speech  + High Motion)                        |
+----------------------------------------+------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                       ANALYTICS & RECOMMENDATION ENGINE                           |
|   - Cohort Attendance KPIs (Present %, Partial %, Avg Duration)                   |
|   - 3-Phase Temporal Trend Trajectory (Opening -> Core -> Closing)                |
|   - Deterministic Pedagogical Rules & Auditable Evidence Chains                   |
|   - Student-Facing Non-Evaluative Aggregate Summary                               |
+----------------------------------------+------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                           LOCAL PERSISTENCE (SQLite 3)                            |
|   - sessions, attendance_records, video_summaries, audio_summaries,               |
|     engagement_intervals, recommendations (CASCADE foreign keys)                  |
+----------------------------------------+------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                             TEACHER DASHBOARD (UI)                                |
|   - Overview Metric Cards (Attendance %, Engagement Index, Dominant Mode)         |
|   - Chart.js Visualizations (Timeline, Multi-Axis Correlation, Mode Doughnut)     |
|   - Attendance Table with Inline Teacher Review & Name Mapping                    |
|   - Export to CSV (Attendance & Multimodal Time-Series Analytics)                 |
+-----------------------------------------------------------------------------------+
```

---

## 4. Technology Stack

| Layer | Component | Version / Library |
| :--- | :--- | :--- |
| **Language** | Python | 3.11.9 (64-bit) |
| **Web Server & REST API** | Flask, Flask-CORS, Werkzeug | Flask 3.1.3 |
| **Computer Vision** | OpenCV Headless | opencv-python-headless 4.11.0 |
| **Acoustic Signal Processing** | SciPy & SoundFile | scipy 1.17.1, soundfile 0.14.0 |
| **Data Processing** | NumPy & Pandas | numpy 1.26.4, pandas 3.0.6 |
| **Persistence** | SQLite 3 | Embedded SQLite |
| **Frontend UI** | HTML5, CSS3, JavaScript (ES6+) | Native Responsive UI |
| **Charts** | Chart.js | 4.4.1 (UMD) |
| **Testing** | Pytest | pytest 9.1.1 (21/21 passing) |

---

## 5. Project Directory Structure

```
multimodel/
├── app.py                      # Flask Application factory & static routing
├── requirements.txt            # Python dependencies with pinned versions
├── README.md                   # Complete system documentation
├── .env.example                # Environment variable defaults
├── .gitignore                  # Git ignore rules
│
├── backend/
│   ├── config.py               # Central configuration & thresholds
│   ├── database/
│   │   ├── db.py               # SQLite connection & CRUD repository
│   │   └── schema.sql          # DDL tables & indices
│   ├── routes/
│   │   ├── session_routes.py   # /api/sessions CRUD
│   │   ├── processing_routes.py# /upload, /process, /process-demo
│   │   ├── attendance_routes.py# /attendance & teacher mapping
│   │   ├── analytics_routes.py # /analytics report aggregation
│   │   └── export_routes.py    # CSV export endpoints
│   ├── services/
│   │   ├── vision/             # PersonDetector, MotionAnalyzer, Tracker, Attendance
│   │   ├── audio/              # AudioAnalysisService (RMS, ZCR, Bandpass)
│   │   ├── agent/              # SignalAligner & MultimodalEngagementAgent
│   │   └── analytics/          # SessionAnalyticsEngine & RecommendationEngine
│   └── utils/
│       ├── file_validator.py   # Security sanitization & retention cleanup
│       └── sample_generator.py # Synthetic classroom media generator
│
├── frontend/
│   ├── index.html              # Modern responsive Teacher Dashboard UI
│   ├── css/
│   │   └── style.css           # Styling system & responsive layout
│   └── js/
│       ├── app.js              # REST API controller & dashboard state
│       └── charts.js           # Chart.js visualization wrappers
│
├── sample_data/                # Standalone sample MP4 and WAV media
│   ├── classroom_sample.mp4
│   └── classroom_sample.wav
│
├── tests/                      # Automated test suite (21 unit & integration tests)
│   ├── test_database.py
│   ├── test_vision.py
│   ├── test_audio.py
│   ├── test_multimodal.py
│   ├── test_analytics.py
│   └── test_api.py
│
└── docs/                       # University & Board Infinity evaluation documentation
    ├── ARCHITECTURE.md
    ├── REQUIREMENTS.md
    ├── API_SPEC.md
    ├── MILESTONES.md
    ├── VIVA_QUESTIONS.md
    ├── DEMO_GUIDE.md
    └── BOARD_INFINITY_SUBMISSION.md
```

---

## 6. Installation & Execution Guide

### Prerequisites
* Windows 10/11, macOS, or Linux.
* Python 3.11 installed.

### Step 1: Clone / Open Project Folder
```powershell
cd c:\Users\DELL\OneDrive\Desktop\multimodel
```

### Step 2: Activate Virtual Environment
The virtual environment has already been created in `.venv`:
```powershell
.\.venv\Scripts\Activate.ps1
```

### Step 3: Verify Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Run the Full Test Suite
Ensure all 21 automated tests pass:
```powershell
pytest tests/ -v
```

### Step 5: Start the Local Flask Server
```powershell
python app.py
```
Output:
```
Starting Multimodal Classroom Intelligence Server on http://127.0.0.1:5000
 * Running on http://127.0.0.1:5000
```

### Step 6: Access the Teacher Dashboard
Open your browser and navigate to:
**`http://127.0.0.1:5000`**

---

## 7. How to Demonstrate the Project

### Option A: One-Click Instant Evaluation Demo (Recommended)
1. In the left sidebar, click the **"▶ Launch Interactive Demo"** button.
2. The system automatically:
   - Synthesizes a realistic 15-second classroom lecture scene with 4 seated students and synchronized vocal audio.
   - Executes person tracking, audio spectral analysis, multimodal fusion, and pedagogical advice generation.
   - Populates the dashboard with real KPIs, interactive Chart.js graphs, and sustained presence records.
3. In the **Participant Attendance** table, click **"Review / Map"** on any student track (e.g., Track #1), type a student's name (e.g., "Alex Mercer"), and click **"Save Mapping"**. Notice how the track immediately updates in SQLite.
4. Click **"📥 Export Attendance CSV"** or **"📊 Export Analytics CSV"** to inspect the generated spreadsheets.

### Option B: Uploading Sample Media Files
1. In the sidebar, select:
   - Video: `sample_data/classroom_sample.mp4`
   - Audio: `sample_data/classroom_sample.wav`
2. Click **"⚙️ Ingest & Run Agent"**.
3. The server processes the files locally, generates the analytics report, and wipes temporary media according to privacy retention policy.

---

## 8. Verification & Test Results Summary

The project includes 21 comprehensive automated tests across all system layers:

| Test Suite | Module Under Test | Tests | Status |
| :--- | :--- | :--- | :--- |
| `tests/test_database.py` | SQLite schema, cascade deletion, CRUD, manual student mapping | 4 | **PASSED** |
| `tests/test_vision.py` | HOG/Haar detector, IoU/Centroid tracker, occlusion handling | 3 | **PASSED** |
| `tests/test_audio.py` | Acoustic RMS, ZCR, speech-band filtering, noise floor | 3 | **PASSED** |
| `tests/test_multimodal.py` | Timestamp alignment, missing data fallback, rule-based inference | 3 | **PASSED** |
| `tests/test_analytics.py` | KPI calculation, 3-phase trends, pedagogical recommendations | 4 | **PASSED** |
| `tests/test_api.py` | Health, CRUD, demo flow, student mapping PATCH, CSV exports | 4 | **PASSED** |
| **Total** | **End-to-End System** | **21** | **ALL PASSED (100%)** |

---

## 9. Academic & Evaluation Documentation

Detailed documentation prepared for university project review and Board Infinity evaluation:
- [System Architecture](docs/ARCHITECTURE.md)
- [Requirements Specification](docs/REQUIREMENTS.md)
- [REST API Specification](docs/API_SPEC.md)
- [Milestones & Evidence Tracker](docs/MILESTONES.md)
- [Viva Questions & Model Answers](docs/VIVA_QUESTIONS.md)
- [Step-by-Step Demo Guide](docs/DEMO_GUIDE.md)
- [Board Infinity Submission Report](docs/BOARD_INFINITY_SUBMISSION.md)
