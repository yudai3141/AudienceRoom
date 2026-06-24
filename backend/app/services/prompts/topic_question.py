from app.services.ai.llm.base import LLMMessage


def build_topic_question_prompt(
    topic_title: str,
    graph_context: str,
    candidates: list[dict],
    conversation_history: list[dict],
) -> list[LLMMessage]:
    """仮想 GraphRAG: 候補ノードから深掘り質問を生成するプロンプト。

    Args:
        topic_title: トピック名
        graph_context: 現在のトピックグラフ (ノード/関係) のテキスト表現
        candidates: 質問対象の候補ノード [{id, label, coverage, node_type}]
        conversation_history: 直近の会話 [{role, content}]

    Returns:
        質問生成用の LLMMessage リスト。
        LLM 出力は {"selected_node_id": int, "question": str, "rationale": str}。
    """
    candidate_lines = "\n".join(
        f"- id={c['id']} [{c.get('coverage')}] {c.get('label')}"
        + (f" ({c['node_type']})" if c.get("node_type") else "")
        for c in candidates
    )

    history_text = "\n".join(
        f"{'面接官' if m.get('role') == 'assistant' else 'ユーザー'}: {m.get('content')}"
        for m in conversation_history
    ) or "(まだ会話なし)"

    system_prompt = f"""あなたは面接官です。トピック「{topic_title}」について、ユーザーが面接で
話せる状態に育てるための深掘り質問を 1 つ作ります。

ランダムな一般質問ではなく、下の候補ノードの中から「まだ弱い/空いている/矛盾している」点を
1 つ選び、その点を突く質問をしてください。会話の流れも踏まえて自然に繋げてください。

# 現在のトピックグラフ
{graph_context}

# 質問対象の候補ノード
{candidate_lines}

# 直近の会話
{history_text}

以下の JSON 形式で出力してください：
{{
  "selected_node_id": 12,
  "question": "その手法によって、具体的にどのような成果が得られましたか？",
  "rationale": "手法は説明されたが成果との接続が弱いため"
}}

注意:
- selected_node_id は必ず候補ノードの id から選ぶ
- question は 1 文の自然な面接質問
- rationale は「なぜこの質問をするのか」を簡潔に
"""

    # LLM プロバイダ (Gemini 等) は user メッセージを最低 1 つ要求するため付与する。
    return [
        LLMMessage(role="system", content=system_prompt),
        LLMMessage(
            role="user",
            content="上記の候補ノードから 1 つ選び、深掘り質問を JSON で出力してください。",
        ),
    ]
