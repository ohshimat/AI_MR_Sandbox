import sounddevice as sd
import numpy as np
import wave
from faster_whisper import WhisperModel

device_id = 7
duration = 3
samplerate = 44100
wav_file = "speech_test.wav"

# Whisperモデル
print("Whisperモデルを準備しています...")
model = WhisperModel(
    "base",
    device="cpu",
    compute_type="int8"
)

# 録音
print("3秒間話してください")

audio = sd.rec(
    int(duration * samplerate),
    samplerate=samplerate,
    channels=1,
    dtype="float32",
    device=device_id
)

sd.wait()
print("録音終了")

# WAVファイルとして保存
audio_int16 = (audio * 32767).astype(np.int16)

with wave.open(wav_file, "wb") as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(samplerate)
    wf.writeframes(audio_int16.tobytes())

# 音声認識
print("認識中...")

segments, info = model.transcribe(
    wav_file,
    language="ja"
)

text = "".join(segment.text for segment in segments)

print("認識結果:")
print(text)