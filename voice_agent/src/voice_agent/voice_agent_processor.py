"""
Voice Agent Processor
----------------------

How to run:
1. Ensure a Python virtualenv with dependencies installed (see `requirements.txt`).
2. Place a 16 kHz mono WAV file (PCM 16-bit) alongside the project or use the
     provided recorder in `src/audio` to create `test_recording.wav`.
3. Run this file directly for a quick test:

     python src/voice_agent/voice_agent_processor.py

Description:
- This module converts speech audio to text (offline) using Vosk STT and
    extracts acoustic features using OpenSMILE. It integrates the project's
    `SilenceDetector` (from `src/audio/silence_detector.py`) to detect voiced
    segments, compute pauses and speech duration used for calculating
    `pause_mean` and `speech_rate`.
- Output JSON format (example):

    {
        "text": "I feel overwhelmed",
        "acoustic_features": {
            "pitch_mean": 215.4,
            "pitch_var": 47.2,
            "energy": 0.71,
            "speech_rate": 4.8,
            "pause_mean": 0.19,
            "jitter": 0.021,
            "shimmer": 0.034,
            "mfcc": [/* 13 float values */]
        }
    }

Notes:
- This module DOES NOT perform emotion detection or stress scoring.
- It uses OpenSMILE for acoustic feature extraction. Install with:

    pip install opensmile

"""

import sys
from pathlib import Path
import json
import numpy as np
import soundfile as sf
from typing import Dict, Any, List
from vosk import Model, KaldiRecognizer
import opensmile

# Ensure `src` directory is on sys.path so imports work when scripts are run directly
from pathlib import Path as _Path
_SRC = str(_Path(__file__).resolve().parents[1])
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

# Silence detector from project audio utilities (try relative then absolute)
try:
    from ..audio.silence_detector import SilenceDetector
except Exception:
    from audio.silence_detector import SilenceDetector


