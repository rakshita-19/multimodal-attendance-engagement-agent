# REST API Specification

Base URL: `http://127.0.0.1:5000/api`

### 1. Health & Status
- **`GET /health`**
  - Response: `{"status": "ok", "app": "Multimodal Attendance & Engagement Agent", "version": "1.0.0"}`

### 2. Session Management
- **`POST /sessions`**
  - Payload: `{"title": "string", "notes": "string"}`
  - Response: Session metadata object.
- **`GET /sessions`**
  - Response: Array of session objects ordered by timestamp descending.
- **`GET /sessions/<session_id>`**
  - Response: Session object or 404.
- **`DELETE /sessions/<session_id>`**
  - Response: `{"success": true, "message": "Session deleted"}`

### 3. Media Ingestion & Processing
- **`POST /sessions/<session_id>/upload`**
  - Multipart Form: `video` (file, optional), `audio` (file, optional)
  - Response: Saved file paths, media validation status.
- **`POST /sessions/<session_id>/process`**
  - Payload (optional): `{"min_presence_seconds": 10.0, "window_size": 5.0}`
  - Response: Pipeline execution summary (video, audio, multimodal alignment, recommendations).
- **`POST /sessions/<session_id>/process-demo`**
  - Generates synthetic test classroom video & audio in-memory/locally, runs the complete pipeline, and populates the session. Ideal for instant evaluation and demo.

### 4. Attendance & Student Mapping
- **`GET /sessions/<session_id>/attendance`**
  - Response: List of attendance records for the session.
- **`PATCH /sessions/<session_id>/attendance/<int:track_id>`**
  - Payload: `{"student_name": "string", "notes": "string"}`
  - Response: Updated attendance record.

### 5. Analytics & Recommendations
- **`GET /sessions/<session_id>/analytics`**
  - Response: Complete analytics bundle including video summary, audio summary, engagement intervals, KPIs, and pedagogical recommendations.
- **`GET /sessions/<session_id>/export/attendance.csv`**
  - Response: CSV download for session attendance.
- **`GET /sessions/<session_id>/export/analytics.csv`**
  - Response: CSV download for session time-series engagement intervals.
