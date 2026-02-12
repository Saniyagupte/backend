"""Speech-to-Text using Vosk offline speech recognition model."""

import json
import numpy as np
from pathlib import Path
from typing import Optional
from vosk import Model, KaldiRecognizer


class STTVosk:
    """Speech-to-Text engine using Vosk offline model."""

    def __init__(
        self,
        model_path: Optional[str] = None,
        sample_rate: int = 16000,
    ):
        """
        Initialize Vosk STT engine.

        Args:
            model_path: Path to Vosk model directory. If None, uses default
                       from config or workspace models directory.
            sample_rate: Sample rate of audio in Hz (default 16000)

        Raises:
            FileNotFoundError: If model not found at specified path
            RuntimeError: If Vosk model fails to load
        """
        self.sample_rate = sample_rate

        # Determine model path
        if model_path is None:
            model_path = self._find_default_model()

        model_path = Path(model_path)
        if not model_path.exists():
            raise FileNotFoundError(f"Vosk model not found at: {model_path}")

        try:
            self.model = Model(str(model_path))
        except Exception as e:
            raise RuntimeError(f"Failed to load Vosk model: {e}")

        self.recognizer = None

    def _find_default_model(self) -> str:
        """
        Find default Vosk model in workspace.

        Returns:
            Path to model directory

        Raises:
            FileNotFoundError: If no model found
        """
        # Look for model in standard project structure
        workspace_root = Path(__file__).parent.parent.parent
        model_dir = workspace_root / "models" / "vosk" / "vosk-model-small-en-us-0.15"

        if model_dir.exists():
            return str(model_dir)

        # Alternative common locations
        alt_paths = [
            Path.home() / "vosk-model-small-en-us-0.15",
            Path("/usr/share/vosk/models/vosk-model-small-en-us-0.15"),
        ]

        for alt_path in alt_paths:
            if alt_path.exists():
                return str(alt_path)

        raise FileNotFoundError(
            f"Vosk model not found. Expected at: {model_dir}\n"
            "Download from: https://github.com/alphacep/vosk-model-small/releases"
        )

    def transcribe(self, audio_buffer: np.ndarray) -> str:
        """
        Transcribe audio buffer to text using Vosk.

        Processes the entire audio buffer and returns the final recognized text.
        This is suitable for complete utterances where recording has ended.

        Args:
            audio_buffer: Audio samples as numpy array
                         Should be 16kHz mono audio in float32 or int16 format

        Returns:
            Recognized text as string (empty string if nothing recognized)

        Raises:
            ValueError: If audio buffer is empty
            RuntimeError: If transcription fails
        """
        if audio_buffer is None or len(audio_buffer) == 0:
            raise ValueError("Audio buffer is empty")

        # Convert to int16 PCM format if needed
        audio_data = self._prepare_audio(audio_buffer)

        # Create recognizer for this transcription
        self.recognizer = KaldiRecognizer(self.model, self.sample_rate)

        try:
            # Process audio data in chunks (standard Vosk chunk size is 4096 samples)
            chunk_size = 4096
            final_result = ""

            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i : i + chunk_size]

                if self.recognizer.AcceptWaveform(chunk.tobytes()):
                    # Got a final result
                    result = json.loads(self.recognizer.Result())
                    if "result" in result:
                        # Extract words from result
                        words = [item.get("word", "") for item in result.get("result", [])]
                        if words:
                            final_result = " ".join(words)

            # Get any remaining final result
            final_json = json.loads(self.recognizer.FinalResult())

            # Extract final recognized text
            if "result" in final_json and final_json["result"]:
                final_result = " ".join([item.get("word", "") for item in final_json["result"]])
            elif "partial" in final_json:
                final_result = final_json.get("partial", "")

            return final_result.strip()

        except Exception as e:
            raise RuntimeError(f"Transcription failed: {e}")

    def transcribe_stream(self, audio_buffer: np.ndarray) -> dict:
        """
        Transcribe audio and return detailed results including confidence.

        Args:
            audio_buffer: Audio samples as numpy array

        Returns:
            Dictionary with keys:
            - 'text': Final recognized text
            - 'confidence': Confidence scores if available
            - 'partial': Last partial result

        Raises:
            ValueError: If audio buffer is empty
            RuntimeError: If transcription fails
        """
        if audio_buffer is None or len(audio_buffer) == 0:
            raise ValueError("Audio buffer is empty")

        audio_data = self._prepare_audio(audio_buffer)
        self.recognizer = KaldiRecognizer(self.model, self.sample_rate)

        try:
            chunk_size = 4096
            final_result = {
                "text": "",
                "confidence": [],
                "partial": "",
            }

            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i : i + chunk_size]

                if self.recognizer.AcceptWaveform(chunk.tobytes()):
                    result = json.loads(self.recognizer.Result())
                    if "result" in result:
                        # update confidences with the latest final result
                        final_result["confidence"] = [
                            item.get("conf", 0.0) for item in result["result"]
                        ]

            # Get final result
            final_json = json.loads(self.recognizer.FinalResult())

            if "result" in final_json and final_json["result"]:
                final_result["text"] = " ".join([item.get("word", "") for item in final_json["result"]])
                final_result["confidence"] = [
                    item.get("conf", 0.0) for item in final_json["result"]
                ]
            elif "partial" in final_json:
                final_result["partial"] = final_json.get("partial", "")
                final_result["text"] = final_json.get("partial", "")

            return final_result

        except Exception as e:
            raise RuntimeError(f"Stream transcription failed: {e}")

    def _prepare_audio(self, audio_buffer: np.ndarray) -> np.ndarray:
        """
        Prepare audio buffer for Vosk processing.

        Converts float audio to int16 PCM format if needed.

        Args:
            audio_buffer: Audio samples as numpy array

        Returns:
            Audio in int16 PCM format
        """
        # If already int16, return as is
        if audio_buffer.dtype == np.int16:
            return audio_buffer

        # If float, convert to int16
        if audio_buffer.dtype in [np.float32, np.float64]:
            # Clip to [-1, 1] range
            audio_clipped = np.clip(audio_buffer, -1.0, 1.0)
            # Convert to int16 (scale by 32767)
            return (audio_clipped * 32767).astype(np.int16)

        # Otherwise, try direct conversion
        return audio_buffer.astype(np.int16)

    def set_sample_rate(self, sample_rate: int) -> None:
        """
        Set sample rate for audio processing.

        Args:
            sample_rate: Sample rate in Hz
        """
        self.sample_rate = sample_rate
        # Reset recognizer to apply new sample rate
        self.recognizer = None

    def __del__(self):
        """Cleanup resources."""
        self.recognizer = None
        self.model = None
