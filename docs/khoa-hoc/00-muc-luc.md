# Khóa học: Xây dựng Agent chăm sóc khách hàng từ con số 0 đến production

Chào mừng bạn! Khóa học này dẫn bạn từng bước xây một **trợ lý AI chăm sóc khách hàng** cho chuỗi cửa hàng tiện lợi (tên giả định: **Tiện Lợi 24h**), đưa nó lên **máy chủ thật trên Internet**, rồi **tự chạy mô hình AI trên GPU** và **đo hiệu năng (benchmark serving)**.

Cuối khóa, bạn sẽ có:

- Một trang web chat, nơi khách hỏi "Cửa hàng Quận 1 còn sữa tươi không?" và nhận câu trả lời đúng, lấy từ database thật.
- Agent biết tra giá, tồn kho, khuyến mãi, cửa hàng, chính sách đổi trả, và biết chuyển cho nhân viên khi khách khiếu nại.
- Hệ thống chạy trên VPS của bạn, có tên miền, HTTPS, giám sát, sao lưu, tự động deploy khi push code.
- Một bảng số liệu benchmark do chính bạn đo, để biết máy chủ AI chịu được bao nhiêu khách cùng lúc.

---

## Bức tranh tổng thể

Đây là hệ thống bạn sẽ xây. Đừng lo nếu chưa hiểu hết các thuật ngữ. Mỗi ô trong hình sẽ có một bài riêng.

```
  Khách hàng (trình duyệt)
          │  HTTPS
          ▼
  ┌──────────────────┐
  │      Nginx       │  ← Bài 15: tên miền, HTTPS, chặn spam (rate limit)
  └────────┬─────────┘
           │
           ▼
  ┌──────────────────┐      ┌────────────────────────────┐
  │  App FastAPI     │─────▶│  LLM                        │
  │  - /chat         │      │  Giai đoạn 1: Gemini API    │ ← Bài 03
  │  - giao diện web │      │  Giai đoạn 2: vLLM trên GPU │ ← Bài 16
  │  - vòng lặp agent│      └────────────────────────────┘
  │  - các tool      │
  └────────┬─────────┘
           │ SQL
           ▼
  ┌──────────────────┐      ┌────────────────────────────┐
  │  PostgreSQL      │      │  Prometheus + Grafana      │ ← Bài 13
  │  + pgvector      │      │  (giám sát)                │
  │  sản phẩm, tồn   │      └────────────────────────────┘
  │  kho, hội thoại, │
  │  tài liệu RAG    │ ← Bài 05, 07, 08
  └──────────────────┘
```

**Luồng một câu hỏi:**

1. Khách gõ câu hỏi trên trang web.
2. Trang web gửi câu hỏi tới API `/chat` của app.
3. App gửi câu hỏi cùng danh sách "công cụ" (tool) cho LLM.
4. LLM quyết định cần tra cứu gì, ví dụ gọi tool `tim_san_pham`.
5. App chạy tool, tức là truy vấn database, rồi gửi kết quả lại cho LLM.
6. LLM viết câu trả lời dựa trên dữ liệu thật.
7. App lưu hội thoại và trả câu trả lời về trang web.

---

## Lộ trình học

