もちろんです。今回の「まっさらなPCからcloneして動作確認」までの実体験を反映した、更新版 `Prerequisites.md` の文案をまとめます。

特に今回は、**Workspace Trust、PowerShell Execution Policy、`.unity` / `.meta` のGit管理、Unity 6000.0.31f1、Python依存関係の再導入**を明示的に追加しています。

````markdown
# Prerequisites
## AI_MR_Sandbox Development Environment

この文書は，AI_MR_Sandboxを新しいWindows PC上で再構築し，
GitHubからcloneしたリソースを再現するための前提環境と手順を記録する．

本プロジェクトでは，

```text
GitHub
=
Source Code
Unity Scene
Configuration
Documentation
Checkpoint Records
````

を共有し，

```text
Python virtual environment
Unity generated files
Device-specific settings
```

は各PC上で再構築する．

---

## 1. Baseline Environment

現時点の基準環境は以下とする．

```text
OS              : Windows
Editor          : Visual Studio Code
Python          : 3.11.9
Unity           : 6000.0.31f1
Version Control : Git / GitHub
```

CHECKPOINT-1からCHECKPOINT-7までのテストコンテンツは，

```text
Unity 6000.0.31f1
Python 3.11.9
```

を基準として動作確認している．

再現性確認では，
まず同じバージョンを使用する．

Unityを最新版へ更新する場合は，
基準環境で動作確認した後に，
別branchまたはProject copyで検証することを推奨する．

---

## 2. Visual Studio Code

Visual Studio Codeをインストールする．

### 2.1 日本語化

Extensionsから，

```text
Japanese Language Pack for Visual Studio Code
```

を検索し，
Microsoft製Extensionをインストールする．

インストール後，
表示言語を日本語へ変更し，
VS Codeを再起動する．

---

## 3. VS Code Theme

視認性を考慮し，
明るいテーマを使用する．

現在は，

```text
Light Modern
```

等のLight Themeを使用している．

変更：

```text
ファイル
→ ユーザー設定
→ テーマ
→ 配色テーマ
```

---

## 4. Workspace Trust

VS Codeでは，
Workspaceが信頼されていない場合，

```text
Restricted Mode
制限モード
```

となり，
Python Extensionや一部Commandが正常に動作しない場合がある．

Command Palette：

```text
Ctrl + Shift + P
```

から，

```text
Workspaces: Manage Workspace Trust
```

または，

```text
ワークスペースの信頼を管理
```

を開き，
自分で管理しているAI_MR_Sandbox Repositoryを信頼する．

---

## 5. Python

Python 3.11.9をインストールする．

他のPython versionが共存していてもよいが，
本Projectでは，

```text
Python 3.11.9
```

をBaselineとする．

確認：

```powershell
python --version
```

期待値：

```text
Python 3.11.9
```

---

## 6. VS Code Python Extension

VS Code Extensionsから，

```text
Python
```

を検索し，

```text
Microsoft
ms-python.python
```

をインストールする．

必要に応じてPylance等が同時に導入されても問題ない．

Command Palette：

```text
Ctrl + Shift + P
```

から，

```text
Python: インタープリターを選択
```

を実行し，

```text
Python 3.11.9
```

を選択する．

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

---

## 8. GitHub Repository

Repository：

```text
https://github.com/ohshimat/AI_MR_Sandbox
```

Clone URL：

```text
https://github.com/ohshimat/AI_MR_Sandbox.git
```

VS Codeから，

```text
Ctrl + Shift + P
→ Git: Clone
```

を選択する．

保存先には，
Repositoryそのものではなく
親フォルダを指定する．

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

## 9. Python Virtual Environment

Python仮想環境 `.venv` はGitHubでは共有しない．

各PC上で新規に作成する．

Repository rootで，

```powershell
python -m venv .venv
```

を実行する．

---

## 10. PowerShell Execution Policy

Windows PowerShellでは，

```powershell
.venv\Scripts\Activate.ps1
```

を実行した際，

```text
PSSecurityException
このシステムではスクリプトの実行が無効になっている
```

というエラーが出る場合がある．

この場合，
Current Userに対して，

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

を実行する．

確認を求められた場合は，

```text
Y
```

を入力する．

その後，
VS Code Terminalを一度閉じ，
新しいPowerShell Terminalを開く．

再度，

```powershell
.venv\Scripts\Activate.ps1
```

を実行する．

成功すると，

```text
(.venv)
```

がTerminalの先頭に表示される．

`Unrestricted` や恒久的な `Bypass` は使用しない．

---

## 11. .venv 再作成時の注意

すでに `.venv` が有効な状態で，

```powershell
python -m venv .venv
```

を実行すると，

```text
Permission denied:
...\.venv\Scripts\python.exe
```

が出る場合がある．

この場合は，

```powershell
deactivate
```

を実行する．

その後 `.venv` フォルダを削除し，

```powershell
python -m venv .venv
```

を再実行する．

`.venv` は各PC固有のローカル環境であり，
削除・再作成して問題ない．

---

## 12. Python Dependencies

CHECKPOINT-1からCHECKPOINT-7までのPython側実装では，
少なくとも以下を使用する．

```text
sounddevice
numpy
faster-whisper
```

`.venv` を有効化した状態で，

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

## 13. requirements.txt

将来的には，

```text
requirements.txt
```

をRepositoryに含め，

```powershell
pip install -r requirements.txt
```

で依存関係を再構築できるようにする．

これにより，
複数PCおよび共同研究者間での
Python環境再現性を向上させる．

---

## 14. Microphone

音声認識では，
使用するAudio Input Deviceを確認する必要がある．

Microphoneのdevice IDは
PCごとに異なる可能性がある．

したがって，

```text
device_id = 7
```

等の値を別PCへそのままコピーしない．

`python-sounddevice` 等でAudio Device一覧を取得し，
使用するMicrophoneを確認する．

device IDは環境依存パラメータとして扱う．

---

## 15. Unity Version

現在のBaseline：

```text
Unity 6000.0.31f1
```

CHECKPOINT-1からCHECKPOINT-7までの
Unity Test Contentは，
このversionで確認している．

新しいPCで再現する場合は，
まず同じversionをUnity Hubから導入する．

Projectを別versionで開く前に，
Baseline versionでの動作を確認する．

---

## 16. Unity Project

Repository内のUnity Project：

```text
unity/SpeechReceiver
```

をUnity Hubから開く．

Unity初回起動時には，

```text
Library
Temp
Obj
Logs
```

等が再生成される．

これらはGit管理しない．

---

## 17. Unity Scene

CHECKPOINT-1からCHECKPOINT-7までのSceneは，

```text
unity/SpeechReceiver/Assets/MyWork/SandboxScene.unity
```

として保存する．

Scene fileと同時に，

```text
SandboxScene.unity.meta
```

もGit管理する．

重要：

```text
.unity
.meta
```

は，
Unity Sceneを別PCで再現するために必要である．

C# Scriptのみでは，
HierarchyやInspector Referenceは再現できない．

---

## 18. SceneをGit管理する重要性

Scene fileがRepositoryに含まれていない場合，
別PCでProjectを開いても，

```text
SpeechReceiver
Human_1
AI_1
Permission
Verification
HumanEvaluation
Experience
```

等のHierarchyは再現されない．

また，
Component間のInspector Referenceも
Sceneに保存される．

したがって，
Unity Sceneは
Checkpoint Runtime構成そのものとして扱う．

---

## 19. Unity Inspector References

CHECKPOINT-7時点の主要な参照関係：

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

Clone後，
Inspectorで参照が維持されているか確認する．

特に，

```text
SpeechReceiver
└─ TcpSpeechReceiver
     ├─ Permission Checker → Permission
     └─ Action Verifier    → Verification
