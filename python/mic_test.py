import sounddevice as sd
import numpy as np

device_id = 7
duration = 3
samplerate = 44100

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
print("最大振幅:", np.max(np.abs(audio)))