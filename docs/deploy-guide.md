# AudienceRoom デプロイガイド (GCP)

## 全体像

ローカルで動いている3つのコンテナ（Frontend / Backend / VOICEVOX）を GCP にデプロイする。
**VOICEVOX のみ Cloud Run ではなく Compute Engine** に載せる（CPU バウンド + 起動コスト大のため）。

```
ローカル (Docker Compose)             ->    GCP
┌──────────────┐                            ┌────────────────────────────────────┐
│ Frontend     │ localhost:3000        ->   │ Cloud Run (Frontend)               │
│ Backend      │ localhost:8000        ->   │ Cloud Run (Backend) [VPC Connector]│
│ VOICEVOX     │ localhost:50021       ->   │ Compute Engine (VOICEVOX) [VPC]    │
│ PostgreSQL   │ localhost:5432        ->   │ Cloud SQL                          │
│ Firebase Emu │ localhost:9099        ->   │ Firebase Auth                      │
└──────────────┘                            └────────────────────────────────────┘

Backend -> VOICEVOX: VPC 内部通信 (10.0.0.2:50021)
Backend -> Cloud SQL: Cloud SQL Proxy (Unix ソケット)
Backend -> Gemini API: パブリック (Egress: private-ranges-only)
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
  compute.googleapis.com \
  vpcaccess.googleapis.com
```

## Step 2: VPC ネットワーク + ファイアウォール作成

**やること**: Backend (Cloud Run) と VOICEVOX (GCE) をつなぐプライベートネットワークを作る。

```bash
# VPC ネットワーク
gcloud compute networks create audienceroom-vpc \
  --subnet-mode=custom \
  --bgp-routing-mode=regional

# GCE 用サブネット (/24)
gcloud compute networks subnets create audienceroom-subnet \
  --network=audienceroom-vpc \
  --region=asia-northeast1 \
  --range=10.0.0.0/24

# VPC Connector 用サブネット (/28 必須)
gcloud compute networks subnets create audienceroom-connector-subnet \
  --network=audienceroom-vpc \
  --region=asia-northeast1 \
  --range=10.8.0.0/28

# VPC 内部通信を全プロトコルで許可
gcloud compute firewall-rules create audienceroom-allow-internal \
  --network=audienceroom-vpc \
  --allow=tcp,udp,icmp \
  --source-ranges=10.0.0.0/24,10.8.0.0/28

# IAP 経由の SSH を許可（GCE のメンテ用）
gcloud compute firewall-rules create audienceroom-allow-ssh-iap \
  --network=audienceroom-vpc \
  --allow=tcp:22 \
  --source-ranges=35.235.240.0/20
```

## Step 3: Artifact Registry（Docker イメージ置き場）作成

**やること**: GCP 内にプライベートな Docker イメージ保管場所を作る（AWS の ECR 相当）。

```bash
gcloud artifacts repositories create audienceroom \
  --repository-format=docker \
  --location=asia-northeast1

# Docker CLI を Artifact Registry に認証
gcloud auth configure-docker asia-northeast1-docker.pkg.dev --quiet
```

## Step 4: Cloud SQL（本番 DB）作成

**やること**: ローカルの PostgreSQL コンテナの代わりとなるマネージド DB を作る。

UI 推奨: https://console.cloud.google.com/sql/instances/create;engine=PostgreSQL

| 設定 | 値 | 理由 |
|-----|-----|------|
| エンジン | PostgreSQL 16 | ローカルと同じバージョン |
| エディション | Enterprise | Plus は HA 用で MVP には不要 |
| インスタンス ID | `audienceroom-db` | |
| リージョン | `asia-northeast1` | Cloud Run と同リージョン |
| マシンタイプ | `db-f1-micro` | 1人利用なら十分 |

```bash
gcloud sql databases create audienceroom --instance=audienceroom-db
gcloud sql users create app --instance=audienceroom-db --password='<パスワード>'
# ※ パスワードに @ を含めると URL パースで壊れるので避ける
```

## Step 5: Compute Engine で VOICEVOX を起動

