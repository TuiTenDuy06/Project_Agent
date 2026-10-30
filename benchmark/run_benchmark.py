"""Bắn tải vào LLM server (mode llm) hoặc vào agent (mode agent), lưu số liệu ra JSON."""

import argparse
import asyncio
import json
import os
import time
import uuid
from pathlib import Path

import httpx

SYSTEM_PROMPT = "Bạn là trợ lý chăm sóc khách hàng của chuỗi cửa hàng tiện lợi. Trả lời ngắn gọn."


async def call_llm(client: httpx.AsyncClient, args, prompt: str) -> dict:
    payload = {
        "model": args.model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": args.max_tokens,
        "temperature": 0,
        "stream": True,
        "stream_options": {"include_usage": True},
    }
    api_key = os.environ.get("BENCH_API_KEY")
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    start = time.perf_counter()
    first_token_at = None
    output_tokens = 0
    async with client.stream(
        "POST", f"{args.url}/chat/completions", json=payload, headers=headers
    ) as resp:
        resp.raise_for_status()
        async for line in resp.aiter_lines():
            if not line.startswith("data: "):
                continue
            data = line.removeprefix("data: ")
            if data == "[DONE]":
                break
            chunk = json.loads(data)
            if chunk.get("usage"):
                output_tokens = chunk["usage"]["completion_tokens"]
            choices = chunk.get("choices") or []
            if first_token_at is None and choices and choices[0]["delta"].get("content"):
                first_token_at = time.perf_counter()
    end = time.perf_counter()
    if first_token_at is None:
        raise RuntimeError("Không nhận được token nào")
    return {
        "ttft": first_token_at - start,
        "latency": end - start,
        "output_tokens": output_tokens,
        # TPOT: thời gian trung bình sinh mỗi token sau token đầu tiên
        "tpot": (end - first_token_at) / (output_tokens - 1) if output_tokens > 1 else None,
    }


async def call_agent(client: httpx.AsyncClient, args, prompt: str) -> dict:
    start = time.perf_counter()
    resp = await client.post(
        f"{args.url}/chat",
        json={"session_id": f"bench-{uuid.uuid4().hex[:12]}", "message": prompt},
    )
    resp.raise_for_status()
    return {"latency": time.perf_counter() - start}


async def run_level(args, prompts: list[str], concurrency: int) -> dict:
    call = call_llm if args.mode == "llm" else call_agent
    semaphore = asyncio.Semaphore(concurrency)
    results = []

    async def worker(i: int):
        async with semaphore:
            try:
                r = await call(client, args, prompts[i % len(prompts)])
                r["ok"] = True
            except (httpx.HTTPError, RuntimeError, json.JSONDecodeError) as e:
                r = {"ok": False, "error": f"{type(e).__name__}: {e}"}
            results.append(r)

    limits = httpx.Limits(max_connections=concurrency)
    async with httpx.AsyncClient(timeout=args.timeout, limits=limits) as client:
        start = time.perf_counter()
        await asyncio.gather(*(worker(i) for i in range(args.num_requests)))
        duration = time.perf_counter() - start

    return {
        "mode": args.mode,
        "model": args.model,
        "concurrency": concurrency,
        "duration": duration,
        "results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["llm", "agent"], default="llm")
    parser.add_argument("--url", required=True, help="llm: http://host:8000/v1, agent: http://host:8080")
    parser.add_argument("--model", default="Qwen/Qwen2.5-7B-Instruct")
    parser.add_argument("--dataset", default="benchmark/datasets/prompts.jsonl")
    parser.add_argument("--concurrency", default="1,4,8,16", help="Các mức đồng thời, cách nhau bởi dấu phẩy")
    parser.add_argument("--num-requests", type=int, default=50, help="Số request mỗi mức")
    parser.add_argument("--max-tokens", type=int, default=256)
    parser.add_argument("--timeout", type=float, default=120)
    parser.add_argument("--out", default="benchmark/results")
    args = parser.parse_args()

    lines = Path(args.dataset).read_text(encoding="utf-8").splitlines()
    prompts = [json.loads(line)["prompt"] for line in lines if line.strip()]
    run_dir = Path(args.out) / time.strftime("%Y%m%d-%H%M%S")
    run_dir.mkdir(parents=True)

    for level in [int(x) for x in args.concurrency.split(",")]:
        print(f"Đang chạy concurrency={level} ...")
        data = asyncio.run(run_level(args, prompts, level))
        ok = sum(r["ok"] for r in data["results"])
        print(f"  xong trong {data['duration']:.1f}s, thành công {ok}/{args.num_requests}")
        (run_dir / f"c{level}.json").write_text(json.dumps(data, ensure_ascii=False, indent=2))

    print(f"Kết quả lưu tại {run_dir}")


if __name__ == "__main__":
    main()
