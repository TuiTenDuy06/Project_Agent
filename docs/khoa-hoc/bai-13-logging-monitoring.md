# Bài 13: Logging và giám sát

## Mục tiêu

Sau bài này bạn sẽ:

- Hiểu **ba trụ cột quan sát hệ thống** (observability): log, metric, trace.
- Ghi **log dạng JSON** có cấu trúc, và **che số điện thoại** khách trong log.
- Đo **metric**: số request, độ trễ, số token LLM, số lần gọi tool.
- Chạy **Prometheus** thu thập metric và **Grafana** vẽ dashboard.
- Biết nên theo dõi chỉ số nào và khi nào cần cảnh báo.

## Kiến thức cần học

| Chủ đề | Tài liệu |
|---|---|
| Python logging | [Logging HOWTO](https://docs.python.org/3/howto/logging.html) |
| Prometheus | [Prometheus: Overview](https://prometheus.io/docs/introduction/overview/) |
| Các loại metric | [Prometheus: Metric types](https://prometheus.io/docs/concepts/metric_types/) |
| PromQL | [Prometheus: Querying basics](https://prometheus.io/docs/prometheus/latest/querying/basics/) |
| Grafana | [Grafana: Getting started](https://grafana.com/docs/grafana/latest/getting-started/) |
| Instrumentator | [prometheus-fastapi-instrumentator](https://github.com/trallnag/prometheus-fastapi-instrumentator) |
| Tư duy giám sát | [Google SRE Book: Monitoring Distributed Systems](https://sre.google/sre-book/monitoring-distributed-systems/), đọc phần "The Four Golden Signals" |

---

## Phần lý thuyết

### 1. Vì sao cần quan sát hệ thống?

Ở production, bạn **không ngồi nhìn terminal** được. Khi khách phàn nàn "bot trả lời chậm" hay "bot không trả lời", bạn cần trả lời được: chậm từ khi nào? Chậm ở đâu, LLM hay database? Bao nhiêu khách bị ảnh hưởng?

### 2. Ba trụ cột

| | Log | Metric | Trace |
|---|---|---|---|
| Là gì | Dòng ghi chép từng sự kiện | Con số đo theo thời gian | Hành trình của **một** request qua các bước |
| Ví dụ | "session=abc gọi tool tim_san_pham" | "95% request /chat xong trong 3 giây" | "/chat 3,2s = LLM 1,1s + tool 0,1s + LLM 2,0s" |
| Dùng để | Điều tra **chi tiết** một sự cố | Thấy **xu hướng**, đặt **cảnh báo** | Tìm **chỗ chậm** |
| Trong dự án | Log JSON | Prometheus + Grafana | Giới thiệu ở cuối bài |

### 3. Log có cấu trúc (JSON)

Log dạng chữ tự do (`print("lỗi rồi")`) khó tìm kiếm khi có hàng triệu dòng. Log **dạng JSON**, mỗi dòng một object có các trường cố định (`time`, `level`, `msg`), thì máy đọc được: lọc theo `level`, tìm theo `session`, đếm lỗi…

**Mức độ log (level):**

| Level | Khi nào dùng |
|---|---|
| `DEBUG` | Chi tiết để gỡ lỗi, thường tắt ở production |
| `INFO` | Sự kiện bình thường: request xong, agent gọi tool |
| `WARNING` | Bất thường nhưng vẫn chạy được |
| `ERROR` | Lỗi, một request thất bại |

**Không ghi vào log:** API key, mật khẩu, số điện thoại, số thẻ… Log thường được nhiều người xem và lưu lâu, nên rất dễ lộ.

### 4. Bốn chỉ số vàng (Four Golden Signals)

Google đề xuất 4 chỉ số quan trọng nhất cho mọi dịch vụ:

1. **Latency (độ trễ):** mất bao lâu để trả lời.
2. **Traffic (lưu lượng):** bao nhiêu request mỗi giây.
3. **Errors (lỗi):** tỉ lệ request thất bại.
4. **Saturation (độ bão hòa):** hệ thống "đầy" đến đâu (CPU, RAM, kết nối database).

Với agent AI, thêm: **số token** (liên quan trực tiếp đến **tiền**) và **tool nào được gọi nhiều**.

### 5. Prometheus và Grafana hoạt động thế nào?

```
 App ── /metrics (văn bản các con số) ◀── Prometheus "kéo" (scrape) mỗi 15 giây, lưu theo thời gian
                                                │
                                                ▼
                                          Grafana truy vấn bằng PromQL, vẽ biểu đồ
```

**Các loại metric:**

- **Counter**: chỉ tăng. Ví dụ tổng số request, tổng số token.
- **Histogram**: phân bố giá trị. Ví dụ độ trễ, để tính được "95% request nhanh hơn X giây" (gọi là **p95**).
- **Gauge**: tăng giảm tùy ý. Ví dụ số kết nối đang mở.

🧠 **Hiểu sâu, vì sao dùng p95, p99 thay vì trung bình?** Giả sử 99 request mất 1 giây và 1 request mất 100 giây: trung bình là 2 giây, trông "ổn". Nhưng thực tế có khách chờ gần 2 phút. **p95** = 95% request nhanh hơn giá trị này; **p99** cho thấy trải nghiệm của nhóm khách xui nhất. Bài 17 sẽ dùng rất nhiều.

---

## Thực hành từng bước

> Chuẩn bị: `cd ~/project_agent && source .venv/bin/activate`.

### Bước 1: Log dạng JSON và che số điện thoại

Tạo file `src/agent/logging_config.py`:

```python
import json
import logging
import re

PHONE_RE = re.compile(r"(?:\+84|0)\d{9}")


def mask_pii(text: str) -> str:
    """Che số điện thoại: 0912345678 -> 091****678."""
    return PHONE_RE.sub(lambda m: m.group()[:3] + "****" + m.group()[-3:], text)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        data = {
            "time": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "msg": mask_pii(record.getMessage()),
        }
        if record.exc_info:
            data["exc"] = self.formatException(record.exc_info)
        return json.dumps(data, ensure_ascii=False)


def setup_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)
```

Giải thích:

- **`PHONE_RE`**: regex tìm số điện thoại Việt Nam, bắt đầu bằng `0` hoặc `+84`, theo sau là 9 chữ số. `(?:...)` là nhóm không lưu kết quả.
- **`mask_pii`**: thay mỗi số tìm được bằng 3 ký tự đầu + `****` + 3 ký tự cuối. PII là viết tắt của Personally Identifiable Information (thông tin định danh cá nhân).
- **`JsonFormatter`**: định dạng mỗi bản ghi log thành một dòng JSON. Nếu log có lỗi kèm theo (`logger.exception`), thêm trường `exc` chứa traceback.
- **`setup_logging`**: áp dụng định dạng này cho **toàn bộ** log của app, kể cả log của thư viện. `force=True` ghi đè cấu hình cũ nếu có.
- Log ghi ra **stdout/stderr**, không ghi ra file. Trong Docker, `docker compose logs` đọc được ngay, và Docker tự quản lý việc lưu trữ.

### Bước 2: Bật log JSON trong app

Mở `src/agent/app.py`:

1. Thêm import:

   ```python
   import time
   ```

   và

   ```python
   from agent.logging_config import setup_logging
   ```

2. Ngay **dưới** các dòng import, **trên** dòng `logger = logging.getLogger(__name__)`, thêm:

   ```python
   setup_logging()
   ```

3. Thay hàm `chat` bằng phiên bản có ghi lại thời gian xử lý:

   ```python
   @app.post("/chat", response_model=ChatResponse)
   def chat(req: ChatRequest):
       start = time.perf_counter()
       try:
           result = run_agent(req.session_id, req.message)
       except Exception:
           logger.exception("Lỗi khi xử lý chat session=%s", req.session_id)
           raise HTTPException(
               status_code=503, detail="Hệ thống đang bận, bạn thử lại sau ít phút nhé."
           )
       logger.info(
           "chat session=%s latency=%.2fs", req.session_id, time.perf_counter() - start
       )
       return result
   ```

Để ý: ta log `session_id` và thời gian xử lý, nhưng **không log nội dung tin nhắn**. Nội dung đã được lưu trong database (có kiểm soát truy cập), không cần nhân bản ra log.

### Bước 3: Test hàm che số điện thoại

Thêm vào cuối `tests/test_tools.py`:

```python
from agent.logging_config import mask_pii


def test_che_so_dien_thoai():
    assert mask_pii("Gọi tôi 0912345678 nhé") == "Gọi tôi 091****678 nhé"
    assert mask_pii("+84912345678") == "+84****678"
```

Rồi chuyển dòng `from agent.logging_config import mask_pii` lên đầu file, cạnh các import khác, để ruff không báo lỗi thứ tự import. Chạy:

```bash
pytest
```

Kết quả: `13 passed`.

### Bước 4: Thêm metric cho app

Thêm thư viện vào `dependencies` trong `pyproject.toml`:

```toml
    "prometheus-fastapi-instrumentator>=7.0",
```

```bash
pip install -e ".[dev]"
```

Mở `src/agent/app.py`:

1. Thêm import:

   ```python
   from prometheus_fastapi_instrumentator import Instrumentator
   ```

2. Ngay **dưới** khối `if settings.cors_origins: ...`, thêm:

   ```python
   Instrumentator().instrument(app).expose(app, include_in_schema=False)
   ```

Một dòng này tự động đo **mọi endpoint**: số request (theo status code), độ trễ, kích thước request/response. Kết quả có ở `/metrics`. `include_in_schema=False` ẩn `/metrics` khỏi trang `/docs`.

### Bước 5: Metric riêng cho agent

Cập nhật `src/agent/agent.py` để đo thời gian gọi LLM, số token, số lần gọi từng tool. Toàn bộ file:

```python
import logging
import time

from prometheus_client import Counter, Histogram

from agent import llm, memory, tools
from agent.prompts import SYSTEM_PROMPT

logger = logging.getLogger(__name__)

MAX_STEPS = 5  # chặn vòng lặp vô hạn nếu LLM cứ gọi tool mãi
FALLBACK_REPLY = "Xin lỗi, mình chưa xử lý được yêu cầu này. Bạn thử hỏi lại ngắn gọn hơn nhé."

LLM_SECONDS = Histogram("llm_request_seconds", "Thời gian mỗi lần gọi LLM")
LLM_TOKENS = Counter("llm_tokens_total", "Số token LLM đã dùng", ["loai"])
TOOL_CALLS = Counter("agent_tool_calls_total", "Số lần agent gọi tool", ["tool"])


def run_agent(session_id: str, user_message: str) -> dict:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *memory.load(session_id),
        {"role": "user", "content": user_message},
    ]
    tools_used = []
    reply = FALLBACK_REPLY

    for _ in range(MAX_STEPS):
        start = time.perf_counter()
        resp = llm.chat(messages, tools=tools.TOOL_SCHEMAS)
        LLM_SECONDS.observe(time.perf_counter() - start)
        if resp.usage:
            LLM_TOKENS.labels("input").inc(resp.usage.prompt_tokens)
            LLM_TOKENS.labels("output").inc(resp.usage.completion_tokens)

        msg = resp.choices[0].message
        if not msg.tool_calls:
            reply = msg.content or FALLBACK_REPLY
            break

        # Phải gửi lại chính tin nhắn có tool_calls thì LLM mới hiểu kết quả tool
        messages.append(msg.model_dump(exclude_none=True))
        for call in msg.tool_calls:
            name = call.function.name
            TOOL_CALLS.labels(name).inc()
            tools_used.append(name)
            result = tools.execute(name, call.function.arguments, session_id)
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result})

    memory.save(session_id, user_message, reply)
    logger.info("session=%s tools=%s", session_id, tools_used)
    return {"reply": reply, "tools_used": tools_used}
```

Giải thích:

- `prometheus_client` được cài kèm theo instrumentator.
- **`Histogram("llm_request_seconds", ...)`**: đo phân bố thời gian gọi LLM. `.observe(x)` ghi một giá trị.
- **`Counter(..., ["loai"])`**: counter có **label** (nhãn). `.labels("input").inc(n)` tăng thêm `n` cho nhãn `loai="input"`. Nhờ label, một metric phân biệt được token đầu vào và đầu ra.
- **`if resp.usage:`**: một số server LLM không trả `usage`, nên kiểm tra trước để tránh lỗi.

Chạy lại test để chắc chắn không hỏng gì:

```bash
pytest
```

Chạy app, chat vài câu, rồi xem metric:

```bash
curl -s http://localhost:8080/metrics | grep -E "^(llm_|agent_|http_requests_total)"
```

Bạn sẽ thấy các dòng như `agent_tool_calls_total{tool="tim_san_pham"} 2.0`.

### Bước 6: Chạy Prometheus và Grafana

```bash
mkdir -p monitoring
```

Tạo file `monitoring/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: agent
    static_configs:
      - targets: ["app:8080"]
```

Prometheus sẽ gọi `http://app:8080/metrics` mỗi 15 giây. `app` là tên service trong Compose.

Mở `compose.yaml`, thêm 2 service **dưới** service `app`:

```yaml
  prometheus:
    image: prom/prometheus:v2.55.1
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - promdata:/prometheus
    ports:
      - "127.0.0.1:9090:9090"
    restart: unless-stopped

  grafana:
    image: grafana/grafana:11.3.0
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD:-admin}
    volumes:
      - grafanadata:/var/lib/grafana
    ports:
      - "127.0.0.1:3000:3000"
    restart: unless-stopped
```

Và sửa phần `volumes:` ở cuối file thành:

```yaml
volumes:
  pgdata:
  promdata:
  grafanadata:
```

Thêm vào `.env.example`:

```bash
# Mật khẩu đăng nhập Grafana (user: admin)
GRAFANA_PASSWORD=
```

Ghi chú:

- Image được **ghim phiên bản** (`v2.55.1`, `11.3.0`) thay vì `latest`. Như vậy hệ thống không tự nhiên thay đổi khi nhà phát triển ra bản mới. Bạn có thể dùng bản mới hơn, nhưng hãy chủ động nâng cấp và kiểm tra.
- Cả hai chỉ mở ở `127.0.0.1`. Trên máy chủ, bạn sẽ truy cập qua **SSH tunnel** (Bài 15), không mở ra Internet.

Khởi động:

```bash
docker compose up -d --build
```

```bash
docker compose ps
```

### Bước 7: Kiểm tra Prometheus

Mở **http://localhost:9090** → menu **Status** → **Targets**. Target `agent` phải ở trạng thái **UP**.

Vào trang chủ (Graph), gõ truy vấn rồi bấm **Execute**:

```
agent_tool_calls_total
```

Chat thêm vài câu trên http://localhost:8080, đợi 15 giây rồi Execute lại để thấy số tăng.

### Bước 8: Tạo dashboard Grafana

1. Mở **http://localhost:3000**, đăng nhập `admin` / mật khẩu (`admin` nếu chưa đặt `GRAFANA_PASSWORD`). Grafana yêu cầu đổi mật khẩu ở lần đầu.
2. **Kết nối Prometheus:** menu **Connections** → **Data sources** → **Add data source** → **Prometheus**. Ô **Prometheus server URL** điền `http://prometheus:9090`. Bấm **Save & test**, phải thấy thông báo thành công.
3. **Tạo dashboard:** menu **Dashboards** → **New** → **New dashboard** → **Add visualization** → chọn data source Prometheus.
4. Ở ô truy vấn, chọn chế độ **Code** (thay vì Builder), dán truy vấn PromQL, đặt **Title** ở khung bên phải, bấm **Save dashboard**. Lặp lại **Add** → **Visualization** cho từng panel.

**Các panel nên có:**

| Tên panel | Truy vấn PromQL | Ý nghĩa |
|---|---|---|
| Request /chat mỗi giây | `sum(rate(http_requests_total{handler="/chat"}[5m]))` | Lưu lượng |
| Lỗi 5xx mỗi giây | `sum(rate(http_requests_total{handler="/chat", status="5xx"}[5m]))` | Lỗi |
| Độ trễ trung bình /chat (giây) | `rate(http_request_duration_seconds_sum{handler="/chat"}[5m]) / rate(http_request_duration_seconds_count{handler="/chat"}[5m])` | Độ trễ |
| p95 thời gian gọi LLM (giây) | `histogram_quantile(0.95, sum(rate(llm_request_seconds_bucket[5m])) by (le))` | LLM có chậm không |
| Token mỗi giờ | `sum by (loai) (increase(llm_tokens_total[1h]))` | Chi phí |
| Tool được gọi mỗi giờ | `sum by (tool) (increase(agent_tool_calls_total[1h]))` | Khách hỏi gì nhiều |

Giải thích PromQL:

- `rate(x[5m])`: tốc độ tăng **mỗi giây** của counter `x`, tính trung bình trong 5 phút.
- `increase(x[1h])`: counter tăng **bao nhiêu** trong 1 giờ.
- `sum by (tool) (...)`: cộng gộp, nhưng tách riêng theo từng giá trị của label `tool`.
- `histogram_quantile(0.95, ...)`: tính p95 từ histogram.

💡 **Mẹo:** dashboard lưu trong volume `grafanadata`. Có thể xuất ra file JSON (biểu tượng chia sẻ → **Export**) và commit vào `monitoring/` để không mất.

### Bước 9: Cảnh báo (alert)

Dashboard chỉ hữu ích khi có người nhìn. **Cảnh báo** tự báo cho bạn khi có sự cố. Gợi ý các cảnh báo nên có:

| Cảnh báo | Điều kiện gợi ý |
|---|---|
| App sập | Target `agent` DOWN quá 2 phút |
| Lỗi tăng cao | Tỉ lệ 5xx trên `/chat` > 5% trong 5 phút |
| LLM chậm | p95 thời gian gọi LLM > 10 giây trong 10 phút |
| Chi phí bất thường | Token mỗi giờ gấp 3 lần bình thường |

Grafana có sẵn tính năng **Alerting** (menu **Alerting** → **Alert rules**), gửi thông báo qua email, Telegram, Slack… Xem [Grafana Alerting](https://grafana.com/docs/grafana/latest/alerting/).

Ngoài ra, nên dùng thêm một dịch vụ **giám sát từ bên ngoài** (ví dụ [UptimeRobot](https://uptimerobot.com/) bản miễn phí) gọi `https://<ten-mien>/health` mỗi 5 phút. Nếu cả máy chủ sập thì Grafana cũng sập theo và không báo được, nhưng dịch vụ bên ngoài vẫn báo.

### Bước 10: Xem log JSON

```bash
docker compose logs --tail 20 app
```

Mỗi dòng là một JSON. Lọc chỉ lấy dòng lỗi (cần cài `jq`: `sudo apt install jq`):

```bash
docker compose logs --no-log-prefix app | grep '^{' | jq 'select(.level == "ERROR")'
```

Gửi tin nhắn có số điện thoại để xem log có bị che không:

```bash
curl -s -X POST http://localhost:8080/chat -H "Content-Type: application/json" \
  -d '{"session_id": "test-pii", "message": "Tôi muốn khiếu nại, gọi tôi số 0912345678"}'
```

```bash
docker compose logs --tail 30 app | grep 0912
```

Lệnh cuối **không được in ra** số đầy đủ `0912345678`.

### Bước 11: Commit

```bash
git add src/ tests/ pyproject.toml compose.yaml monitoring/ .env.example
```

```bash
git commit -m "Bài 13: log JSON, che PII, metric Prometheus, Grafana"
```

```bash
git push
```

---

## Tìm hiểu thêm: tracing cho ứng dụng LLM

Khi agent gọi LLM nhiều vòng và nhiều tool, rất cần xem **toàn bộ hành trình** của một câu hỏi: prompt gửi đi, tool được gọi, kết quả tool, câu trả lời, thời gian và token của từng bước. Có các công cụ chuyên cho việc này:

- [Langfuse](https://langfuse.com/): mã nguồn mở, tự host bằng Docker được, có tích hợp sẵn với thư viện `openai`.
- [OpenTelemetry](https://opentelemetry.io/): chuẩn chung cho tracing mọi loại ứng dụng.

Đây là bài tập nâng cao rất đáng làm sau khi xong khóa học.

## Kiểm tra kết quả

- [ ] Log của app là JSON, số điện thoại bị che.
- [ ] `/metrics` có `llm_tokens_total`, `agent_tool_calls_total`, `http_requests_total`.
- [ ] Prometheus target `agent` ở trạng thái UP.
- [ ] Grafana có dashboard với ít nhất 4 panel.
- [ ] `pytest` báo `13 passed`.

## Lỗi thường gặp

| Lỗi | Nguyên nhân | Cách sửa |
|---|---|---|
| Target `agent` DOWN, lỗi `connection refused` | App chưa chạy hoặc sai tên service | `docker compose ps`; target phải là `app:8080` |
| Grafana `Save & test` thất bại | Điền URL `localhost:9090` | Trong mạng Docker phải là `http://prometheus:9090` |
| Panel "No data" | Chưa có request nào, hoặc chưa đủ 5 phút cho `rate(...[5m])` | Chat vài câu, đợi vài phút |
| `Duplicated timeseries in CollectorRegistry` | Metric bị tạo hai lần (thường do import module hai lần theo hai đường khác nhau) | Chỉ khai báo metric ở **một** nơi, tạo ở cấp module |
| Panel token hiện số nhảy lung tung | App khởi động lại làm counter về 0 | Bình thường, `rate`/`increase` tự xử lý việc counter bị reset |

## Bài tập

1. Thêm metric `handoff_total` (Counter) tăng mỗi khi agent chuyển cho nhân viên. Thêm panel cho nó.
2. Tạo một alert rule trong Grafana: báo khi có lỗi 5xx. Thử kích hoạt bằng cách tắt database (`docker compose stop db`) rồi chat.
3. Thêm panel "Chi phí ước tính mỗi giờ (USD)": nhân số token với giá mỗi token của model bạn dùng.
4. (Nâng cao) Thêm [postgres_exporter](https://github.com/prometheus-community/postgres_exporter) để giám sát database (số kết nối, kích thước bảng).

## Checklist hoàn thành

- [ ] Hiểu log, metric, trace và Four Golden Signals
- [ ] Log JSON, không chứa số điện thoại
- [ ] Prometheus thu thập metric, Grafana có dashboard
- [ ] Biết cần cảnh báo những gì
- [ ] Đã commit và push

➡️ Tiếp theo: [Bài 14: CI/CD với GitHub Actions](bai-14-ci-cd.md)
