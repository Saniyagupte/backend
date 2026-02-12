"""
Mock relaxation agent for testing Voice Agent TTS input.

This module emits a small JSON-like dict with `text` and `voice_style`.
"""
from typing import Dict

def sample_decision(strategy: str) -> Dict:
    mapping = {
        "breathing": "calm_slow",
        "grounding": "flat_steady",
        "focus_reset": "clear_neutral",
    }
    voice_style = mapping.get(strategy, "neutral")
    text_map = {
        "breathing": "Breathe in... and out...",
        "grounding": "Notice the ground under your feet.",
        "focus_reset": "Let's take a short break and refocus.",
        "neutral": "Hello. This is a neutral message."
    }

    return {"text": text_map.get(strategy, text_map["neutral"]), "voice_style": voice_style}


if __name__ == "__main__":
    # quick demo
    import sys
    strat = sys.argv[1] if len(sys.argv) > 1 else "breathing"
    d = sample_decision(strat)
    print(d)
