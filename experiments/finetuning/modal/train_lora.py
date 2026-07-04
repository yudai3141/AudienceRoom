"""Modal 上で LoRA SFT（スモークテスト）。

- ベース: Qwen/Qwen2.5-3B-Instruct（日本語可・A10G 1枚で収まる）
- データ: sft_train.jsonl（chat形式30件）を**引数として**リモート関数へ渡す（小さいのでマウント不要）
- 出力: Modal Volume `audienceroom-lora` に LoRA アダプタを保存
- 学習後に1件だけ生成してみて、JSONとしてパースできるかの簡易チェック付き

実行（リポジトリ root から。Modal トークンは modal/.env に置く）:
  docker run --rm -it -v "$(pwd)/experiments:/experiments" \
    -w /experiments/finetuning --env-file modal/.env python:3.11-slim \
    bash -c "pip install -q modal && modal run modal/train_lora.py"
"""
import json

import modal

app = modal.App("audienceroom-lora-smoke")

# バージョンは API 互換性のため固定（trl の API は版によって大きく変わる）
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "torch==2.5.1",
        "transformers==4.46.3",
        "trl==0.12.2",
        "peft==0.13.2",
        "datasets==3.1.0",
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
def train(examples: list[dict], base_model: str, epochs: int, run_name: str) -> dict:
    import torch
    from datasets import Dataset
    from peft import LoraConfig
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from trl import SFTConfig, SFTTrainer

    ds = Dataset.from_list([{"messages": e["messages"]} for e in examples])
    tok = AutoTokenizer.from_pretrained(base_model)
    model = AutoModelForCausalLM.from_pretrained(
        base_model, torch_dtype=torch.bfloat16, device_map="auto"
    )

    peft_cfg = LoraConfig(
        r=16, lora_alpha=32, lora_dropout=0.05, task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    )
    cfg = SFTConfig(
        output_dir=f"/out/{run_name}",
        num_train_epochs=epochs,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,
        learning_rate=2e-4,
        lr_scheduler_type="cosine",
        warmup_ratio=0.05,
        logging_steps=5,
        bf16=True,
        max_seq_length=6144,
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        save_strategy="no",
        report_to=[],
    )
    trainer = SFTTrainer(
        model=model, tokenizer=tok, train_dataset=ds, peft_config=peft_cfg, args=cfg
    )
    result = trainer.train()
    trainer.save_model(f"/out/{run_name}/adapter")
    vol.commit()

    # ── 簡易サニティ: 学習データ1件の入力で生成し、JSON になるか見る ──
    msgs = examples[0]["messages"][:2]  # system + user
    prompt = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
    inputs = tok(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=1500, do_sample=False,
                             pad_token_id=tok.eos_token_id)
    gen = tok.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
    parse_ok, n_nodes = False, 0
    try:
        g = json.loads(gen.strip().removeprefix("```json").removeprefix("```").removesuffix("```"))
        parse_ok, n_nodes = True, len(g.get("nodes", []))
    except Exception:
        pass
    return {
        "train_loss": round(result.training_loss, 4),
        "sample_parse_ok": parse_ok,
        "sample_n_nodes": n_nodes,
        "sample_head": gen[:400],
        "adapter_path": f"/out/{run_name}/adapter (Modal Volume: audienceroom-lora)",
    }


@app.local_entrypoint()
def main(data: str = "data/sft_train.jsonl", epochs: int = 4,
         base_model: str = "Qwen/Qwen2.5-3B-Instruct", run_name: str = "smoke30"):
    examples = [json.loads(l) for l in open(data, encoding="utf-8") if l.strip()]
    print(f"学習データ {len(examples)} 件 / base={base_model} / epochs={epochs}")
    res = train.remote(examples, base_model, epochs, run_name)
    print(json.dumps(res, ensure_ascii=False, indent=2))
