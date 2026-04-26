# Phase 2: スケーリング構成

## 概要

Phase 1 の2つの限界を、クラウドインフラの分離で解決する。

| 課題 | 解決策 | 分離の考え方 |
|------|--------|------------|
| SSE 接続がコンテナを占有する | Cloud Pub/Sub で「接続保持」と「重い処理」を分離 | 接続保持 → SSE ゲートウェイ、計算 → ワーカー |
| base64 音声が SSE 帯域を圧迫する | Cloud Storage + Signed URL で音声配信を分離 | 音声配信 → Cloud Storage (+ Cloud CDN) |
| VOICEVOX が単一インスタンスでスケールしない | MIG（マネージドインスタンスグループ）+ 内部 LB で水平スケール | 負荷に応じてインスタンス数を自動調整 |

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

            subgraph SSELayer["SSE 接続層 (軽量)"]
                CloudRun_GW["Cloud Run<br/>(SSE ゲートウェイ)"]
            end

            subgraph Worker["ワーカー層 (重い処理)"]
                CloudRun_WK["Cloud Run<br/>(FastAPI ワーカー)"]
            end

            subgraph TTS["音声合成 (GCE MIG)"]
                ILB_VV["内部ロードバランサ"]
                GCE_VV["Compute Engine MIG<br/>(VOICEVOX × N台)"]
            end

            subgraph Data["データ"]
                CloudSQL["Cloud SQL<br/>(PostgreSQL)"]
            end
        end

        subgraph Messaging["メッセージング"]
            PubSub["Cloud Pub/Sub"]
        end

        subgraph Storage["音声配信"]
            GCS["Cloud Storage"]
            CDN["Cloud CDN"]
        end

        subgraph CI["イメージ管理"]
            AR["Artifact Registry<br/>(Docker イメージ)"]
        end

        subgraph Auth["認証"]
            FirebaseAuth["Firebase<br/>Authentication"]
        end
    end

    subgraph External["外部サービス"]
        LLM["Gemini API"]
    end

    Browser -->|HTTPS| LB
    LB -->|"/*"| CloudRun_FE
    LB -->|"/api/stream/*"| CloudRun_GW
    Browser -->|Firebase SDK| FirebaseAuth

    CloudRun_GW -->|subscribe| PubSub
    CloudRun_GW -->|"VPC 内通信"| CloudRun_WK

    CloudRun_WK -->|publish| PubSub
    CloudRun_WK -->|"プライベート IP"| CloudSQL
    CloudRun_WK -->|generate_stream| LLM
    CloudRun_WK -->|"VPC 内通信"| ILB_VV
    ILB_VV --> GCE_VV
    CloudRun_WK -->|"WAV アップロード"| GCS
    CloudRun_WK -->|トークン検証| FirebaseAuth

    GCS --> CDN
    Browser -->|"音声ダウンロード"| CDN

    AR -.->|pull| CloudRun_FE
    AR -.->|pull| CloudRun_GW
    AR -.->|pull| CloudRun_WK
    AR -.->|pull| GCE_VV
