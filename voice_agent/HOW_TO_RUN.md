# Voice Agent - How to Test & Run

## 🚀 QUICK START (Choose Your Path)

### Path A: Auto-Test (Recommended - 2 minutes)
```bash
python test_voice_agent.py
```
✓ Checks all dependencies  
✓ Initializes Voice Agent  
✓ Tests with synthetic audio  
✓ Shows results  

---

### Path B: Full Test with Real Voice (5-10 minutes)
```bash
# Step 1: Record your voice
python src/audio/trigger_recorder_simple.py

# Step 2: Process with Voice Agent
python src/voice_agent/voice_agent_processor.py

# Step 3: View results
cat test_recording.wav.json  (if saved)
```

---

### Path C: Manual Integration (10-15 minutes)
```python
# Create test_integration.py
from src.voice_agent.voice_agent_processor import VoiceAgentProcessor
from src.relaxation_agent.mock_relaxation import RelaxationAgent
import json

# Initialize
voice_agent = VoiceAgentProcessor()
relaxation_agent = RelaxationAgent()

# Process voice
result = voice_agent.process_audio("test_recording.wav")

# Send to Relaxation Agent
response = relaxation_agent.process(
    text=result["text"],
    acoustic_features=result["acoustic_features"]
)

# Display results
print("=== VOICE AGENT ===")
print(json.dumps(result, indent=2))
print("\n=== RELAXATION RESPONSE ===")
print(json.dumps(response, indent=2))
```

Run it:
```bash
python test_integration.py
```

---

## 📋 DETAILED STEP-BY-STEP

### 1. INSTALLATION (First Time Only)

**Check Python version:**
```bash
python --version
# Should be 3.7+
```

**Install dependencies:**
```bash
pip install vosk numpy soundfile opensmile
```

**Verify installation:**
```bash
python -c "import vosk, opensmile, numpy, soundfile; print('✓ All packages installed')"
```

Expected output:
```
LOG (VoskAPI:ReadDataFiles():model.cc:213) Decoding params...
✓ All packages installed
```

---

### 2. DOWNLOAD VOSK MODEL (First Time Only)

Check if model exists:
```bash
dir models\vosk\vosk-model-small-en-us-0.15\
```

If not found:
1. Download: https://github.com/alphacep/vosk-model-small/releases
2. Extract to: `models/vosk/vosk-model-small-en-us-0.15/`
3. Should have: `am/`, `conf/`, `graph/`, `ivector/` folders

Verify:
```bash
dir models\vosk\vosk-model-small-en-us-0.15\am\
# Should show: final.mdl and other files
```

---

### 3. TEST VOICE AGENT (Every Time)

**Quick test (2 minutes):**
```bash
python test_voice_agent.py
```

Expected output:
```
======================================================================
Voice Agent Processor - Module Availability Check
======================================================================

Checking installed packages:
  ✓ vosk            - Speech-to-Text engine
  ✓ opensmile       - Acoustic feature extraction
  ✓ numpy           - Array operations
  ✓ soundfile       - WAV file I/O

----------------------------------------------------------------------
✓ All dependencies installed!

[1] Attempting to import Voice Agent Processor...
✓ Voice Agent Processor imported successfully

[2] Initializing Voice Agent...
✓ Voice Agent initialized

[3] Checking test audio file...
✓ test_recording.wav found

[4] Processing audio...
✓ Processing complete

----------------------------------------------------------------------
RESULTS:
----------------------------------------------------------------------

Text: (text from audio, or empty if synthetic)

Acoustic Features:
  pitch_mean:     145.23 Hz
  pitch_var:      52.40
  energy:         -12.34 dB
  speech_rate:    3.45 phonemes/sec
  pause_mean:     0.250 sec
  jitter:         0.0234
  shimmer:        0.0456
  mfcc (13 vals): ['0.123', '0.456', ...] 

======================================================================
✓ Test completed successfully
======================================================================
```

---

### 4. RECORD YOUR OWN VOICE (Optional but Recommended)

**Run recorder:**
```bash
python src/audio/trigger_recorder_simple.py
```

**Follow prompts:**
```
Microphone open. Press ENTER to start recording:
[Press ENTER]
Recording triggered... speak now
(Speak for 2-3 seconds)
(Stay silent for ~1 second to stop)
```

