# AGENT.md

## 1. Project Overview

AudienceRoom は、面接やプレゼンなど「人前で話す場面」を再現し、本番に近い緊張感の中で練習するためのアプリである。

このリポジトリでは、以下の方針を前提に開発すること。

- フロントエンドとバックエンドを同一リポジトリで管理する
- 認証は Firebase Authentication を使う
- 業務データは PostgreSQL に保存する
- バックエンドは FastAPI を使う
- ORM は SQLAlchemy 2.x を使う
- マイグレーションは Alembic を使う
- ローカル開発は Docker Compose を前提とする
- 本番環境は Cloud Run + Cloud SQL for PostgreSQL を想定する

AudienceRoom のバックエンドは、単なるAPIの集合ではなく、以下の主要概念を中心に設計する。

- users
- practice_sessions
- ai_characters
- session_participants
- session_messages
- session_feedback
- feedback_metrics

このアプリの中心は「1回の練習 = 1セッション」である。  
したがって、設計・実装・テストは `practice_sessions` を中心に組み立てること。

---

## 2. Development Workflow

開発は以下の順番で進めること。順番を飛ばしてはいけない。

1. 要件を確認する
2. 既存の README / AGENT.md / 関連コードを確認する
3. 必要であれば DB スキーマを先に設計する
4. SQLAlchemy models を作成または修正する
5. Alembic migration を作成する
6. Repository を作成または修正する
7. Service を作成または修正する
8. API routes を作成または修正する
9. テストを追加する
10. テストを pass させる
11. ドキュメントが必要なら更新する
12. その後に merge する

禁止事項:

- API から直接 DB 操作をしてはいけない
- Service を経由せずに business logic を routes に書いてはいけない
- Migration なしで DB の変更をしてはいけない
- README や AGENT.md と矛盾する実装をしてはいけない

---

## 3. Branch Naming Rules

すべての作業はブランチを切って行うこと。  
`main` に直接 commit してはいけない。

ブランチ名は以下の形式に従うこと。

- `feat/<feature-name>`
- `fix/<bug-name>`
- `refactor/<target>`
- `chore/<infra-or-config>`
- `docs/<document-name>`

例:

- `feat/database-setup`
- `feat/firebase-auth`
- `feat/practice-session`
- `feat/session-messages`
- `feat/feedback`
- `fix/session-status-bug`
- `refactor/session-service`
- `docs/update-readme`
- `chore/docker-compose`

ルール:

- ブランチ名は小文字の kebab-case にする
- 曖昧な名前を使わない
- 1ブランチ = 1目的にする
- テーブル追加、認証追加、Docker修正など、責務ごとに分ける
- 大きすぎる作業を1ブランチに詰め込まない

推奨粒度:

- 1テーブル追加
- 1機能追加
- 1責務の修正
- 1つのインフラ設定変更

---

## 4. Commit Message Rules

コミットメッセージは Conventional Commits に寄せること。  
以下のプレフィックスを使う。

- `feat:`
- `fix:`
- `refactor:`
- `docs:`
- `chore:`

例:

- `feat: add users model`
- `feat: add practice session repository`
- `fix: fix session status validation`
- `refactor: split session service`
- `docs: update backend readme`
- `chore: update docker compose`

ルール:

- 1コミット = 1意味にする
- 「いろいろ修正」みたいな曖昧なメッセージは禁止
- migration を含む変更は、できれば model 修正と同じ文脈でまとめる
- 大量変更を1コミットに押し込まない

---

## 5. Architecture Rules

AudienceRoom のバックエンドはレイヤードアーキテクチャで実装する。

依存方向は以下に限定する。

```text
routes -> services -> repositories -> database
```

各層の責務は次の通り。

### routes
役割:
- HTTP request を受け取る
- schema による入力検証を行う
- service を呼ぶ
- HTTP response を返す

禁止:
- business logic を書かない
- SQLAlchemy の query を直接書かない
- repository を直接呼ばない

### services
役割:
- business logic を実装する
- 複数 repository を組み合わせる
- トランザクションのまとまりを設計する
- アプリ固有のルールを表現する

禁止:
- FastAPI への依存を持たない
- request / response の都合を書き込まない
- SQL を直接書かない

### repositories
役割:
- DB の読み書きを担当する
- SQLAlchemy を使って query を組み立てる
- persistence layer として振る舞う

禁止:
- business logic を書かない
- HTTP の概念を持ち込まない

### models
役割:
- DB スキーマを表現する
- SQLAlchemy model を定義する

禁止:
- API 向けの schema を書かない
- service 的な処理を書かない

### schemas
役割:
- Request / Response の形式を定義する
- バリデーションを行う

禁止:
- DB の責務を持たない
- SQLAlchemy model と混同しない

設計原則:

- model と schema は分ける
- route と service は分ける
- service と repository は分ける
- DB access は repository に閉じ込める
- framework 依存は outer layer に寄せる

---

## 6. Database Rules

