# experiments — LLM 検証サンドボックス

本体（frontend/backend）とは分離した、技術検証用フォルダ。
**目的：トピック抽出を小型モデルに置き換えられるか試す**（LoRA fine-tuning + セルフホスト + 監視）。

## なぜトピック抽出が対象か（課題の整理）

AudienceRoom で LLM(Gemini) を使う箇所のうち：

| 箇所 | fine-tune 向き？ |
| --- | --- |
| 会話の質問生成 / フィードバック | ✗ オープンで創造性が要・品質リスク高 |
| **トピック抽出**（会話 → 概念グラフ JSON 差分） | ◎ 狭い・構造化出力・頻出・データを自前で作れる |

トピック抽出の根っこの課題は **タクソノミー未定義**（`node_type` / `relation_type` が自由文字列で毎回バラバラ）。
これを「良い抽出例」を学習させることで **暗黙的に一貫させる**のが狙い。

> アプリ側で実際に動いている抽出は `backend/app/services/ai/topic_memory_updater.py`
> （プロンプト: `backend/app/services/prompts/topic_session_update.py`）。練習後に1回呼ばれる。

## 道のり

| ステップ | 内容 | 場所 |
| --- | --- | --- |
| 1 | **Langfuse** で抽出の入出力を可視化＆教師データ収集 | `langfuse/` |
| 2 | 集めたトレースを **SFT データセット**に整形 | `finetuning/prepare_data.py` |
| 3 | **Modal** で小型モデルを **LoRA fine-tuning** | `finetuning/train_lora.py` |
| 4 | **Modal** でセルフホスト配信 → backend と A/B、Langfuse で比較 | `serving/` |

## 用語ミニ辞典（ML 初心者向け）

- **fine-tuning**: 既存モデルを、特定タスクの例で追加学習して専用化すること。
- **LoRA**: モデル全体ではなく「小さな差分行列」だけを学習する軽量 fine-tuning。GPU メモリ・時間・コストを大幅削減。
- **SFT（教師ありファインチューニング）**: 「入力 → 望ましい出力」のペアで学習させる最も基本的な方法。
- **データセット**: その「入力 → 出力」ペアの集合。今回は (会話 → 望ましい JSON)。
- **トレース（Langfuse）**: 1回の LLM 呼び出しの入力・出力・コスト等の記録。
- **Modal**: Python 関数にデコレータを付けて呼ぶと、クラウド GPU 上で実行してくれるサービス。

各ステップの詳細は各サブフォルダの README を参照。
