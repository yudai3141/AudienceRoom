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


QUALITIES = [
    "受け答えが具体的で流暢（数字・固有名詞が出る）",
    "所々で詰まり、一部の質問には曖昧にしか答えられない",
    "抽象的な回答が多く、深掘りされると答えに窮する箇所がある",
]


def build_conversation_prompt(topic: str, persona: str, turns: int, quality: str) -> list[LLMMessage]:
    system = f"""あなたは面接の脚本家です。リアルな模擬面接の会話を作ります。
- トピック: 「{topic}」
- 応募者の背景: {persona}
- 応募者のタイプ: {quality}
- 面接官は弱い点・曖昧な点を {turns} 回ほど深掘りする。
- **発話は短く**: 面接官は1〜2文、応募者は2〜4文。長広舌にしない。
- 応募者のタイプに応じて、答えられない質問・曖昧なままの論点を残すこと。

出力は次の JSON のみ：
{{"conversation": [{{"speaker": "interviewer", "text": "..."}}, {{"speaker": "applicant", "text": "..."}}]}}"""
    user = f"トピック「{topic}」、背景「{persona}」で模擬面接の会話を JSON で生成してください。"
    return [
        LLMMessage(role="system", content=system),
        LLMMessage(role="user", content=user),
    ]


def _conv_text(conv: list[dict]) -> str:
    label = {"interviewer": "面接官", "applicant": "応募者"}
    return "\n".join(f"{label.get(c.get('speaker'), c.get('speaker'))}: {c.get('text')}" for c in conv)


def select_fewshot(examples: list[dict], topic: str, k: int = 3) -> list[dict]:
    """同ドメイン優先で最大 k 例を選ぶ（同topic 2 + 他 1 が基本形）。"""
    same = [e for e in examples if e.get("topic") == topic]
    other = [e for e in examples if e.get("topic") != topic]
    return (same[:2] + other)[:k]


def fewshot_block(examples: list[dict]) -> str:
    """人間検証済み gold を few-shot としてプロンプトに埋め込む。"""
    if not examples:
        return ""
    parts = ["\n# 良い抽出の例（この粒度・型付け・coverage 判断・関係の張り方を踏襲すること）"]
    for i, ex in enumerate(examples, 1):
        parts.append(f"\n## 例{i}: トピック「{ex['topic']}」の会話")
        parts.append(_conv_text(ex["conversation"]))
        parts.append(f"\n## 例{i} の正しい出力")
        parts.append(json.dumps(ex["graph"], ensure_ascii=False))
    return "\n".join(parts)


def build_extraction_messages(
    topic: str, conversation_text: str, examples: list[dict] | None = None
) -> tuple[str, str]:
    """型を固定した抽出プロンプト。teacher 呼び出しと SFT の入力の両方で使う。"""
    system = f"""あなたは面接の記録係です。会話からトピック「{topic}」の概念グラフを抽出します。

# ルール（オントロジー v0.1）
- **中心ノード（主題・プロジェクト）を必ず1つ立て、グラフのハブにする**。label は会話中の呼び方に忠実に。
- **全ノードはハブから辿れるようにする**（孤立したノード・サブグラフを作らない）。
- label は具体的な概念・エンティティ・専門用語（「課題」「効果」等の抽象カテゴリ名にしない）。
- **重要な概念に絞り、ノードは 8〜15 個程度**（過剰に細分化しない）。
- node_type は次の中から必ず1つ選ぶ: {", ".join(NODE_TYPES)}
- relation_type は次の中から必ず1つ選ぶ: {", ".join(RELATION_TYPES)}
- 関係の向き:
  - 遂行中に生じた困難・対立: ハブ --causes--> problem
  - 課題・インサイト → それを受けた行動・設計判断: problem --leads_to--> method/component（動機づけの向き）
  - 行動・検証 → 成果: method --leads_to--> result、成果 → 学び/応用: result --leads_to--> result/goal
  - 調査 → 発見: method --leads_to--> problem。役割・貢献の帰属: component --part_of--> ハブ/method
  - addresses はハブレベルの対処のみ。同一ペアに両方向は張らない。矛盾は contradicts で保持
- coverage は covered(十分話せた)/weak(説明が弱い/曖昧)/gap(触れたが未説明) から選ぶ。
  **会話で詰まった・曖昧だった概念は weak、名前は出たが説明されていない・答えられなかった概念は gap（全部 covered にしない）**。

出力は次の JSON のみ：
{{"nodes": [{{"label": "...", "node_type": "...", "detail": "...", "coverage": "..."}}],
 "edges": [{{"source": "...", "target": "...", "relation_type": "..."}}],
 "current_summary": "..."}}"""
    system = system + fewshot_block(examples or [])
    user = f"# 面接会話\n{conversation_text}\n\nこの会話から概念グラフを JSON で抽出してください。"
    return system, user


