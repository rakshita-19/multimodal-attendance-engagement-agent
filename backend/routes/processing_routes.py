from pathlib import Path
from flask import Blueprint, request, jsonify
from backend.config import Config
from backend.database.db import (
    get_session,
    update_session_status,
    save_attendance_records,
    save_video_summary,
    save_audio_summary,
    save_engagement_intervals,
    save_recommendations,
    get_complete_session_report
)
from backend.utils.file_validator import (
    is_allowed_video,
    is_allowed_audio,
    sanitize_and_save,
    safe_remove_file
)
from backend.utils.sample_generator import generate_sample_classroom_media
from backend.services.vision.attendance_service import VisionAttendanceService
from backend.services.audio.audio_service import AudioAnalysisService
from backend.services.agent.multimodal_agent import MultimodalEngagementAgent
from backend.services.analytics.recommendations import RecommendationEngine

processing_bp = Blueprint("processing", __name__, url_prefix="/api/sessions")

@processing_bp.route("/<session_id>/upload", methods=["POST"])
def upload_media(session_id: str):
    """Handle uploading of video and/or audio files for a session."""
    sess = get_session(session_id)
    if not sess:
        return jsonify({"status": "error", "message": "Session not found"}), 404

    Config.ensure_directories()
    uploaded_video_path = None
    uploaded_audio_path = None

    if "video" in request.files:
        video_file = request.files["video"]
        if video_file and video_file.filename != "":
            if not is_allowed_video(video_file.filename):
                return jsonify({"status": "error", "message": f"Unsupported video format. Allowed: {Config.ALLOWED_VIDEO_EXTENSIONS}"}), 400
            saved_v = sanitize_and_save(video_file, Config.UPLOAD_FOLDER, prefix=session_id)
            uploaded_video_path = str(saved_v)

    if "audio" in request.files:
        audio_file = request.files["audio"]
        if audio_file and audio_file.filename != "":
            if not is_allowed_audio(audio_file.filename):
                return jsonify({"status": "error", "message": f"Unsupported audio format. Allowed: {Config.ALLOWED_AUDIO_EXTENSIONS}"}), 400
            saved_a = sanitize_and_save(audio_file, Config.UPLOAD_FOLDER, prefix=session_id)
            uploaded_audio_path = str(saved_a)

    if not uploaded_video_path and not uploaded_audio_path:
        return jsonify({"status": "error", "message": "No valid video or audio file provided in request"}), 400

    conn_db = None
    from backend.database.db import get_connection
    conn = get_connection()
    try:
        with conn:
            if uploaded_video_path and uploaded_audio_path:
                conn.execute(
                    "UPDATE sessions SET video_file_name = ?, audio_file_name = ?, status = 'media_uploaded' WHERE id = ?",
                    (uploaded_video_path, uploaded_audio_path, session_id)
                )
            elif uploaded_video_path:
                conn.execute(
                    "UPDATE sessions SET video_file_name = ?, status = 'media_uploaded' WHERE id = ?",
                    (uploaded_video_path, session_id)
                )
            elif uploaded_audio_path:
                conn.execute(
                    "UPDATE sessions SET audio_file_name = ?, status = 'media_uploaded' WHERE id = ?",
                    (uploaded_audio_path, session_id)
                )
    finally:
        conn.close()

    return jsonify({
        "status": "success",
        "message": "Media uploaded successfully",
        "video_path": uploaded_video_path,
        "audio_path": uploaded_audio_path
    })

