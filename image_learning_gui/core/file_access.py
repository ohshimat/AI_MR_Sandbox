from __future__ import annotations

import json
import os
import struct
import threading
from pathlib import Path

_DIALOG_LOCK = threading.Lock()
EXTENSIONS = {'.json', '.log', '.png', '.jpg', '.jpeg', '.safetensors'}


def require_windows():
    if os.name != 'nt':
        raise OSError('この操作はローカルWindows環境専用です。')


def choose_folder(current):
    """Create and destroy Tk on the same callback thread; cancel preserves input."""
    require_windows()
    import tkinter as tk
    from tkinter import filedialog
    with _DIALOG_LOCK:
        root = tk.Tk()
        root.withdraw()
        try:
            root.attributes('-topmost', True)
            initial = Path(current).expanduser() if current else Path.home()
            while not initial.is_dir() and initial != initial.parent:
                initial = initial.parent
            selected = filedialog.askdirectory(
                parent=root, title='フォルダーを選択', initialdir=str(initial), mustexist=True
            )
            return str(Path(selected).resolve(strict=True)) if selected else current
        finally:
            root.destroy()


def checked_path(value, roots):
    path = Path(value).expanduser().resolve(strict=True)
    if not any(path.is_relative_to(Path(root).expanduser().resolve()) for root in roots):
        raise ValueError('許可ルート外のファイルです。')
    if not path.is_file() or path.suffix.lower() not in EXTENSIONS:
        raise ValueError('未対応のファイルです。')
    return path


def read_content(path):
    if path.suffix.lower() == '.safetensors':
        with path.open('rb') as stream:
            raw = stream.read(8)
            if len(raw) != 8:
                raise ValueError('safetensorsヘッダーが不正です。')
            size = struct.unpack('<Q', raw)[0]
            if size > 8 * 1024 * 1024 or size > path.stat().st_size - 8:
                raise ValueError('safetensorsヘッダーのサイズが不正です。')
            header = json.loads(stream.read(size))
        return json.dumps(header, ensure_ascii=False, indent=2)
    with path.open('rb') as stream:
        raw = stream.read(1024 * 1024 + 1)
    text = raw[:1024 * 1024].decode('utf-8-sig', errors='replace')
    return text + ('\n（1 MiBで表示を省略）' if len(raw) > 1024 * 1024 else '')


def open_local(path, folder=False):
    require_windows()
    # Fixed, validated document types only. Never interpolate shell commands.
    os.startfile(str(path.parent if folder else path))