def _conversation_to_text(conv: list[dict]) -> str:
    label = {"interviewer": "面接官", "applicant": "応募者"}
    return "\n".join(f"{label.get(c.get('speaker'), c.get('speaker'))}: {c.get('text')}" for c in conv)


async def generate_one(provider, topic: str, persona: str, turns: int, quality: str, examples: list[dict] | None = None) -> dict | None:
    # 1) 会話生成
    conv_data = await provider.generate_json(
        build_conversation_prompt(topic, persona, turns, quality), temperature=0.9
    )
    conversation = conv_data.get("conversation", [])
    if not conversation:
        return None
    conv_text = _conversation_to_text(conversation)

    # 2) 型固定で抽出（＝正解）
    system, user = build_extraction_messages(topic, conv_text, select_fewshot(examples or [], topic))
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


async def main(count: int, topics: list[str], fmt: str, out: Path, prefix: str, fewshot: str) -> None:
    provider = get_llm_provider()
    examples: list[dict] = []
    if fewshot:
        examples = [json.loads(l) for l in open(fewshot, encoding="utf-8") if l.strip()]
        print(f"few-shot 例: {len(examples)} 件をロード（各生成で同ドメイン優先の3件を注入）")
    out.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with out.open("w", encoding="utf-8") as fout:
        for i in range(count):
            topic = topics[i % len(topics)]
            persona = random.choice(PERSONAS)
            quality = QUALITIES[i % len(QUALITIES)]
            turns = 3
            try:
                ex = await generate_one(provider, topic, persona, turns, quality, examples)
            except Exception as e:
                print(f"  [{i + 1}/{count}] 失敗 {topic}: {e}")
                continue
            if ex is None:
                print(f"  [{i + 1}/{count}] 空 {topic}: スキップ")
                continue
            if fmt == "pending":
                # Claude 検証待ちの素データ（会話 + Gemini 下書き）
                record = {
                    "id": f"{prefix}-{i + 1:03d}",
                    "topic": topic,
                    "persona": persona,
                    "quality": quality,
                    "conversation": ex["conversation"],
                    "draft_graph": ex["graph"],
                }
            else:
                record = {"messages": ex["messages"], "meta": ex["meta"] | {"quality": quality}}
            fout.write(json.dumps(record, ensure_ascii=False) + "\n")
            written += 1
            print(f"  [{i + 1}/{count}] OK {topic} / {persona} / {quality[:12]}… (発話={len(ex['conversation'])}, nodes={len(ex['graph'].get('nodes', []))})")
    print(f"完了: {written}/{count} 件を {out} に書き出し")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=12)
    parser.add_argument("--topics", type=str, default="", help="カンマ区切りで対象トピックを限定")
    parser.add_argument("--format", dest="fmt", choices=["sft", "pending"], default="sft")
    parser.add_argument("--out", type=str, default=str(OUTPUT_PATH))
    parser.add_argument("--prefix", type=str, default="pending", help="pending 形式の id プレフィックス")
    parser.add_argument("--fewshot", type=str, default="", help="few-shot 例 jsonl（人間検証済み gold）")
    args = parser.parse_args()
    topic_list = [t.strip() for t in args.topics.split(",") if t.strip()] or TOPICS
    asyncio.run(main(args.count, topic_list, args.fmt, Path(args.out), args.prefix, args.fewshot))
