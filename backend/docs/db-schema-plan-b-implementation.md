# Plan B 実装計画 (トピック記憶 + 仮想 GraphRAG)

`backend/docs/db-schema-plan-b-topics.md`（DB 設計）と `docs/concept/audienceroom_topic_ux_design.md`（UX 設計）を実装に落とすためのロードマップ。

CLAUDE.md / AGENTS.md §2 のバックエンド手順（要件 → model → migration → repository → service → route → schema → OpenAPI → test → export → merge）に沿って、Plan B を 3 フェーズに割り付ける。

---

## ドキュメント更新の方針

| ファイル | 更新内容 | タイミング |
| --- | --- | --- |
| `CLAUDE.md` + `AGENTS.md`（**両者は完全に同一。必ず同期する**） | §1「中心概念」に `topics` / `topic_nodes` / `topic_edges` / `user_persona_facts` を追加。「1 練習 = 1 `practice_session`（揮発）／`topic` = 記憶の永続単位」と整理し直す | Phase B-1 でテーブルが着地する時（実装と同時。先行更新で未実装を documment 化しない） |
| `README.md` | §4 Concept（トピック記憶の再定義）、§10 Database Design（新テーブル）、§14 Roadmap（B-1〜B-3） | Concept は随時可。DB Design はテーブル着地時 |
| 設計 2 文書（plan-b-topics / topic-ux-design） | 正本。随時メンテ | — |

> 各フェーズの「model → … → merge」の最後に **doc 更新**を 1 ステップとして含める。

---

## ⚡ 最初に: 薄い縦スライスで GraphRAG を de-risk

最も不確実なのは「グラフを使った質問生成」。横展開の前に **1 本の細い動線**だけ通して検証する。

```
手動で topic + node 数個を seed
  → session を topic_id 付きで開始
  → グラフを context に質問が 1 つ生成される
  → 回答 → グラフが 1 ノード更新される
```

ここが回れば、残りは CRUD と UI の横展開になる。

---

## Phase B-1: トピック記憶の土台 + 仮想 GraphRAG（コア）

### Backend
1. **models**: `topics` / `topic_nodes` / `topic_edges`、`practice_sessions.topic_id`（nullable FK）
2. **migration**: 追加のみ（破壊的変更なし）。upgrade / rollback を確認
3. **repositories**: `TopicRepository` / `TopicNodeRepository` / `TopicEdgeRepository`
   - 候補ノード抽出 SQL（`coverage IN ('gap','weak')` ＋ 矛盾を持つノード）、近傍（1〜2 hop）取得を含む
4. **services**: `TopicService`(CRUD) ＋ 会話サービス拡張（仮想 GraphRAG ループ）
   - 候補抽出 → 質問生成 → 回答抽出 → グラフ upsert
   - coverage 遷移・矛盾検出の判定は **LLM**。service は構造化結果を受けて upsert（business logic は service 層、route には書かない）
5. **prompts**（`backend/app/services/prompts/`）: `topic_question.py`（候補から質問生成）/ `topic_extract.py`（回答 → グラフ差分抽出）
6. **routes / schemas**: `/topics` CRUD、`/sessions` に `topic_id`、会話ターン拡張。Pydantic schema
7. **OpenAPI export** → `make generate-api`、**test**（repository / service / API）

### Frontend
- 型生成（`make generate-api`）→ セットアップに「トピック選択 / 新規作成」を追加（最小 UI）

---

## Phase B-2: ダッシュボード可視化 + 練習後更新

### Backend
- フィードバック生成を拡張し `topics.completeness_score` / `current_summary` を更新
- `/topics/{id}` 詳細（nodes / edges / summary）
- フィードバックに「客観的に見た結果」ブロック ＋ トピック更新差分

### Frontend
- トピック一覧（完成度 / 弱点数 / 次の質問）
- トピック詳細の **CSS ツリー可視化**（`coverage` 塗り分け・`contradicts` 強調）
- フィードバック画面の刷新（4 ブロック + 差分）

---

## Phase B-3: ペルソナ活用

### Backend
- `user_persona_facts`（model / migration / repository / service）
- 質問生成プロンプトにペルソナを注入

### Frontend
- ペルソナ管理の最小 UI／オンボーディングで育てる導線

---

## 各フェーズ共通の締め（CLAUDE.md §11–14）

1. OpenAPI 再生成（**Docker 経由**）
   ```bash
   docker compose run --rm --no-deps \
     -v "$(pwd)/openapi.json:/output/openapi.json" \
     backend python -m scripts.export_openapi /output/openapi.json
   ```
2. `cd frontend && npm run generate:api` → `schema.gen.ts` をコミット
3. CI の OpenAPI 差分チェック pass
4. typecheck / lint / test pass
5. **CLAUDE.md / AGENTS.md / README 更新**（doc 同期）
6. merge

### ブランチ運用（CLAUDE.md §3: 1 ブランチ 1 目的）
1 フェーズ = 複数 PR に分割する。例:
- `feat/topic-models`（models + migration）
- `feat/topic-repositories`
- `feat/topic-graphrag`（会話サービス + prompts）
- `feat/topic-api`（routes + schema + OpenAPI）
- `feat/topic-dashboard`（frontend）

---

## マージ前提条件（CLAUDE.md §14）

- ブランチ名が規則に従う / 単一責務
- テスト追加済み・pass / typecheck・lint pass
- OpenAPI・型差分なし / Docker 環境を壊していない
- CLAUDE.md・AGENTS.md に違反していない（中心概念の同期を含む）

---

## 進捗チェックリスト

### Phase B-1
- [ ] `topics` / `topic_nodes` / `topic_edges` model
- [ ] `practice_sessions.topic_id` 追加 migration
- [ ] Topic 系 repository（候補抽出・近傍取得 SQL）
- [ ] 会話サービスの仮想 GraphRAG ループ
- [ ] `topic_question.py` / `topic_extract.py` prompt
- [ ] `/topics` CRUD + `/sessions` topic_id 拡張 + 会話ターン拡張
- [ ] OpenAPI export + 型生成
- [ ] repository / service / API テスト
- [ ] frontend: セットアップのトピック選択
- [ ] 縦スライス（seed → 質問 → 更新）が動く

### Phase B-2
- [ ] フィードバック生成で topic 更新
- [ ] `/topics/{id}` 詳細 API
- [ ] トピック一覧ダッシュボード
- [ ] トピック詳細ツリー可視化（coverage / contradicts）
- [ ] フィードバック画面刷新

### Phase B-3
- [ ] `user_persona_facts` 一式
- [ ] 質問生成へのペルソナ注入
- [ ] ペルソナ管理 UI

### 共通
- [ ] CLAUDE.md / AGENTS.md §1 更新（同期）
- [ ] README §4 / §10 / §14 更新
