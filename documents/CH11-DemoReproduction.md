# AI MR Sandboxの変更点とデモ再現手順

立命館業務共有資料　対象日 2026年10月20日　更新日 2026年10月21日

## 1 変更の概要

本資料は、Sample6への追加機能と、同じデモを再現するための配置・起動・操作手順を示す。

Sample6でWhisperとOllamaを使った音声操作を確認し、AI_1を移動させる処理を動作させた。続いて、PCのGUIで「操作」と「会話」を切り替える追加機能を作成・導入した。操作はOllama、会話はOpenAI APIを使う構成である。

Main_Conversationシーンで右方向への移動とVerification: PASSを確認した。OpenAIによる会話・音声応答は、APIキーの準備後に動作確認する。

## 2 フォルダ構成の変更点

リポジトリの基本構成を保ちながら、Pythonの処理とUnityの追加機能を増設した。元のMainシーンを残し、会話機能を試すMain_Conversationシーンを別に用意する。

| 場所 | 変更内容 |
| --- | --- |
| python/ | 音声操作用のspeech_to_unity_ollama.pyを追加。さらにGUI用のPython 3本を追加した。既存のspeech_to_unity_loop.pyは残す。 |
| python/mr_agent_tests/ | 追加したGUI側処理の検証コードを格納するフォルダを作成した。 |
| unity_addons/MRConversation/ | Unityに組み込むC#の配布元。実行時スクリプト2本と、Editor内の導入用スクリプト1本をまとめた。 |
| 作業用UnityのAssets/MRConversation/ | 配布元のC#をUnityへコピーする導入先。Editorサブフォルダも含めて配置する。 |
| 作業用UnityのAssets/Scenes/ | Mainを複製したMain_Conversation.unityに、MRConversationオブジェクトを追加する。 |
| リポジトリ直下 | MRConversation_README.mdとMRConversation_Package_v1.zipを追加した。 |

## 3 作業用UnityとPython環境

プロジェクトの起点は C:\Users\Administrator\Desktop\AI_MR_Sandbox。導入手順では、既存のSample6を複製した次の作業用フォルダを使用する。

unity/MREAL_OpenXR_Sample6_Haptic_Sandbox_ollama_test/

音声操作・会話GUIはリポジトリ直下の.venvを使用する。画像生成・LoRA学習用のC:\AI_venvs\AI_MR_Sandboxとは別の環境であり、今回の変更は音声操作・会話機能側の追加である。

## 4 追加ファイルの内容

以下のパスは、AI_MR_Sandboxを起点とする。Unityの導入先では、unity_addons/MRConversation/に相当する部分をAssets/MRConversation/に読み替える。

| ファイル | 役割 |
| --- | --- |
| python/speech_to_unity_ollama.py | Whisperで音声を文字起こしし、Qwenが移動命令に変換する。確認のみ／Unityへ送信を切り替える従来経路の実行用。 |
| python/mr_agent_gui.py | PC用の操作画面。モード選択、5秒録音、文字入力、結果表示、APIキーなどの設定を行う。GUI起動時にバックエンドも起動する。 |
| python/mr_agent_backend.py | 録音・文字起こし、処理状態、モード切替、取消しを管理する。会話応答と音声を生成し、Unity向けのHTTP通信を提供する。 |
| python/mr_agent_commands.py | Ollamaへの命令解釈依頼と返却JSONの検証を担当する。右・左・前への移動に対応し、曖昧な依頼や非対応の指示は実行しない設計。 |
| unity_addons/MRConversation/<br>MRConversationBridge.cs | Unityとバックエンドを接続する。操作時のAIRManager通信、移動結果の通知、会話音声の再生、音量に応じた見た目の伸縮を行う。 |
| unity_addons/MRConversation/<br>MRAgentPanel.cs | MR空間の操作パネルを作成する。操作／会話、録音、停止、表示位置の調整を提供し、指先接触やGame画面のマウス操作を扱う。 |
| unity_addons/MRConversation/<br>Editor/MRConversationInstaller.cs | UnityのToolsメニューから導入する処理。Mainの複製、MRConversationの追加、参照設定、旧受信コンポーネントの無効化を行う。 |
| python/mr_agent_tests/<br>test_controller.py | モード変更時の取消し、重複入力の制御、WAV生成、HTTP連携などを模擬応答で検証するテスト。 |
| MRConversation_README.md | 配置先、起動手順、Unityの設定、動作確認、通信方式を記載した導入説明書。 |
| MRConversation_Package_v1.zip | 導入用一式。Python 3本、Unity C# 3本、テスト、README_JA.mdを含む。speech_to_unity_ollama.pyは含まない。 |