class VoiceAgentProcessor:
    """Process voice input: extract text and acoustic features."""

    def __init__(self, stt_model_path: str = None):
        """
        Initialize Voice Agent with STT model and OpenSMILE.

        Args:
            stt_model_path: Path to Vosk model. Auto-detects if None.
        """
        # Load Vosk STT model
        self.stt_model = self._load_stt_model(stt_model_path)
        self.sample_rate = 16000

        # Initialize OpenSMILE for acoustic features
        # Using eGeMAPS feature set (GeMAPS = Geneva Minimalistic Acoustic Parameter Set)
        self.smile = opensmile.Smile(
            feature_set=opensmile.FeatureSet.eGeMAPS,
            feature_level=opensmile.FeatureLevel.Functionals,
        )

        # Initialize silence detector for segmentation (20ms frames)
        self.silence_detector = SilenceDetector(sample_rate=self.sample_rate)

    def process_audio(self, wav_file: str) -> Dict[str, Any]:
        """
        Process audio file: extract text and acoustic features.

        Args:
            wav_file: Path to WAV file (16kHz mono, PCM 16-bit)

        Returns:
            Dictionary with text and acoustic_features in required format

        Raises:
            FileNotFoundError: If WAV file not found
            ValueError: If audio format incorrect
        """
        wav_path = Path(wav_file)
        if not wav_path.exists():
            raise FileNotFoundError(f"WAV file not found: {wav_file}")

        # Load audio from WAV file
        audio, sr = sf.read(wav_file)

        # Validate sample rate
        if sr != self.sample_rate:
            raise ValueError(f"Expected {self.sample_rate}Hz, got {sr}Hz")


        # Step 1: Extract text using Vosk STT
        text = self._extract_text(audio)

        # Use silence detector to compute pauses and voiced durations
        pause_mean, total_voiced_sec = self._analyze_silences(audio)

        # Step 2: Extract acoustic features using OpenSMILE
        acoustic_features = self._extract_acoustic_features(wav_file)

        # Insert computed pause_mean and speech_rate (words/sec)
        acoustic_features["pause_mean"] = pause_mean
        # Compute speech_rate = words / total_voiced_seconds (fallback if zero)
        words = len(text.split()) if text else 0
        if total_voiced_sec > 0 and words > 0:
            acoustic_features["speech_rate"] = words / total_voiced_sec
        else:
            # fallback to OpenSMILE value if available, else 0
            acoustic_features.setdefault("speech_rate", acoustic_features.get("speech_rate", 0.0))

        # Step 3: Construct final JSON output
        output = {"text": text, "acoustic_features": acoustic_features}

        return output

    def _load_stt_model(self, model_path: str = None) -> Model:
        """
        Load Vosk STT model.

        Args:
            model_path: Path to model directory. Auto-detects if None.

        Returns:
            Loaded Vosk Model

        Raises:
            FileNotFoundError: If model not found
        """
        if model_path is None:
            # Auto-detect model in workspace
            workspace_root = Path(__file__).parent.parent.parent
            model_path = (
                workspace_root
                / "models"
                / "vosk"
                / "vosk-model-small-en-us-0.15"
            )

        model_path = Path(model_path)
        if not model_path.exists():
            raise FileNotFoundError(
                f"Vosk model not found at: {model_path}\n"
                "Download from: https://github.com/alphacep/vosk-model-small/releases"
            )

        return Model(str(model_path))

    def _extract_text(self, audio: np.ndarray) -> str:
        """
        Extract spoken text from audio using Vosk STT.

        Args:
            audio: Audio samples as numpy array (16kHz mono)

        Returns:
            Recognized text as string (empty if no speech detected)
        """
        # Ensure audio is int16 PCM for Vosk
        if audio.dtype != np.int16:
            audio = np.clip(audio, -1.0, 1.0)
            audio = (audio * 32767).astype(np.int16)

        # Create Kaldi recognizer
        recognizer = KaldiRecognizer(self.stt_model, self.sample_rate)

        # Feed audio in chunks to improve recognition for long streams
        chunk_size = 4096
        words = []
        partial_accum = []
        last_partial = ""

        for i in range(0, len(audio), chunk_size):
            chunk = audio[i : i + chunk_size]
            try:
                accepted = recognizer.AcceptWaveform(chunk.tobytes())
                if accepted:
                    res = json.loads(recognizer.Result())
                    if "result" in res:
                        words.extend([w.get("word", "") for w in res.get("result", [])])
                else:
                    # capture partials to help when FinalResult is empty
                    pr = json.loads(recognizer.PartialResult())
                    partial_text = pr.get("partial", "").strip()
                    if partial_text and partial_text != last_partial:
                        # split and append new tokens
                        for tok in partial_text.split():
                            if tok not in partial_accum:
                                partial_accum.append(tok)
                        last_partial = partial_text
            except Exception:
                # If a chunk causes an error, continue to next
                continue

        # Finalize and collect remaining words
        try:
            final = json.loads(recognizer.FinalResult())
            if "result" in final and final["result"]:
                words.extend([w.get("word", "") for w in final["result"]])
            elif "partial" in final and not words:
                # Use partial result if no final words but partial exists
                return final.get("partial", "").strip()
        except Exception:
            pass

        # prefer final words, but fall back to accumulated partials
        if words:
            text = " ".join([w for w in words if w]).strip()
        elif partial_accum:
            text = " ".join(partial_accum).strip()
        else:
            text = ""

        # Debugging hint when empty
        if not text:
            try:
                duration = len(audio) / self.sample_rate
            except Exception:
                duration = None
            print(f"[STT DEBUG] No transcript produced. audio_len={len(audio)}, dtype={audio.dtype}, duration={duration}")

        return text

    def _analyze_silences(self, audio: np.ndarray) -> (float, float):
        """
        Analyze audio with `SilenceDetector` to compute mean pause duration
        and total voiced seconds.

        Returns:
            (pause_mean_seconds, total_voiced_seconds)
        """
        # Ensure mono numpy array
        if audio.ndim > 1:
            audio_mono = audio.mean(axis=1)
        else:
            audio_mono = audio

        frame_len = self.silence_detector.frame_samples
        num_frames = int(np.ceil(len(audio_mono) / frame_len))

        voiced_flags: List[bool] = []
        pause_durations: List[float] = []
        current_pause_frames = 0
        in_voice = False

        for i in range(num_frames):
            start = i * frame_len
            end = start + frame_len
            frame = audio_mono[start:end]
            is_silent, should_stop, _rms = self.silence_detector.process_frame(frame)

            if is_silent:
                if in_voice:
                    # we are now in a pause after voice
                    current_pause_frames += 1
                    in_voice = False
                else:
                    current_pause_frames += 1
            else:
                # voiced frame
                if not in_voice and current_pause_frames > 0:
                    # a pause that just ended (between voiced segments)
                    pause_durations.append(current_pause_frames * frame_len / self.sample_rate)
                    current_pause_frames = 0
                in_voice = True

            voiced_flags.append(not is_silent)

        # If audio ends in a pause, we may want to ignore trailing silence for pause_mean
        if len(pause_durations) == 0:
            pause_mean = 0.0
        else:
            pause_mean = float(np.mean(pause_durations))

        total_voiced_frames = sum(1 for v in voiced_flags if v)
        total_voiced_sec = total_voiced_frames * frame_len / self.sample_rate

        # Reset detector state
        self.silence_detector.reset()

        return pause_mean, total_voiced_sec

    def _extract_acoustic_features(self, wav_file: str) -> Dict[str, Any]:
        """
        Extract acoustic features from audio using OpenSMILE.

        Features extracted:
        - pitch_mean: Mean fundamental frequency (Hz)
        - pitch_var: Variance of fundamental frequency
        - energy: Energy/loudness of speech
        - speech_rate: Speed of speech
        - pause_mean: Mean duration of pauses
        - jitter: Pitch variability (frequency perturbation)
        - shimmer: Amplitude variability
        - mfcc: 13 Mel-Frequency Cepstral Coefficients

        Args:
            wav_file: Path to WAV file

        Returns:
            Dictionary with required acoustic features
        """
        # Extract all eGeMAPS features using OpenSMILE (88 functionals)
        features_df = self.smile.process_file(wav_file)

        # Initialize feature dictionary
        features = {}

        # Map required features to actual eGeMAPS column names (verified against eGeMAPS v1.0)
        feature_mapping = {
            "pitch_mean": "F0semitoneFrom27.5Hz_sma3nz_amean",
            "pitch_var": "F0semitoneFrom27.5Hz_sma3nz_stddevNorm",
            "energy": "loudness_sma3_amean",
            "speech_rate": "VoicedSegmentsPerSec",
            "pause_mean": "MeanVoicedSegmentLengthSec",
            "jitter": "jitterLocal_sma3nz_amean",
            "shimmer": "shimmerLocaldB_sma3nz_amean",
        }

        # Extract mapped features from OpenSMILE output
        for feature_name, column_name in feature_mapping.items():
            if column_name in features_df.columns:
                value = float(features_df[column_name].values[0])
                features[feature_name] = value
            else:
                # If column not found, return 0.0 (safe fallback)
                features[feature_name] = 0.0

        # Extract 13 MFCC coefficients from OpenSMILE
        mfcc_values = self._extract_mfcc(features_df)
        features["mfcc"] = mfcc_values

        return features

    def _find_feature_value(
        self, features_df, column_name: str, default: float = 0.0
    ) -> float:
        """
        Find feature value from DataFrame, with fallback to default.

        Attempts to find the column; if not found, searches for partial matches.

        Args:
            features_df: OpenSMILE features DataFrame
            column_name: Target column name
            default: Default value if not found

        Returns:
            Feature value or default
        """
        # Try exact match first
        if column_name in features_df.columns:
            return float(features_df[column_name].values[0])

        # Try partial matches (first column containing key substring)
        key = column_name.split("_")[0]
        for col in features_df.columns:
            if key in col:
                return float(features_df[col].values[0])

        return default

    def _extract_mfcc(self, features_df) -> list:
        """
        Extract 13 MFCC (Mel-Frequency Cepstral Coefficients) from features.

        Args:
            features_df: OpenSMILE features DataFrame

        Returns:
            List of 13 MFCC values
        """
        # Extract voiced MFCC coefficients (mfcc1V through mfcc4V means + their stddev)
        # These are more reliable for voice analysis
        mfcc_voiced_cols = [
            "mfcc1V_sma3nz_amean",
            "mfcc2V_sma3nz_amean",
            "mfcc3V_sma3nz_amean",
            "mfcc4V_sma3nz_amean",
            "mfcc1V_sma3nz_stddevNorm",
            "mfcc2V_sma3nz_stddevNorm",
            "mfcc3V_sma3nz_stddevNorm",
            "mfcc4V_sma3nz_stddevNorm",
        ]

        # Also get unvoiced MFCC for additional coefficients
        mfcc_unvoiced = [
            "mfcc1_sma3_amean",
            "mfcc2_sma3_amean",
            "mfcc3_sma3_amean",
            "mfcc4_sma3_amean",
        ]

        # Extract values from available columns
        mfcc_values = []
        
        # First, add voiced MFCC values
        for col in mfcc_voiced_cols:
            if col in features_df.columns:
                value = float(features_df[col].values[0])
                mfcc_values.append(value)

        # If we need more, add unvoiced MFCC
        for col in mfcc_unvoiced:
            if len(mfcc_values) < 13 and col in features_df.columns:
                value = float(features_df[col].values[0])
                mfcc_values.append(value)

        # Pad with zeros if fewer than 13 features found
        while len(mfcc_values) < 13:
            mfcc_values.append(0.0)

        return mfcc_values[:13]  # Ensure exactly 13 values


