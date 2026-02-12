"""
SST Engine
----------

How to run:
1. Activate your virtualenv: `& ".venv\Scripts\Activate.ps1"` on Windows PowerShell.
2. Install requirements: `pip install -r requirements.txt`.
3. Run a file test:

   python -c "from voice_agent.sst_engine import SSTEngine; print('ok')"

Description:
- `SSTEngine` performs offline speech-to-text using `stt_vosk.STTVosk`,
  segments audio using `SilenceDetector` from `src/audio/silence_detector.py`,
  and extracts acoustic features via OpenSMILE. It returns a JSON-like
  dictionary with `text` and `acoustic_features` matching the requested
  schema. This module does NOT perform emotion or stress scoring.
"""

import sys
from pathlib import Path
import json
from typing import Dict, Any, Optional

# Ensure `src` directory is on sys.path so imports work when scripts are run directly
from pathlib import Path as _Path
_SRC = str(_Path(__file__).resolve().parents[1])
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import numpy as np
import soundfile as sf
import opensmile

try:
    # Preferred relative import when used as package
    from .stt_vosk import STTVosk
    from ..audio.silence_detector import SilenceDetector
except Exception:
    # Fallback absolute imports when running as script
    from voice_agent.stt_vosk import STTVosk
    from audio.silence_detector import SilenceDetector


class SSTEngine:
    """Simple SST wrapper producing text + acoustic features.

    Methods:
    - `process_audio(wav_path)` -> Dict with `text` and `acoustic_features`.
    """

    def __init__(self, model_path: Optional[str] = None, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.stt = STTVosk(model_path=model_path, sample_rate=sample_rate)

        # OpenSMILE using eGeMAPS functionals (compact, informative)
        self.smile = opensmile.Smile(
            feature_set=opensmile.FeatureSet.eGeMAPS,
            feature_level=opensmile.FeatureLevel.Functionals,
        )

        self.silence_detector = SilenceDetector(sample_rate=sample_rate)

    def process_audio(self, wav_path: str) -> Dict[str, Any]:
        """
        Process a WAV file and return the requested output structure.

        Args:
            wav_path: Path to 16kHz mono WAV (PCM 16-bit preferred)

        Returns:
            {"text": str, "acoustic_features": {...}}
        """
        wav = Path(wav_path)
        if not wav.exists():
            raise FileNotFoundError(f"WAV not found: {wav_path}")

        audio, sr = sf.read(str(wav))
        if sr != self.sample_rate:
            raise ValueError(f"Expected {self.sample_rate}Hz, got {sr}Hz")

        # 1) Transcribe
        text = self.stt.transcribe(audio)

        # 2) Acoustic features from OpenSMILE
        features_df = self.smile.process_file(str(wav))

        # Map core features (safe fallbacks to 0)
        mapping = {
            "pitch_mean": "F0semitoneFrom27.5Hz_sma3nz_amean",
            "pitch_var": "F0semitoneFrom27.5Hz_sma3nz_stddevNorm",
            "energy": "loudness_sma3_amean",
            "jitter": "jitterLocal_sma3nz_amean",
            "shimmer": "shimmerLocaldB_sma3nz_amean",
        }

        acoustic = {}
        for k, col in mapping.items():
            acoustic[k] = float(features_df[col].values[0]) if col in features_df.columns else 0.0

        # MFCC (13 values) using same extraction logic as other modules
        mfcc_cols = [c for c in features_df.columns if c.lower().startswith("mfcc")]
        mfcc_vals = []
        for col in mfcc_cols:
            if len(mfcc_vals) >= 13:
                break
            mfcc_vals.append(float(features_df[col].values[0]))

        while len(mfcc_vals) < 13:
            mfcc_vals.append(0.0)

        acoustic["mfcc"] = mfcc_vals[:13]

        # 3) Silence-based pause analysis and speech_rate (words / voiced_seconds)
        pause_mean, voiced_sec = self._analyze_silences(audio)
        acoustic["pause_mean"] = pause_mean

        words = len(text.split()) if text else 0
        acoustic["speech_rate"] = (words / voiced_sec) if (voiced_sec > 0 and words > 0) else 0.0

        # Construct final output
        out = {"text": text, "acoustic_features": acoustic}
        return out

    def _analyze_silences(self, audio: np.ndarray):
        # reuse SilenceDetector frame logic similar to other modules
        if audio.ndim > 1:
            mono = audio.mean(axis=1)
        else:
            mono = audio

        frame_len = self.silence_detector.frame_samples
        num_frames = int(np.ceil(len(mono) / frame_len))

        pause_durations = []
        current_pause = 0
        in_voice = False
        voiced_frames = 0

        for i in range(num_frames):
            start = i * frame_len
            end = start + frame_len
            frame = mono[start:end]
            is_silent, _, _ = self.silence_detector.process_frame(frame)

            if is_silent:
                if in_voice:
                    current_pause += 1
                    in_voice = False
                else:
                    current_pause += 1
            else:
                if not in_voice and current_pause > 0:
                    pause_durations.append(current_pause * frame_len / self.sample_rate)
                    current_pause = 0
                in_voice = True
                voiced_frames += 1

        pause_mean = float(np.mean(pause_durations)) if pause_durations else 0.0
        voiced_sec = voiced_frames * frame_len / self.sample_rate
        self.silence_detector.reset()
        return pause_mean, voiced_sec
