# AudienceRoom

## 1. Overview
**AudienceRoom** は、面接やプレゼンなど「人前で話す場面」を再現し、  
本番に近い緊張感の中で練習するためのアプリです。

少し厳しめの環境で練習することで、本番を少し楽に感じられるようにすることを目的としています。

> AudienceRoom = 「聴衆のいる部屋」

---

## 2. Table of Contents
1. [Overview](#1-overview)
2. [Quick Start](#3-quick-start)
3. [Concept](#4-concept)
4. [UI Flow](#5-ui-flow)
5. [Main Features](#6-main-features)
6. [System Architecture](#7-system-architecture)
7. [Backend Architecture](#8-backend-architecture)
8. [AI Integration Architecture](#9-ai-integration-architecture)
9. [Database Design](#10-database-design)
10. [Tech Stack](#11-tech-stack)
11. [Local Development](#12-local-development)
12. [Project Structure](#13-project-structure)
13. [Development Roadmap](#14-development-roadmap)

---

## 3. Quick Start

### 必要条件
- [ ] Docker / Docker Compose がインストールされている
- [ ] Gemini API Key を取得済み（[Google AI Studio](https://aistudio.google.com/) で取得）

### 起動手順

```bash
# 1. リポジトリをクローン
git clone https://github.com/yudai3141/AudienceRoom.git
cd AudienceRoom

# 2. 環境変数を設定
cp backend/.env.example backend/.env
# backend/.env を編集して GEMINI_API_KEY を設定

# 3. Docker で起動
docker compose up --build
```

### 動作確認チェックリスト

- [ ] http://localhost:3000 にアクセスできる
- [ ] http://localhost:8000/health が `{"status": "ok"}` を返す
- [ ] http://localhost:4000 で Firebase Emulator UI が表示される
- [ ] ログイン画面で新規アカウントを作成できる
- [ ] ダッシュボードが表示される
- [ ] 「新しい練習を始める」から練習を開始できる
- [ ] カメラ・マイクのアクセス許可後、セッションルームが表示される
- [ ] AIとの会話ができる
- [ ] 退出後、フィードバックが表示される

### アクセス先一覧

| サービス | URL | 説明 |
|----------|-----|------|
| アプリ | http://localhost:3000 | Next.js フロントエンド |
| API | http://localhost:8000 | FastAPI バックエンド |
| API ドキュメント | http://localhost:8000/docs | Swagger UI |
| Firebase Emulator UI | http://localhost:4000 | Auth Emulator 管理画面 |
| VOICEVOX | http://localhost:50021 | TTS エンジン |

### トラブルシューティング

**Q: `GEMINI_API_KEY` のエラーが出る**
- `backend/.env` に正しい API キーが設定されているか確認
- API キーは [Google AI Studio](https://aistudio.google.com/) で取得

**Q: マイクが使えない**
- Chrome ブラウザを使用してください（Web Speech API の互換性）
- `http://localhost:3000` でカメラ・マイクのアクセスを許可

**Q: 音声が再生されない**
- VOICEVOX コンテナが起動しているか確認: `docker compose ps`
- 初回起動時は VOICEVOX の起動に時間がかかることがあります

---

## 4. Concept
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

## 5. UI Flow

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

### 5.1 Login
- Email / Password
- Google Login
- Apple Login
- Firebase Authentication を使用

### 5.2 Home（Dashboard）
表示内容：
- 「今日の練習」ボタン
- 前回のフィードバックの一言
- これまでの練習回数
- 履歴ページへのリンク

### 5.3 練習設定
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

### 5.4 AudienceRoom（Zoom風UI）
必要なUI要素：
- 自分のカメラ ON/OFF
- 自分のマイク ON/OFF
- 退出ボタン
- 参加者の画面
- メモ欄

### 5.5 フィードバック画面
表示内容：
- 良かった点
- 改善点
- スコア
- 一言コメント
- 自信を持たせるフィードバック

### 5.6 学習履歴
例：

```text
3/20 面接練習 ★★★★☆
3/18 プレゼン ★★★☆☆
3/15 自由会話 ★★★★★
```

---

## 6. Main Features
- 面接練習
- プレゼン練習
- 自由会話練習
- AI面接官 / AI聴衆
- フィードバック生成
- スコアリング
- 練習履歴管理

---

## 7. System Architecture

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

## 8. Backend Architecture

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

### 8.1 Responsibilities

| Layer | Responsibility |
|------|---------------|
| routes | HTTP request / response |
| services | Business logic |
| repositories | Database access |
| models | Database schema |
| schemas | Request / Response schema |

---

## 9. AI Integration Architecture

### 9.1 Conversation Flow (SSE Streaming)

LLM のストリーミング出力と、文ごとの TTS 生成を並列で進めることで、応答の体感速度を最大化しています。

```text
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (Browser)                       │
├─────────────────────────────────────────────────────────────────┤
│  [ユーザー発話 → STT (Web Speech API, PTT 方式)]                 │
│       ↓                                                          │
│  [POST /conversation/message/stream]                             │
│       ↓                                                          │
│  [SSE 受信: text_chunk / audio_chunk / complete]                 │
│       ├─ text_chunk: 逐次画面に表示                               │
│       └─ audio_chunk: sequence 順でキューに入れて順次再生         │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                         Backend (FastAPI)                        │
├─────────────────────────────────────────────────────────────────┤
│  [POST /conversation/message/stream 受信]                        │
│       ↓                                                          │
│  [session_messages 保存（ユーザー発話）]                          │
│       ↓                                                          │
│  [asyncio.Queue による Producer-Consumer]                        │
│       ├─ Producer: LLM ストリーミング → 文の区切りで TTS 生成    │
│       └─ Consumer: SSE で text_chunk / audio_chunk を yield       │
│       ↓                                                          │
│  [session_messages 保存（AI応答）]                                │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│              VOICEVOX (Compute Engine, VPC 内)                   │
├─────────────────────────────────────────────────────────────────┤
│  [POST /audio_query] → [POST /synthesis] → WAV 返却              │
└─────────────────────────────────────────────────────────────────┘
```

**SSE イベント種別:**
- `metadata`: セッション情報（speaker など）
- `text_chunk`: LLM の出力テキスト（逐次）
- `audio_chunk`: TTS 生成済み音声（base64 + sequence）
- `complete`: 応答完了

### 9.2 Feedback Generation Flow

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

### 9.3 Technology Selection

| 機能 | 採用 | 将来拡張 | 説明 |
|------|-----|----------|------|
| STT | Web Speech API | Whisper | ブラウザ内蔵、無料、ペイロードが軽量 |
| LLM | Gemini 2.5 Flash (Google AI Studio) | Vertex AI 経由 Gemini / OpenAI GPT-4o | 高速・低コスト、日本語対応 |
| TTS | VOICEVOX (Compute Engine, VPC 内) | MIG による水平スケール | 高品質日本語音声、キャラクター音声対応 |
| 通信 | SSE ストリーミング | Pub/Sub 分離 + Cloud Storage 音声配信 | 体感速度を最大化 |

**LLM Provider 設計:**
- `LLMProvider` インターフェースで抽象化
- `GeminiProvider` / `OpenAIProvider` を実装
- 環境変数で切り替え可能（`LLM_PROVIDER=gemini|openai`）

### 9.4 AI Module File Structure

```text
backend/app/
├── services/
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── llm/
│   │   │   ├── __init__.py
│   │   │   ├── base.py                          # LLMProvider 抽象クラス
│   │   │   ├── gemini.py                        # GeminiProvider
│   │   │   ├── openai.py                        # OpenAIProvider
│   │   │   └── factory.py                       # get_llm_provider()
│   │   ├── streaming_conversation_service.py    # SSE ストリーミング会話
│   │   ├── feedback_generator.py                # FB 生成
│   │   └── tts_service.py                       # VOICEVOX TTS
│   └── prompts/
│       ├── interview.py                         # 面接用
│       ├── presentation.py                      # プレゼン用
│       └── feedback.py                          # FB 生成用
├── api/routes/
│   └── conversation.py                          # POST /conversation/message/stream

frontend/src/features/sessions/
├── hooks/
│   ├── useSpeechRecognition.ts                  # STT (Web Speech API, PTT 方式)
│   └── useStreamingConversation.ts              # SSE 通信 + 音声キュー再生
├── components/
│   └── SessionRoom.tsx                          # 統合
├── lib/api/
│   └── sse.ts                                   # SSE パーサ (ReadableStream)
```

### 9.5 VOICEVOX Integration

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

### 9.6 Prompt Design Principles

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

## 10. Database Design

このアプリの中心は **「1回の練習 = 1セッション」** です。  
そのため `practice_sessions` を中心にデータを設計します。

### 10.1 Main Tables
- `users`
- `practice_sessions`
- `ai_characters`
- `session_participants`
- `session_messages`
- `session_feedback`
- `feedback_metrics`

### 10.2 users

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

### 10.3 practice_sessions

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

### 10.4 ai_characters

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

### 10.5 session_participants

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

### 10.6 session_messages

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

### 10.7 session_feedback

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

### 10.8 feedback_metrics

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

## 11. Tech Stack

### 11.1 Frontend
- Next.js 16 (App Router / TypeScript)
- Tailwind CSS v4
- openapi-fetch（型安全な API クライアント）
- openapi-typescript（OpenAPI → TypeScript 型自動生成）

### 11.2 Backend
- FastAPI
- SQLAlchemy 2.x
- Alembic
- PostgreSQL 16
- firebase-admin SDK

### 11.3 Authentication
- Firebase Authentication
- Firebase Auth Emulator（ローカル開発）

### 11.4 Infrastructure
- **ローカル**: Docker Compose（Frontend / Backend / DB / VOICEVOX / Firebase Emulator Suite）
- **本番 (GCP)**:
  - Cloud Run（Frontend / Backend）
  - Compute Engine（VOICEVOX、VPC 内で常時起動）
  - Cloud SQL for PostgreSQL（マネージド DB）
  - Serverless VPC Connector（Cloud Run -> VPC 内通信）
  - Artifact Registry（Docker イメージ管理）
  - Firebase Authentication（本番）

詳細は [`docs/deploy-guide.md`](./docs/deploy-guide.md) と [`docs/cloud/`](./docs/cloud/) を参照。

### 11.5 CI/CD
- GitHub Actions
  - Backend CI（pytest + Firebase Emulator）
  - OpenAPI Schema Check（spec と型の一致検証）

---

## 12. Local Development

### 12.1 Prerequisites
- Docker
- Docker Compose
- Node.js 20+（ローカル実行時）
- Python 3.11+（ローカル実行時）

### 12.2 Start
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

### 12.3 Health Check

```text
http://localhost:8000/health
http://localhost:8000/health/db
```

### 12.4 API Docs

```text
http://localhost:8000/docs
```

### 12.5 OpenAPI 型生成

```bash
make generate-api
```

---

## 13. Project Structure

```text
AudienceRoom/
├── frontend/
│   ├── src/
│   │   ├── app/                # Next.js App Router（routing only）
│   │   ├── features/           # Feature logic
│   │   ├── components/         # Reusable UI components
│   │   ├── lib/api/            # API client + SSE parser
│   │   ├── generated/          # OpenAPI 自動生成型
│   │   ├── hooks/              # Reusable hooks
│   │   └── types/              # Manual types
│   ├── Dockerfile              # ローカル開発用
│   ├── Dockerfile.prod         # 本番ビルド (Next.js standalone)
│   └── package.json
├── backend/
│   ├── app/
│   │   ├── api/routes/         # FastAPI routes
│   │   ├── core/               # Config / Auth / Firebase
│   │   ├── db/
│   │   │   ├── models/         # SQLAlchemy models
│   │   │   └── migrations/     # Alembic migrations
│   │   ├── repositories/       # DB access layer
│   │   ├── schemas/            # Request / response schemas
│   │   ├── services/           # Business logic（AI / プロンプト等）
│   │   └── main.py
│   ├── scripts/                # OpenAPI export 等のスクリプト
│   ├── tests/
│   ├── Dockerfile              # ローカル開発用
│   ├── Dockerfile.prod         # 本番ビルド
│   └── pyproject.toml
├── firebase/
│   ├── firebase.json           # Emulator config
│   └── Dockerfile
├── docs/
│   ├── deploy-guide.md         # GCP デプロイ手順
│   └── cloud/                  # クラウドアーキテクチャ図 (Phase 1 / 2)
├── .github/workflows/          # CI workflows
├── docker-compose.yml
├── Makefile
├── openapi.json                # OpenAPI spec（自動生成）
├── README.md
└── AGENTS.md
```

---

## 14. Development Roadmap

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

### Phase 7: AI 連携 ✅

#### Phase 7-1: LLM 基盤
- [x] `LLMProvider` 抽象クラス（`services/ai/llm/base.py`）
- [x] `GeminiProvider` 実装（MVP）
- [x] `OpenAIProvider` 実装（将来用）
- [x] 環境変数設定（`LLM_PROVIDER`, `GEMINI_API_KEY`, `OPENAI_API_KEY`）
- [x] 基本プロンプトテンプレート

#### Phase 7-2: フィードバック生成
- [x] FB 生成サービス（`services/ai/feedback_generator.py`）
- [x] FB 生成プロンプト（`services/prompts/feedback.py`）
- [x] `POST /practice-sessions/{id}/generate-feedback` API
- [x] 既存の `session_feedback` + `feedback_metrics` に保存

#### Phase 7-3: VOICEVOX TTS
- [x] VOICEVOX Docker 追加（`docker-compose.yml`）
- [x] TTS サービス（`services/ai/tts_service.py`）
- [x] キャラクター音声設定

#### Phase 7-4: 会話 API
- [x] 会話プロンプト（面接 / プレゼン用）
- [x] 会話サービス（`services/ai/conversation_service.py`）
- [x] `POST /conversation/message` エンドポイント

### Phase 8: AudienceRoom 統合 ✅

#### Phase 8-1: Frontend STT
- [x] `useSpeechRecognition` フック（Web Speech API）
- [x] 無音検知による発話終了検出
- [x] リアルタイム文字起こし表示

#### Phase 8-2: 会話通信
- [x] `useConversation` フック（REST API）
- [x] SessionRoom に統合
- [x] VOICEVOX 音声の再生

#### Phase 8-3: 会話 UI
- [x] 参加者情報の表示
- [x] 会話ログの表示
- [x] ターン管理（誰が話しているか）
- [x] セッション設定の表示
- [x] フィードバック生成オーバーレイ

#### Phase 8-4: ストリーミング応答 ✅
- [x] SSE による LLM ストリーミング
- [x] 文の区切りごとの逐次 TTS 生成（asyncio.Queue Producer-Consumer）
- [x] フロントエンド側の音声キュー再生（sequence 順）
- [x] PTT (Push-to-Talk) 方式の発話入力

### Phase 9: 本番デプロイ ✅
- [x] 本番用 Dockerfile（Backend / Frontend）
- [x] Cloud Run デプロイ（Frontend / Backend）
- [x] Cloud SQL for PostgreSQL（Unix ソケット接続）
- [x] Firebase Authentication（本番）
- [x] Artifact Registry によるイメージ管理
- [x] VOICEVOX を Compute Engine に移行（コールドスタート回避）
- [x] VPC + Serverless VPC Connector 構築

### Phase 10: スケーリング・拡張 🔜

優先度順:

#### Phase 10-1: VOICEVOX 並列化
- [ ] Managed Instance Group (MIG) で水平スケール
- [ ] 内部ロードバランサ経由でアクセス
- [ ] スケーリングポリシー（CPU 使用率ベース）

#### Phase 10-2: Secret Manager 移行
- [ ] DB パスワード / Firebase 設定 / Gemini API Key を Secret Manager に
- [ ] Cloud Run から `--set-secrets` で参照
- [ ] ローカルは `.env` のまま（Docker Compose）

#### Phase 10-3: Vertex AI 経由 Gemini
- [ ] `LLMProvider` に Vertex AI 実装を追加
- [ ] サービスアカウント認証への切り替え
- [ ] API Key 管理を不要化

#### Phase 10-4: ユーザー知識グラフ
- [ ] ユーザーの過去セッションから関心領域・弱点を抽出
- [ ] 知識グラフ（テーマ・スキル・改善点の関連）を構築
- [ ] AI のプロンプトに反映してパーソナライズ

### Phase 11: さらにスケールが必要になったら（Phase 2 設計）
- [ ] SSE ゲートウェイ + Cloud Pub/Sub による接続層分離
- [ ] Cloud Storage + CDN による音声配信分離
- [ ] Cloud Load Balancing + 独自ドメイン

詳細は [`docs/cloud/phase2_scaling.md`](./docs/cloud/phase2_scaling.md) 参照。
