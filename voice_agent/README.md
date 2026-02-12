# Neurodivergent Driving Assistant — TTS Module

This small TTS module converts a relaxation agent's text output and a
`voice_style` into a speech WAV file (`output.wav`). It uses Coqui TTS
(`TTS.api.TTS`) and applies post-processing for speed, pitch, and energy
when the model or TTS API does not provide direct control.

Folder structure

- `main.py` — demo runner that simulates Relaxation Agent input and writes `output.wav`.
- `src/voice_agent/style_map.py` — `VOICE_STYLE_MAP` and helper.
- `src/voice_agent/tts_engine.py` — Coqui TTS wrapper with post-processing.
- `requirements.txt` — Python dependencies.

Installation

1. Create and activate a virtual environment (recommended):

```bash
python -m venv .venv
# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
# macOS / Linux
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

Note: `librosa` and `TTS` may install heavy dependencies (FFmpeg, numba,
sox). Ensure your environment has necessary build tools. `pydub` uses
FFmpeg for advanced audio operations; install FFmpeg on your system if needed.

How to run

```bash
python main.py
```

This will produce `output.wav` in the project root.

Voice styles

The module maps `voice_style` keys to prosody parameters (speed, pitch,
energy). The mapping is defined in `src/voice_agent/style_map.py`:

| style         | speed | pitch(semitones) | energy |
|---------------|-------:|------------------:|-------:|
| calm_slow     |  0.80 |               -2  |    0.6 |
| flat_steady   |  0.95 |               -1  |    0.7 |
| clear_neutral |  1.05 |                0  |    1.0 |
| neutral       |  1.00 |                0  |    0.9 |

If a `voice_style` is not found, the system falls back to `neutral`.

Implementation notes

- The TTS model used is `tts_models/en/vctk/vits` (Coqui VITS). On first
  use, the model weights are downloaded automatically by the `TTS` package.
- `speed` is applied with `librosa.effects.time_stretch` to change
  speaking rate without affecting pitch.
- `pitch` is applied with `librosa.effects.pitch_shift` (in semitones).
- `energy` scales waveform amplitude; clipping is prevented by limiting
  peak amplitude.

Troubleshooting

- If `TTS` is not installed, `main.py` will raise an informative error.
- Ensure `FFmpeg` is available in your PATH for `pydub`/audio backend
  operations.
- If installation of `librosa` or `TTS` fails due to binary dependencies,
  consult their installation instructions for your platform.

License & attribution

This code is provided for the final year project and may be adapted for
experimentation and demonstration. Coqui TTS models are provided by the
Coqui project under their respective licenses.
# VoiceAgent

Lightweight offline Voice Agent for extracting speech text and acoustic features.

Contents
- `src/` — Python source (main modules below)
- `models/` — optional model data (e.g., Vosk)
- `requirements.txt` — Python dependencies

Overview
--------
This project provides:
- Offline STT using Vosk (`src/voice_agent/stt_vosk.py`).
- Acoustic feature extraction via OpenSMILE (`src/voice_agent/voice_agent_processor.py` and `src/voice_agent/sst_engine.py`).
- Audio utilities and recorders in `src/audio/` including `SilenceDetector`.

Quick setup
-----------
1. Create and activate a virtual environment (PowerShell):

```powershell
python -m venv .venv
& ".venv\Scripts\Activate.ps1"
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

Run the modules
---------------
- Run the full processor test (uses `test_recording.wav` if present):

```powershell
python src/voice_agent/voice_agent_processor.py
```

- Run the SST wrapper (programmatic API):

```powershell
python - <<'PY'
import sys
sys.path.insert(0, 'src')
from voice_agent.sst_engine import SSTEngine
print(SSTEngine().process_audio('test_recording.wav'))
PY
```

- Quick STT test (example runner `run_stt.py`):

```powershell
python run_stt.py path\to\your.wav
```

Audio format
------------
For best results use 16 kHz mono PCM WAV files. The included recorders in `src/audio/` will save correct formats.

Testing
-------
- Unit tests: none included by default. You can run the test script `src/voice_agent/voice_agent_processor.py` as a smoke test.
- Where tests are needed, add `tests/` and use `pytest`.

Integration notes
-----------------
- The SST output is a JSON-like `dict` with keys `text` and `acoustic_features`.
- To integrate into another system:
  - Import `SSTEngine` from `voice_agent.sst_engine` (ensure `src` is on `PYTHONPATH` or install package editable).
  - Provide WAV path and use the return dict. Example:

```python
from voice_agent.sst_engine import SSTEngine
engine = SSTEngine()
result = engine.process_audio('recording.wav')
```

Maintenance
-----------
- Keep `models/` (e.g., Vosk) updated if using different STT models.
- OpenSMILE may warn about feature-set deprecation; migrate to newer feature sets if needed.

Contact
-------
For changes, edit and open a PR in this repository.

TTS (Voice Agent)
------------------
This repository includes a simple Voice Agent TTS module that maps a small
set of `voice_style` values (e.g. `calm_slow`, `flat_steady`, `clear_neutral`,
`neutral`) to prosody parameters and synthesizes speech.

Files:
- `src/voice_agent/tts_engine.py` — Voice Agent TTS wrapper. It will use
  Coqui TTS (`TTS.api.TTS`) when available, or fall back to a lightweight
  sine-wave generator for testing without downloading large models.
- `src/relaxation_agent/mock_relaxation.py` — fake relaxation agent that
  emits `{text, voice_style}` decisions for testing.
- `run_tts.py` — small runner that demonstrates the integration.

Quick TTS test (fast, uses fallback synthetic audio):
```powershell
python run_tts.py --backend=fallback
```

To use Coqui TTS (will download model weights on first run):
```powershell
pip install TTS
python run_tts.py --backend=coqui
```