# ============================================================================
# TEST SECTION
# ============================================================================

if __name__ == "__main__":
    import sys

    print("\n" + "=" * 70)
    print("Voice Agent Processor - Test")
    print("=" * 70)

    try:
        # Initialize Voice Agent
        print("\n[1] Initializing Voice Agent...")
        agent = VoiceAgentProcessor()
        print("✓ Voice Agent initialized successfully")

        # Test with WAV file
        test_wav = "test_recording.wav"
        print(f"\n[2] Processing audio: {test_wav}")

        # Check if test file exists
        if not Path(test_wav).exists():
            print(f"✗ {test_wav} not found")
            print("\nTo generate test file, run:")
            print("  python src/audio/trigger_recorder_simple.py")
            sys.exit(1)

        # Process audio
        result = agent.process_audio(test_wav)

        # Display results
        print("✓ Processing complete\n")
        print("-" * 70)
        print("EXTRACTED TEXT:")
        print("-" * 70)
        print(f'  "{result["text"]}"')

        print("\n" + "-" * 70)
        print("ACOUSTIC FEATURES:")
        print("-" * 70)

        features = result["acoustic_features"]
        print(f"  pitch_mean:     {features['pitch_mean']:.2f} Hz")
        print(f"  pitch_var:      {features['pitch_var']:.2f}")
        print(f"  energy:         {features['energy']:.2f} dB")
        print(f"  speech_rate:    {features['speech_rate']:.2f} phonemes/sec")
        print(f"  pause_mean:     {features['pause_mean']:.3f} sec")
        print(f"  jitter:         {features['jitter']:.4f}")
        print(f"  shimmer:        {features['shimmer']:.4f}")
        print(f"  mfcc (13 vals): {[f'{v:.3f}' for v in features['mfcc'][:5]]} ...")

        print("\n" + "-" * 70)
        print("JSON OUTPUT:")
        print("-" * 70)
        print(json.dumps(result, indent=2))

        print("\n" + "=" * 70)
        print("✓ Test completed successfully")
        print("=" * 70 + "\n")

    except FileNotFoundError as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
