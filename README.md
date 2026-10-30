# Project Agent — Agent chăm sóc khách hàng cho chuỗi cửa hàng tiện lợi

Agent AI trả lời và xử lý yêu cầu của khách hàng cho chuỗi cửa hàng tiện lợi (hỏi giá, tồn kho, khuyến mãi, giờ mở cửa, đổi trả, khiếu nại), kèm bộ **benchmark serving** để đo hiệu năng mô hình khi phục vụ thực tế.

> 📚 **Người mới bắt đầu:** làm theo [khóa học từng bước](docs/khoa-hoc/00-muc-luc.md). Khóa học dẫn bạn xây toàn bộ dự án từ đầu, đưa lên production và benchmark.

## Mục tiêu

### Agent chăm sóc khách hàng
- Trả lời câu hỏi thường gặp bằng tiếng Việt tự nhiên, dựa trên dữ liệu thật của cửa hàng (RAG trên FAQ, chính sách).
- Gọi công cụ (tool calling) để tra cứu:
  - giá và tồn kho sản phẩm theo cửa hàng,
  - chương trình khuyến mãi đang chạy,
  - cửa hàng theo khu vực và giờ mở cửa,
  - chính sách đổi trả, thẻ thành viên, thanh toán, giao hàng.
- Tiếp nhận khiếu nại; chuyển cho nhân viên khi vượt quá thẩm quyền hoặc khách yêu cầu.
- Giữ ngữ cảnh hội thoại nhiều lượt; không bịa thông tin giá, tồn kho, chính sách.

### Benchmark serving
- Đo hiệu năng phục vụ mô hình dưới tải giống thực tế:
  - **TTFT** (time to first token), **TPOT** (thời gian mỗi token),
  - **latency** end-to-end (p50 / p90 / p99),
  - **throughput** (request/s, token/s),
  - tỉ lệ lỗi theo mức đồng thời (concurrency).
- So sánh các cấu hình: mô hình, lượng tử hóa, độ dài ngữ cảnh, giới hạn batch.
- Dùng prompt lấy từ hội thoại CSKH để kết quả sát với tải sản xuất.
- Đánh giá chất lượng trả lời song song với tốc độ (bộ eval).

## Công nghệ

Python 3.12 · FastAPI · PostgreSQL + pgvector · thư viện `openai` (Gemini API hoặc vLLM tự host qua API tương thích OpenAI) · Docker Compose · Prometheus + Grafana · Nginx · GitHub Actions.

## Cấu trúc thư mục

```
Project_Agent/
├── README.md
├── pyproject.toml              # Khai báo dự án và thư viện
├── .env.example                # Biến môi trường mẫu
├── compose.yaml                # db, app, prometheus, grafana
├── Dockerfile
├── .github/workflows/ci.yml    # CI: ruff, pytest, docker build; CD: deploy qua SSH
├── db/init/                    # SQL tạo bảng và dữ liệu mẫu
├── data/knowledge/             # Tài liệu chính sách, FAQ cho RAG
├── src/agent/
│   ├── app.py                  # API FastAPI: /chat, /health, /admin/handoffs, /metrics
│   ├── agent.py                # Vòng lặp agent (tool calling)
│   ├── tools.py                # Tool: sản phẩm, khuyến mãi, cửa hàng, chính sách, chuyển nhân viên
│   ├── rag.py                  # Tìm kiếm tài liệu bằng pgvector
│   ├── memory.py               # Lịch sử hội thoại
│   ├── llm.py                  # Client LLM và embedding
│   ├── config.py, db.py, prompts.py, logging_config.py
│   └── static/index.html       # Giao diện chat
├── scripts/build_index.py      # Xây chỉ mục RAG
├── tests/                      # Unit test (LLM giả, không cần database)
├── eval/                       # Bộ eval chất lượng với LLM thật
├── monitoring/prometheus.yml
├── deploy/                     # Cấu hình Nginx, script sao lưu
├── benchmark/                  # run_benchmark.py, analyze.py, datasets/
└── docs/khoa-hoc/              # Khóa học từng bước
```

## Cách chạy

### 1. Yêu cầu
- Python 3.11+, Docker
- API key Gemini (miễn phí tại [Google AI Studio](https://aistudio.google.com/)), hoặc server vLLM tự host

### 2. Cài đặt

```bash
git clone git@github.com:<tai-khoan>/project_agent.git && cd project_agent
```

```bash
python3 -m venv .venv && source .venv/bin/activate
```

```bash
pip install -e ".[dev]"
```

```bash
cp .env.example .env
```

Sửa `.env`: điền `LLM_API_KEY` và `ADMIN_API_KEY`.

### 3. Chạy toàn bộ hệ thống

```bash
docker compose up -d --build
```

```bash
docker compose run --rm app python scripts/build_index.py
```

Mở http://localhost:8080 để chat. Grafana ở http://localhost:3000, Prometheus ở http://localhost:9090.

### 4. Test và eval

```bash
pytest
```

```bash
ruff check .
```

```bash
python eval/run_eval.py
```

### 5. Benchmark serving

Với server vLLM (xem [Bài 16](docs/khoa-hoc/bai-16-self-host-vllm.md)):

```bash
export BENCH_API_KEY=<VLLM_API_KEY>
```

```bash
python benchmark/run_benchmark.py --url https://<server-vllm>/v1 --concurrency 1,4,8,16,32 --num-requests 100
```

```bash
python benchmark/analyze.py --input benchmark/results/<run-id>
```

Kết quả gồm bảng TTFT, TPOT, latency p50/p90/p99, throughput theo từng mức concurrency. Chi tiết ở [Bài 17](docs/khoa-hoc/bai-17-benchmark-serving.md).

## Lộ trình

- [ ] Khung agent + API `/chat` ([Bài 03–06](docs/khoa-hoc/bai-06-tool-calling.md))
- [ ] Tool tra giá, tồn kho, khuyến mãi, cửa hàng
- [ ] RAG trên FAQ và chính sách ([Bài 07](docs/khoa-hoc/bai-07-rag.md))
- [ ] Bộ nhớ hội thoại, chuyển nhân viên ([Bài 08](docs/khoa-hoc/bai-08-bo-nho-handoff-guardrails.md))
- [ ] Giao diện chat ([Bài 09](docs/khoa-hoc/bai-09-giao-dien-chat.md))
- [ ] Test và eval ([Bài 10](docs/khoa-hoc/bai-10-test-va-eval.md))
- [ ] Docker, bảo mật, giám sát, CI/CD ([Bài 11–14](docs/khoa-hoc/bai-11-docker.md))
- [ ] Deploy VPS ([Bài 15](docs/khoa-hoc/bai-15-deploy-vps.md))
- [ ] Self-host vLLM và benchmark serving ([Bài 16–17](docs/khoa-hoc/bai-16-self-host-vllm.md))
