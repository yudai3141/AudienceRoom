"""coverage 審判: 全ノード covered が疑わしいレコードについて、会話を根拠に coverage を再判定させる。

- Claude 検証で較正した判定基準（オントロジーの coverage 規則）をプロンプト化して Gemini に代行させる
- 安全のため **降格のみ適用**（covered→weak/gap。昇格はしない）
- 変更は manual_notes に記録

実行（リポジトリ root から）:
  docker compose run --rm -v "$(pwd)/experiments:/experiments" -e PYTHONPATH=/app \
    backend python /experiments/finetuning/coverage_referee.py data/prereviewed_b5.jsonl
"""
import asyncio
import json
import sys
from pathlib import Path

from app.services.ai.llm import get_llm_provider
from app.services.ai.llm.base import LLMMessage

ORDER = {"covered": 2, "weak": 1, "gap": 0}


def build_prompt(conv_text: str, labels: list[str]) -> list[LLMMessage]:
    system = """あなたは面接記録の採点者です。概念グラフの各ノードについて、会話を根拠に
coverage（どれだけ話せたか）を判定します。

# 判定基準（厳しめに）
- covered: 数字・固有名詞・理由まで**具体的に**語れた
- weak: 言及したが曖昧・詰まった・一言だけ・「〜と思います/感じます」の主観のみ・体感ベースで数値なし・仮説や願望止まり
- gap: 名前しか出ていない／質問されたのに答えられなかった／「まだ模索中」「経験がない」等の欠落

出力は JSON のみ: {"coverages": {"ノードlabel": "covered|weak|gap", ...}}"""
    user = f"# 面接会話\n{conv_text}\n\n# 判定対象ノード\n" + "\n".join(f"- {l}" for l in labels) \
        + "\n\n各ノードの coverage を判定して JSON で返してください。"
    return [LLMMessage(role="system", content=system), LLMMessage(role="user", content=user)]


async def main(path: str) -> None:
    provider = get_llm_provider()
    p = Path(path)
    recs = [json.loads(l) for l in p.open(encoding="utf-8")]
    lab = {"interviewer": "面接官", "applicant": "応募者"}
    n_changed = 0
    for r in recs:
        g = r["draft_graph"]
        covs = [n.get("coverage") for n in g["nodes"]]
        # 対象: 全covered かつ 流暢タイプでない
        if "流暢" in r.get("quality", "") or any(c != "covered" for c in covs):
            continue
        conv_text = "\n".join(f"{lab.get(t['speaker'], t['speaker'])}: {t['text']}" for t in r["conversation"])
        labels = [n["label"] for n in g["nodes"]]
        try:
            out = await provider.generate_json(build_prompt(conv_text, labels), temperature=0.1)
        except Exception as e:
            print(f"  {r['id']}: referee失敗 {e}")
            continue
        verdicts = out.get("coverages", {})
        changes = []
        for n in g["nodes"]:
            v = verdicts.get(n["label"])
            if v in ORDER and ORDER[v] < ORDER[n["coverage"]]:  # 降格のみ
                changes.append(f"{n['label']}: {n['coverage']}→{v}")
                n["coverage"] = v
        if changes:
            n_changed += 1
            r.setdefault("manual_notes", []).append("[coverage審判] " + " / ".join(changes))
            print(f"  {r['id']}: {len(changes)}ノード降格")
        else:
            print(f"  {r['id']}: 変更なし（審判も全covered判定）")
    with p.open("w", encoding="utf-8") as f:
        for x in recs:
            f.write(json.dumps(x, ensure_ascii=False) + "\n")
    print(f"完了: {n_changed} 件に降格を適用")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "data/prereviewed_b5.jsonl"))
