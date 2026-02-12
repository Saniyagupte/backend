"""
Simple trigger-based voice recorder with RMS silence detection.
Records 16kHz mono audio. Saves as valid PCM 16-bit WAV files.
"""

import numpy as np
import sounddevice as sd
import soundfile as sf
from pathlib import Path


class TriggerRecorder:
    """Records audio when trigger() is called. Stops after 1 second of silence."""

    def __init__(self, sample_rate=16000, rms_threshold=0.02):
        """
        Initialize recorder.
        
        Args:
            sample_rate: 16000 Hz (fixed for speech)
            rms_threshold: Silence threshold (0.02 is good default)
        """
        self.sample_rate = sample_rate
        self.rms_threshold = rms_threshold
        self.block_size = int(sample_rate * 0.02)  # 20ms blocks
        self.silence_frames = 0
        self.max_silence_frames = int(1.0 * sample_rate / self.block_size)  # 1 second
        
        self.recording = False
        self.listening = False
        self.audio_data = []

    def _audio_callback(self, indata, frames, time_info, status):
        """Process incoming audio."""
        if status:
            print(f"Audio error: {status}")
        
        if not self.listening:
            return
        
        frame = indata[:, 0]  # Mono
        
        # Calculate RMS
        rms = np.sqrt(np.mean(np.square(frame)))
        
        # Silence detection
        if rms < self.rms_threshold:
            self.silence_frames += 1
        else:
            self.silence_frames = 0
        
        # Record while triggered
        if self.recording:
            self.audio_data.append(frame.copy())
        
        # Stop if silence threshold reached
        if self.silence_frames >= self.max_silence_frames:
            self.recording = False

    def trigger(self):
        """Start recording."""
        self.audio_data = []
        self.silence_frames = 0
        self.recording = True
        print("Recording triggered... speak now")

    def record_until_silence(self, device=None):
        """
        Open stream, wait for trigger, record until silence.
        
        Args:
            device: Audio device index (None = default)
            
        Returns:
            Audio as numpy array (float32), 16kHz mono
        """
        self.listening = True
        self.audio_data = []
        
        try:
            with sd.InputStream(
                device=device,
                samplerate=self.sample_rate,
                channels=1,
                blocksize=self.block_size,
                dtype=np.float32,
                callback=self._audio_callback
            ):
                print("Microphone open. Press ENTER to start recording:")
                input()
                self.trigger()
                
                # Wait for recording to finish
                while self.recording:
                    sd.sleep(10)
                
                self.listening = False
        
        except Exception as e:
            print(f"Error: {e}")
            return None
        
        # Concatenate and return
        if self.audio_data:
            return np.concatenate(self.audio_data, axis=0).astype(np.float32)
        return None

    def save_wav(self, audio, filename="recording.wav"):
        """
        Save audio as valid PCM 16-bit WAV file.
        
        Args:
            audio: numpy array (float32, -1.0 to 1.0)
            filename: output WAV filename
        """
        # Ensure output directory exists
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        
        # Convert float32 to int16
        audio_int16 = np.clip(audio * 32767, -32768, 32767).astype(np.int16)
        
        # Write with soundfile (ensures correct RIFF header)
        sf.write(filename, audio_int16, self.sample_rate, subtype='PCM_16')
        print(f"✓ Saved: {filename}")


# ============================================================================
# TEST SECTION - Run this to test recording
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("TRIGGER RECORDER TEST")
    print("=" * 70)
    
    # Create recorder
    recorder = TriggerRecorder(sample_rate=16000, rms_threshold=0.02)
    
    # Record
    print("\n[1] Recording audio...")
    audio = recorder.record_until_silence()
    
    if audio is None or len(audio) == 0:
        print("No audio recorded")
    else:
        # Save as WAV
        print(f"\n[2] Saving to test_recording.wav...")
        output_file = "test_recording.wav"
        recorder.save_wav(audio, output_file)
        
        # Verify by loading
        print(f"\n[3] Verifying saved file...")
        loaded_audio, sr = sf.read(output_file, dtype='int16')
        
        print(f"    Sample rate: {sr} Hz")
        print(f"    Data type: {loaded_audio.dtype}")
        print(f"    Shape: {loaded_audio.shape}")
        print(f"    Duration: {loaded_audio.shape[0] / sr:.2f} seconds")
        
        print(f"\n✓ Success! File is valid PCM 16-bit WAV")
        print(f"\n[4] Manual test:")
        print(f"    Open '{output_file}' in:")
        print(f"    • Windows Media Player")
        print(f"    • VLC media player")
        print(f"    • Any audio player")
        print(f"\nFile location: {Path(output_file).absolute()}")
        
        print("\n" + "=" * 70)
