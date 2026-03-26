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
7. [AI Integration Architecture](#8-ai-integration-architecture)
8. [Database Design](#9-database-design)
9. [Tech Stack](#10-tech-stack)
10. [Local Development](#11-local-development)
11. [Project Structure](#12-project-structure)
12. [Development Roadmap](#13-development-roadmap)

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

## 8. AI Integration Architecture

### 8.1 Conversation Flow (MVP: REST API)

```text
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (Browser)                       │
├─────────────────────────────────────────────────────────────────┤
│  [ユーザー発話開始]                                               │
│       ↓                                                          │
│  [STT: Web Speech API] ← 無音検知で自動停止                       │
│       ↓                                                          │
│  [onend イベント: 発話終了検知]                                   │
│       ↓                                                          │
│  [POST /conversation/message] ─────────┐                         │
│                                        │                         │
│  [Response: テキスト + 音声] ←─────────┼─────────┐               │
│       ↓                                │         │               │
│  [音声再生 (WAV)]                       │         │               │
│       ↓                                │         │               │
│  [再生完了 → 次の発話待ち]              │         │               │
└────────────────────────────────────────┼─────────┼───────────────┘
                                         │         │
┌────────────────────────────────────────┼─────────┼───────────────┐
│                         Backend (FastAPI)        │               │
├────────────────────────────────────────┼─────────┼───────────────┤
│                                        ↓         │               │
│  [POST /conversation/message 受信]               │               │
│       ↓                                          │               │
│  [session_messages に保存（ユーザー発話）]        │               │
│       ↓                                          │               │
│  [LLM API (Gemini): 応答生成]                    │               │
│       ↓                                          │               │
│  [session_messages に保存（AI応答）]              │               │
│       ↓                                          │               │
│  [VOICEVOX: TTS 音声生成]                         │               │
│       ↓                                          │               │
│  [Response: { text, audio_base64 }] ─────────────┘               │
└─────────────────────────────────────────────────────────────────┘
                                         │
┌────────────────────────────────────────┼─────────────────────────┐
│                         VOICEVOX (Docker)                        │
├──────────────────────────────────────────────────────────────────┤
│  [POST /audio_query] → [POST /synthesis] → 音声データ返却        │
└──────────────────────────────────────────────────────────────────┘
```

**将来拡張: WebSocket**
- リアルタイムストリーミング応答が必要な場合に検討
- LLM のストリーミング出力 + 逐次 TTS 生成

### 8.2 Feedback Generation Flow

```text
[セッション中]
    ↓
[退出ボタン or 時間終了]
    ↓
[POST /practice-sessions/{id}/status → completed]
    ↓
[POST /practice-sessions/{id}/generate-feedback]
    ↓
[session_messages 全取得]
    ↓
[LLM API: フィードバック生成プロンプト実行]
    ↓
[session_feedback + feedback_metrics 保存]
    ↓
[practice_sessions.overall_score 更新]
    ↓
[Frontend: /sessions/{id}/result にリダイレクト]
```

### 8.3 Technology Selection

| 機能 | MVP | 将来拡張 | 説明 |
|------|-----|----------|------|
| STT | Web Speech API | Whisper | ブラウザ内蔵、無料 |
| LLM | Gemini 2.5 Flash | OpenAI GPT-4o | 高速・低コスト、日本語対応 |
| TTS | VOICEVOX (Docker) | - | 高品質日本語音声、キャラクター音声対応 |

**LLM Provider 設計:**
- `LLMProvider` インターフェースで抽象化
- `GeminiProvider` / `OpenAIProvider` を実装
- 環境変数で切り替え可能（`LLM_PROVIDER=gemini|openai`）

### 8.4 AI Module File Structure

```text
backend/app/
├── services/
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── llm/
│   │   │   ├── __init__.py
│   │   │   ├── base.py              # LLMProvider 抽象クラス
│   │   │   ├── gemini.py            # GeminiProvider
│   │   │   ├── openai.py            # OpenAIProvider（将来用）
│   │   │   └── factory.py           # get_llm_provider()
│   │   ├── conversation_service.py  # 会話ロジック
│   │   ├── feedback_generator.py    # FB 生成ロジック
│   │   └── tts_service.py           # VOICEVOX TTS
│   └── prompts/
│       ├── __init__.py
│       ├── interview.py             # 面接用プロンプト
│       ├── presentation.py          # プレゼン用プロンプト
│       └── feedback.py              # FB 生成用プロンプト
├── api/routes/
│   └── conversation.py              # POST /conversation/message

frontend/src/features/sessions/
├── hooks/
│   ├── useSpeechRecognition.ts      # STT (Web Speech API + 無音検知)
│   └── useConversation.ts           # REST API 通信 + 音声再生
├── components/
│   └── SessionRoom.tsx              # 統合
```

### 8.5 VOICEVOX Integration

```yaml
# docker-compose.yml に追加
voicevox:
  image: voicevox/voicevox_engine:cpu-ubuntu20.04-latest
  ports:
    - "50021:50021"
```

**使用方法:**
```python
# 1. 音声クエリ生成
response = requests.post(
    "http://voicevox:50021/audio_query",
    params={"text": "こんにちは", "speaker": 1}
)
query = response.json()

# 2. 音声合成
audio = requests.post(
    "http://voicevox:50021/synthesis",
    params={"speaker": 1},
    json=query
)
# audio.content に WAV データ
```

### 8.6 Prompt Design Principles

1. **キャラクター設定**
   - 面接官 / 聴衆の役割を明確に
   - strictness（gentle / normal / hard）に応じた応答トーン

2. **コンテキスト維持**
   - セッション設定（mode, theme, user_goal, user_concerns）を含める
   - 直近の会話履歴を含める

3. **フィードバック生成**
   - positive_points: 3-5 個の具体的な良い点
   - improvement_points: 2-3 個の建設的な改善提案
   - overall_score: 0-100 の総合評価
   - closing_message: 励ましのメッセージ

---

## 9. Database Design

このアプリの中心は **「1回の練習 = 1セッション」** です。  
そのため `practice_sessions` を中心にデータを設計します。

### 9.1 Main Tables
- `users`
- `practice_sessions`
- `ai_characters`
- `session_participants`
- `session_messages`
- `session_feedback`
- `feedback_metrics`

### 9.2 users

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

### 9.3 practice_sessions

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

### 9.4 ai_characters

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

### 9.5 session_participants

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

### 9.6 session_messages

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

### 9.7 session_feedback

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

### 9.8 feedback_metrics

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

## 10. Tech Stack

### 10.1 Frontend
- Next.js 16 (App Router / TypeScript)
- Tailwind CSS v4
- openapi-fetch（型安全な API クライアント）
- openapi-typescript（OpenAPI → TypeScript 型自動生成）

### 10.2 Backend
- FastAPI
- SQLAlchemy 2.x
- Alembic
- PostgreSQL 16
- firebase-admin SDK

### 10.3 Authentication
- Firebase Authentication
- Firebase Auth Emulator（ローカル開発）

### 10.4 Infrastructure
- Docker / Docker Compose
- Firebase Emulator Suite
- Cloud Run + Cloud SQL for PostgreSQL（本番想定）

### 10.5 CI/CD
- GitHub Actions
  - Backend CI（pytest + Firebase Emulator）
  - OpenAPI Schema Check（spec と型の一致検証）

---

## 11. Local Development

### 11.1 Prerequisites
- Docker
- Docker Compose
- Node.js 20+（ローカル実行時）
- Python 3.11+（ローカル実行時）

### 11.2 Start
プロジェクトルートで以下を実行します。

```bash
docker compose up --build
```

以下のサービスが起動します。

| サービス | URL | 説明 |
|---|---|---|
| Frontend | http://localhost:3000 | Next.js |
| Backend | http://localhost:8000 | FastAPI |
| DB | localhost:5432 | PostgreSQL |
| Firebase Emulator | http://localhost:9099 | Auth Emulator |
| Firebase Emulator UI | http://localhost:4000 | Emulator 管理画面 |

### 11.3 Health Check

```text
http://localhost:8000/health
http://localhost:8000/health/db
```

### 11.4 API Docs

```text
http://localhost:8000/docs
```

### 11.5 OpenAPI 型生成

```bash
make generate-api
```

---

## 12. Project Structure

```text
AudienceRoom/
├── frontend/
│   ├── src/
│   │   ├── app/            # Next.js App Router（routing only）
│   │   ├── features/       # Feature logic
│   │   ├── components/     # Reusable UI components
│   │   ├── lib/api/        # API client + generated types
│   │   ├── hooks/          # Reusable hooks
│   │   └── types/          # Manual types
│   ├── Dockerfile
│   └── package.json
├── backend/
│   ├── app/
│   │   ├── api/routes/     # FastAPI routes
│   │   ├── core/           # Config / Auth / Firebase
│   │   ├── db/
│   │   │   ├── models/     # SQLAlchemy models
│   │   │   └── migrations/ # Alembic migrations
│   │   ├── repositories/   # DB access layer
│   │   ├── schemas/        # Request / response schemas
│   │   ├── services/       # Business logic
│   │   └── main.py
│   ├── scripts/            # Utility scripts
│   ├── tests/
│   ├── Dockerfile
│   └── pyproject.toml
├── firebase/
│   ├── firebase.json       # Emulator config
│   └── Dockerfile
├── .github/workflows/      # CI workflows
├── docker-compose.yml
├── Makefile
├── openapi.json            # Auto-generated OpenAPI spec
├── README.md
└── AGENTS.md
```

---

## 13. Development Roadmap

### Phase 1: Backend 基盤 ✅
- [x] Backend project structure + Docker setup
- [x] DB 接続（SQLAlchemy + PostgreSQL）
- [x] Alembic 初期化
- [x] Health check endpoint

### Phase 2: Core Tables ✅
- [x] `users` テーブル + CRUD API
- [x] `ai_characters` テーブル + CRUD API
- [x] `practice_sessions` テーブル + CRUD API + ステータス遷移
- [x] `session_participants` テーブル + CRUD API（一括登録対応）

### Phase 3: Session Data Tables ✅
- [x] `session_messages` テーブル + CRUD API
- [x] `session_feedback` テーブル + CRUD API
- [x] `feedback_metrics` テーブル + CRUD API（一括登録対応）

### Phase 4: 認証・API 拡張 ✅
- [x] Firebase Authentication 導入（firebase-admin SDK）
- [x] Firebase Auth Emulator（Docker 統合）
- [x] `POST /auth/login`（token 検証 → ユーザ取得 or 作成）
- [x] `GET /users/me`（認証済みユーザ情報取得）
- [x] OpenAPI → TypeScript 型自動生成パイプライン
- [x] CI: OpenAPI spec と型の一致チェック

### Phase 5: API 拡張 ✅
- [x] セッション詳細統合 API（participants + messages + feedback + metrics）
- [x] セッション一覧ページネーション + FB 有無フラグ
- [x] ダッシュボード用サマリー API
- [x] SessionParticipant に AI キャラ情報ネスト

### Phase 6: Frontend UI ✅
- [x] ログイン画面（Firebase Client SDK）
- [x] ダッシュボード画面
- [x] セッション作成フロー（設定画面）
- [x] 履歴一覧画面
- [x] セッションルーム（カメラ / マイク制御）
- [x] フィードバック表示画面

### Phase 7: AI 連携 🔜

#### Phase 7-1: LLM 基盤
- [ ] `LLMProvider` 抽象クラス（`services/ai/llm/base.py`）
- [ ] `GeminiProvider` 実装（MVP）
- [ ] `OpenAIProvider` 実装（将来用）
- [ ] 環境変数設定（`LLM_PROVIDER`, `GEMINI_API_KEY`, `OPENAI_API_KEY`）
- [ ] 基本プロンプトテンプレート

#### Phase 7-2: フィードバック生成
- [ ] FB 生成サービス（`services/ai/feedback_generator.py`）
- [ ] FB 生成プロンプト（`services/prompts/feedback.py`）
- [ ] `POST /practice-sessions/{id}/generate-feedback` API
- [ ] 既存の `session_feedback` + `feedback_metrics` に保存

#### Phase 7-3: VOICEVOX TTS
- [ ] VOICEVOX Docker 追加（`docker-compose.yml`）
- [ ] TTS サービス（`services/ai/tts_service.py`）
- [ ] キャラクター音声設定

#### Phase 7-4: 会話 API
- [ ] 会話プロンプト（面接 / プレゼン用）
- [ ] 会話サービス（`services/ai/conversation_service.py`）
- [ ] `POST /conversation/message` エンドポイント

### Phase 8: AudienceRoom 統合

#### Phase 8-1: Frontend STT
- [ ] `useSpeechRecognition` フック（Web Speech API）
- [ ] 無音検知による発話終了検出
- [ ] リアルタイム文字起こし表示

#### Phase 8-2: 会話通信
- [ ] `useConversation` フック（REST API）
- [ ] SessionRoom に統合
- [ ] VOICEVOX 音声の再生

#### Phase 8-3: 会話 UI
- [ ] 参加者情報の表示
- [ ] 会話ログの表示
- [ ] ターン管理（誰が話しているか）

#### Phase 8-4: 将来拡張（WebSocket）
- [ ] リアルタイムストリーミング応答
- [ ] LLM ストリーミング + 逐次 TTS

### Phase 9: 仕上げ
- [ ] E2E テスト
- [ ] パフォーマンス最適化
- [ ] 本番デプロイ（Cloud Run + Cloud SQL）
