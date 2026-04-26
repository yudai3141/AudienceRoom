# AudienceRoom デプロイガイド (GCP Cloud Run)

## 全体像

ローカルで動いている3つのコンテナ（Frontend / Backend / VOICEVOX）を、
そのまま Google Cloud Run に載せて、インターネットからアクセスできるようにする。

```
ローカル (Docker Compose)          ->    GCP (Cloud Run)
┌──────────────┐                      ┌──────────────────────┐
│ Frontend     │ localhost:3000   ->   │ Cloud Run (Frontend) │ https://frontend-xxx.run.app
│ Backend      │ localhost:8000   ->   │ Cloud Run (Backend)  │ https://backend-xxx.run.app
│ VOICEVOX     │ localhost:50021  ->   │ Cloud Run (VOICEVOX) │ https://voicevox-xxx.run.app
│ PostgreSQL   │ localhost:5432   ->   │ Cloud SQL            │ マネージド DB
│ Firebase Emu │ localhost:9099   ->   │ Firebase Auth        │ 本番 Firebase
└──────────────┘                      └──────────────────────┘
```

## 前提

- GCP アカウント + 請求先アカウント
- gcloud CLI (`brew install --cask google-cloud-sdk`)
- Docker Desktop

---

## Step 1: GCP プロジェクト作成 + API 有効化

**やること**: GCP 上に「箱」を作り、使うサービスのスイッチを入れる。

```bash
# ログイン
gcloud auth login

# プロジェクトを設定（UI で作成済みの前提）
gcloud config set project audienceroom

# 必要な API を有効化
gcloud services enable \
  run.googleapis.com \
  sqladmin.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com \
  compute.googleapis.com
```

## Step 2: Artifact Registry（Docker イメージ置き場）作成

**やること**: Docker Hub の代わりに、GCP 内にプライベートな Docker イメージ保管場所を作る。

```bash
# リポジトリ作成（東京リージョン）
gcloud artifacts repositories create audienceroom \
  --repository-format=docker \
  --location=asia-northeast1

# Docker CLI が Artifact Registry に push できるよう認証設定
gcloud auth configure-docker asia-northeast1-docker.pkg.dev --quiet
```

## Step 3: Cloud SQL（本番 DB）作成

**やること**: ローカルの PostgreSQL コンテナの代わりになるマネージド DB を作る。

UI での作成を推奨: https://console.cloud.google.com/sql/instances/create;engine=PostgreSQL

| 設定 | 値 | 理由 |
|-----|-----|------|
| エンジン | PostgreSQL 16 | ローカルと同じバージョンにして環境差異を防ぐ |
| エディション | Enterprise | Plus は高可用性向けで MVP には不要 |
| インスタンス ID | `audienceroom-db` | |
| リージョン | `asia-northeast1` | Cloud Run と同リージョンにして通信を速く |
| マシンタイプ | `db-f1-micro` | 1人利用なら十分 |

作成後、DB とユーザーを CLI で作成:

```bash
gcloud sql databases create audienceroom --instance=audienceroom-db
gcloud sql users create app --instance=audienceroom-db --password='<パスワード>'
# ※ パスワードに @ を含めると URL パースで壊れるので避ける
```

## Step 4: Docker イメージのビルド & プッシュ

**やること**: 本番用の Docker イメージを作って、Step 2 の置き場にアップロードする。

**重要**: Apple Silicon Mac では `--platform linux/amd64` が必要。Cloud Run は x86 で動くため。

```bash
REPO=asia-northeast1-docker.pkg.dev/audienceroom/audienceroom

# Backend
docker build --platform linux/amd64 \
  -f backend/Dockerfile.prod \
  -t $REPO/backend:latest \
  ./backend

# Frontend（ビルド時に環境変数を埋め込む）
docker build --platform linux/amd64 \
  -f frontend/Dockerfile.prod \
  --build-arg NEXT_PUBLIC_API_URL=https://backend-xxx.run.app \
  --build-arg NEXT_PUBLIC_FIREBASE_API_KEY=xxx \
  --build-arg NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=xxx.firebaseapp.com \
  --build-arg NEXT_PUBLIC_FIREBASE_PROJECT_ID=audienceroom \
  --build-arg NEXT_PUBLIC_FIREBASE_APP_ID=xxx \
  -t $REPO/frontend:latest \
  ./frontend

# プッシュ
docker push $REPO/backend:latest
docker push $REPO/frontend:latest
```

## Step 5: Cloud Run デプロイ — VOICEVOX

**やること**: 音声合成エンジンを Cloud Run にデプロイ。公式イメージをそのまま使う。

```bash
gcloud run deploy voicevox \
  --image=voicevox/voicevox_engine:cpu-ubuntu20.04-latest \
  --region=asia-northeast1 \
  --cpu=2 --memory=2Gi \
  --min-instances=0 --max-instances=2 \
  --port=50021 \
  --allow-unauthenticated \
  --timeout=300
```

## Step 6: Cloud Run デプロイ — Backend

**やること**: FastAPI を Cloud Run にデプロイ。Cloud SQL への接続と環境変数を設定する。