**Output:**
```
Sample rate: 16000 Hz
Data type: int16
Shape: (48000,)
Duration: 3.00 seconds
File: test_recording.wav ✓
```

---

### 5. PROCESS RECORDED AUDIO

**Run Voice Agent on your recording:**
```bash
python src/voice_agent/voice_agent_processor.py
```

**Expected output:**
```
======================================================================
Voice Agent Processor - Test
======================================================================

[1] Initializing Voice Agent...
✓ Voice Agent initialized successfully

[2] Processing audio: test_recording.wav
✓ Processing complete

----------------------------------------------------------------------
EXTRACTED TEXT:
----------------------------------------------------------------------
  "I feel stressed by traffic"

----------------------------------------------------------------------
ACOUSTIC FEATURES:
----------------------------------------------------------------------
  pitch_mean:     215.40 Hz
  pitch_var:      47.20
  energy:         0.71 dB
  speech_rate:    4.80 phonemes/sec
  pause_mean:     0.19 sec
  jitter:         0.021
  shimmer:        0.034
  mfcc (13 vals): ['0.123', '0.456', ...] 

----------------------------------------------------------------------
JSON OUTPUT:
----------------------------------------------------------------------
{
  "text": "I feel stressed by traffic",
  "acoustic_features": {
    "pitch_mean": 215.40,
    "pitch_var": 47.20,
    "energy": 0.71,
    ...
  }
}

======================================================================
✓ Test completed successfully
======================================================================
```

---

### 6. INTEGRATE WITH RELAXATION AGENT

**Create file: `test_pipeline.py`**
```python
from src.voice_agent.voice_agent_processor import VoiceAgentProcessor
from src.relaxation_agent.mock_relaxation import RelaxationAgent
import json

print("\n" + "="*70)
print("COMPLETE PIPELINE: Voice → Relaxation → Response")
print("="*70)

# 1. Process voice
print("\n[Step 1] Processing voice audio...")
agent = VoiceAgentProcessor()
voice_result = agent.process_audio("test_recording.wav")
print("✓ Voice processed")

# 2. Send to Relaxation Agent
print("\n[Step 2] Sending to Relaxation Agent...")
relaxation = RelaxationAgent()
response = relaxation.process(
    text=voice_result["text"],
    acoustic_features=voice_result["acoustic_features"]
)
print("✓ Response generated")

# 3. Display results
print("\n[Step 3] Results:")
print("-"*70)
print("\nText Extracted:")
print(f'  "{voice_result["text"]}"')

print("\nAcoustic Features:")
for key, val in voice_result["acoustic_features"].items():
    if key != "mfcc":
        print(f"  {key}: {val}")
    else:
        print(f"  mfcc: {len(val)} coefficients")

print("\nRelaxation Agent Response:")
print(json.dumps(response, indent=2))

print("\n" + "="*70)
print("✓ PIPELINE COMPLETE")
print("="*70 + "\n")
```

**Run it:**
```bash
python test_pipeline.py
```

---

## 🐛 TROUBLESHOOTING

### Problem 1: "No module named 'opensmile'"
```bash
pip install opensmile --upgrade
```

### Problem 2: "Vosk model not found"
```bash
# Check model exists
dir models\vosk\vosk-model-small-en-us-0.15\am\
# If not: Download and extract from GitHub
```

### Problem 3: "Empty text from audio"
- Speak louder
- Use different microphone
- Try again with fresh recording
- Audio must be actual speech (not noise)

### Problem 4: "All features are 0.0"
- This is expected for synthetic/silent audio
- Test with real speech
- Run the recorder first: `python src/audio/trigger_recorder_simple.py`

### Problem 5: "ModuleNotFoundError"
```bash
# Make sure you're in project root
cd "e:\7th sem\Project\VoiceAgent"
python test_voice_agent.py
```

---

## 📊 EXPECTED OUTPUTS

### Test 1: Dependency Check
```
✓ vosk
✓ opensmile
✓ numpy
✓ soundfile
✓ All dependencies installed!
```

### Test 2: Module Initialization
```
✓ Voice Agent Processor imported successfully
✓ Voice Agent initialized
```

### Test 3: Audio Processing
```
✓ Processing complete
Text extracted (or empty if no speech)
7 acoustic features + 13 MFCC values
```

