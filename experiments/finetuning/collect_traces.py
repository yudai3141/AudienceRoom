"""トピック抽出のトレース収集スクリプト（ステップ1後半）。

何をするか:
- AudienceRoom DB の「完了した topic 付きセッション」を読み
- 本番と同じ抽出プロンプト (build_topic_session_update_prompt) + Gemini を呼び
- その呼び出しを Langfuse に計装（入力プロンプト・出力JSON・モデル・コスト等を記録）
- 同時に (会話 -> 望ましいJSON) を JSONL データセットとして書き出す

→ Langfuse 画面でトレースが見られ、かつ fine-tune 用データの素が貯まる。

実行（リポジトリ root から。backend コンテナ内で動かす）:
  docker compose run --rm \
    -v "$(pwd)/experiments:/experiments" \
    -e LANGFUSE_HOST=http://host.docker.internal:3001 \
    -e LANGFUSE_PUBLIC_KEY=pk-lf-local-audienceroom \
    -e LANGFUSE_SECRET_KEY=sk-lf-local-audienceroom \
    backend sh -c "pip install -q 'langfuse>=3,<4' && python /experiments/finetuning/collect_traces.py --limit 5"

注意:
- 学習データの「正解」をどう作るかは次のステップで詰める。ここでは「会話 -> 現在のGemini
  が出すJSON」をそのまま記録する（まず仕組みを通すのが目的）。
- graph_context は空（ゼロから概念グラフを抽出するタスクとして扱う）。
"""
import argparse
import asyncio
import json
import os
from pathlib import Path

from langfuse import Langfuse

from app.db.session import SessionLocal, engine
from app.repositories.practice_session_repository import PracticeSessionRepository
from app.repositories.session_message_repository import SessionMessageRepository
from app.repositories.topic_repository import TopicRepository
from app.services.ai.llm import get_llm_provider
from app.services.prompts.topic_session_update import build_topic_session_update_prompt
from sqlalchemy import select
from app.db.models.practice_session import PracticeSession

engine.echo = False

OUTPUT_PATH = Path("/experiments/finetuning/data/topic_extraction.jsonl")


def _completed_topic_sessions(db, limit: int):
    stmt = (
        select(PracticeSession)
        .where(
            PracticeSession.status == "completed",
            PracticeSession.topic_id.isnot(None),
            PracticeSession.deleted_at.is_(None),
        )
        .order_by(PracticeSession.created_at.desc())
        .limit(limit)
    )
    return list(db.execute(stmt).scalars().all())


def _messages_to_dicts(messages):
    return [
        {"role": "assistant" if m.participant_id else "user", "content": m.content}
        for m in messages
    ]


async def main(limit: int) -> None:
    lf = Langfuse()  # 認証情報は LANGFUSE_* 環境変数から読む
    if not lf.auth_check():
        raise SystemExit("Langfuse 認証に失敗。LANGFUSE_* 環境変数を確認してください。")

    provider = get_llm_provider()
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    db = SessionLocal()
    msg_repo = SessionMessageRepository(db)
    topic_repo = TopicRepository(db)
    PracticeSessionRepository(db)  # （将来の拡張用に保持）

    sessions = _completed_topic_sessions(db, limit)
    print(f"対象セッション: {len(sessions)} 件")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with OUTPUT_PATH.open("w", encoding="utf-8") as fout:
        for s in sessions:
            topic = topic_repo.get_by_id(s.topic_id)
            if topic is None:
                continue
            messages = msg_repo.list_by_session_id(s.id)
            conversation = _messages_to_dicts(messages)
            if not conversation:
                continue

            prompt = build_topic_session_update_prompt(
                topic_title=topic.title,
                graph_context="[ノード]\n(なし)\n[関係]\n(なし)",
                conversation_log=conversation,
            )
            input_messages = [{"role": m.role, "content": m.content} for m in prompt]

            with lf.start_as_current_generation(
                name="topic-extraction",
                model=model_name,
                input=input_messages,
            ) as gen:
                try:
                    output = await provider.generate_json(prompt, temperature=0.3)
                except Exception as e:
                    gen.update(output={"error": str(e)})
                    print(f"  session {s.id}: 失敗 {e}")
                    continue
                gen.update(output=output)
                lf.update_current_trace(
                    name=f"extract-session-{s.id}",
                    tags=["topic-extraction", "collect"],
                    metadata={"session_id": s.id, "topic_id": s.topic_id},
                )

            fout.write(
                json.dumps(
                    {
                        "session_id": s.id,
                        "topic_id": s.topic_id,
                        "topic_title": topic.title,
                        "conversation": conversation,
                        "output": output,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
            written += 1
            print(f"  session {s.id}: OK")

    lf.flush()
    print(f"完了: {written} 件を {OUTPUT_PATH} に書き出し、Langfuse にトレース送信")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()
    asyncio.run(main(args.limit))