主DBは PostgreSQL とする。  
Firebase は認証に使うが、業務データの正本は PostgreSQL に置く。

### 6.1 General Rules

- テーブル名は snake_case の複数形にする
- カラム名は snake_case にする
- 外部キーは必ず定義する
- すべての主要テーブルに `created_at` を持たせる
- 更新されるテーブルには `updated_at` を持たせる
- 論理削除が必要なテーブルには `deleted_at` を持たせる
- 状態管理の値は、基本的に `varchar + CHECK 制約` で表現する
- 将来変わりうるものに PostgreSQL enum を安易に使わない
- セッションや発話の順序が重要なものは、順序カラムに制約を持たせる

### 6.2 AudienceRoom-specific Rules

次のテーブルを中核として設計すること。

- `users`
- `practice_sessions`
- `ai_characters`
- `session_participants`
- `session_messages`
- `session_feedback`
- `feedback_metrics`

設計原則:

- 1回の練習 = 1 `practice_session`
- AIキャラの定義は `ai_characters` に持つ
- セッション内の参加者は `session_participants` に持つ
- 発話ログは `session_messages` に持つ
- フィードバック本文は `session_feedback` に持つ
- 数値評価は `feedback_metrics` に持つ

### 6.3 Schema Change Rules

- model を変更したら migration を必ず作る
- migration なしで DB を変更してはいけない
- migration ファイルをコミットし忘れてはいけない
- 破壊的変更は README か PR 説明で明示する
- nullable / default / unique / foreign key を適当に決めない

### 6.4 Data Handling Rules

- セッション中のリアルタイム処理は DB に過剰に書き込まない
- `session_messages` には、初期段階では確定済み発話のみ保存する
- VAD や一時的な中間状態は persistent storage に入れない
- まだ使わない分析値を先回りで保存しすぎない

---

## 7. Migration Rules

- Alembic を使うこと
- model を追加・変更したら migration を作ること
- migration は必ずレビュー対象に含めること
- 空の migration を放置しないこと
- migration だけ先に作って model を追従させないこと
- model と migration の不整合を残さないこと

作業順序:

1. model を定義または変更する
2. migration を生成する
3. migration 内容を確認する
4. DB に適用する
5. 必要なら rollback が可能か確認する

---

## 8. Project Structure

このリポジトリはモノレポとして扱う。  
Git はプロジェクトルートで管理すること。

想定構成:

```text
AudienceRoom/
  frontend/
  backend/
    app/
      api/
        routes/
      core/
      db/
        migrations/
        models/
      repositories/
      schemas/
      services/
      main.py
    tests/
    Dockerfile
    pyproject.toml
  docker-compose.yml
  README.md
  AGENT.md
```

バックエンド内の各ディレクトリの役割:

- `app/api/routes`: FastAPI routes
- `app/core`: 設定管理
- `app/db/models`: SQLAlchemy models
- `app/db/migrations`: Alembic migrations
- `app/repositories`: DB access layer
- `app/services`: business logic
- `app/schemas`: request / response schema
- `tests`: テストコード

ルール:

- 単一ファイルにロジックを詰め込まない
- `main.py` を肥大化させない
- 新規機能は責務に応じて適切な層に配置する
- utility を増やしすぎて責務を曖昧にしない

---

## 9. Environment

### Local Development

- Docker Compose を前提にする
- ローカル DB は PostgreSQL コンテナを使う
- backend は Docker で起動できる状態を維持する
- frontend と backend と db は、プロジェクトルートの `docker-compose.yml` からまとめて起動できるようにする

### Production Assumptions

- backend: Cloud Run
- database: Cloud SQL for PostgreSQL
- auth: Firebase Authentication

### Environment Variable Rules

- 秘密情報は `.env` に置く
- `.env` はコミットしない
- `.env.example` は必ず最新状態を保つ
- 環境変数名は明示的にする
- DB 接続文字列はコードに直書きしない

---

## 10. Additional Rules

### 10.1 Documentation
- README は構成変更時に必要に応じて更新する
- DB 設計が変わった場合は README か別ドキュメントに反映する
- 重要な設計判断は、コードだけで済ませず説明できるようにする

### 10.2 Code Quality
- 型ヒントをできるだけ書く
- 責務の異なる処理を1関数に詰め込まない
- 関数名とクラス名は意味が分かるものにする
- magic number を避ける
- TODO を残す場合は意図を明確にする

### 10.3 Scope Control
- MVP 段階では必要以上に抽象化しない
- まだ使わない機能を先回りで実装しない
- ただし、責務の分離は崩さない
- 「今必要な最小限」と「後で壊れない構造」を両立する

### 10.4 Merge Preconditions
以下を満たさない限り merge してはいけない。

- ブランチ名が規則に従っている
- 変更内容が単一の目的に収まっている
- migration が必要なら含まれている
- テストが pass している
- ルートから起動する Docker 環境を壊していない
- AGENT.md のルールに違反していない
