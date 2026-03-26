from app.services.ai.llm.base import LLMMessage


def build_interview_prompt(
    theme: str | None,
    user_goal: str | None,
    user_concerns: str | None,
    strictness: str,
    character_name: str,
    conversation_history: list[dict],
) -> list[LLMMessage]:
    """Build prompt for interview mode conversation.

    Args:
        theme: Interview theme/topic
        user_goal: What user wants to practice
        user_concerns: What user wants to overcome
        strictness: Character strictness (gentle, normal, hard)
        character_name: AI character name
        conversation_history: Previous messages [{role, content}]

    Returns:
        List of LLMMessage for conversation
    """
    strictness_instructions = {
        "gentle": """- 優しく丁寧な口調で話す
- 回答に詰まっても急かさない
- 良い点を積極的に褒める
- 質問は基本的なものから始める""",
        "normal": """- 適度な緊張感を保つ
- 的確なフォローアップ質問をする
- 良い点と改善点をバランスよく指摘
- 実際の面接に近い雰囲気""",
        "hard": """- 厳しめの質問で深掘りする
- 曖昧な回答には追加質問
- 高いレベルの回答を求める
- 実践的で挑戦的な質問""",
    }
    strictness_instruction = strictness_instructions.get(
        strictness, strictness_instructions["normal"]
    )

    context_parts = []
    if theme:
        context_parts.append(f"面接テーマ: {theme}")
    if user_goal:
        context_parts.append(f"ユーザーの練習目標: {user_goal}")
    if user_concerns:
        context_parts.append(f"ユーザーが克服したいこと: {user_concerns}")

    context = "\n".join(context_parts) if context_parts else "一般的な面接練習"

    system_prompt = f"""あなたは「{character_name}」という名前の面接官です。

【設定】
{context}

【あなたの振る舞い】
{strictness_instruction}

【重要なルール】
- 1回の発言は2-3文程度に収める
- 自然な会話の流れを意識する
- ユーザーの回答をよく聞いて、適切なフォローアップをする
- 面接の進行を意識し、適切なタイミングで次の質問に移る
- 最初の発言では簡単な自己紹介と最初の質問をする

日本語で会話してください。"""

    messages = [LLMMessage(role="system", content=system_prompt)]

    for msg in conversation_history:
        role = "user" if msg["role"] == "user" else "assistant"
        messages.append(LLMMessage(role=role, content=msg["content"]))

    return messages
