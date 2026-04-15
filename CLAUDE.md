# AGENTS.md

## 1. Project Overview

AudienceRoom は、面接やプレゼンなど「人前で話す場面」を再現し、本番に近い緊張感の中で練習するためのアプリである。

本リポジトリはモノレポ構成とし、frontend / backend を同一リポジトリで管理する。

技術方針:

- Frontend: Next.js (TypeScript)
- Backend: FastAPI
- Database: PostgreSQL
- ORM: SQLAlchemy 2.x
- Migration: Alembic
- Auth: Firebase Authentication
- API契約: OpenAPI
- 型生成: OpenAPI → TypeScript 型自動生成
- Local: Docker Compose
- Production: Cloud Run + Cloud SQL

AudienceRoom の中心概念:

- users
- practice_sessions
- ai_characters
- session_participants
- session_messages
- session_feedback
- feedback_metrics

「1回の練習 = 1 practice_session」である。
設計・実装・テストは practice_sessions を中心に考えること。

---

## 2. Development Workflow

### Backend

以下の順序で実装すること。順番を飛ばしてはいけない。

1. 要件確認
2. README / AGENTS.md / 既存コード確認
3. DB スキーマ設計
4. SQLAlchemy models 作成
5. Alembic migration 作成
6. Repository 作成
7. Service 作成
8. API Route 作成
9. Pydantic Schema 作成
10. OpenAPI に反映されることを確認
11. テスト作成
12. テストを pass
13. OpenAPI export
14. Merge

禁止事項:

- Route から直接 DB 操作しない
- Route に business logic を書かない
- Migration なしで DB を変更しない
- Repository に business logic を書かない

---

### Frontend

1. OpenAPI の変更を確認
2. make generate-api で型を更新
3. feature 単位で実装
4. page / feature / component を分離
5. API 呼び出しは lib/api に実装
6. テスト作成
7. typecheck / lint / test を pass
8. Merge

---

## 3. Branch Naming Rules

- feat/<feature-name>
- fix/<bug-name>
- refactor/<target>
- chore/<infra>
- docs/<document>
- test/<test-target>

ルール:

- kebab-case
- 1ブランチ = 1目的
- 大きすぎる変更を1ブランチに入れない

---

## 4. Commit Message Rules

Conventional Commits を使用する。

- feat:
- fix:
- refactor:
- docs:
- chore:
- test:

例:

- feat: add practice session api
- feat: add session setup form
- fix: fix session status bug
- test: add session service test

---

## 5. Backend Architecture Rules

レイヤードアーキテクチャを採用する。

依存方向:

routes → services → repositories → database

### routes
- HTTP request を受け取る
- schema で validation
- service を呼ぶ
- response を返す
- business logic を書かない

### services
- business logic を書く
- 複数 repository を組み合わせる
- FastAPI に依存しない

### repositories
- DB access を担当
- SQLAlchemy を使用
- business logic を書かない

### models
- DB schema を表現

### schemas
- request / response schema
- validation

---

## 6. Database Rules

- テーブル名: snake_case 複数形
- カラム名: snake_case
- 外部キーは必ず定義
- created_at を持たせる
- updated_at を持たせる
- deleted_at は論理削除用
- enum は安易に使わない
- status は varchar + CHECK 制約

---

## 7. Migration Rules

手順:

1. model 変更
2. migration 生成
3. migration 確認
4. upgrade
5. rollback 可能か確認

禁止:

- migration なしで DB 変更
- 空 migration 放置
- model と migration の不整合

---

## 8. Project Structure

AudienceRoom/
  frontend/
    src/
      app/
      features/
      components/
        ui/
        layout/
      lib/
        api/
      generated/
      hooks/
      types/
      tests/
    public/
    package.json
    tsconfig.json
    next.config.ts
  backend/
    app/
      api/
      core/
      db/
        models/
        migrations/
      repositories/
      services/
      schemas/
    tests/
    Dockerfile
    pyproject.toml
    alembic.ini
  .github/
    workflows/
  docker-compose.yml
  README.md
  AGENTS.md
  Makefile

ルール:
単一ファイルにロジックを詰め込まない
page.tsx に business logic を書きすぎない
main.py を肥大化させない
新規機能は責務に応じて適切な層に配置する
generated/ は手編集しない
API 呼び出しは lib/api に集約する

---

## 9. Environment Rules

- .env はコミットしない
- .env.example は必ず更新
- 環境変数をコードに直書きしない

---

## 10. Frontend Architecture Rules

### Directory Structure

frontend/src:

- app/ → routing only
- features/ → feature logic
- components/ → reusable UI
- lib/api/ → API client
- generated/ → OpenAPI generated types
- hooks/ → reusable hooks
- types/ → manual types
- tests/ → tests

