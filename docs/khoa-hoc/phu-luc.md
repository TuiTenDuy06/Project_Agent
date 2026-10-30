# Phụ lục: thuật ngữ, lỗi thường gặp, lệnh hay dùng, tài liệu học thêm

## A. Bảng thuật ngữ

| Thuật ngữ | Giải thích ngắn | Bài |
|---|---|---|
| Agent | Chương trình dùng LLM để tự quyết định gọi công cụ nào, rồi trả lời dựa trên kết quả | 06 |
| API | "Cửa" để chương trình này gọi chương trình khác | 02 |
| API key | Chuỗi bí mật để xác thực khi gọi API | 03, 12 |
| async/await | Cách viết code chạy nhiều việc chờ mạng cùng lúc | 02, 17 |
| AWQ / GPTQ | Các phương pháp lượng tử hóa model xuống 4-bit | 16 |
| Batching (continuous) | GPU xử lý nhiều request trong một lượt tính; request mới chen vào ngay khi có chỗ | 16 |
| CI/CD | Tự động kiểm tra (CI) và tự động triển khai (CD) code | 14 |
| Chunk / Chunking | Đoạn văn bản nhỏ / việc cắt tài liệu thành đoạn cho RAG | 07 |
| Concurrency | Số request được xử lý đồng thời | 17 |
| Connection pool | "Hồ" giữ sẵn kết nối database để dùng lại | 05 |
| Container | Phiên bản đang chạy của một image Docker | 11 |
| Context window | Số token tối đa model "nhìn thấy" trong một lần gọi | 03 |
| CORS | Cơ chế cho phép trang web ở domain khác gọi API | 12 |
| Cosine distance | Khoảng cách giữa hai vector theo góc; càng nhỏ càng giống nghĩa | 07 |
| Cron | Công cụ chạy lệnh theo lịch trên Linux | 15 |
| Decode | Giai đoạn model sinh từng token đầu ra | 16 |
| Dependency (FastAPI) | Hàm chạy trước endpoint, ví dụ kiểm tra API key | 12 |
| DNS / bản ghi A | Hệ thống đổi tên miền thành địa chỉ IP / bản ghi trỏ tên miền về IP | 15 |
| Docker Compose | Công cụ chạy nhiều container từ một file YAML | 05, 11 |
| Embedding | Vector số biểu diễn ý nghĩa của đoạn văn | 07 |
| Endpoint | Một đường dẫn API, ví dụ `POST /chat` | 04 |
| Eval | Bộ tình huống mẫu để đo chất lượng agent với LLM thật | 10 |
| Firewall (UFW) | Tường lửa chặn các cổng mạng không cần thiết | 15 |
| Guardrails | Các lớp rào chắn giữ agent hoạt động an toàn, đúng phạm vi | 08 |
| Hallucination | LLM tự tin "bịa" thông tin không có thật | 03 |
| Handoff | Chuyển cuộc trò chuyện cho nhân viên | 08 |
| Healthcheck | Kiểm tra định kỳ xem dịch vụ còn sống không | 04, 11 |
| HTTPS / TLS | HTTP có mã hóa | 15 |
| Image (Docker) | Bản đóng gói chỉ đọc của ứng dụng | 11 |
| Index (database) | Cấu trúc giúp tìm dữ liệu nhanh | 08 |
| KV cache | Bộ nhớ GPU lưu "ghi nhớ" của các token trước đó khi sinh văn bản | 16 |
| Latency | Độ trễ, thời gian từ lúc gửi đến lúc nhận đủ kết quả | 13, 17 |
| Lifespan | Code chạy khi app FastAPI khởi động và tắt | 05 |
| LLM | Large Language Model, mô hình ngôn ngữ lớn | 03 |
| Metric | Con số đo theo thời gian (số request, độ trễ…) | 13 |
| Migration | Thay đổi cấu trúc database đang có dữ liệu | 07 |
| Monkeypatch | Thay tạm một hàm trong lúc chạy test | 10 |
| p50 / p95 / p99 | Phân vị: 50% / 95% / 99% giá trị nhỏ hơn con số này | 13, 17 |
| PagedAttention | Kỹ thuật quản lý KV cache theo trang của vLLM | 16 |
| pgvector | Extension PostgreSQL lưu và tìm kiếm vector | 07 |
| PII | Thông tin định danh cá nhân (số điện thoại, tên, địa chỉ…) | 08, 13 |
| Prefill | Giai đoạn model đọc toàn bộ prompt | 16 |
| Prompt injection | Kỹ thuật dùng nội dung nhập vào để ghi đè chỉ dẫn của LLM | 08 |
| PromQL | Ngôn ngữ truy vấn của Prometheus | 13 |
| Pull Request (PR) | Đề nghị gộp một nhánh vào nhánh chính | 14 |
| Quantization | Lượng tử hóa: giảm số bit lưu trọng số để model nhỏ và nhanh hơn | 16 |
| RAG | Tìm đoạn tài liệu liên quan rồi đưa cho LLM đọc để trả lời | 07 |
| Rate limit | Giới hạn số request trong một khoảng thời gian | 15 |
| Reverse proxy | Máy chủ đứng trước app, nhận request rồi chuyển vào (Nginx) | 15 |
| Rollback / Revert | Quay lại phiên bản trước | 15 |
| Session | Một cuộc hội thoại, phân biệt bằng `session_id` | 08 |
| SLO | Mục tiêu chất lượng dịch vụ bằng con số | 17 |
| SQL injection | Tấn công chèn câu lệnh SQL qua dữ liệu đầu vào | 05 |
| SSE (Server-Sent Events) | Định dạng server gửi dữ liệu từng phần về client (streaming) | 17 |
| SSH / SSH key | Giao thức điều khiển máy chủ từ xa / cặp khóa để đăng nhập | 01, 15 |
| Stateless | Ứng dụng không giữ dữ liệu trong bộ nhớ giữa các request | 18 |
| System prompt | Chỉ dẫn cho LLM về vai trò và quy tắc | 03, 06 |
| Temperature | Tham số điều chỉnh độ ngẫu nhiên khi LLM sinh văn bản | 03 |
| Throughput | Thông lượng: số request hoặc token xử lý mỗi giây | 17 |
| Token | Mẩu văn bản nhỏ mà LLM đọc và sinh ra | 03 |
| Tool calling | LLM yêu cầu chương trình chạy một hàm và trả kết quả | 06 |
| TPOT / ITL | Thời gian sinh mỗi token sau token đầu tiên | 17 |
| TTFT | Thời gian đến token đầu tiên | 17 |
| Validation | Kiểm tra dữ liệu đầu vào có hợp lệ không | 04 |
| Virtualenv (venv) | Môi trường Python riêng cho từng dự án | 01 |
| Volume (Docker) | Ổ lưu dữ liệu bền vững cho container | 05, 11 |
| VPS | Máy chủ ảo thuê trên Internet | 15 |
| vLLM | Phần mềm phục vụ (serving) LLM hiệu năng cao | 16 |
| XSS | Tấn công chèn mã JavaScript độc hại vào trang web | 09 |

