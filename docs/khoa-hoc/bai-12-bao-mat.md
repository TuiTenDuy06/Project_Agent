# Bài 12: Bảo mật

## Mục tiêu

Sau bài này bạn sẽ:

- Nắm các rủi ro bảo mật chính của một ứng dụng web có AI.
- Quản lý **bí mật** (API key, mật khẩu) đúng cách, và biết phải làm gì khi lỡ để lộ.
- Làm **API quản trị** có xác thực bằng API key, để nhân viên xem danh sách khách cần hỗ trợ.
- Hiểu **CORS** và cấu hình khi cần.
- Kiểm tra lỗ hổng trong thư viện bằng **pip-audit**.
- Có một **checklist bảo mật** để rà soát trước khi đưa lên production.

## Kiến thức cần học

| Chủ đề | Tài liệu |
|---|---|
| Top 10 rủi ro web | [OWASP Top 10](https://owasp.org/www-project-top-ten/) |
| Top 10 rủi ro ứng dụng LLM | [OWASP Top 10 for LLM Applications](https://genai.owasp.org/llm-top-10/) |
| Bảo mật trong FastAPI | [FastAPI: Security](https://fastapi.tiangolo.com/tutorial/security/) |
| CORS | [MDN: CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS) |
| Bí mật trong Git | [GitHub: Removing sensitive data](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository) |
| pip-audit | [pip-audit trên GitHub](https://github.com/pypa/pip-audit) |

---

## Phần lý thuyết

### 1. Những gì cần bảo vệ

| Tài sản | Mất thì sao |
|---|---|
| API key Gemini / GPU | Kẻ xấu dùng chùa, bạn trả tiền |
| Database | Lộ hội thoại, số điện thoại khách; dữ liệu bị sửa hoặc xóa |
| Máy chủ | Bị chiếm làm máy đào tiền ảo, phát tán mã độc |
| Uy tín | Agent bị dụ nói điều sai lệch, xúc phạm khách |

### 2. Nguyên tắc chung

1. **Quyền hạn tối thiểu** (least privilege): mỗi thành phần chỉ có đúng quyền nó cần. Ví dụ: tool chỉ đọc, container không chạy root, database không mở ra Internet.
2. **Phòng thủ nhiều lớp** (defense in depth): không trông chờ vào một lớp duy nhất. Prompt có bị vượt qua thì tool vẫn giới hạn quyền. Tool có lỗi thì database vẫn có ràng buộc.
3. **Không tin dữ liệu từ bên ngoài**: kiểm tra mọi thứ ở cửa vào (Pydantic), và coi kết quả của LLM cũng là dữ liệu không tin cậy.
4. **Bí mật không nằm trong code**.

### 3. Những gì dự án đã làm được từ các bài trước

| Biện pháp | Bài |
|---|---|
| `.env` không commit, không đóng gói vào image | 01, 11 |
| SQL dùng tham số, chống SQL injection | 05 |
| Database chỉ mở ở `127.0.0.1` | 05 |
| Validation đầu vào bằng Pydantic | 04 |
| Lỗi nội bộ không trả chi tiết cho client | 04 |
| Tool chỉ đọc, `session_id` do server gán | 06, 08 |
| Giới hạn vòng lặp agent | 06 |
| Chống XSS bằng `textContent` | 09 |
| Container chạy bằng user thường | 11 |

Bài này bổ sung: xác thực API quản trị, CORS, quản lý bí mật, kiểm tra thư viện. Bài 15 bổ sung: firewall, HTTPS, giới hạn tốc độ (rate limit).

### 4. Xác thực bằng API key

API `/admin/handoffs` cho phép xem số điện thoại khách, nên **không thể để công khai**. Cách đơn giản: yêu cầu header `X-API-Key` chứa một khóa bí mật dài, ngẫu nhiên. Chỉ nhân viên có khóa mới gọi được.

Khi so sánh khóa, dùng `secrets.compare_digest()` thay vì `==`. Phép `==` dừng lại ngay ở ký tự sai đầu tiên, nên kẻ xấu có thể **đo thời gian phản hồi** để đoán dần từng ký tự (timing attack). `compare_digest` luôn mất thời gian như nhau.

🧠 **Hiểu sâu:** API key phù hợp cho vài nhân viên nội bộ. Hệ thống lớn có nhiều người dùng sẽ cần đăng nhập thật (OAuth2, JWT), phân quyền theo vai trò, và ghi lại ai đã xem gì. Đọc [FastAPI: OAuth2 with JWT](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/) khi cần.

### 5. CORS

Trình duyệt có quy tắc **Same-Origin Policy**: JavaScript của trang `a.com` **không được** gọi API của `b.com`, trừ khi `b.com` cho phép bằng **CORS** (Cross-Origin Resource Sharing).

- Trang chat của ta nằm **cùng địa chỉ** với API, nên **không cần CORS**.
- Nếu sau này muốn nhúng khung chat vào website khác (ví dụ `tienloi24h.vn` gọi API ở `cskh.tienloi24h.vn`), thì phải cho phép đúng domain đó.
- **Không bao giờ** đặt `allow_origins=["*"]` cho API có dữ liệu nhạy cảm.

---

## Thực hành từng bước

> Chuẩn bị: `cd ~/project_agent && source .venv/bin/activate`, database đang chạy.

### Bước 1: Thêm cấu hình bảo mật

Mở `src/agent/config.py`, thêm vào class `Settings` (dưới `database_url`):

```python
    # Khóa bảo vệ các API quản trị (/admin/...)
    admin_api_key: str = ""
    # Các domain khác được phép gọi API từ trình duyệt
    cors_origins: list[str] = []
```

Tạo một khóa ngẫu nhiên đủ mạnh:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Thêm vào `.env` (dán chuỗi vừa tạo):

```bash
ADMIN_API_KEY=<chuỗi-vừa-tạo>
```

Thêm vào `.env.example` (để trống giá trị):

```bash
# Tạo bằng: python -c "import secrets; print(secrets.token_urlsafe(32))"
ADMIN_API_KEY=
# Chỉ cần khi nhúng chat vào domain khác, dạng JSON: ["https://tienloi24h.vn"]
CORS_ORIGINS=[]
```

`admin_api_key` mặc định là chuỗi rỗng. Code bên dưới sẽ **từ chối mọi request** khi khóa rỗng. Quên cấu hình thì API quản trị bị khóa, chứ không bị mở toang. Đây là nguyên tắc **"mặc định an toàn"** (secure by default).

### Bước 2: API quản trị và CORS

Cập nhật `src/agent/app.py`. Toàn bộ file sau khi sửa:

```python
import logging
import secrets
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from agent.agent import run_agent
from agent.config import settings
from agent.db import pool

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    pool.open(wait=True)  # mở pool khi app khởi động, lỗi ngay nếu không kết nối được
    yield
    pool.close()  # đóng pool khi app tắt


app = FastAPI(title="Agent CSKH Tiện Lợi 24h", lifespan=lifespan)

if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["POST"],
        allow_headers=["Content-Type"],
    )


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    message: str = Field(min_length=1, max_length=1000)


class ChatResponse(BaseModel):
    reply: str
    tools_used: list[str]


def require_admin(x_api_key: str = Header(default="")) -> None:
    # compare_digest: so sánh chống đoán khóa theo thời gian phản hồi
    if not settings.admin_api_key or not secrets.compare_digest(
        x_api_key, settings.admin_api_key
    ):
        raise HTTPException(status_code=401, detail="Sai hoặc thiếu API key")


@app.get("/health")
def health():
    with pool.connection() as conn:
        conn.execute("SELECT 1")
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    try:
        return run_agent(req.session_id, req.message)
    except Exception:
        logger.exception("Lỗi khi xử lý chat session=%s", req.session_id)
        raise HTTPException(
            status_code=503, detail="Hệ thống đang bận, bạn thử lại sau ít phút nhé."
        )


@app.get("/admin/handoffs", dependencies=[Depends(require_admin)])
def list_handoffs():
    with pool.connection() as conn:
        return conn.execute(
            """
            SELECT id, session_id, reason, phone, status, created_at
            FROM handoffs
            WHERE status = 'moi'
            ORDER BY created_at
            """
        ).fetchall()


# Đặt cuối cùng: mọi đường dẫn khác trả về giao diện chat
app.mount(
    "/", StaticFiles(directory=Path(__file__).parent / "static", html=True), name="web"
)
```

Giải thích các phần mới:

- **`require_admin`** là một **dependency** (phụ thuộc) của FastAPI. `x_api_key: str = Header(default="")` đọc header `X-API-Key`; FastAPI tự đổi `x_api_key` thành `X-API-Key`. Hàm ném lỗi `401` nếu khóa sai hoặc server chưa cấu hình khóa.
- **`dependencies=[Depends(require_admin)]`**: FastAPI chạy `require_admin` **trước** hàm `list_handoffs`. Khóa sai thì hàm không bao giờ chạy. Muốn bảo vệ endpoint quản trị khác, chỉ cần thêm dòng này.
- **CORS** chỉ bật khi `CORS_ORIGINS` có giá trị, và chỉ cho phép đúng method `POST` với header `Content-Type`, vừa đủ cho `/chat`.

### Bước 3: Thử API quản trị

Chạy app:

```bash
uvicorn agent.app:app --reload --port 8080
```

Không có khóa:

```bash
curl -i http://localhost:8080/admin/handoffs
```

Kết quả: `401`. Khóa sai:

```bash
curl -i http://localhost:8080/admin/handoffs -H "X-API-Key: doan-bua"
```

Kết quả: `401`. Khóa đúng (thay bằng khóa trong `.env`):

```bash
curl http://localhost:8080/admin/handoffs -H "X-API-Key: <khoa-trong-env>"
```

Kết quả: danh sách yêu cầu hỗ trợ đã tạo ở Bài 08.

### Bước 4: Thêm test cho API quản trị

Mở `tests/conftest.py`, thêm dòng:

```python
os.environ.setdefault("ADMIN_API_KEY", "test-admin-key")
```

Thêm vào cuối `tests/test_app.py`:

```python
def test_admin_can_api_key():
    res = client.get("/admin/handoffs")
    assert res.status_code == 401


def test_admin_tu_choi_khoa_sai():
    res = client.get("/admin/handoffs", headers={"X-API-Key": "sai"})
    assert res.status_code == 401
```

Chạy:

```bash
pytest
```

Kết quả: `12 passed`.

### Bước 5: Quản lý bí mật đúng cách

**Trên máy bạn và máy chủ:**

- Chỉ chủ sở hữu được đọc `.env`:

  ```bash
  chmod 600 .env
  ```

- Mỗi môi trường (máy bạn, máy chủ) dùng **khóa riêng**. Lộ một cái thì không ảnh hưởng cái còn lại.
- Đặt **giới hạn chi tiêu** (budget) và cảnh báo chi phí trong trang quản lý Google Cloud / nhà cung cấp GPU, để key có bị lộ thì thiệt hại cũng có giới hạn.

**Kiểm tra Git chưa từng chứa bí mật:**

```bash
git log --all --oneline -- .env
```

Nếu lệnh này **không in gì**: tốt, `.env` chưa bao giờ được commit. Nếu có, xem mục tiếp theo.

**Nếu lỡ commit hoặc làm lộ bí mật:**

1. **Thu hồi ngay**: xóa API key cũ trên trang của nhà cung cấp, tạo key mới. Đổi mật khẩu bị lộ. **Đây là bước quan trọng nhất**, vì xóa file khỏi Git **không đủ**: bot quét GitHub tìm key chỉ trong vài phút.
2. Cập nhật key mới vào `.env` ở mọi nơi.
3. Xóa bí mật khỏi lịch sử Git theo [hướng dẫn của GitHub](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository).

💡 **Mẹo:** bật **Secret scanning** trong tab Settings → Code security của repository GitHub. GitHub sẽ cảnh báo khi phát hiện key trong code.

### Bước 6: Kiểm tra lỗ hổng trong thư viện

Thư viện bạn dùng cũng có thể có lỗ hổng. `pip-audit` so sánh các thư viện đã cài với cơ sở dữ liệu lỗ hổng đã công bố:

```bash
pip install pip-audit
```

```bash
pip-audit
```

Nếu có lỗ hổng, công cụ chỉ ra phiên bản đã sửa. Nâng cấp bằng `pip install -U <ten-thu-vien>`, chạy lại test, rồi commit. Hãy chạy `pip-audit` **định kỳ**, ví dụ mỗi tháng. Bài 14 có thể đưa nó vào CI.

💡 **Mẹo:** bật **Dependabot** trên GitHub (Settings → Code security → Dependabot alerts). GitHub sẽ tự báo và tự tạo pull request nâng cấp thư viện có lỗ hổng.

### Bước 7: Commit

```bash
git add src/ tests/ .env.example
```

```bash
git commit -m "Bài 12: API quản trị có xác thực, CORS, test bảo mật"
```

```bash
git push
```

---

## Checklist bảo mật trước khi lên production

Lưu checklist này lại. Bạn sẽ dùng nó ở Bài 15 và Bài 18.

**Bí mật**
- [ ] `.env` không có trong Git, không có trong image Docker
- [ ] `.env` trên máy chủ có quyền `600`
- [ ] Mật khẩu database trên máy chủ là chuỗi ngẫu nhiên mạnh, không phải `agent`
- [ ] `ADMIN_API_KEY` là chuỗi ngẫu nhiên tối thiểu 32 ký tự
- [ ] Đã đặt giới hạn chi tiêu cho API key LLM

**Mạng**
- [ ] Chỉ mở cổng 22 (SSH), 80, 443 trên firewall (Bài 15)
- [ ] Database, app, Prometheus, Grafana chỉ nghe ở `127.0.0.1`
- [ ] Có HTTPS (Bài 15)
- [ ] Có rate limit cho `/chat` (Bài 15)
- [ ] `/metrics` không truy cập được từ Internet (Bài 15)

**Ứng dụng**
- [ ] Validation đầu vào đầy đủ
- [ ] API quản trị yêu cầu API key
- [ ] Tool chỉ có quyền tối thiểu
- [ ] Log không chứa số điện thoại, API key (Bài 13)
- [ ] `pip-audit` không còn lỗ hổng nghiêm trọng

**Máy chủ**
- [ ] Đăng nhập SSH bằng key, đã tắt đăng nhập bằng mật khẩu (Bài 15)
- [ ] Không đăng nhập trực tiếp bằng `root` (Bài 15)
- [ ] Tự động cập nhật bản vá bảo mật (Bài 15)
- [ ] Có sao lưu database, đã thử khôi phục (Bài 15)

## Lỗi thường gặp

| Lỗi | Nguyên nhân | Cách sửa |
|---|---|---|
| Luôn nhận `401` dù gửi đúng khóa | Server chưa đọc được `ADMIN_API_KEY` (quên khởi động lại sau khi sửa `.env`) | Khởi động lại uvicorn hoặc container |
| `error parsing value for field "cors_origins"` | `CORS_ORIGINS` không đúng định dạng JSON | Viết dạng `["https://a.vn"]`, có ngoặc vuông và nháy kép |
| Trình duyệt báo `blocked by CORS policy` | Đang gọi API từ domain khác chưa được cho phép | Thêm domain đó vào `CORS_ORIGINS` |

## Bài tập

1. Thêm endpoint `POST /admin/handoffs/{id}/xong` (có bảo vệ API key) để đổi `status` của một yêu cầu thành `da_xu_ly`. Viết test cho trường hợp thiếu khóa.
2. Ở production, trang `/docs` làm lộ danh sách API. Tìm cách tắt nó: gợi ý là tham số `docs_url` và `redoc_url` của `FastAPI(...)`. Có nên tắt không? Vì sao?
3. Đọc [OWASP Top 10 for LLM](https://genai.owasp.org/llm-top-10/). Với mỗi mục, viết 1–2 câu: dự án của bạn đã phòng chống chưa, bằng cách nào?
4. Chạy `pip-audit` và ghi lại kết quả.

## Checklist hoàn thành

- [ ] Hiểu nguyên tắc quyền hạn tối thiểu, phòng thủ nhiều lớp, mặc định an toàn
- [ ] API `/admin/handoffs` yêu cầu API key, so sánh bằng `compare_digest`
- [ ] Biết xử lý khi lộ bí mật: thu hồi trước, dọn dẹp sau
- [ ] Đã chạy `pip-audit`
- [ ] `pytest` báo `12 passed`
- [ ] Đã commit và push

➡️ Tiếp theo: [Bài 13: Logging và giám sát](bai-13-logging-monitoring.md)
