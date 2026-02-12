# SST (Speech-to-Text) Module

Location: `src/voice_agent/`

Overview
--------
This module provides two main pieces:

- `stt_vosk.py`: low-level Vosk STT wrapper (`STTVosk`) that accepts a numpy audio buffer and returns a string transcription.
- `sst_engine.py`: higher-level `SSTEngine` wrapper that runs STT, computes silence-based statistics (pause mean and voiced duration) and extracts acoustic features using OpenSMILE. Returns a dictionary:

```
{
  "text": "...",
  "acoustic_features": {
    "pitch_mean": ..., "pitch_var": ..., "energy": ..., "speech_rate": ..., "pause_mean": ..., "jitter": ..., "shimmer": ..., "mfcc": [...] 
  }
}
```

How to run
----------
1. Activate venv and install requirements:

```powershell
& ".venv\Scripts\Activate.ps1"
pip install -r requirements.txt
```

2. Run the built-in processor smoke test (uses `test_recording.wav` if present):

```powershell
python src/voice_agent/voice_agent_processor.py
```

3. Programmatic usage via `SSTEngine`:

```python
import sys
sys.path.insert(0, 'src')
from voice_agent.sst_engine import SSTEngine
engine = SSTEngine()
result = engine.process_audio('test_recording.wav')
print(result)
```

STTVosk usage
--------------
`STTVosk` is intended for direct audio buffer transcription. Example:

```python
import soundfile as sf
from voice_agent.stt_vosk import STTVosk

audio, sr = sf.read('sample.wav')
stt = STTVosk()
text = stt.transcribe(audio)
```

Notes on transcription quality
-----------------------------
- Ensure audio is reasonably loud and clear; Vosk models are sensitive to noise.
- The processor now feeds audio to Vosk in 4096-sample chunks and accumulates partials, improving recognition for short/streamed inputs.

Integration suggestions
-----------------------
- To integrate into a larger pipeline, call `SSTEngine.process_audio()` and forward the returned dict to the downstream component.
- If you deploy as a service, consider implementing a wrapper that accepts audio uploads and returns JSON responses.

TTS Integration
---------------
The Voice Agent TTS is implemented in `src/voice_agent/tts_engine.py`. To synthesize
the text returned by a relaxation policy, call `TTSVoiceAgent.synthesize(text, voice_style)`.

Example (programmatic):

```python
import sys
sys.path.insert(0, 'src')
from relaxation_agent.mock_relaxation import sample_decision
from voice_agent.tts_engine import TTSVoiceAgent

decision = sample_decision('breathing')
tts = TTSVoiceAgent(backend='fallback')  # or 'coqui' if installed
tts.synthesize(decision['text'], decision['voice_style'], out_path='out.wav')
```

See `run_tts.py` for a small demo script that wires the mock relaxation agent to the TTS engine.

