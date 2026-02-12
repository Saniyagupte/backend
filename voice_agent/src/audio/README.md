# Audio Recording Module

This module provides microphone recording with automatic silence detection for the VoiceAgent project.

## Components

### 1. **AudioBuffer** (`audio_buffer.py`)
Manages buffering of audio frames.

**Key Features:**
- Stores audio frames in a buffer
- Concatenates frames into single numpy array
- Tracks total samples and duration
- Clean buffer management

**Usage:**
```python
from audio_buffer import AudioBuffer

buffer = AudioBuffer(sample_rate=16000)
buffer.add_frame(audio_frame)
audio_data = buffer.get_audio()
duration = buffer.get_duration()
```

### 2. **SilenceDetector** (`silence_detector.py`)
Detects silence in audio using RMS (Root Mean Square) energy.

**Key Features:**
- Calculates RMS energy for each frame
- Compares against configurable threshold (default 0.02)
- Tracks consecutive silent frames
- Stops recording when silence exceeds 1 second
- Adjustable sensitivity

**Algorithm:**
- RMS = sqrt(mean(audio_frame²))
- If RMS < threshold → frame is silent
- If silence duration > 1 second → stop recording

**Usage:**
```python
from silence_detector import SilenceDetector

detector = SilenceDetector(sample_rate=16000, rms_threshold=0.02)
is_silent, should_stop, rms = detector.process_frame(audio_frame)
silence_duration = detector.get_silence_duration()
```

### 3. **MicrophoneRecorder** (`microphone.py`)
Main class for recording audio from microphone.

**Key Features:**
- Records 16kHz mono audio using `sounddevice`
- Continuous recording with silence detection
- Automatic stop when 1+ second of silence detected
- Real-time RMS energy calculation
- Device selection support
- Recording state tracking

**Usage:**
```python
from microphone import MicrophoneRecorder

recorder = MicrophoneRecorder(
    sample_rate=16000,
    channels=1,
    rms_threshold=0.02
)

# Record audio (blocks until silence detected)
audio = recorder.record(verbose=True)

# Save or process audio
import soundfile as sf
sf.write('output.wav', audio, 16000)
```

## Configuration

### Recording Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `sample_rate` | 16000 | Sample rate in Hz |
| `channels` | 1 | Number of channels (1=mono) |
| `block_duration_ms` | 20 | Duration of recording block |
| `rms_threshold` | 0.02 | RMS threshold for silence |

### Fine-tuning Silence Detection

**RMS Threshold:**
- Lower values (0.01-0.015): More sensitive, stops earlier
- Higher values (0.03-0.05): Less sensitive, tolerates more noise

```python
recorder = MicrophoneRecorder(rms_threshold=0.03)
# or adjust after creation
recorder.set_rms_threshold(0.025)
```

## Examples

### Basic Recording
```python
recorder = MicrophoneRecorder()
audio = recorder.record(verbose=True)
```

### Custom Configuration
```python
recorder = MicrophoneRecorder(
    sample_rate=16000,
    rms_threshold=0.025,  # Adjusted sensitivity
    block_duration_ms=20
)
audio = recorder.record()
```

### With Device Selection
```python
# List available devices
recorder.list_devices()

# Record from specific device
audio = recorder.record(device=2)  # Device ID 2
```

### Get Recording State
```python
state = recorder.get_recording_state()
print(f"Buffer duration: {state['buffer_duration']:.2f}s")
print(f"Silence duration: {state['silence_duration']:.2f}s")
```

## Running Examples

```bash
# Basic recording example
python example_recording.py --mode basic

# Custom threshold example
python example_recording.py --mode threshold

# List available devices
python example_recording.py --mode devices
```

## Requirements

- `sounddevice` - For audio input from microphone
- `numpy` - For audio processing
- `soundfile` - For saving audio files (examples only)

Install with:
```bash
pip install sounddevice numpy soundfile
```

## Technical Details

### Audio Format
- **Sample Rate:** 16 kHz (16000 Hz)
- **Channels:** Mono (1 channel)
- **Bit Depth:** 32-bit float (internally), convertible to 16-bit PCM
- **Frame Size:** 320 samples per 20ms block (16000 * 0.02)

### Silence Detection Algorithm
1. Each audio block (20ms) is processed
2. RMS energy calculated: `RMS = sqrt(mean(samples²))`
3. Compared against threshold
4. Silent frames counted
5. If silence count × frame duration ≥ 1 second, recording stops

### Performance
- Minimal latency (20ms block processing)
- Efficient numpy-based calculations
- Non-blocking stream handling
- Low CPU usage

## Troubleshooting

### No Audio Recorded
- Check microphone is connected and working
- Test with `recorder.list_devices()`
- Increase RMS threshold if environment is quiet

### Recording Stops Too Early
- Reduce RMS threshold: `recorder.set_rms_threshold(0.015)`
- May indicate high background noise

### Recording Doesn't Stop
- Increase RMS threshold: `recorder.set_rms_threshold(0.03)`
- May indicate low noise floor

### Device Not Found
```python
# Check available devices
recorder.list_devices()
# Use correct device ID in record() call
```

## Integration with VoiceAgent

The microphone module integrates with the main VoiceAgent pipeline:

```python
from audio.microphone import MicrophoneRecorder
from voice_agent.stt_vosk import STTEngine

recorder = MicrophoneRecorder()
stt = STTEngine()

# Record audio
audio = recorder.record()

# Process with STT
if audio is not None:
    text = stt.transcribe(audio)
```

## Future Enhancements

- Adaptive threshold based on noise floor
- Multiple consecutive silence detection modes
- Audio level normalization
- Pre-emphasis filtering
- VAD (Voice Activity Detection) integration