**やること**: VOICEVOX を GCE 上で常時起動させる。VPC 内に配置し、Backend から内部 IP でアクセスできるようにする。

```bash
gcloud compute instances create-with-container voicevox-vm \
  --zone=asia-northeast1-a \
  --machine-type=e2-medium \
  --network=audienceroom-vpc \
  --subnet=audienceroom-subnet \
  --tags=voicevox \
  --container-image=voicevox/voicevox_engine:cpu-ubuntu20.04-latest \
  --container-restart-policy=always
```

**ポイント**:
- `create-with-container` で Container-Optimized OS が起動し、指定したコンテナを自動起動
- `--container-restart-policy=always` で再起動時も自動復旧
- 内部 IP は `gcloud compute instances describe voicevox-vm --zone=asia-northeast1-a --format='value(networkInterfaces[0].networkIP)'` で取得

**動作確認** (SSH 経由):
```bash
gcloud compute ssh voicevox-vm --zone=asia-northeast1-a --tunnel-through-iap \
  --command="curl -s http://localhost:50021/version"
# -> "latest" などが返れば OK
```

## Step 6: Serverless VPC Connector 作成

**やること**: Cloud Run の Backend が VPC 内（VOICEVOX）にアクセスできるようにする。

```bash
gcloud compute networks vpc-access connectors create audienceroom-connector \
  --region=asia-northeast1 \
  --subnet=audienceroom-connector-subnet \
  --min-instances=2 \
  --max-instances=3 \
  --machine-type=e2-micro
# 作成に数分かかる
```

## Step 7: Docker イメージのビルド & プッシュ

**やること**: Backend / Frontend の本番用イメージを Artifact Registry にアップロード。

**重要**: Apple Silicon Mac では `--platform linux/amd64` が必要。Cloud Run は x86 で動くため。

```bash
REPO=asia-northeast1-docker.pkg.dev/audienceroom/audienceroom

# Backend
docker build --platform linux/amd64 \
  -f backend/Dockerfile.prod \
  -t $REPO/backend:latest \
  ./backend

# Frontend（ビルド時に NEXT_PUBLIC_* を埋め込む）
docker build --platform linux/amd64 \
  -f frontend/Dockerfile.prod \
  --build-arg NEXT_PUBLIC_API_URL=https://backend-xxx.run.app \
  --build-arg NEXT_PUBLIC_FIREBASE_API_KEY=xxx \
  --build-arg NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=xxx.firebaseapp.com \
  --build-arg NEXT_PUBLIC_FIREBASE_PROJECT_ID=audienceroom \
  --build-arg NEXT_PUBLIC_FIREBASE_APP_ID=xxx \
  -t $REPO/frontend:latest \
  ./frontend

docker push $REPO/backend:latest
docker push $REPO/frontend:latest
```

## Step 8: Cloud Run デプロイ — Backend

**やること**: FastAPI を Cloud Run にデプロイ。Cloud SQL 接続、VPC Connector、環境変数を設定。

```bash
# VOICEVOX の内部 IP を取得
VOICEVOX_IP=$(gcloud compute instances describe voicevox-vm \
  --zone=asia-northeast1-a \
  --format='value(networkInterfaces[0].networkIP)')

gcloud run deploy backend \
  --image=$REPO/backend:latest \
  --region=asia-northeast1 \
  --cpu=2 --memory=1Gi \
  --min-instances=1 --max-instances=5 \
  --port=8000 \
  --allow-unauthenticated \
  --timeout=300 \
  --add-cloudsql-instances=audienceroom:asia-northeast1:audienceroom-db \
  --vpc-connector=audienceroom-connector \
  --vpc-egress=private-ranges-only \
  --set-env-vars="\
APP_ENV=production,\
DATABASE_URL=postgresql+psycopg://app:<password>@/audienceroom?host=/cloudsql/audienceroom:asia-northeast1:audienceroom-db,\
FIREBASE_PROJECT_ID=audienceroom,\
VOICEVOX_HOST=$VOICEVOX_IP,\
VOICEVOX_PORT=50021,\
LLM_PROVIDER=gemini,\
GEMINI_API_KEY=<your-key>,\
GEMINI_MODEL=gemini-2.5-flash,\
CORS_ORIGIN=https://frontend-xxx.asia-northeast1.run.app"
```

