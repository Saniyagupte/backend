"""Run TTS demo: uses mock relaxation agent and TTSVoiceAgent.

Usage:
  python run_tts.py --backend=fallback  # fast test
  python run_tts.py --backend=coqui     # use Coqui TTS (downloads model)
"""
import sys
import argparse
from pathlib import Path

sys.path.insert(0, "src")

from relaxation_agent.mock_relaxation import sample_decision
from voice_agent.tts_clean import TTSVoiceAgent


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--backend", choices=["coqui", "fallback"], default="fallback")
    p.add_argument("--strategy", choices=["breathing", "grounding", "focus_reset", "neutral"], default="breathing")
    p.add_argument("--out", default="tts_output.wav")
    args = p.parse_args()

    decision = sample_decision(args.strategy)
    print("Mock relaxation decision:", decision)

    tts = TTSVoiceAgent(backend=args.backend)
    result = tts.synthesize(decision["text"], decision["voice_style"], out_path=args.out)
    print("Wrote:", result["file"])


if __name__ == "__main__":
    main()
