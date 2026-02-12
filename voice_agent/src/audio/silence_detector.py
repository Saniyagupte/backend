"""Silence detection using RMS energy threshold."""

import numpy as np
from typing import Tuple


class SilenceDetector:
    """Detects silence in audio frames using RMS energy."""

    def __init__(
        self,
        sample_rate: int = 16000,
        rms_threshold: float = 0.02,
        frame_duration_ms: int = 20,
    ):
        """
        Initialize silence detector.

        Args:
            sample_rate: Sample rate in Hz (default 16000)
            rms_threshold: RMS energy threshold for silence detection (default 0.02)
            frame_duration_ms: Duration of each frame in milliseconds (default 20)
        """
        self.sample_rate = sample_rate
        self.rms_threshold = rms_threshold
        self.frame_duration_ms = frame_duration_ms
        self.frame_samples = int(sample_rate * frame_duration_ms / 1000)
        self.silence_frames = 0
        self.max_silence_frames = int(1.0 * sample_rate / self.frame_samples)  # 1 second

    def calculate_rms(self, audio_frame: np.ndarray) -> float:
        """
        Calculate RMS (Root Mean Square) energy of audio frame.

        Args:
            audio_frame: Audio frame as numpy array

        Returns:
            RMS value (0.0 to 1.0 for normalized audio)
        """
        if len(audio_frame) == 0:
            return 0.0
        # Calculate RMS
        rms = np.sqrt(np.mean(np.square(audio_frame)))
        return float(rms)

    def is_silent(self, audio_frame: np.ndarray) -> bool:
        """
        Check if audio frame is silent.

        Args:
            audio_frame: Audio frame as numpy array

        Returns:
            True if frame is silent, False otherwise
        """
        rms = self.calculate_rms(audio_frame)
        return rms < self.rms_threshold

    def process_frame(self, audio_frame: np.ndarray) -> Tuple[bool, bool, float]:
        """
        Process an audio frame for silence detection.

        Args:
            audio_frame: Audio frame as numpy array

        Returns:
            Tuple of (is_silent, should_stop, rms_value):
            - is_silent: True if current frame is silent
            - should_stop: True if silence duration exceeded threshold
            - rms_value: RMS energy of the frame
        """
        rms = self.calculate_rms(audio_frame)
        is_silent = rms < self.rms_threshold

        if is_silent:
            self.silence_frames += 1
        else:
            self.silence_frames = 0

        # Stop recording if silence exceeds 1 second
        should_stop = self.silence_frames >= self.max_silence_frames

        return is_silent, should_stop, rms

    def reset(self) -> None:
        """Reset silence counter."""
        self.silence_frames = 0

    def get_silence_duration(self) -> float:
        """
        Get current silence duration in seconds.

        Returns:
            Silence duration in seconds
        """
        return (self.silence_frames * self.frame_samples) / self.sample_rate

    def set_threshold(self, threshold: float) -> None:
        """
        Set new RMS threshold for silence detection.

        Args:
            threshold: New RMS threshold value
        """
        self.rms_threshold = threshold
