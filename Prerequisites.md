はい．今回の「別PCでGitHubからクローンして再現する」作業をそのまま反映して，`Prerequisites.md` を作りましょう．  
これはCheckpoint文書とは別に，**AI_MR_Sandboxを新しいPCで動かす前提環境**をまとめる文書にするとよいです．

そのまま貼れる形です．

```markdown
# Prerequisites
## AI_MR_Sandbox Development Environment

この文書は，AI_MR_Sandboxを新しいWindows PC上で再構築するための
基本的な開発環境とセットアップ手順を記録する．

本プロジェクトでは，GitHub上のソースコードを共有し，
Python仮想環境などのローカル環境は各PC上で再構築する．

---

## 1. 基本環境

現時点の基本開発環境は以下とする．

```text
OS          : Windows
Editor      : Visual Studio Code
Python      : 3.11.9
Version Control : Git / GitHub
Unity       : Unity project included in repository
```

Pythonについては，

```text
Python 3.11.9
```

を基準バージョンとして使用する．

Python 3.13等がPCに共存していてもよいが，
AI_MR_SandboxではPython 3.11.9を選択する．

---

## 2. Visual Studio Code

Visual Studio Codeをインストールする．

### 日本語化

Extensionsから，

```text
Japanese Language Pack for Visual Studio Code
```

をインストールする．

Microsoft製のExtensionを使用する．

インストール後，表示言語を日本語に変更し，
VS Codeを再起動する．

---

## 3. VS Codeの表示テーマ

視認性を考慮し，
明るいテーマを使用する．

現在は，

```text
Light Modern
```

等のLight Themeを推奨する．

テーマは，

```text
ファイル
→ ユーザー設定
→ テーマ
→ 配色テーマ
```

から変更できる．

---

## 4. VS Code Workspace Trust

VS Codeでは，
セキュリティ設定によりExtensionやPython機能が
制限される場合がある．

画面に，

```text
制限モード
Restricted Mode
```

が表示されている場合には，
自分で管理しているAI_MR_Sandboxフォルダについて，

```text
このフォルダーを信頼する
```

を選択する．

Workspaceが信頼されていない場合，

```text
Python:
```

コマンドがCommand Paletteに表示されないことがある．

---

## 5. Python Extension

VS Code Extensionsから，

```text
Python
```

を検索し，

```text
Microsoft
ms-python.python
```

のPython Extensionをインストールする．

必要に応じてPylance等が同時にインストールされても問題ない．

---

## 6. Python Interpreterの選択

Python 3.11.9をPCへインストールした後，

```text
Ctrl + Shift + P
```

から，

```text
Python: インタープリターを選択
```

を実行する．

Python 3.11.9を選択する．

確認：

```powershell
python --version
```

期待される結果：

```text
Python 3.11.9
```

---

## 7. Git

Git for Windowsをインストールする．

確認：

```powershell
git --version
```

例：

```text
git version 2.x.x.windows.x
```

Gitが認識されれば準備完了である．

---

## 8. GitHub Repository

AI_MR_SandboxのRepository：

```text
https://github.com/ohshimat/AI_MR_Sandbox
```

VS Codeから，

```text
Ctrl + Shift + P
```

を開き，

```text
Git: Clone
```

を選択する．

Clone URL：

```text
https://github.com/ohshimat/AI_MR_Sandbox.git
```

保存先の親フォルダを指定する．

例：

```text
C:\Users\<UserName>\Desktop\
```

Clone後，

```text
AI_MR_Sandbox
```

フォルダをVS Codeで開く．

---

## 9. Python仮想環境

Pythonの仮想環境はGitHubでは共有しない．

各PC上で，

```text
.venv
```

を新しく作成する．

Repository rootで，

```powershell
python -m venv .venv
```

を実行する．

Windows PowerShellでは，

```powershell
.venv\Scripts\Activate.ps1
```

で有効化する．

成功するとTerminalの先頭が，

```text
(.venv)
```

となる．

確認：

```powershell
python --version
```

結果：

```text
Python 3.11.9
```

---

## 10. .venv再作成時の注意

すでに `.venv` が有効になっている状態で，

```powershell
python -m venv .venv
```

を実行すると，

```text
Permission denied:
...\ .venv\Scripts\python.exe
```

のようなエラーが発生する場合がある．

この場合はまず，

```powershell
deactivate
```

を実行する．

その後，

```text
.venv
```

フォルダを削除し，

```powershell
python -m venv .venv
```

を再実行する．

`.venv` は各PC固有のローカル環境なので，
削除・再作成して問題ない．

---

## 11. Python Packages

現在のPython側実装では，
少なくとも以下を使用する．

```text
sounddevice
numpy
faster-whisper
```

仮想環境を有効化した状態で，

```powershell
pip install sounddevice numpy faster-whisper
```

を実行する．

確認：

```powershell
pip list
```

少なくとも，

```text
sounddevice
numpy
faster-whisper
```

が表示されることを確認する．

---

## 12. Microphone

音声認識Checkpointでは，
PCから利用可能なAudio Input Deviceを確認する必要がある．

使用デバイス番号はPCごとに異なる可能性があるため，
以前のPCで使用していた，

```text
device_id = 7
```

等をそのまま使用しない．

新しいPCでは `sounddevice` により
Audio Device一覧を確認し，
使用するMicrophoneのdevice IDを設定する．

したがって，

```text
device_id
```

は環境依存パラメータとして扱う．

---

## 13. Unity

Repositoryに含まれるUnity Projectを，
Unity Hubから開く．

初回起動時にはUnityが，

```text
Library
Temp
Obj
Logs
```

等のローカル生成ファイルを再構築する場合がある．

これらはGitHubでは共有しない．

Unity Projectを開いた後，

```text
Hierarchy
Scene
Scripts
Inspector references
```

が正しく復元されていることを確認する．

特にCHECKPOINT-7以降では，
Inspector上のComponent参照が動作に重要である．

---

## 14. Unity Inspector Reference

CHECKPOINT-7時点では，
主な参照関係は以下である．

```text
TcpSpeechReceiver
    │
    ├── PermissionChecker
    ├── Human_1 Transform
    ├── AI_1 Transform
    │
    └── ActionVerifier
            │
            ├── Human_1 Transform
            ├── AI_1 Transform
            │
            └── HumanEvaluator
                    │
                    └── ExperienceLogger
