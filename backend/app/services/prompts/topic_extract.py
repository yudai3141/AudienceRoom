from app.services.ai.llm.base import LLMMessage


def build_topic_extract_prompt(
    topic_title: str,
    graph_context: str,
    question: str | None,
    answer: str,
) -> list[LLMMessage]:
    """仮想 GraphRAG: ユーザーの回答からグラフ差分を抽出するプロンプト。

    Args:
        topic_title: トピック名
        graph_context: 現在のトピックグラフのテキスト表現 (既存ノードの label を含む)
        question: 直前の質問 (なければ None)
        answer: ユーザーの回答

    Returns:
        抽出用の LLMMessage リスト。
        LLM 出力は {"nodes": [...], "edges": [...]}。
    """
    system_prompt = f"""あなたは面接の記録係です。トピック「{topic_title}」について、
ユーザーの回答から重要な情報を抽出し、トピックグラフの差分として返します。

# ルール
- 既存ノードを補強できるなら、同じ label を再利用して更新する（新規に作らない）。
- 新しい論点だけ新規ノードにする。
- 既存の内容と食い違う場合は、矛盾内容を別ノードにして、relation_type="contradicts" の
  エッジで既存ノードと結ぶ（上書きせず矛盾を残す）。
- coverage は covered(十分話せた)/weak(説明が弱い)/gap(まだ空いている) から選ぶ。

# 現在のトピックグラフ（既存 label を再利用すること）
{graph_context}

# 直前の質問
{question or "(なし)"}

# ユーザーの回答
{answer}

以下の JSON 形式で出力してください：
{{
  "nodes": [
    {{"label": "評価方法", "node_type": "method", "detail": "PTSDモデルを定量評価", "coverage": "weak"}}
  ],
  "edges": [
    {{"source": "手法", "target": "成果", "relation_type": "leads_to"}}
  ]
}}

注意:
- edges の source/target は nodes か既存グラフの label を指すこと
- 抽出すべき情報が無ければ nodes/edges を空配列にする
"""

    return [LLMMessage(role="system", content=system_prompt)]
