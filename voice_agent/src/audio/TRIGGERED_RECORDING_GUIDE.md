# Triggered Microphone Recording Module

This module provides **on-demand voice recording** with **live RMS energy monitoring**. Start recording only when you explicitly trigger it, and automatically stop after 1+ second of silence.

## Features

✅ **Trigger-based recording** - Start recording only when you call trigger function  
✅ **16kHz mono audio** - Optimized for speech processing  
✅ **Live RMS monitoring** - See audio energy in real-time with visual bar  
✅ **Automatic silence detection** - Stops after 1+ second of silence  
✅ **Interactive terminal UI** - Clear feedback during recording  
✅ **Audio file saving** - Save to WAV format automatically  
✅ **Playback support** - Listen to recording immediately after  

## Module Files

### Core Module
- **`triggered_recorder.py`** - Main `TriggeredMicrophoneRecorder` class with trigger-based control and RMS callbacks

### Interactive Tool
- **`record_voice_interactive.py`** - User-friendly terminal application with real-time RMS visualization

## Installation

### 1. Install Dependencies
```bash
pip install sounddevice numpy soundfile
```

### 2. Verify Microphone
```bash
python src/audio/record_voice_interactive.py --list-devices
```
Look for devices marked with "in" (input devices). Note the device ID.

## Quick Start (Run Recording)

### Basic Usage - Default Microphone
```bash
python src/audio/record_voice_interactive.py
```

When you see:
```
>>> Press ENTER to START RECORDING <<<
```
Press ENTER, then speak. Recording stops automatically after 1 second of silence.

### With Specific Microphone Device
```bash
python src/audio/record_voice_interactive.py --device 1
```
Replace `1` with your microphone device ID (from `--list-devices`).

### Custom Output Filename
```bash
python src/audio/record_voice_interactive.py --output my_voice.wav
```

### Adjust Silence Sensitivity
```bash
python src/audio/record_voice_interactive.py --threshold 0.015
```
- Lower threshold (0.01-0.015): More sensitive, stops sooner
- Higher threshold (0.03-0.05): Less sensitive, tolerates more noise

### List All Devices
```bash
python src/audio/record_voice_interactive.py --list-devices
```

## How It Works

### Recording Flow
```
1. Opens microphone stream (listening mode)
2. Waits for user to press ENTER
3. Starts recording and displays live RMS energy bar
4. Monitors for 1+ second of silence
5. Automatically stops recording
6. Saves audio to file
7. Offers to play back recording
```

### RMS Energy Display
```
[████████░░░░░░░░░░░░░░░░░░░░░░░░] RMS: 0.0542 | 🔊 SOUND
```

- **Bar length**: Visual representation of audio energy
- **RMS value**: Exact energy reading (higher = louder)
- **Status**: Shows if currently silent or detecting sound
- **Stopping indicator**: Shows when silence threshold reached

### Silence Detection Algorithm
1. Measures RMS energy of each 20ms audio block
2. Compares against threshold (default 0.02)
3. If frame is silent, increments silence counter
4. After 1 second of silence, stops recording

## Python API

### Using the Module Programmatically

```python
from src.audio.triggered_recorder import TriggeredMicrophoneRecorder
import sounddevice as sd

# Create recorder
recorder = TriggeredMicrophoneRecorder(
    sample_rate=16000,
    channels=1,
    rms_threshold=0.02
)

# Optional: Add RMS monitoring callback
def on_rms(rms: float, is_silent: bool, should_stop: bool):
    print(f"RMS: {rms:.4f}, Silent: {is_silent}, Stop: {should_stop}")

recorder.set_rms_callback(on_rms)

# Open stream and listen
with sd.InputStream(
    samplerate=16000,
    channels=1,
    blocksize=320,
    callback=recorder._audio_callback
):
    # Start listening
    recorder.start_listening()
    
    # Wait for user to trigger
    print("Press ENTER to start recording")
    input()
    
    # Trigger recording
    recorder.trigger_recording()
    print("Recording... (speak now)")
    
    # Wait for silence to stop recording
    while recorder.is_recording:
        sd.sleep(10)
    
    # Stop listening
    recorder.stop_listening()

# Get recorded audio
audio = recorder.stop_recording()

# Save
import soundfile as sf
sf.write("output.wav", audio, 16000)
```

## Example Usage Scenarios

### Scenario 1: Quick Voice Note
```bash
python src/audio/record_voice_interactive.py --output voice_note_1.wav
```
Press ENTER → Speak → Auto-stops → Saved to `output/voice_note_1.wav`

### Scenario 2: High-Sensitivity Recording (for quiet environments)
```bash
python src/audio/record_voice_interactive.py --threshold 0.01 --output quiet_room.wav
```
Stops sooner on quiet pauses.

### Scenario 3: Low-Sensitivity Recording (for noisy environments)
```bash
python src/audio/record_voice_interactive.py --threshold 0.05 --output noisy_room.wav
```
Tolerates more background noise before stopping.

### Scenario 4: Using Non-Default Microphone
```bash
python src/audio/record_voice_interactive.py --device 13 --output external_mic.wav
```
Replace `13` with your microphone device ID.

## Terminal Output Examples

