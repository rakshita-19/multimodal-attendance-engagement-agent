# Requirements Specification

## 1. Functional Requirements
- **FR-1: Video Ingestion & Processing**: Process local video files (.mp4, .avi, .mov, .mkv) and real-time webcam video feed with downsampling for CPU efficiency.
- **FR-2: Person Detection & Tracking**: Detect visible classroom participants per frame using local computer vision (HOG person detector & frontal face cascades) and track persistent participants across frames using IoU (Intersection-over-Union) and Centroid distance tracking.
- **FR-3: Sustained Presence Attendance**: Calculate continuous and cumulative visibility duration for each tracker ID. Classify into `present`, `partial`, or `insufficient_presence` using configurable time thresholds.
- **FR-4: Identity Disambiguation & Manual Review**: Prevent duplicate counting within the same track. Provide a clean UI for teachers to map temporary `Track #` identifiers to official student names.
- **FR-5: Privacy-Preserving Audio Processing**: Compute short-time Root Mean Square (RMS) energy, Zero Crossing Rate (ZCR), and spectral bandpass energy. Determine silence intervals and speech-like activity ratios. Strictly forbid speech-to-text or voice biometric profiling.
- **FR-6: Multimodal Alignment & Fusion**: Segment video and audio streams into uniform time windows (e.g., 5 seconds) and compute composite classroom engagement indicators using deterministic, transparent rules.
- **FR-7: Explainable Teaching Recommendations**: Rule-based pedagogical recommendations for lesson pacing, student check-ins, active discussions, or brain breaks, complete with explicit timestamped evidence.
- **FR-8: Teacher Dashboard & Visualizations**: Interactive web dashboard featuring summary cards, Chart.js time-series plots, attendance management, session history, and CSV export.

## 2. Non-Functional Requirements
- **NFR-1: Local Execution & Privacy**: Zero cloud dependency. No data egress to external LLMs or third-party computer vision APIs.
- **NFR-2: Performance & Latency**: Real-time or faster-than-real-time offline processing on standard modern multi-core consumer CPUs without requiring a dedicated GPU.
- **NFR-3: Reliability**: Graceful degradation when either audio or video is absent or corrupted.
- **NFR-4: Explainability**: 100% auditable deterministic logic. No "black-box" hallucinated outputs.
- **NFR-5: Modularity**: Clean separation of routes, services, database layer, utilities, and frontend presentation.
