"""
Voice style mapping
-------------------

Contains the VOICE_STYLE_MAP used by the TTS engine. Provides a helper
to retrieve parameters for a given style with a fallback to `neutral`.
"""
from typing import Dict

VOICE_STYLE_MAP: Dict[str, Dict[str, float]] = {
    "calm_slow":     {"speed": 0.80, "pitch": -2, "energy": 0.6},
    "flat_steady":   {"speed": 0.95, "pitch": -1, "energy": 0.7},
    "clear_neutral": {"speed": 1.05, "pitch":  0, "energy": 1.0},
    "neutral":       {"speed": 1.00, "pitch":  0, "energy": 0.9},
}


def get_voice_params(style: str) -> Dict[str, float]:
    """Return prosody parameters for `style`, fallback to `neutral`.

    Args:
        style: voice style key

    Returns:
        Dictionary with `speed`, `pitch` (semitones), and `energy`.
    """
    return VOICE_STYLE_MAP.get(style, VOICE_STYLE_MAP["neutral"]) 