### Test 4: JSON Output
```json
{
  "text": "extracted speech",
  "acoustic_features": {
    "pitch_mean": 215.4,
    "pitch_var": 47.2,
    "energy": 0.71,
    "speech_rate": 4.8,
    "pause_mean": 0.19,
    "jitter": 0.021,
    "shimmer": 0.034,
    "mfcc": [13 values]
  }
}
```

### Test 5: Relaxation Response
```json
{
  "stress_level": "high",
  "intervention": "breathing_exercise",
  "guidance": "Take 3 deep breaths..."
}
```

---

## ⏱️ TIME ESTIMATES

| Task | Time | Effort |
|------|------|--------|
| Install dependencies | 2-3 min | Easy |
| Download Vosk model | 5-10 min | Easy |
| Test dependencies | 1 min | Very Easy |
| Record voice | 5 min | Easy |
| Process with Voice Agent | 5-10 sec | Very Easy |
| Full pipeline test | 5 min | Easy |
| **Total (First Time)** | **20-30 min** | **Easy** |
| **Total (Repeat)** | **2-5 min** | **Very Easy** |

---

## ✅ VERIFICATION CHECKLIST

- [ ] Python 3.7+ installed
- [ ] All packages installed (pip list shows vosk, opensmile, numpy, soundfile)
- [ ] Vosk model in `models/vosk/vosk-model-small-en-us-0.15/`
- [ ] `test_voice_agent.py` shows all ✓
- [ ] Can record voice with `trigger_recorder_simple.py`
- [ ] `voice_agent_processor.py` processes audio without errors
- [ ] JSON output matches specification
- [ ] Relaxation Agent receives output correctly
- [ ] Full pipeline works end-to-end

---

## 🎯 NEXT STEPS

1. **Right Now:**
   ```bash
   python test_voice_agent.py
   ```

2. **Then:**
   ```bash
   python src/audio/trigger_recorder_simple.py
   ```

3. **Then:**
   ```bash
   python src/voice_agent/voice_agent_processor.py
   ```

4. **Finally:**
   Read `INTEGRATION_GUIDE.md` to connect to Relaxation Agent

---

## 📚 DOCUMENTATION REFERENCE

| File | When to Read |
|------|-------------|
| **This File** | Getting started |
| **VOICE_AGENT_QUICKREF.md** | Quick lookup |
| **VOICE_AGENT_README.md** | Understanding details |
| **INTEGRATION_GUIDE.md** | Connecting modules |
| **VOICE_AGENT_SUMMARY.md** | Viva preparation |
| **INDEX.md** | Complete index |

---

## 💡 TIPS & TRICKS

### Tip 1: Quick Test Loop
```bash
# Record → Process → View (30 seconds)
python src/audio/trigger_recorder_simple.py && python src/voice_agent/voice_agent_processor.py
```

### Tip 2: Debug Mode
```python
# Add to code to see intermediate results
import json
agent = VoiceAgentProcessor()
audio, sr = sf.read("test_recording.wav")
text = agent._extract_text(audio)
features = agent._extract_acoustic_features("test_recording.wav")
print(json.dumps({"text": text, "features": features}, indent=2))
```

### Tip 3: Batch Processing
```python
# Process multiple files
from pathlib import Path
agent = VoiceAgentProcessor()

for wav_file in Path(".").glob("*.wav"):
    result = agent.process_audio(str(wav_file))
    print(f"{wav_file}: {result['text']}")
```

---

## 🎓 FOR YOUR VIVA

**Be ready to explain:**
1. Run this test: `python test_voice_agent.py`
2. Show the output
3. Record voice: `python src/audio/trigger_recorder_simple.py`
4. Process it: `python src/voice_agent/voice_agent_processor.py`
5. Discuss the output format and features

**They will ask:**
- "What happens if Vosk doesn't recognize?" → Empty string returned
- "Why these specific acoustic features?" → Stress indicators
- "What's the JSON format?" → Show the output
- "Can you modify it?" → Yes, swap STT or add features

---

**Ready? Start with:**
```bash
python test_voice_agent.py
```

**Questions? See:**
- Quick Ref: `VOICE_AGENT_QUICKREF.md`
- Full Guide: `VOICE_AGENT_README.md`

---

**Good luck! 🚀**
