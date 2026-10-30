# Bài 02: Kiến thức web và Python bổ trợ

## Mục tiêu

Sau bài này bạn sẽ:

- Hiểu **HTTP** hoạt động thế nào: request, response, method, status code, header.
- Đọc và viết được **JSON**.
- Hiểu **REST API** là gì và gọi được API bằng `curl` và Python.
- Hiểu **biến môi trường** và vì sao không viết mật khẩu vào code.
- Nắm các tính năng Python sẽ gặp trong dự án: type hint, `with`, decorator, `**kwargs`, xử lý ngoại lệ, `async/await`.

## Kiến thức cần học

| Chủ đề | Tài liệu |
|---|---|
| HTTP tổng quan | [MDN: An overview of HTTP](https://developer.mozilla.org/en-US/docs/Web/HTTP/Overview) |
| Mã trạng thái HTTP | [MDN: HTTP response status codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status) |
| JSON | [MDN: Working with JSON](https://developer.mozilla.org/en-US/docs/Learn/JavaScript/Objects/JSON) |
| REST | [restfulapi.net](https://restfulapi.net/) |
| Type hint | [Python docs: typing](https://docs.python.org/3/library/typing.html) |
| async/await | [FastAPI: Concurrency and async/await](https://fastapi.tiangolo.com/async/), bài giải thích rất dễ hiểu |
| httpx | [httpx docs](https://www.python-httpx.org/) |

---

## Phần lý thuyết

### 1. HTTP: ngôn ngữ giữa trình duyệt và máy chủ

Khi bạn mở một trang web, trình duyệt (**client**) gửi một **request** (yêu cầu) đến máy chủ (**server**). Server xử lý rồi trả về một **response** (phản hồi).

Một HTTP request gồm:

```
POST /chat HTTP/1.1                      ← method + đường dẫn (path)
Host: cskh.example.com                   ← header: thông tin phụ
Content-Type: application/json           ← header: nội dung là JSON

{"session_id": "abc", "message": "Xin chào"}   ← body: dữ liệu gửi đi
```

Một HTTP response gồm:

```
HTTP/1.1 200 OK                          ← status code
Content-Type: application/json

{"reply": "Chào bạn! Mình giúp gì được?"}
```

**Các method hay dùng:**

| Method | Ý nghĩa | Ví dụ trong dự án |
|---|---|---|
| `GET` | Lấy dữ liệu, không thay đổi gì | `GET /health`: kiểm tra server còn sống |
| `POST` | Gửi dữ liệu để xử lý hoặc tạo mới | `POST /chat`: gửi câu hỏi |
| `PUT` / `PATCH` | Cập nhật | (không dùng) |
| `DELETE` | Xóa | (không dùng) |

**Các status code cần nhớ:**

| Code | Ý nghĩa | Khi nào gặp |
|---|---|---|
| `200 OK` | Thành công | Bình thường |
| `400 Bad Request` | Request sai | Gửi thiếu dữ liệu |
| `401 Unauthorized` | Chưa xác thực | Thiếu hoặc sai API key |
| `404 Not Found` | Không có đường dẫn này | Gõ sai URL |
| `422 Unprocessable Entity` | Dữ liệu không hợp lệ | FastAPI trả về khi JSON sai định dạng |
| `429 Too Many Requests` | Gửi quá nhiều | Bị giới hạn tốc độ (rate limit) |
| `500 Internal Server Error` | Server lỗi | Code có bug |
| `503 Service Unavailable` | Server tạm không phục vụ được | LLM quá tải |

Quy tắc dễ nhớ: **2xx thành công, 4xx lỗi do client, 5xx lỗi do server.**

### 2. JSON: định dạng dữ liệu phổ biến nhất

JSON (JavaScript Object Notation) trông gần giống `dict` và `list` của Python:

```json
{
  "ten": "Bánh mì sandwich trứng",
  "gia": 15000,
  "con_hang": true,
  "cua_hang": ["Q1-01", "Q3-01"],
  "khuyen_mai": null
}
```

So sánh với Python:

| JSON | Python |
|---|---|
| `{}` object | `dict` |
| `[]` array | `list` |
| `"chuỗi"` (bắt buộc nháy kép) | `str` |
| `123`, `1.5` | `int`, `float` |
| `true` / `false` | `True` / `False` |
| `null` | `None` |

Trong Python, `json.dumps()` đổi `dict` thành chuỗi JSON. `json.loads()` đổi chuỗi JSON thành `dict`.

### 3. REST API

**API** (Application Programming Interface) là "cửa" để chương trình này gọi chương trình khác. **REST API** là kiểu API dùng HTTP, với URL mô tả **tài nguyên** và method mô tả **hành động**. Dự án của bạn sẽ:

- **Cung cấp** REST API: `/chat`, `/health`, `/admin/handoffs`.
- **Gọi** REST API của người khác: API Gemini để dùng LLM.

### 4. Biến môi trường

Biến môi trường (environment variable) là các cặp `TÊN=giá trị` mà hệ điều hành truyền vào chương trình. Ta dùng chúng để chứa **cấu hình và bí mật** (API key, mật khẩu database). Nhờ vậy:

- Không phải viết bí mật vào code. Code đẩy lên GitHub sẽ không lộ.
- Cùng một code chạy được ở nhiều nơi (máy bạn, máy chủ) với cấu hình khác nhau.

Trong dự án, các biến này nằm trong file `.env`. File này **đã bị loại khỏi Git** bằng `.gitignore` ở Bài 01.

---

## Thực hành từng bước

> Nhớ kích hoạt môi trường ảo trước: `cd ~/project_agent && source .venv/bin/activate`

### Bước 1: Gọi API bằng `curl`

`curl` là công cụ gửi HTTP request từ terminal. Ta sẽ thử với `httpbin.org`, một trang chuyên để thử HTTP.

Gửi `GET`:

```bash
curl https://httpbin.org/get
```

Bạn sẽ thấy JSON mô tả request của chính bạn.

Xem cả status code và header (thêm `-i`):

```bash
curl -i https://httpbin.org/status/404
```

Dòng đầu là `HTTP/2 404`.

Gửi `POST` có body JSON:

```bash
curl -X POST https://httpbin.org/post \
  -H "Content-Type: application/json" \
  -d '{"session_id": "abc", "message": "Xin chào"}'
```

Giải thích:

- `-X POST`: dùng method POST.
- `-H`: thêm header.
- `-d`: dữ liệu body.
- Dấu `\` ở cuối dòng: lệnh còn tiếp ở dòng dưới.

Trong kết quả, mục `"json"` chính là dữ liệu bạn gửi.

### Bước 2: Gọi API bằng Python

Cài thư viện `httpx`:

```bash
pip install httpx
```

Tạo file `scripts/thu_http.py`:

```python
import httpx

# GET
resp = httpx.get("https://httpbin.org/get", params={"q": "sữa tươi"})
print("Status:", resp.status_code)
print("URL thật sự đã gọi:", resp.url)

# POST với JSON
resp = httpx.post(
    "https://httpbin.org/post",
    json={"session_id": "abc", "message": "Xin chào"},
)
data = resp.json()  # chuỗi JSON -> dict
print("Server nhận được:", data["json"])

# Xử lý lỗi
resp = httpx.get("https://httpbin.org/status/500")
try:
    resp.raise_for_status()  # ném lỗi nếu status là 4xx hoặc 5xx
except httpx.HTTPStatusError as e:
    print("Lỗi:", e.response.status_code)
```

Chạy:

```bash
python scripts/thu_http.py
```

Chú ý cách `params` tự mã hóa tiếng Việt trong URL (`%E1%BB%AF...`).

### Bước 3: Ôn các tính năng Python sẽ dùng trong dự án

Tạo file `scripts/on_python.py` và gõ từng phần, chạy thử sau mỗi phần.

**3a. Type hint (chú thích kiểu).** Type hint không làm code chạy khác đi, nhưng giúp người đọc và VS Code hiểu code. FastAPI và Pydantic **dùng type hint để kiểm tra dữ liệu**.

```python
def tinh_tong(gia: int, so_luong: int = 1) -> int:
    return gia * so_luong


def tim_ma(ma: str | None = None) -> list[dict]:
    # str | None nghĩa là: chuỗi hoặc None
    return [] if ma is None else [{"ma": ma}]


print(tinh_tong(15000, 2))
print(tim_ma("Q1-01"))
```

**3b. `**kwargs`: truyền tham số bằng dict.** Agent sẽ nhận tham số từ LLM dưới dạng dict rồi gọi hàm bằng `func(**args)`.

```python
def tim_san_pham(tu_khoa: str, ma_cua_hang: str | None = None) -> str:
    return f"Tìm '{tu_khoa}' ở cửa hàng {ma_cua_hang}"


args = {"tu_khoa": "sữa", "ma_cua_hang": "Q1-01"}
print(tim_san_pham(**args))  # giống tim_san_pham(tu_khoa="sữa", ma_cua_hang="Q1-01")

ham = {"tim_san_pham": tim_san_pham}  # dict ánh xạ tên -> hàm
print(ham["tim_san_pham"](**args))
```

**3c. Xử lý ngoại lệ (exception).**

```python
import json

for chuoi in ['{"a": 1}', "{hỏng"]:
    try:
        print(json.loads(chuoi))
    except json.JSONDecodeError as e:
        print("JSON không hợp lệ:", e)
```

**3d. `with`: tự dọn dẹp tài nguyên.** `with` đảm bảo tài nguyên (file, kết nối database) được **đóng lại kể cả khi có lỗi**. Bạn sẽ thấy `with pool.connection() as conn:` rất nhiều ở Bài 05.

```python
with open("scripts/tam.txt", "w", encoding="utf-8") as f:
    f.write("xin chào")
# ra khỏi khối with, file đã tự đóng

with open("scripts/tam.txt", encoding="utf-8") as f:
    print(f.read())
```

**3e. Decorator.** Decorator là cú pháp `@...` đặt trên hàm để "đăng ký" hoặc "bọc" hàm. FastAPI dùng `@app.get("/health")` để nói: "khi có request GET /health thì gọi hàm này".

```python
routes = {}


def route(path):
    def dang_ky(func):
        routes[path] = func
        return func
    return dang_ky


@route("/health")
def health():
    return {"status": "ok"}


print(routes["/health"]())  # {'status': 'ok'}
```

Đây chính là cách FastAPI hoạt động bên trong, chỉ đơn giản hơn nhiều.

Chạy:

```bash
python scripts/on_python.py
```

Rồi xóa file tạm:

```bash
rm scripts/tam.txt
```

### Bước 4: Hiểu async/await, chạy nhiều việc cùng lúc

Khi gọi API, phần lớn thời gian chương trình chỉ **ngồi chờ mạng**. `async/await` cho phép trong lúc chờ việc này thì làm việc khác. Ở Bài 17, script benchmark dùng async để gửi hàng chục request **đồng thời**.

Tạo file `scripts/thu_async.py`:

```python
import asyncio
import time

import httpx


async def goi(client: httpx.AsyncClient, i: int) -> int:
    # httpbin chờ 1 giây rồi mới trả lời
    resp = await client.get("https://httpbin.org/delay/1")
    print(f"Request {i} xong: {resp.status_code}")
    return resp.status_code


async def main():
    async with httpx.AsyncClient(timeout=30) as client:
        start = time.perf_counter()
        # Gửi 5 request cùng lúc
        await asyncio.gather(*(goi(client, i) for i in range(5)))
        print(f"Tổng thời gian: {time.perf_counter() - start:.1f} giây")


asyncio.run(main())
```

Chạy:

```bash
python scripts/thu_async.py
```

Mỗi request mất khoảng 1 giây, nhưng 5 request **tổng cộng chỉ mất khoảng 1–2 giây** chứ không phải 5 giây. Đó là sức mạnh của async.

🧠 **Hiểu sâu:**

- `async def` khai báo một **coroutine**, tức là hàm có thể tạm dừng.
- `await` nghĩa là "chờ việc này xong. Trong lúc chờ, cho việc khác chạy".
- `asyncio.gather(...)` chạy nhiều coroutine cùng lúc và đợi tất cả xong.
- Trong app FastAPI của dự án, ta sẽ dùng hàm **thường** (`def`), vì thư viện database và LLM ta dùng là loại đồng bộ. FastAPI tự chạy hàm `def` trong một nhóm thread (threadpool), nên vẫn phục vụ được nhiều người cùng lúc. Đọc bài [FastAPI async](https://fastapi.tiangolo.com/async/) để hiểu khi nào dùng `def`, khi nào dùng `async def`.

### Bước 5: Thử biến môi trường

```bash
export TEN_CUA_HANG="Tiện Lợi 24h"
```

```bash
python -c "import os; print(os.environ.get('TEN_CUA_HANG'))"
```

```bash
python -c "import os; print(os.environ.get('KHONG_TON_TAI', 'giá trị mặc định'))"
```

`export` chỉ có tác dụng trong **cửa sổ terminal hiện tại**. Đó là lý do ta sẽ dùng file `.env` ở Bài 03.

### Bước 6: Commit

```bash
git add scripts/
```

```bash
git commit -m "Bài 02: thực hành HTTP, JSON, async"
```

```bash
git push
```

---

## Kiểm tra kết quả

- [ ] `curl -i https://httpbin.org/status/404` hiện `404`.
- [ ] `scripts/thu_http.py` in được dữ liệu server nhận và bắt được lỗi 500.
- [ ] `scripts/thu_async.py` chạy 5 request trong khoảng 1–2 giây.
- [ ] Bạn trả lời được: status code `422` và `503` khác nhau thế nào?

## Lỗi thường gặp

| Lỗi | Nguyên nhân | Cách sửa |
|---|---|---|
| `ModuleNotFoundError: No module named 'httpx'` | Chưa kích hoạt venv hoặc chưa cài | `source .venv/bin/activate` rồi `pip install httpx` |
| `httpx.ReadTimeout` | Mạng chậm, hoặc httpbin.org đang quá tải | Thử lại, hoặc tăng `timeout=` |
| `json.decoder.JSONDecodeError` | Server không trả JSON (ví dụ trang HTML báo lỗi) | In `resp.text` ra để xem server thật sự trả gì |
| `curl: (6) Could not resolve host` | Mất mạng hoặc gõ sai tên miền | Kiểm tra mạng và URL |

## Bài tập

1. Dùng `curl` gọi `https://httpbin.org/headers` với header tự đặt `-H "X-API-Key: abc123"`. Tìm header đó trong kết quả.
2. Viết hàm Python `re_nhat(san_pham: list[dict]) -> dict` trả về sản phẩm có `gia` nhỏ nhất. Thử với 3 sản phẩm.
3. Sửa `thu_async.py` để gửi 20 request nhưng **tối đa 5 request cùng lúc**. Gợi ý: dùng `asyncio.Semaphore(5)`. Đây chính là kỹ thuật dùng trong script benchmark ở Bài 17.
4. Giải thích bằng lời của bạn: tại sao không nên viết API key thẳng vào file `.py`?

## Checklist hoàn thành

- [ ] Hiểu request/response, method, status code, header, body
- [ ] Đọc và viết được JSON, đổi qua lại với `dict` Python
- [ ] Gọi được API bằng `curl` và `httpx`
- [ ] Hiểu type hint, `**kwargs`, `try/except`, `with`, decorator
- [ ] Hiểu async/await chạy đồng thời thế nào
- [ ] Đã commit và push

➡️ Tiếp theo: [Bài 03: LLM là gì, gọi API Gemini lần đầu](bai-03-llm-co-ban.md)
