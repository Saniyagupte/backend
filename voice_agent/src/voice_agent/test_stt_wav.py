from src.voice_agent.stt_vosk import STTVosk

import soundfile as sf

# CHANGE THIS PATH
WAV_PATH = "test2.wav"

MODEL_PATH = "models/vosk/vosk-model-small-en-us-0.15"

audio, sr = sf.read(WAV_PATH, dtype="float32")

print("Sample rate:", sr)
print("Samples:", len(audio))

stt = STTVosk(model_path=MODEL_PATH)
text = stt.transcribe(audio)

print("Recognized text:", text)
