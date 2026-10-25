import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env if present
load_dotenv(BASE_DIR / ".env")

class Config:
    """Application configuration parameters with safe defaults."""
    
    SECRET_KEY = os.getenv("SECRET_KEY", "classroom-intelligence-local-secret-2026")
    DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")
    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", 5000))

    # Persistence
    DATABASE_PATH = os.getenv("DATABASE_PATH", str(BASE_DIR / "multimodal_classroom.db"))
    SCHEMA_PATH = BASE_DIR / "backend" / "database" / "schema.sql"

    # Temporary and Upload folders
    UPLOAD_FOLDER = BASE_DIR / os.getenv("UPLOAD_FOLDER", "uploads")
    TEMP_FOLDER = BASE_DIR / os.getenv("TEMP_FOLDER", "temp")
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 100 * 1024 * 1024))  # 100 MB

    # Allowed extensions
    ALLOWED_VIDEO_EXTENSIONS = {"mp4", "avi", "mov", "mkv", "webm"}
    ALLOWED_AUDIO_EXTENSIONS = {"wav", "mp3", "ogg", "flac", "aac", "m4a"}

    # Vision Processing Config
    MIN_PRESENCE_SECONDS = float(os.getenv("MIN_PRESENCE_SECONDS", 10.0))  # seconds before 'present' status
    PARTIAL_PRESENCE_RATIO = 0.40  # >= 40% of session time is considered partial if min presence met
    FULL_PRESENCE_RATIO = 0.75     # >= 75% of session time is considered fully present
    TRACK_MAX_DISAPPEARED_FRAMES = int(os.getenv("TRACK_MAX_DISAPPEARED_FRAMES", 30))
    TRACK_IOU_THRESHOLD = 0.30
    FRAME_SAMPLE_RATE = 2  # Process every 2nd or 3rd frame for CPU efficiency
    
    # Audio Processing Config
    AUDIO_SAMPLE_RATE = 16000  # Resample for standardized signal processing
    AUDIO_ENERGY_THRESHOLD = float(os.getenv("AUDIO_ENERGY_THRESHOLD", 0.015))
    AUDIO_SILENCE_THRESHOLD = 0.005
    SPEECH_ZCR_LOW = 0.02
    SPEECH_ZCR_HIGH = 0.25
    SPEECH_BAND_HZ = (300, 3400)

    # Multimodal Alignment Config
    WINDOW_SIZE_SECONDS = float(os.getenv("WINDOW_SIZE_SECONDS", 5.0))  # 5-second synchronized time windows
    
    # Retention Policy
    AUTO_CLEANUP_RAW_MEDIA = True  # Privacy-first: delete temporary raw video/audio after feature extraction

    @classmethod
    def ensure_directories(cls):
        """Ensure necessary storage directories exist."""
        cls.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
        cls.TEMP_FOLDER.mkdir(parents=True, exist_ok=True)
        Path(cls.DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)
