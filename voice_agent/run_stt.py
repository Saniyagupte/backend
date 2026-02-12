import sys
sys.path.insert(0, "src")
from voice_agent.stt_vosk import STTVosk
import soundfile as sf

wav = sys.argv[1]
audio, sr = sf.read(wav)
stt = STTVosk()                # optionally pass model_path
print(stt.transcribe(audio))