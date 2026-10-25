import os
import re
from pathlib import Path
from werkzeug.utils import secure_filename
from backend.config import Config

def is_allowed_video(filename: str) -> bool:
    """Check if the file has an allowed video extension."""
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in Config.ALLOWED_VIDEO_EXTENSIONS

def is_allowed_audio(filename: str) -> bool:
    """Check if the file has an allowed audio extension."""
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in Config.ALLOWED_AUDIO_EXTENSIONS

def sanitize_and_save(file_obj, destination_folder: Path, prefix: str = "") -> Path:
    """Safely sanitize a filename, ensure destination directory exists, and save file."""
    destination_folder.mkdir(parents=True, exist_ok=True)
    raw_name = secure_filename(file_obj.filename)
    if not raw_name:
        raw_name = "upload.dat"
        
    cleaned_prefix = re.sub(r'[^a-zA-Z0-9_-]', '_', prefix)
    target_name = f"{cleaned_prefix}_{raw_name}" if cleaned_prefix else raw_name
    target_path = destination_folder / target_name
    
    file_obj.save(str(target_path))
    return target_path

def safe_remove_file(file_path: Path):
    """Safely delete a temporary file if it exists."""
    try:
        if file_path and Path(file_path).exists():
            Path(file_path).unlink()
    except Exception as e:
        # Avoid crashing when cleaning up temporary files
        pass
