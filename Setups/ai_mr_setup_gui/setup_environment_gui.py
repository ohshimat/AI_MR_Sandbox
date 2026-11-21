"""AI_MR_Sandbox Windows first-PC setup assistant (stdlib-only, safe by default).
Run: py -3.11 setup_environment_gui.py
This is a companion bootstrapper, not a replacement for CH10.5-10.7 scripts.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import queue
import shutil
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import urllib.request

ROOT = Path(__file__).resolve().parent
if not (ROOT / "documents").exists():
    ROOT = Path.cwd()
HOME = Path.home()
DEFAULT_VENV = Path(os.environ.get('AI_MR_PYTHON_ENV_DIR', r'C:\AI_venvs\AI_MR_Sandbox'))
DEFAULT_RES = Path(os.environ.get('AI_MR_RESOURCE_DIR', r'C:\AI_MR_Sandbox'))
DEFAULT_WS = HOME / 'AI_MR_Workspace'

class SetupApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('AI_MR_Sandbox | 初回PCセットアップ')
        self.geometry('940x720')
        self.minsize(780, 600)
        self.root_var = tk.StringVar(value=str(ROOT))
        self.venv_var = tk.StringVar(value=str(DEFAULT_VENV))
        self.resource_var = tk.StringVar(value=str(DEFAULT_RES))
        self.workspace_var = tk.StringVar(value=str(DEFAULT_WS))
        self.status = tk.StringVar(value='初期状態：未検証')
        self.messages = queue.Queue()
        self.busy = False
        self._build()
        self.after(100, self._drain)

    def _build(self):
        main = ttk.Frame(self, padding=14)
        main.pack(fill='both', expand=True)
        ttk.Label(main, text='AI_MR_Sandbox 新規PC導入アシスタント', font=('Yu Gothic UI', 16, 'bold')).pack(anchor='w')
        ttk.Label(main, text='CH10.5 ローカルLLM → CH10.6 SDXL画像生成 → CH10.7 LoRA学習 | PC独立Python方式', wraplength=850).pack(anchor='w', pady=(4, 12))
        fields = [('リポジトリ', self.root_var), ('Python仮想環境（PC側）', self.venv_var), ('実行資源・モデル（PC側）', self.resource_var), ('成果物（ユーザー領域）', self.workspace_var)]
        paths = ttk.LabelFrame(main, text='構成パス（任意に変更可能）', padding=9)
        paths.pack(fill='x')
        for i, (label, var) in enumerate(fields):
            ttk.Label(paths, text=label).grid(row=i, column=0, sticky='w', padx=(0, 8), pady=3)
            ttk.Entry(paths, textvariable=var).grid(row=i, column=1, sticky='ew', pady=3)
            ttk.Button(paths, text='参照', command=lambda v=var: self._choose(v)).grid(row=i, column=2, padx=(8, 0), pady=3)
        paths.columnconfigure(1, weight=1)
        actions = ttk.LabelFrame(main, text='工程別の検査・準備（インストール操作は明示実行のみ）', padding=8)
        actions.pack(fill='x', pady=(12, 8))
        items = [
            ('1. 事前診断', self.diagnose),
            ('2. PC側Python環境を作成', self.make_venv),
            ('3. ワークスペース用フォルダ作成', self.make_dirs),
            ('4. Ollama / qwen3:8b 確認', self.check_ollama),
            ('5. CUDA・画像生成依存関係を確認', self.check_python),
            ('6. SDXLモデルを検出', self.check_sdxl),
            ('7. 既存画像学習GUIのセットアップを起動', self.launch_existing_setup),
            ('8. 最終診断', self.diagnose),
        ]
        for i, (name, callback) in enumerate(items):
            ttk.Button(actions, text=name, command=lambda fn=callback: self._async(fn)).grid(row=i // 2, column=i % 2, sticky='ew', padx=4, pady=4)
        actions.columnconfigure(0, weight=1)
        actions.columnconfigure(1, weight=1)
        ttk.Label(main, textvariable=self.status).pack(anchor='w', pady=(6, 3))
        logs = ttk.LabelFrame(main, text='実行記録（コピーして保存可能）', padding=6)
        logs.pack(fill='both', expand=True)
        self.log_widget = tk.Text(logs, height=14, wrap='word', font=('Consolas', 10), state='disabled')
        self.log_widget.pack(side='left', fill='both', expand=True)
        scroll = ttk.Scrollbar(logs, command=self.log_widget.yview)
        scroll.pack(side='right', fill='y')
        self.log_widget.config(yscrollcommand=scroll.set)
        ttk.Label(main, text='注意：既存の仮想環境・モデルを削除／上書きしません。外部パッケージのインストールは既存の検証済み手順を使用してください。', wraplength=890).pack(anchor='w', pady=(8, 2))

    def _choose(self, var):
        result = filedialog.askdirectory(initialdir=var.get() if Path(var.get()).exists() else str(HOME))
        if result:
            var.set(result)

    def _log(self, line):
        self.messages.put(('log', line))

    def _drain(self):
        try:
            while True:
                kind, message = self.messages.get_nowait()
                if kind == 'log':
                    self.log_widget.config(state='normal')
                    self.log_widget.insert('end', message + '\n')
                    self.log_widget.see('end')
                    self.log_widget.config(state='disabled')
                elif kind == 'status':
                    self.status.set(message)
                elif kind == 'done':
                    self.busy = False
        except queue.Empty:
            pass
        self.after(100, self._drain)

    def _async(self, callback):
        if self.busy:
            messagebox.showinfo('処理中', '現在の工程が完了してから次の操作を実行してください。')
            return
        self.busy = True
        def worker():
            self.messages.put(('status', '処理中: ' + callback.__name__))
            try:
                callback()
                self.messages.put(('status', '完了: ' + callback.__name__))
            except Exception as ex:
                self._log('ERROR: ' + str(ex))
                self.messages.put(('status', '要確認: ' + callback.__name__))
            finally:
                self.messages.put(('done', ''))
        threading.Thread(target=worker, daemon=True).start()

    def _run(self, args, cwd=None, timeout=120):
        self._log('> ' + subprocess.list2cmdline([str(x) for x in args]))
        p = subprocess.run(args, cwd=cwd, capture_output=True, text=True, errors='replace', timeout=timeout, shell=False)
        if p.stdout.strip(): self._log(p.stdout.strip()[-6000:])
        if p.stderr.strip(): self._log(p.stderr.strip()[-2000:])
        self._log('終了コード: ' + str(p.returncode))
        return p.returncode == 0

    def _python(self):
        return Path(self.venv_var.get()) / 'Scripts' / 'python.exe'

    def diagnose(self):
        root = Path(self.root_var.get())
        self._log('=== 事前・最終診断 ===')
        self._log('リポジトリ存在: ' + str(root.is_dir()))
        for name in ['CH10.5-LocalLLM.md', 'CH10.6-ImageGeneration.md', 'CH10.7-ImageLearning.md']:
            self._log(name + ': ' + ('OK' if (root / 'documents' / name).is_file() else '未検出'))
        for cmd in ['git', 'py', 'nvidia-smi', 'ollama']:
            self._log(cmd + ': ' + (shutil.which(cmd) or '未検出'))
        self._log('PC側Python: ' + ('OK' if self._python().is_file() else '未作成'))
        self._log('資源ディレクトリ: ' + str(Path(self.resource_var.get())))
        self._log('成果物ディレクトリ: ' + str(Path(self.workspace_var.get())))
        if shutil.which('py'):
            self._run(['py', '-3.11', '--version'], timeout=20)

    def make_venv(self):
        dst = Path(self.venv_var.get())
        exe = dst / 'Scripts' / 'python.exe'
        if exe.exists():
            self._log('既存Python環境を保持: ' + str(exe))
            self._run([str(exe), '--version'], timeout=30)
            return
        if dst.exists() and any(dst.iterdir()):
            raise RuntimeError('既存の非空ディレクトリを上書きしません: ' + str(dst))
        if not shutil.which('py'):
            raise RuntimeError('Python Launcher (py) がありません。Python 3.11を導入してください。')
        self._run(['py', '-3.11', '--version'], timeout=20) or self._fail('Python 3.11を検出できません')
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not self._run(['py', '-3.11', '-m', 'venv', str(dst)], timeout=180):
            raise RuntimeError('venvの作成に失敗。中途生成ディレクトリは自動削除しません。')

    def _fail(self, message):
        raise RuntimeError(message)

    def make_dirs(self):
        resource = Path(self.resource_var.get())
        workspace = Path(self.workspace_var.get())
        dirs = [resource / 'models' / 'huggingface', resource / 'models' / 'sdxl', resource / 'runtime' / 'image_gui_packages', resource / 'runtime' / 'image_training_packages', resource / 'temp', workspace / 'generated', workspace / 'training', workspace / 'lora_outputs', workspace / 'gui_records', workspace / 'gui_state']
        self._log('作成対象: ' + ', '.join(map(str, dirs)))
        for p in dirs: p.mkdir(parents=True, exist_ok=True)
        self._log('既存データを保持しつつフォルダを準備しました')

    def check_ollama(self):
        self._log('=== CH10.5 / Ollama ===')
        if shutil.which('ollama'):
            self._run(['ollama', '--version'], timeout=20)
            self._run(['ollama', 'list'], timeout=30)
        else:
            self._log('Ollama CLI未検出。公式のインストーラによる導入が必要です。')
        try:
            with urllib.request.urlopen('http://127.0.0.1:11434/api/tags', timeout=3) as res:
                data = json.load(res)
            models = [x.get('name', '') for x in data.get('models', [])]
            self._log('ローカルAPI接続: OK / モデル: ' + ', '.join(models))
            if not any(m.lower().startswith('qwen3:8b') for m in models):
                self._log('qwen3:8b 未検出。導入する場合: ollama pull qwen3:8b （ダウンロードあり）')
        except Exception as e:
            self._log('ローカルAPI未接続: ' + str(e))

    def check_python(self):
        self._log('=== CH10.6 / CUDA・依存関係 ===')
        exe = self._python()
        if not exe.is_file():
            raise RuntimeError('PC側Python環境がありません。工程2を先に実行してください。')
        code = "import importlib.util,json; names=['torch','diffusers','transformers','peft','accelerate','huggingface_hub','gradio']; print(json.dumps({x:bool(importlib.util.find_spec(x)) for x in names})); import torch; print('CUDA available:',torch.cuda.is_available()); print('Torch:',torch.__version__)"
        self._run([str(exe), '-c', code], timeout=90)
        self._log('欠けている依存パッケージはCH10.6/10.7の検証済み手順で導入してください。')
        if shutil.which('nvidia-smi'):
            self._run(['nvidia-smi', '--query-gpu=name,memory.total,driver_version', '--format=csv,noheader'], timeout=20)

    def check_sdxl(self):
        self._log('=== CH10.6/10.7 / SDXL Base 1.0 ===')
        r = Path(self.resource_var.get())
        candidates = [r / 'models' / 'sdxl' / 'stable-diffusion-xl-base-1.0']
        cache = r / 'models' / 'huggingface' / 'models--stabilityai--stable-diffusion-xl-base-1.0' / 'snapshots'
        if cache.exists(): candidates.extend(x for x in cache.iterdir() if x.is_dir())
        wcache = Path(self.workspace_var.get()) / 'models' / 'huggingface' / 'models--stabilityai--stable-diffusion-xl-base-1.0' / 'snapshots'
        if wcache.exists(): candidates.extend(x for x in wcache.iterdir() if x.is_dir())
        found = []
        for p in candidates:
            if (p / 'model_index.json').is_file():
                found.append(str(p))
        self._log('モデル候補: ' + (', '.join(found) if found else '未検出'))
        self._log('検出はmodel_index.jsonのみの簡易検査です。FP16重みや動作成功は別途検証が必要です。')
        if not found: self._log('SDXLは自動ダウンロードしません。モデルのライセンス・保存先を確認して導入してください。')

    def launch_existing_setup(self):
        root = Path(self.root_var.get())
        script = root / 'setup_image_learning_gui.cmd'
        if not script.is_file():
            raise RuntimeError('既存セットアップがありません: ' + str(script))
        self._log('既存セットアップ: ' + str(script))
        self._log('注意: このスクリプトには既定のC側パスがある可能性があります。新規に指定したパスを使用する保証はありません。')
        # Do not run uninspected install scripts inside GUI. Let user review independently.
        self._log('安全のため自動実行は行いません。内容を確認後、リポジトリ直下のPowerShellで次を実行してください: .\\setup_image_learning_gui.cmd')

if __name__ == '__main__':
    if os.name != 'nt':
        print('Windows専用GUIです。')
        sys.exit(2)
    SetupApp().mainloop()
