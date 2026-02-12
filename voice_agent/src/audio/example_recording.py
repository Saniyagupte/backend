"""Example usage of the microphone recording module with silence detection."""

import numpy as np
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

from audio.microphone import MicrophoneRecorder
import soundfile as sf


def example_basic_recording():
    """Basic example: Record audio until silence is detected."""
    print("\n=== Basic Recording Example ===")

    # Create recorder with default settings
    recorder = MicrophoneRecorder(
        sample_rate=16000,
        channels=1,
        block_duration_ms=20,
        rms_threshold=0.02,
    )

    # Record audio
    audio = recorder.record(verbose=True)

    if audio is not None:
        print(f"\nRecorded {len(audio)} samples")
        print(f"Duration: {len(audio) / 16000:.2f} seconds")
        return audio
    else:
        print("Recording failed")
        return None


def example_with_custom_threshold():
    """Example: Recording with custom RMS threshold."""
    print("\n=== Recording with Custom Threshold ===")

    recorder = MicrophoneRecorder(
        sample_rate=16000,
        channels=1,
        rms_threshold=0.03,  # Higher threshold for less sensitive silence detection
    )

    # Adjust threshold after initialization
    recorder.set_rms_threshold(0.025)
    print(f"RMS Threshold set to: {recorder.silence_detector.rms_threshold}")

    audio = recorder.record(verbose=True)
    return audio


def example_list_devices():
    """Example: List available audio devices."""
    print("\n=== Available Audio Devices ===")
    recorder = MicrophoneRecorder()
    recorder.list_devices()


def example_save_recording(audio: np.ndarray):
    """Example: Save recorded audio to file."""
    if audio is None:
        print("No audio to save")
        return

    output_path = Path(__file__).parent.parent.parent / "output" / "recording.wav"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Save audio file
        sf.write(str(output_path), audio, 16000, subtype="PCM_16")
        print(f"\nAudio saved to: {output_path}")
    except Exception as e:
        print(f"Error saving audio: {e}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Microphone recording examples")
    parser.add_argument(
        "--mode",
        choices=["basic", "threshold", "devices"],
        default="basic",
        help="Example mode to run",
    )

    args = parser.parse_args()

    try:
        if args.mode == "basic":
            audio = example_basic_recording()
            example_save_recording(audio)

        elif args.mode == "threshold":
            audio = example_with_custom_threshold()
            example_save_recording(audio)

        elif args.mode == "devices":
            example_list_devices()

    except KeyboardInterrupt:
        print("\n\nRecording interrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
