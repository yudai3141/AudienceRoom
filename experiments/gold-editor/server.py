"""Gold エディタのサーバ（FastAPI）。

会話を選ぶ → Gemini で概念グラフを下書き → 画面上で視覚的に編集 → gold として保存。
既存の backend モジュール（DB / LLM provider）を再利用するため、backend コンテナ内で動かす。

起動（リポジトリ root から）:
  docker compose run --rm -p 8100:8100 \
    -v "$(pwd)/experiments:/experiments" -e PYTHONPATH=/app \
    backend python /experiments/gold-editor/server.py
  → ブラウザで http://localhost:8100
"""
import datetime
import json
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy import select

from app.db.models.practice_session import PracticeSession
from app.db.session import SessionLocal, engine
from app.repositories.session_message_repository import SessionMessageRepository
from app.repositories.topic_repository import TopicRepository
from app.services.ai.llm import get_llm_provider
from app.services.ai.llm.base import LLMMessage

engine.echo = False

# ── 固定タクソノミー（gold の芯） ──────────────────────────────
NODE_TYPES = ["concept", "method", "problem", "goal", "result", "context", "component"]
RELATION_TYPES = ["uses", "addresses", "causes", "leads_to", "part_of", "contradicts"]

TOPICS = [
    "研究内容", "自己PR", "志望動機", "学生時代に力を入れたこと", "失敗経験",
    "チーム開発経験", "周りを巻き込んだ経験", "困難を乗り越えた経験",
    "将来やりたいこと", "長所と短所", "インターン経験", "リーダーシップ経験",
]
PERSONAS = [
    "情報系の学部生、Web系エンジニア志望",
    "心理学専攻の修士、研究職志望",
    "経済学部、コンサル志望",
    "機械工学専攻、メーカー志望",
    "デザイン系の専門学生、UI/UX志望",
]

BASE = Path("/experiments/gold-editor")
GOLD_PATH = BASE / "gold" / "gold.jsonl"
INDEX_HTML = BASE / "static" / "index.html"

app = FastAPI(title="Gold Editor")


def _speaker(m) -> str:
    return "interviewer" if m.participant_id else "applicant"


def _extraction_prompt(topic: str, conv_text: str) -> list[LLMMessage]:
    system = f"""あなたは面接の記録係です。会話からトピック「{topic}」の概念グラフを抽出します。

# ルール
- label は具体的な概念・エンティティ・専門用語（「課題」「効果」等の抽象カテゴリ名にしない）。
- 重要な概念に絞り、ノードは 8〜15 個程度。
- node_type は次から必ず1つ: {", ".join(NODE_TYPES)}
- relation_type は次から必ず1つ: {", ".join(RELATION_TYPES)}
- coverage は covered(十分話せた)/weak(曖昧)/gap(触れたが未説明)。全部 covered にしない。

出力は次の JSON のみ：
{{"nodes":[{{"label":"...","node_type":"...","detail":"...","coverage":"..."}}],
 "edges":[{{"source":"...","target":"...","relation_type":"..."}}],
 "current_summary":"..."}}"""
    user = f"# 面接会話\n{conv_text}\n\nこの会話から概念グラフを JSON で抽出してください。"
    return [LLMMessage(role="system", content=system), LLMMessage(role="user", content=user)]


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return INDEX_HTML.read_text(encoding="utf-8")


@app.get("/api/meta")
def meta() -> dict:
    return {
        "node_types": NODE_TYPES,
        "relation_types": RELATION_TYPES,
        "topics": TOPICS,
        "personas": PERSONAS,
    }


def _conversation_prompt(topic: str, persona: str, turns: int) -> list[LLMMessage]:
    system = f"""あなたは面接の脚本家です。リアルで深掘りのある模擬面接の会話を作ります。
- トピック: 「{topic}」
- 応募者の背景: {persona}
- 面接官は応募者の回答の弱い点・曖昧な点を {turns} 回ほど深掘りする。
- 応募者は具体的な固有名詞・数字・経験を交えて答える（所々で詰まる）。

出力は次の JSON のみ：
{{"conversation": [{{"speaker": "interviewer", "text": "..."}}, {{"speaker": "applicant", "text": "..."}}]}}"""
    user = f"トピック「{topic}」、背景「{persona}」で模擬面接の会話を JSON で生成してください。"
    return [LLMMessage(role="system", content=system), LLMMessage(role="user", content=user)]


class GenConvRequest(BaseModel):
    topic: str
    persona: str = ""
    turns: int = 5


@app.post("/api/generate-conversation")
async def generate_conversation(req: GenConvRequest) -> dict:
    provider = get_llm_provider()
    data = await provider.generate_json(
        _conversation_prompt(req.topic, req.persona, req.turns), temperature=0.9
    )
    return {"session_id": None, "topic": req.topic, "turns": data.get("conversation", [])}


@app.get("/api/conversations")
def conversations() -> list[dict]:
    """完了した topic 付きセッションを会話として返す。"""
    db = SessionLocal()
    try:
        stmt = (
            select(PracticeSession)
            .where(
                PracticeSession.status == "completed",
                PracticeSession.topic_id.isnot(None),
                PracticeSession.deleted_at.is_(None),
            )
            .order_by(PracticeSession.created_at.desc())
            .limit(50)
        )
        sessions = list(db.execute(stmt).scalars().all())
        msg_repo = SessionMessageRepository(db)
        topic_repo = TopicRepository(db)
        out = []
        for s in sessions:
            topic = topic_repo.get_by_id(s.topic_id)
            msgs = msg_repo.list_by_session_id(s.id)
            if not msgs:
                continue
            out.append(
                {
                    "session_id": s.id,
                    "topic": topic.title if topic else "(不明)",
                    "turns": [{"speaker": _speaker(m), "text": m.content} for m in msgs],
                }
            )
        return out
    finally:
        db.close()


class DraftRequest(BaseModel):
    topic: str
    turns: list[dict]


@app.post("/api/draft")
async def draft(req: DraftRequest) -> dict:
    label = {"interviewer": "面接官", "applicant": "応募者"}
    conv_text = "\n".join(f"{label.get(t['speaker'], t['speaker'])}: {t['text']}" for t in req.turns)
    provider = get_llm_provider()
    graph = await provider.generate_json(_extraction_prompt(req.topic, conv_text), temperature=0.2)
    graph.setdefault("nodes", [])
    graph.setdefault("edges", [])
    graph.setdefault("current_summary", "")
    return graph


class SaveRequest(BaseModel):
    session_id: int | None = None
    topic: str
    turns: list[dict]
    graph: dict


@app.post("/api/save")
def save(req: SaveRequest) -> dict:
    GOLD_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "session_id": req.session_id,
        "topic": req.topic,
        "turns": req.turns,
        "graph": req.graph,
        "saved_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    with GOLD_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    total = sum(1 for _ in GOLD_PATH.open(encoding="utf-8"))
    return {"ok": True, "total_gold": total}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8100)
