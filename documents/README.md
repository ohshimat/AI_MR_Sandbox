Unity: SpeechReceiver_v3_prefab
py: speech_to_unity_loop.py
C++: AIRManager_v2

<!-- CHAPTER_INDEX_BEGIN -->
## 開発Checkpoint索引（CH01〜CH12）

番号は開発の順序、ファイル名の主題は各段階の主要成果を示す。
CH10.5〜10.7はCH11に向けた補助的な導入・検証記録である。

| 章 | 記録・再現手順 | 主題 |
| --- | --- | --- |
| CH01 | [CH01-SpeechToUnityConsole.md](CH01-SpeechToUnityConsole.md) | 音声認識 → TCP/IP → Unity Console |
| CH01.1 | [CH01.1-SpeechToUnityUI.md](CH01.1-SpeechToUnityUI.md) | 音声認識結果をUnity UIに表示 |
| CH02 | [CH02-NaturalLanguageCommand.md](CH02-NaturalLanguageCommand.md) | 自然言語を構造化行動指示へ変換 |
| CH03 | [CH03-BodyCenteredAction.md](CH03-BodyCenteredAction.md) | 身体基準の空間参照とAIアバター行動 |
| CH04 | [CH04-ActionVerification.md](CH04-ActionVerification.md) | Actionと独立したVerification |
| CH05 | [CH05-ExperienceLogging.md](CH05-ExperienceLogging.md) | ExperienceのJSONL永続記録 |
| CH06 | [CH06-PermissionControl.md](CH06-PermissionControl.md) | AIアバター行動前の権限確認 |
| CH07 | [CH07-HumanEvaluation.md](CH07-HumanEvaluation.md) | 人間による評価とExperienceの統合 |
| CH08 | [CH08-AIRManagerIntegration.md](CH08-AIRManagerIntegration.md) | 独立AIR ManagerとEnd-to-End統合 |
| CH09 | [CH09-MREALIntegration.md](CH09-MREALIntegration.md) | MREALへのSandbox Runtime導入・統合 |
| CH10 | [CH10-PhysicalSpaceTracking.md](CH10-PhysicalSpaceTracking.md) | MREAL Head Trackingと実空間への接続 |
| CH10.5 | [CH10.5-LocalLLM.md](CH10.5-LocalLLM.md) | ローカルLLM導入準備 |
| CH10.6 | [CH10.6-ImageGeneration.md](CH10.6-ImageGeneration.md) | ローカルAI画像生成環境の導入とテスト |
| CH10.7 | [CH10.7-ImageLearning.md](CH10.7-ImageLearning.md) | AI画像学習環境の導入とテスト |
| CH11 | [CH11-DemoReproduction.md](CH11-DemoReproduction.md) | 音声操作・会話GUIとデモ再現手順 |
| CH12 | [CH12-Portable.md](CH12-Portable.md) | PC・ユーザ・Portableの環境分離と検証 |
| CH12図 | [CH12-AIRManager-Sequence.pptx](CH12-AIRManager-Sequence.pptx) | AI_1移動のシーケンス図：UnityとAIR Managerの座標授受（実測／コード照合待ちを区別） |

**検証範囲の注意：** CH11の会話・音声応答のOpenAI API実機確認は未検証。CH12の新PC側RuntimeのCPU環境構築と、音声入力からAIR Manager経由のAI_1移動までは実機検証済み。GPU実行、Action Verification、Experience Loggingの実動作は未検証として区別する。

このREADME冒頭の3行は従来の実装メモとして保全しており、現在の構成が同一であることを保証しない。
<!-- CHAPTER_INDEX_END -->