```

**Cloud Load Balancing**: Phase 1 と同様に全リクエストの入口。パスルーティングで SSE ストリーミング系（`/api/stream/*`）を SSE ゲートウェイに振り分ける。

**VPC**: Cloud SQL、VOICEVOX、FastAPI ワーカー、SSE ゲートウェイ間の通信はプライベートネットワーク内で完結。Cloud Pub/Sub と Cloud Storage は VPC 外のマネージドサービスだが、VPC Service Controls で制限可能。

**Compute Engine MIG (VOICEVOX)**: Phase 1 の単一 GCE インスタンスを、マネージドインスタンスグループ（MIG）+ 内部ロードバランサに拡張。CPU 使用率に応じてインスタンス数を自動スケールする。ワーカーからは内部 LB の単一エンドポイントでアクセスするため、コード変更は不要。

**Artifact Registry**: Phase 1 に加え、SSE ゲートウェイのイメージも管理する。

## 通信の流れ

```mermaid
sequenceDiagram
    participant B as ブラウザ
    participant LB as Cloud LB
    participant GW as SSE ゲートウェイ
    participant PS as Cloud Pub/Sub
    participant WK as FastAPI ワーカー
    participant DB as Cloud SQL
    participant LLM as Gemini API
    participant VV as VOICEVOX (GCE MIG)
    participant GCS as Cloud Storage / CDN

    B->>LB: POST /api/stream/conversation/message
    LB->>GW: ルーティング (/api/stream/* → GW)
    GW->>GW: SSE 接続を開く
    GW->>PS: subscribe(session_id)
    GW->>WK: リクエス��転送 (VPC 内通信)

    Note over WK: 重い処理はここで実行

    WK->>DB: INSERT ユーザーメッセージ
    WK->>DB: SELECT 会話履歴

    WK->>LLM: generate_stream(prompt)
    loop テキストチャンクごと
        LLM-->>WK: LLMStreamChunk
        WK->>PS: publish(text_chunk)
        PS-->>GW: deliver(text_chunk)
        GW-->>LB: SSE: text_chunk
        LB-->>B: SSE: text_chunk
    end

    loop 文の区切りごと
        WK->>VV: POST /audio_query + /synthesis
        Note over WK,VV: VPC 内通信
        VV-->>WK: WAV バイ��リ
        WK->>GCS: WAV アップロード + Signed URL 生成
        WK->>PS: publish(audio_chunk + URL)
        PS-->>GW: deliver(audio_chunk)
        GW-->>LB: SSE: audio_chunk {audio_url, sequence}
        LB-->>B: SSE: audio_chunk {audio_url, sequence}
        B->>GCS: GET audio_url (CDN 経由)
        GCS-->>B: WAV バイナリ
    end

    WK->>DB: INSERT AI メッセージ
    WK->>PS: publish(complete)
    PS-->>GW: deliver(complete)
    GW-->>LB: SSE: complete
    LB-->>B: SSE: complete
    GW->>GW: SSE 接続を閉じる

    Note over B: Audio API で音声再生
```

## Phase 1 からの変更点

### 1. SSE ゲートウェイの導入

Phase 1 では FastAPI コンテナが SSE 接続を保持しつつ LLM/TTS の重い処理を行っていたため、
1接続 = 1コンテナの concurrency 枠を長時間占有していた。

Phase 2 では SSE ゲートウェイが接続保持のみを担う。
処理は「Pub/Sub からメッセージを受け取り、SSE で転送する」だけなので非常に軽く、
1インスタンスで数千接続を捌ける。

```
Phase 1:
  [コンテナ] = SSE 接続保持 + LLM 呼び出し + TTS 生成
  → 1接続で concurrency 1枠を 10秒占有
  → 80並列で飽和

Phase 2:
  [SSE ゲートウェイ] = Pub/Sub → SSE 転送のみ
  → 1インスタンスで数千接続可能
  → CPU をほぼ使わない

  [ワーカー] = LLM + TTS 処理のみ
  → 処理が終わったら即解放
  → 接続を保持しない
```

### 2. Cloud Storage + Signed URL による音声配信分離

Phase 1 では base64 エンコードされた WAV (1文あたり 50〜150KB) が SSE ストリームを通過していた。
1応答で 2〜4 文 → 合計 200〜600KB が SSE を経由し、接続時間を長引かせていた。

Phase 2 ではワーカーが WAV を Cloud Storage にアップロードし、
期限付き Signed URL だけを SSE で送る。ブラウザは Cloud Storage (CDN 経由) から直接音声をダウンロードする。

```
Phase 1: SSE で送るもの
  text_chunk: {"text": "はい、"}                                   ~50 バイト
  audio_chunk: {"audio_base64": "UklGR...(150KB)...", "sequence": 1}  ~150 KB

Phase 2: SSE で送るもの
  text_chunk: {"text": "はい、"}                                   ~50 バイト
  audio_chunk: {"audio_url": "https://storage.../a.wav", "sequence": 1}  ~200 バイト

→ SSE を通るデータ量が 1/1000 に削減
→ SSE 接続時間が短縮され、ゲートウェイの接続効率がさらに向上
```

## 各コンポーネントの設定

| コンポーネント | インフラ | 設定 | 役割 |
|--------------|---------|------|------|
| Next.js | Cloud Run | CPU: 1, Memory: 512Mi, min: 0, max: 10 | 静的配信 |
| SSE ゲートウェイ | Cloud Run | CPU: 1, Memory: 256Mi, min: 1, max: 10 | SSE 接続保持 + Pub/Sub → SSE 転送 |
| FastAPI ワーカー | Cloud Run | CPU: 2, Memory: 1Gi, min: 0, max: 50 | LLM/TTS 処理。接続を保持しないため min=0 可能 |
| VOICEVOX | **GCE MIG** | e2-standard-2, min: 1, max: 5 | 音声合成。内部 LB 経由でアクセス |
| Cloud SQL | マネージド | db-g1-small〜 | Phase 1 と同じ |
| Cloud Pub/Sub | マネージド | — | メッセージ中継。設定不要 |
| Cloud Storage | マネージド | Standard | 音声ファイル保存。TTL でライフサイクル管理 |

### 3. VOICEVOX の水平スケール（GCE MIG）

Phase 1 では VOICEVOX は単一の GCE インスタンスだったため、同時リクエスト数に上限があった。

Phase 2 ではマネージドインスタンスグループ（MIG）を使い、CPU 使用率に応じてインスタンスを自動増減する。
ワーカーからは内部ロードバランサの単一 IP でアクセスするため、アプリケーションコードの変更は不要。

```
Phase 1:
  [GCE 1台] = VOICEVOX
  → 同時 10〜20 リクエストで飽和

Phase 2:
  [内部 LB] → [GCE MIG: 1〜5台]
  → CPU 使用率 70% 超でスケールアウト
  → 負荷が下がれば自動スケールイン
```

## 追加遅延の影響

| 経路 | Phase 1 | Phase 2 | 差分 |
|------|---------|---------|------|
| テキスト配信 | 直接 SSE (0ms) | Pub/Sub 経由 (+20〜50ms) | 体感差なし（LLM 生成自体が秒単位） |
| 音声配信 | SSE 内 base64 (0ms) | Storage アップロード + CDN DL (+50〜100ms) | 体感差なし（TTS 生成自体が数百ms） |

LLM の生成や TTS の合成自体が秒〜数百ms 単位なので、中継の数十ms はユーザー体験に影響しない。
