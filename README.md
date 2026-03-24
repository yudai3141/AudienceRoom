# AudienceRoom

## 1. Overview
**AudienceRoom** は、面接やプレゼンなど「人前で話す場面」を再現し、  
本番に近い緊張感の中で練習するためのアプリです。

少し厳しめの環境で練習することで、本番を少し楽に感じられるようにすることを目的としています。

> AudienceRoom = 「聴衆のいる部屋」

---

## 2. Table of Contents
1. [Overview](#1-overview)
2. [Concept](#3-concept)
3. [UI Flow](#4-ui-flow)
4. [Main Features](#5-main-features)
5. [System Architecture](#6-system-architecture)
6. [Backend Architecture](#7-backend-architecture)
7. [Database Design](#8-database-design)
8. [Tech Stack](#9-tech-stack)
9. [Local Development](#10-local-development)
10. [Project Structure](#11-project-structure)
11. [Development Roadmap](#12-development-roadmap)

---

## 3. Concept
AudienceRoom は、以下のような課題を解決するためのアプリです。

- 面接が怖い
- プレゼンで緊張する
- 人前で話す練習環境がない
- 一人で練習しても緊張感がない

そこで、

- Zoomのような画面
- AIの聴衆・面接官
- 少し厳しめの質問
- 練習後のフィードバック

を組み合わせ、**本番に近い環境を再現**します。

---

## 4. UI Flow

```text
Login
 ↓
Home（ダッシュボード）
 ↓
練習設定
 ↓
AudienceRoom（Zoom画面）
 ↓
フィードバック
 ↓
履歴保存
 ↓
Home
```

### 4.1 Login
- Email / Password
- Google Login
- Apple Login
- Firebase Authentication を使用

### 4.2 Home（Dashboard）
表示内容：
- 「今日の練習」ボタン
- 前回のフィードバックの一言
- これまでの練習回数
- 履歴ページへのリンク

### 4.3 練習設定
設定できる項目：
- 参加人数
- 厳しさ
- モード
  - プレゼン形式
  - 面接形式
  - 自由会話
- AIの性格
- 業界設定
- フィードバックの重点
- フィードバック ON/OFF
- 話すテーマ
- 克服したいこと

### 4.4 AudienceRoom（Zoom風UI）
必要なUI要素：
- 自分のカメラ ON/OFF
- 自分のマイク ON/OFF
- 退出ボタン
- 参加者の画面
- メモ欄

### 4.5 フィードバック画面
表示内容：
- 良かった点
- 改善点
- スコア
- 一言コメント
- 自信を持たせるフィードバック

### 4.6 学習履歴
例：

```text
3/20 面接練習 ★★★★☆
3/18 プレゼン ★★★☆☆
3/15 自由会話 ★★★★★
```

---

## 5. Main Features
- 面接練習
- プレゼン練習
- 自由会話練習
- AI面接官 / AI聴衆
- フィードバック生成
- スコアリング
- 練習履歴管理

---

## 6. System Architecture

```text
Frontend
  ↓
FastAPI (Backend)
  ↓
SQLAlchemy
  ↓
PostgreSQL
```

認証は Firebase Authentication を使用します。

```text
Firebase Auth → FastAPI → PostgreSQL
```

---

## 7. Backend Architecture

レイヤードアーキテクチャを採用します。

```text
Client
  ↓
API Layer (routes)
  ↓
Service Layer (business logic)
  ↓
Repository Layer (DB access)
  ↓
Database (PostgreSQL)
```

### 7.1 Responsibilities

| Layer | Responsibility |
|------|---------------|
| routes | HTTP request / response |
| services | Business logic |
| repositories | Database access |
| models | Database schema |
| schemas | Request / Response schema |

---

## 8. Database Design

このアプリの中心は **「1回の練習 = 1セッション」** です。  
そのため `practice_sessions` を中心にデータを設計します。

### 8.1 Main Tables
- `users`
- `practice_sessions`
- `ai_characters`
- `session_participants`
- `session_messages`
- `session_feedback`
- `feedback_metrics`

### 8.2 users

| Column | Type | Required | Description |
|---|---|---:|---|
| id | bigint | ○ | 内部ユーザID |
| firebase_uid | varchar(128) | ○ | Firebase Auth の UID |
| email | varchar(255) | ○ | メールアドレス |
| display_name | varchar(100) | ○ | 表示名 |
| photo_url | text |  | アイコンURL |
| onboarding_completed | boolean | ○ | 初期設定完了フラグ |
| created_at | timestamptz | ○ | 作成日時 |
| updated_at | timestamptz | ○ | 更新日時 |
| deleted_at | timestamptz |  | 論理削除日時 |

**Notes**
- `firebase_uid` は Firebase Authentication 上のユーザと、PostgreSQL 上のユーザレコードを紐づけるためのキーです。
- `firebase_uid` と `email` は一意制約を想定します。

### 8.3 practice_sessions

| Column | Type | Required | Description |
|---|---|---:|---|
| id | bigint | ○ | セッションID |
| user_id | bigint | ○ | `users.id` |
| status | varchar(20) | ○ | セッション状態 |
| mode | varchar(30) | ○ | `presentation` / `interview` / `free_conversation` |
| participant_count | int | ○ | 参加AI人数 |
| feedback_enabled | boolean | ○ | フィードバック有無 |
| theme | text |  | テーマ |
| presentation_duration_sec | int |  | 発表時間（秒） |
| presentation_qa_count | int |  | 質疑応答回数 |
| user_goal | text |  | 何を練習したいか |
| user_concerns | text |  | 何を克服したいか |
| session_brief | text |  | AIに渡す事前説明の要約 |
| target_context | varchar(50) |  | 面接/発表などの文脈ラベル |
| overall_score | int |  | 総合点 |
| feedback_summary | text |  | 一言要約 |
| started_at | timestamptz |  | 開始時刻 |
| ended_at | timestamptz |  | 終了時刻 |
| created_at | timestamptz | ○ | 作成日時 |
| updated_at | timestamptz | ○ | 更新日時 |
| deleted_at | timestamptz |  | 論理削除日時 |

**Status**
- `waiting`: 開始前
- `active`: 練習中
- `completed`: 正常終了
- `cancelled`: 中断
- `error`: 異常終了

### 8.4 ai_characters

| Column | Type | Required | Description |
|---|---|---:|---|
| id | bigint | ○ | AIキャラID |
| code | varchar(50) | ○ | 内部コード |
| name | varchar(100) | ○ | 表示名 |
| role | varchar(20) | ○ | `host` / `audience` |
| strictness | varchar(20) | ○ | `gentle` / `normal` / `hard` |
| personality | varchar(50) |  | 性格ラベル |
| voice_style | varchar(50) |  | TTS用の声質ラベル |
| description | text |  | 説明 |
| is_active | boolean | ○ | 利用可否 |
| created_at | timestamptz | ○ | 作成日時 |
| updated_at | timestamptz | ○ | 更新日時 |

### 8.5 session_participants

| Column | Type | Required | Description |
|---|---|---:|---|
| id | bigint | ○ | 参加者インスタンスID |
| session_id | bigint | ○ | `practice_sessions.id` |
| ai_character_id | bigint | ○ | `ai_characters.id` |
| display_name | varchar(100) | ○ | 今回の表示名 |
| role | varchar(20) | ○ | `host` / `audience` |
| seat_index | int | ○ | 画面上の位置 |
| is_active | boolean | ○ | 有効フラグ |
| created_at | timestamptz | ○ | 作成日時 |

### 8.6 session_messages

| Column | Type | Required | Description |
|---|---|---:|---|
| id | bigint | ○ | 発話ID |
| session_id | bigint | ○ | `practice_sessions.id` |
| participant_id | bigint |  | `session_participants.id` |
| sequence_no | int | ○ | 発話順 |
| content | text | ○ | 発話内容 |
| transcript_confidence | numeric(4,3) |  | 音声認識信頼度 |
| created_at | timestamptz | ○ | 作成日時 |

**Notes**
- リアルタイム処理の負荷を抑えるため、まずは確定済みの発話のみ保存する想定です。
- フィラーや話速などの詳細分析値は、初期段階では保持しません。

### 8.7 session_feedback

| Column | Type | Required | Description |
|---|---|---:|---|
| id | bigint | ○ | フィードバックID |
| session_id | bigint | ○ | `practice_sessions.id` |
| user_id | bigint | ○ | `users.id` |
| summary_title | text | ○ | 総評タイトル |
| short_comment | text |  | 短いコメント |
| positive_points | jsonb | ○ | 良かった点 |
| improvement_points | jsonb | ○ | 改善点 |
| closing_message | text |  | 最後の一言 |
| created_at | timestamptz | ○ | 作成日時 |
| updated_at | timestamptz | ○ | 更新日時 |

### 8.8 feedback_metrics

| Column | Type | Required | Description |
|---|---|---:|---|
| id | bigint | ○ | 主キー |
| feedback_id | bigint | ○ | `session_feedback.id` |
| metric_key | varchar(50) | ○ | 指標キー |
| metric_value | numeric(8,2) | ○ | 値 |
| metric_label | varchar(100) |  | 表示名 |
| metric_unit | varchar(20) |  | 単位 |
| created_at | timestamptz | ○ | 作成日時 |

---

## 9. Tech Stack

### 9.1 Frontend
- React / Next.js or similar
- Zoom-like practice UI
- Camera / microphone controls

### 9.2 Backend
- FastAPI
- SQLAlchemy 2.x
- Alembic
- PostgreSQL

### 9.3 Authentication
- Firebase Authentication
- Google Login
- Apple Login

### 9.4 Infrastructure
- Docker / Docker Compose
- Local PostgreSQL
- Cloud SQL for PostgreSQL (production)

---

## 10. Local Development

### 10.1 Prerequisites
- Docker
- Docker Compose
- Python 3.11+（ローカル実行時）

### 10.2 Start
プロジェクトルートで以下を実行します。

```bash
docker compose up --build
```

### 10.3 Health Check
バックエンド起動後、以下にアクセスします。

```text
http://localhost:8000/health
```

---

## 11. Project Structure

```text
backend/
├── app
│   ├── api
│   │   └── routes
│   ├── core
│   ├── db
│   │   ├── migrations
│   │   └── models
│   ├── repositories
│   ├── schemas
│   ├── services
│   └── main.py
├── Dockerfile
├── pyproject.toml
└── tests
```

### 11.1 Directory Roles

| Directory | Role |
|---|---|
| `app/api/routes` | FastAPI routes |
| `app/core` | Config / settings |
| `app/db/models` | SQLAlchemy models |
| `app/db/migrations` | Alembic migrations |
| `app/repositories` | DB access layer |
| `app/services` | Business logic |
| `app/schemas` | Request / response schemas |
| `tests` | Test code |

---

## 12. Development Roadmap

### 12.1 Phase 1
- [x] Backend project structure
- [x] Docker setup
- [x] Health check endpoint
- [ ] DB connection setup
- [ ] Alembic initialization

### 12.2 Phase 2
- [ ] `users` table
- [ ] Firebase Auth integration
- [ ] User creation / sync API

### 12.3 Phase 3
- [ ] `practice_sessions`
- [ ] `ai_characters`
- [ ] `session_participants`
- [ ] Session creation flow

### 12.4 Phase 4
- [ ] `session_messages`
- [ ] `session_feedback`
- [ ] `feedback_metrics`

### 12.5 Phase 5
- [ ] Frontend integration
- [ ] Practice room UI
- [ ] Feedback screen
- [ ] Learning history screen

---

## 13. Notes
この README は現時点の設計メモを元にした初期版です。  
今後、実装に合わせて更新していきます。
