# Cloud Architecture

AudienceRoom のクラウドデプロイ構成を2段階で整理する。

| 構成 | 対象フェーズ | 特徴 |
|------|------------|------|
| [Phase 1: 初期デプロイ構成](./phase1_initial.md) | MVP / 少人数利用 | シンプル。Cloud Run + Cloud SQL で完結 |
| [Phase 2: スケーリング構成](./phase2_scaling.md) | 多人数同時利用 | 接続保持・音声配信・計算処理を分離 |

## 前提

- クラウドプロバイダ: **GCP**（README / CLAUDE.md で Cloud Run + Cloud SQL を採用済み）
- 図のフォーマット: Mermaid（GitHub / VS Code でプレビュー可能）
