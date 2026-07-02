"""SFT 用の合成データ生成（ステップ2）。

狙い:
- 「型(タクソノミー)を固定した一貫した正解」を、多様なトピックで大量に作る。
- これを小型モデルに学習させると、型・粒度を“暗黙的に”内面化する（distillation）。

流れ（1 例あたり）:
  1) Gemini に「面接会話」を生成させる（多様なトピック × 背景）
  2) Gemini に「型を固定した指示」で会話から概念グラフを抽出させる（＝正解）
  3) (固定プロンプト + 会話 → 正解JSON) を SFT ペアとして JSONL に保存

出力: data/sft_topic_extraction.jsonl（gitignore 済み）
  各行: {"messages": [system, user, assistant(JSON)], "meta": {...}}

実行（リポジトリ root から）:
  docker compose run --rm \
    -v "$(pwd)/experiments:/experiments" -e PYTHONPATH=/app \
    backend sh -c "python /experiments/finetuning/generate_sft_data.py --count 12"
"""
import argparse
import asyncio
import json
import random
from pathlib import Path

from app.services.ai.llm import get_llm_provider
from app.services.ai.llm.base import LLMMessage

# ── 固定タクソノミー（“ゆるく固定”：これがお手本の芯になる） ──────────────
NODE_TYPES = ["concept", "method", "problem", "goal", "result", "context", "component"]
RELATION_TYPES = ["uses", "addresses", "causes", "leads_to", "part_of", "contradicts"]

OUTPUT_PATH = Path("/experiments/finetuning/data/sft_topic_extraction.jsonl")

TOPICS = [
    "研究内容", "自己PR", "志望動機", "学生時代に力を入れたこと", "失敗経験",
    "チーム開発経験", "周りを巻き込んだ経験", "困難を乗り越えた経験",
    "将来やりたいこと", "長所と短所", "インターン経験", "リーダーシップ経験",
    "アルバイトで工夫したこと", "卒業制作", "ボランティア経験",
]
PERSONAS = [
    "情報系の学部生、Web系エンジニア志望",
    "心理学専攻の修士、研究職志望",
    "経済学部、コンサル志望",
    "機械工学専攻、メーカー志望",
    "デザイン系の専門学生、UI/UX志望",
    "文学部、出版・メディア志望",
]


def build_conversation_prompt(topic: str, persona: str, turns: int) -> list[LLMMessage]:
    system = f"""あなたは面接の脚本家です。リアルで深掘りのある模擬面接の会話を作ります。
- トピック: 「{topic}」
- 応募者の背景: {persona}
- 面接官は応募者の回答の弱い点・曖昧な点を {turns} 回ほど深掘りする。
- 応募者は具体的な固有名詞・数字・経験を交えて答える（ただし所々で詰まる）。

出力は次の JSON のみ：
{{"conversation": [{{"speaker": "interviewer", "text": "..."}}, {{"speaker": "applicant", "text": "..."}}]}}"""
    user = f"トピック「{topic}」、背景「{persona}」で模擬面接の会話を JSON で生成してください。"
    return [
        LLMMessage(role="system", content=system),
        LLMMessage(role="user", content=user),
    ]


def build_extraction_messages(topic: str, conversation_text: str) -> tuple[str, str]:
    """型を固定した抽出プロンプト。teacher 呼び出しと SFT の入力の両方で使う。"""
    system = f"""あなたは面接の記録係です。会話からトピック「{topic}」の概念グラフを抽出します。

# ルール
- label は具体的な概念・エンティティ・専門用語（抽象カテゴリ名にしない）。
- **重要な概念に絞り、ノードは 8〜15 個程度にする**（過剰に細分化しない）。
- node_type は次の中から必ず1つ選ぶ: {", ".join(NODE_TYPES)}
- relation_type は次の中から必ず1つ選ぶ: {", ".join(RELATION_TYPES)}
- coverage は covered(十分話せた)/weak(説明が弱い/曖昧)/gap(触れたが未説明) から選ぶ。
  **会話で詰まった・曖昧だった概念は weak、名前は出たが説明されていない概念は gap にする（全部 covered にしない）**。
- 概念どうしを関係で繋ぎ、ナレッジグラフにする。

出力は次の JSON のみ：
{{"nodes": [{{"label": "...", "node_type": "...", "detail": "...", "coverage": "..."}}],
 "edges": [{{"source": "...", "target": "...", "relation_type": "..."}}],
 "current_summary": "..."}}"""
    user = f"# 面接会話\n{conversation_text}\n\nこの会話から概念グラフを JSON で抽出してください。"
    return system, user


def _conversation_to_text(conv: list[dict]) -> str:
    label = {"interviewer": "面接官", "applicant": "応募者"}
    return "\n".join(f"{label.get(c.get('speaker'), c.get('speaker'))}: {c.get('text')}" for c in conv)


async def generate_one(provider, topic: str, persona: str, turns: int) -> dict | None:
    # 1) 会話生成
    conv_data = await provider.generate_json(
        build_conversation_prompt(topic, persona, turns), temperature=0.9
    )
    conversation = conv_data.get("conversation", [])
    if not conversation:
        return None
    conv_text = _conversation_to_text(conversation)

    # 2) 型固定で抽出（＝正解）
    system, user = build_extraction_messages(topic, conv_text)
    graph = await provider.generate_json(
        [LLMMessage(role="system", content=system), LLMMessage(role="user", content=user)],
        temperature=0.2,
    )
    if not graph.get("nodes"):
        return None

    # 3) SFT ペア（chat 形式）+ 素の会話/グラフ（pending 用）
    return {
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
            {"role": "assistant", "content": json.dumps(graph, ensure_ascii=False)},
        ],
        "conversation": conversation,
        "graph": graph,
        "meta": {"topic": topic, "persona": persona},
    }


async def main(count: int, topics: list[str], fmt: str, out: Path) -> None:
    provider = get_llm_provider()
    out.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with out.open("w", encoding="utf-8") as fout:
        for i in range(count):
            topic = topics[i % len(topics)]
            persona = random.choice(PERSONAS)
            turns = random.randint(4, 7)
            try:
                ex = await generate_one(provider, topic, persona, turns)
            except Exception as e:
                print(f"  [{i + 1}/{count}] 失敗 {topic}: {e}")
                continue
            if ex is None:
                print(f"  [{i + 1}/{count}] 空 {topic}: スキップ")
                continue
            if fmt == "pending":
                # Claude 検証待ちの素データ（会話 + Gemini 下書き）
                record = {
                    "id": f"pending-{i + 1:03d}",
                    "topic": topic,
                    "persona": persona,
                    "conversation": ex["conversation"],
                    "draft_graph": ex["graph"],
                }
            else:
                record = {"messages": ex["messages"], "meta": ex["meta"]}
            fout.write(json.dumps(record, ensure_ascii=False) + "\n")
            written += 1
            print(f"  [{i + 1}/{count}] OK {topic} / {persona} (nodes={len(ex['graph'].get('nodes', []))})")
    print(f"完了: {written}/{count} 件を {out} に書き出し")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=12)
    parser.add_argument("--topics", type=str, default="", help="カンマ区切りで対象トピックを限定")
    parser.add_argument("--format", dest="fmt", choices=["sft", "pending"], default="sft")
    parser.add_argument("--out", type=str, default=str(OUTPUT_PATH))
    args = parser.parse_args()
    topic_list = [t.strip() for t in args.topics.split(",") if t.strip()] or TOPICS
    asyncio.run(main(args.count, topic_list, args.fmt, Path(args.out)))
