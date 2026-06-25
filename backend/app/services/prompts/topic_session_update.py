from app.services.ai.llm.base import LLMMessage


def build_topic_session_update_prompt(
    topic_title: str,
    graph_context: str,
    conversation_log: list[dict],
) -> list[LLMMessage]:
    """練習後に、会話全体からトピックグラフの差分と要約を抽出するプロンプト。

    会話中の毎ターン更新はせず、終了後にまとめて 1 回だけ呼ぶ（仮想 GraphRAG の write 部分）。

    Args:
        topic_title: トピック名
        graph_context: 現在のトピックグラフのテキスト表現（既存 label を含む）
        conversation_log: 会話全体 [{role, content}]（role: user / assistant）

    Returns:
        LLMMessage リスト。出力は
        {"nodes": [...], "edges": [...], "current_summary": str}。
    """
    system_prompt = f"""あなたは面接の記録係です。トピック「{topic_title}」について、
今回の面接会話全体を読み、トピックグラフの差分と全体要約を抽出します。

# ルール（ナレッジグラフを作る）
- ユーザーが話した内容を**重要な概念・エンティティ・専門用語の粒度に分解**してノードにする。
  良い例: 「認知科学とLLMの組み合わせ」「エクスポージャー療法」「トラウマ再喚起リスク」「対話型エージェント」「グラフDBによる連想記憶」
  悪い例（使わない）: 「課題」「効果」「解決策」「手法」「特徴」のような抽象カテゴリ名を label にしない。
  カテゴリは node_type に入れる（例: node_type="method", label="グラフDBによる連想記憶"）。
- 1つの発話に複数の概念があれば複数ノードに分け、概念どうしを意味のある関係
  （addresses/uses/causes/leads_to/supports/contradicts 等）で繋ぐ。ノード数は多めでよい。
- 既存ノードを補強できるなら、同じ label を再利用して更新する（新規に作らない）。
- 新しい論点だけ新規ノードにする。
- 既存と食い違う発言があれば、矛盾内容を別ノードにし、relation_type="contradicts" の
  エッジで既存ノードと結ぶ（上書きせず矛盾を残す）。
- coverage は covered(十分話せた)/weak(説明が弱い)/gap(まだ未説明) から選ぶ。
  今回しっかり話せた論点は covered に上げる。
- current_summary は、このトピックが面接で話せる状態にどれだけ近づいたかを
  2〜3文で簡潔にまとめる。

# 現在のトピックグラフ（既存 label を再利用すること）
{graph_context}

以下の JSON 形式で出力してください：
{{
  "nodes": [
    {{"label": "認知科学とLLMの組み合わせ", "node_type": "approach", "detail": "対話エージェント構築の基盤", "coverage": "covered"}},
    {{"label": "エクスポージャー療法", "node_type": "domain", "detail": "PTSD治療の文脈", "coverage": "covered"}},
    {{"label": "トラウマ再喚起リスク", "node_type": "problem", "detail": "療法中の患者負荷", "coverage": "weak"}}
  ],
  "edges": [
    {{"source": "エクスポージャー療法", "target": "トラウマ再喚起リスク", "relation_type": "causes"}},
    {{"source": "認知科学とLLMの組み合わせ", "target": "トラウマ再喚起リスク", "relation_type": "addresses"}}
  ],
  "current_summary": "研究の全体像と設計意図は説明できるようになった。残る弱点は評価方法。"
}}

注意:
- label は具体的なエンティティにする（抽象カテゴリ名にしない）
- edges の source/target は nodes か既存グラフの label を指すこと
- 抽出すべき情報が無ければ nodes/edges を空配列にする
"""

    transcript = "\n".join(
        f"{'面接官' if m.get('role') == 'assistant' else 'ユーザー'}: {m.get('content')}"
        for m in conversation_log
    ) or "(会話なし)"

    user_prompt = f"""# 今回の面接会話
{transcript}

この会話からトピックグラフの差分と current_summary を JSON で返してください。"""

    return [
        LLMMessage(role="system", content=system_prompt),
        LLMMessage(role="user", content=user_prompt),
    ]