| Phần | Bài | Nội dung | Thời gian gợi ý |
|---|---|---|---|
| **1. Nền tảng** | [Bài 01](bai-01-chuan-bi-moi-truong.md) | Chuẩn bị máy: terminal, Git, GitHub, Python, VS Code, Docker | 3–4 giờ |
| | [Bài 02](bai-02-kien-thuc-web.md) | Kiến thức web: HTTP, REST, JSON, async | 3–4 giờ |
| **2. Xây agent** | [Bài 03](bai-03-llm-co-ban.md) | LLM là gì, gọi API Gemini lần đầu | 3 giờ |
| | [Bài 04](bai-04-fastapi.md) | Viết API bằng FastAPI | 3–4 giờ |
| | [Bài 05](bai-05-postgresql.md) | Database PostgreSQL cho cửa hàng | 4–5 giờ |
| | [Bài 06](bai-06-tool-calling.md) | Tool calling: trái tim của agent | 4–5 giờ |
| | [Bài 07](bai-07-rag.md) | RAG: trả lời theo tài liệu chính sách | 4 giờ |
| | [Bài 08](bai-08-bo-nho-handoff-guardrails.md) | Bộ nhớ hội thoại, chuyển nhân viên, guardrails | 3–4 giờ |
| | [Bài 09](bai-09-giao-dien-chat.md) | Giao diện chat web | 2–3 giờ |
| **3. Chất lượng** | [Bài 10](bai-10-test-va-eval.md) | Viết test và đánh giá chất lượng agent | 4 giờ |
| **4. Production** | [Bài 11](bai-11-docker.md) | Đóng gói bằng Docker | 3–4 giờ |
| | [Bài 12](bai-12-bao-mat.md) | Bảo mật | 3 giờ |
| | [Bài 13](bai-13-logging-monitoring.md) | Logging và giám sát | 3–4 giờ |
| | [Bài 14](bai-14-ci-cd.md) | CI/CD với GitHub Actions | 3 giờ |
| | [Bài 15](bai-15-deploy-vps.md) | Deploy lên VPS: tên miền, HTTPS, sao lưu | 5–6 giờ |
| **5. Serving** | [Bài 16](bai-16-self-host-vllm.md) | Tự chạy LLM bằng vLLM trên GPU | 4 giờ |
| | [Bài 17](bai-17-benchmark-serving.md) | Benchmark serving | 4 giờ |
| | [Bài 18](bai-18-van-hanh.md) | Vận hành, chi phí, mở rộng, checklist go-live | 2–3 giờ |
| **Phụ lục** | [Phụ lục](phu-luc.md) | Thuật ngữ, lỗi thường gặp, tài liệu học thêm | tra cứu |

Tổng cộng khoảng **60–70 giờ**. Nếu học 1–2 giờ mỗi ngày, bạn sẽ xong trong khoảng 6–8 tuần.

---

## Cách học hiệu quả

1. **Học theo thứ tự.** Bài sau dùng code của bài trước. Đừng nhảy cóc.
2. **Tự gõ code, đừng copy-paste.** Gõ lại giúp bạn để ý từng dòng và nhớ lâu hơn rất nhiều. Chỉ copy những file dữ liệu dài (ví dụ dữ liệu mẫu SQL).
3. **Chạy thử sau mỗi bước.** Mỗi bài đều có mục "Kiểm tra kết quả". Đừng sang bước tiếp nếu bước hiện tại chưa chạy.
4. **Gặp lỗi là chuyện bình thường.** Đọc kỹ dòng cuối của thông báo lỗi, xem mục "Lỗi thường gặp" của bài, rồi tra [Phụ lục](phu-luc.md). Nếu vẫn kẹt, copy nguyên văn thông báo lỗi lên Google hoặc hỏi AI.
5. **Commit sau mỗi bài.** Mỗi bài kết thúc bằng một lần `git commit`. Nếu làm hỏng, bạn luôn quay lại được bản chạy tốt gần nhất.
6. **Làm bài tập.** Mục "Bài tập" ở cuối bài là nơi bạn thật sự học. Hướng dẫn chỉ cho bạn thấy đường, còn bài tập bắt bạn tự đi.
7. **Đọc tài liệu chính thức.** Mỗi bài có mục "Kiến thức cần học" kèm link. Hãy tập thói quen đọc tài liệu gốc, vì đó là kỹ năng quan trọng nhất của lập trình viên.

---

## Kiến thức cần có trước khi bắt đầu

Khóa học giả định bạn **biết Python cơ bản**:

- Biến, kiểu dữ liệu: `str`, `int`, `float`, `bool`, `list`, `dict`.
- `if`, `for`, `while`.
- Viết và gọi hàm, tham số mặc định.
- `import` module, cài thư viện bằng `pip`.
- Đọc hiểu thông báo lỗi `Traceback` cơ bản.

Tự kiểm tra: bạn có viết được hàm nhận vào một `list` các `dict` sản phẩm và trả về sản phẩm rẻ nhất không? Nếu chưa, hãy học trước:

