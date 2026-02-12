# Quick Start - Record Voice from Terminal

## One Command to Record

```bash
python src/audio/record_voice_interactive.py
```

That's it! Then:
1. **Press ENTER** when you see the prompt
2. **Speak into the microphone**
3. **Stop speaking** and stay silent for ~1 second
4. **Recording saves automatically** to `output/recording.wav`
5. **Option to playback** when asked

---

## Command Cheat Sheet

### Basic Recording
```bash
# Record with default settings
python src/audio/record_voice_interactive.py
```

### Save to Custom Filename
```bash
python src/audio/record_voice_interactive.py --output my_voice.wav
```

### List Your Microphones
```bash
python src/audio/record_voice_interactive.py --list-devices
```

### Use Specific Microphone (e.g., device 13)
```bash
python src/audio/record_voice_interactive.py --device 13
```

### Adjust Silence Sensitivity
```bash
# More sensitive (stops sooner)
python src/audio/record_voice_interactive.py --threshold 0.015

# Less sensitive (tolerates more pauses)
python src/audio/record_voice_interactive.py --threshold 0.03
```

### Combine Multiple Options
```bash
python src/audio/record_voice_interactive.py --device 13 --output voice.wav --threshold 0.02
```

---

## What Happens During Recording

```
Step 1: Microphone opens
Step 2: You press ENTER to trigger recording
Step 3: Live RMS energy bar displays:
        [████████░░░░░░░░░░░░░░░░░░░░░░░░] RMS: 0.0542 | 🔊 SOUND
Step 4: You speak
Step 5: Silent for 1+ second → Recording stops automatically
Step 6: Audio saved to output/ folder
```

---

## Troubleshooting in 30 Seconds

| Problem | Solution |
|---------|----------|
| **Can't find microphone** | Run `--list-devices` and use correct device ID |
| **Recording stops too quick** | Use `--threshold 0.03` (less sensitive) |
| **Recording won't stop** | Use `--threshold 0.01` (more sensitive) |
| **No audio heard** | Make sure microphone is plugged in and selected |
| **Need dependencies** | Run `pip install sounddevice numpy soundfile` |

---

## File Locations

- **Recordings save to:** `output/recording.wav` (or your custom filename)
- **Module code:** `src/audio/triggered_recorder.py`
- **Full guide:** `src/audio/TRIGGERED_RECORDING_GUIDE.md`

---

## Example: Record 3 Voice Notes

```bash
# Note 1
python src/audio/record_voice_interactive.py --output note_1.wav

# Note 2
python src/audio/record_voice_interactive.py --output note_2.wav

# Note 3
python src/audio/record_voice_interactive.py --output note_3.wav
```

All saved to `output/` and ready to use!

---

## Features You Get

✅ **Trigger when ready** - Press ENTER to start (not auto-start)  
✅ **Live RMS display** - See audio energy bars in real-time  
✅ **Auto-stop on silence** - Stops 1 second after you stop talking  
✅ **16kHz mono** - Perfect for speech processing  
✅ **Auto-save** - Saved as WAV file immediately  
✅ **Instant playback** - Listen right after recording  

---

## Next: Use Recorded Audio

### Option 1: Play with Vosk STT
```python
from src.audio.triggered_recorder import TriggeredMicrophoneRecorder
from src.voice_agent.stt_vosk import STTVosk

recorder = TriggeredMicrophoneRecorder()
audio = recorder.record()

stt = STTVosk()
text = stt.transcribe(audio)
print(f"You said: {text}")
```

### Option 2: Use in Vosk Example
```bash
python src/voice_agent/stt_example.py --mode simple
```

### Option 3: Process Manually
```python
import soundfile as sf
audio, sr = sf.read("output/recording.wav")
# Your processing here...
```

---

**Ready? Run this now:**
```bash
python src/audio/record_voice_interactive.py
```

That's all you need! 🎤
