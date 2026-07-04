"""評価用プロンプトの事前生成（S13b）。

評価 gold（held-out 3ドメイン・人間検証済み）の会話から、
zero-shot / few-shot 両条件の入力プロンプトを作り JSONL に書き出す。
Modal 側はこれを読むだけ（backend 依存を持ち込まない）。

実行:
  docker compose run --rm -v "$(pwd)/experiments:/experiments" -e PYTHONPATH=/app \
    backend python /experiments/finetuning/make_eval_prompts.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from generate_sft_data import build_extraction_messages, select_fewshot

GOLD_PATH = Path("/experiments/gold-editor/gold/gold.jsonl")
FEWSHOT_PATH = Path("/experiments/finetuning/data/fewshot_examples.jsonl")
OUT_PATH = Path("/experiments/finetuning/data/eval_prompts.jsonl")

HELDOUT = {"志望動機", "失敗経験", "アルバイトで工夫したこと"}
TRANSFER = {"志望動機": "far", "失敗経験": "near", "アルバイトで工夫したこと": "near"}


def conv_text(turns: list[dict]) -> str:
    lab = {"interviewer": "面接官", "applicant": "応募者"}
    return "\n".join(f"{lab.get(t.get('speaker'), t.get('speaker'))}: {t.get('text')}" for t in turns)


def main() -> None:
    fewshot = [json.loads(l) for l in FEWSHOT_PATH.open(encoding="utf-8") if l.strip()]
    n = 0
    with OUT_PATH.open("w", encoding="utf-8") as fout:
        for line in GOLD_PATH.open(encoding="utf-8"):
            r = json.loads(line)
            if r.get("topic") not in HELDOUT:
                continue
            n += 1
            text = conv_text(r["turns"])
            sys_zero, user = build_extraction_messages(r["topic"], text, examples=None)
            # few-shot は生成時と同じ選択（held-out に同族は無いので学習族から3例）
            sys_few, _ = build_extraction_messages(r["topic"], text, select_fewshot(fewshot, r["topic"]))
            fout.write(json.dumps({
                "id": f"evgold-{n:02d}",
                "topic": r["topic"],
                "transfer": TRANSFER[r["topic"]],
                "gold_graph": r["graph"],
                "messages_zero": [{"role": "system", "content": sys_zero}, {"role": "user", "content": user}],
                "messages_few": [{"role": "system", "content": sys_few}, {"role": "user", "content": user}],
            }, ensure_ascii=False) + "\n")
    print(f"{n} 件の評価プロンプトを {OUT_PATH} に書き出し")


if __name__ == "__main__":
    main()