### Successful Recording
```
======================================================================
TRIGGERED MICROPHONE RECORDER - INTERACTIVE MODE
======================================================================
Sample Rate: 16000 Hz
Channels: Mono (1)
RMS Silence Threshold: 0.02
======================================================================

[STEP 1] Opening microphone stream...
Press ENTER to start recording when ready
Recording will stop automatically after 1 second of silence

[STEP 2] Microphone ready. Listening for trigger...

>>> Press ENTER to START RECORDING <<<

[STEP 1] RECORDING STARTED <<<
Speak now... (will stop after 1 second of silence)

[████████████░░░░░░░░░░░░░░░░░░░░░░] RMS: 0.1245 | 🔊 SOUND

======================================================================
RECORDING COMPLETE
======================================================================
Duration: 2.45 seconds
Samples: 39200
RMS Statistics:
  Min RMS: 0.0015
  Max RMS: 0.1856
  Mean RMS: 0.0487
  Peak RMS: 0.1856
======================================================================

✓ Saved to: E:\7th sem\Project\VoiceAgent\output\recording.wav

Do you want to play back the recording? (y/n) y
Playing back...
Playback finished
```

## Configuration Reference

### RMS Threshold Tuning

| Threshold | Behavior | Best For |
|-----------|----------|----------|
| 0.01 | Very sensitive | Quiet environments, short pauses |
| 0.015 | More sensitive | Normal rooms |
| 0.02 (default) | Balanced | Most environments |
| 0.03 | Less sensitive | Noisy environments |
| 0.05 | Very insensitive | Very noisy places |

### Device Selection

Get device ID:
```bash
python src/audio/record_voice_interactive.py --list-devices
```

Look for lines with "in" (input):
```
   1 Microphone Array (AMD Audio Device), MME (2 in, 0 out)
   9 Microphone Array (AMD Audio Device), Windows WASAPI (2 in, 0 out)
  13 Microphone (Realtek HD Audio Mic input), Windows WDM-KS (2 in, 0 out)
```

Use any of these device IDs: `--device 1` or `--device 9` or `--device 13`

## Troubleshooting

### "No audio recorded"
1. Check microphone is connected and working
2. Verify with `--list-devices` and ensure `in` device exists
3. Increase RMS threshold: `--threshold 0.03`
4. Make sure you pressed ENTER to trigger recording

### "ModuleNotFoundError: No module named 'sounddevice'"
```bash
pip install sounddevice
```

### Recording stops too quickly
Increase RMS threshold to be less sensitive:
```bash
python src/audio/record_voice_interactive.py --threshold 0.03
```

### Recording doesn't stop
Decrease RMS threshold to be more sensitive:
```bash
python src/audio/record_voice_interactive.py --threshold 0.01
```

### Wrong microphone is being used
1. List devices: `python src/audio/record_voice_interactive.py --list-devices`
2. Note the correct device ID
3. Use it: `python src/audio/record_voice_interactive.py --device 13`

### Audio playback not working
Some systems may need additional audio libraries. Recording will still work even if playback fails.

## Output Directory

Recordings are saved to:
```
E:\7th sem\Project\VoiceAgent\output\
```

All `.wav` files can be opened with any audio player.

## Advanced: Monitoring RMS in Real-Time

The module provides callback support for custom RMS monitoring:

```python
def my_rms_monitor(rms: float, is_silent: bool, should_stop: bool):
    if should_stop:
        print("Silence detected, stopping...")
    else:
        print(f"RMS Energy: {rms:.4f}")

recorder.set_rms_callback(my_rms_monitor)
```

## File Locations

```
src/audio/
├── triggered_recorder.py          ← Core module
├── record_voice_interactive.py    ← Interactive tool (RUN THIS)
├── audio_buffer.py                ← Audio buffering
├── silence_detector.py            ← Silence detection
└── microphone.py                  ← Original recorder
```

## Integration with VoiceAgent

For STT processing after recording:

```python
from src.audio.triggered_recorder import TriggeredMicrophoneRecorder
from src.voice_agent.stt_vosk import STTVosk

# Record audio
recorder = TriggeredMicrophoneRecorder()
audio = recorder.record()

# Transcribe
if audio is not None:
    stt = STTVosk()
    text = stt.transcribe(audio)
    print(f"You said: {text}")
```

## Performance Notes

- **Recording latency**: ~20ms block processing
- **Silence detection**: Real-time, low CPU
- **Memory**: ~1MB per minute of audio
- **File saving**: < 1 second for 5-minute recording

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| Microphone not found | Run `--list-devices` and use correct device ID |
| Audio too quiet | Lower RMS threshold |
| Recording stops too soon | Increase RMS threshold |
| File not saving | Check `output/` directory has write permissions |
| Program hangs after ENTER | It's recording! Speak into microphone |
| Ctrl+C doesn't stop immediately | Wait for stream to close gracefully |

## Next Steps

1. ✅ Run the interactive tool: `python src/audio/record_voice_interactive.py`
2. ✅ Test with different devices: `--device <ID>`
3. ✅ Adjust silence sensitivity: `--threshold <value>`
4. ✅ Record voice notes daily to `output/` directory
5. ✅ Integrate with STT pipeline for text conversion

---

**That's it!** You now have a professional voice recording system with automatic silence detection. Start recording by simply running the command and pressing ENTER when ready.
