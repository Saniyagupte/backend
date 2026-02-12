"""Triggered microphone recorder with RMS energy monitoring."""

import numpy as np
import sounddevice as sd
from typing import Optional, Callable
from .audio_buffer import AudioBuffer
from .silence_detector import SilenceDetector


class TriggeredMicrophoneRecorder:
    """Records audio from microphone triggered by a call, with RMS monitoring."""

    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        block_duration_ms: int = 20,
        rms_threshold: float = 0.02,
    ):
        """
        Initialize triggered recorder.

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
        self.is_listening = False
        self.dtype = np.float32

        # Callbacks for RMS monitoring
        self.rms_callback: Optional[Callable[[float, bool, bool], None]] = None

    def set_rms_callback(self, callback: Callable[[float, bool, bool], None]) -> None:
        """
        Set callback function for RMS monitoring.

        Callback signature: callback(rms_value: float, is_silent: bool, should_stop: bool)

        Args:
            callback: Function to call with (rms, is_silent, should_stop) for each frame
        """
        self.rms_callback = callback

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

        # Only process if listening
        if not self.is_listening:
            return

        # Process frame for silence detection
        audio_frame = indata[:, 0] if self.channels == 1 else indata

        # Normalize audio to [-1.0, 1.0] range if needed
        if np.max(np.abs(audio_frame)) > 1.0:
            audio_frame = audio_frame / np.max(np.abs(audio_frame))

        is_silent, should_stop, rms = self.silence_detector.process_frame(audio_frame)

        # Call RMS monitoring callback if set
        if self.rms_callback:
            self.rms_callback(rms, is_silent, should_stop)

        # Add to buffer only if we're recording
        if self.is_recording:
            self.audio_buffer.add_frame(audio_frame)

        # Stop recording if silence threshold reached
        if should_stop:
            self.is_recording = False

    def start_listening(self) -> None:
        """Start audio stream (listening mode, not recording yet)."""
        self.is_listening = True
        print("Microphone listening started (press Ctrl+C to stop)")

    def stop_listening(self) -> None:
        """Stop audio stream."""
        self.is_listening = False

    def trigger_recording(self) -> None:
        """Trigger the start of actual recording."""
        if not self.is_listening:
            print("ERROR: Must call start_listening() first")
            return

        self.audio_buffer.clear()
        self.silence_detector.reset()
        self.is_recording = True
        print("\n>>> RECORDING STARTED <<<")

    def stop_recording(self) -> Optional[np.ndarray]:
        """
        Stop recording and return audio buffer.

        Returns:
            Recorded audio as numpy array, or None if nothing recorded
        """
        self.is_recording = False
        audio_data = self.audio_buffer.get_audio()
        return audio_data

    def record(
        self,
        device: Optional[int] = None,
        verbose: bool = True,
    ) -> Optional[np.ndarray]:
        """
        Record audio from microphone with trigger-based control.

        Full lifecycle:
        1. Opens audio stream (listening)
        2. Waits for trigger to start recording
        3. Records until silence detected
        4. Closes stream and returns audio

        Args:
            device: Microphone device index (default None for default device)
            verbose: Print status messages (default True)

        Returns:
            Recorded audio as numpy array, or None if recording failed
        """
        try:
            # Create and start audio stream
            with sd.InputStream(
                device=device,
                samplerate=self.sample_rate,
                channels=self.channels,
                blocksize=self.block_samples,
                dtype=self.dtype,
                callback=self._audio_callback,
            ):
                # Start listening
                self.start_listening()

                try:
                    # Wait for recording to complete
                    while self.is_listening and not self.is_recording:
                        sd.sleep(10)

                    # Keep stream running while recording
                    while self.is_listening and self.is_recording:
                        sd.sleep(10)

                except KeyboardInterrupt:
                    print("\n\nRecording interrupted by user")
                finally:
                    self.stop_listening()

            # Get recorded audio
            audio_data = self.audio_buffer.get_audio()

            if audio_data is not None and len(audio_data) > 0:
                if verbose:
                    duration = len(audio_data) / self.sample_rate
                    print(f"\n✓ Recording saved: {duration:.2f}s, {len(audio_data)} samples")
                return audio_data
            else:
                if verbose:
                    print("No audio recorded")
                return None

        except Exception as e:
            print(f"Error during recording: {e}")
            self.is_listening = False
            self.is_recording = False
            return None

    def get_recording_state(self) -> dict:
        """
        Get current recording state.

        Returns:
            Dictionary with state information
        """
        return {
            "is_listening": self.is_listening,
            "is_recording": self.is_recording,
            "buffer_duration": self.audio_buffer.get_duration(),
            "buffer_samples": self.audio_buffer.total_samples,
            "silence_duration": self.silence_detector.get_silence_duration(),
            "rms_threshold": self.silence_detector.rms_threshold,
        }

    def set_rms_threshold(self, threshold: float) -> None:
        """
        Set RMS threshold for silence detection.

        Args:
            threshold: New RMS threshold value
        """
        self.silence_detector.set_threshold(threshold)

    def list_devices(self) -> None:
        """Print available audio devices."""
        print(sd.query_devices())
