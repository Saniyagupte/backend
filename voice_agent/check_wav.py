import sys
import soundfile as sf

if len(sys.argv) < 2:
    print("Usage: python check_wav.py <wavfile>")
    sys.exit(1)

f = sys.argv[1]
data, sr = sf.read(f)
print(f"file={f} samples={len(data)} sr={sr} duration={len(data)/sr:.3f}s")