---

## B. Cách gỡ lỗi chung

Khi gặp lỗi, làm theo thứ tự:

1. **Đọc dòng cuối của thông báo lỗi.** Với Python, dòng cuối của `Traceback` cho biết loại lỗi và nguyên nhân. Các dòng phía trên cho biết lỗi xảy ra ở file nào, dòng nào.
2. **Xác định lỗi ở tầng nào:** trình duyệt (F12 → Console/Network)? Nginx (`sudo tail /var/log/nginx/error.log`)? App (`docker compose logs app`)? Database (`docker compose logs db`)? LLM (log app có `APIError`, `RateLimitError`…)?
3. **Tìm trong mục "Lỗi thường gặp"** của bài đang học và bảng bên dưới.
4. **Thu hẹp phạm vi:** gọi thẳng từng tầng. `curl` vào app bỏ qua Nginx (`http://127.0.0.1:8080`); dùng `psql` hỏi thẳng database; gọi thẳng LLM bằng `scripts/hello_llm.py`.
5. **Tìm kiếm:** copy **nguyên văn** dòng lỗi (bỏ phần riêng của bạn như đường dẫn, mật khẩu) lên Google hoặc hỏi AI, kèm ngữ cảnh: bạn đang làm gì, đã thử gì.
6. **Quay về bản chạy được:** `git diff` xem đã sửa gì so với commit gần nhất; `git stash` cất thay đổi tạm để thử lại bản cũ.

---

## C. Lỗi thường gặp (tổng hợp)

