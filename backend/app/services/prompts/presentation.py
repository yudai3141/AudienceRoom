from app.services.ai.llm.base import LLMMessage


def build_presentation_prompt(
    theme: str | None,
    user_goal: str | None,
    user_concerns: str | None,
    strictness: str,
    character_name: str,
    conversation_history: list[dict],
    is_qa_phase: bool = False,
) -> list[LLMMessage]:
    """Build prompt for presentation mode conversation.

    Args:
        theme: Presentation theme/topic
        user_goal: What user wants to practice
        user_concerns: What user wants to overcome
        strictness: Character strictness (gentle, normal, hard)
        character_name: AI character name
        conversation_history: Previous messages [{role, content}]
        is_qa_phase: Whether currently in Q&A phase

    Returns:
        List of LLMMessage for conversation
    """
    strictness_instructions = {
        "gentle": """- 穏やかで協力的な態度
- 簡単な質問から始める
- 回答を肯定的に受け止める
- プレッシャーを与えない""",
        "normal": """- 適度に鋭い質問をする
- プレゼン内容を深掘りする
- 建設的な指摘を行う
- 実際の聴衆に近い反応""",
        "hard": """- 厳しい質問で内容を追及する
- 論理の穴を指摘する
- 高いレベルの説明を求める
- 実践的で挑戦的な質問""",
    }
    strictness_instruction = strictness_instructions.get(
        strictness, strictness_instructions["normal"]
    )

    context_parts = []
    if theme:
        context_parts.append(f"プレゼンテーマ: {theme}")
    if user_goal:
        context_parts.append(f"ユーザーの練習目標: {user_goal}")
    if user_concerns:
        context_parts.append(f"ユーザーが克服したいこと: {user_concerns}")

    context = "\n".join(context_parts) if context_parts else "一般的なプレゼン練習"

    if is_qa_phase:
        phase_instruction = """【現在のフェーズ】質疑応答
- プレゼン内容に関する質問をする
- 1回に1つの質問に絞る
- ユーザーの回答に応じてフォローアップする"""
    else:
        phase_instruction = """【現在のフェーズ】プレゼン中
- 聴衆として自然なリアクションをする
- 相槌や短い反応を返す（「なるほど」「興味深いですね」など）
- プレゼン終了時に質疑応答に移る旨を伝える"""

    system_prompt = f"""あなたは「{character_name}」という名前のプレゼンの聴衆です。

【設定】
{context}

【あなたの振る舞い】
{strictness_instruction}

{phase_instruction}

【重要なルール】
- 1回の発言は1-2文程度に収める（長くても50文字以内）
- 自然な会話の流れを意識する
- プレゼン中は相槌程度、質疑応答では具体的な質問
- 最初の発言では「それでは始めてください」と促す
- 相手の名前は知らない前提で話す（「〇〇さん」のような呼びかけはしない）
- 標準的な敬語で話すこと。キャラクター口調（「〜なのだ」「〜ですわ」等）は使わない

日本語で会話してください。"""

    messages = [LLMMessage(role="system", content=system_prompt)]

    for msg in conversation_history:
        role = "user" if msg["role"] == "user" else "assistant"
        messages.append(LLMMessage(role=role, content=msg["content"]))

    return messages
