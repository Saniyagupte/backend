"""Audio buffer for storing recorded audio frames."""

import numpy as np
from typing import Optional


class AudioBuffer:
    """Manages audio frame buffering and retrieval."""

    def __init__(self, sample_rate: int = 16000, dtype: np.dtype = np.float32):
        """
        Initialize audio buffer.

        Args:
            sample_rate: Sample rate in Hz (default 16000)
            dtype: Data type for audio samples (default float32)
        """
        self.sample_rate = sample_rate
        self.dtype = dtype
        self.frames = []
        self.total_samples = 0

    def add_frame(self, frame: np.ndarray) -> None:
        """
        Add an audio frame to the buffer.

        Args:
            frame: Audio frame as numpy array
        """
        if frame.size > 0:
            self.frames.append(frame.astype(self.dtype))
            self.total_samples += len(frame)

    def get_audio(self) -> Optional[np.ndarray]:
        """
        Get concatenated audio from all buffered frames.

        Returns:
            Concatenated audio as numpy array, or None if buffer is empty
        """
        if not self.frames:
            return None
        return np.concatenate(self.frames, axis=0)

    def clear(self) -> None:
        """Clear all buffered frames."""
        self.frames = []
        self.total_samples = 0

    def get_duration(self) -> float:
        """
        Get duration of buffered audio in seconds.

        Returns:
            Duration in seconds
        """
        return self.total_samples / self.sample_rate if self.sample_rate > 0 else 0.0

    def __len__(self) -> int:
        """Get number of buffered frames."""
        return len(self.frames)

    def __bool__(self) -> bool:
        """Check if buffer has any frames."""
        return len(self.frames) > 0
