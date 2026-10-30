# Bài 18: Vận hành, chi phí, mở rộng và checklist go-live

## Mục tiêu

Bài cuối không viết nhiều code. Bài này giúp bạn **suy nghĩ như người vận hành hệ thống thật**:

- Tính và **tối ưu chi phí**.
- Biết **mở rộng** hệ thống theo từng nấc khi lượng khách tăng.
- Tăng **độ tin cậy**: hệ thống vẫn phục vụ được khi một phần bị hỏng.
- Có **quy trình xử lý sự cố**.
- Duy trì **vòng cải tiến chất lượng** agent sau khi ra mắt.
- Rà soát **checklist go-live** trước khi mở cho khách thật.

## Kiến thức cần học

| Chủ đề | Tài liệu |
|---|---|
| Vận hành hệ thống tin cậy | [Google SRE Book](https://sre.google/sre-book/table-of-contents/), các chương 1, 4, 6, 15 |
| Postmortem không đổ lỗi | [Google SRE: Postmortem Culture](https://sre.google/sre-book/postmortem-culture/) |
| Mở rộng ứng dụng web | [The Twelve-Factor App](https://12factor.net/) |
| Tối ưu chi phí LLM | [OpenAI: Latency optimization](https://platform.openai.com/docs/guides/latency-optimization) (nhiều mẹo áp dụng chung cho mọi LLM) |
| Bảo vệ dữ liệu cá nhân | Nghị định 13/2023/NĐ-CP về bảo vệ dữ liệu cá nhân |

---

## 1. Chi phí

### Bảng chi phí hằng tháng

Điền số thật của bạn:

| Hạng mục | Cách tính | Ví dụ |
|---|---|---|
| VPS | Giá cố định | 200.000đ |
| Tên miền | Giá năm / 12 | 40.000đ |
| LLM API | Token đầu vào × giá + token đầu ra × giá | Xem panel "Token mỗi giờ" trên Grafana (Bài 13) |
| GPU (nếu tự host) | Giá/giờ × 720 giờ | |
| Sao lưu ngoài máy chủ | Theo dung lượng | Thường rất nhỏ |

**Chi phí cho mỗi cuộc hội thoại** = tổng chi phí / số hội thoại. Đây là con số quan trọng nhất để so sánh với chi phí nhân viên trực chat.

### Các cách giảm chi phí LLM

Sắp xếp từ dễ đến khó:

1. **Rút gọn system prompt và mô tả tool**: chúng được gửi đi trong **mỗi** lần gọi LLM.
2. **Giới hạn lịch sử hội thoại** (`MAX_TURNS`, Bài 08): đã làm.
3. **Giới hạn độ dài trả lời**: thêm `max_tokens` vào `llm.chat()`, và yêu cầu "trả lời ngắn gọn" trong prompt (đã có).
4. **Giới hạn kết quả tool**: `LIMIT 20` trong SQL (đã làm), chỉ trả các cột cần thiết.
5. **Chọn model rẻ hơn**: các bản "flash" / "mini" thường đủ tốt cho chăm sóc khách hàng. Dùng **bộ eval** để kiểm chứng.
6. **Prompt caching**: nhiều nhà cung cấp giảm giá cho phần đầu prompt lặp lại giống nhau (system prompt, mô tả tool). Đọc tài liệu nhà cung cấp của bạn.
7. **Tự host** khi lượng khách đủ lớn (Bài 16–17).

**Luôn đo trước và sau khi tối ưu**: chi phí (Grafana) **và** chất lượng (eval). Tối ưu chi phí mà làm agent trả lời sai là lỗ.

---

## 2. Mở rộng theo từng nấc

Đừng xây hệ thống cho một triệu khách khi mới có một trăm. Hãy mở rộng **khi số liệu giám sát cho thấy cần**.

| Nấc | Khi nào | Làm gì |
|---|---|---|
| **0. Hiện tại** | Vài chục khách cùng lúc | 1 VPS, Docker Compose. Nút thắt thường là **LLM**, không phải app |
| **1. Tăng cấu hình** | CPU/RAM VPS thường xuyên > 70% | Nâng VPS lên cấu hình cao hơn. Đơn giản nhất, không đổi kiến trúc |
| **2. Tách database** | Database chiếm nhiều tài nguyên; cần sao lưu và dự phòng tốt hơn | Dùng PostgreSQL có quản lý (managed): nhà cung cấp lo sao lưu, cập nhật, dự phòng. Chỉ cần đổi `DATABASE_URL` |
| **3. Nhiều bản app** | Một tiến trình app không xử lý kịp | Chạy nhiều container app phía sau Nginx (`upstream`). App của ta **không lưu trạng thái trong bộ nhớ** (lịch sử nằm ở database), nên nhân bản dễ dàng |
| **4. Nhiều máy chủ** | Một máy không đủ, cần chịu được việc mất cả một máy | Load balancer, nhiều VPS, cân nhắc Kubernetes |
| **LLM** | LLM là nút thắt | API: xin tăng hạn mức. Tự host: thêm GPU, dùng kết quả Bài 17 để biết cần bao nhiêu |

🧠 **Hiểu sâu, vì sao app của ta dễ nhân bản?** Nguyên tắc **stateless** (không trạng thái) trong [Twelve-Factor App](https://12factor.net/processes): mọi dữ liệu cần nhớ (lịch sử chat, handoff) nằm trong database, không nằm trong bộ nhớ của tiến trình. Request của cùng một khách đi vào bản app nào cũng được.

> ⚠️ **Lưu ý khi chạy nhiều tiến trình app:** metric Prometheus (Bài 13) được giữ trong bộ nhớ **của từng tiến trình**. Khi chạy nhiều container, cấu hình Prometheus thu thập **từng container** riêng. Khi dùng `uvicorn --workers N` trong một container, cần bật chế độ multiprocess của `prometheus_client`. Đọc [tài liệu multiprocess](https://prometheus.github.io/client_python/multiprocess/) trước khi làm.

---

## 3. Độ tin cậy

### Những gì có thể hỏng và cách ứng phó

| Thành phần hỏng | Hệ quả | Ứng phó |
|---|---|---|
| LLM API chậm hoặc lỗi | Khách chờ lâu, nhận lỗi | `timeout=30`, `max_retries=2` (đã có). Thêm **LLM dự phòng** (bài tập 1) |
| LLM bị giới hạn tốc độ (429) | Lỗi khi đông khách | Xin tăng hạn mức, dự phòng nhà cung cấp khác, rate limit phía Nginx |
| Database sập | Toàn bộ agent không hoạt động | `restart: unless-stopped`, healthcheck, sao lưu, cân nhắc database có quản lý |
| VPS sập | Toàn bộ dịch vụ ngừng | UptimeRobot báo động (Bài 15), snapshot VPS, tài liệu dựng lại máy chủ |
| Bản deploy mới có lỗi | Agent trả lời sai hoặc lỗi | CI chặn trước (Bài 14), rollback bằng `git revert` (Bài 15) |
| Hết dung lượng đĩa | Database không ghi được | Giám sát dung lượng đĩa, xóa backup cũ (đã có), `docker system prune` định kỳ |

### Xuống cấp từ từ (graceful degradation)

Khi một phần hỏng, hệ thống nên **vẫn làm được gì đó có ích** thay vì sập hoàn toàn. Ví dụ đã có trong dự án:

- Tool lỗi thì trả JSON báo lỗi, LLM vẫn trả lời được phần còn lại (Bài 06).
- Agent lỗi thì khách nhận thông báo lịch sự `503`, không phải trang lỗi khó hiểu (Bài 04).

Có thể làm thêm: khi LLM lỗi liên tục, hiện số hotline và giờ làm việc của nhân viên ngay trên trang chat.

---

## 4. Quy trình xử lý sự cố

Ghi quy trình này vào `deploy/HUONG_DAN_VAN_HANH.md` (bài tập 5 của Bài 15) để khi có sự cố không phải suy nghĩ từ đầu.

1. **Phát hiện**: cảnh báo từ Grafana/UptimeRobot, hoặc khách phản ánh.
2. **Đánh giá**: bao nhiêu khách bị ảnh hưởng? Mất hoàn toàn hay chỉ chậm? Bắt đầu từ khi nào? Xem dashboard và `docker compose logs app`.
3. **Giảm thiểu trước, tìm nguyên nhân sau**: ưu tiên làm dịch vụ chạy lại.
   - Vừa deploy? Rollback ngay (`git revert`).
   - LLM lỗi? Chuyển sang LLM dự phòng (đổi `.env`, `docker compose up -d app`).
   - Database đầy hay chết? Xem `docker compose logs db`, dung lượng đĩa `df -h`.
4. **Khắc phục triệt để**: sửa nguyên nhân gốc, viết test để lỗi không lặp lại.
5. **Viết postmortem**: chuyện gì đã xảy ra, dòng thời gian, nguyên nhân gốc, đã làm gì, sẽ làm gì để không lặp lại. **Không đổ lỗi cho người**, mà tìm cách cải thiện **hệ thống** và **quy trình**.

---

## 5. Cải tiến chất lượng liên tục

Ra mắt chỉ là bắt đầu. Agent tốt lên nhờ **vòng lặp**:

```
 Khách dùng thật ──▶ Thu thập: hội thoại, lý do handoff, phản hồi
        ▲                         │
        │                         ▼
   Deploy (CD)          Phân tích: agent sai ở đâu?
        ▲                         │
        │                         ▼
  Eval đạt ◀── Sửa: prompt, tool, tài liệu RAG, thêm ca vào eval
```

**Việc cần làm định kỳ (ví dụ mỗi tuần):**

- Đọc **mẫu ngẫu nhiên** khoảng 20–50 hội thoại trong bảng `messages`. Đánh dấu câu trả lời sai, thiếu, khó hiểu.
- Đọc **lý do handoff** trong bảng `handoffs`. Câu hỏi nào agent đáng lẽ tự trả lời được?
- Xem panel "Tool được gọi mỗi giờ": khách hỏi gì nhiều nhất? Có nhu cầu nào chưa có tool?
- **Cập nhật tài liệu** trong `data/knowledge/` khi chính sách thay đổi, rồi chạy lại `build_index.py`.
- Mỗi lỗi tìm được: **thêm vào `eval/cases.json`** trước, rồi mới sửa. Chạy eval để chắc chắn đã sửa được và không làm hỏng ca khác.

💡 **Thu thập phản hồi:** thêm nút 👍 / 👎 dưới mỗi câu trả lời trên trang chat, lưu vào database. Những câu bị 👎 là nguồn ca eval quý giá nhất.

---

## 6. Pháp lý và trách nhiệm

- **Minh bạch:** cho khách biết họ đang chat với **trợ lý AI**, và có thể yêu cầu gặp nhân viên.
- **Dữ liệu cá nhân:** tìm hiểu và tuân thủ quy định về bảo vệ dữ liệu cá nhân (Nghị định 13/2023/NĐ-CP). Thông báo việc thu thập, mục đích, thời hạn lưu trữ (90 ngày ở Bài 15). Có cách xử lý khi khách yêu cầu xóa dữ liệu.
- **Giới hạn phạm vi:** agent không đưa lời khuyên y tế, pháp lý, tài chính. Quy tắc 1 trong system prompt đã giới hạn chủ đề.
- **Trách nhiệm về thông tin:** giá và khuyến mãi agent nêu phải khớp với hệ thống bán hàng. Đó là lý do mọi con số đều lấy từ tool. Khi tích hợp dữ liệu thật, hãy đảm bảo database được cập nhật từ hệ thống bán hàng thường xuyên.

---

## 7. Checklist go-live

Rà soát **toàn bộ** trước khi mở cho khách thật.

**Chất lượng**
- [ ] Bộ eval có ít nhất 30 tình huống, gồm cả câu tấn công, đạt ≥ 90%
- [ ] Đã thử với 5–10 người thật (nhân viên, bạn bè) và sửa các vấn đề tìm thấy
- [ ] Dữ liệu sản phẩm, cửa hàng, khuyến mãi, tài liệu chính sách là dữ liệu **thật, mới nhất**
- [ ] Đã xóa dữ liệu mẫu (`02_seed.sql`) khỏi production

**Bảo mật**: toàn bộ checklist bảo mật ở Bài 12 đã đạt

**Vận hành**
- [ ] CI xanh, CD hoạt động, đã thử rollback
- [ ] Sao lưu hằng ngày, có bản ngoài máy chủ, **đã thử khôi phục**
- [ ] Dashboard Grafana và các cảnh báo hoạt động
- [ ] UptimeRobot (hoặc tương đương) giám sát từ bên ngoài
- [ ] Có tài liệu vận hành (deploy, rollback, khôi phục, xử lý sự cố)
- [ ] Đã đặt giới hạn chi tiêu cho LLM API

**Con người và quy trình**
- [ ] Có nhân viên nhận và xử lý các yêu cầu handoff, biết dùng `/admin/handoffs`
- [ ] Có người nhận cảnh báo khi hệ thống gặp sự cố
- [ ] Trang chat có thông báo về AI và về việc lưu hội thoại
- [ ] Có kế hoạch rà soát hội thoại định kỳ

**Ra mắt từ từ**
- [ ] Bắt đầu với một nhóm nhỏ (một cửa hàng, hoặc một tỉ lệ nhỏ khách), theo dõi sát 1–2 tuần, rồi mới mở rộng

---

## Bài tập cuối khóa

1. **LLM dự phòng:** sửa `llm.py` để khi gọi LLM chính thất bại (sau khi đã retry), tự gọi sang LLM dự phòng (ví dụ vLLM chính, Gemini dự phòng). Gợi ý: thêm `fallback_base_url`, `fallback_api_key`, `fallback_model` vào `Settings`, tạo client thứ hai, bắt `openai.APIError` trong `chat()`. Viết test bằng monkeypatch cho trường hợp client chính lỗi.
2. **Nút phản hồi:** thêm 👍 / 👎 trên trang chat, endpoint `POST /feedback`, bảng `feedback` trong database, và panel Grafana tỉ lệ 👍.
3. **Tính chi phí thật:** sau 1 tuần chạy, tính chi phí mỗi hội thoại từ số liệu Grafana.
4. **Viết postmortem tập dượt:** cố tình gây một sự cố trên máy thử nghiệm (ví dụ đặt sai `LLM_API_KEY` rồi deploy), xử lý theo quy trình ở mục 4, rồi viết postmortem.
5. **Đọc thêm và tự đánh giá:** đọc lại [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents). Dự án của bạn đang ở mức nào? Nếu làm lại từ đầu, bạn sẽ thiết kế gì khác?

---

## Học tiếp gì sau khóa này?

| Hướng | Chủ đề gợi ý |
|---|---|
| Agent nâng cao | Streaming câu trả lời về trình duyệt; tracing với Langfuse; LLM-as-a-judge; hybrid search cho RAG; agent nhiều bước có lập kế hoạch |
| Backend | SQLAlchemy và Alembic (migration); Redis (cache, hàng đợi); xác thực OAuth2/JWT |
| Hạ tầng | Kubernetes; Terraform (hạ tầng dạng code); load balancing; CDN |
| Serving | Tối ưu vLLM nâng cao (speculative decoding, prefix caching, tensor parallel nhiều GPU); fine-tune model nhỏ cho đúng nghiệp vụ (LoRA) |
| Kênh khách hàng | Tích hợp Zalo OA, Facebook Messenger: nhận tin qua webhook rồi gọi cùng hàm `run_agent` |

---

🎓 **Chúc mừng bạn đã hoàn thành khóa học!**

Từ một repository trống, bạn đã xây dựng, kiểm thử, bảo mật, triển khai, giám sát và đo hiệu năng một hệ thống AI thật. Đó là toàn bộ vòng đời của một sản phẩm phần mềm, và là kỹ năng mà rất nhiều lập trình viên chuyên nghiệp đang dùng hằng ngày.

Hãy tiếp tục cải tiến agent của bạn, và đừng quên: **đo trước, sửa sau, đo lại**.

➡️ Tra cứu: [Phụ lục: thuật ngữ, lỗi thường gặp, tài liệu học thêm](phu-luc.md)
