# Nhánh lời giải

Nhánh `loi-giai` chứa **code hoàn chỉnh của dự án ở trạng thái cuối khóa học** (sau Bài 17), để bạn đối chiếu khi tự làm theo [khóa học](docs/khoa-hoc/00-muc-luc.md).

## Nhánh này có gì

- Toàn bộ code của các bài 01–17: `src/agent/`, `db/init/`, `data/knowledge/`, `scripts/`, `tests/`, `eval/`, `benchmark/`, `monitoring/`, `deploy/`, `Dockerfile`, `compose.yaml`, `.github/workflows/ci.yml`.
- Các script thực hành trong `scripts/` (Bài 02–07), giữ nguyên như trong bài.

## Nhánh này không có gì

- **Lời giải phần "Bài tập"** cuối mỗi bài. Phần đó để bạn tự làm.
- File `.env` (bí mật). Hãy tạo từ `.env.example`.
- `benchmark/BAO_CAO.md`: báo cáo với số liệu do chính bạn đo ở Bài 17.

## Lưu ý: code ở đây là trạng thái CUỐI khóa

Nhiều file được xây dần qua nhiều bài. Ví dụ `agent.py` có bộ nhớ từ Bài 08, có metric từ Bài 13. Khi đang ở giữa khóa học, file của bạn **sẽ khác** lời giải ở những phần thuộc các bài sau. Đó là bình thường. Với trạng thái giữa chừng, hãy đối chiếu với **nội dung bài học**.

## Cách đối chiếu

Lấy nhánh lời giải về máy (không ảnh hưởng code của bạn):

```bash
git fetch origin loi-giai
```

So sánh **một file** của bạn với lời giải:

```bash
git diff origin/loi-giai -- src/agent/tools.py
```

Dòng bắt đầu bằng `-` là của lời giải, `+` là của bạn. Thêm `--stat` để xem nhanh những file nào khác nhau:

```bash
git diff --stat origin/loi-giai -- src/ tests/
```

Xem nguyên nội dung một file trong lời giải:

```bash
git show origin/loi-giai:src/agent/agent.py
```

Chạy thử lời giải trong một thư mục riêng, không đụng đến code của bạn:

```bash
git worktree add ../project_agent_loi_giai origin/loi-giai
```

```bash
cd ../project_agent_loi_giai && python3 -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]" && pytest
```

Xong thì xóa thư mục đó:

```bash
cd ../project_agent && git worktree remove ../project_agent_loi_giai
```

> ⚠️ **Không merge nhánh `loi-giai` vào nhánh `main` của bạn.** Làm vậy sẽ ghi đè code bạn tự viết. Ngoài ra, sau Bài 15, mỗi lần đẩy code lên `main` đều tự động deploy lên máy chủ.

## Đã kiểm tra

- `ruff check .` không báo lỗi; `pytest` qua 13 test.
- Hệ thống chạy được bằng Docker Compose (pgvector, app, Prometheus, Grafana) với LLM giả lập; RAG, các tool, bộ nhớ, chuyển nhân viên, API quản trị, metric, benchmark, eval, Nginx (rate limit) và sao lưu/khôi phục đều chạy được.
- Chưa kiểm tra với Gemini API thật, vLLM trên GPU thật và VPS thật.
