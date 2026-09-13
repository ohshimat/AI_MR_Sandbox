# CHECKPOINT-1
## Speech Recognition → TCP/IP → Unity Console

## 1. 目的
ユーザの発話をPythonで音声認識し，
認識結果をJSONメッセージとしてTCP/IP経由でUnityへ送信し，
Unity側でJSONを解釈して text フィールドをConsoleへ表示する．

## 2. 達成条件
発話：
「私の右へ移動してください」

Unity Console：
私の右へ移動してください

## 3. 実行環境
- Windows
- Python 3.11.9
- Visual Studio Code
- Unity
- faster-whisper
- sounddevice
- numpy
- TCP/IP
- UTF-8
- localhost 127.0.0.1
- Port 50000

## 4. システム構成

Human Speech
↓
Microphone
↓
Python
↓
faster-whisper
↓
JSON
↓
TCP/IP
↓
Unity
↓
JsonUtility
↓
text
↓
Console

## 5. Python仮想環境
...

## 6. マイク設定
device_id = 7
Microphone (USB Sound Blaster HD)

## 7. Python側プログラム
speech_to_unity.py
...

## 8. Unity側プログラム
TcpSpeechReceiver.cs
...

## 9. 実行手順
1. UnityをPlayする
2. TCP server started. を確認
3. speech_to_unity.pyを実行
4. 3秒間発話
5. Unity Consoleで認識文字列を確認

## 10. JSONメッセージ仕様
{
  "type": "speech_recognition",
  "speaker": "Human_1",
  "text": "私の右へ移動してください"
}

## 11. 確認結果
Python側で音声認識成功．
JSON生成成功．
TCP/IP通信成功．
Unity側でJSON解析成功．
textフィールドのConsole表示成功．

## 12. Checkpoint 1 判定
達成．

## 13. 次のCheckpoint
認識文字列をHuman-AI相互作用エンジン内で解釈し，
行動指示として扱う処理へ進む．