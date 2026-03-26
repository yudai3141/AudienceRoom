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

---

## 12. Testing Rules

### Backend
- pytest
- repository test
- service test
- API test

### Frontend

3種類のテストを書く:

1. Unit Test
2. Component Test
3. E2E Test

ルール:

- 新機能にはテストを書く
- main フローは E2E で担保
- テスト失敗状態で merge 禁止

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