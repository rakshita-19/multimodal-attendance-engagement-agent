import time
import numpy as np
import soundfile as sf
from scipy import signal
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from backend.config import Config

class AudioAnalysisService:
    """
    Privacy-preserving local classroom audio processor.
    Extracts acoustic dynamics, RMS energy, and speech-like activity intervals
    WITHOUT transcription, voice recognition, or content inspection.
    """
    def __init__(self,
                 energy_threshold: float = Config.AUDIO_ENERGY_THRESHOLD,
                 silence_threshold: float = Config.AUDIO_SILENCE_THRESHOLD,
                 speech_band: Tuple[int, int] = Config.SPEECH_BAND_HZ,
                 window_size_seconds: float = Config.WINDOW_SIZE_SECONDS):
        self.energy_threshold = energy_threshold
        self.silence_threshold = silence_threshold
        self.speech_band = speech_band
        self.window_size_seconds = window_size_seconds

    def process_audio(self, audio_path: str, session_id: str) -> Dict[str, Any]:
        """
        Process a recorded audio file.
        Returns aggregate audio summary and synchronized time-series windows.
        """
        path = Path(audio_path)
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found at: {audio_path}")

        start_time = time.time()

        # Read audio file using soundfile
        try:
            data, sample_rate = sf.read(str(path))
        except Exception as e:
            raise ValueError(f"Failed to read audio file format: {e}")

        # Convert multi-channel audio to mono
        if len(data.shape) > 1:
            channels = data.shape[1]
            mono_data = np.mean(data, axis=1)
        else:
            channels = 1
            mono_data = data

        total_samples = len(mono_data)
        duration_seconds = total_samples / sample_rate if sample_rate > 0 else 0.0

        if total_samples == 0 or duration_seconds == 0:
            return self._empty_audio_result(session_id, sample_rate, channels)

        # Normalize audio signal
        max_amp = np.max(np.abs(mono_data))
        if max_amp > 0:
            norm_data = mono_data / max_amp
        else:
            norm_data = mono_data

        # 1. Compute Short-Time Frame Statistics (50ms frames with 25ms hop)
        frame_len = int(0.050 * sample_rate)  # 50 ms
        hop_len = int(0.025 * sample_rate)    # 25 ms
        
        num_frames = max(1, (total_samples - frame_len) // hop_len + 1)
        
        frame_rms_list = []
        frame_zcr_list = []
        frame_speech_flags = []

        # Bandpass filter coefficients for human vocal range (300Hz - 3400Hz)
        nyquist = sample_rate / 2.0
        low = min(0.9, max(0.01, self.speech_band[0] / nyquist))
        high = min(0.95, max(low + 0.05, self.speech_band[1] / nyquist))
        b, a = signal.butter(4, [low, high], btype="bandpass")

        # Speech-filtered signal
        filtered_data = signal.filtfilt(b, a, norm_data)

        for i in range(num_frames):
            start_s = i * hop_len
            end_s = start_s + frame_len
            chunk = norm_data[start_s:end_s]
            chunk_filt = filtered_data[start_s:end_s]

            # RMS Energy
            rms = np.sqrt(np.mean(chunk ** 2)) if len(chunk) > 0 else 0.0
            filt_rms = np.sqrt(np.mean(chunk_filt ** 2)) if len(chunk_filt) > 0 else 0.0
            frame_rms_list.append(rms)

            # Zero Crossing Rate (ZCR)
            zero_crossings = np.sum(np.abs(np.diff(chunk > 0))) / max(1, len(chunk))
            frame_zcr_list.append(zero_crossings)

            # Speech-like determination:
            # 1) Energy above ambient threshold
            # 2) Significant proportion in vocal band (filt_rms / rms > 0.45)
            # 3) ZCR typical of human speech (0.02 to 0.30)
            is_speech_like = (
                rms >= self.energy_threshold and
                (filt_rms / max(1e-5, rms) >= 0.40) and
                (0.02 <= zero_crossings <= 0.32)
            )
            frame_speech_flags.append(is_speech_like)

        frame_rms_arr = np.array(frame_rms_list)
        frame_flags_arr = np.array(frame_speech_flags)

        # Baseline noise floor (15th percentile of RMS)
        noise_floor = float(np.percentile(frame_rms_arr, 15)) if len(frame_rms_arr) > 0 else 0.0
        avg_rms = float(np.mean(frame_rms_arr)) if len(frame_rms_arr) > 0 else 0.0
        peak_rms = float(np.max(frame_rms_arr)) if len(frame_rms_arr) > 0 else 0.0

        silence_mask = frame_rms_arr < max(self.silence_threshold, noise_floor * 1.4)
        silence_pct = float(np.mean(silence_mask) * 100.0) if len(silence_mask) > 0 else 0.0
        speech_like_pct = float(np.mean(frame_flags_arr) * 100.0) if len(frame_flags_arr) > 0 else 0.0

        # Highly active discussion (sustained speech with higher than average energy)
        active_disc_mask = frame_flags_arr & (frame_rms_arr > avg_rms * 1.2)
        active_disc_pct = float(np.mean(active_disc_mask) * 100.0) if len(active_disc_mask) > 0 else 0.0

        # 2. Windowed Aggregations aligned with video intervals
        audio_intervals = self._compute_windowed_audio(
            norm_data, filtered_data, sample_rate, duration_seconds
        )

        proc_time = time.time() - start_time

        audio_summary = {
            "session_id": session_id,
            "duration_seconds": round(duration_seconds, 2),
            "sample_rate": int(sample_rate),
            "channels": int(channels),
            "avg_rms_energy": round(avg_rms, 4),
            "peak_rms_energy": round(peak_rms, 4),
            "silence_percentage": round(silence_pct, 1),
            "speech_like_percentage": round(speech_like_pct, 1),
            "active_discussion_percentage": round(active_disc_pct, 1),
            "noise_floor": round(noise_floor, 4),
            "processing_time_seconds": round(proc_time, 2)
        }

        return {
            "audio_summary": audio_summary,
            "audio_intervals": audio_intervals
        }

    def _compute_windowed_audio(self, data: np.ndarray, filtered_data: np.ndarray,
                                sample_rate: int, duration_seconds: float) -> List[Dict[str, Any]]:
        """Slice audio into uniform synchronization windows for multimodal fusion."""
        intervals = []
        samples_per_window = int(self.window_size_seconds * sample_rate)
        num_windows = int(np.ceil(duration_seconds / self.window_size_seconds))

        for w_idx in range(num_windows):
            start_sample = w_idx * samples_per_window
            end_sample = min(len(data), (w_idx + 1) * samples_per_window)
            chunk = data[start_sample:end_sample]
            chunk_filt = filtered_data[start_sample:end_sample]

            w_start_sec = w_idx * self.window_size_seconds
            w_end_sec = min(duration_seconds, (w_idx + 1) * self.window_size_seconds)

            if len(chunk) > 0:
                rms = float(np.sqrt(np.mean(chunk ** 2)))
                filt_rms = float(np.sqrt(np.mean(chunk_filt ** 2)))
                
                # Check sub-blocks of 50ms inside this window to compute speech activity ratio
                sub_len = int(0.050 * sample_rate)
                sub_count = max(1, len(chunk) // sub_len)
                speech_sub_count = 0
                for s in range(sub_count):
                    sc = chunk[s * sub_len:(s + 1) * sub_len]
                    sf_c = chunk_filt[s * sub_len:(s + 1) * sub_len]
                    s_rms = np.sqrt(np.mean(sc ** 2)) if len(sc) > 0 else 0
                    sf_rms = np.sqrt(np.mean(sf_c ** 2)) if len(sf_c) > 0 else 0
                    if s_rms >= self.energy_threshold and (sf_rms / max(1e-5, s_rms) >= 0.40):
                        speech_sub_count += 1
                
                speech_ratio = min(1.0, speech_sub_count / sub_count)
            else:
                rms = 0.0
                speech_ratio = 0.0

            intervals.append({
                "interval_index": w_idx,
                "start_seconds": round(w_start_sec, 2),
                "end_seconds": round(w_end_sec, 2),
                "audio_rms": round(rms, 4),
                "speech_activity_ratio": round(speech_ratio, 2)
            })

        return intervals

    def _empty_audio_result(self, session_id: str, sample_rate: int, channels: int) -> Dict[str, Any]:
        """Gracefully handle empty audio stream."""
        return {
            "audio_summary": {
                "session_id": session_id,
                "duration_seconds": 0.0,
                "sample_rate": sample_rate,
                "channels": channels,
                "avg_rms_energy": 0.0,
                "peak_rms_energy": 0.0,
                "silence_percentage": 100.0,
                "speech_like_percentage": 0.0,
                "active_discussion_percentage": 0.0,
                "noise_floor": 0.0,
                "processing_time_seconds": 0.0
            },
            "audio_intervals": []
        }
