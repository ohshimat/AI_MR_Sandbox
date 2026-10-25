from __future__ import annotations

from pathlib import Path

from core.config import load_config, merged_settings
from core.controller import AppController


APP_CSS = """
.status-card { border-left: 6px solid #3b82f6; padding-left: 12px; }
.warning-card { border-left: 6px solid #f59e0b; padding-left: 12px; }
.generation-wait-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 18px;
  border: 1px solid #60a5fa;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.12), rgba(14, 165, 233, 0.06));
}
.generation-spinner {
  width: 34px;
  height: 34px;
  flex: 0 0 auto;
  border: 4px solid rgba(96, 165, 250, 0.28);
  border-top-color: #2563eb;
  border-radius: 50%;
  animation: generation-spin 0.9s linear infinite;
}
.generation-wait-copy { flex: 1; min-width: 0; }
.generation-wait-title { font-weight: 700; font-size: 1.02rem; }
.generation-wait-note { margin-top: 3px; opacity: 0.78; font-size: 0.92rem; }
.generation-progress-track {
  position: relative;
  height: 5px;
  margin-top: 10px;
  overflow: hidden;
  border-radius: 999px;
  background: rgba(96, 165, 250, 0.22);
}
.generation-progress-track::after {
  content: "";
  position: absolute;
  top: 0;
  bottom: 0;
  width: 38%;
  border-radius: inherit;
  background: linear-gradient(90deg, #2563eb, #38bdf8);
  animation: generation-progress 1.35s ease-in-out infinite;
}
@keyframes generation-spin { to { transform: rotate(360deg); } }
@keyframes generation-progress {
  from { transform: translateX(-110%); }
  to { transform: translateX(300%); }
}
@media (prefers-reduced-motion: reduce) {
  .generation-spinner, .generation-progress-track::after { animation-duration: 2.8s; }
}
footer { display: none !important; }
"""


def generation_is_waiting(controller) -> bool:
    """Return whether the current foreground job is image generation."""

    snapshot = controller.jobs.snapshot()
    return snapshot.operation == "画像生成" and snapshot.state in {
        "starting",
        "running",
        "stopping",
    }


def create_caption_select_handler(controller, select_data_type):
    """Create a Gallery callback with a concrete Gradio event annotation.

    This module uses postponed annotations, while Gradio discovers injected event
    arguments from the runtime class. Assigning the concrete class prevents the
    event from being treated as a normal component input.
    """

    def on_caption_image_select(directory, evt):
        return controller.select_caption_image(directory, evt.index)

    on_caption_image_select.__annotations__ = {
        "directory": str,
        "evt": select_data_type,
    }
    return on_caption_image_select


