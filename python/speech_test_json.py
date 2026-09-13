import sounddevice as sd
import numpy as np
import wave
import json
from faster_whisper import WhisperModel

device_id = 7
duration = 3
samplerate = 44100
wav_file = "speech_test.wav"

print("Whisperモデルを準備しています...")

model = WhisperModel(
    "base",
    device="cpu",
    compute_type="int8"
)

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

audio_int16 = (audio * 32767).astype(np.int16)

with wave.open(wav_file, "wb") as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(samplerate)
    wf.writeframes(audio_int16.tobytes())

print("認識中...")

segments, info = model.transcribe(
    wav_file,
    language="ja"
)

text = "".join(segment.text for segment in segments).strip()

message = {
    "type": "speech_recognition",
    "speaker": "Human_1",
    "text": text
}

print("\n認識結果:")
print(text)

print("\n送信用JSON:")
print(json.dumps(message, ensure_ascii=False))