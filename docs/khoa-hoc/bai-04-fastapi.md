# Bài 04: Viết API bằng FastAPI

## Mục tiêu

Sau bài này bạn sẽ:

- Hiểu web framework là gì và vì sao chọn **FastAPI**.
- Tạo được API có 2 endpoint: `GET /health` và `POST /chat`.
- Dùng **Pydantic** để kiểm tra dữ liệu đầu vào (validation).
- Xử lý lỗi đúng cách: trả status code hợp lý, không làm lộ chi tiết lỗi bên trong.
- Thử API bằng trang tài liệu tự động `/docs` và bằng `curl`.

## Kiến thức cần học

| Chủ đề | Tài liệu |
|---|---|
| FastAPI tutorial (rất nên đọc) | [FastAPI: Tutorial - User Guide](https://fastapi.tiangolo.com/tutorial/), các mục First Steps đến Handling Errors |
| Pydantic | [Pydantic: Models](https://docs.pydantic.dev/latest/concepts/models/) và [Fields](https://docs.pydantic.dev/latest/concepts/fields/) |
| Uvicorn | [Uvicorn docs](https://www.uvicorn.org/) |
| Biểu thức chính quy (regex) | [regex101.com](https://regex101.com/), trang để thử regex |

---

## Phần lý thuyết

### Web framework là gì?

Bạn có thể tự viết code đọc HTTP request từ mạng, nhưng rất mất công. **Web framework** lo phần đó giúp bạn. Bạn chỉ việc viết hàm xử lý và "gắn" hàm vào đường dẫn.

**FastAPI** được chọn vì:

- **Nhanh** để viết, code ngắn gọn.
- **Tự kiểm tra dữ liệu** dựa vào type hint và Pydantic.
- **Tự sinh tài liệu API** ở `/docs`, thử API ngay trên trình duyệt.
- Phổ biến trong cộng đồng AI/ML.

### Uvicorn

FastAPI chỉ định nghĩa **ứng dụng**. Cần một **server** để nhận kết nối mạng và chuyển request vào ứng dụng, đó là **Uvicorn**.

### Validation: không bao giờ tin dữ liệu từ bên ngoài

Mọi dữ liệu từ client đều có thể sai, thiếu, quá dài hoặc độc hại. **Kiểm tra ngay ở cửa vào** (gọi là "trust boundary", ranh giới tin cậy) là nguyên tắc bảo mật cơ bản. Với Pydantic, bạn khai báo "trường `message` là chuỗi dài 1–1000 ký tự". Gửi sai thì FastAPI tự trả lỗi `422` mà hàm của bạn không phải chạy.

---

## Thực hành từng bước

> Kích hoạt môi trường ảo: `cd ~/project_agent && source .venv/bin/activate`

### Bước 1: Thêm thư viện

Mở `pyproject.toml`, thêm 2 dòng vào `dependencies`:

```toml
dependencies = [
    "openai>=1.50",
    "pydantic-settings>=2.4",
    "fastapi>=0.115",
    "uvicorn[standard]>=0.30",
]
```

Cài lại:

```bash
pip install -e ".[dev]"
```

### Bước 2: Endpoint đầu tiên `/health`

Tạo file `src/agent/app.py`:

```python
from fastapi import FastAPI

app = FastAPI(title="Agent CSKH Tiện Lợi 24h")


@app.get("/health")
def health():
    return {"status": "ok"}
```

Chạy server:

```bash
uvicorn agent.app:app --reload --port 8080
```

Giải thích lệnh:

- `agent.app:app`: trong module `agent.app` (file `src/agent/app.py`), lấy biến tên `app`.
- `--reload`: tự khởi động lại khi bạn sửa code. **Chỉ dùng khi phát triển.**
- `--port 8080`: nghe ở cổng 8080.

Mở **terminal thứ hai** (nhớ kích hoạt venv), gọi thử:

```bash
curl http://localhost:8080/health
```

Kết quả: `{"status":"ok"}`.

Mở trình duyệt vào **http://localhost:8080/docs**. Đây là trang tài liệu FastAPI tự sinh. Bấm vào `GET /health` → **Try it out** → **Execute**.

🧠 **Hiểu sâu:** endpoint `/health` có vẻ vô dụng nhưng rất quan trọng ở production. Docker (Bài 11), Nginx và hệ thống giám sát gọi nó định kỳ để biết app còn sống không. Bài 05 sẽ cho nó kiểm tra cả kết nối database.

### Bước 3: Định nghĩa dữ liệu vào và ra bằng Pydantic

Thay toàn bộ nội dung `src/agent/app.py`:

```python
import logging

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from agent import llm

logger = logging.getLogger(__name__)

app = FastAPI(title="Agent CSKH Tiện Lợi 24h")

SYSTEM_PROMPT = "Bạn là trợ lý chăm sóc khách hàng của chuỗi cửa hàng tiện lợi Tiện Lợi 24h. Trả lời ngắn gọn."


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    message: str = Field(min_length=1, max_length=1000)


class ChatResponse(BaseModel):
    reply: str
    tools_used: list[str]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": req.message},
    ]
    try:
        resp = llm.chat(messages)
    except Exception:
        logger.exception("Lỗi khi gọi LLM, session=%s", req.session_id)
        raise HTTPException(
            status_code=503, detail="Hệ thống đang bận, bạn thử lại sau ít phút nhé."
        )
    return {"reply": resp.choices[0].message.content or "", "tools_used": []}
```

Giải thích từng phần:

**`ChatRequest`** mô tả JSON client phải gửi:

- `session_id`: mã phiên chat, để phân biệt các khách (dùng ở Bài 08). Chỉ cho phép chữ, số, `_`, `-`, tối đa 64 ký tự. Regex `^[A-Za-z0-9_-]+$` nghĩa là từ đầu (`^`) đến cuối (`$`) chỉ gồm các ký tự trong ngoặc vuông.
- `message`: câu hỏi, 1–1000 ký tự. Giới hạn độ dài giúp chặn kẻ xấu gửi văn bản cực dài làm tốn tiền LLM.

**`ChatResponse`** mô tả JSON trả về. `tools_used` cho biết agent đã dùng tool nào (Bài 06). Giờ nó luôn rỗng.

**`response_model=ChatResponse`**: FastAPI kiểm tra và lọc dữ liệu trả về theo đúng mô hình này.

**`def chat(req: ChatRequest)`**: FastAPI thấy type hint `ChatRequest`, tự đọc JSON body, kiểm tra, rồi tạo object `req`.

**Khối `try/except`:**

- Nếu LLM lỗi (mất mạng, hết hạn mức…), ta **ghi log chi tiết** (`logger.exception` ghi cả traceback) để lập trình viên xem.
- Client chỉ nhận một câu thông báo thân thiện với status `503`.
- **Không bao giờ trả chi tiết lỗi nội bộ cho client**, vì nó có thể làm lộ cấu trúc hệ thống, đường dẫn file, thậm chí bí mật.

### Bước 4: Thử API

Server vẫn đang chạy với `--reload` nên đã tự cập nhật. Gọi thử:

```bash
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "khach-01", "message": "Cửa hàng có bán bánh mì không?"}'
```

Thử gửi dữ liệu **sai** để thấy validation hoạt động:

```bash
curl -i -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "khach 01!", "message": ""}'
```

Kết quả: status `422` và JSON mô tả chính xác từng lỗi: `session_id` sai pattern, `message` quá ngắn. Hàm `chat` **không hề chạy**, nên không tốn tiền LLM.

Thử trên **http://localhost:8080/docs**: mục `POST /chat` hiện sẵn ví dụ JSON. Bấm **Try it out**, sửa nội dung, bấm **Execute**.

### Bước 5: Thử tình huống LLM lỗi

Mở `.env`, cố tình làm hỏng key: thêm chữ `x` vào cuối `LLM_API_KEY`. Dừng server (`Ctrl + C`) rồi chạy lại, vì `--reload` chỉ theo dõi file code, không theo dõi `.env`:

```bash
uvicorn agent.app:app --reload --port 8080
```

Gọi lại `/chat`. Bạn nhận `503` với câu thông báo thân thiện. Ở terminal chạy server, bạn thấy traceback đầy đủ. Đó chính là log dành cho lập trình viên.

**Nhớ sửa lại key cho đúng** rồi khởi động lại server.

### Bước 6: Commit

```bash
git add pyproject.toml src/agent/app.py
```

```bash
git commit -m "Bài 04: API FastAPI với /health và /chat"
```

```bash
git push
```

---

## Kiểm tra kết quả

- [ ] `curl http://localhost:8080/health` trả `{"status":"ok"}`.
- [ ] `POST /chat` với dữ liệu đúng trả câu trả lời của LLM.
- [ ] `POST /chat` với `message` rỗng trả `422`.
- [ ] Key sai thì trả `503`, không lộ chi tiết lỗi cho client.
- [ ] Trang `/docs` hoạt động.

## Lỗi thường gặp

| Lỗi | Nguyên nhân | Cách sửa |
|---|---|---|
| `[Errno 98] Address already in use` | Cổng 8080 đang bị chương trình khác dùng (thường là server cũ chưa tắt) | Tắt server cũ bằng `Ctrl + C`, hoặc dùng `--port 8081` |
| `Error loading ASGI app. Could not import module "agent.app"` | Chưa `pip install -e .`, hoặc gõ sai tên | Kiểm tra file `src/agent/app.py` tồn tại, chạy lại `pip install -e ".[dev]"` |
| `curl: (7) Failed to connect` | Server chưa chạy | Xem terminal chạy server có báo lỗi không |
| Sửa `.env` mà không có tác dụng | `--reload` không theo dõi `.env` | Dừng và chạy lại uvicorn |

## Bài tập

1. Thêm endpoint `GET /info` trả về `{"ten_cua_hang": "Tiện Lợi 24h", "phien_ban": "0.1.0"}`.
2. Thử gửi `message` dài 1.500 ký tự. Gợi ý: `python -c "print('a'*1500)"`. Status code trả về là gì?
3. Đọc mục [Path Parameters](https://fastapi.tiangolo.com/tutorial/path-params/), rồi tạo endpoint `GET /xin-chao/{ten}` trả về `{"loi_chao": "Xin chào <ten>"}`.
4. Giải thích: vì sao ta dùng `logger.exception(...)` thay vì `print(...)`? (Gợi ý: Bài 13 sẽ trả lời chi tiết.)

## Checklist hoàn thành

- [ ] Hiểu FastAPI, Uvicorn, Pydantic dùng để làm gì
- [ ] Có `/health` và `/chat` chạy được
- [ ] Hiểu validation và cách xử lý lỗi an toàn
- [ ] Đã commit và push

➡️ Tiếp theo: [Bài 05: Database PostgreSQL cho cửa hàng](bai-05-postgresql.md)
