# finetuning — トピック抽出の fine-tune

## ステップ

### 1. トレース収集（実装済み: `collect_traces.py`）
DB の完了セッションを、本番と同じ抽出プロンプト + Gemini で再実行し、Langfuse に計装しつつ
`(会話 → 抽出JSON)` を `data/topic_extraction.jsonl` に書き出す。

```bash
# リポジトリ root から（Langfuse と AudienceRoom db/backend が起動している前提）
docker compose run --rm \
  -v "$(pwd)/experiments:/experiments" \
  -e PYTHONPATH=/app \
  -e LANGFUSE_HOST=http://host.docker.internal:3001 \
  -e LANGFUSE_PUBLIC_KEY=pk-lf-local-audienceroom \
  -e LANGFUSE_SECRET_KEY=sk-lf-local-audienceroom \
  backend sh -c "pip install -q 'langfuse>=3,<4' && python /experiments/finetuning/collect_traces.py --limit 20"
```

- `data/` は会話を含むため **gitignore**（コミットしない）。
- backend コンテナ → ホストの Langfuse(:3001) は `host.docker.internal` で接続。
- `PYTHONPATH=/app` を渡すのは、絶対パス実行だと `app` パッケージが見えないため。

### 2. SFT データセットへ整形（次）
収集した `(会話 → JSON)` の「正解」をどう作るか決め、`(prompt, completion)` 形式に整形。
- 案: Gemini 出力をそのまま正解にする（弱教師）/ 一部を手直しして良質化 / 型を緩く固定。

### 3. LoRA fine-tuning（Modal）
小型の日本語モデルに、上のデータで LoRA SFT。`train_lora.py`（予定）。

### 4. セルフホスト配信（Modal）→ A/B
fine-tune したモデルを Modal で配信し、backend の LLM provider を切替。Langfuse で品質/コストを比較。
