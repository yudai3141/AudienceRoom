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

# ルール（ナレッジグラフを作る）
- 回答を**重要な概念・エンティティ・専門用語の粒度に分解**してノードにする。
  良い例: 「認知科学とLLMの組み合わせ」「エクスポージャー療法」「トラウマ再喚起リスク」
  悪い例（使わない）: 「課題」「効果」「手法」のような抽象カテゴリ名を label にしない。カテゴリは node_type に入れる。
- 1つの発話に複数の概念があれば複数ノードに分け、概念どうしを意味のある関係
  （addresses/uses/causes/leads_to/supports/contradicts 等）で繋ぐ。
- 既存ノードを補強できるなら、同じ label を再利用して更新する（新規に作らない）。
- 新しい論点だけ新規ノードにする。
- 既存の内容と食い違う場合は、矛盾内容を別ノードにして、relation_type="contradicts" の
  エッジで既存ノードと結ぶ（上書きせず矛盾を残す）。
- coverage は covered(十分話せた)/weak(説明が弱い)/gap(まだ空いている) から選ぶ。

# 現在のトピックグラフ（既存 label を再利用すること）
{graph_context}

以下の JSON 形式で出力してください：
{{
  "nodes": [
    {{"label": "グラフDBによる連想記憶", "node_type": "method", "detail": "エンティティ間の連想を表現", "coverage": "covered"}},
    {{"label": "エピソード記憶", "node_type": "concept", "detail": "出来事単位の記憶", "coverage": "weak"}}
  ],
  "edges": [
    {{"source": "グラフDBによる連想記憶", "target": "エピソード記憶", "relation_type": "supports"}}
  ]
}}

注意:
- label は具体的なエンティティにする（抽象カテゴリ名にしない）
- edges の source/target は nodes か既存グラフの label を指すこと
- 抽出すべき情報が無ければ nodes/edges を空配列にする
"""

    user_prompt = f"""直前の質問: {question or "(なし)"}

ユーザーの回答:
{answer}

この回答からトピックグラフの差分を抽出し、JSON で返してください。"""

    return [
        LLMMessage(role="system", content=system_prompt),
        LLMMessage(role="user", content=user_prompt),
    ]
