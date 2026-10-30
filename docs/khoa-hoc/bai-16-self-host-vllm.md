# Bài 16: Tự chạy LLM bằng vLLM trên GPU

## Mục tiêu

Sau bài này bạn sẽ:

- Hiểu khi nào nên **tự host LLM** thay vì dùng API, và đánh đổi những gì.
- Ước lượng được **GPU cần bao nhiêu bộ nhớ** cho một model.
- Hiểu vì sao **vLLM** phục vụ nhanh: PagedAttention, continuous batching.
- Thuê GPU theo giờ, chạy model mã nguồn mở **Qwen2.5-7B-Instruct** bằng vLLM, có tool calling.
- Chuyển agent sang dùng model tự host **mà không sửa dòng code nào**, rồi so sánh chất lượng bằng bộ eval.

## Kiến thức cần học

| Chủ đề | Tài liệu |
|---|---|
| vLLM | [vLLM docs: Quickstart](https://docs.vllm.ai/en/latest/getting_started/quickstart.html) |
| Server tương thích OpenAI | [vLLM: OpenAI-Compatible Server](https://docs.vllm.ai/en/latest/serving/openai_compatible_server.html) |
| Tool calling trong vLLM | [vLLM: Tool Calling](https://docs.vllm.ai/en/latest/features/tool_calling.html) |
| PagedAttention | [Bài blog giới thiệu vLLM](https://blog.vllm.ai/2023/06/20/vllm.html) |
| Bộ nhớ GPU cho LLM | [Hugging Face: LLM inference optimization](https://huggingface.co/docs/transformers/llm_optims) |
| Model Qwen2.5 | [Qwen2.5-7B-Instruct trên Hugging Face](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct) |
| Lượng tử hóa (quantization) | [Hugging Face: Quantization overview](https://huggingface.co/docs/transformers/quantization/overview) |

---

## Phần lý thuyết

### 1. API hay tự host?

| | Dùng API (Gemini…) | Tự host (vLLM trên GPU) |
|---|---|---|
| Bắt đầu | Rất nhanh, chỉ cần key | Phải thuê GPU, cài đặt, vận hành |
| Chi phí | Trả theo token, rẻ khi ít khách | Trả theo giờ GPU **dù không có khách**, rẻ hơn khi rất nhiều khách |
| Dữ liệu | Gửi sang bên thứ ba | Nằm trên máy của bạn |
| Chất lượng | Model lớn, thường thông minh hơn | Model nhỏ hơn (7B–70B), cần kiểm tra kỹ |
| Kiểm soát | Phụ thuộc nhà cung cấp (đổi giá, ngừng model) | Tự quyết phiên bản, cấu hình |
| Độ trễ | Phụ thuộc mạng và tải của nhà cung cấp | Tự tối ưu được |

**Lời khuyên thực tế:** hầu hết dự án nên **bắt đầu bằng API**. Tự host khi có lý do rõ ràng: lượng khách lớn khiến tiền API vượt tiền GPU, yêu cầu dữ liệu không rời hệ thống, hoặc cần độ trễ ổn định. Bài này dạy kỹ năng tự host để bạn **có lựa chọn** và **hiểu tầng serving**, vốn là nền tảng cho Bài 17.

### 2. GPU cần bao nhiêu bộ nhớ?

LLM chạy trên GPU cần bộ nhớ (VRAM) cho hai thứ chính:

**a) Trọng số model (weights)**

```
Bộ nhớ trọng số ≈ số tham số × số byte mỗi tham số
```

| Model 7 tỷ tham số (7B) | Byte/tham số | Bộ nhớ |
|---|---|---|
| BF16/FP16 (bản gốc) | 2 | khoảng 15 GB |
| FP8 / INT8 | 1 | khoảng 8 GB |
| INT4 (AWQ, GPTQ) | 0,5 | khoảng 5 GB |

**b) KV cache**

Khi sinh token, model lưu lại "ghi nhớ" (key, value) của mọi token trước đó để không phải tính lại. Đó là **KV cache**. Nó tăng theo **độ dài ngữ cảnh × số request chạy đồng thời**. KV cache càng nhiều chỗ thì càng phục vụ được nhiều khách cùng lúc.

Ví dụ: GPU 24GB chạy Qwen2.5-7B bản BF16. Trọng số chiếm khoảng 15GB, còn khoảng 6–7GB cho KV cache, đủ cho vài chục hội thoại ngắn chạy song song. Muốn nhiều hơn thì dùng GPU lớn hơn hoặc model đã lượng tử hóa.

### 3. Prefill và decode

Mỗi request có hai giai đoạn:

1. **Prefill:** model đọc **toàn bộ prompt** (system prompt, lịch sử, kết quả tool) một lần. Giai đoạn này quyết định **thời gian đến token đầu tiên** (TTFT).
2. **Decode:** model sinh **từng token một**. Giai đoạn này quyết định **tốc độ ra chữ** (thời gian mỗi token).

Bài 17 sẽ đo cả hai.

### 4. Vì sao vLLM nhanh?

- **PagedAttention:** quản lý KV cache theo từng "trang" nhỏ, giống cách hệ điều hành quản lý RAM. Nhờ vậy không lãng phí bộ nhớ, nên chạy được nhiều request song song hơn.
- **Continuous batching:** GPU xử lý nhiều request **cùng lúc trong một lượt tính**. Request mới được chen vào ngay khi có chỗ, không phải đợi cả nhóm xong. Thông lượng (throughput) tăng nhiều lần so với xử lý từng request.
- **Server tương thích OpenAI:** cùng định dạng API với Gemini. Agent của bạn đổi sang chỉ bằng cách sửa `.env`.

### 5. Chọn model

Ta chọn **Qwen2.5-7B-Instruct** vì:

- Tiếng Việt khá tốt so với các model cùng cỡ.
- Hỗ trợ **tool calling**, và vLLM có sẵn bộ đọc (parser) cho định dạng của nó.
- Chạy được trên một GPU 24GB.
- Giấy phép Apache 2.0, dùng thương mại được.

Model mới ra liên tục. Khi bạn học bài này, có thể đã có model tốt hơn (các bản Qwen mới hơn, Llama, Gemma…). Cách làm vẫn giống hệt. Chỉ cần kiểm tra ba điều: giấy phép, tool calling, và **chạy bộ eval** để so sánh.

---

## Thực hành từng bước

> ⚠️ **Cảnh báo về chi phí:** GPU tính tiền **theo giờ kể cả khi bạn không dùng**. Đọc hết bài trước khi thuê, làm liền một mạch, và **nhớ tắt hoặc xóa máy** khi xong (Bước 9). Đặt nhắc nhở trên điện thoại nếu cần.

### Bước 1: Thuê máy GPU

Một số nơi cho thuê GPU theo giờ, phổ biến với người học: [RunPod](https://www.runpod.io/), [Vast.ai](https://vast.ai/), [Lambda](https://lambda.ai/), hoặc GPU của các nhà cung cấp cloud lớn (Google Cloud, AWS, Azure). Hướng dẫn dưới đây theo kiểu RunPod; các nơi khác tương tự.

1. Tạo tài khoản, nạp một khoản nhỏ (ví dụ 10 USD).
2. Tạo **Pod** (máy GPU) với:
   - **GPU:** loại có **24GB VRAM** trở lên (RTX 4090, RTX 3090, L4, A10, A5000…).
   - **Template:** một template có sẵn PyTorch và CUDA (ví dụ "RunPod PyTorch").
   - **Ổ đĩa (container/volume disk):** từ 50GB, vì model nặng khoảng 15GB.
   - **Expose HTTP ports:** thêm cổng `8000`.
3. Khởi động Pod. Khi sẵn sàng, mở **Web Terminal** hoặc SSH vào theo hướng dẫn của nhà cung cấp.

Kiểm tra GPU:

```bash
nvidia-smi
```

Bạn thấy tên GPU, bộ nhớ (ví dụ `24564MiB`) và phiên bản CUDA.

### Bước 2: Cài vLLM

```bash
pip install vllm
```

Cài khá lâu (vài phút). Kiểm tra:

```bash
vllm --version
```

> 💡 **Ghim phiên bản ở production:** vLLM ra bản mới rất nhanh, đôi khi thay đổi tham số. Khi chạy thật, hãy ghi lại phiên bản đang dùng (ví dụ `pip install vllm==<phiên bản>`), hoặc dùng image Docker chính thức `vllm/vllm-openai` có tag phiên bản cụ thể.

### Bước 3: Chạy server vLLM

Tạo một API key ngẫu nhiên để bảo vệ server:

```bash
export VLLM_API_KEY=$(openssl rand -hex 24)
```

```bash
echo $VLLM_API_KEY
```

**Ghi lại key này.** Rồi chạy server:

```bash
vllm serve Qwen/Qwen2.5-7B-Instruct \
  --host 0.0.0.0 \
  --port 8000 \
  --api-key "$VLLM_API_KEY" \
  --max-model-len 8192 \
  --gpu-memory-utilization 0.90 \
  --enable-auto-tool-choice \
  --tool-call-parser hermes
```

Giải thích từng tham số:

| Tham số | Ý nghĩa |
|---|---|
| `Qwen/Qwen2.5-7B-Instruct` | Tên model trên Hugging Face. vLLM tự tải về (khoảng 15GB, lần đầu mất vài phút) |
| `--host 0.0.0.0 --port 8000` | Nhận kết nối từ bên ngoài ở cổng 8000 |
| `--api-key` | **Bắt buộc có.** Thiếu nó thì ai biết địa chỉ cũng dùng được GPU của bạn |
| `--max-model-len 8192` | Độ dài ngữ cảnh tối đa (token). Model hỗ trợ dài hơn, nhưng giới hạn lại giúp dành bộ nhớ cho KV cache. Agent của ta thường chỉ dùng 2.000–4.000 token |
| `--gpu-memory-utilization 0.90` | Dùng 90% VRAM. Phần lớn chỗ còn lại sau trọng số được dành cho KV cache |
| `--enable-auto-tool-choice` | Cho phép model tự quyết định gọi tool |
| `--tool-call-parser hermes` | Cách đọc tool call từ chữ model sinh ra. Qwen2.5 dùng định dạng "hermes" |

Đợi đến khi log hiện dòng tương tự `Application startup complete` và `Uvicorn running on http://0.0.0.0:8000`. Trong log, tìm dòng nói về **KV cache** (ví dụ "GPU KV cache size: ... tokens"): đó là tổng số token có thể giữ trong bộ nhớ cùng lúc.

### Bước 4: Kiểm tra server

Mở **terminal thứ hai** trên máy GPU:

```bash
curl http://localhost:8000/v1/models -H "Authorization: Bearer $VLLM_API_KEY"
```

Thử chat:

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer $VLLM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "Qwen/Qwen2.5-7B-Instruct", "messages": [{"role": "user", "content": "Gợi ý một bữa sáng nhanh ở cửa hàng tiện lợi."}], "max_tokens": 200}'
```

Thử gọi mà **không có key**: phải bị từ chối `401`.

```bash
curl -i http://localhost:8000/v1/models
```

Theo dõi GPU trong lúc chạy:

```bash
watch -n 1 nvidia-smi
```

Bộ nhớ GPU gần như đầy (khoảng 90%). Đó là bình thường, vì vLLM đã giữ trước chỗ cho KV cache.

### Bước 5: Lấy địa chỉ truy cập từ bên ngoài

Mỗi nhà cung cấp có cách khác nhau. Với RunPod, cổng HTTP đã "expose" có địa chỉ dạng:

```
https://<pod-id>-8000.proxy.runpod.net
```

Xem địa chỉ chính xác trong trang quản lý Pod (nút **Connect**). Kiểm tra từ **máy bạn**:

```bash
curl https://<dia-chi-pod>/v1/models -H "Authorization: Bearer <VLLM_API_KEY>"
```

> ⚠️ **Cảnh báo:** chỉ dùng địa chỉ **HTTPS**. Nếu nhà cung cấp chỉ cho địa chỉ IP với cổng mở (HTTP thường), API key và nội dung hội thoại sẽ đi trên mạng không mã hóa. Khi đó, hãy dùng SSH tunnel (giống Bài 15) hoặc đặt Nginx có HTTPS phía trước.

### Bước 6: Chuyển agent sang model tự host

Trên **máy bạn**, sửa `.env`:

```bash
# LLM: chuyển sang vLLM tự host
LLM_BASE_URL=https://<dia-chi-pod>/v1
LLM_API_KEY=<VLLM_API_KEY>
LLM_MODEL=Qwen/Qwen2.5-7B-Instruct

# Embedding: vẫn dùng Gemini (vLLM đang chỉ chạy model chat)
EMBED_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
EMBED_API_KEY=<API key Gemini của bạn>
EMBED_MODEL=gemini-embedding-001
```

Nhớ lại Bài 07: ta đã tách sẵn cấu hình embedding. Đây là lúc nó phát huy tác dụng. Đổi LLM nhưng embedding giữ nguyên, nên **không phải xây lại chỉ mục RAG**.

Thử agent:

```bash
python scripts/thu_agent.py "Cửa hàng Quận 1 còn sữa tươi không, giá bao nhiêu?"
```

```bash
python scripts/thu_agent.py "Mua bánh mì bị mốc thì đổi được không?"
```

Agent gọi tool và trả lời, lần này bằng model chạy trên GPU **của bạn**. Không dòng code nào phải sửa.

### Bước 7: So sánh chất lượng bằng bộ eval

```bash
python eval/run_eval.py
```

So sánh điểm với lần chạy dùng Gemini ở Bài 10. Ghi lại vào bảng:

| Model | Điểm eval | Ghi chú (câu nào trượt, vì sao) |
|---|---|---|
| Gemini (flash) | ?/? | |
| Qwen2.5-7B-Instruct | ?/? | |

Model 7B thường **kém hơn** model API lớn ở các câu khó: tiếng Việt kém tự nhiên hơn, đôi khi quên gọi tool, dễ bị prompt injection hơn. Đây chính là đánh đổi cần cân nhắc. Có thể cải thiện bằng cách:

- Viết system prompt và mô tả tool **rõ ràng, cụ thể hơn**. Model nhỏ cần chỉ dẫn kỹ hơn.
- Thử model lớn hơn (14B, 32B) nếu GPU đủ bộ nhớ.
- Thử các model mới hơn.

### Bước 8 (tùy chọn): Thử model lượng tử hóa

Dừng server (`Ctrl + C`), chạy bản **AWQ 4-bit** (khoảng 5GB thay vì 15GB):

```bash
vllm serve Qwen/Qwen2.5-7B-Instruct-AWQ \
  --host 0.0.0.0 \
  --port 8000 \
  --api-key "$VLLM_API_KEY" \
  --max-model-len 8192 \
  --gpu-memory-utilization 0.90 \
  --enable-auto-tool-choice \
  --tool-call-parser hermes
```

Để ý trong log: **KV cache lớn hơn nhiều**, vì trọng số nhỏ hơn nên còn nhiều chỗ trống. Nhớ đổi `LLM_MODEL=Qwen/Qwen2.5-7B-Instruct-AWQ` trong `.env`, rồi chạy lại eval. Chất lượng giảm bao nhiêu? Bài 17 sẽ đo xem tốc độ và sức chứa tăng bao nhiêu.

### Bước 9: Tắt máy GPU

Khi xong phần thực hành (hoặc xong cả Bài 17 nếu bạn làm liền):

1. Vào trang quản lý → **Stop** Pod (dừng tính tiền GPU; ổ đĩa có thể vẫn tính phí nhỏ).
2. Không cần nữa thì **Terminate/Delete** để dừng mọi chi phí.
3. Trên máy bạn, đổi `.env` về cấu hình Gemini như cũ.

### Bước 10: Ghi lại và commit

Vì `.env` không được commit, hãy ghi lại cấu hình vLLM vào `.env.example` để lần sau không phải nhớ:

```bash
# --- Cấu hình khi dùng vLLM tự host (Bài 16) ---
# LLM_BASE_URL=https://<dia-chi-server-vllm>/v1
# LLM_API_KEY=<VLLM_API_KEY>
# LLM_MODEL=Qwen/Qwen2.5-7B-Instruct
# EMBED_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
# EMBED_API_KEY=<API key Gemini>
```

```bash
git add .env.example
```

```bash
git commit -m "Bài 16: ghi chú cấu hình vLLM tự host"
```

```bash
git push
```

---

## Đưa vLLM lên production (đọc thêm)

Khi tự host thật, cần lưu ý thêm:

- **Máy chủ GPU chạy liên tục** (thuê theo tháng rẻ hơn theo giờ), đặt cùng khu vực với VPS app để độ trễ mạng thấp.
- **Kết nối riêng tư** giữa app và vLLM (mạng nội bộ, VPN như WireGuard/Tailscale) thay vì đi qua Internet công khai.
- **Chạy vLLM bằng Docker** với image có tag phiên bản cố định, `restart: unless-stopped`, và volume lưu model (`~/.cache/huggingface`) để khởi động lại không phải tải lại 15GB.
- **Giám sát**: vLLM có sẵn `/metrics` cho Prometheus, gồm số request đang chạy, số request đang chờ, mức sử dụng KV cache. Tên metric có thể thay đổi giữa các phiên bản, nên hãy xem trực tiếp `/metrics` của bản bạn dùng.
- **Dự phòng (fallback)**: nếu vLLM sập, tạm chuyển sang API Gemini (bài tập ở Bài 18).

## Kiểm tra kết quả

- [ ] `nvidia-smi` thấy GPU.
- [ ] vLLM chạy, `/v1/models` trả về model khi có key, và từ chối khi không có key.
- [ ] Agent chạy với model tự host chỉ bằng cách đổi `.env`.
- [ ] Có bảng so sánh điểm eval giữa Gemini và Qwen.
- [ ] **Đã tắt hoặc xóa máy GPU.**

## Lỗi thường gặp

| Lỗi | Nguyên nhân | Cách sửa |
|---|---|---|
| `CUDA out of memory` khi khởi động | GPU không đủ bộ nhớ cho model và KV cache | Giảm `--max-model-len` (ví dụ 4096), dùng bản AWQ, hoặc thuê GPU lớn hơn |
| `ValueError: ... max_model_len ... larger than ... KV cache` | KV cache không đủ chứa dù chỉ một request dài tối đa | Giảm `--max-model-len` |
| Tải model rất chậm hoặc lỗi | Mạng của máy GPU chậm, hoặc ổ đĩa đầy | Kiểm tra `df -h`; chọn máy có ổ đĩa lớn hơn |
| Agent không gọi tool, hoặc in ra chữ `<tool_call>` thô | Thiếu `--enable-auto-tool-choice` hoặc sai `--tool-call-parser` | Kiểm tra lại lệnh `vllm serve`; xem tài liệu tool calling của vLLM cho model bạn dùng |
| `401 Unauthorized` từ agent | `LLM_API_KEY` trong `.env` không khớp `--api-key` | Kiểm tra lại key |
| `404 ... model does not exist` | `LLM_MODEL` khác tên model vLLM đang chạy | Lấy tên chính xác từ `/v1/models` |

## Bài tập

1. Tính toán: với giá thuê GPU bạn đã trả (USD/giờ), chạy liên tục 1 tháng tốn bao nhiêu? So với chi phí Gemini ở bài tập 4 của Bài 03, cần bao nhiêu câu hỏi mỗi ngày thì tự host mới rẻ hơn?
2. Thử một model khác hỗ trợ tool calling (xem danh sách trong tài liệu tool calling của vLLM). Chạy eval và so sánh.
3. Đọc `curl http://localhost:8000/metrics` trên máy GPU trong lúc agent đang chạy. Tìm metric cho số request đang chạy và mức sử dụng KV cache.
4. (Nâng cao) Chạy vLLM bằng Docker image `vllm/vllm-openai` thay vì `pip install`. Viết lệnh `docker run` tương đương với lệnh `vllm serve` ở Bước 3.

## Checklist hoàn thành

- [ ] Hiểu đánh đổi API và tự host
- [ ] Ước lượng được bộ nhớ GPU: trọng số + KV cache
- [ ] Hiểu prefill/decode, PagedAttention, continuous batching
- [ ] Chạy được vLLM có API key và tool calling
- [ ] Agent chạy với model tự host, có so sánh eval
- [ ] Đã tắt máy GPU

➡️ Tiếp theo: [Bài 17: Benchmark serving](bai-17-benchmark-serving.md)