- [Python Tutorial chính thức](https://docs.python.org/3/tutorial/), chương 3 đến 6.
- Hoặc khóa miễn phí [Python for Everybody](https://www.py4e.com/), chương 1 đến 10.

Những thứ **không cần biết trước**: web, database, Docker, Linux, AI. Khóa học sẽ dạy hết.

---

## Chi phí dự kiến

| Hạng mục | Chi phí | Khi nào cần |
|---|---|---|
| Gemini API (gói miễn phí) | 0đ | Bài 03 trở đi |
| GitHub | 0đ | Bài 01 trở đi |
| VPS 2 CPU, 4GB RAM | khoảng 100.000–250.000đ/tháng | Bài 15 |
| Tên miền `.com` hoặc `.vn` | khoảng 250.000–800.000đ/năm | Bài 15 (có thể dùng tên miền miễn phí để học) |
| GPU thuê theo giờ (RTX 4090 / A10 / L4) | khoảng 0,3–1 USD/giờ | Bài 16–17, chỉ bật khi dùng |

> **Lưu ý về GPU:** thuê GPU tính tiền **theo giờ, kể cả khi bạn không dùng**. Học xong nhớ **tắt (stop) hoặc xóa (terminate)** máy, nếu không tiền sẽ chạy liên tục.

---

## Quy ước trong khóa học

- Khối lệnh có nhãn `bash` là lệnh gõ trong **terminal**. Gõ từng lệnh rồi nhấn Enter.
- Không gõ chữ `$` ở đầu dòng (nếu có).
- Khối có nhãn `python`, `sql`, `yaml`… là **nội dung file**. Dòng ngay trên khối luôn nói rõ tên file, ví dụ: "Tạo file `src/agent/config.py`:".
- Đường dẫn file luôn tính từ **thư mục gốc dự án** `project_agent/`.
- `<...>` là chỗ bạn thay bằng giá trị của mình. Ví dụ `<ten-cua-ban>` thành `duy`.
- Các ô ghi chú:
  - **💡 Mẹo:** cách làm nhanh hoặc hay hơn.
  - **⚠️ Cảnh báo:** làm sai có thể mất dữ liệu, mất tiền hoặc lộ bí mật.
  - **🧠 Hiểu sâu:** giải thích thêm, đọc nếu bạn tò mò.

---

## Cấu trúc dự án khi hoàn thành

```
project_agent/
├── README.md
├── pyproject.toml              # Khai báo dự án và thư viện (Bài 03)
├── .env.example                # Mẫu biến môi trường (Bài 03)
├── .gitignore                  # (Bài 01)
├── compose.yaml                # Docker Compose: db, app, giám sát (Bài 05, 11, 13)
├── Dockerfile                  # (Bài 11)
├── .dockerignore               # (Bài 11)
├── .github/workflows/ci.yml    # CI/CD (Bài 14)
├── db/init/                    # Các file SQL tạo bảng và dữ liệu mẫu (Bài 05, 07, 08)
├── data/knowledge/             # Tài liệu chính sách cho RAG (Bài 07)
├── src/agent/
│   ├── config.py               # Đọc cấu hình (Bài 03)
│   ├── llm.py                  # Gọi LLM và embedding (Bài 03, 07)
│   ├── app.py                  # API FastAPI (Bài 04 trở đi)
│   ├── db.py                   # Kết nối database (Bài 05)
│   ├── tools.py                # Các tool của agent (Bài 06–08)
│   ├── agent.py                # Vòng lặp agent (Bài 06, 08, 13)
│   ├── prompts.py              # System prompt (Bài 06, 08)
│   ├── rag.py                  # Tìm kiếm tài liệu (Bài 07)
│   ├── memory.py               # Bộ nhớ hội thoại (Bài 08)
│   ├── logging_config.py       # Log dạng JSON, che dữ liệu cá nhân (Bài 13)
│   └── static/index.html       # Giao diện chat (Bài 09)
├── scripts/                    # Script tiện ích (Bài 03, 05, 07)
├── tests/                      # Test tự động (Bài 10)
├── eval/                       # Đánh giá chất lượng agent (Bài 10)
├── monitoring/                 # Cấu hình Prometheus (Bài 13)
├── deploy/                     # Cấu hình Nginx, script sao lưu (Bài 15)
└── benchmark/                  # Benchmark serving (Bài 17)
```

Sẵn sàng chưa? Bắt đầu với [Bài 01: Chuẩn bị môi trường](bai-01-chuan-bi-moi-truong.md).
