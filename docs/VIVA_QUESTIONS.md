# Viva Voce Questions & Expert Model Answers

Prepared for B.Tech Final Year Evaluation and Board Infinity Project Defense.

---

### Q1: What is the core problem your project solves, and how does it differ from traditional attendance systems?
**Answer:**
Traditional attendance systems rely either on manual roll calls (which consume instructional time and are prone to proxy attendance) or intrusive biometric facial recognition (which poses significant student privacy risks, stores biometric facial embeddings, and requires constant cloud access). 
Our **Multimodal Attendance & Engagement Agent** introduces a privacy-preserving, local alternative. It computes **sustained-presence attendance** using temporal object tracking without storing facial biometric templates. Furthermore, it combines visual presence with acoustic signal dynamics to give instructors explainable, real-time feedback on classroom engagement without relying on third-party cloud AI or surveillance.

---

### Q2: Why did you use transient Track IDs instead of automated facial recognition?
**Answer:**
Under GDPR, FERPA, and ethical AI principles, automated facial recognition in educational spaces carries high risks of algorithmic bias, misidentification, and unauthorized biometric profiling. 
Our system assigns temporary tracking tokens (`Track #1`, `Track #2`) to monitor sustained presence during a specific session. If real-world identity association is needed, we provide an explicit **Teacher Review / Manual Mapping** feature. This keeps a human educator in the loop and prevents automated surveillance errors.

---

### Q3: How do you track participants across frames, and how do you handle temporary occlusions?
**Answer:**
We employ a multi-stage tracking architecture:
1. **Detection:** We combine OpenCV's HOG (Histogram of Oriented Gradients) Person Detector, Haar Cascade frontal face/upper-body classifiers, and contour-based silhouette analysis with Non-Maximum Suppression (NMS).
2. **Data Association:** In each incoming frame, we compute an **Intersection-over-Union (IoU)** matrix against active tracks. Detections exceeding an IoU threshold (0.25) are matched. For remaining candidates, we calculate Euclidean distance between bounding box centroids.
3. **Occlusion Handling:** If a student momentarily bends down or someone walks in front of them, the detector may miss them for several frames. Instead of instantly dropping the track, our tracker increments a `disappeared_frames` counter. As long as `disappeared_frames <= max_disappeared` (30 frames / ~1.5s), the track record is preserved and recovers immediately when visible again.

---

### Q4: How does your audio module preserve privacy while still measuring engagement?
**Answer:**
Our audio module strictly extracts **mathematical acoustic features** rather than linguistic content:
1. **Short-Time RMS Energy:** Measures ambient sound volume across 50ms frames.
2. **Zero-Crossing Rate (ZCR):** Analyzes signal frequency transitions to differentiate speech from background hum.
3. **Vocal Bandpass Filtering (300 Hz – 3400 Hz):** Extracts signal energy residing in the standard human vocal formant range using a 4th-order Butterworth filter.
4. **No Speech-to-Text or Speaker Diarization:** We do not transcribe words or identify who is speaking. A quiet student is never penalized, and conversational content is never stored or transmitted.

---

### Q5: How do you align video and audio signals given that video operates in frames and audio operates in sample rates?
**Answer:**
We implement a **synchronized temporal windowing strategy** (`SignalAligner`):
- Both modalities are segmented into uniform time windows (default: 5.0 seconds).
- The video module computes the average visible headcount and mean scene motion energy within each $[t, t + \Delta t]$ window.
- The audio module computes average RMS energy and the fraction of sub-blocks matching speech-like acoustics within the exact same $[t, t + \Delta t]$ window.
- The multimodal agent fuses these aligned vectors into a composite engagement index and classifies the interaction mode.

---

### Q6: Why did you use deterministic rule-based reasoning rather than a Large Language Model (LLM) or Black-Box Neural Network for recommendations?
**Answer:**
1. **Auditable Explainability:** In educational settings, teachers need to know *why* a system suggested an interactive check-in or pacing pause. Our rules link explicitly to quantitative evidence (e.g., "Acoustic lull sustained for 15 seconds across intervals 2-4").
2. **Deterministic & Hallucination-Free:** LLMs can hallucinate non-existent classroom events or provide unpredictable feedback.
3. **Zero Cost & Local Privacy:** A rule-based engine executes in milliseconds on standard CPU hardware without cloud API costs or data leakage.

---

### Q7: What are the distinct interaction modes your multimodal agent infers?
**Answer:**
1. **Active Discussion:** High vocal activity + low-to-moderate motion + visible headcount.
2. **Attentive Listening / Lecture:** Steady vocal delivery in the vocal band + calm physical seating.
3. **Collaborative Group Work:** High physical motion co-occurring with decentralized vocal activity across multiple attendees.
4. **Passive / Lull:** Low acoustic presence + minimal motion (indicates silent reading, writing, or pauses).
5. **Transition / Restlessness:** Elevated scene motion without vocal activity (indicates room movement, packing up, or restlessness).

---

### Q8: What database did you choose and how do you ensure data integrity?
**Answer:**
We use **SQLite 3** because it is lightweight, embedded, serverless, and requires zero cloud configuration. We enforce:
- Foreign key constraints (`PRAGMA foreign_keys = ON;`) with `ON DELETE CASCADE`.
- Parameterized SQL queries to prevent SQL injection vulnerabilities.
- Unique constraints (`UNIQUE(session_id, track_id)`) to eliminate duplicate participant attendance records.
- Secondary indexes on foreign keys (`session_id`) for $O(1)$ fast query retrieval.

---

### Q9: What happens if a video stream is available but the microphone is disconnected?
**Answer:**
Our `SignalAligner` detects single-modality inputs gracefully. If audio is missing, it processes vision intervals alone, uses vision-only decision rules, and discounts the overall data quality confidence score (from 0.95 down to 0.65). The system never crashes when a sensor channel is absent.

---

### Q10: What are the main limitations of the current system, and what is your future scope?
**Answer:**
- **Limitation 1:** If a participant leaves the classroom for an extended period and re-enters, the tracker assigns a new Track ID because it does not maintain persistent facial embeddings. The teacher review tool bridges this gap.
- **Limitation 2:** Camera position and occlusion: Seated participants obscured behind high podiums or directly behind taller attendees may have reduced visibility.
- **Future Scope:** Integrating edge-accelerated depth cameras (e.g., Intel RealSense) for 3D spatial occupancy, multi-microphone acoustic beamforming for spatial speaker direction without recording content, and institutional LMS integration (Canvas / Moodle / Blackboard).
