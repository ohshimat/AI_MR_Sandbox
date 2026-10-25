from __future__ import annotations

import os
import subprocess
import threading
from collections import deque
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

from .records import iso_now


@dataclass(frozen=True)
class JobSnapshot:
    job_id: str | None
    operation: str | None
    state: str
    started_at: str | None
    finished_at: str | None
    return_code: int | None
    log_path: str | None
    message: str
    log_tail: str

    def to_dict(self) -> dict:
        return asdict(self)


class JobBusyError(RuntimeError):
    pass


class ProcessManager:
    """Own exactly one long-running local GPU child process."""

    def __init__(self, max_log_lines: int = 3000) -> None:
        self._lock = threading.RLock()
        self._process: subprocess.Popen[str] | None = None
        self._thread: threading.Thread | None = None
        self._lines: deque[str] = deque(maxlen=max_log_lines)
        self._job_id: str | None = None
        self._operation: str | None = None
        self._state = "idle"
        self._started_at: str | None = None
        self._finished_at: str | None = None
        self._return_code: int | None = None
        self._log_path: Path | None = None
        self._message = "準備完了"
        self._stop_requested = False

    @property
    def busy(self) -> bool:
        with self._lock:
            return self._state in {"starting", "running", "stopping"}

    def start(
        self,
        *,
        job_id: str,
        operation: str,
        command: list[str],
        cwd: str | Path,
        environment: dict[str, str],
        log_path: str | Path,
        on_complete: Callable[[JobSnapshot], None] | None = None,
    ) -> JobSnapshot:
        with self._lock:
            if self.busy:
                raise JobBusyError("別の学習または画像生成処理が実行中です。")

            self._job_id = job_id
            self._operation = operation
            self._state = "starting"
            self._started_at = iso_now()
            self._finished_at = None
            self._return_code = None
            self._lines.clear()
            self._message = f"{operation}を開始しています。"
            self._stop_requested = False
            self._log_path = Path(log_path)
            self._log_path.parent.mkdir(parents=True, exist_ok=True)

            creationflags = 0
            if os.name == "nt":
                creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW

            try:
                self._process = subprocess.Popen(
                    command,
                    cwd=str(Path(cwd)),
                    env=environment,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    bufsize=1,
                    shell=False,
                    creationflags=creationflags,
                )
            except Exception as error:
                self._state = "failed"
                self._finished_at = iso_now()
                self._message = f"子プロセスを開始できませんでした: {error}"
                self._lines.append(self._message)
                raise
            self._state = "running"
            self._message = f"{operation}を実行中です。"
            self._thread = threading.Thread(
                target=self._monitor,
                args=(on_complete,),
                name=f"job-{job_id}",
                daemon=True,
            )
            self._thread.start()
            return self.snapshot()

    def _monitor(self, on_complete: Callable[[JobSnapshot], None] | None) -> None:
        assert self._process is not None
        process = self._process
        log_path = self._log_path
        try:
            assert process.stdout is not None
            assert log_path is not None
            with log_path.open("a", encoding="utf-8") as log_file:
                for line in process.stdout:
                    clean = line.rstrip("\r\n")
                    with self._lock:
                        self._lines.append(clean)
                    log_file.write(line)
                    log_file.flush()
            return_code = process.wait()
            with self._lock:
                self._return_code = return_code
                self._finished_at = iso_now()
                if self._stop_requested:
                    self._state = "stopped"
                    self._message = "処理を停止しました。"
                elif return_code == 0:
                    self._state = "succeeded"
                    self._message = f"{self._operation}が完了しました。"
                else:
                    self._state = "failed"
                    self._message = (
                        f"{self._operation}が終了コード{return_code}で失敗しました。"
                    )
        except Exception as error:
            with self._lock:
                self._state = "failed"
                self._finished_at = iso_now()
                self._message = f"処理監視中にエラーが発生しました: {error}"
                self._lines.append(self._message)
        finally:
            snapshot = self.snapshot()
            if on_complete is not None:
                try:
                    on_complete(snapshot)
                except Exception as error:
                    with self._lock:
                        self._state = "failed"
                        self._message = f"完了処理に失敗しました: {error}"
                        self._lines.append(self._message)

    def stop(self) -> JobSnapshot:
        with self._lock:
            if not self.busy or self._process is None:
                self._message = "停止対象の処理はありません。"
                return self.snapshot()
            process = self._process
            self._stop_requested = True
            self._state = "stopping"
            self._message = "停止処理中です。"

        if process.poll() is None:
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
            else:
                process.terminate()
        return self.snapshot()

    def snapshot(self) -> JobSnapshot:
        with self._lock:
            return JobSnapshot(
                job_id=self._job_id,
                operation=self._operation,
                state=self._state,
                started_at=self._started_at,
                finished_at=self._finished_at,
                return_code=self._return_code,
                log_path=str(self._log_path) if self._log_path else None,
                message=self._message,
                log_tail="\n".join(self._lines),
            )
