# Bài 14: CI/CD với GitHub Actions

## Mục tiêu

Sau bài này bạn sẽ:

- Hiểu **CI** (Continuous Integration) và **CD** (Continuous Deployment) là gì.
- Viết workflow **GitHub Actions** tự động chạy ruff, pytest và build Docker mỗi lần push.
- Làm việc theo quy trình chuyên nghiệp: **nhánh → pull request → CI xanh → merge**.
- Bảo vệ nhánh `main`: không cho merge code làm hỏng test.

Phần **CD** (tự động deploy lên máy chủ) cần có máy chủ trước, nên sẽ hoàn thành ở cuối Bài 15.

## Kiến thức cần học

| Chủ đề | Tài liệu |
|---|---|
| GitHub Actions | [GitHub Actions: Quickstart](https://docs.github.com/en/actions/writing-workflows/quickstart) |
| Cú pháp workflow | [Workflow syntax](https://docs.github.com/en/actions/writing-workflows/workflow-syntax-for-github-actions) |
| YAML | [Learn YAML in Y minutes](https://learnxinyminutes.com/docs/yaml/) |
| Pull request | [GitHub: About pull requests](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests) |
| Bảo vệ nhánh | [About protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches) |

---

## Phần lý thuyết

### 1. CI là gì?

**Continuous Integration (tích hợp liên tục):** mỗi lần có code mới, một máy chủ **tự động** kiểm tra: code có lỗi cú pháp không, test có đạt không, build được không. Lỗi được phát hiện **ngay**, khi bạn còn nhớ mình vừa sửa gì, chứ không phải vài tuần sau khi khách phàn nàn.

### 2. CD là gì?

**Continuous Deployment (triển khai liên tục):** khi CI đạt trên nhánh `main`, code **tự động** được đưa lên máy chủ. Không còn cảnh SSH vào máy chủ gõ lệnh tay, vốn dễ quên bước và dễ gõ nhầm.

```
 Bạn push code ──▶ GitHub Actions:
                   1. ruff check     ─┐
                   2. pytest          ├─ CI: đạt hết mới đi tiếp
                   3. docker build   ─┘
                   4. SSH vào VPS, pull code, chạy lại container  ← CD (Bài 15)
```

### 3. GitHub Actions

GitHub cho bạn **máy ảo miễn phí** (có giới hạn số phút mỗi tháng) để chạy các bước tự động. Bạn mô tả các bước trong file YAML đặt ở thư mục `.github/workflows/`.

**Các khái niệm:**

- **Workflow**: một quy trình tự động (một file YAML).
- **Trigger** (`on`): sự kiện kích hoạt workflow: push, pull request, lịch hẹn giờ…
- **Job**: một nhóm bước chạy trên **một máy ảo**. Các job chạy song song, trừ khi khai báo `needs` để chạy nối tiếp.
- **Step**: một bước, có thể là lệnh shell (`run`) hoặc một **action** có sẵn (`uses`).
- **Secret**: biến bí mật (SSH key, mật khẩu) lưu mã hóa trên GitHub, không hiện trong log.

### 4. Quy trình làm việc với nhánh

Đừng sửa code thẳng trên `main`. Quy trình chuẩn:

1. Tạo nhánh mới cho mỗi tính năng: `git switch -c them-tool-danh-muc`.
2. Code, commit, push nhánh lên GitHub.
3. Tạo **Pull Request** (PR): đề nghị gộp nhánh vào `main`.
4. CI tự chạy trên PR. **Xanh** = đạt, **đỏ** = có lỗi.
5. Xem lại thay đổi (tự review, hoặc nhờ người khác).
6. CI xanh thì **Merge**. Nhánh `main` luôn ở trạng thái chạy được.

---

## Thực hành từng bước

> Chuẩn bị: `cd ~/project_agent && source .venv/bin/activate`. Đảm bảo `pytest` và `ruff check .` đều đạt trên máy bạn trước.

### Bước 1: Viết workflow CI

```bash
mkdir -p .github/workflows
```

Tạo file `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Lấy code
        uses: actions/checkout@v4

      - name: Cài Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
          cache-dependency-path: pyproject.toml

      - name: Cài thư viện
        run: pip install -e ".[dev]"

      - name: Kiểm tra code (ruff)
        run: ruff check .

      - name: Chạy test
        run: pytest

      - name: Build Docker image
        run: docker build -t project-agent .
```

Giải thích:

- **`on`**: chạy khi push lên `main`, và khi có pull request vào bất kỳ nhánh nào.
- **`runs-on: ubuntu-latest`**: chạy trên máy ảo Ubuntu, đã cài sẵn Docker.
- **`actions/checkout@v4`**: action có sẵn, tải code của repository về máy ảo.
- **`actions/setup-python@v5`**: cài Python 3.12. `cache: pip` lưu thư viện đã tải giữa các lần chạy cho nhanh. `cache-dependency-path` cho biết dựa vào file nào để biết khi nào cần làm mới cache.
- **Thứ tự các bước**: ruff (nhanh nhất) → pytest → docker build (chậm nhất). Bước nào lỗi thì dừng ngay, không chạy bước sau.
- **Không cần API key hay database**: unit test dùng LLM giả (Bài 10), và `tests/conftest.py` đặt sẵn key giả.

🧠 **Hiểu sâu, `@v4`, `@v5`:** đây là phiên bản của action. Luôn ghim phiên bản, đừng dùng `@main`. Lý do: người viết action có thể thay đổi code bất cứ lúc nào, kể cả theo hướng độc hại. Các tổ chức rất cẩn trọng còn ghim theo mã commit đầy đủ (SHA).

### Bước 2: Push và xem CI chạy

```bash
git add .github/
```

```bash
git commit -m "Bài 14: CI với GitHub Actions"
```

```bash
git push
```

Vào trang repository trên GitHub → tab **Actions**. Bạn sẽ thấy workflow "CI" đang chạy (vòng tròn vàng). Bấm vào để xem từng bước và log. Sau khoảng 2–3 phút, nó chuyển sang **dấu tích xanh** ✅.

### Bước 3: Thử làm CI đỏ

Ta cố tình làm hỏng code để xem CI bắt lỗi thế nào, **trên một nhánh riêng**:

```bash
git switch -c thu-ci-do
```

Mở `src/agent/agent.py`, đổi `MAX_STEPS = 5` thành `MAX_STEPS = 0`.

```bash
git commit -am "Thử làm hỏng test"
```

```bash
git push -u origin thu-ci-do
```

Trên GitHub sẽ hiện thông báo **"Compare & pull request"**. Bấm vào, rồi bấm **Create pull request**.

Ở trang PR, đợi CI chạy xong: dấu **X đỏ** ❌. Bấm **Details** để xem: bước "Chạy test" thất bại, log chỉ rõ test nào trượt.

Sửa lại cho đúng:

```bash
git restore --source=main src/agent/agent.py
```

```bash
git commit -am "Sửa lại MAX_STEPS"
```

```bash
git push
```

CI tự chạy lại trên PR và chuyển xanh. Lúc này bạn có thể **đóng PR** (Close pull request), vì đây chỉ là thử nghiệm. Quay về `main` và xóa nhánh thử:

```bash
git switch main
```

```bash
git branch -D thu-ci-do
```

```bash
git push origin --delete thu-ci-do
```

### Bước 4: Bảo vệ nhánh `main`

Trên GitHub: tab **Settings** → **Branches** (hoặc **Rules** → **Rulesets**) → **Add branch ruleset** / **Add rule**:

1. Áp dụng cho nhánh `main`.
2. Bật **Require a pull request before merging**: không push thẳng lên `main` được nữa.
3. Bật **Require status checks to pass**, thêm check `test` (tên job trong workflow): PR chỉ merge được khi CI xanh.
4. Lưu lại.

Từ giờ, mọi thay đổi đi qua PR và phải qua CI. Nhánh `main` luôn chạy được, và đó là điều kiện để bật **tự động deploy** ở Bài 15.

> 💡 Với repository **private** trên gói GitHub miễn phí, một số tính năng bảo vệ nhánh có thể bị giới hạn. Nếu không bật được, hãy tự giữ kỷ luật: luôn làm trên nhánh riêng, chỉ merge khi CI xanh.

### Bước 5: Quy trình làm việc hằng ngày (từ giờ trở đi)

```bash
git switch main
```

```bash
git pull
```

```bash
git switch -c <ten-tinh-nang>
```

Code, chạy `pytest` và `ruff check .` trên máy, rồi:

```bash
git add <file>
```

```bash
git commit -m "<mô tả>"
```

```bash
git push -u origin <ten-tinh-nang>
```

Tạo PR trên GitHub, đợi CI xanh, Merge, rồi xóa nhánh.

---

## Kiểm tra kết quả

- [ ] Tab Actions có workflow CI chạy xanh trên `main`.
- [ ] Đã thấy CI đỏ trên PR khi test hỏng, và xanh lại khi sửa.
- [ ] Nhánh `main` được bảo vệ (hoặc bạn đã nắm quy trình PR).

## Lỗi thường gặp

| Lỗi | Nguyên nhân | Cách sửa |
|---|---|---|
| Workflow không chạy | File sai vị trí hoặc sai đuôi | Phải là `.github/workflows/ci.yml` (có dấu chấm ở đầu `.github`) |
| `Invalid workflow file` | Lỗi thụt lề YAML | YAML dùng **dấu cách**, không dùng Tab. Kiểm tra từng cấp thụt lề |
| `ValidationError ... llm_api_key` trong CI | Thiếu `tests/conftest.py` | Kiểm tra file đã được commit |
| Test đạt trên máy nhưng trượt trên CI | Test phụ thuộc vào thứ chỉ có trên máy bạn (`.env`, database, file chưa commit) | Kiểm tra `git status` xem quên commit file nào không |
| `ruff check` trượt trên CI | Quên chạy ruff trên máy trước khi push | Chạy `ruff check . --fix` trên máy |

## Bài tập

1. Thêm một bước chạy `pip-audit` vào workflow (nhớ cài nó trước trong một bước `run`). Nên để bước này làm **đỏ** CI hay chỉ cảnh báo? Gợi ý: tìm hiểu `continue-on-error: true`.
2. Thêm trigger `schedule` để CI tự chạy mỗi thứ Hai, phát hiện thư viện mới có lỗ hổng. Gợi ý: `on: schedule: - cron: "0 1 * * 1"`.
3. Thêm huy hiệu (badge) trạng thái CI vào `README.md`. Gợi ý: tab Actions → chọn workflow → nút **...** → **Create status badge**.
4. (Nâng cao) Tìm hiểu cách đẩy image Docker lên **GitHub Container Registry (GHCR)** trong CI, để máy chủ chỉ cần tải image về thay vì tự build.

## Checklist hoàn thành

- [ ] Hiểu CI, CD, workflow, job, step, secret
- [ ] CI chạy ruff, pytest, docker build mỗi lần push và PR
- [ ] Làm việc theo quy trình nhánh → PR → CI xanh → merge
- [ ] Đã commit và push

➡️ Tiếp theo: [Bài 15: Deploy lên VPS](bai-15-deploy-vps.md)
