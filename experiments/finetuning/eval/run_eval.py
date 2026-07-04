"""3条件の予測を gold と突き合わせて集計（S13b の答え合わせ）。

入力: data/eval_prompts.jsonl（gold_graph 入り）+ data/predictions.jsonl
出力: 条件×指標の表（全体 / near / far 転移別）+ data/results.json

実行: python3 eval/run_eval.py
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from metrics import graph_scores, granularity, normalize, type_consistency

BASE = Path(__file__).parent.parent / "data"


def main() -> None:
    prompts = {r["id"]: r for r in (json.loads(l) for l in (BASE / "eval_prompts.jsonl").open(encoding="utf-8"))}
    preds = [json.loads(l) for l in (BASE / "predictions.jsonl").open(encoding="utf-8")]

    by_cond = defaultdict(list)  # cond -> list of (item, graph or None)
    unrecoverable = defaultdict(int)
    for p in preds:
        item = prompts[p["id"]]
        g = normalize(p["output"])
        if g is None or not g.get("nodes"):
            unrecoverable[p["condition"]] += 1
            by_cond[p["condition"]].append((item, None))
        else:
            by_cond[p["condition"]].append((item, g))

    results = {}
    for cond, pairs in by_cond.items():
        buckets = {"all": pairs,
                   "near": [x for x in pairs if x[0]["transfer"] == "near"],
                   "far": [x for x in pairs if x[0]["transfer"] == "far"]}
        results[cond] = {}
        for bname, bpairs in buckets.items():
            ok = [(it, g) for it, g in bpairs if g is not None]
            scores = [graph_scores(g, it["gold_graph"]) for it, g in ok]
            def avg(path):
                vals = [s for s in scores]
                for k in path:
                    vals = [v[k] for v in vals]
                return round(sum(vals) / len(vals), 3) if vals else None
            gran = granularity([g for _, g in ok]) if ok else {}
            tc = type_consistency([g for _, g in ok]) if ok else {}
            results[cond][bname] = {
                "n": len(bpairs), "unrecoverable": len(bpairs) - len(ok),
                "node_f1": avg(["node", "f1"]),
                "typed_f1": avg(["typed_node", "f1"]),
                "edge_strict_f1": avg(["edge_strict", "f1"]),
                "edge_relaxed_f1": avg(["edge_relaxed", "f1"]),
                "coverage_agree_f1": avg(["coverage_agree", "f1"]),
                "node_count_mean": gran.get("node_count_mean"),
                "node_count_std": gran.get("node_count_std"),
                "abstract_rate": gran.get("abstract_label_rate"),
                "type_consistency": tc.get("agreement"),
            }

    (BASE / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    for bname in ("all", "near", "far"):
        print(f"\n===== {bname} =====")
        header = f"{'cond':<6} {'n':>3} {'修復不能':>5} {'nodeF1':>7} {'typedF1':>8} {'edgeS':>6} {'edgeR':>6} {'covAgr':>7} {'N平均':>6} {'Nstd':>5} {'抽象率':>6} {'型一貫':>6}"
        print(header)
        print("-" * len(header))
        for cond in ("zero", "few", "lora"):
            r = results.get(cond, {}).get(bname)
            if not r:
                continue
            print(f"{cond:<6} {r['n']:>3} {r['unrecoverable']:>5} {r['node_f1'] or '-':>7} {r['typed_f1'] or '-':>8} "
                  f"{r['edge_strict_f1'] or '-':>6} {r['edge_relaxed_f1'] or '-':>6} {r['coverage_agree_f1'] or '-':>7} "
                  f"{r['node_count_mean'] or '-':>6} {r['node_count_std'] or '-':>5} {r['abstract_rate'] if r['abstract_rate'] is not None else '-':>6} "
                  f"{r['type_consistency'] or '-':>6}")
    print("\n保存: data/results.json")


if __name__ == "__main__":
    main()
