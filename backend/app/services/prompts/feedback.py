from app.services.ai.llm.base import LLMMessage


def build_feedback_prompt(
    mode: str,
    theme: str | None,
    user_goal: str | None,
    user_concerns: str | None,
    conversation_log: list[dict],
) -> list[LLMMessage]:
    """Build prompt for feedback generation.

    Args:
        mode: Session mode (interview, presentation, free_conversation)
        theme: Session theme
        user_goal: What user wants to practice
        user_concerns: What user wants to overcome
        conversation_log: List of messages [{role, content}]

    Returns:
        List of LLMMessage for feedback generation
    """
    mode_labels = {
        "interview": "面接練習",
        "presentation": "プレゼン練習",
        "free_conversation": "自由会話練習",
    }
    mode_label = mode_labels.get(mode, mode)

    system_prompt = f"""あなたは{mode_label}のフィードバックを提供する専門家です。
ユーザーの練習セッションを分析し、建設的で励みになるフィードバックを提供してください。

フィードバックは以下のJSON形式で出力してください：
{{
  "summary_title": "総評のタイトル（20文字以内）",
  "short_comment": "一言コメント（50文字以内）",
  "positive_points": ["良かった点1", "良かった点2", "良かった点3"],
  "improvement_points": ["改善点1", "改善点2"],
  "overall_score": 75,
  "closing_message": "最後の励ましメッセージ（100文字以内）",
  "metrics": [
    {{"key": "clarity", "value": 80, "label": "話の明確さ"}},
    {{"key": "confidence", "value": 70, "label": "自信"}},
    {{"key": "structure", "value": 75, "label": "論理構成"}},
    {{"key": "engagement", "value": 85, "label": "聞き手への配慮"}}
  ]
}}

注意事項：
- overall_score は 0-100 の整数
- positive_points は 3-5 個、具体的な良い点を挙げる
- improvement_points は 2-3 個、建設的な改善提案
- closing_message は前向きで励みになる内容
- metrics の value は 0-100 の整数"""

    context_parts = [f"【練習モード】{mode_label}"]

    if theme:
        context_parts.append(f"【テーマ】{theme}")
    if user_goal:
        context_parts.append(f"【練習目標】{user_goal}")
    if user_concerns:
        context_parts.append(f"【克服したいこと】{user_concerns}")

    context = "\n".join(context_parts)

    conversation_text = "\n".join(
        f"{'ユーザー' if msg['role'] == 'user' else 'AI'}: {msg['content']}"
        for msg in conversation_log
    )

    user_prompt = f"""{context}

【会話ログ】
{conversation_text}

上記の会話を分析し、フィードバックをJSON形式で出力してください。"""

    return [
        LLMMessage(role="system", content=system_prompt),
        LLMMessage(role="user", content=user_prompt),
    ]