```

Clone後は，
これらのInspector Referenceが維持されているか確認する．

特に，

```text
Verification
└─ ActionVerifier
     └─ Human Evaluator → HumanEvaluation
```

および，

```text
HumanEvaluation
└─ HumanEvaluator
     └─ Experience Logger → Experience
```

を確認する．

参照が `None` になっている場合，
コードにエラーがなくても処理が実行されない場合がある．

---

## 15. Gitで共有しないもの

以下は各PC上で再生成する．

```text
.venv/
__pycache__/

Unity/Library/
Unity/Temp/
Unity/Obj/
Unity/Logs/
Unity/UserSettings/
```

これらはGitHub Repositoryには含めない．

`.gitignore` により管理する．

---

## 16. 最小動作確認

新しいPCでは，
一度にシステム全体を動かすのではなく，
以下の順序で確認する．

```text
Python 3.11.9
↓
.venv
↓
Python packages
↓
hello.py
↓
Microphone
↓
Speech Recognition
↓
TCP/IP
↓
Unity
↓
CHECKPOINT processing
```

まず，

```powershell
python hello.py
```

等の最小Pythonプログラムから確認する．

その後，

```text
Microphone
→ faster-whisper
→ JSON
→ TCP/IP
→ Unity
```

の順に確認する．

---

## 17. Repository再現性の基本方針

AI_MR_Sandboxでは，

```text
GitHub
=
Source Code
Configuration
Documentation
Checkpoint Records
```

を共有する．

一方，

```text
Python virtual environment
Unity generated files
Device-specific settings
```

は各PC上で再構築する．

したがって基本方針は，

```text
Clone
↓
Local Environment Reconstruction
↓
Dependency Installation
↓
Checkpoint Reproduction
```

とする．

---

## 18. 今後の改善

今後，Python package環境については，

```text
requirements.txt
```

をRepositoryに追加し，

```powershell
pip install -r requirements.txt
```

だけで必要なPython packageを再構築できるようにする予定である．

これにより，
複数PCおよび共同研究者間での
再現性をさらに高める．
```

今回，別PCで実際に再構築してみたことで，`Prerequisites.md` に書くべきことがかなり具体化しました．特に **Workspace Trust，`.venv` の再作成，マイクのdevice IDがPC依存，Unity Inspector参照**の4点は，単なる一般的なセットアップ説明ではなく，このプロジェクト固有の重要事項です．

そして次に `requirements.txt` を作るのが非常に自然です．これをRepositoryへ入れれば，今回手作業で行った

```powershell
pip install sounddevice numpy faster-whisper
```

も再現手順として固定できます．