```bash
gcloud run deploy backend \
  --image=$REPO/backend:latest \
  --region=asia-northeast1 \
  --cpu=2 --memory=1Gi \
  --min-instances=1 --max-instances=5 \
  --port=8000 \
  --allow-unauthenticated \
  --timeout=300 \
  --add-cloudsql-instances=audienceroom:asia-northeast1:audienceroom-db \
  --set-env-vars="\
APP_ENV=production,\
DATABASE_URL=postgresql+psycopg://app:<password>@/audienceroom?host=/cloudsql/audienceroom:asia-northeast1:audienceroom-db,\
FIREBASE_PROJECT_ID=audienceroom,\
VOICEVOX_HOST=voicevox-xxx.asia-northeast1.run.app,\
VOICEVOX_PORT=443,\
LLM_PROVIDER=gemini,\
GEMINI_API_KEY=<your-key>,\
GEMINI_MODEL=gemini-2.5-flash,\
CORS_ORIGIN=https://frontend-xxx.asia-northeast1.run.app"
```

**ポイント**:
- `--add-cloudsql-instances` で Cloud SQL Proxy が自動的にサイドカーとして入る
- DB 接続は Unix ソケット経由（`?host=/cloudsql/...`）。TCP ではない
- VOICEVOX はポート 443（HTTPS）で接続する（Cloud Run が TLS を終端するため）

## Step 7: Cloud Run デプロイ — Frontend

**やること**: Next.js を Cloud Run にデプロイ。

```bash
gcloud run deploy frontend \
  --image=$REPO/frontend:latest \
  --region=asia-northeast1 \
  --cpu=1 --memory=512Mi \
  --min-instances=0 --max-instances=5 \
  --port=3000 \
  --allow-unauthenticated \
  --timeout=60
```

**注意**: `NEXT_PUBLIC_*` 環境変数はビルド時に埋め込まれる（Next.js の仕様）。
Backend の URL が変わったら Frontend の再ビルドが必要。

## Step 8: DB マイグレーション

**やること**: 本番 DB にテーブルを作る。Cloud SQL Auth Proxy 経由でローカルから実行。

```bash
# Auth Proxy 用の認証
gcloud auth application-default login

# Cloud SQL Auth Proxy を起動（ローカルの 15432 ポートで Cloud SQL に接続）
brew install cloud-sql-proxy
cloud-sql-proxy audienceroom:asia-northeast1:audienceroom-db --port=15432 &

# Docker 経由でマイグレーション実行
docker compose run --rm --no-deps \
  -e POSTGRES_HOST=host.docker.internal \
  -e POSTGRES_PORT=15432 \
  -e POSTGRES_DB=audienceroom \
  -e POSTGRES_USER=app \
  -e 'POSTGRES_PASSWORD=<password>' \
  backend alembic upgrade head

# Proxy を停止
pkill -f cloud-sql-proxy
```

## Step 9: Firebase Authentication 設定

**やること**: ローカルの Firebase エミュレーターの代わりに、本番の Firebase Auth を設定する。

1. GCP プロジェクトに Firebase を追加:
   ```bash
   gcloud services enable firebase.googleapis.com
   ```
   REST API で Firebase を有効化:
   ```bash
   curl -X POST \
     "https://firebase.googleapis.com/v1beta1/projects/audienceroom:addFirebase" \
     -H "Authorization: Bearer $(gcloud auth print-access-token)" \
     -H "x-goog-user-project: audienceroom"
   ```

2. Firebase Console (https://console.firebase.google.com/project/audienceroom) で:
   - Authentication -> Sign-in method -> Google を有効化
   - 承認済みドメインに Cloud Run の Frontend URL を追加
   - ウェブアプリを追加して `firebaseConfig` の値を取得

3. 取得した値で Frontend を再ビルド & デプロイ（Step 4 + Step 7）

## Step 10: 動作確認

Frontend の URL にアクセスして、ログイン -> セッション作成 -> 会話ができれば完了。

---

## デプロイ更新（コード変更後）

```bash
REPO=asia-northeast1-docker.pkg.dev/audienceroom/audienceroom

# Backend を更新する場合
docker build --platform linux/amd64 -f backend/Dockerfile.prod -t $REPO/backend:latest ./backend
docker push $REPO/backend:latest
gcloud run deploy backend --image=$REPO/backend:latest --region=asia-northeast1

# Frontend を更新する場合
docker build --platform linux/amd64 -f frontend/Dockerfile.prod \
  --build-arg NEXT_PUBLIC_API_URL=https://backend-xxx.run.app \
  --build-arg NEXT_PUBLIC_FIREBASE_API_KEY=xxx \
  --build-arg NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=xxx.firebaseapp.com \
  --build-arg NEXT_PUBLIC_FIREBASE_PROJECT_ID=audienceroom \
  --build-arg NEXT_PUBLIC_FIREBASE_APP_ID=xxx \
  -t $REPO/frontend:latest ./frontend
docker push $REPO/frontend:latest
gcloud run deploy frontend --image=$REPO/frontend:latest --region=asia-northeast1
```

## ハマりポイントまとめ

| 問題 | 原因 | 対処 |
|------|------|------|
| Cloud Run がイメージを拒否 | ARM Mac でビルド -> x86 が必要 | `--platform linux/amd64` を付ける |
| DB 接続エラー | Cloud SQL は Unix ソケット接続 | `DATABASE_URL` に `?host=/cloudsql/...` を使う |
| CORS エラー (OPTIONS 400) | Backend の許可オリジンに Cloud Run URL がない | `CORS_ORIGIN` 環境変数で追加 |
| VOICEVOX 音声が出ない | `http://` ハードコード + Cloud Run は HTTPS | ポート 443 で HTTPS 接続に対応 |
| Firebase ログインエラー | 承認済みドメインに未登録 | Firebase Console で Frontend URL を追加 |
| DB パスワードの `@` がパース失敗 | URL の `@` がホスト区切りと解釈される | パスワードに `@` を含めない |
