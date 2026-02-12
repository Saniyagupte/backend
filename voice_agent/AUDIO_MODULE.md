# Audio Module

Location: `src/audio/`

Overview
--------
The audio module contains small utilities and simple recorders used by the VoiceAgent:

- `silence_detector.py`: `SilenceDetector` class that detects silent frames using RMS energy and helps segment audio into voiced and silent regions.
- `microphone.py`, `trigger_recorder_simple.py`, `triggered_recorder.py`, `record_voice_interactive.py`: small scripts to record audio from a microphone and save WAV files suitable for processing.

Key component: `SilenceDetector`
--------------------------------
API summary:

- `SilenceDetector(sample_rate=16000, rms_threshold=0.02, frame_duration_ms=20)`
- `process_frame(audio_frame)` -> `(is_silent: bool, should_stop: bool, rms: float)`
- `calculate_rms(audio_frame)` -> `float`
- `reset()`

Usage example (programmatic):

```python
from audio.silence_detector import SilenceDetector
import soundfile as sf

audio, sr = sf.read('test_recording.wav')
detector = SilenceDetector(sample_rate=sr)
frame_samples = detector.frame_samples

for i in range(0, len(audio), frame_samples):
    frame = audio[i:i+frame_samples]
    is_silent, should_stop, rms = detector.process_frame(frame)
    # handle voiced/silent logic
```

Recorders
---------
Use the scripts under `src/audio/` to capture audio from a microphone. They save WAV files in the project — those files can be consumed by the STT/SST modules.

Tips
----
- Use 16 kHz mono for best compatibility with Vosk and to match the project's expectations.
- Tune `rms_threshold` in `SilenceDetector` if you have noisy environment.
