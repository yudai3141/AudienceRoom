"""Claude 検証の前処理: 較正済みの定型修正を自動適用し、人手が要る点をフラグする。

自動修正（これまでの人間較正で確立したルールの機械適用）:
  A1. ハブ以外からの addresses → 向きを反転して leads_to（problem leads_to method の動機づけ向き）
  A2. 同一ペアの複数エッジ → ハブ発を優先して1本に（ハブ非関与なら先勝ち）
  A3. node_type に coverage 値が紛れたもの → concept に退避（+フラグ）

フラグ（人手判断が必要）:
  F1. ハブ未到達ノード
  F2. contradicts 使用（発言矛盾か）
  F3. 全ノード covered（応募者タイプと不整合の可能性）
  F4. 数字の忠実性: label/detail 中の数値が会話に存在しない（捏造の疑い）

使い方:
  python3 review_assist.py data/pending_b4.jsonl -o data/prereviewed_b4.jsonl
"""
import argparse
import json
import re
from collections import defaultdict

COVERAGES = {"covered", "weak", "gap"}
NUM_RE = re.compile(r"\d+(?:\.\d+)?")


def autofix(rec: dict) -> tuple[dict, list[str], list[str]]:
    g = json.loads(json.dumps(rec["draft_graph"], ensure_ascii=False))
    fixes, flags = [], []
    nodes = g.get("nodes", [])
    edges = g.get("edges", [])
    if not nodes:
        return g, fixes, ["FATAL: ノードなし"]
    hub = nodes[0].get("label")
    labelset = {n.get("label") for n in nodes}

    # A3: node_type に coverage 値
    for n in nodes:
        if n.get("node_type") in COVERAGES:
            fixes.append(f"A3 型スワップ退避: {n.get('label')} node_type={n.get('node_type')} -> concept")
            if n.get("coverage") not in COVERAGES:
                n["coverage"] = n.get("node_type")
            n["node_type"] = "concept"
            flags.append(f"F: 型を要確認（concept に仮置き）: {n.get('label')}")

    # A1: 非ハブ addresses の反転
    new_edges = []
    for e in edges:
        if e.get("relation_type") == "addresses" and e.get("source") != hub:
            fixes.append(f"A1 向き反転: {e['source']} addresses {e['target']} -> {e['target']} leads_to {e['source']}")
            new_edges.append({"source": e["target"], "target": e["source"], "relation_type": "leads_to"})
        else:
            new_edges.append(e)
    edges = new_edges

    # A2: 同一ペア重複の解消
    by_pair = defaultdict(list)
    for e in edges:
        by_pair[frozenset((e.get("source"), e.get("target")))].append(e)
    kept = []
    for pair, lst in by_pair.items():
        if len(lst) == 1:
            kept.append(lst[0])
            continue
        hub_out = [e for e in lst if e.get("source") == hub]
        chosen = hub_out[0] if hub_out else lst[0]
        kept.append(chosen)
        dropped = [e for e in lst if e is not chosen]
        fixes.append(f"A2 重複ペア解消: 残={chosen['source']}--{chosen['relation_type']}-->{chosen['target']} / 削除={len(dropped)}本")
    # 順序を安定化（元の順を維持）
    g["edges"] = [e for e in edges if e in kept]

    # F4: 数字の忠実性
    conv = " ".join(t.get("text", "") for t in rec.get("conversation", []))
    conv_nums = set(NUM_RE.findall(conv))
    for n in nodes:
        for num in NUM_RE.findall((n.get("label") or "") + " " + (n.get("detail") or "")):
            if num not in conv_nums:
                flags.append(f"F4 数字が会話に無い（捏造疑い）: {n.get('label')} の '{num}'")

    return g, fixes, flags


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("-o", "--out", required=True)
    args = ap.parse_args()

    import graph_lint

    out_records = []
    need_manual = 0
    for line in open(args.path, encoding="utf-8"):
        if not line.strip():
            continue
        rec = json.loads(line)
        g, fixes, flags = autofix(rec)
        lint = graph_lint.lint_graph(g)
        # 全covered は quality が流暢タイプなら許容
        if "流暢" in rec.get("quality", ""):
            lint = [i for i in lint if "全ノード covered" not in i]
        rec["draft_graph"] = g
        rec["autofixes"] = fixes
        rec["flags"] = flags + lint
        if rec["flags"]:
            need_manual += 1
        out_records.append(rec)

    with open(args.out, "w", encoding="utf-8") as f:
        for r in out_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"{len(out_records)} 件処理 / 自動修正のみで clean: {len(out_records) - need_manual} / 要手動: {need_manual}")
    for r in out_records:
        if r["flags"]:
            print(f"✗ {r['id']} ({r['topic']} / {r.get('quality','')[:8]})")
            for fl in r["flags"]:
                print(f"    - {fl}")


if __name__ == "__main__":
    main()
