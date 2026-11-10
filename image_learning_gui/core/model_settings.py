from __future__ import annotations

import os

MODEL_ENVIRONMENT_VARIABLE = 'AI_MR_SDXL_MODEL_PATH'


def read_user_model_path() -> str | None:
    """Read persisted settings when the parent process has no explicit override."""
    if os.name != 'nt':
        return None
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Environment') as key:
            value, kind = winreg.QueryValueEx(key, MODEL_ENVIRONMENT_VARIABLE)
        if kind in (winreg.REG_SZ, winreg.REG_EXPAND_SZ) and isinstance(value, str):
            return os.path.expandvars(value) if kind == winreg.REG_EXPAND_SZ else value
    except OSError:
        pass
    return None


def notify_environment_change() -> bool:
    """Notify Windows launchers; existing terminal processes retain their own env."""
    import ctypes
    from ctypes import wintypes
    send = ctypes.WinDLL('user32', use_last_error=True).SendMessageTimeoutW
    send.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM,
                     wintypes.UINT, wintypes.UINT, ctypes.POINTER(ctypes.c_size_t)]
    send.restype = wintypes.LPARAM
    result = ctypes.c_size_t()
    value = ctypes.create_unicode_buffer('Environment')
    return bool(send(0xFFFF, 0x001A, 0, ctypes.cast(value, ctypes.c_void_p).value,
                     0x0002, 1000, ctypes.byref(result)))


def save_user_model_path(path: str) -> bool:
    """Write only HKCU Environment, then update this process. No shell commands."""
    if os.name != 'nt':
        raise OSError('モデルの環境変数保存はローカルWindows専用です。')
    import winreg
    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, 'Environment', 0, winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(key, MODEL_ENVIRONMENT_VARIABLE, 0, winreg.REG_SZ, path)
    os.environ[MODEL_ENVIRONMENT_VARIABLE] = path
    try:
        return notify_environment_change()
    except OSError:
        return False
