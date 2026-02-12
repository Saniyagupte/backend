"""Interactive terminal script for triggered recording with RMS monitoring."""

import sys
import numpy as np
import threading
import time
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from audio.triggered_recorder import TriggeredMicrophoneRecorder
import soundfile as sf


class RecordingMonitor:
    """Monitors and displays RMS energy during recording."""

    def __init__(self):
        """Initialize monitor."""
        self.rms_values = []
        self.is_silent_count = 0
        self.current_rms = 0.0
        self.lock = threading.Lock()

    def callback(self, rms: float, is_silent: bool, should_stop: bool) -> None:
        """
        RMS monitoring callback.

        Args:
            rms: Current RMS energy value
            is_silent: Whether current frame is silent
            should_stop: Whether recording should stop
        """
        with self.lock:
            self.current_rms = rms
            self.rms_values.append(rms)

            if is_silent:
                self.is_silent_count += 1
            else:
                self.is_silent_count = 0

            # Print real-time RMS visualization
            bar_length = 40
            filled = int(bar_length * min(rms / 0.15, 1.0))
            bar = "█" * filled + "░" * (bar_length - filled)

            silence_indicator = "🔇 SILENCE" if is_silent else "🔊 SOUND"
            stop_indicator = "⏹ STOPPING" if should_stop else ""

            print(
                f"\r[{bar}] RMS: {rms:.4f} | {silence_indicator} {stop_indicator}",
                end="",
                flush=True,
            )

    def get_stats(self) -> dict:
        """Get recording statistics."""
        if not self.rms_values:
            return {"min": 0, "max": 0, "mean": 0, "peak": 0}

        values = np.array(self.rms_values)
        return {
            "min": float(np.min(values)),
            "max": float(np.max(values)),
            "mean": float(np.mean(values)),
            "peak": float(np.max(values)),
        }


def run_triggered_recording(
    rms_threshold: float = 0.02,
    device: int = None,
) -> tuple:
    """
    Run interactive triggered recording with RMS monitoring.

    Args:
        rms_threshold: RMS threshold for silence detection
        device: Audio device index (None for default)

    Returns:
        Tuple of (audio_data, monitor_stats)
    """
    print("\n" + "=" * 70)
    print("TRIGGERED MICROPHONE RECORDER - INTERACTIVE MODE")
    print("=" * 70)
    print(f"Sample Rate: 16000 Hz")
    print(f"Channels: Mono (1)")
    print(f"RMS Silence Threshold: {rms_threshold}")
    print("=" * 70)

    # Create recorder
    recorder = TriggeredMicrophoneRecorder(
        sample_rate=16000,
        channels=1,
        rms_threshold=rms_threshold,
    )

    # Create monitor for RMS tracking
    monitor = RecordingMonitor()
    recorder.set_rms_callback(monitor.callback)

    print("\n[STEP 1] Opening microphone stream...")
    print("Press ENTER to start recording when ready")
    print("Recording will stop automatically after 1 second of silence\n")

    # Start recording in main thread with user trigger
    try:
        # Create stream
        import sounddevice as sd

        print("[STEP 2] Microphone ready. Listening for trigger...")

        with sd.InputStream(
            device=device,
            samplerate=recorder.sample_rate,
            channels=recorder.channels,
            blocksize=recorder.block_samples,
            dtype=recorder.dtype,
            callback=recorder._audio_callback,
        ):
            recorder.start_listening()

            # Wait for user trigger
            print("\n>>> Press ENTER to START RECORDING <<<")
            input()

            recorder.trigger_recording()

            print("Speak now... (will stop after 1 second of silence)")

            # Keep stream running while recording
            while recorder.is_recording:
                sd.sleep(10)

            recorder.stop_listening()

        # Get recorded audio
        audio_data = recorder.stop_recording()

        if audio_data is not None and len(audio_data) > 0:
            duration = len(audio_data) / 16000
            stats = monitor.get_stats()

            print("\n\n" + "=" * 70)
            print("RECORDING COMPLETE")
            print("=" * 70)
            print(f"Duration: {duration:.2f} seconds")
            print(f"Samples: {len(audio_data)}")
            print(f"RMS Statistics:")
            print(f"  Min RMS: {stats['min']:.4f}")
            print(f"  Max RMS: {stats['max']:.4f}")
            print(f"  Mean RMS: {stats['mean']:.4f}")
            print(f"  Peak RMS: {stats['peak']:.4f}")
            print("=" * 70)

            return audio_data, stats
        else:
            print("\nNo audio recorded")
            return None, {}

    except KeyboardInterrupt:
        print("\n\nRecording cancelled by user")
        return None, {}
    except Exception as e:
        print(f"\nError: {e}")
        return None, {}


def save_recording(audio_data: np.ndarray, filename: str = "recording.wav") -> None:
    """
    Save recording to file.

    Args:
        audio_data: Audio samples
        filename: Output filename (in output/ directory)
    """
    if audio_data is None or len(audio_data) == 0:
        print("No audio to save")
        return

    output_dir = Path(__file__).parent.parent.parent / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename

    try:
        sf.write(str(output_path), audio_data, 16000, subtype="PCM_16")
        print(f"\n✓ Saved to: {output_path}")
    except Exception as e:
        print(f"Error saving file: {e}")


def list_devices() -> None:
    """List available audio devices."""
    import sounddevice as sd

    print("\n" + "=" * 70)
    print("AVAILABLE AUDIO DEVICES")
    print("=" * 70)
    print(sd.query_devices())
    print("=" * 70)


def main():
    """Main interactive recording loop."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Triggered microphone recorder with RMS monitoring"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.02,
        help="RMS threshold for silence detection (default 0.02)",
    )
    parser.add_argument(
        "--device",
        type=int,
        default=None,
        help="Audio device index (default: system default)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="recording.wav",
        help="Output filename (default: recording.wav)",
    )
    parser.add_argument(
        "--list-devices",
        action="store_true",
        help="List available audio devices and exit",
    )

    args = parser.parse_args()

    if args.list_devices:
        list_devices()
        return

    # Run recording
    audio, stats = run_triggered_recording(
        rms_threshold=args.threshold,
        device=args.device,
    )

    # Save if recording succeeded
    if audio is not None:
        save_recording(audio, args.output)

        # Offer to play back
        try:
            print("\nDo you want to play back the recording? (y/n) ", end="")
            if input().lower() == "y":
                import sounddevice as sd

                print("Playing back...")
                sd.play(audio, 16000)
                sd.wait()
                print("Playback finished")
        except Exception as e:
            print(f"Playback error: {e}")


if __name__ == "__main__":
    main()
