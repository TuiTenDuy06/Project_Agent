# Bài 17: Benchmark serving

## Mục tiêu

Sau bài này bạn sẽ:

- Hiểu và đo được các chỉ số hiệu năng của LLM: **TTFT, TPOT, độ trễ end-to-end, throughput**.
- Hiểu mối quan hệ giữa **số request đồng thời (concurrency)**, độ trễ và thông lượng.
- Tự viết **script benchmark** bằng Python async, có hỗ trợ streaming.
- Chạy **thí nghiệm có kiểm soát** để so sánh cấu hình serving (model gốc và model lượng tử hóa).
- Đặt **mục tiêu chất lượng dịch vụ (SLO)**, ước lượng **sức chứa**: một GPU phục vụ được bao nhiêu khách.
- Viết **báo cáo benchmark**.

## Kiến thức cần học

| Chủ đề | Tài liệu |
|---|---|
| Các chỉ số hiệu năng LLM | [NVIDIA: LLM Inference Benchmarking: Fundamental Concepts](https://developer.nvidia.com/blog/llm-benchmarking-fundamental-concepts/) |
| Streaming (SSE) | [MDN: Server-sent events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events) |
| Streaming trong API OpenAI | [OpenAI: Streaming responses](https://platform.openai.com/docs/api-reference/chat-streaming) |
| Benchmark chính thức của vLLM | [vLLM: Benchmark CLI](https://docs.vllm.ai/en/latest/contributing/benchmarks.html) |
| httpx async | [httpx: Async Support](https://www.python-httpx.org/async/) |
| Định luật Little | [Wikipedia: Little's law](https://en.wikipedia.org/wiki/Little%27s_law) |

---

## Phần lý thuyết

### 1. Các chỉ số cần đo

Một request đến LLM có dạng streaming (trả từng token) diễn ra như sau:

```
gửi request                          token đầu tiên                         token cuối
    │◀────────────── TTFT ────────────▶│◀─ TPOT ─▶│◀─ TPOT ─▶│ ... │◀─ TPOT ─▶│
    │◀───────────────────────────── Latency (end-to-end) ──────────────────────▶│
```

| Chỉ số | Định nghĩa | Ảnh hưởng đến khách | Phụ thuộc vào |
|---|---|---|---|
| **TTFT** (Time To First Token) | Thời gian từ lúc gửi đến khi nhận token đầu tiên | Khách thấy bot "bắt đầu trả lời" sau bao lâu | Prefill: độ dài prompt, số request đang chờ |
| **TPOT** (Time Per Output Token) | Thời gian trung bình sinh mỗi token **sau** token đầu tiên | Chữ hiện ra nhanh hay chậm | Decode: số request chạy chung một lượt (batch) |
| **Latency (E2E)** | Tổng thời gian một request | Thời gian chờ toàn bộ câu trả lời | TTFT + TPOT × (số token − 1) |
| **Throughput (req/s)** | Số request hoàn thành mỗi giây | Hệ thống phục vụ được bao nhiêu khách | Toàn bộ hệ thống |
| **Throughput (token/s)** | Số token đầu ra mỗi giây, cộng dồn mọi request | Hiệu suất sử dụng GPU | Batch size, model, GPU |
| **Tỉ lệ lỗi** | Số request thất bại hoặc quá thời gian | Khách không nhận được trả lời | Quá tải, cấu hình sai |

TPOT còn được gọi là ITL (Inter-Token Latency) ở một số công cụ. Hai khái niệm gần giống nhau.

Người đọc thường thấy chữ hiện ra đủ mượt khi TPOT dưới khoảng 50–100ms (10–20 token/giây).

### 2. Đánh đổi giữa độ trễ và thông lượng

Khi tăng **concurrency** (số request gửi cùng lúc):

- **Throughput tăng**: GPU xử lý nhiều request trong một lượt tính (continuous batching, Bài 16), nên tận dụng tốt hơn.
- **Latency cũng tăng**: mỗi lượt tính phục vụ nhiều request hơn nên chậm hơn một chút, và khi đầy thì request phải **xếp hàng chờ**, làm TTFT tăng vọt.

```
throughput                                latency (p99)
   │            ________  bão hòa            │                    /
   │         __/                             │                  _/   ← xếp hàng
   │      __/                                │             ___/
   │   __/                                   │   _________/
   │__/                                      │__/
   └─────────────────── concurrency          └─────────────────── concurrency
```

**Mục tiêu của benchmark:** tìm **điểm vận hành**, tức mức concurrency cao nhất mà vẫn đáp ứng yêu cầu về độ trễ.

### 3. SLO: mục tiêu chất lượng dịch vụ

**SLO** (Service Level Objective) là cam kết về chất lượng, viết bằng con số. Ví dụ cho agent chăm sóc khách hàng:

- TTFT p95 < 1 giây
- TPOT p50 < 50 ms
- Tỉ lệ lỗi < 1%

Concurrency cao nhất **vẫn đạt mọi SLO** chính là sức chứa thực tế của một GPU.

### 4. Ước lượng số khách: định luật Little

```
Số request đang xử lý đồng thời = Số request mỗi giây × Thời gian xử lý mỗi request
```

Ví dụ: benchmark cho thấy GPU đạt SLO ở concurrency 16, mỗi request mất trung bình 4 giây. Thông lượng là 16 / 4 = **4 request/giây**. Giả sử mỗi khách gửi trung bình 1 tin nhắn mỗi 30 giây khi đang chat, thì một GPU phục vụ được khoảng 4 × 30 = **120 khách chat cùng lúc**.

Lưu ý: **một câu hỏi của khách = nhiều lần gọi LLM** (vòng lặp tool, thường 2–3 lần). Nhớ nhân lên khi tính.

### 5. Những điều làm benchmark sai lệch

- **Prompt không giống thực tế**: prompt quá ngắn hoặc quá dài so với thật. Ta dùng câu hỏi CSKH thật.
- **Chạy quá ít request**: p99 của 10 request là vô nghĩa. Nên chạy ít nhất 50–100 request mỗi mức.
- **Máy benchmark quá gần hoặc quá xa**: đo từ máy bạn qua Internet sẽ cộng thêm độ trễ mạng. Muốn đo **riêng server** thì chạy script ngay trên máy GPU.
- **"Làm nóng" (warm-up)**: vài request đầu thường chậm hơn. Có thể bỏ qua mức concurrency đầu tiên hoặc chạy thử một lần trước.
- **Thay đổi nhiều thứ cùng lúc**: mỗi thí nghiệm chỉ đổi **một** yếu tố.

---

## Thực hành từng bước

> Chuẩn bị: máy GPU từ Bài 16 đang chạy vLLM. Trên máy bạn: `cd ~/project_agent && source .venv/bin/activate`. `httpx` đã có trong nhóm `dev`.

### Bước 1: Tập prompt benchmark

```bash
mkdir -p benchmark/datasets
```

Tạo file `benchmark/datasets/prompts.jsonl`. Mỗi dòng là một JSON (định dạng **JSON Lines**):

```json
{"prompt": "Cửa hàng ở Quận 1 mở cửa đến mấy giờ?"}
{"prompt": "Sữa tươi Vinamilk 1 lít giá bao nhiêu?"}
{"prompt": "Hiện đang có chương trình khuyến mãi nào không?"}
{"prompt": "Mình mua bánh mì bị hỏng, đổi trả thế nào?"}
{"prompt": "Thẻ thành viên tích điểm ra sao?"}
{"prompt": "Cửa hàng Bình Thạnh còn mì ly Hảo Hảo không?"}
{"prompt": "Có thanh toán bằng ví điện tử được không?"}
{"prompt": "Mình muốn khiếu nại nhân viên thái độ không tốt."}
{"prompt": "Gợi ý cho mình bữa sáng nhanh dưới 30.000đ."}
{"prompt": "Cửa hàng có giao hàng tận nhà không?"}
```

💡 Khi đã có khách thật, hãy lấy mẫu câu hỏi thật (đã xóa thông tin cá nhân) từ bảng `messages` để benchmark sát thực tế hơn.

### Bước 2: Script benchmark

Tạo file `benchmark/run_benchmark.py`:

```python
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
```

Đọc hiểu các phần quan trọng:

**`call_llm`: đo một request streaming**

- `"stream": True`: server trả từng mẩu (chunk) ngay khi sinh ra, theo định dạng **SSE** (Server-Sent Events). Mỗi mẩu là một dòng `data: {...}`, dòng cuối là `data: [DONE]`.
- `"stream_options": {"include_usage": True}`: yêu cầu server gửi thêm một mẩu cuối chứa **số token** chính xác. Mẩu này có `choices` rỗng, nên code dùng `chunk.get("choices") or []` để không lỗi.
- `client.stream(...)` và `resp.aiter_lines()`: đọc từng dòng **ngay khi nó đến**, không đợi cả response.
- **TTFT** = thời điểm nhận mẩu đầu tiên **có nội dung** − thời điểm gửi.
- **TPOT** = (thời điểm kết thúc − thời điểm token đầu) / (số token − 1).
- `"temperature": 0`: câu trả lời ổn định hơn giữa các lần chạy, giúp so sánh công bằng.
- `max_tokens`: giới hạn độ dài trả lời. Độ dài ảnh hưởng mạnh đến latency, nên giữ cố định khi so sánh.
- API key đọc từ biến môi trường `BENCH_API_KEY`, **không truyền qua tham số dòng lệnh**, vì tham số dòng lệnh bị lưu trong lịch sử terminal.

**`call_agent`: đo toàn bộ agent** (gồm vòng lặp tool, database). Agent không streaming nên chỉ đo latency. Mỗi request dùng `session_id` ngẫu nhiên để không bị ảnh hưởng bởi lịch sử hội thoại.

**`run_level`: chạy một mức concurrency**

- `asyncio.Semaphore(concurrency)`: giới hạn **tối đa `concurrency` request chạy cùng lúc**. Đây chính là bài tập 3 của Bài 02.
- `asyncio.gather(...)`: tạo `num_requests` tác vụ. Semaphore đảm bảo chỉ `concurrency` tác vụ chạy song song, request này xong thì request khác vào ngay, giống khách thật liên tục đến.
- `httpx.Limits(max_connections=concurrency)`: đủ kết nối cho số request song song.
- Lỗi của từng request được **ghi lại** chứ không làm dừng cả benchmark. Tỉ lệ lỗi cũng là một kết quả quan trọng.

**`main`**: chạy lần lượt từng mức concurrency, lưu kết quả **thô** của mỗi mức ra một file JSON trong thư mục đặt tên theo thời gian. Lưu dữ liệu thô giúp bạn phân tích lại theo cách khác sau này mà không phải chạy lại.

### Bước 3: Script phân tích

Tạo file `benchmark/analyze.py`:

```python
"""Đọc kết quả của run_benchmark.py và in bảng tổng hợp."""

import argparse
import json
from pathlib import Path


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    values = sorted(values)
    return values[min(len(values) - 1, int(len(values) * p))]


def fmt(value: float | None, scale: float = 1, digits: int = 2) -> str:
    return "-" if value is None else f"{value * scale:.{digits}f}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Thư mục kết quả, ví dụ benchmark/results/20261030-101500")
    args = parser.parse_args()

    files = sorted(Path(args.input).glob("c*.json"), key=lambda f: int(f.stem[1:]))
    print(
        "| Concurrency | Thành công | Req/s | Token/s | TTFT p50 (ms) | TTFT p99 (ms) "
        "| TPOT p50 (ms) | Latency p50 (s) | Latency p90 (s) | Latency p99 (s) |"
    )
    print("|---|---|---|---|---|---|---|---|---|---|")
    for f in files:
        data = json.loads(f.read_text())
        ok = [r for r in data["results"] if r["ok"]]
        total = len(data["results"])
        ttft = [r["ttft"] for r in ok if "ttft" in r]
        tpot = [r["tpot"] for r in ok if r.get("tpot") is not None]
        latency = [r["latency"] for r in ok]
        tokens = sum(r.get("output_tokens", 0) for r in ok)
        duration = data["duration"]
        print(
            f"| {data['concurrency']} | {len(ok)}/{total} | {len(ok) / duration:.2f} "
            f"| {tokens / duration:.1f} | {fmt(percentile(ttft, 0.5), 1000, 0)} "
            f"| {fmt(percentile(ttft, 0.99), 1000, 0)} | {fmt(percentile(tpot, 0.5), 1000, 1)} "
            f"| {fmt(percentile(latency, 0.5))} | {fmt(percentile(latency, 0.9))} "
            f"| {fmt(percentile(latency, 0.99))} |"
        )
        errors = {r["error"] for r in data["results"] if not r["ok"]}
        for e in list(errors)[:3]:
            print(f"  lỗi c={data['concurrency']}: {e}")


if __name__ == "__main__":
    main()
```

Giải thích:

- **`percentile`**: sắp xếp các giá trị, lấy phần tử ở vị trí `p` (ví dụ 0,99 là vị trí 99%). Đây là cách tính đơn giản, đủ chính xác khi có từ 50 mẫu trở lên.
- **Req/s và token/s** tính trên **thời gian thực tế của cả mức** (`duration`), không phải cộng thời gian từng request. Đó mới là thông lượng thật của hệ thống.
- Bảng in ra theo định dạng **Markdown**, dán thẳng vào báo cáo được.
- In tối đa 3 loại lỗi khác nhau của mỗi mức để bạn biết vì sao request thất bại.

### Bước 4: Chạy thử với cấu hình nhỏ

Đặt API key của vLLM vào biến môi trường (không lưu vào lịch sử lệnh nếu bắt đầu dòng bằng dấu cách, tùy cấu hình shell):

```bash
export BENCH_API_KEY=<VLLM_API_KEY>
```

Chạy thử nhanh để chắc chắn mọi thứ hoạt động:

```bash
python benchmark/run_benchmark.py --url https://<dia-chi-pod>/v1 --concurrency 1,2 --num-requests 4
```

```bash
python benchmark/analyze.py --input benchmark/results/<thu-muc-vua-tao>
```

Nếu mọi request thành công và bảng có số liệu, chuyển sang bước tiếp.

> 💡 **Đo chính xác hơn:** chạy script **ngay trên máy GPU** (copy 2 file script và tập prompt lên, rồi dùng `--url http://localhost:8000/v1`). Như vậy loại bỏ được độ trễ mạng giữa máy bạn và máy GPU. Đo từ máy bạn thì kết quả gần với trải nghiệm thật của app hơn, nhưng bị nhiễu do mạng. Hãy ghi rõ đo từ đâu trong báo cáo.

### Bước 5: Thí nghiệm 1: tìm điểm vận hành

```bash
python benchmark/run_benchmark.py --url https://<dia-chi-pod>/v1 --concurrency 1,4,8,16,32,64 --num-requests 100
```

```bash
python benchmark/analyze.py --input benchmark/results/<thu-muc-vua-tao>
```

Trong lúc chạy, mở một terminal trên máy GPU và theo dõi:

```bash
watch -n 1 nvidia-smi
```

Cột **GPU-Util** tăng dần theo concurrency.

**Đọc kết quả:**

1. **Token/s** tăng thế nào khi concurrency tăng? Đến mức nào thì gần như không tăng nữa (bão hòa)?
2. **TTFT p99** bắt đầu tăng mạnh ở mức nào? Đó là dấu hiệu request bắt đầu **xếp hàng**.
3. **TPOT p50** tăng chậm hay nhanh?
4. Có lỗi không? Ở mức nào?
5. Mức concurrency **cao nhất mà vẫn đạt SLO** (ví dụ TTFT p99 < 1000ms, TPOT p50 < 50ms, không lỗi) là bao nhiêu?

### Bước 6: Thí nghiệm 2: so sánh bản gốc và bản lượng tử hóa

Khởi động lại vLLM với bản AWQ (Bước 8 của Bài 16), rồi chạy **đúng** lệnh benchmark như thí nghiệm 1, chỉ đổi `--model`:

```bash
python benchmark/run_benchmark.py --url https://<dia-chi-pod>/v1 --model Qwen/Qwen2.5-7B-Instruct-AWQ --concurrency 1,4,8,16,32,64 --num-requests 100
```

So sánh hai bảng: bản AWQ nhanh hơn hay chậm hơn ở concurrency thấp? Chịu được concurrency cao hơn không (nhờ KV cache lớn hơn)? Kết hợp với **điểm eval** từ Bài 16 để quyết định: tốc độ tăng có đáng với chất lượng giảm không?

**Các thí nghiệm khác bạn có thể làm** (mỗi lần chỉ đổi một yếu tố):

| Yếu tố | Cách đổi |
|---|---|
| Độ dài trả lời | `--max-tokens 64` và `--max-tokens 512` |
| Giới hạn số request cùng lúc của vLLM | Thêm `--max-num-seqs 16` khi chạy `vllm serve` |
| Độ dài ngữ cảnh | `--max-model-len 4096` và `16384` |
| Loại GPU | Thuê GPU khác, chạy lại cùng bộ thí nghiệm |

### Bước 7: Benchmark toàn bộ agent

Benchmark LLM chỉ đo **một lần gọi**. Khách thật trải nghiệm **cả agent**: nhiều lần gọi LLM, truy vấn database, RAG. Để đo, chạy app trên máy bạn (với `.env` đang trỏ tới vLLM), rồi:

```bash
python benchmark/run_benchmark.py --mode agent --url http://localhost:8080 --concurrency 1,4,8 --num-requests 30
```

```bash
python benchmark/analyze.py --input benchmark/results/<thu-muc-vua-tao>
```

So sánh latency của agent với latency một lần gọi LLM: agent chậm hơn bao nhiêu lần? Điều đó cho biết trung bình agent gọi LLM bao nhiêu vòng.

> ⚠️ **Cảnh báo:**
> - **Không** benchmark agent qua tên miền production: bạn sẽ bị chính rate limit của Nginx chặn (429), và làm chậm khách thật. Hãy chạy trên máy bạn hoặc một máy thử nghiệm riêng.
> - **Không** benchmark với Gemini API ở mức concurrency cao: vừa tốn tiền, vừa bị giới hạn tốc độ (429) nên kết quả không phản ánh gì.
> - Benchmark agent sẽ **ghi dữ liệu vào bảng `messages`** (các session `bench-...`). Trên máy thử nghiệm thì không sao.

### Bước 8: So sánh với công cụ chính thức (tùy chọn)

vLLM có sẵn công cụ benchmark (lệnh `vllm bench serve`) với nhiều tùy chọn và bộ dữ liệu chuẩn. Đọc [tài liệu benchmark của vLLM](https://docs.vllm.ai/en/latest/contributing/benchmarks.html) và thử chạy trên máy GPU. So sánh kết quả với script của bạn. Nếu chênh nhau nhiều, hãy tìm hiểu vì sao: khác độ dài prompt, khác cách tính, khác vị trí đo.

### Bước 9: Viết báo cáo benchmark

Tạo file `benchmark/BAO_CAO.md` theo mẫu:

```markdown
# Báo cáo benchmark serving

## Môi trường
- Ngày đo:
- GPU: (tên, VRAM), nhà cung cấp, giá thuê/giờ:
- vLLM phiên bản:
- Model:
- Tham số vLLM: --max-model-len ..., --gpu-memory-utilization ...
- Script chạy từ: (máy GPU / máy cá nhân qua Internet)
- Tập prompt: benchmark/datasets/prompts.jsonl, max_tokens = 256

## SLO
- TTFT p99 < 1000 ms
- TPOT p50 < 50 ms
- Tỉ lệ lỗi < 1%

## Kết quả: Qwen2.5-7B-Instruct (BF16)
(dán bảng từ analyze.py)

## Kết quả: Qwen2.5-7B-Instruct-AWQ
(dán bảng)

## Kết quả: toàn bộ agent
(dán bảng)

## Nhận xét
- Điểm bão hòa thông lượng:
- Concurrency tối đa đạt SLO:
- So sánh BF16 và AWQ (tốc độ và điểm eval):

## Ước lượng sức chứa
- Thông lượng tại điểm vận hành: ... request LLM/giây
- Trung bình ... lần gọi LLM cho mỗi câu hỏi của khách
- => khoảng ... câu hỏi/giây, khoảng ... khách chat cùng lúc mỗi GPU

## Đề xuất
- Cấu hình chọn cho production:
- Lý do:
```

Commit script và báo cáo. Thư mục `benchmark/results/` đã nằm trong `.gitignore` (Bài 01), nên dữ liệu thô không bị commit:

```bash
git add benchmark/
```

```bash
git commit -m "Bài 17: script benchmark serving và báo cáo"
```

```bash
git push
```

> ⚠️ **Nhớ tắt hoặc xóa máy GPU** khi xong.

---

## Kiểm tra kết quả

- [ ] Chạy được benchmark ở chế độ `llm` với ít nhất 5 mức concurrency, 100 request mỗi mức.
- [ ] Giải thích được TTFT, TPOT, latency, throughput thay đổi thế nào khi tăng concurrency.
- [ ] Xác định được concurrency tối đa đạt SLO.
- [ ] Có bảng so sánh BF16 và AWQ.
- [ ] Có báo cáo `benchmark/BAO_CAO.md` kèm ước lượng sức chứa.
- [ ] Đã tắt máy GPU.

## Lỗi thường gặp

| Lỗi | Nguyên nhân | Cách sửa |
|---|---|---|
| Mọi request lỗi `HTTPStatusError: 401` | Chưa `export BENCH_API_KEY` hoặc sai key | Kiểm tra `echo $BENCH_API_KEY` |
| `RuntimeError: Không nhận được token nào` | Server không trả nội dung (thường do model trả về rỗng hoặc sai tên model) | Thử gọi `curl` như Bài 16 Bước 4 |
| Nhiều lỗi `ReadTimeout` ở concurrency cao | Server quá tải, request chờ quá lâu | Đây là **kết quả** (vượt sức chứa). Có thể tăng `--timeout` để đo được latency thật |
| `TTFT`, `TPOT` hiện `-` | Server không hỗ trợ `stream_options` hoặc không gửi `usage` | Kiểm tra phiên bản vLLM; với API khác có thể không hỗ trợ |
| Kết quả mỗi lần chạy chênh nhau nhiều | Quá ít request, mạng không ổn định | Tăng `--num-requests`, chạy script ngay trên máy GPU |
| `FileExistsError` ở thư mục kết quả | Hai lần chạy bắt đầu trong cùng một giây | Đợi 1 giây rồi chạy lại |

## Bài tập

1. Vẽ biểu đồ "Token/s theo concurrency" và "TTFT p99 theo concurrency" từ file JSON kết quả (dùng `matplotlib` hoặc dán số liệu vào Google Sheets).
2. Thêm cột **"Goodput"**: số request/giây **đạt SLO** (không chỉ thành công mà còn đủ nhanh). Sửa `analyze.py` để tính.
3. Thêm tùy chọn `--duration 60` cho `run_benchmark.py`: thay vì chạy số request cố định, gửi liên tục trong 60 giây. Cách này có ưu điểm gì?
4. Tính chi phí mỗi 1.000 câu hỏi khi tự host (giá GPU/giờ chia cho số câu hỏi/giờ ở điểm vận hành). So sánh với chi phí Gemini.
5. (Nâng cao) Thêm chế độ gửi request theo **phân phối Poisson** (khách đến ngẫu nhiên với tốc độ trung bình X request/giây) thay vì concurrency cố định. Tìm hiểu tham số `--request-rate` trong benchmark chính thức của vLLM.

## Checklist hoàn thành

- [ ] Hiểu TTFT, TPOT, latency, throughput, SLO, goodput
- [ ] Hiểu đánh đổi giữa độ trễ và thông lượng khi tăng concurrency
- [ ] Viết và chạy được script benchmark async có streaming
- [ ] Làm thí nghiệm có kiểm soát, mỗi lần đổi một yếu tố
- [ ] Ước lượng được sức chứa và chi phí
- [ ] Có báo cáo benchmark, đã commit

➡️ Tiếp theo: [Bài 18: Vận hành, chi phí, mở rộng, checklist go-live](bai-18-van-hanh.md)
