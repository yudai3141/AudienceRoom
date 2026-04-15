# Backend Architecture Diagrams

このディレクトリには、主要エンドポイントのアーキテクチャ図が含まれています。

## ディレクトリ構成

```
docs/
├── conversation/     # POST /conversation/message
├── practice_session/ # POST /practice-sessions
├── auth/             # POST /auth/login
└── feedback/         # POST /practice-sessions/{id}/generate-feedback
```

## 各エンドポイントの図

| ファイル | 内容 |
|---------|------|
| `flowchart.mermaid` | ファイル・クラス間の依存関係 |
| `class_diagram.mermaid` | 主要クラスの関係 |
| `sequence_diagram.mermaid` | リクエストからレスポンスまでの処理順序 |
| `er_diagram.mermaid` | 関連するDBテーブル構造 |

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
