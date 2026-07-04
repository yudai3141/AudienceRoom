"""ものさしの検証: gold に高得点・壊した gold に低得点が出ることを確認する。

破壊操作（実験設計 4.4）:
  C1 型シャッフル      → typed_node F1 だけ落ちるはず（node F1 は不変）
  C2 抽象ラベル置換    → node F1 が落ち、抽象ラベル率が上がるはず
  C3 ノード過分割      → precision が落ち、ノード数が跳ねるはず
  C4 関係シャッフル    → edge_strict だけ落ちるはず（edge_relaxed は不変）

使い方:
  python3 eval/validate_metrics.py ../gold-editor/gold/gold.jsonl
"""
import copy
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from metrics import ABSTRACT_LABELS, granularity, graph_scores

random.seed(7)
ABS = sorted(ABSTRACT_LABELS)


def c1_type_shuffle(g):
    g = copy.deepcopy(g)
    types = [n["node_type"] for n in g["nodes"]]
    random.shuffle(types)
    # 全ノードを確実にずらす（同型に戻るのを避けるため回転を併用）
    types = types[1:] + types[:1]
    for n, t in zip(g["nodes"], types):
        n["node_type"] = t
    return g


def c2_abstract_labels(g, rate=0.4):
    g = copy.deepcopy(g)
    idx = list(range(len(g["nodes"])))
    random.shuffle(idx)
    mapping = {}
    for k, i in enumerate(idx[: max(1, int(len(idx) * rate))]):
        old = g["nodes"][i]["label"]
        new = ABS[k % len(ABS)]
        g["nodes"][i]["label"] = new
        mapping[old] = new
    for e in g["edges"]:
        e["source"] = mapping.get(e["source"], e["source"])
        e["target"] = mapping.get(e["target"], e["target"])
    return g


def c3_fragmentation(g):
    g = copy.deepcopy(g)
    new_nodes = []
    for n in g["nodes"]:
        new_nodes.append(n)
        lab = n["label"]
        if len(lab) >= 6:  # ラベルを半分に割った“断片ノード”を追加
            frag = dict(n)
            frag = {**n, "label": lab[: len(lab) // 2]}
            new_nodes.append(frag)
    g["nodes"] = new_nodes
    return g


def c4_relation_shuffle(g):
    g = copy.deepcopy(g)
    rels = [e["relation_type"] for e in g["edges"]]
    rels = rels[1:] + rels[:1]
    for e, r in zip(g["edges"], rels):
        e["relation_type"] = r
    return g


def avg(dicts, path):
    vals = []
    for d in dicts:
        v = d
        for k in path:
            v = v[k]
        vals.append(v)
    return round(sum(vals) / len(vals), 3) if vals else 0.0


def main(path: str) -> None:
    golds = [json.loads(l)["graph"] for l in open(path, encoding="utf-8") if l.strip()]
    print(f"gold {len(golds)} 件で検証\n")

    conds = {
        "self（gold vs gold）": lambda g: copy.deepcopy(g),
        "C1 型シャッフル": c1_type_shuffle,
        "C2 抽象ラベル置換(40%)": c2_abstract_labels,
        "C3 ノード過分割": c3_fragmentation,
        "C4 関係シャッフル": c4_relation_shuffle,
    }
    header = f"{'条件':<22} {'nodeF1':>7} {'typedF1':>8} {'edgeS':>7} {'edgeR':>7} {'抽象率':>7} {'ノード数':>8}"
    print(header)
    print("-" * len(header))
    for name, fn in conds.items():
        preds = [fn(g) for g in golds]
        scores = [graph_scores(p, g) for p, g in zip(preds, golds)]
        gran = granularity(preds)
        print(
            f"{name:<22} {avg(scores,['node','f1']):>7} {avg(scores,['typed_node','f1']):>8} "
            f"{avg(scores,['edge_strict','f1']):>7} {avg(scores,['edge_relaxed','f1']):>7} "
            f"{gran['abstract_label_rate']:>7} {gran['node_count_mean']:>8}"
        )


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "../gold-editor/gold/gold.jsonl")
