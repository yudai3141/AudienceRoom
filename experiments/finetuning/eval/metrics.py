"""概念グラフ評価の指標（層2: 粒度・一貫性 / 層3: gold一致）。

依存ゼロ（標準ライブラリのみ）。ラベルの曖昧マッチは文字バイグラム Jaccard
（日本語の短い概念ラベルに有効）。将来、埋め込み類似に差し替える場合は
`similarity()` だけ入れ替えればよい。
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict

ABSTRACT_LABELS = {
    "課題", "問題", "効果", "成果", "手法", "方法", "改善点", "工夫", "強み", "弱み",
    "学び", "学んだこと", "目標", "背景", "状況", "チーム", "役割", "私の役割",
    "経験", "スキル", "技術", "プロセス", "解決策", "特徴", "貢献",
}

# ---------------------------------------------------------------- 正規化


def normalize(raw: str) -> dict | None:
    """モデル出力テキスト → graph dict。修復不能なら None（除外率として報告する）。"""
    s = raw.strip()
    s = re.sub(r"^```(?:json)?\s*|\s*```$", "", s, flags=re.M).strip()
    for candidate in (s,):
        try:
            return json.loads(candidate)
        except Exception:
            pass
    # 最後の { ... } ブロックを試す
    m = re.search(r"\{.*\}", s, flags=re.S)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            pass
    return None


# ---------------------------------------------------------------- 類似度


def _bigrams(s: str) -> set[str]:
    s = re.sub(r"\s+", "", s or "")
    return {s[i : i + 2] for i in range(len(s) - 1)} if len(s) > 1 else {s}


def similarity(a: str, b: str) -> float:
    """文字バイグラム Jaccard（0..1）。埋め込みに差し替え可能な唯一の関数。"""
    A, B = _bigrams(a), _bigrams(b)
    if not A or not B:
        return 0.0
    return len(A & B) / len(A | B)


def match_nodes(pred: list[dict], gold: list[dict], tau: float = 0.5) -> list[tuple[int, int, float]]:
    """貪欲マッチ（類似度降順、1対1）。(pred_idx, gold_idx, sim) を返す。"""
    cands = []
    for i, p in enumerate(pred):
        for j, g in enumerate(gold):
            s = similarity(p.get("label", ""), g.get("label", ""))
            if s >= tau:
                cands.append((s, i, j))
    cands.sort(reverse=True)
    used_p, used_g, out = set(), set(), []
    for s, i, j in cands:
        if i in used_p or j in used_g:
            continue
        used_p.add(i)
        used_g.add(j)
        out.append((i, j, s))
    return out


# ---------------------------------------------------------------- 層3: gold 一致


def prf(n_match: int, n_pred: int, n_gold: int) -> dict:
    p = n_match / n_pred if n_pred else 0.0
    r = n_match / n_gold if n_gold else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return {"precision": round(p, 3), "recall": round(r, 3), "f1": round(f, 3)}


def graph_scores(pred: dict, gold: dict, tau: float = 0.5) -> dict:
    pn, gn = pred.get("nodes", []), gold.get("nodes", [])
    matches = match_nodes(pn, gn, tau)
    node = prf(len(matches), len(pn), len(gn))
    typed = prf(
        sum(1 for i, j, _ in matches if pn[i].get("node_type") == gn[j].get("node_type")),
        len(pn), len(gn),
    )
    cov = prf(
        sum(1 for i, j, _ in matches if pn[i].get("coverage") == gn[j].get("coverage")),
        len(pn), len(gn),
    )

    # エッジ: マッチしたノード対応で写像し比較
    p2g = {pn[i]["label"]: gn[j]["label"] for i, j, _ in matches}
    gold_edges = {}
    for e in gold.get("edges", []):
        gold_edges[(e.get("source"), e.get("target"))] = e.get("relation_type")
    strict = relaxed = 0
    pe = pred.get("edges", [])
    for e in pe:
        s, t = p2g.get(e.get("source")), p2g.get(e.get("target"))
        if s is None or t is None:
            continue
        if (s, t) in gold_edges:
            relaxed += 1
            if gold_edges[(s, t)] == e.get("relation_type"):
                strict += 1
    n_gold_e = len(gold.get("edges", []))
    return {
        "node": node,
        "typed_node": typed,
        "coverage_agree": cov,
        "edge_strict": prf(strict, len(pe), n_gold_e),
        "edge_relaxed": prf(relaxed, len(pe), n_gold_e),
    }


# ---------------------------------------------------------------- 層2: 粒度・一貫性


def granularity(graphs: list[dict]) -> dict:
    counts = [len(g.get("nodes", [])) for g in graphs]
    n = len(counts) or 1
    mean = sum(counts) / n
    var = sum((c - mean) ** 2 for c in counts) / n
    abstract = total = dup_pairs = pair_total = isolated = 0
    lab_lens = []
    for g in graphs:
        nodes = g.get("nodes", [])
        labels = [x.get("label", "") for x in nodes]
        total += len(labels)
        abstract += sum(1 for l in labels if l.strip() in ABSTRACT_LABELS)
        lab_lens += [len(l) for l in labels]
        for i in range(len(labels)):
            for j in range(i + 1, len(labels)):
                pair_total += 1
                if similarity(labels[i], labels[j]) > 0.7:
                    dup_pairs += 1
        touched = set()
        for e in g.get("edges", []):
            touched.add(e.get("source"))
            touched.add(e.get("target"))
        isolated += sum(1 for l in labels if l not in touched)
    return {
        "n_graphs": len(graphs),
        "node_count_mean": round(mean, 2),
        "node_count_std": round(var ** 0.5, 2),
        "band_rate_6_20": round(sum(1 for c in counts if 6 <= c <= 20) / n, 3),
        "abstract_label_rate": round(abstract / total, 4) if total else 0.0,
        "label_len_mean": round(sum(lab_lens) / len(lab_lens), 1) if lab_lens else 0.0,
        "dup_node_rate": round(dup_pairs / pair_total, 4) if pair_total else 0.0,
        "isolated_node_rate": round(isolated / total, 4) if total else 0.0,
    }


def type_consistency(graphs: list[dict], tau: float = 0.7) -> dict:
    """出力横断で、類似ラベルのクラスタが同じ node_type を得ているか。"""
    items = []
    for g in graphs:
        for x in g.get("nodes", []):
            items.append((x.get("label", ""), x.get("node_type", "")))
    # 貪欲クラスタリング
    clusters: list[list[int]] = []
    for idx, (lab, _) in enumerate(items):
        placed = False
        for cl in clusters:
            if similarity(items[cl[0]][0], lab) >= tau:
                cl.append(idx)
                placed = True
                break
        if not placed:
            clusters.append([idx])
    multi = [cl for cl in clusters if len(cl) >= 2]
    if not multi:
        return {"clusters": 0, "agreement": None}
    agree = 0
    for cl in multi:
        types = Counter(items[i][1] for i in cl)
        agree += types.most_common(1)[0][1] / len(cl)
    return {"clusters": len(multi), "agreement": round(agree / len(multi), 3)}
