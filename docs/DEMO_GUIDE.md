# Step-by-Step Project Demonstration Guide

Use this script during your college project presentation or Board Infinity viva defense.

---

## 1. Environment Preparation (Before Evaluator Arrives)
1. Open PowerShell terminal in the project directory:
   ```powershell
   cd c:\Users\DELL\OneDrive\Desktop\multimodel
   ```
2. Verify virtual environment and dependencies:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   pytest tests/ -v
   ```
   *(Point out to evaluator: "All 21 automated unit and integration tests are passing 100% across database, vision, audio, agent, analytics, and API modules.")*
3. Start the Flask application:
   ```powershell
   python app.py
   ```
4. Open browser to:
   `http://127.0.0.1:5000`

---

## 2. Walkthrough Script for Evaluators

### Step 1: Explain the Core Objective and Problem
* **Script:**
  > "Respected evaluators, modern classroom systems either rely on manual roll-call or intrusive facial biometric surveillance. Our project, **Multimodal Attendance & Engagement Agent**, is an AI-powered, privacy-preserving classroom intelligence platform running entirely locally on standard CPU hardware without paid cloud AI."

### Step 2: Showcase the Instant Evaluation Demo
* **Action:**
  Click the **"▶ Launch Interactive Demo"** button on the left sidebar.
* **Script:**
  > "For instant evaluation, our system generates a synthetic 15-second multi-participant classroom lecture with individual student desks, natural attendee movement, and speech bursts. The local multimodal engine immediately processes both streams."
* **What to highlight on screen:**
  1. **Overview KPI Cards:**
     - Sustained Attendance Rate (e.g. 75% - 100%).
     - Tracked attendees count (4 participants tracked).
     - Composite Multimodal Engagement Score (e.g. 75 / 100).
     - Dominant Interaction Mode (e.g., Active Discussion or Attentive Lecture).
  2. **Privacy & Pedagogical Integrity Banner:**
     - Explicit disclosure that individual students are **not** labeled as inattentive based on face or gaze, preserving student dignity.

### Step 3: Explain the Chart Visualizations
* **Action:**
  Scroll down to the charts.
* **Script:**
  > "Here, Chart.js displays three synchronized dimensions:
  > 1. **Engagement Timeline:** Shows continuous composite scores across 5-second intervals.
  > 2. **Interaction Mode Distribution:** Doughnut chart breaking down time spent in Active Discussion, Lecture Listening, Group Work, or Lull.
  > 3. **Observable Signals Correlation:** Shows how participant headcount directly correlates with speech acoustic activity and motion energy."

### Step 4: Demonstrate Sustained Attendance & Ethical Name Mapping
* **Action:**
  Scroll to the **Participant Attendance** table. Click **"Review / Map"** on Track #1.
  Enter Name: `Alex Mercer`, Notes: `Roll No 401, seated front row`. Click **"Save Mapping"**.
* **Script:**
  > "Notice that the vision tracker outputs transient tokens: Track #1, Track #2, calculated by sustained presence duration. To maintain privacy, we do not perform automatic facial recognition. Instead, the teacher review feature allows the instructor to verify and map the student's name with full human accountability."

### Step 5: Highlight Explainable Pedagogical Recommendations
* **Action:**
  Scroll to the **Teaching Recommendations** section.
* **Script:**
  > "Our recommendation engine is deterministic and rule-based rather than a black-box LLM. Each card specifies the category, priority, actionable suggestion, and the exact timestamped acoustic and visual evidence triggering it."

### Step 6: Demonstrate CSV Report Exports
* **Action:**
  Click **"📥 Export Attendance CSV"** and **"📊 Export Analytics CSV"**. Open the downloaded CSV files.
* **Script:**
  > "All attendance logs and time-series intervals can be exported to standard CSV spreadsheets for administrative record-keeping and LMS archival."

### Step 7: Optional Media File Upload Demonstration
* **Action:**
  In the sidebar, choose:
  - Video: `sample_data/classroom_sample.mp4`
  - Audio: `sample_data/classroom_sample.wav`
  Click **"⚙️ Ingest & Run Agent"**.
* **Script:**
  > "In addition to the synthetic demo, the application seamlessly ingests real recorded classroom MP4/AVI videos and WAV/MP3 audio files, enforcing automatic media cleanup upon completion."
