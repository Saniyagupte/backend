"""
Main demo for TTS module
-----------------------

Simulates a Relaxation Agent input and generates `output.wav` using the
TTS engine. This script is intentionally small and demonstrates the
required voice_style -> prosody -> speech flow.

Run:
  pip install -r requirements.txt
  python main.py

"""
from pathlib import Path
import json

from src.voice_agent.style_map import get_voice_params
from src.voice_agent.tts_clean import TTSVoiceAgent


def main():
    fake_input = {
        "text": "Let’s slow down together. Take a gentle breath in.",
        "voice_style": "calm_slow",
    }

    out_path = Path("output.wav")

    print("Using voice_style:", fake_input["voice_style"])
    params = get_voice_params(fake_input["voice_style"])
    print("Params:", params)

    tts = TTSVoiceAgent()
    meta = tts.synthesize(fake_input["text"], fake_input["voice_style"], out_path=str(out_path))

    print("Wrote:", meta["file"])


if __name__ == "__main__":
    main()
