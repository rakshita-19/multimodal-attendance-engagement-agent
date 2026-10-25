import pytest
import tempfile
import numpy as np
import soundfile as sf
from pathlib import Path
from backend.services.audio.audio_service import AudioAnalysisService

def create_synthetic_wav(filepath: Path, duration_seconds: float = 3.0, 
                         sample_rate: int = 16000, speech_interval: bool = True) -> Path:
    """Generate synthetic audio waveform with known acoustic characteristics."""
    t = np.linspace(0, duration_seconds, int(sample_rate * duration_seconds), endpoint=False)
    
    # Base low ambient noise (RMS ~ 0.002)
    noise = np.random.normal(0, 0.002, len(t))
    signal = noise.copy()

    if speech_interval:
        # Add vocal-band tone (e.g., 800Hz & 1500Hz formant) during second half
        speech_start = int(len(t) * 0.4)
        speech_end = int(len(t) * 0.9)
        tone = 0.35 * np.sin(2 * np.pi * 800 * t[speech_start:speech_end]) + \
               0.20 * np.sin(2 * np.pi * 1500 * t[speech_start:speech_end])
        signal[speech_start:speech_end] += tone

    sf.write(str(filepath), signal, sample_rate)
    return filepath

def test_audio_silence():
    """Verify audio processing on near-silent audio."""
    with tempfile.TemporaryDirectory() as tmpdir:
        wav_file = Path(tmpdir) / "silent.wav"
        create_synthetic_wav(wav_file, duration_seconds=2.0, speech_interval=False)

        service = AudioAnalysisService(window_size_seconds=1.0)
        res = service.process_audio(str(wav_file), session_id="test-silent")

        summary = res["audio_summary"]
        assert summary["duration_seconds"] >= 1.9
        assert summary["silence_percentage"] > 80.0
        assert summary["speech_like_percentage"] < 15.0

def test_audio_speech_detection():
    """Verify acoustic detection of vocal-band activity intervals."""
    with tempfile.TemporaryDirectory() as tmpdir:
        wav_file = Path(tmpdir) / "speech_test.wav"
        create_synthetic_wav(wav_file, duration_seconds=3.0, speech_interval=True)

        service = AudioAnalysisService(window_size_seconds=1.0)
        res = service.process_audio(str(wav_file), session_id="test-speech")

        summary = res["audio_summary"]
        assert summary["avg_rms_energy"] > 0.01
        assert summary["speech_like_percentage"] > 20.0
        assert len(res["audio_intervals"]) == 3
        # First interval should have lower speech ratio than the middle/last interval
        intervals = res["audio_intervals"]
        assert intervals[1]["speech_activity_ratio"] > intervals[0]["speech_activity_ratio"]

def test_audio_nonexistent_file():
    """Verify clean exception handling on missing file."""
    service = AudioAnalysisService()
    with pytest.raises(FileNotFoundError):
        service.process_audio("non_existent_audio_path.wav", "session-err")
