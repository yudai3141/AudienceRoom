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
        subgraph Frontend["フロントエンド"]
            CloudRun_FE["Cloud Run<br/>(Next.js)"]
        end

        subgraph Backend["バックエンド"]
            CloudRun_BE["Cloud Run<br/>(FastAPI)"]
        end

        subgraph Data["データ"]
            CloudSQL["Cloud SQL<br/>(PostgreSQL)"]
        end

        subgraph Auth["認証"]
            FirebaseAuth["Firebase<br/>Authentication"]
        end

        subgraph TTS["音声合成"]
            CloudRun_VV["Cloud Run<br/>(VOICEVOX)"]
        end
    end

    subgraph External["外部サービス"]
        LLM["Gemini API<br/>(Google AI)"]
    end

    Browser -->|HTTPS| CloudRun_FE
    Browser -->|Firebase SDK| FirebaseAuth
    Browser -->|"POST + SSE<br/>(テキスト + base64音声)"| CloudRun_BE
    CloudRun_BE -->|SQL| CloudSQL
    CloudRun_BE -->|"generate_stream()"| LLM
    CloudRun_BE -->|"audio_query + synthesis"| CloudRun_VV
    CloudRun_BE -->|"トークン検証"| FirebaseAuth
```

## 通信の流れ

```mermaid
sequenceDiagram
    participant B as ブラウザ
    participant FE as Cloud Run (Next.js)
    participant BE as Cloud Run (FastAPI)
    participant DB as Cloud SQL
    participant LLM as Gemini API
    participant VV as Cloud Run (VOICEVOX)
    participant FA as Firebase Auth

    Note over B: ブラウザ内 STT でテキスト化

    B->>FA: getIdToken()
    FA-->>B: JWT トークン

    B->>BE: POST /conversation/message/stream<br/>{session_id, message, generate_audio}
    BE->>FA: トークン検証
    BE->>DB: INSERT ユーザーメッセージ
    BE->>DB: SELECT 会話履歴

    BE->>LLM: generate_stream(prompt)
    loop テキストチャンクごと
        LLM-->>BE: LLMStreamChunk
        BE-->>B: SSE: text_chunk
    end

    loop 文の区切りごと
        BE->>VV: POST /audio_query + /synthesis
        VV-->>BE: WAV バイナリ
        BE-->>B: SSE: audio_chunk (base64)
    end

    BE->>DB: INSERT AI メッセージ
    BE-->>B: SSE: complete

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
