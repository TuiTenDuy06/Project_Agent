# Bài 09: Giao diện chat web

## Mục tiêu

Sau bài này bạn sẽ:

- Hiểu HTML, CSS, JavaScript ở mức đủ để làm một trang chat đơn giản.
- Gọi API `/chat` từ trình duyệt bằng `fetch`.
- Lưu `session_id` trong trình duyệt bằng `localStorage`.
- Hiểu lỗ hổng **XSS** và cách tránh.
- Cho FastAPI phục vụ trang web (static files).

## Kiến thức cần học

| Chủ đề | Tài liệu |
|---|---|
| HTML cơ bản | [MDN: Getting started with HTML](https://developer.mozilla.org/en-US/docs/Learn/HTML/Introduction_to_HTML/Getting_started) |
| CSS cơ bản | [MDN: CSS first steps](https://developer.mozilla.org/en-US/docs/Learn/CSS/First_steps) |
| Flexbox | [CSS-Tricks: A Complete Guide to Flexbox](https://css-tricks.com/snippets/css/a-guide-to-flexbox/) |
| JavaScript cơ bản | [javascript.info](https://javascript.info/), Phần 1, chương 1–6 |
| fetch API | [MDN: Using the Fetch API](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch) |
| XSS | [OWASP: Cross Site Scripting](https://owasp.org/www-community/attacks/xss/) |
| FastAPI static files | [FastAPI: Static Files](https://fastapi.tiangolo.com/tutorial/static-files/) |

---

## Phần lý thuyết

### 1. Ba ngôn ngữ của trang web

- **HTML**: **cấu trúc**, tức trang có những gì (tiêu đề, khung tin nhắn, ô nhập, nút gửi).
- **CSS**: **trình bày**, tức màu sắc, kích thước, bố cục.
- **JavaScript**: **hành vi**, tức khi bấm nút thì gửi tin nhắn và hiện câu trả lời.

Cả ba được trình duyệt tải về và chạy **trên máy khách hàng**. Python của bạn chạy **trên server**.

### 2. Luồng hoạt động

```
[Trình duyệt]                              [Server FastAPI]
GET /  ─────────────────────────────────▶  trả file index.html
Khách gõ câu hỏi, bấm Gửi
fetch POST /chat {session_id, message} ─▶  run_agent(...)
hiện câu trả lời  ◀──────────────────────  {reply, tools_used}
```

Trang web và API **cùng một địa chỉ** (cùng "origin"), nên không cần cấu hình CORS. Bài 12 sẽ giải thích CORS khi cần nhúng chat vào trang web khác.

### 3. `session_id` lưu ở đâu?

Lần đầu khách vào trang, JavaScript tạo một mã ngẫu nhiên (UUID) và lưu vào **`localStorage`**, tức bộ nhớ nhỏ của trình duyệt dành riêng cho trang này. Lần sau khách quay lại, mã vẫn còn, nên agent nhớ hội thoại cũ.

### 4. XSS: lỗ hổng khi hiển thị nội dung

Nếu hiển thị tin nhắn bằng `div.innerHTML = text`, và `text` là `<img src=x onerror="alert('hack')">`, trình duyệt sẽ **chạy đoạn mã đó**. Đây là **XSS** (Cross-Site Scripting). Kẻ xấu có thể dùng nó để đánh cắp dữ liệu.

Câu trả lời của LLM cũng có thể chứa mã độc, nếu kẻ xấu dụ LLM viết ra. Cách phòng: **luôn dùng `textContent`** để hiển thị chữ. `textContent` coi mọi thứ là chữ thường, không bao giờ chạy mã.

---

## Thực hành từng bước

> Chuẩn bị: `cd ~/project_agent && source .venv/bin/activate`, database đang chạy.

### Bước 1: Tạo trang chat

```bash
mkdir -p src/agent/static
```

Tạo file `src/agent/static/index.html`:

```html
<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Tiện Lợi 24h - Hỗ trợ khách hàng</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 0; background: #f4f4f5; }
    .chat { max-width: 640px; margin: 0 auto; height: 100vh; display: flex; flex-direction: column; background: #fff; }
    header { padding: 16px; background: #16a34a; color: #fff; font-weight: 600; }
    #log { flex: 1; overflow-y: auto; padding: 16px; }
    .msg { margin: 8px 0; padding: 10px 14px; border-radius: 12px; max-width: 80%; white-space: pre-wrap; }
    .user { background: #dcfce7; margin-left: auto; }
    .bot { background: #f4f4f5; }
    .note { font-size: 12px; color: #71717a; text-align: center; padding: 4px 12px 0; }
    form { display: flex; gap: 8px; padding: 12px; border-top: 1px solid #e4e4e7; }
    input { flex: 1; padding: 10px; font-size: 16px; border: 1px solid #d4d4d8; border-radius: 8px; }
    button { padding: 10px 16px; font-size: 16px; border: 0; border-radius: 8px; background: #16a34a; color: #fff; cursor: pointer; }
    button:disabled { opacity: .5; }
  </style>
</head>
<body>
  <div class="chat">
    <header>Tiện Lợi 24h - Hỗ trợ khách hàng</header>
    <div id="log" aria-live="polite"></div>
    <p class="note">Hội thoại được lưu lại để hỗ trợ bạn tốt hơn. Đừng gửi mật khẩu hay số thẻ ngân hàng.</p>
    <form id="form">
      <label for="input" hidden>Tin nhắn</label>
      <input id="input" autocomplete="off" maxlength="1000" placeholder="Nhập câu hỏi..." required>
      <button id="send">Gửi</button>
    </form>
  </div>
  <script>
    const log = document.getElementById("log");
    const form = document.getElementById("form");
    const input = document.getElementById("input");
    const send = document.getElementById("send");

    let sessionId = localStorage.getItem("session_id");
    if (!sessionId) {
      sessionId = crypto.randomUUID();
      localStorage.setItem("session_id", sessionId);
    }

    function addMessage(text, who) {
      const div = document.createElement("div");
      div.className = "msg " + who;
      div.textContent = text; // textContent, không dùng innerHTML: chống chèn mã độc (XSS)
      log.appendChild(div);
      log.scrollTop = log.scrollHeight;
    }

    addMessage("Chào bạn! Mình có thể giúp tra giá, tồn kho, khuyến mãi, cửa hàng và chính sách đổi trả.", "bot");

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const text = input.value.trim();
      if (!text) return;
      addMessage(text, "user");
      input.value = "";
      send.disabled = true;
      try {
        const res = await fetch("/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ session_id: sessionId, message: text }),
        });
        const data = await res.json();
        if (res.ok) addMessage(data.reply, "bot");
        else if (res.status === 429) addMessage("Bạn gửi nhanh quá, đợi một chút rồi thử lại nhé.", "bot");
        else addMessage(data.detail || "Có lỗi xảy ra, bạn thử lại nhé.", "bot");
      } catch {
        addMessage("Không kết nối được máy chủ.", "bot");
      } finally {
        send.disabled = false;
        input.focus();
      }
    });
  </script>
</body>
</html>
```

Đọc hiểu từng phần:

**Phần `<head>`:**

- `<meta charset="utf-8">`: hiển thị đúng tiếng Việt.
- `<meta name="viewport" ...>`: hiển thị đẹp trên điện thoại.
- `<style>`: CSS. `.chat` dùng **flexbox** xếp các phần theo chiều dọc. `#log { flex: 1 }` cho khung tin nhắn chiếm hết chỗ trống. `.user { margin-left: auto }` đẩy tin của khách sang phải.

**Phần `<body>`:**

- `aria-live="polite"`: trình đọc màn hình (cho người khiếm thị) sẽ đọc tin nhắn mới.
- `<label ... hidden>`: nhãn cho ô nhập, ẩn khỏi mắt nhưng trình đọc màn hình vẫn đọc được.
- `maxlength="1000"`: khớp với giới hạn của API. Lưu ý đây chỉ là **tiện lợi cho người dùng**, không phải bảo mật. Kẻ xấu gọi thẳng API vẫn bị Pydantic chặn ở server.

**Phần `<script>`:**

- **`crypto.randomUUID()`**: tạo mã ngẫu nhiên kiểu `3b241101-e2bb-4255-8caf-4136c566a962`. Định dạng này khớp với pattern `^[A-Za-z0-9_-]+$` của API.
- **`addMessage`**: tạo thẻ `div` mới, gán chữ bằng `textContent`, thêm vào khung, cuộn xuống cuối.
- **`form.addEventListener("submit", ...)`**: chạy khi bấm Gửi hoặc nhấn Enter. `e.preventDefault()` ngăn trình duyệt tải lại trang (hành vi mặc định của form).
- **`await fetch(...)`**: gửi POST đến `/chat`. Giống `httpx.post` ở Bài 02 nhưng chạy trong trình duyệt.
- **Xử lý lỗi theo status:** `429` (bị giới hạn tốc độ, Bài 15) có câu riêng; lỗi khác hiện `detail` từ server; mất mạng rơi vào `catch`.
- **`send.disabled = true`**: khóa nút trong lúc chờ, tránh khách bấm nhiều lần gửi trùng.

### Bước 2: Cho FastAPI phục vụ trang web

Mở `src/agent/app.py`.

1. Thêm 2 import ở đầu file:

   ```python
   from pathlib import Path

   from fastapi.staticfiles import StaticFiles
   ```

   Đặt `from pathlib import Path` cạnh các import thư viện chuẩn (`logging`, `contextlib`), và `from fastapi.staticfiles import StaticFiles` cạnh `from fastapi import ...`.

2. Thêm vào **cuối file**:

   ```python
   # Đặt cuối cùng: mọi đường dẫn khác trả về giao diện chat
   app.mount(
       "/", StaticFiles(directory=Path(__file__).parent / "static", html=True), name="web"
   )
   ```

Giải thích:

- `Path(__file__).parent / "static"`: thư mục `static` nằm cạnh file `app.py`. Dùng đường dẫn tương đối theo file nên chạy từ thư mục nào cũng đúng.
- `html=True`: vào `/` thì tự trả `index.html`.
- **Phải đặt cuối cùng**: `mount("/")` khớp với **mọi** đường dẫn. Nếu đặt trước, nó "nuốt" luôn `/chat` và `/health`.

### Bước 3: Đóng gói file HTML cùng code Python

Khi cài dự án vào Docker (Bài 11), Python chỉ copy file `.py` theo mặc định. Phải khai báo để nó copy cả file HTML.

Thêm vào cuối `pyproject.toml`:

```toml
[tool.setuptools.package-data]
agent = ["static/*"]
```

Cài lại:

```bash
pip install -e ".[dev]"
```

### Bước 4: Chạy thử

```bash
uvicorn agent.app:app --reload --port 8080
```

Mở trình duyệt vào **http://localhost:8080**. Thử các câu:

1. "Cửa hàng Quận 1 mở cửa mấy giờ?"
2. "Ở đó còn mì ly Hảo Hảo không?" (kiểm tra bộ nhớ)
3. "Đổi trả hàng thế nào?"
4. `<b>đậm</b><img src=x onerror=alert(1)>` (kiểm tra XSS: chữ phải hiện **nguyên văn**, không có hộp thoại `alert` bật lên)

Tải lại trang (F5): lịch sử trên màn hình mất (ta chưa làm phần tải lại lịch sử), nhưng agent **vẫn nhớ** hội thoại, vì `session_id` còn trong `localStorage`. Hỏi "Mình vừa hỏi gì?" để kiểm tra.

### Bước 5: Dùng công cụ cho lập trình viên (DevTools)

Nhấn **F12** để mở DevTools của trình duyệt:

- Tab **Network**: gửi một tin nhắn, bấm vào request `chat` để xem request body, response và thời gian phản hồi.
- Tab **Console**: xem lỗi JavaScript nếu có.
- Tab **Application** → **Local Storage**: thấy `session_id`. Xóa nó đi rồi tải lại trang, bạn sẽ có hội thoại mới.

Thử thêm chế độ điện thoại: bấm biểu tượng điện thoại/máy tính bảng trên thanh DevTools để xem giao diện ở màn hình nhỏ.

### Bước 6: Commit

```bash
git add src/agent/static/ src/agent/app.py pyproject.toml
```

```bash
git commit -m "Bài 09: giao diện chat web"
```

```bash
git push
```

---

## Kiểm tra kết quả

- [ ] Vào http://localhost:8080 thấy trang chat.
- [ ] Gửi câu hỏi và nhận câu trả lời đúng.
- [ ] Tải lại trang, agent vẫn nhớ ngữ cảnh.
- [ ] Gửi chuỗi HTML độc hại, chữ hiện nguyên văn, không chạy mã.
- [ ] `/health` và `/docs` vẫn hoạt động (không bị trang chat "nuốt").

## Lỗi thường gặp

| Lỗi | Nguyên nhân | Cách sửa |
|---|---|---|
| `/chat` trả `405 Method Not Allowed` | `app.mount("/")` đặt trước các route | Chuyển `app.mount` xuống cuối file |
| `RuntimeError: Directory ... static does not exist` | Sai vị trí thư mục | File phải ở `src/agent/static/index.html` |
| Trang hiện lỗi font tiếng Việt | Thiếu `<meta charset="utf-8">` | Kiểm tra phần `<head>` |
| Bấm Gửi trang bị tải lại | Thiếu `e.preventDefault()` | Kiểm tra lại đoạn `addEventListener` |
| Sửa HTML không thấy thay đổi | Trình duyệt dùng bản cũ trong bộ nhớ đệm (cache) | Nhấn `Ctrl + Shift + R` để tải lại hoàn toàn |

## Bài tập

1. Thêm hiệu ứng "đang trả lời…": hiện một tin nhắn tạm khi chờ, rồi xóa nó khi có câu trả lời.
2. Thêm nút **"Cuộc trò chuyện mới"**: xóa `session_id` trong `localStorage`, tạo mã mới, xóa nội dung khung chat.
3. Đổi màu chủ đạo theo ý bạn (sửa các mã màu `#16a34a`).
4. (Nâng cao) Thêm endpoint `GET /history/{session_id}` trả lịch sử hội thoại, rồi cho trang web gọi nó khi tải để hiện lại tin nhắn cũ. Suy nghĩ: người khác đoán được `session_id` thì có xem trộm được không? Vì sao UUID ngẫu nhiên giúp giảm rủi ro này?

## Checklist hoàn thành

- [ ] Hiểu vai trò của HTML, CSS, JavaScript
- [ ] Trang chat gọi được `/chat` bằng `fetch`
- [ ] Hiểu XSS và luôn dùng `textContent`
- [ ] FastAPI phục vụ trang web, file HTML được khai báo trong `package-data`
- [ ] Đã commit và push

🎉 **Chúc mừng! Bạn đã có một agent chăm sóc khách hàng hoạt động đầy đủ trên máy mình.** Phần tiếp theo sẽ đảm bảo nó **chạy đúng** và **sẵn sàng cho production**.

➡️ Tiếp theo: [Bài 10: Viết test và đánh giá chất lượng agent](bai-10-test-va-eval.md)
