# Modal での LoRA 学習

**Modal** = Python 関数にデコレータを付けるとクラウド GPU で実行してくれるサービス。
学習（train_lora.py）も、後の配信も同じ仕組みで動かす。

## 初回セットアップ

**既に `~/.modal.toml` がある場合（`modal token set` 済み）→ 何もしなくてよい**（下の実行コマンドがマウントする）。

無い場合は https://modal.com でアカウント作成 → Settings → API Tokens → New Token →
このフォルダの `.env`（gitignore 済み）に:

```
MODAL_TOKEN_ID=ak-xxxxxxxx
MODAL_TOKEN_SECRET=as-xxxxxxxx
```

## スモークテストの実行（リポジトリ root から）

```bash
# ~/.modal.toml を使う場合
docker run --rm -v "$(pwd)/experiments:/experiments" \
  -v ~/.modal.toml:/root/.modal.toml:ro \
  -w /experiments/finetuning python:3.11-slim \
  bash -c "pip install -q modal && modal run modal/train_lora.py"

# .env を使う場合は -v ~/.modal.toml... の代わりに --env-file modal/.env
```

- ローカル Python は汚さない（使い捨てコンテナ内で modal CLI を実行）
- データ（30件・~150KB）は引数としてリモートに渡すのでアップロード設定は不要
- GPU は A10G 1枚。スモーク（30件×4epoch）は **10〜20分・$0.5 以下**の見込み
- 出力: LoRA アダプタが Modal Volume `audienceroom-lora` に保存される

## W&B（学習runの記録・任意）

1. https://wandb.ai でアカウント作成 → https://wandb.ai/authorize で API キー取得
2. `modal/.env` に追記: `WANDB_API_KEY=xxxx`
3. 実行コマンドに `--env-file modal/.env` を足す（`~/.modal.toml` マウントと併用可）:

```bash
docker run --rm -v "$(pwd)/experiments:/experiments" \
  -v ~/.modal.toml:/root/.modal.toml:ro --env-file modal/.env \
  -w /experiments/finetuning python:3.11-slim \
  bash -c "pip install -q modal && modal run modal/train_lora.py"
```

キー未設定なら自動で OFF（ログ無しで学習は普通に動く）。プロジェクト名は `audienceroom-lora`。
役割分担: **Langfuse=推論トレース / W&B=学習run**。

## 出力の見方

実行終了時に JSON が出る:

- `train_loss`: 学習損失（下がっていれば学習は回っている）
- `sample_parse_ok` / `sample_n_nodes`: 学習後モデルの生成1件が JSON としてパースでき、
  ノードを持つか（＝形式を覚えたかの最低ライン）
- `adapter_path`: 保存先

## 注意

- ライブラリはバージョン固定（trl は版で API が大きく変わるため）
- スモークの目的は**配線確認**（Modal・学習コード・保存・生成が通るか）。
  品質評価は本番データ（120件目標）+ 評価ハーネスで行う