配布元のunity_addons/、ZIP内のUnity/、導入後のAssets/は同じ追加機能の置き場所を表す。Unityが読み込むのは、プロジェクト内のAssets/MRConversation/である。

## 5 初回の配置とUnity設定

既存のSample6でMREAL実機表示ができるWindows PCを前提とする。共有する追加ZIPは、既存のSample6、MREALの実行環境、C++のAIRManager_v2と組み合わせて使う。設定済みのMain_Conversationを受け取った場合は、参照を確認して次ページの起動手順へ進む。

### 5.1 必要な環境

| 項目 | 使用するもの |
| --- | --- |
| UnityとMREAL | 作業用Sample6が動作するUnityとMREAL環境。Unityの版は、共有された作業用コピーのProjectSettings/ProjectVersion.txtに合わせる。 |
| Python | Python 3.11.9を基準とした、リポジトリ直下の.venv。sounddevice、numpy、faster-whisperとTkinterを使用する。 |
| 音声認識と命令解釈 | Whisper baseとOllamaのqwen3:8b。マイクを接続する。モデル未取得時はダウンロードにインターネット接続が必要。 |
| 位置計算 | C++/AIRManager_v2/x64/Debug/AIRManager.exe。実行ファイルがない場合はAIRManager.slnをVisual Studioで開き、Debug／x64でビルドする。 |

### 5.2 ファイルを配置する

既存のunity/MREAL_OpenXR_Sample6_Haptic_Sandboxを作業用コピーとして用意し、Unity Hubから開く。以下ではコピー名をMREAL_OpenXR_Sample6_Haptic_Sandbox_ollama_testとする。

| ZIP内のファイル | 配置先 |
| --- | --- |
| python/内のmr_agent_*.py 3本 | AI_MR_Sandbox/python/ |
| Unity/MRConversation/一式 | 作業用UnityのAssets/MRConversation/<br>Editorサブフォルダも含める。 |
| python/mr_agent_tests/ | AI_MR_Sandbox/python/mr_agent_tests/<br>検証用。デモ実行には必須ではない。 |

### 5.3 会話用シーンを作成する

① コピー側のAssets/Scenes/Mainを開き、再生を停止した状態でCtrl+S。② コンパイル完了後、Tools → MR Sandbox → Add Conversation to Current Sceneを選ぶ。③ 作成されたMain_ConversationをCtrl+Sで保存する。

HierarchyのMRConversationを選び、MR Conversation Bridgeの参照を確認する。導入処理は既存のAIRStateSenderからHuman_1とAI_1の参照を引き継ぐ。

| Inspectorの項目 | 設定 |
| --- | --- |
| Human Transform ／ AI Transform | 既存のHuman_1 ／ AI_1 |
| Permission Checker ／ Human Evaluator | 既存のPermissionChecker ／ HumanEvaluator |
| Backend URL ／ Air Port | http://127.0.0.1:50002 ／ 50001 |
| Speech Expansion | 0.08（音声再生時の最大拡大量） |

PermissionCheckerのAllow Moveをオンにする。新シーンでは旧TcpSpeechReceiverが無効になるため、旧speech_to_unity_ollama.pyの--sendは併用しない。元のMainシーンと既存スクリプトは保持する。

## 6 起動する

Python GUI、Unity、AIRManagerは同じPCで起動する。以下のコマンドはPowerShellで実行する。最初のパスは、AI_MR_Sandboxの実際の保存先に置き換える。

Set-Location "C:\Users\Administrator\Desktop\AI_MR_Sandbox"

### 6.1 Python環境を確認する

既存の.venvが使える場合は、そのまま使用する。別PCで.venvがない場合は、Python 3.11.9を用意してから次を実行する。仮想環境の有効化は不要で、以降はpython.exeを直接指定する。

python --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install sounddevice numpy faster-whisper

マイク番号はPCごとに異なる。次の一覧で入力デバイスを確認し、GUI起動時の--deviceに指定する。10月20日の動作確認では1を使用した。

.\.venv\Scripts\python.exe -c "import sounddevice as sd; print(sd.query_devices())"

### 6.2 Ollamaを起動する

Ollamaアプリを起動し、次のコマンドでqwen3:8bがあることを確認する。モデルがない場合だけ、続くpullコマンドで取得する。

ollama list
ollama pull qwen3:8b

