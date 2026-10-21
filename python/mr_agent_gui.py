"""Run with the project's .venv Python. See ../MRConversation_README.md."""
import argparse
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from mr_agent_backend import Controller, make_server


class AgentWindow:
    def __init__(self, root, controller, server):
        self.root, self.controller, self.server = root, controller, server
        self.expanded = False
        root.title("MR Sandbox · AI_1")
        root.geometry(f"450x380+{max(20, root.winfo_screenwidth() - 490)}+60")
        root.minsize(420, 380)
        style = ttk.Style(root)
        style.theme_use("clam")
        style.configure(".", font=("Yu Gothic UI", 10), background="#f3f5f7", foreground="#182c3b")
        style.configure("TButton", padding=(10, 7))
        style.configure("Selected.TButton", background="#176b66", foreground="white")
        style.configure("Status.TLabel", font=("Yu Gothic UI", 13, "bold"))
        root.configure(background="#f3f5f7")
        body = ttk.Frame(root, padding=14)
        body.pack(fill="both", expand=True)
        top = ttk.Frame(body)
        top.pack(fill="x")
        ttk.Label(top, text="AI_1  /  MR Sandbox", font=("Yu Gothic UI", 12, "bold")).pack(side="left")
        ttk.Button(top, text="設定", command=self.settings).pack(side="right")
        self.link = ttk.Label(body, text="Unity未接続")
        self.link.pack(anchor="w", pady=(5, 8))
        modes = ttk.Frame(body)
        modes.pack(fill="x")
        self.control = ttk.Button(modes, text="操作 · Ollama", command=lambda: self.act(lambda: controller.set_mode("control")))
        self.control.pack(side="left", expand=True, fill="x", padx=(0, 4))
        self.chat = ttk.Button(modes, text="会話 · OpenAI", command=lambda: self.act(lambda: controller.set_mode("chat")))
        self.chat.pack(side="left", expand=True, fill="x", padx=(4, 0))
        self.stage = ttk.Label(body, style="Status.TLabel", wraplength=410)
        self.stage.pack(anchor="w", pady=(12, 4))
        self.summary = tk.StringVar(value="")
        tk.Label(body, textvariable=self.summary, wraplength=410, justify="left", anchor="nw", height=4,
                 font=("Yu Gothic UI", 9), background="#f3f5f7", foreground="#182c3b").pack(anchor="w", fill="x", pady=(0, 8))
        actions = ttk.Frame(body)
        actions.pack(fill="x")
        self.record = ttk.Button(actions, text="● 話す（5秒）", command=lambda: self.act(controller.begin))
        self.record.pack(side="left", fill="x", expand=True, padx=(0, 4))
        ttk.Button(actions, text="停止", command=lambda: self.act(controller.cancel)).pack(side="left")
        self.text = ttk.Entry(body)
        self.text.pack(fill="x", pady=(10, 3))
        self.text.bind("<Return>", lambda _: self.send())
        line = ttk.Frame(body)
        line.pack(fill="x")
        self.send_button = ttk.Button(line, text="文字を送信", command=self.send)
        self.send_button.pack(side="left")
        ttk.Button(line, text="パネルを前へ", command=controller.recenter_panel).pack(side="left", padx=3)
        ttk.Button(line, text="詳細", command=self.toggle).pack(side="right")
        self.topmost = tk.BooleanVar(value=False)
        ttk.Checkbutton(line, text="最前面", variable=self.topmost,
                        command=lambda: root.attributes("-topmost", self.topmost.get())).pack(side="right", padx=6)
        ttk.Label(body, text="会話の音声はAIによる合成音声です。", font=("Yu Gothic UI", 9)).pack(anchor="w", pady=(7, 0))
        self.detail = ttk.Frame(body)
        self.logs = tk.Text(self.detail, height=13, wrap="word", font=("Yu Gothic UI", 9),
                            background="#102431", foreground="#dce8ee", relief="flat", padx=8, pady=6)
        scroll = ttk.Scrollbar(self.detail, command=self.logs.yview)
        self.logs.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.logs.pack(fill="both", expand=True)
        self.last_logs = None
        root.protocol("WM_DELETE_WINDOW", self.close)
        self.refresh()

    def act(self, fn):
        try:
            fn()
        except Exception as exc:
            messagebox.showerror("MR Sandbox", str(exc), parent=self.root)

    def send(self):
        text = self.text.get().strip()
        if text:
            try:
                self.controller.begin(text)
                self.text.delete(0, "end")
            except Exception as exc:
                messagebox.showerror("MR Sandbox", str(exc), parent=self.root)

    def toggle(self):
        self.expanded = not self.expanded
        if self.expanded:
            self.detail.pack(fill="both", expand=True, pady=(10, 0))
            self.root.geometry("450x640")
        else:
            self.detail.pack_forget()
            self.root.geometry("450x380")

    def settings(self):
        window = tk.Toplevel(self.root)
        window.title("AI_1 設定")
        window.transient(self.root)
        frame = ttk.Frame(window, padding=16)
        frame.pack(fill="both", expand=True)
        with self.controller.lock:
            config = self.controller.settings.copy()
        fields = {}
        for row, (key, label) in enumerate((("device", "マイク番号"), ("chat_model", "会話モデル"), ("voice", "合成音声"), ("api_key", "OpenAI APIキー"))):
            ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", pady=6, padx=(0, 10))
            variable = tk.StringVar(value=str(config[key]))
            fields[key] = variable
            if key == "voice":
                entry = ttk.Combobox(frame, textvariable=variable, values=["coral", "alloy", "marin", "cedar", "sage"], state="readonly", width=32)
            else:
                entry = ttk.Entry(frame, textvariable=variable, width=35, show="•" if key == "api_key" else "")
            entry.grid(row=row, column=1, sticky="ew")
        ttk.Label(frame, text="キーはファイルに保存しません。GUI終了後に消去されます。\n会話では文字起こし・会話履歴をOpenAIへ送信します。\n音声APIと会話APIの利用料金が発生します。", wraplength=460).grid(row=4, columnspan=2, sticky="w", pady=10)
        mic_list = tk.Text(frame, height=6, width=65, font=("Yu Gothic UI", 9))
        mic_list.grid(row=5, columnspan=2, sticky="ew")
        try:
            import sounddevice as sd
            inputs = [f"{i}: {d['name']}" for i, d in enumerate(sd.query_devices()) if d["max_input_channels"] > 0]
            mic_list.insert("end", "入力マイク一覧\n" + "\n".join(inputs))
        except Exception as exc:
            mic_list.insert("end", "マイク一覧を取得できません: " + str(exc))
        mic_list.configure(state="disabled")

        def save():
            try:
                settings = {k: v.get().strip() for k, v in fields.items()}
                settings["device"] = int(settings["device"])
                if settings["device"] < 0 or not settings["chat_model"]:
                    raise ValueError("マイク番号とモデル名を確認してください")
                with self.controller.lock:
                    if self.controller.busy or self.controller.worker_active:
                        raise ValueError("処理終了後に設定してください")
                    self.controller.settings.update(settings)
                fields["api_key"].set("")
                window.destroy()
            except ValueError as exc:
                messagebox.showerror("設定", str(exc), parent=window)

        ttk.Button(frame, text="適用して閉じる", command=save).grid(row=6, column=1, sticky="e", pady=(12, 0))
        ttk.Button(frame, text="会話履歴を消去", command=lambda: self.act(self.controller.reset_history)).grid(row=6, column=0, sticky="w")

    def refresh(self):
        state = self.controller.snapshot()
        self.control.configure(style="Selected.TButton" if state["mode"] == "control" else "TButton")
        self.chat.configure(style="Selected.TButton" if state["mode"] == "chat" else "TButton")
        self.link.configure(text=("● Unity接続中" if state["connected"] else "○ Unity未接続") + f"  ·  マイク {self.controller.settings['device']}")
        self.stage.configure(text=state["stage"])
        summary = []
        if state["user_text"]:
            summary.append("あなた：" + state["user_text"][:65])
        if state["reply_text"]:
            summary.append("AI：" + state["reply_text"][:95])
        if state["result"]:
            summary.append(state["result"][:120])
        if state["busy"]:
            summary.append(f"経過 {state['elapsed']:.1f} 秒")
        if not state["connected"]:
            summary.append("Unityの追加機能を設定してMainを再生してください。")
        elif not state["unity_ready"]:
            summary.append("Unityの参照設定を確認: " + state["unity_info"])
        self.summary.set("\n".join(summary) if summary else "「話す」を押すと5秒間録音します。")
        enabled = not state["busy"] and state["connected"] and state["unity_ready"]
        for button in (self.record, self.send_button):
            button.configure(state="normal" if enabled else "disabled")
        logs = "\n".join(state["logs"])
        if logs != self.last_logs:
            self.logs.configure(state="normal")
            self.logs.delete("1.0", "end")
            self.logs.insert("end", logs)
            self.logs.see("end")
            self.logs.configure(state="disabled")
            self.last_logs = logs
        self.root.after(150, self.refresh)

    def close(self):
        self.controller.close()
        threading.Thread(target=self.server.shutdown, daemon=True).start()
        self.root.destroy()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", type=int, default=1)
    parser.add_argument("--port", type=int, default=50002)
    args = parser.parse_args()
    root = tk.Tk()
    controller = Controller(args.device)
    try:
        server = make_server(controller, args.port)
    except OSError:
        messagebox.showerror("起動できません", f"ポート {args.port} を使用中です。GUIを二重起動していないか確認してください。")
        root.destroy()
        return
    threading.Thread(target=server.serve_forever, daemon=True).start()
    AgentWindow(root, controller, server)
    root.mainloop()
    server.server_close()


if __name__ == "__main__":
    main()
