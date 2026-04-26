# Phase 1: 初期デプロイ構成

## 概要

MVP / 少人数利用を想定したシンプルな構成。
現在のコードベースをそのまま Cloud Run にデプロイできる。

## アーキテクチャ図

```mermaid
flowchart TB
    subgraph Client["クライアント"]
        Browser["ブラウザ"]
    end

    subgraph GCP["Google Cloud Platform"]
        LB["Cloud Load Balancing<br/>(HTTPS 終端 / パスルーティング)"]

        subgraph VPC["VPC (プライベートネットワーク)"]
            subgraph Frontend["フロントエンド"]
                CloudRun_FE["Cloud Run<br/>(Next.js)"]
            end

            subgraph Backend["バックエンド"]
                CloudRun_BE["Cloud Run<br/>(FastAPI)"]
            end

            subgraph TTS["音声合成"]
                CloudRun_VV["Cloud Run<br/>(VOICEVOX)"]
            end

            subgraph Data["データ"]
                CloudSQL["Cloud SQL<br/>(PostgreSQL)"]
            end
        end

        subgraph CI["イメージ管理"]
            AR["Artifact Registry<br/>(Docker イメージ)"]
        end

        subgraph Auth["認証"]
            FirebaseAuth["Firebase<br/>Authentication"]
        end
    end

    subgraph External["外部サービス"]
        LLM["Gemini API<br/>(Google AI)"]
    end

    Browser -->|HTTPS| LB
    LB -->|"/*"| CloudRun_FE
    LB -->|"/api/*"| CloudRun_BE
    Browser -->|Firebase SDK| FirebaseAuth

    CloudRun_BE -->|"プライベート IP"| CloudSQL
    CloudRun_BE -->|"VPC 内通信"| CloudRun_VV
    CloudRun_BE -->|generate_stream| LLM
    CloudRun_BE -->|トークン検証| FirebaseAuth

    AR -.->|pull| CloudRun_FE
    AR -.->|pull| CloudRun_BE
    AR -.->|pull| CloudRun_VV
```

**Cloud Load Balancing**: ブラウザからの全 HTTPS リクエストの入口。TLS 終端、パスベースルーティング（`/*` → Next.js、`/api/*` → FastAPI）、DDoS 防御を担う。SSE 接続もここを通るため、タイムアウト設定の延長（デフォルト30秒 → 数分）が必要。

**VPC**: Cloud SQL、VOICEVOX、FastAPI 間の通信はプライベートネットワーク内で完結する。Cloud SQL はパブリック IP を持たず、VPC 内からのみアクセス可能。

**Artifact Registry**: Cloud Build や GitHub Actions で Docker イメージをビルドし、ここに push する。各 Cloud Run サービスはデプロイ時にここからイメージを pull する。

## 通信の流れ

```mermaid
sequenceDiagram
    participant B as ブラウザ
    participant LB as Cloud LB
    participant BE as FastAPI
    participant DB as Cloud SQL
    participant LLM as Gemini API
    participant VV as VOICEVOX
    participant FA as Firebase Auth

    Note over B: ブラウザ内 STT でテキスト化

    B->>FA: getIdToken()
    FA-->>B: JWT トークン

    B->>LB: POST /api/conversation/message/stream
    LB->>BE: ルーティング (/api/* → FastAPI)
    BE->>FA: トークン検証
    BE->>DB: INSERT ユーザーメッセージ
    BE->>DB: SELECT 会話履歴

    BE->>LLM: generate_stream(prompt)
    loop テキストチャンクごと
        LLM-->>BE: LLMStreamChunk
        BE-->>LB: SSE: text_chunk
        LB-->>B: SSE: text_chunk
    end

    loop 文の区切りごと
        BE->>VV: POST /audio_query + /synthesis
        Note over BE,VV: VPC 内通信
        VV-->>BE: WAV バイナリ
        BE-->>LB: SSE: audio_chunk (base64)
        LB-->>B: SSE: audio_chunk (base64)
    end

    BE->>DB: INSERT AI メッセージ
    BE-->>LB: SSE: complete
    LB-->>B: SSE: complete

    Note over B: Audio API で音声再生
```

## 各コンポーネントの設定

| コンポーネント | Cloud Run 設定 | 備考 |
|--------------|---------------|------|
| Next.js | CPU: 1, Memory: 512Mi, min: 0, max: 10 | 静的配信が主。負荷は低い |
| FastAPI | CPU: 2, Memory: 1Gi, min: 1, max: 20 | SSE 接続を保持するため min=1 推奨 |
| VOICEVOX | CPU: 2, Memory: 2Gi, min: 0, max: 5 | 音声合成は CPU バウンド |
| Cloud SQL | db-f1-micro → db-g1-small | セッション数に応じてスケールアップ |

## この構成の限界

| 問題 | 原因 | 影響が出る目安 |
|------|------|--------------|
| SSE 接続数の上限 | FastAPI コンテナが接続保持 + LLM/TTS 処理の両方を担う | 同時 50〜100 人 |
| 音声転送の帯域 | base64 WAV (1応答 200〜600KB) が SSE を通過 | SSE 接続時間が長引き、上記を悪化 |
| VOICEVOX のレイテンシ | 1文ごとに HTTP リクエスト（直列） | 長い応答で音声再生が遅れる |

これらの限界を超えるには [Phase 2](./phase2_scaling.md) の構成が必要。
