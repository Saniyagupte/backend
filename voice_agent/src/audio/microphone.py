"""Microphone recording with sounddevice and silence detection."""

import numpy as np
import sounddevice as sd
from typing import Optional, Tuple
from audio_buffer import AudioBuffer
from silence_detector import SilenceDetector


class MicrophoneRecorder:
    """Records audio from microphone with silence detection."""

    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        block_duration_ms: int = 20,
        rms_threshold: float = 0.02,
    ):
        """
        Initialize microphone recorder.

        Args:
            sample_rate: Sample rate in Hz (default 16000)
            channels: Number of audio channels, 1 for mono (default 1)
            block_duration_ms: Duration of each recording block in milliseconds (default 20)
            rms_threshold: RMS energy threshold for silence detection (default 0.02)
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.block_duration_ms = block_duration_ms
        self.block_samples = int(sample_rate * block_duration_ms / 1000)

        # Initialize components
        self.audio_buffer = AudioBuffer(sample_rate=sample_rate)
        self.silence_detector = SilenceDetector(
            sample_rate=sample_rate,
            rms_threshold=rms_threshold,
            frame_duration_ms=block_duration_ms,
        )

        # Recording state
        self.is_recording = False
        self.dtype = np.float32

    def _audio_callback(self, indata: np.ndarray, frames: int, time_info, status) -> None:
        """
        Callback function for audio stream.

        Args:
            indata: Audio data from stream
            frames: Number of frames
            time_info: Time information
            status: Stream status
        """
        if status:
            print(f"Audio stream status: {status}")

        # Process frame for silence detection
        audio_frame = indata[:, 0] if self.channels == 1 else indata

        # Normalize audio to [-1.0, 1.0] range if needed
        if np.max(np.abs(audio_frame)) > 1.0:
            audio_frame = audio_frame / np.max(np.abs(audio_frame))

        is_silent, should_stop, rms = self.silence_detector.process_frame(audio_frame)

        # Add to buffer
        self.audio_buffer.add_frame(audio_frame)

        # Stop recording if silence threshold reached
        if should_stop:
            self.is_recording = False

    def record(
        self,
        device: Optional[int] = None,
        verbose: bool = False,
    ) -> Optional[np.ndarray]:
        """
        Record audio from microphone until silence is detected.

        Records continuously and stops when silence lasts more than 1 second.

        Args:
            device: Microphone device index (default None for default device)
            verbose: Print silence detection information (default False)

        Returns:
            Recorded audio as numpy array, or None if recording failed
        """
        self.audio_buffer.clear()
        self.silence_detector.reset()
        self.is_recording = True

        try:
            if verbose:
                print(f"Starting recording from device {device or 'default'}...")
                print(f"Sample rate: {self.sample_rate} Hz, Mono: {self.channels == 1}")
                print("Recording... (will stop after 1 second of silence)")

            # Create and start audio stream
            with sd.InputStream(
                device=device,
                samplerate=self.sample_rate,
                channels=self.channels,
                blocksize=self.block_samples,
                dtype=self.dtype,
                callback=self._audio_callback,
            ):
                # Keep stream running until silence detected
                while self.is_recording:
                    sd.sleep(10)  # Sleep for 10ms between checks

            # Get recorded audio
            audio_data = self.audio_buffer.get_audio()

            if audio_data is not None and len(audio_data) > 0:
                if verbose:
                    duration = len(audio_data) / self.sample_rate
                    print(f"Recording stopped. Duration: {duration:.2f}s, Samples: {len(audio_data)}")
                return audio_data
            else:
                if verbose:
                    print("No audio data recorded")
                return None

        except Exception as e:
            print(f"Error during recording: {e}")
            self.is_recording = False
            return None

    def list_devices(self) -> None:
        """Print available audio devices."""
        print(sd.query_devices())

    def set_rms_threshold(self, threshold: float) -> None:
        """
        Set RMS threshold for silence detection.

        Args:
            threshold: New RMS threshold value
        """
        self.silence_detector.set_threshold(threshold)

    def get_recording_state(self) -> dict:
        """
        Get current recording state information.

        Returns:
            Dictionary with recording state details
        """
        return {
            "is_recording": self.is_recording,
            "buffer_duration": self.audio_buffer.get_duration(),
            "buffer_frames": len(self.audio_buffer),
            "silence_duration": self.silence_detector.get_silence_duration(),
            "current_rms_threshold": self.silence_detector.rms_threshold,
        }
