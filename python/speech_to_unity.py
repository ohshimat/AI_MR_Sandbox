import sounddevice as sd
import numpy as np
import wave
import json
import socket
from faster_whisper import WhisperModel

# -------------------------
# 設定
# -------------------------

device_id = 7
duration = 3
samplerate = 44100
wav_file = "speech_test.wav"

host = "127.0.0.1"
port = 50000

# -------------------------
# Whisper準備
# -------------------------

print("Whisperモデルを準備しています...")

model = WhisperModel(
    "base",
    device="cpu",
    compute_type="int8"
)

# -------------------------
# 録音
# -------------------------

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

# WAV保存
audio_int16 = (audio * 32767).astype(np.int16)

with wave.open(wav_file, "wb") as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(samplerate)
    wf.writeframes(audio_int16.tobytes())

# -------------------------
# 音声認識
# -------------------------

print("認識中...")

segments, info = model.transcribe(
    wav_file,
    language="ja"
)

text = "".join(segment.text for segment in segments).strip()

print("認識結果:")
print(text)

# -------------------------
# JSONメッセージ作成
# -------------------------

message = {
    "type": "speech_recognition",
    "speaker": "Human_1",
    "text": text
}

json_message = json.dumps(
    message,
    ensure_ascii=False
)

print("送信JSON:")
print(json_message)

# -------------------------
# UnityへTCP送信
# -------------------------

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((host, port))
    s.sendall(json_message.encode("utf-8"))

print("Unityへ送信しました")