**ポイント**:
- `--add-cloudsql-instances` で Cloud SQL Proxy がサイドカーとして自動起動
- DB 接続は Unix ソケット経由（`?host=/cloudsql/...`）。TCP ではない
- `--vpc-connector` + `--vpc-egress=private-ranges-only`: プライベート IP (10.x など) のみ VPC 経由、公開 API は通常経路
- VOICEVOX へは内部 IP で HTTP（HTTPS 不要）

## Step 9: Cloud Run デプロイ — Frontend

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

**注意**: `NEXT_PUBLIC_*` はビルド時に埋め込まれる。Backend の URL が変わったら再ビルドが必要。

## Step 10: DB マイグレーション

**やること**: 本番 DB にテーブルを作る。Cloud SQL Auth Proxy 経由でローカルから実行。

```bash
# Auth Proxy 用の認証
gcloud auth application-default login

# Cloud SQL Auth Proxy を起動 (15432 ポートで Cloud SQL に転送)
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

pkill -f cloud-sql-proxy
```

## Step 11: Firebase Authentication 設定

**やること**: ローカルの Firebase エミュレーターの代わりに本番 Firebase Auth を設定。

1. GCP プロジェクトに Firebase を追加:
   ```bash
   gcloud services enable firebase.googleapis.com

   curl -X POST \
     "https://firebase.googleapis.com/v1beta1/projects/audienceroom:addFirebase" \
     -H "Authorization: Bearer $(gcloud auth print-access-token)" \
     -H "x-goog-user-project: audienceroom"
   ```

2. Firebase Console (https://console.firebase.google.com/project/audienceroom) で:
   - Authentication -> Sign-in method -> Google を有効化
   - 承認済みドメインに Cloud Run の Frontend URL を追加
   - ウェブアプリを追加して `firebaseConfig` の値を取得

3. 取得した値で Frontend を再ビルド & デプロイ（Step 7 + Step 9）

## Step 12: 動作確認

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

# VOICEVOX を更新する場合 (GCE のコンテナを再起動)
gcloud compute ssh voicevox-vm --zone=asia-northeast1-a --tunnel-through-iap \
  --command="docker pull voicevox/voicevox_engine:cpu-ubuntu20.04-latest && \
             sudo systemctl restart konlet-startup"
```

## ハマりポイントまとめ

| 問題 | 原因 | 対処 |
|------|------|------|
| Cloud Run がイメージを拒否 | ARM Mac でビルド -> x86 が必要 | `--platform linux/amd64` を付ける |
| DB 接続エラー | Cloud SQL は Unix ソケット接続 | `DATABASE_URL` に `?host=/cloudsql/...` を使う |
| CORS エラー (OPTIONS 400) | Backend の許可オリジンに Cloud Run URL がない | `CORS_ORIGIN` 環境変数で追加 |
| VOICEVOX に接続できない | VPC Connector 未設定 / 内部 IP 間違い | `--vpc-connector` 必須 + `gcloud compute instances describe` で IP 確認 |
| Firebase ログインエラー | 承認済みドメインに未登録 | Firebase Console で Frontend URL を追加 |
| DB パスワードの `@` がパース失敗 | URL の `@` がホスト区切りと解釈される | パスワードに `@` を含めない |

## なぜ VOICEVOX だけ Compute Engine か

Cloud Run は「リクエストが来たらコンテナを起動し、終わったら落とす」リクエスト駆動型のサービス。VOICEVOX のような **CPU バウンドで起動コストが大きい** ワークロードには以下の問題がある:

| 問題 | Cloud Run | Compute Engine |
|------|-----------|---------------|
| コールドスタート | 10〜30 秒 | 起こらない（常時起動） |
| CPU 性能 | 共有 vCPU で音声合成が遅い | 専有 vCPU |
| min=1 のコスト | 割高 | GCE の方が安い |

**ワークロードの特性に応じて Cloud Run（リクエスト駆動）と GCE（常時起動）を使い分ける** のがクラウド設計のポイント。