禁止事項:

- app に business logic を書かない
- component 内で直接 fetch しない
- generated のコードを手編集しない

---

### Page / Feature / Component Rules

- page → 画面構成のみ
- feature → ロジック
- component → 表示

---

### API Rules

- API 呼び出しは lib/api に集約
- fetch を component に書かない
- OpenAPI の型を使用
- API URL を直書きしない

---

### State Management Rules

状態を分離する:

- UI state
- Server state

Server state を useState で管理しすぎない。
React Query / SWR 等を使用する。

---

### Form Rules

- react-hook-form 使用
- zod で validation
- API schema と型を一致させる
- loading / error 表示を実装

---

## 11. OpenAPI / API Contract Rules

- OpenAPI は backend が正本
- frontend は OpenAPI から型生成
- openapi.json をリポジトリで管理
- 型生成は make generate-api
- CI で OpenAPI と生成型の差分チェック
- API 変更 → OpenAPI 更新 → 型更新 → frontend 修正

### OpenAPI 再生成の注意事項

**必ず Docker 経由で実行:**

```bash
# ✅ 正しい方法（CI と同じ環境）
docker compose run --rm --no-deps \
  -v "$(pwd)/openapi.json:/output/openapi.json" \
  backend python -m scripts.export_openapi /output/openapi.json

# ❌ 間違った方法（ローカル Python 環境）
python -m scripts.export_openapi openapi.json
```

**手順:**

1. ルーター・スキーマ変更
2. 上記コマンドで `openapi.json` を再生成
3. `cd frontend && npm run generate:api` で TypeScript 型を生成
4. `openapi.json` と `schema.gen.ts` の両方をコミット
5. CI で差分チェックが pass することを確認

**トラブルシューティング:**

- `openapi.json` が空の場合: 先に `touch openapi.json` してからボリュームマウント
- 差分が出る場合: Docker イメージのキャッシュをクリア（`docker compose build --no-cache backend`）
- 日本語の docstring を変更した場合も必ず再生成

---

## 12. Testing Rules

### Backend

- pytest
- repository test
- service test
- API test

#### Backend Testing Best Practices

**モックのパッチパスに注意:**

- `patch()` は「使用される場所」でパッチを当てる（定義された場所ではない）
- 例: `StreamingConversationService` が `from app.services.ai.llm import get_llm_provider` でインポートしている場合
  - ❌ `patch("app.services.ai.llm.get_llm_provider")`
  - ✅ `patch("app.services.ai.streaming_conversation_service.get_llm_provider")`
- API キーを必要とする外部サービス（LLM, TTS など）は必ずモックする
- `@pytest.fixture(autouse=True)` を使用して全テストに自動適用
- フィクスチャの依存関係を明示的にする（`service(self, mock_db, mock_llm_provider)`）

**非同期テスト:**

- pytest-asyncio を使用
- `@pytest.mark.asyncio` を async テストに付与
- `pyproject.toml` で `asyncio_mode = "auto"` を設定済み

**共通フィクスチャ:**

- `tests/conftest.py` に共通フィクスチャを配置
- プロジェクト全体で再利用可能にする

### Frontend

3種類のテストを書く:

1. Unit Test
2. Component Test
3. E2E Test

#### Frontend Testing Best Practices

**TypeScript 型アサーション:**

- `Record<string, unknown>` から値を取得する際は型アサーションが必要
- 例:
  ```typescript
  const data: Record<string, unknown> = { ... };
  const text = data.text as string;
  const id = data.participant_id as number | undefined;
  ```
- より型安全にするには discriminated union を使用

**SSE テスト:**

- vitest を使用（`@jest/globals` ではない）
- `ReadableStream` を使ってモックデータを作成
- イベントの順序と内容を検証

ルール:

- 新機能にはテストを書く
- main フローは E2E で担保
- テスト失敗状態で merge 禁止
- CI で失敗したら必ずローカルで再現・修正してから push

---

## 13. CI Rules

### Backend CI

- pytest
- migration
- OpenAPI export

### Frontend CI

- typecheck
- lint
- test
- OpenAPI 型生成
- schema 差分チェック

CI fail 状態で merge してはいけない。

---

## 14. Merge Preconditions

以下を満たさない限り merge してはいけない。

- ブランチ名が規則に従う
- 単一責務
- テスト追加済み
- テスト pass
- typecheck pass
- lint pass
- OpenAPI / 型差分なし
- Docker 環境を壊していない
- AGENTS.md に違反していない

---

## 15. Development Commands

Makefile のコマンドを使用すること。

例:

- make up
- make down
- make migrate
- make test-backend
- make generate-api
- make check-api