| Triệu chứng | Nguyên nhân thường gặp | Xem |
|---|---|---|
| `ModuleNotFoundError: No module named 'agent'` | Chưa kích hoạt venv, chưa `pip install -e ".[dev]"` | Bài 03 |
| `ValidationError ... Field required` khi khởi động | Thiếu biến trong `.env`, hoặc chạy lệnh sai thư mục | Bài 03 |
| `401` / `API key not valid` | Sai API key LLM | Bài 03 |
| `429 Too Many Requests` từ LLM | Vượt hạn mức gói miễn phí | Bài 03 |
| `404 ... model` | Tên model không tồn tại hoặc đã ngừng | Bài 03 |
| `Address already in use` | Cổng đang bị chương trình khác dùng | Bài 04 |
| `422 Unprocessable Entity` | Dữ liệu gửi lên sai định dạng | Bài 04 |
| `PoolTimeout` / `connection refused` | Database chưa chạy, sai `DATABASE_URL` | Bài 05, 11 |
| Sửa file `.sql` mà không có tác dụng | `initdb.d` chỉ chạy lần đầu | Bài 05, 07 |
| `relation "..." does not exist` | Chưa chạy file SQL tạo bảng | Bài 07, 08 |
| Agent bịa giá, không gọi tool | Mô tả tool hoặc system prompt chưa rõ | Bài 06 |
| Lỗi về `tool_call_id` | Sai thứ tự tin nhắn trong vòng lặp agent | Bài 06 |
| `type "vector" does not exist` | Chưa bật pgvector, sai image database | Bài 07 |
| `/chat` trả `405` | `app.mount("/")` đặt trước các route | Bài 09 |
| Test bị treo, `PoolTimeout` | Dùng `with TestClient(app)` | Bài 10 |
| Container app `unhealthy` | `/health` lỗi, thường do database | Bài 11 |
| Trình duyệt báo lỗi CORS | Gọi API từ domain chưa được cho phép | Bài 12 |
| Grafana không kết nối Prometheus | Dùng `localhost` thay vì `prometheus` | Bài 13 |
| CI đỏ dù máy bạn chạy được | Quên commit file, test phụ thuộc `.env` | Bài 14 |
| `502 Bad Gateway` | Nginx chạy nhưng app không chạy | Bài 15 |
| Bị khóa ngoài máy chủ SSH | Tắt đăng nhập mật khẩu khi key chưa hoạt động | Bài 15 |
| `CUDA out of memory` | GPU không đủ bộ nhớ | Bài 16 |

---

## D. Lệnh hay dùng

### Python và dự án

```bash
source .venv/bin/activate
```

```bash
pip install -e ".[dev]"
```

```bash
uvicorn agent.app:app --reload --port 8080
```

```bash
pytest
```

```bash
ruff check . --fix
```

```bash
python eval/run_eval.py
```

### Git

```bash
git status
```

```bash
git switch -c <ten-nhanh>
```

```bash
git add <file> && git commit -m "<mô tả>"
```

```bash
git push -u origin <ten-nhanh>
```

```bash
git log --oneline -10
```

```bash
git diff
```

```bash
git revert <ma-commit>
```

### Docker

```bash
docker compose up -d --build
```

```bash
docker compose ps
```

```bash
docker compose logs -f --tail 100 app
```

```bash
docker compose exec db psql -U agent -d agent
```

```bash
docker compose run --rm app python scripts/build_index.py
```

```bash
docker compose restart app
```

```bash
docker compose down
```

### Máy chủ

```bash
ssh deploy@<IP>
```

```bash
sudo ufw status
```

```bash
sudo nginx -t && sudo systemctl reload nginx
```

```bash
sudo tail -f /var/log/nginx/error.log
```

```bash
df -h
```

```bash
free -h
```

```bash
ssh -L 3000:127.0.0.1:3000 deploy@<IP>
```

---

## E. Tài liệu học thêm

### Nền tảng

- [Python Tutorial chính thức](https://docs.python.org/3/tutorial/)
- [The Missing Semester of Your CS Education (MIT)](https://missing.csail.mit.edu/): terminal, Git, gỡ lỗi
- [Pro Git, tiếng Việt](https://git-scm.com/book/vi/v2)
- [MDN Web Docs](https://developer.mozilla.org/): HTML, CSS, JavaScript, HTTP

### Backend và database

- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)
- [PostgreSQL Tutorial](https://www.postgresqltutorial.com/)
- [Use The Index, Luke](https://use-the-index-luke.com/): index database
- [The Twelve-Factor App](https://12factor.net/)

### LLM và agent

- [Anthropic: Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)
- [Hamel Husain: Your AI Product Needs Evals](https://hamel.dev/blog/posts/evals/)
- [OWASP Top 10 for LLM Applications](https://genai.owasp.org/llm-top-10/)
- [Prompt Engineering Guide](https://www.promptingguide.ai/)
- [Andrej Karpathy: Intro to Large Language Models (video)](https://www.youtube.com/watch?v=zjkBMFhNj_g)

### Hạ tầng và vận hành

- [Docker Docs: Get started](https://docs.docker.com/get-started/)
- [DigitalOcean Community Tutorials](https://www.digitalocean.com/community/tutorials): rất nhiều bài hướng dẫn máy chủ Linux
- [Google SRE Books (miễn phí)](https://sre.google/books/)
- [Prometheus Docs](https://prometheus.io/docs/)

### Serving

- [vLLM Docs](https://docs.vllm.ai/)
- [Hugging Face: LLM inference optimization](https://huggingface.co/docs/transformers/llm_optims)
- [NVIDIA: LLM Inference Benchmarking](https://developer.nvidia.com/blog/llm-benchmarking-fundamental-concepts/)

⬅️ Quay về [Mục lục](00-muc-luc.md)
