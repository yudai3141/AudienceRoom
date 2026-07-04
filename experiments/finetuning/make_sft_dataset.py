"""reviewed_train.jsonl（検証済み30件）→ SFT 学習用 chat データセット。

重要な設計:
- 学習入力は **few-shot なしの素の抽出プロンプト**（zero-shot 条件と同一の system）。
  LoRA は「few-shot の代わりに重みで流儀を覚える」条件なので、プロンプトに例を入れない。
- 出力（assistant）は検証済みグラフの JSON。

実行（リポジトリ root から）:
  docker compose run --rm -v "$(pwd)/experiments:/experiments" -e PYTHONPATH=/app \
    backend python /experiments/finetuning/make_sft_dataset.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from generate_sft_data import build_extraction_messages, _conversation_to_text

IN_PATH = Path("/experiments/finetuning/data/reviewed_train.jsonl")
OUT_PATH = Path("/experiments/finetuning/data/sft_train.jsonl")


def main() -> None:
    n = 0
    with OUT_PATH.open("w", encoding="utf-8") as fout:
        for line in IN_PATH.open(encoding="utf-8"):
            r = json.loads(line)
            conv_text = _conversation_to_text(r["conversation"])
            system, user = build_extraction_messages(r["topic"], conv_text, examples=None)
            target = {
                "nodes": r["graph"]["nodes"],
                "edges": r["graph"]["edges"],
                "current_summary": r["graph"].get("current_summary", ""),
            }
            fout.write(json.dumps({
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                    {"role": "assistant", "content": json.dumps(target, ensure_ascii=False)},
                ],
                "meta": {"id": r["id"], "topic": r["topic"], "quality": r.get("quality", "")},
            }, ensure_ascii=False) + "\n")
            n += 1
    print(f"{n} 件を {OUT_PATH} に書き出し")


if __name__ == "__main__":
    main()
