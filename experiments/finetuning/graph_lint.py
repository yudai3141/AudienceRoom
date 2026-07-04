"""概念グラフの機械リンター（オントロジー v0.1 の機械化可能なルールを検査）。

使い方:
  python3 graph_lint.py data/reviewed_train.jsonl            # graph キーを検査
  python3 graph_lint.py data/pending_train.jsonl --key draft_graph

LLM では守られにくいルールを決定論的に検出する。人間/Claude のレビューは
ここで捕まらないもの（エッジの忠実性・粒度の質・coverage の妥当性）に集中する。
"""
import argparse
import json
import sys
from collections import defaultdict, deque

NODE_TYPES = {"concept", "method", "problem", "goal", "result", "context", "component"}
RELATION_TYPES = {"uses", "addresses", "causes", "leads_to", "part_of", "contradicts"}
COVERAGES = {"covered", "weak", "gap"}

# label 単体で使われたら抽象カテゴリ語とみなすブロックリスト
ABSTRACT_LABELS = {
    "課題", "問題", "効果", "成果", "手法", "方法", "改善点", "工夫", "強み", "弱み",
    "学び", "学んだこと", "目標", "背景", "状況", "チーム", "役割", "私の役割",
    "経験", "スキル", "技術", "プロセス", "解決策", "特徴", "貢献",
}

NODE_RANGE = (6, 20)


def lint_graph(g: dict) -> list[str]:
    issues = []
    nodes = g.get("nodes", [])
    edges = g.get("edges", [])
    labels = [n.get("label", "") for n in nodes]
    labelset = set(labels)

    # --- ノード ---
    if not nodes:
        return ["FATAL: ノードなし"]
    if len(labels) != len(labelset):
        dup = {l for l in labels if labels.count(l) > 1}
        issues.append(f"label 重複: {dup}")
    for n in nodes:
        if n.get("node_type") not in NODE_TYPES:
            issues.append(f"語彙外 node_type: {n.get('label')} -> {n.get('node_type')}")
        if n.get("coverage") not in COVERAGES:
            issues.append(f"語彙外 coverage: {n.get('label')} -> {n.get('coverage')}")
        if n.get("label", "").strip() in ABSTRACT_LABELS:
            issues.append(f"抽象カテゴリ label: 「{n.get('label')}」")
    if not (NODE_RANGE[0] <= len(nodes) <= NODE_RANGE[1]):
        issues.append(f"ノード数 {len(nodes)} が目安 {NODE_RANGE} の外")

    # --- エッジ ---
    seen_pairs = defaultdict(list)
    for e in edges:
        s, t, r = e.get("source"), e.get("target"), e.get("relation_type")
        if r not in RELATION_TYPES:
            issues.append(f"語彙外 relation: {s} --{r}--> {t}")
        if s not in labelset or t not in labelset:
            issues.append(f"宙ぶらりんエッジ: {s} --{r}--> {t}")
            continue
        if s == t:
            issues.append(f"自己ループ: {s}")
        seen_pairs[frozenset((s, t))].append((s, t, r))
    for pair, lst in seen_pairs.items():
        if len(lst) > 1:
            issues.append(f"同一ペアに複数エッジ（両方向含む）: {lst}")

    # --- ハブ到達性（先頭ノードをハブとみなす。part_of は無向扱い） ---
    hub = labels[0]
    adj = defaultdict(list)
    for e in edges:
        if e.get("source") in labelset and e.get("target") in labelset:
            adj[e["source"]].append(e["target"])
            if e.get("relation_type") == "part_of":
                adj[e["target"]].append(e["source"])
    seen = {hub}
    q = deque([hub])
    while q:
        for t in adj[q.popleft()]:
            if t not in seen:
                seen.add(t)
                q.append(t)
    unreached = [l for l in labels if l not in seen]
    if unreached:
        issues.append(f"ハブ未到達: {unreached}")

    # --- addresses はハブ発のみ / contradicts は要確認フラグ ---
    for e in edges:
        if e.get("relation_type") == "addresses" and e.get("source") != hub:
            issues.append(f"addresses がハブ以外から: {e.get('source')} --addresses--> {e.get('target')}")
        if e.get("relation_type") == "contradicts":
            issues.append(f"[要確認] contradicts 使用（発言矛盾か確認）: {e.get('source')} <-> {e.get('target')}")

    # --- coverage 分布 ---
    cov = defaultdict(int)
    for n in nodes:
        cov[n.get("coverage")] += 1
    if cov.get("weak", 0) + cov.get("gap", 0) == 0:
        issues.append("[要確認] 全ノード covered（詰まりのない面接は稀）")

    return issues


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("--key", default="graph", help="graph / draft_graph")
    args = parser.parse_args()

    total, clean = 0, 0
    for line in open(args.path, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        g = rec.get(args.key)
        if g is None:
            continue
        total += 1
        issues = lint_graph(g)
        rid = rec.get("id") or rec.get("topic") or f"#{total}"
        if issues:
            print(f"✗ {rid}")
            for i in issues:
                print(f"    - {i}")
        else:
            clean += 1
            print(f"✓ {rid}")
    print(f"\n{clean}/{total} clean")
    sys.exit(0 if clean == total else 1)


if __name__ == "__main__":
    main()
