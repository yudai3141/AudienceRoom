# AudienceRoom

## Overview
**AudienceRoom** は、面接やプレゼンなど「人前で話す場面」を再現し、  
本番に近い緊張感の中で練習するためのアプリです。

少し厳しめの環境で練習することで、本番を少し楽に感じられるようにすることを目的としています。

> AudienceRoom = 「聴衆のいる部屋」

---

## Table of Contents
- [Overview](#overview)
- [Concept](#concept)
- [UI Flow](#ui-flow)
- [Main Features](#main-features)
- [System Architecture](#system-architecture)
- [Backend Architecture](#backend-architecture)
- [Database Design](#database-design)
- [Tech Stack](#tech-stack)
- [Local Development](#local-development)
- [Project Structure](#project-structure)
- [Development Roadmap](#development-roadmap)

---

## Concept
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

## UI Flow

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

### 1. Login
- Email / Password
- Google Login
- Apple Login
- Firebase Authentication を使用

### 2. Home（Dashboard）
表示内容：
- 「今日の練習」ボタン
- 前回のフィードバックの一言
- これまでの練習回数
- 履歴ページへのリンク

### 3. 練習設定
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

### 4. AudienceRoom（Zoom風UI）
必要なUI要素：
- 自分のカメラ ON/OFF
- 自分のマイク ON/OFF
- 退出ボタン
- 参加者の画面
- メモ欄

### 5. フィードバック画面
表示内容：
- 良かった点
- 改善点
- スコア
- 一言コメント
- 自信を持たせるフィードバック

### 6. 学習履歴
例：

```text
3/20 面接練習 ★★★★☆
3/18 プレゼン ★★★☆☆
3/15 自由会話 ★★★★★
```

---

## Main Features
- 面接練習
- プレゼン練習
- 自由会話練習
- AI面接官 / AI聴衆
- フィードバック生成
- スコアリング
- 練習履歴管理

---

## System Architecture

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

## Backend Architecture

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

### Responsibilities

| Layer | Responsibility |
|------|---------------|
| routes | HTTP request / response |
| services | Business logic |
| repositories | Database access |
| models | Database schema |
| schemas | Request / Response schema |

---

## Database Design

このアプリの中心は **「1回の練習 = 1セッション」** です。  
そのため `practice_sessions` を中心にデータを設計します。

### Main Tables
- `users`
- `practice_sessions`
- `ai_characters`
- `session_participants`
- `session_messages`
- `session_feedback`
- `feedback_metrics`

### users
Firebase Authentication のユーザと、PostgreSQL 上のアプリ内ユーザを結びつけるテーブルです。

主なカラム：
- `id`
- `firebase_uid`
- `email`
- `display_name`
- `photo_url`
- `onboarding_completed`

### practice_sessions
1回の練習セッションを表す中心テーブルです。

主なカラム：
- `id`
- `user_id`
- `status`
- `mode`
- `participant_count`
- `feedback_enabled`
- `theme`
- `presentation_duration_sec`
- `presentation_qa_count`
- `user_goal`
- `user_concerns`
- `session_brief`
- `target_context`
- `overall_score`
- `feedback_summary`
- `started_at`
- `ended_at`

#### status
- `waiting`: 開始前
- `active`: 練習中
- `completed`: 正常終了
- `cancelled`: 中断
- `error`: 異常終了

### ai_characters
AIキャラクターのマスタテーブルです。

主なカラム：
- `id`
- `code`
- `name`
- `role`
- `strictness`
- `personality`
- `voice_style`
- `description`
- `is_active`

#### role
- `host`
- `audience`

### session_participants
各セッションに参加する AI インスタンスを表します。

主なカラム：
- `id`
- `session_id`
- `ai_character_id`
- `display_name`
- `role`
- `seat_index`
- `is_active`

### session_messages
セッション中の発話ログです。

主なカラム：
- `id`
- `session_id`
- `participant_id`
- `sequence_no`
- `content`
- `transcript_confidence`
- `created_at`

### session_feedback
セッション終了後に生成されるフィードバック本文です。

主なカラム：
- `id`
- `session_id`
- `user_id`
- `summary_title`
- `short_comment`
- `positive_points`
- `improvement_points`
- `closing_message`

### feedback_metrics
フィードバックに紐づく数値指標です。

主なカラム：
- `id`
- `feedback_id`
- `metric_key`
- `metric_value`
- `metric_label`
- `metric_unit`

---

## Tech Stack

### Frontend
- React / Next.js or similar
- Zoom-like practice UI
- Camera / microphone controls

### Backend
- FastAPI
- SQLAlchemy 2.x
- Alembic
- PostgreSQL

### Authentication
- Firebase Authentication
- Google Login
- Apple Login

### Infrastructure
- Docker / Docker Compose
- Local PostgreSQL
- Cloud SQL for PostgreSQL (production)

---

## Local Development

### Prerequisites
- Docker
- Docker Compose
- Python 3.11+（ローカル実行時）

### Start
プロジェクトルートで以下を実行します。

```bash
docker compose up --build
```

### Health Check
バックエンド起動後、以下にアクセスします。

```text
http://localhost:8000/health
```

---

## Project Structure

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

### Directory Roles

| Directory | Role |
|----------|------|
| `app/api/routes` | FastAPI routes |
| `app/core` | Config / settings |
| `app/db/models` | SQLAlchemy models |
| `app/db/migrations` | Alembic migrations |
| `app/repositories` | DB access layer |
| `app/services` | Business logic |
| `app/schemas` | Request / response schemas |
| `tests` | Test code |

---

## Development Roadmap

### Phase 1
- [x] Backend project structure
- [x] Docker setup
- [x] Health check endpoint
- [ ] DB connection setup
- [ ] Alembic initialization

### Phase 2
- [ ] `users` table
- [ ] Firebase Auth integration
- [ ] User creation / sync API

### Phase 3
- [ ] `practice_sessions`
- [ ] `ai_characters`
- [ ] `session_participants`
- [ ] Session creation flow

### Phase 4
- [ ] `session_messages`
- [ ] `session_feedback`
- [ ] `feedback_metrics`

### Phase 5
- [ ] Frontend integration
- [ ] Practice room UI
- [ ] Feedback screen
- [ ] Learning history screen

---

## Notes
この README は現時点の設計メモを元にした初期版です。  
今後、実装に合わせて更新していきます。
