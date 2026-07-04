# Modal での LoRA 学習

**Modal** = Python 関数にデコレータを付けるとクラウド GPU で実行してくれるサービス。
学習（train_lora.py）も、後の配信も同じ仕組みで動かす。

## 初回セットアップ（人間の作業・5分）

1. https://modal.com でアカウント作成（GitHub ログイン可。無料枠 $30/月）
2. ダッシュボード → **Settings → API Tokens → New Token** でトークンを作成
3. このフォルダに `.env` を作る（**gitignore 済み**・コミットしない）:

```
MODAL_TOKEN_ID=ak-xxxxxxxx
MODAL_TOKEN_SECRET=as-xxxxxxxx
```

## スモークテストの実行（リポジトリ root から）

```bash
docker run --rm -it -v "$(pwd)/experiments:/experiments" \
  -w /experiments/finetuning --env-file modal/.env python:3.11-slim \
  bash -c "pip install -q modal && modal run modal/train_lora.py"
```

- ローカル Python は汚さない（使い捨てコンテナ内で modal CLI を実行）
- データ（30件・~150KB）は引数としてリモートに渡すのでアップロード設定は不要
- GPU は A10G 1枚。スモーク（30件×4epoch）は **10〜20分・$0.5 以下**の見込み
- 出力: LoRA アダプタが Modal Volume `audienceroom-lora` に保存される

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