@processing_bp.route("/<session_id>/process", methods=["POST"])
def process_session_media(session_id: str):
    """
    Execute full local multimodal pipeline on session media.
    Performs vision tracking, audio signal processing, fusion, and persistence.
    """
    sess = get_session(session_id)
    if not sess:
        return jsonify({"status": "error", "message": "Session not found"}), 404

    video_path = sess.get("video_file_name")
    audio_path = sess.get("audio_file_name")

    if not video_path and not audio_path:
        return jsonify({
            "status": "error",
            "message": "No media associated with this session. Upload files or use /process-demo."
        }), 400

    update_session_status(session_id, "processing")

    try:
        req_data = request.get_json(silent=True) or {}
        min_pres = float(req_data.get("min_presence_seconds", Config.MIN_PRESENCE_SECONDS))
        window_size = float(req_data.get("window_size", Config.WINDOW_SIZE_SECONDS))

        vision_intervals = []
        video_summary = None
        attendance_records = []
        video_duration = 0.0

        # 1. Process Video if present
        if video_path and Path(video_path).exists():
            update_session_status(session_id, "processing_video")
            vision_service = VisionAttendanceService(
                min_presence_seconds=min_pres,
                frame_sample_rate=Config.FRAME_SAMPLE_RATE,
                window_size_seconds=window_size
            )
            v_res = vision_service.process_video(video_path, session_id)
            video_summary = v_res["video_summary"]
            vision_intervals = v_res["vision_intervals"]
            attendance_records = v_res["attendance_records"]
            video_duration = video_summary["duration_seconds"]

            save_video_summary(session_id, video_summary)
            save_attendance_records(session_id, attendance_records)

        # 2. Process Audio if present
        audio_intervals = []
        audio_summary = None
        audio_duration = 0.0

        if audio_path and Path(audio_path).exists():
            update_session_status(session_id, "processing_audio")
            audio_service = AudioAnalysisService(window_size_seconds=window_size)
            a_res = audio_service.process_audio(audio_path, session_id)
            audio_summary = a_res["audio_summary"]
            audio_intervals = a_res["audio_intervals"]
            audio_duration = audio_summary["duration_seconds"]

            save_audio_summary(session_id, audio_summary)

        # Determine overall session duration
        effective_duration = max(video_duration, audio_duration, 1.0)

        # 3. Multimodal Alignment & Reasoning
        update_session_status(session_id, "analyzing")
        agent = MultimodalEngagementAgent(window_size_seconds=window_size)
        agent_res = agent.analyze_session(
            session_id=session_id,
            vision_intervals=vision_intervals,
            audio_intervals=audio_intervals,
            session_duration_seconds=effective_duration
        )

        intervals = agent_res["intervals"]
        save_engagement_intervals(session_id, intervals)

        # 4. Generate Pedagogical Recommendations
        recommender = RecommendationEngine()
        recs = recommender.generate_recommendations(
            session_id=session_id,
            video_summary=video_summary,
            audio_summary=audio_summary,
            intervals=intervals,
            attendance_records=attendance_records
        )
        save_recommendations(session_id, recs)

        # 5. Enforce Privacy-Preserving Retention Policy
        raw_retained = 1
        if Config.AUTO_CLEANUP_RAW_MEDIA:
            safe_remove_file(Path(video_path) if video_path else None)
            safe_remove_file(Path(audio_path) if audio_path else None)
            raw_retained = 0

        update_session_status(
            session_id=session_id,
            status="completed",
            duration_seconds=round(effective_duration, 2),
            raw_files_retained=raw_retained
        )

        report = get_complete_session_report(session_id)
        return jsonify({
            "status": "success",
            "message": "Session processed successfully",
            "report": report
        })

    except Exception as e:
        update_session_status(session_id, "failed")
        return jsonify({"status": "error", "message": f"Processing error: {str(e)}"}), 500

@processing_bp.route("/<session_id>/process-demo", methods=["POST"])
def process_demo_session(session_id: str):
    """
    Generate realistic synthetic classroom video & audio locally,
    execute full multimodal processing, and populate analytics for instant demo evaluation.
    """
    sess = get_session(session_id)
    if not sess:
        return jsonify({"status": "error", "message": "Session not found"}), 404

    Config.ensure_directories()
    v_path = Config.TEMP_FOLDER / f"{session_id}_demo.mp4"
    a_path = Config.TEMP_FOLDER / f"{session_id}_demo.wav"

    # Generate synthetic classroom media
    generate_sample_classroom_media(v_path, a_path, duration_sec=15.0)

    # Attach paths to session in DB
    from backend.database.db import get_connection
    conn = get_connection()
    try:
        with conn:
            conn.execute(
                "UPDATE sessions SET video_file_name = ?, audio_file_name = ? WHERE id = ?",
                (str(v_path), str(a_path), session_id)
            )
    finally:
        conn.close()

    # Trigger processing
    return process_session_media(session_id)
