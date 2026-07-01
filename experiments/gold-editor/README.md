# Gold Editor — 視覚的に gold を作る

会話を選ぶ → **Gemini で概念グラフを下書き** → **画面上でクリック編集**（ノード/エッジ/coverage）→ **gold として保存**。

fine-tune の教師データ（正解）を、JSON を手書きせずに視覚的に整えるためのツール。

## 起動

AudienceRoom の db/backend が起動している前提（会話を DB から読むため）：

```bash
# リポジトリ root から
docker compose up -d db backend

docker compose run --rm -p 8100:8100 \
  -v "$(pwd)/experiments:/experiments" -e PYTHONPATH=/app \
  backend python /experiments/gold-editor/server.py
```

→ ブラウザで **http://localhost:8100**

## 使い方

1. 左の一覧から会話を選ぶ（会話内容が下に出る）
2. **「Gemini下書き」** で概念グラフが自動生成される
3. 中央のグラフを編集：
   - ノード/エッジを**クリック** → 右で label / node_type / coverage / relation を変更、削除
   - **＋ノード** で追加、**エッジ追加: ON** にして始点→終点をクリックで結ぶ
   - ノードは**ドラッグ**で移動
4. **「💾 gold保存」** → `gold/gold.jsonl` に1件追記

- 保存先 `gold/` は会話を含むため **gitignore**。
- 色: 緑=covered / 橙=weak / 灰=gap、赤いエッジ=contradicts。

## 出力形式（gold/gold.jsonl の1行）

```json
{"session_id": 1218, "topic": "研究内容",
 "turns": [{"speaker":"interviewer","text":"..."}, ...],
 "graph": {"nodes":[{"label","node_type","coverage","detail"}], "edges":[{"source","target","relation_type"}]},
 "saved_at": "..."}
```

これを次段で SFT 形式に変換して学習に使う。
