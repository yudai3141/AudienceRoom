"""3条件（zero-shot / few-shot / LoRA）の推論を Modal で実行（S13b）。

- 入力: data/eval_prompts.jsonl（make_eval_prompts.py で事前生成）
- zero / few は素の Qwen2.5-3B-Instruct、lora は Volume の LoRA アダプタを装着
- 出力: data/predictions.jsonl（id × condition × 出力テキスト）

実行（リポジトリ root から）:
  docker run --rm -v "$(pwd)/experiments:/experiments" \
    -v ~/.modal.toml:/root/.modal.toml:ro \
    -w /experiments/finetuning python:3.11-slim \
    bash -c "pip install -q modal && modal run modal/run_conditions.py"
"""
import json
from pathlib import Path

import modal

app = modal.App("audienceroom-lora-eval")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "torch==2.5.1",
        "transformers==4.46.3",
        "peft==0.13.2",
        "accelerate==1.1.1",
    )
    .env({"PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True"})
)

vol = modal.Volume.from_name("audienceroom-lora", create_if_missing=True)
hf_cache = modal.Volume.from_name("hf-cache", create_if_missing=True)


@app.function(
    image=image, gpu="A10G", timeout=7200,
    volumes={"/out": vol, "/root/.cache/huggingface": hf_cache},
)
def infer(items: list[dict], base_model: str, adapter_run: str) -> list[dict]:
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tok = AutoTokenizer.from_pretrained(base_model)
    base = AutoModelForCausalLM.from_pretrained(
        base_model, torch_dtype=torch.bfloat16, device_map="auto"
    )

    def generate(model, messages) -> str:
        prompt = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = tok(prompt, return_tensors="pt").to(model.device)
        with torch.no_grad():
            out = model.generate(
                **inputs, max_new_tokens=3000, do_sample=False,
                temperature=None, top_p=None, top_k=None,
                pad_token_id=tok.eos_token_id,
            )
        return tok.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)

    results = []
    # 条件1・2: 素のベースモデル
    for it in items:
        for cond, key in (("zero", "messages_zero"), ("few", "messages_few")):
            text = generate(base, it[key])
            results.append({"id": it["id"], "condition": cond, "output": text})
            print(f"{it['id']} {cond}: {len(text)} chars")

    # 条件3: LoRA アダプタ装着（zero と同じ素プロンプト）
    model = PeftModel.from_pretrained(base, f"/out/{adapter_run}/adapter")
    model.eval()
    for it in items:
        text = generate(model, it["messages_zero"])
        results.append({"id": it["id"], "condition": "lora", "output": text})
        print(f"{it['id']} lora: {len(text)} chars")

    return results


@app.local_entrypoint()
def main(prompts: str = "data/eval_prompts.jsonl",
         base_model: str = "Qwen/Qwen2.5-3B-Instruct",
         adapter_run: str = "lora120",
         out: str = "data/predictions.jsonl"):
    items = [json.loads(l) for l in open(prompts, encoding="utf-8") if l.strip()]
    print(f"評価 {len(items)} 件 × 3条件 = {len(items)*3} 生成")
    results = infer.remote(items, base_model, adapter_run)
    with Path(out).open("w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"{len(results)} 件を {out} に保存")
