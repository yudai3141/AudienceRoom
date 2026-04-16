# Backend Architecture Diagrams

このディレクトリには、主要エンドポイントのアーキテクチャ図が含まれています。

## ディレクトリ構成

```
docs/
├── conversation/     # 会話エンドポイント
│   ├── POST /conversation/message (同期版)
│   └── POST /conversation/message/stream (ストリーミング版)
├── practice_session/ # POST /practice-sessions
├── auth/             # POST /auth/login
└── feedback/         # POST /practice-sessions/{id}/generate-feedback
```

## 各エンドポイントの図

| ファイル | 内容 |
|---------|------|
| `flowchart.mermaid` | ファイル・クラス間の依存関係 |
| `streaming_flowchart.mermaid` | ストリーミング版の依存関係 _(conversation のみ)_ |
| `class_diagram.mermaid` | 主要クラスの関係 |
| `sequence_diagram.mermaid` | リクエストからレスポンスまでの処理順序 |
| `streaming_sequence_diagram.mermaid` | ストリーミング版の処理順序 _(conversation のみ)_ |
| `er_diagram.mermaid` | 関連するDBテーブル構造 |

## 会話エンドポイント (conversation)

### 同期版: POST /conversation/message
- **ConversationService** を使用
- LLM生成 → TTS生成 → 完成後にJSONレスポンス
- 応答時間: 3-8秒

### ストリーミング版: POST /conversation/message/stream
- **StreamingConversationService** を使用
- Server-Sent Events (SSE) でリアルタイム配信
- LLMストリーミング → 文の区切りごとにTTS並列生成 → SSEイベント送信
- 最初の応答: 0.3-0.5秒

**ストリーミング処理フロー:**
1. `metadata` イベント: participant_id, speaker_id
2. `text_chunk` イベント: LLMからのテキストチャンク
3. `audio_chunk` イベント: 文ごとの音声データ（シーケンス番号付き）
4. `complete` イベント: 生成完了

詳細は以下を参照:
- `conversation/streaming_flowchart.mermaid` - 依存関係図
- `conversation/streaming_sequence_diagram.mermaid` - 処理シーケンス図

## プレビュー方法

### VS Code
- Mermaid Preview 拡張機能をインストール
- `.mermaid` ファイルを開いてプレビュー

### GitHub
- PRやREADMEに埋め込む場合は以下の形式:

```markdown
```mermaid
flowchart TB
    A --> B
```　
```

### Mermaid Live Editor
- https://mermaid.live/ にコードを貼り付け