```

```text
Verification
└─ ActionVerifier
     └─ Human Evaluator → HumanEvaluation
```

```text
HumanEvaluation
└─ HumanEvaluator
     └─ Experience Logger → Experience
```

を確認する．

`None` になっている場合，
コードにエラーがなくても
一部処理が実行されない場合がある．

---

## 20. Gitで共有するもの

原則として，
以下はRepositoryへ含める．

```text
Assets/
ProjectSettings/
Packages/
*.unity
*.unity.meta
C# Scripts
Python Scripts
CHECKPOINT-*.md
Prerequisites.md
```

Unity Sceneとmetaは必ず共有する．

---

## 21. Gitで共有しないもの

以下は各PCで再生成する．

```text
.venv/
__pycache__/

Unity Library/
Unity Temp/
Unity Obj/
Unity Logs/
Unity UserSettings/
```

`.gitignore` により除外する．

---

## 22. Git Statusの確認

Scene等を追加した後，

```powershell
git status
```

を確認する．

例えば，

```text
Untracked files:
    SandboxScene.unity
    SandboxScene.unity.meta
```

と表示されている場合，
まだGit管理されていない．

追加：

```powershell
git add <file>
```

確認：

```powershell
git status
```

Commit後，

```text
nothing to commit, working tree clean
```

となれば，
ローカル作業ツリーに未反映変更はない．

---

## 23. Baseline Reproduction Test

新しいPCでは，
以下の順序で確認する．

```text
VS Code
↓
Workspace Trust
↓
Python 3.11.9
↓
Git Clone
↓
.venv
↓
PowerShell Execution Policy
↓
Python Dependencies
↓
Unity 6000.0.31f1
↓
SandboxScene.unity
↓
Inspector References
↓
Python Runtime
↓
Unity Runtime
```

一度に全体を確認せず，
小さい単位から進める．

---

## 24. Minimal Python Test

まず，

```powershell
python hello.py
```

等の最小Programを実行する．

次に，

```text
Microphone
↓
Speech Recognition
↓
JSON
↓
TCP/IP
↓
Unity
```

の順に確認する．

---

## 25. Reproduction Result

別PCにおいて，

```text
GitHub Clone
↓
Python 3.11.9
↓
.venv
↓
Python Dependencies
↓
Unity 6000.0.31f1
↓
SandboxScene.unity
↓
Runtime Test
```

まで実施し，
GitHubからcloneしたリソースが動作することを確認した．

これにより，
CHECKPOINT-1からCHECKPOINT-7までの実装が，
特定の1台のPCだけに依存せず，
別PC上で再構築可能であることを確認した．

---

## 26. Reproducibility Policy

AI_MR_Sandboxの再現性は，

```text
Repository
+
Prerequisites
+
Dependency Definition
+
Unity Scene
+
Inspector References
+
Device-specific Configuration
```

を含めて成立するものとする．

単にSource CodeがGitHubに存在するだけでは，
Runtime Environment全体の再現性は保証されない．

---

## 27. Future Extension

CHECKPOINT-8以降では，
独立したC/C++ AIR Managerを追加する予定である．

そのため今後，

```text
C/C++ compiler
Build environment
TCP/IP ports
AIR Manager executable
```

等もPrerequisitesへ追加する予定である．

```

今回の更新版では，単なる「インストール手順」ではなく，**実際に別PCで再現性テストを行って判明した注意事項**まで入れています。

特に重要なのは，`SandboxScene.unity` と `.meta` を含めた点です。ここは今回のテストで初めて明確になった、かなり重要な知見です。

次に進めるなら，`requirements.txt` も同時に作っておくと，`Prerequisites.md` のPython依存関係部分がかなり簡潔になります。
```
