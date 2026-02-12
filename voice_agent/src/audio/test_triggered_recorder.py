"""Test suite for triggered recording module."""

import numpy as np
from src.audio.triggered_recorder import TriggeredMicrophoneRecorder
from src.audio.silence_detector import SilenceDetector
from src.audio.audio_buffer import AudioBuffer


def test_triggered_recorder_initialization():
    """Test that recorder initializes correctly."""
    recorder = TriggeredMicrophoneRecorder(
        sample_rate=16000,
        channels=1,
        rms_threshold=0.02,
    )

    state = recorder.get_recording_state()

    assert state["is_listening"] is False
    assert state["is_recording"] is False
    assert state["buffer_samples"] == 0
    assert state["rms_threshold"] == 0.02
    print("✓ Recorder initialization test passed")


def test_audio_buffer():
    """Test audio buffer functionality."""
    buffer = AudioBuffer(sample_rate=16000)

    # Add some frames
    frame1 = np.random.randn(320).astype(np.float32)
    frame2 = np.random.randn(320).astype(np.float32)

    buffer.add_frame(frame1)
    buffer.add_frame(frame2)

    assert len(buffer) == 2
    assert buffer.total_samples == 640
    assert buffer.get_duration() == 0.04  # 640 / 16000

    audio = buffer.get_audio()
    assert len(audio) == 640

    buffer.clear()
    assert len(buffer) == 0
    assert buffer.get_duration() == 0.0

    print("✓ Audio buffer test passed")


def test_silence_detector():
    """Test silence detection."""
    detector = SilenceDetector(sample_rate=16000, rms_threshold=0.02, frame_duration_ms=20)

    # Create silent frame (very low amplitude)
    silent_frame = np.zeros(320).astype(np.float32)

    # Create sound frame (moderate amplitude)
    sound_frame = np.random.randn(320).astype(np.float32) * 0.1

    # Test silent frame detection
    is_silent, should_stop, rms = detector.process_frame(silent_frame)
    assert is_silent is True
    assert rms < 0.02
    print(f"✓ Silent frame detected (RMS={rms:.4f})")

    # Reset and test sound frame
    detector.reset()
    is_silent, should_stop, rms = detector.process_frame(sound_frame)
    assert is_silent is False
    assert rms > 0.01
    print(f"✓ Sound frame detected (RMS={rms:.4f})")

    # Test consecutive silence frames trigger stop
    detector.reset()
    for i in range(50):  # Simulate 1 second of silence (50 frames × 20ms)
        is_silent, should_stop, rms = detector.process_frame(silent_frame)

    assert should_stop is True
    print("✓ Silence detection triggers stop after 1 second")

    print("✓ Silence detector test passed")


def test_rms_callback():
    """Test RMS callback mechanism."""
    recorder = TriggeredMicrophoneRecorder()

    # Track callback calls
    callback_data = {"calls": 0, "rms_values": []}

    def test_callback(rms: float, is_silent: bool, should_stop: bool):
        callback_data["calls"] += 1
        callback_data["rms_values"].append(rms)

    recorder.set_rms_callback(test_callback)
    assert recorder.rms_callback is not None
    print("✓ RMS callback registration test passed")


def test_set_threshold():
    """Test threshold adjustment."""
    recorder = TriggeredMicrophoneRecorder(rms_threshold=0.02)

    assert recorder.silence_detector.rms_threshold == 0.02

    recorder.set_rms_threshold(0.03)
    assert recorder.silence_detector.rms_threshold == 0.03

    print("✓ Threshold adjustment test passed")


def test_generate_synthetic_audio():
    """Test with synthetic audio (no microphone needed)."""
    import soundfile as sf

    # Generate test audio
    duration = 2.0  # seconds
    sample_rate = 16000
    t = np.arange(int(duration * sample_rate)) / sample_rate

    # Create audio: silence, tone, silence
    audio = np.zeros_like(t)
    audio[int(0.5 * sample_rate) : int(1.5 * sample_rate)] = (
        0.1 * np.sin(2 * np.pi * 440 * t[int(0.5 * sample_rate) : int(1.5 * sample_rate)])
    )

    # Test with buffer
    buffer = AudioBuffer(sample_rate=16000)
    chunk_size = 320
    for i in range(0, len(audio), chunk_size):
        chunk = audio[i : i + chunk_size]
        if len(chunk) > 0:
            buffer.add_frame(chunk)

    assert buffer.total_samples > 0
    print(f"✓ Synthetic audio test passed ({buffer.total_samples} samples)")


if __name__ == "__main__":
    print("=" * 60)
    print("TRIGGERED RECORDER TEST SUITE")
    print("=" * 60 + "\n")

    try:
        test_triggered_recorder_initialization()
        test_audio_buffer()
        test_silence_detector()
        test_rms_callback()
        test_set_threshold()
        test_generate_synthetic_audio()

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED ✓")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback

        traceback.print_exc()
        exit(1)