Ollamaが起動していない場合は、別のPowerShellでollama serveを実行して、そのウィンドウを開いておく。11434番が使用中の場合は、Ollamaがすでに動いている可能性があるため、二重起動せずollama listの応答を確認する。

### 6.3 AIRManagerとGUIを起動する

AIRManagerが未起動の場合に実行する。続くコマンドでPC用GUIを起動する。--device 1の1は、使用するマイク番号に置き換える。

Start-Process ".\C++\AIRManager_v2\x64\Debug\AIRManager.exe"
.\.venv\Scripts\python.exe .\python\mr_agent_gui.py --device 1

### 6.4 Unityを再生する

作業用UnityのAssets/Scenes/Main_Conversationを開き、再生する。一時停止は解除する。PC用GUIに「Unity接続中」が表示され、MREAL内にAI_1が表示されることを確認する。

| 接続 | 用途 |
| --- | --- |
| localhost:11434 | PythonからOllamaへ命令解釈を依頼する。 |
| 127.0.0.1:50002 | PythonとUnityの間で入力・状態・結果を受け渡す。 |
| 127.0.0.1:50001 | UnityからAIRManagerへ位置計算を依頼する。 |

新GUIは50000番を使用しない。Whisper baseは最初の音声入力時に準備されるため、初回は「録音中」の表示まで待つ。

## 7 移動デモを再現する

APIキーなしで確認できる操作モードを使用する。まず文字入力で移動経路を確認し、次に音声入力へ進む。

| 操作 | 確認する結果 |
| --- | --- |
| ① GUIで「操作 · Ollama」を選ぶ。<br>「私の右に来て」を文字欄へ入力し、<br>「文字を送信」を押す。 | AI_1がHuman_1の右側へ移動する。GUIの「詳細」またはUnity ConsoleでVerification: PASS Direction = rightを確認する。 |
| ② 「話す（5秒）」を押し、<br>「録音中」と表示されてから<br>「私の左に来て」と話す。 | 文字起こし、命令解釈を経てAI_1が左側へ移動する。Direction = leftのPASSを確認する。 |
| ③ 同じ手順で<br>「私の前に来て」と話す。 | AI_1がHuman_1の正面へ移動する。Direction = forwardのPASSを確認する。 |

位置の基準は、実行時のHuman_1の位置と水平向きで、距離は1m固定。到着後は追従しない。Human_1が頭部追跡に接続されていない場合は、シーン内のHuman_1の向きが基準になる。

パネルが見えない場合はGUIの「パネルを前へ」を押す。手追跡が動く環境ではMR内のボタンを指先で操作できる。10月20日は手追跡の警告があったため、再現確認はPC用GUIから行う。

## 8 会話機能を試す場合

会話・音声再生・伸縮は実装済みだが、10月20日はAPIキー未取得のため実サービスでの動作は未確認。次は移動デモとは別の追加確認手順である。

① 利用可能なOpenAI APIキーを用意する。② GUIの「設定」でキーを入力し、「適用して閉じる」。③ 「会話 · OpenAI」を選び、「こんにちは」を文字で送信する。④ 返答文、AI_1からの音声、音量に合わせた伸縮を確認する。音声入力でも同様に試す。

コードの初期値は会話gpt-4.1-mini、音声gpt-4o-mini-tts、声coral。会話中は移動を行わない。声の高さや感情ではなく、音量に応じて見た目を最大8%拡大する。

## 9 うまく動かない場合

| 症状 | 確認する場所 |
| --- | --- |
| GUIがUnity未接続 | Main_Conversationが再生中か、MRConversationが有効か、Backend URLが50002か、Inspector参照がNoneでないか確認する。 |
| 入力しても移動しない | 操作モード、Ollamaの起動とqwen3:8b、AIRManagerの起動、PermissionCheckerのAllow Moveを確認する。 |
| 音声を認識しない | マイク番号とWindowsのマイク使用許可を確認し、「録音中」になってから話す。文字入力で移動できれば、音声入力側を切り分けられる。 |
| 手のパネルを押せない | XR Handsの追跡状態を確認する。PC用GUI、またはUnityのGame画面上のマウス操作で確認を続ける。 |

## 10 終了する

GUIの「停止」を押し、Unityの再生を止め、GUIを閉じる。デモ用に起動したAIRManagerも終了する。従来の動作へ戻す場合は、元のAssets/Scenes/Mainを開く。

再現手順の根拠　MRConversation_README.md、追加Python・C#の実装、2026年10月20日の動作確認画面。Ollamaコマンドの参考　https://docs.ollama.com/cli
