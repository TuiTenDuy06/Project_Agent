# Project Agent — Agent chăm sóc khách hàng cho chuỗi cửa hàng tiện lợi

Agent AI trả lời và xử lý yêu cầu của khách hàng cho chuỗi cửa hàng tiện lợi (hỏi giá, tồn kho, khuyến mãi, giờ mở cửa, đổi trả, khiếu nại), kèm bộ **benchmark serving** để đo hiệu năng mô hình khi phục vụ thực tế.

> Trạng thái: **đang khởi tạo**. Cấu trúc thư mục và lệnh bên dưới là thiết kế dự kiến, sẽ cập nhật khi code được thêm vào.

## Mục tiêu

### Agent chăm sóc khách hàng
- Trả lời câu hỏi thường gặp bằng tiếng Việt tự nhiên, dựa trên dữ liệu thật của cửa hàng (RAG trên FAQ, chính sách, danh mục sản phẩm).
- Gọi công cụ (tool calling) để tra cứu:
  - giá và tồn kho sản phẩm theo cửa hàng,
  - chương trình khuyến mãi đang chạy,
  - cửa hàng gần nhất và giờ mở cửa,
  - trạng thái đơn hàng / điểm thành viên.
- Tiếp nhận khiếu nại, đổi trả; chuyển cho nhân viên khi vượt quá thẩm quyền hoặc khách yêu cầu.
- Giữ ngữ cảnh hội thoại nhiều lượt; không bịa thông tin giá, tồn kho, chính sách.

### Benchmark serving
- Đo hiệu năng phục vụ mô hình dưới tải giống thực tế:
  - **TTFT** (time to first token), **TPOT / ITL** (thời gian mỗi token),
  - **latency** end-to-end (p50 / p90 / p99),
  - **throughput** (request/s, token/s),
  - tỉ lệ lỗi / timeout theo mức đồng thời (concurrency).
- So sánh các cấu hình: backend serving, mô hình, lượng tử hóa, batch size, độ dài ngữ cảnh.
- Dùng prompt lấy từ hội thoại CSKH thật (đã ẩn danh) để kết quả sát với tải sản xuất.
- Đánh giá chất lượng trả lời song song với tốc độ (độ chính xác tool call, tỉ lệ trả lời đúng).

## Cấu trúc thư mục dự kiến

```
Project_Agent/
├── README.md
├── pyproject.toml            # Dependency và cấu hình package
├── .env.example              # Biến môi trường mẫu (API key, URL model server, DB)
├── configs/
│   ├── agent.yaml            # Prompt hệ thống, model, tham số sinh
│   └── benchmark/            # Kịch bản benchmark (concurrency, số request, dataset)
├── data/
│   ├── knowledge/            # FAQ, chính sách đổi trả, giờ mở cửa... cho RAG
│   ├── catalog/              # Danh mục sản phẩm, giá, tồn kho mẫu
│   └── conversations/        # Hội thoại mẫu (đã ẩn danh) dùng cho eval/benchmark
├── src/
│   └── agent/
│       ├── app.py            # API server (FastAPI): /chat, /health
│       ├── core/             # Vòng lặp agent, quản lý hội thoại, prompt
│       ├── tools/            # Tool: tra giá, tồn kho, khuyến mãi, cửa hàng, đơn hàng
│       ├── rag/              # Embedding, index, truy xuất tài liệu
│       └── llm/              # Client gọi model server (OpenAI-compatible)
├── benchmark/
│   ├── run_benchmark.py      # Bắn tải tới endpoint, ghi số liệu
│   ├── datasets/             # Tập prompt benchmark
│   ├── analyze.py            # Tổng hợp p50/p90/p99, vẽ biểu đồ
│   └── results/              # Kết quả theo từng lần chạy (không commit file lớn)
├── eval/                     # Đánh giá chất lượng trả lời và độ chính xác tool call
├── scripts/                  # Script tiện ích: nạp dữ liệu, build index, khởi động server
├── tests/                    # Unit test và integration test
└── docker/                   # Dockerfile, docker-compose cho agent + model server
```

## Cách chạy (dự kiến)

### 1. Yêu cầu
- Python 3.11+
- GPU NVIDIA (nếu tự host model) hoặc API key của nhà cung cấp LLM
- Docker (tùy chọn)

### 2. Cài đặt

```bash
git clone https://github.com/tuitenduy06/project_agent.git
```

```bash
cd project_agent
```

```bash
python -m venv .venv && source .venv/bin/activate
```

```bash
pip install -e ".[dev]"
```

```bash
cp .env.example .env
```

Sửa `.env`: điền `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL` và thông tin kết nối dữ liệu.

### 3. Khởi động model server (nếu tự host)

Ví dụ với vLLM (endpoint tương thích OpenAI):

```bash
vllm serve <model-name> --port 8000
```

### 4. Nạp dữ liệu và build index RAG

```bash
python scripts/build_index.py --source data/knowledge
```

### 5. Chạy agent

```bash
uvicorn agent.app:app --host 0.0.0.0 --port 8080
```

Thử gọi:

```bash
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "demo", "message": "Cửa hàng gần quận 1 còn sữa tươi không?"}'
```

### 6. Chạy benchmark serving

```bash
python benchmark/run_benchmark.py --config configs/benchmark/default.yaml
```

```bash
python benchmark/analyze.py --input benchmark/results/<run-id>
```

Kết quả gồm bảng TTFT, TPOT, latency p50/p90/p99, throughput theo từng mức concurrency.

### 7. Chạy test và eval

```bash
pytest
```

```bash
python eval/run_eval.py --dataset data/conversations
```

## Lộ trình

- [ ] Khung agent + API `/chat`
- [ ] Tool tra giá, tồn kho, khuyến mãi, cửa hàng
- [ ] RAG trên FAQ và chính sách
- [ ] Chuyển tiếp sang nhân viên (human handoff)
- [ ] Bộ benchmark serving + báo cáo
- [ ] Bộ eval chất lượng trả lời
- [ ] Docker hóa và hướng dẫn triển khai