def build_app():
    try:
        import gradio as gr
    except ImportError as error:
        raise SystemExit(
            "Gradioが未導入です。install_gui_dependencies.cmdを実行してください。"
        ) from error

    config = merged_settings(load_config())
    controller = AppController(config)
    ui = config["ui_defaults"]
    training = config["training"]
    generation = config["generation"]
    fixed_generation = {
        key: value
        for key, value in generation.items()
        if key not in {"width", "height"}
    }

    def refresh_checkpoint_choices(output_dir, image_count, repetitions, mode):
        report, choices, selected = controller.checkpoint_choices(output_dir)
        target, plan = controller.recalculate_training_plan(
            image_count, repetitions, mode, selected or ""
        )
        return (
            report,
            gr.update(choices=choices, value=selected),
            target,
            plan,
        )

    with gr.Blocks(title=config["app"]["title"]) as demo:
        gr.Markdown(
            "# AI画像学習・生成GUI\n"
            "SDXL BaseとDreamBooth LoRAを使用する、研究用の完全ローカル実験画面です。"
        )
        gr.Markdown(
            "実在人物の画像は、本人の同意と研究倫理上の手続きを確認して使用してください。",
            elem_classes="warning-card",
        )
        status = gr.Markdown(
            "## ✅ 準備完了\n\n状態：`idle`  \n処理：`なし`",
            elem_classes="status-card",
        )

        with gr.Tab("学習"):
            gr.Markdown(
                "学習画像を検査し、SDXL Baseから新しいLoRAを作るか、"
                "既存のcheckpointから継続します。"
            )
            training_image_dir = gr.Textbox(
                label="学習画像フォルダ",
                value=ui["training_image_dir"],
                lines=1,
            )
            with gr.Row():
                inspect_button = gr.Button("画像を検査", variant="secondary")
                checkpoint_button = gr.Button("checkpointを確認", variant="secondary")
            dataset_report = gr.Markdown("画像を検査すると結果が表示されます。")

            with gr.Accordion("詳細学習モード：個別キャプション編集", open=True):
                gr.Markdown(
                    "学習画像を一覧から選び、画像ごとの説明を直接入力します。"
                    "保存すると画像と同じフォルダへ、同じ基本ファイル名の `.txt` を作成します。"
                )
                load_caption_button = gr.Button(
                    "画像一覧とキャプションを読み込む", variant="secondary"
                )
                caption_gallery = gr.Gallery(
                    label="学習画像ブラウザ",
                    columns=5,
                    rows=2,
                    height=360,
                    allow_preview=False,
                    interactive=False,
                    object_fit="cover",
                )
                selected_caption_image = gr.State("")
                with gr.Row():
                    caption_preview = gr.Image(
                        label="選択画像", type="filepath", interactive=False
                    )
                    with gr.Column():
                        caption_text = gr.Textbox(
                            label="この画像のキャプション",
                            placeholder=(
                                "例：a full-body photo of a woman wearing an "
                                "aimrsuit01 armored power suit with a helmet"
                            ),
                            lines=7,
                        )
                        save_caption_button = gr.Button(
                            "この画像のキャプションを保存", variant="primary"
                        )
                caption_report = gr.Markdown(
                    "画像一覧を読み込むと、入力済み件数と未入力件数を表示します。"
                )
                gr.Markdown(
                    "画像別キャプション方式を選ぶと、同名 `.txt` がある画像にはその内容を使用し、"
                    "未入力の画像には下の共通プロンプトを使用します。"
                )

            training_caption_mode = gr.Radio(
                ["固定プロンプト", "画像別キャプション（未入力は共通）"],
                value=ui["training_caption_mode"],
                label="学習プロンプト方式",
                info=(
                    "固定方式は全画像に共通プロンプトを使用します。画像別方式は同名.txtを優先し、"
                    "ない画像には共通プロンプトを適用します。"
                ),
            )
            training_mode = gr.Radio(
                ["新規学習", "checkpointから継続"],
                value="新規学習",
                label="学習モード",
            )
            training_output_dir = gr.Textbox(
                label="学習結果フォルダ",
                value=ui["training_output_dir"],
                lines=1,
            )
            checkpoint_report = gr.Markdown("継続学習ではcheckpointを確認してください。")
            resume_checkpoint = gr.Dropdown(
                choices=[],
                value=None,
                label="継続元checkpoint",
                info=(
                    "「checkpointを確認」で候補を読み込みます。"
                    "新規学習では選択不要です。"
                ),
                interactive=True,
            )
            gr.Markdown("#### 学習量")
            with gr.Row():
                training_image_count = gr.Number(
                    label="学習画像数（自動取得）",
                    value=0,
                    precision=0,
                    interactive=False,
                )
                training_repetitions = gr.Number(
                    label="1画像あたりの総学習回数",
                    value=ui["training_repetitions"],
                    precision=0,
                    minimum=1,
                )
                target_steps = gr.Number(
                    label="適用する最終目標ステップ",
                    value=ui["target_steps"],
                    precision=0,
                    interactive=False,
                )
            training_plan_report = gr.Markdown(
                "画像を検査すると、画像数と学習回数から目標ステップを計算します。"
            )
            training_prompt = gr.Textbox(
                label="共通／識別用学習プロンプト",
                value=ui["training_prompt"],
                lines=1,
                info=(
                    "固定方式では全画像に使用します。画像別方式でも、トリガー識別と成果物名のため入力します。"
                ),
            )
            with gr.Accordion("固定学習条件", open=False):
                gr.JSON(value=training, label="GUIから変更しない設定")
            with gr.Row():
                train_button = gr.Button("学習開始", variant="primary")
                stop_training_button = gr.Button("実行中の処理を停止", variant="stop")
            training_log = gr.Textbox(
                label="学習・生成ログ",
                value="",
                lines=18,
                max_lines=30,
                interactive=False,
            )

        with gr.Tab("画像生成"):
            gr.Markdown(
                "SDXL Baseに、1～3個のLoRAとそれぞれの係数を組み合わせて画像を生成します。"
            )
            gr.Markdown(
                "LoRA 1は必須です。LoRA 2・3は、使わない場合は空欄にします。"
                "すべて同じSDXL Base用のLoRAを選び、最初は低めの係数から試してください。"
            )
            lora_choices = controller.lora_choices()
            with gr.Row():
                lora_path = gr.Dropdown(
                    choices=lora_choices,
                    value=ui["generation_lora"],
                    allow_custom_value=True,
                    label="LoRA 1（必須）",
                )
                lora_strength = gr.Slider(
                    minimum=0.0,
                    maximum=2.0,
                    step=0.05,
                    value=ui["lora_strength"],
                    label="LoRA 1 係数",
                )
            with gr.Row():
                lora_path_2 = gr.Dropdown(
                    choices=lora_choices,
                    value=ui["generation_lora_2"],
                    allow_custom_value=True,
                    label="LoRA 2（任意）",
                )
                lora_strength_2 = gr.Slider(
                    minimum=0.0,
                    maximum=2.0,
                    step=0.05,
                    value=ui["lora_strength_2"],
                    label="LoRA 2 係数",
                )
            with gr.Row():
                lora_path_3 = gr.Dropdown(
                    choices=lora_choices,
                    value=ui["generation_lora_3"],
                    allow_custom_value=True,
                    label="LoRA 3（任意）",
                )
                lora_strength_3 = gr.Slider(
                    minimum=0.0,
                    maximum=2.0,
                    step=0.05,
                    value=ui["lora_strength_3"],
                    label="LoRA 3 係数",
                )
            refresh_lora_button = gr.Button("LoRA一覧を更新", variant="secondary")
            generation_prompt = gr.Textbox(
                label="画像生成プロンプト",
                value=ui["generation_prompt"],
                lines=5,
            )
            generation_seed = gr.Number(
                label="seed", value=ui["generation_seed"], precision=0
            )
            gr.Markdown(
                "#### 生成画像の解像度\n"
                "8GB GPUでは `512 × 512` または縦長の `512 × 768` から試してください。"
            )
            with gr.Row():
                generation_width = gr.Number(
                    label="横幅（width）",
                    value=ui["generation_width"],
                    precision=0,
                    minimum=256,
                    maximum=2048,
                )
                generation_height = gr.Number(
                    label="縦幅（height）",
                    value=ui["generation_height"],
                    precision=0,
                    minimum=256,
                    maximum=2048,
                )
            gr.Markdown(
                "横幅・縦幅は8の倍数で指定します。大きくすると処理時間とGPUメモリ使用量が増えます。"
            )
            generation_output_dir = gr.Textbox(
                label="画像生成フォルダ",
                value=ui["generation_output_dir"],
                lines=1,
            )
            with gr.Accordion("その他の固定生成条件", open=False):
                gr.JSON(value=fixed_generation, label="GUIから変更しない設定")
            with gr.Row():
                generate_button = gr.Button("画像生成", variant="primary")
                stop_generation_button = gr.Button("実行中の処理を停止", variant="stop")
            generation_wait = gr.HTML(
                """
                <div class="generation-wait-card" role="status" aria-live="polite">
                  <div class="generation-spinner" aria-hidden="true"></div>
                  <div class="generation-wait-copy">
                    <div class="generation-wait-title">画像を生成しています…</div>
                    <div class="generation-wait-note">
                      SDXL BaseとLoRAの読み込みを含むため、数分かかる場合があります。
                    </div>
                    <div class="generation-progress-track" aria-hidden="true"></div>
                  </div>
                </div>
                """,
                visible=False,
            )
            generated_image = gr.Image(label="生成画像", type="filepath")
            generation_result = gr.Markdown("生成後に結果が表示されます。")

        with gr.Tab("保存・復元"):
            gr.Markdown(
                "PC本体で完了した実験を外部ストレージへ保存し、必要なときにPCへ復元します。"
                "学習中・画像生成中は実行できません。既存フォルダへの上書きも行いません。"
            )
            with gr.Accordion("実験を外部ストレージへ保存", open=True):
                gr.Markdown(
                    "学習タブの画像フォルダと学習結果フォルダ、画像生成タブの生成フォルダを"
                    "一つの検証可能な実験データとして保存します。"
                )
                external_storage_root = gr.Textbox(
                    label="外部ストレージの保存先ルート",
                    value=ui["external_storage_root"],
                    placeholder="例：E:\\AI_MR_Archive",
                    lines=1,
                )
                archive_experiment_name = gr.Textbox(
                    label="実験名",
                    value=ui["archive_experiment_name"],
                    lines=1,
                )
                include_checkpoints = gr.Checkbox(
                    label="checkpointも保存する（継続学習が必要な場合のみ）",
                    value=False,
                )
                export_experiment_button = gr.Button(
                    "実験を外部ストレージへ保存", variant="primary"
                )

            with gr.Accordion("保存データを検査・PCへ復元", open=True):
                archive_path = gr.Textbox(
                    label="保存済み実験フォルダ",
                    value=ui["archive_path"],
                    placeholder=(
                        "例：E:\\AI_MR_Archive\\AI_MR_Research\\experiments"
                        "\\experiment_001"
                    ),
                    lines=1,
                )
                restore_pc_root = gr.Textbox(
                    label="PC側の復元先ルート",
                    value=ui["restore_pc_root"],
                    lines=1,
                )
                with gr.Row():
                    inspect_archive_button = gr.Button(
                        "保存データを検査", variant="secondary"
                    )
                    restore_experiment_button = gr.Button(
                        "実験をPCへ復元", variant="primary"
                    )
            storage_report = gr.Markdown(
                "保存または復元を実行すると、ファイル数・容量・完全性を表示します。"
            )

        with gr.Tab("環境・履歴"):
            with gr.Row():
                refresh_environment_button = gr.Button("環境を再確認")
                refresh_history_button = gr.Button("履歴を更新")
            environment_report = gr.Markdown(controller.environment_markdown())
            history_report = gr.Markdown(controller.history_markdown())

        def refresh_lora_dropdowns():
            choices = controller.lora_choices()
            return tuple(gr.Dropdown(choices=choices) for _ in range(3))

        def start_generation_with_effect(*args):
            status_text, log_text = controller.start_generation(*args)
            return (
                status_text,
                log_text,
                gr.update(visible=generation_is_waiting(controller)),
            )

        def poll_with_generation_effect():
            return (
                *controller.poll(),
                gr.update(visible=generation_is_waiting(controller)),
            )

        inspect_button.click(
            controller.inspect_training_plan,
            inputs=[
                training_image_dir,
                training_repetitions,
                training_mode,
                resume_checkpoint,
            ],
            outputs=[
                dataset_report,
                training_image_count,
                target_steps,
                training_plan_report,
            ],
            api_visibility="private",
        )
        demo.load(
            controller.inspect_training_plan,
            inputs=[
                training_image_dir,
                training_repetitions,
                training_mode,
                resume_checkpoint,
            ],
            outputs=[
                dataset_report,
                training_image_count,
                target_steps,
                training_plan_report,
            ],
            api_visibility="private",
        )
        training_image_dir.change(
            controller.inspect_training_plan,
            inputs=[
                training_image_dir,
                training_repetitions,
                training_mode,
                resume_checkpoint,
            ],
            outputs=[
                dataset_report,
                training_image_count,
                target_steps,
                training_plan_report,
            ],
            api_visibility="private",
        )
        training_repetitions.change(
            controller.recalculate_training_plan,
            inputs=[
                training_image_count,
                training_repetitions,
                training_mode,
                resume_checkpoint,
            ],
            outputs=[target_steps, training_plan_report],
            api_visibility="private",
        )
        training_mode.change(
            controller.recalculate_training_plan,
            inputs=[
                training_image_count,
                training_repetitions,
                training_mode,
                resume_checkpoint,
            ],
            outputs=[target_steps, training_plan_report],
            api_visibility="private",
        )
        resume_checkpoint.change(
            controller.recalculate_training_plan,
            inputs=[
                training_image_count,
                training_repetitions,
                training_mode,
                resume_checkpoint,
            ],
            outputs=[target_steps, training_plan_report],
            api_visibility="private",
        )
        checkpoint_button.click(
            refresh_checkpoint_choices,
            inputs=[
                training_output_dir,
                training_image_count,
                training_repetitions,
                training_mode,
            ],
            outputs=[
                checkpoint_report,
                resume_checkpoint,
                target_steps,
                training_plan_report,
            ],
            api_visibility="private",
        )
        load_caption_button.click(
            controller.load_caption_browser,
            inputs=[training_image_dir],
            outputs=[
                caption_gallery,
                selected_caption_image,
                caption_preview,
                caption_text,
                caption_report,
            ],
            api_visibility="private",
        )

        caption_gallery.select(
            create_caption_select_handler(controller, gr.SelectData),
            inputs=[training_image_dir],
            outputs=[
                selected_caption_image,
                caption_preview,
                caption_text,
                caption_report,
            ],
            api_visibility="private",
        )
        save_caption_button.click(
            controller.save_caption,
            inputs=[training_image_dir, selected_caption_image, caption_text],
            outputs=[caption_gallery, caption_text, caption_report],
            api_visibility="private",
        )
        train_button.click(
            controller.start_training,
            inputs=[
                training_image_dir,
                training_mode,
                training_output_dir,
                resume_checkpoint,
                training_repetitions,
                training_prompt,
                training_caption_mode,
            ],
            outputs=[status, training_log],
            api_visibility="private",
            concurrency_limit=1,
            concurrency_id="gpu_job",
        )
        generate_button.click(
            start_generation_with_effect,
            inputs=[
                lora_path,
                lora_strength,
                lora_path_2,
                lora_strength_2,
                lora_path_3,
                lora_strength_3,
                generation_prompt,
                generation_seed,
                generation_width,
                generation_height,
                generation_output_dir,
            ],
            outputs=[status, training_log, generation_wait],
            api_visibility="private",
            concurrency_limit=1,
            concurrency_id="gpu_job",
        )
        stop_training_button.click(
            controller.stop,
            outputs=[status, training_log],
            api_visibility="private",
            queue=False,
        )
        stop_generation_button.click(
            controller.stop,
            outputs=[status, training_log],
            api_visibility="private",
            queue=False,
        )
        refresh_lora_button.click(
            refresh_lora_dropdowns,
            outputs=[lora_path, lora_path_2, lora_path_3],
            api_visibility="private",
        )
        export_experiment_button.click(
            controller.export_experiment,
            inputs=[
                training_image_dir,
                training_output_dir,
                generation_output_dir,
                external_storage_root,
                archive_experiment_name,
                include_checkpoints,
            ],
            outputs=[storage_report],
            api_visibility="private",
            concurrency_limit=1,
            concurrency_id="storage_job",
        )
        inspect_archive_button.click(
            controller.inspect_experiment_archive,
            inputs=[archive_path],
            outputs=[storage_report],
            api_visibility="private",
            concurrency_limit=1,
            concurrency_id="storage_job",
        )
        restore_experiment_button.click(
            controller.restore_experiment,
            inputs=[
                archive_path,
                restore_pc_root,
                training_image_dir,
                training_output_dir,
                generation_output_dir,
            ],
            outputs=[
                storage_report,
                training_image_dir,
                training_output_dir,
                generation_output_dir,
            ],
            api_visibility="private",
            concurrency_limit=1,
            concurrency_id="storage_job",
        )
        refresh_environment_button.click(
            controller.environment_markdown,
            outputs=[environment_report],
            api_visibility="private",
        )
        refresh_history_button.click(
            controller.history_markdown,
            outputs=[history_report],
            api_visibility="private",
        )

        timer = gr.Timer(value=1.0, active=True)
        timer.tick(
            poll_with_generation_effect,
            outputs=[
                status,
                training_log,
                generated_image,
                generation_result,
                history_report,
                generation_wait,
            ],
            api_visibility="private",
            queue=False,
            show_progress="hidden",
        )

    return demo, config


def main() -> None:
    demo, config = build_app()
    demo.queue(default_concurrency_limit=2).launch(
        server_name=config["app"]["server_name"],
        server_port=int(config["app"]["server_port"]),
        share=bool(config["app"]["share"]),
        inbrowser=True,
        show_error=True,
        css=APP_CSS,
        allowed_paths=[str(Path(config["paths"]["preview_cache"]).resolve())],
    )


if __name__ == "__main__":
    main()
