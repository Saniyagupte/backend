from audio.microphone import MicrophoneRecorder
from voice_agent.stt_vosk import STTVosk

# Record and transcribe
recorder = MicrophoneRecorder()
audio = recorder.record(verbose=True)

stt = STTVosk()
text = stt.transcribe(audio)
print(f"You said: {text}")