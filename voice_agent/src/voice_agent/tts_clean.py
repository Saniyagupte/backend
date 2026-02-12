"""
Clean TTS engine (alternate module): exposes `TTSVoiceAgent`.

Prefer this file when `tts_engine.py` is corrupted. It is self-contained,
prefers Coqui TTS when available, and falls back to a harmonic synthesizer.
"""
from pathlib import Path
import logging
import tempfile
import json
from typing import Dict

import numpy as np
import soundfile as sf

from src.voice_agent.style_map import get_voice_params

log = logging.getLogger("tts_clean")

try:
    from TTS.api import TTS  # type: ignore
    _HAS_COQUI = True
except Exception:
    TTS = None  # type: ignore
    _HAS_COQUI = False

try:
    import librosa
except Exception:
    librosa = None


class TTSVoiceAgent:
    def __init__(self, model_name: str = "tts_models/en/vctk/vits", backend: str = "coqui"):
        self.model_name = model_name
        self._tts = None
        self.backend = backend
        # If user requests fallback, disable Coqui even if installed
        if backend == "fallback":
            self.coqui_available = False
        else:
            self.coqui_available = _HAS_COQUI

    def _ensure_model(self):
        if not self.coqui_available:
            return
        if self._tts is None:
            self._tts = TTS(self.model_name)

    def synthesize(self, text: str, voice_style: str, out_path: str = "output.wav") -> Dict:
        params = get_voice_params(voice_style)
        out_path = Path(out_path)

        if self.coqui_available:
            self._ensure_model()
            tmp_path = None
            try:
                tf = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
                tmp_path = Path(tf.name)
                tf.close()

                try:
                    try:
                        self._tts.tts_to_file(text=text, file_path=str(tmp_path), speed=params.get("speed"))
                    except TypeError:
                        self._tts.tts_to_file(text=text, file_path=str(tmp_path))
                except Exception:
                    wav = self._tts.tts(text)
                    if isinstance(wav, (list, tuple)):
                        data = np.asarray(wav[0], dtype=np.float32)
                        sr = int(wav[1]) if len(wav) > 1 else getattr(self._tts, "sr", 22050)
                        sf.write(str(tmp_path), data, sr)
                    else:
                        data = np.asarray(wav, dtype=np.float32)
                        sr = getattr(self._tts, "sr", 22050)
                        sf.write(str(tmp_path), data, sr)

                data, sr = sf.read(str(tmp_path), dtype="float32")
            finally:
                if tmp_path is not None and tmp_path.exists():
                    try:
                        tmp_path.unlink()
                    except Exception:
                        pass

            if data.ndim > 1:
                data = np.mean(data, axis=1)

            duration = len(data) / float(sr) if sr > 0 else 0.0
            if duration < 0.03:
                log.warning("Generated audio very short (%.3fs); writing raw output", duration)
                sf.write(str(out_path), data, sr)
                return {"file": str(out_path), "params": params}

            y = data.astype("float32")
            speed = float(params.get("speed", 1.0))
            pitch = float(params.get("pitch", 0.0))
            energy = float(params.get("energy", 0.9))

            if librosa is not None:
                try:
                    if abs(speed - 1.0) > 1e-3:
                        y = librosa.effects.time_stretch(y, rate=speed)
                    if abs(pitch) > 1e-3:
                        y = librosa.effects.pitch_shift(y, sr, n_steps=pitch)
                except Exception as e:
                    log.warning("librosa post-processing failed: %s", e)
            else:
                if abs(speed - 1.0) > 1e-3:
                    write_sr = int(sr * speed)
                    sf.write(str(out_path), y, write_sr)
                    return {"file": str(out_path), "params": params}

            try:
                y = y * (energy / 0.9)
                peak = np.max(np.abs(y))
                if peak > 1.0:
                    y = y / peak * 0.99
            except Exception:
                log.warning("energy scaling failed, skipping")

            sf.write(str(out_path), y, sr)
            return {"file": str(out_path), "params": params}

        # fallback
        self._synthesize_fallback(text, params, out_path)
        return {"file": str(out_path), "params": params}

    def _synthesize_fallback(self, text: str, params: Dict, out_path: Path):
        sample_rate = 22050
        try:
            word_count = max(1, len(str(text).split()))
        except Exception:
            word_count = 1

        base_per_word = 0.6
        duration_sec = float(min(20.0, max(1.0, base_per_word * word_count)))

        speed = float(params.get("speed", 1.0))
        pitch = float(params.get("pitch", 0.0))
        energy = float(params.get("energy", 0.9))

        adjusted_duration = duration_sec / max(1e-6, speed)
        n_samples = int(sample_rate * adjusted_duration)

        base_freq = 220.0 * (2 ** (pitch / 12.0))
        amplitude = max(0.01, min(0.9, energy)) * 0.6

        t = np.linspace(0, adjusted_duration, n_samples, endpoint=False)
        value = 0.6 * np.sin(2.0 * np.pi * base_freq * t)
        value += 0.3 * np.sin(2.0 * np.pi * base_freq * 2 * t)
        value += 0.1 * np.sin(2.0 * np.pi * base_freq * 3 * t)

        fade_len = int(0.02 * sample_rate)
        env = np.ones_like(value)
        if fade_len > 0 and fade_len < len(env):
            env[:fade_len] = np.linspace(0.0, 1.0, fade_len)
            env[-fade_len:] = np.linspace(1.0, 0.0, fade_len)

        y = amplitude * env * value
        peak = np.max(np.abs(y)) if y.size else 0.0
        if peak > 1.0:
            y = y / peak * 0.99

        sf.write(str(out_path), y.astype("float32"), sample_rate)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    demo_text = "Let's slow down together. Take a gentle breath in."
    agent = TTSVoiceAgent()
    out = agent.synthesize(demo_text, "calm_slow", out_path="output.wav")
    print(json.dumps(out, indent=2))