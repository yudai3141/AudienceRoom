# Langfuse（セルフホスト）

## これは何？

**Langfuse = LLM アプリの「ログ＆計測」ダッシュボード。**
LLM への入力（プロンプト）・出力・使用トークン・コスト・レイテンシを記録して可視化する。

今回の目的：AudienceRoom の**トピック抽出**（会話 → 概念グラフ JSON）の入出力を記録し、
- どんな入出力をしているか目で見る
- それを **fine-tune の教師データの素** として集める

## 構成（公式 compose をポートだけ調整）

| サービス | 役割 | ホストポート |
| --- | --- | --- |
| langfuse-web | ダッシュボード UI | **3001**（3000 は AudienceRoom frontend） |
| langfuse-worker | 取り込み処理 | 3030 |
| postgres | メタデータ | 5433（5432 は AudienceRoom db） |
| clickhouse | トレース分析用 DB | 8123 / 9000 |
| redis | キュー | 6379 |
| minio | イベント/メディアの保管(S3互換) | 9090 / 9091 |

`.env`（gitignore 済み）に秘密情報と「初回起動でプロジェクト＋APIキーを自動作成」する設定が入っている。

## 起動

```bash
cd experiments/langfuse
docker compose up -d           # 初回はマイグレーションで 1〜2 分かかる
```

- UI: http://localhost:3001 → `.env` の `LANGFUSE_INIT_USER_EMAIL` / `LANGFUSE_INIT_USER_PASSWORD` でログイン
- 計装に使う API キー（`.env` に定義済み）:
  - Public key: `LANGFUSE_INIT_PROJECT_PUBLIC_KEY`
  - Secret key: `LANGFUSE_INIT_PROJECT_SECRET_KEY`
  - Host: `http://localhost:3001`

## 停止 / 片付け

```bash
docker compose down            # 停止（データは残る）
docker compose down -v         # データも消す
```

> AudienceRoom 本体（`docker-compose.yml`）とは別スタック。compose プロジェクト名が `langfuse` で分離されている。
