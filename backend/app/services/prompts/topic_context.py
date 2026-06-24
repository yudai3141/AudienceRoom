from app.db.models.topic_edge import TopicEdge
from app.db.models.topic_node import TopicNode


def build_topic_memory_context(
    nodes: list[TopicNode], edges: list[TopicEdge]
) -> str | None:
    """トピックグラフをプロンプト注入用のテキストにする (純粋関数)。

    ノードが無ければ None を返す（注入をスキップさせる）。仮想 GraphRAG の
    「retrieve したグラフをプロンプトに足す」部分。

    Args:
        nodes: トピックの全ノード
        edges: トピックの全エッジ

    Returns:
        記憶コンテキストのテキスト、またはノードが無い場合は None。
    """
    if not nodes:
        return None

    id_to_label = {n.id: n.label for n in nodes}
    lines = [
        "【このトピックで過去に話した内容（あなたの記憶）】",
        "あなたはこのトピックを覚えています。下の情報を踏まえ、まだ弱い(weak)・",
        "未説明(gap)・矛盾(contradicts)している点を中心に、自然に深掘りしてください。",
        "",
        "■ 論点 (covered=話せる / weak=説明が弱い / gap=まだ未説明)",
    ]
    for n in nodes:
        detail = f" — {n.detail}" if n.detail else ""
        lines.append(f"- [{n.coverage}] {n.label}{detail}")

    if edges:
        lines.append("")
        lines.append("■ 関係 (contradicts=食い違い)")
        for e in edges:
            src = id_to_label.get(e.source_node_id, "?")
            tgt = id_to_label.get(e.target_node_id, "?")
            lines.append(f"- {src} --{e.relation_type}--> {tgt}")

    return "\n".join(lines)
