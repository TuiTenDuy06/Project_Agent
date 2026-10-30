# Bài 11: Đóng gói bằng Docker

## Mục tiêu

Sau bài này bạn sẽ:

- Hiểu các khái niệm Docker: **image, container, layer, volume, network**.
- Viết **Dockerfile** cho app Python, chạy bằng user thường (không phải root).
- Dùng **Docker Compose** chạy cả database và app bằng một lệnh.
- Biết các lệnh Docker hằng ngày: xem log, vào container, chạy lệnh một lần.

## Kiến thức cần học

| Chủ đề | Tài liệu |
|---|---|
| Docker tổng quan | [Docker: Get started](https://docs.docker.com/get-started/) |
| Dockerfile | [Dockerfile reference](https://docs.docker.com/reference/dockerfile/) |
| Best practices | [Docker: Building best practices](https://docs.docker.com/build/building/best-practices/) |
| Compose | [Compose file reference](https://docs.docker.com/reference/compose-file/) |
| Mạng trong Compose | [Networking in Compose](https://docs.docker.com/compose/how-tos/networking/) |

---

## Phần lý thuyết

### 1. Vấn đề "máy tôi chạy được mà"

App của bạn chạy trên máy bạn vì máy bạn có đúng Python 3.12, đúng thư viện, đúng cấu hình. Lên máy chủ, mọi thứ có thể khác và app hỏng. **Docker đóng gói app cùng mọi thứ nó cần** vào một "hộp" chạy giống hệt nhau ở mọi nơi.

### 2. Các khái niệm

| Khái niệm | Giải thích | Ví dụ đời thường |
|---|---|---|
| **Image** | Bản đóng gói **chỉ đọc**: hệ điều hành tối giản, Python, thư viện, code | Đĩa cài phần mềm |
| **Container** | Một **phiên bản đang chạy** của image | Phần mềm đang chạy |
| **Dockerfile** | File **công thức** để tạo image | Công thức nấu ăn |
| **Layer** | Mỗi lệnh trong Dockerfile tạo một lớp. Lớp không đổi thì Docker dùng lại (cache) | Các bước nấu đã làm sẵn |
| **Volume** | Ổ lưu dữ liệu **bền vững**, không mất khi xóa container | Ổ cứng gắn ngoài |
| **Network** | Mạng riêng giữa các container. Chúng gọi nhau bằng **tên service** | Mạng LAN trong nhà |
| **Compose** | Chạy **nhiều container** cùng lúc từ một file YAML | Bản nhạc cho cả dàn nhạc |

### 3. Container là "dùng xong vứt"

Container nên được coi là **có thể xóa bất cứ lúc nào**. Mọi dữ liệu cần giữ (database) phải nằm trong **volume**. Code mới thì build image mới rồi thay container, chứ không sửa code bên trong container đang chạy.

### 4. Vì sao không chạy bằng root?

Mặc định, chương trình trong container chạy bằng **root** (quyền cao nhất). Nếu kẻ xấu khai thác được lỗ hổng trong app, họ có quyền root trong container, dễ leo thang ra ngoài hơn. Chạy bằng **user thường** giảm thiệt hại khi có sự cố.

---

## Thực hành từng bước

> Chuẩn bị: `cd ~/project_agent`, Docker đang chạy.

### Bước 1: Viết Dockerfile

Tạo file `Dockerfile` ở thư mục gốc:

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml ./
COPY src ./src
RUN pip install .

COPY scripts ./scripts
COPY data ./data
COPY eval ./eval

RUN useradd --create-home appuser
USER appuser

EXPOSE 8080
CMD ["uvicorn", "agent.app:app", "--host", "0.0.0.0", "--port", "8080"]
```

Giải thích từng dòng:

| Dòng | Ý nghĩa |
|---|---|
| `FROM python:3.12-slim` | Bắt đầu từ image có sẵn Python 3.12. Bản `slim` nhỏ gọn hơn (khoảng 150MB thay vì 1GB) |
| `PYTHONDONTWRITEBYTECODE=1` | Không tạo file `.pyc` thừa |
| `PYTHONUNBUFFERED=1` | In log **ngay lập tức**, không giữ lại trong bộ đệm. Thiếu dòng này, `docker logs` có thể không hiện log |
| `PIP_NO_CACHE_DIR=1` | pip không giữ file cache, giúp image nhỏ hơn |
| `WORKDIR /app` | Thư mục làm việc trong container |
| `COPY ... RUN pip install .` | Copy code và cài dự án cùng thư viện. Không dùng `-e` (editable), vì trong image code không thay đổi |
| `COPY scripts data eval` | Các script, tài liệu RAG và bộ eval, để chạy được `build_index.py` và `run_eval.py` trong container |
| `useradd ... USER appuser` | Tạo user thường và chuyển sang user đó |
| `EXPOSE 8080` | Ghi chú rằng app nghe cổng 8080 |
| `CMD [...]` | Lệnh chạy khi container khởi động. **Không có `--reload`**, vì đó chỉ dành cho lúc phát triển |

🧠 **Hiểu sâu, `--host 0.0.0.0`:** mặc định uvicorn chỉ nhận kết nối từ `127.0.0.1`, tức chính container. Muốn nhận kết nối từ bên ngoài container thì phải nghe trên `0.0.0.0` (mọi địa chỉ). Việc **chặn** truy cập từ Internet được làm ở tầng `ports` của Compose và ở firewall (Bài 15).

🧠 **Hiểu sâu, tối ưu cache:** mỗi lần sửa code trong `src/`, Docker phải chạy lại `pip install .` và tải lại mọi thư viện, khá chậm. Dự án lớn thường tách bước "cài thư viện" ra trước bước "copy code" để tận dụng cache. Với dự án này, build vẫn chỉ mất khoảng 1 phút, nên ta giữ Dockerfile đơn giản.

### Bước 2: Tạo `.dockerignore`

Giống `.gitignore`, nhưng dành cho Docker: những file **không** được đưa vào image.

Tạo file `.dockerignore`:

```
.venv/
.git/
.env
__pycache__/
*.pyc
.pytest_cache/
.ruff_cache/
benchmark/results/
```

> ⚠️ **Cảnh báo:** **`.env` phải có trong `.dockerignore`.** Nếu không, API key bị đóng gói vào image, ai có image là có key. Bí mật được truyền vào container **lúc chạy** (qua `env_file`), không bao giờ "nướng" vào image.

### Bước 3: Build image

```bash
docker build -t project-agent .
```

- `-t project-agent`: đặt tên image.
- `.`: dùng thư mục hiện tại làm "build context" (nguồn để `COPY`).

Lần đầu mất vài phút để tải image Python và thư viện. Xem image vừa tạo:

```bash
docker images project-agent
```

Kiểm tra app trong image chạy bằng user nào:

```bash
docker run --rm project-agent whoami
```

Kết quả: `appuser`.

### Bước 4: Thêm app vào Docker Compose

Mở `compose.yaml`, thêm service `app` **ngay dưới** service `db` (thụt lề cùng cấp với `db:`):

```yaml
  app:
    build: .
    env_file: .env
    environment:
      DATABASE_URL: postgresql://agent:${POSTGRES_PASSWORD:-agent}@db:5432/agent
    ports:
      - "127.0.0.1:8080:8080"
    depends_on:
      db:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')"]
      interval: 30s
      timeout: 5s
      retries: 3
    restart: unless-stopped
```

Toàn bộ `compose.yaml` sau khi sửa:

```yaml
services:
  db:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: agent
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-agent}
      POSTGRES_DB: agent
    ports:
      - "127.0.0.1:5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./db/init:/docker-entrypoint-initdb.d:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U agent -d agent"]
      interval: 5s
      timeout: 3s
      retries: 10
    restart: unless-stopped

  app:
    build: .
    env_file: .env
    environment:
      DATABASE_URL: postgresql://agent:${POSTGRES_PASSWORD:-agent}@db:5432/agent
    ports:
      - "127.0.0.1:8080:8080"
    depends_on:
      db:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')"]
      interval: 30s
      timeout: 5s
      retries: 3
    restart: unless-stopped

volumes:
  pgdata:
```

Giải thích các điểm mới:

- **`build: .`**: build image từ `Dockerfile` trong thư mục hiện tại.
- **`env_file: .env`**: nạp mọi biến trong `.env` (API key…) vào container **lúc chạy**.
- **`DATABASE_URL: ...@db:5432/...`**: trong mạng Compose, app gọi database bằng **tên service `db`**, không phải `localhost`. Trong container, `localhost` là **chính container app**. Giá trị trong `environment` **ghi đè** giá trị cùng tên trong `.env`, nên `.env` vẫn giữ `localhost` để chạy trực tiếp trên máy được.
- **`depends_on ... service_healthy`**: chỉ bật app khi database đã `healthy`.
- **`healthcheck`**: Docker gọi `/health` mỗi 30 giây. Image `slim` không có `curl`, nên ta dùng Python có sẵn để gọi.

### Bước 5: Chạy cả hệ thống

Tắt uvicorn đang chạy trực tiếp trên máy (nếu có) bằng `Ctrl + C`, vì nó đang giữ cổng 8080. Rồi chạy:

```bash
docker compose up -d --build
```

`--build` build lại image nếu code thay đổi. Kiểm tra:

```bash
docker compose ps
```

Đợi đến khi `app` hiện `(healthy)`, khoảng 30 giây. Mở **http://localhost:8080** và chat thử.

### Bước 6: Các lệnh Docker hằng ngày

Xem log của app (thêm `-f` để theo dõi liên tục, `Ctrl + C` để thoát):

```bash
docker compose logs -f app
```

Xem 50 dòng log cuối:

```bash
docker compose logs --tail 50 app
```

Chạy một lệnh **một lần** trong container mới, ví dụ xây lại chỉ mục RAG:

```bash
docker compose run --rm app python scripts/build_index.py
```

`--rm` xóa container tạm sau khi chạy xong.

Chạy bộ eval trong container:

```bash
docker compose run --rm app python eval/run_eval.py
```

Mở shell bên trong container **đang chạy** để xem xét:

```bash
docker compose exec app bash
```

Thử `ls`, `whoami`, `python --version`, rồi gõ `exit` để thoát.

Khởi động lại một service:

```bash
docker compose restart app
```

Dừng tất cả (giữ nguyên dữ liệu):

```bash
docker compose down
```

Xem dung lượng Docker đang dùng, và dọn image/container cũ không dùng nữa:

```bash
docker system df
```

```bash
docker system prune
```

> ⚠️ **Cảnh báo:** `docker compose down -v` và `docker volume prune` **xóa dữ liệu database**. Chỉ dùng khi bạn chắc chắn.

### Bước 7: Quy trình khi sửa code

1. Sửa code.
2. Chạy test: `pytest`.
3. Build và chạy lại: `docker compose up -d --build`.
4. Xem log: `docker compose logs -f app`.

💡 **Mẹo:** khi **đang phát triển**, chạy app trực tiếp bằng `uvicorn --reload` (chỉ database chạy trong Docker) để thấy thay đổi tức thì. Dùng `docker compose up --build` để **kiểm tra trước khi deploy**.

### Bước 8: Commit

```bash
git add Dockerfile .dockerignore compose.yaml
```

```bash
git commit -m "Bài 11: Dockerfile và Docker Compose cho app"
```

```bash
git push
```

---

## Kiểm tra kết quả

- [ ] `docker compose ps` thấy `db` và `app` đều `healthy`.
- [ ] http://localhost:8080 chat được.
- [ ] `docker compose run --rm app whoami` in `appuser`.
- [ ] `docker compose logs app` thấy log mỗi lần chat.
- [ ] `docker compose down` rồi `up -d` lại: lịch sử chat **vẫn còn** (nhờ volume).

## Lỗi thường gặp

| Lỗi | Nguyên nhân | Cách sửa |
|---|---|---|
| `env file .env not found` | Thiếu file `.env` | Tạo `.env` theo `.env.example` |
| `PoolTimeout` / `connection refused` trong log app | `DATABASE_URL` dùng `localhost` trong container | Kiểm tra `environment: DATABASE_URL` trong `compose.yaml` dùng `@db:5432` |
| `port is already allocated` cho 8080 | uvicorn chạy trực tiếp trên máy vẫn đang bật | Tắt nó, hoặc đổi cổng |
| App `unhealthy` | `/health` lỗi | Xem `docker compose logs app` |
| Trang chat báo `404` | File HTML không có trong image | Kiểm tra `[tool.setuptools.package-data]` trong `pyproject.toml` (Bài 09) |
| Sửa code mà container không đổi | Quên `--build` | `docker compose up -d --build` |

## Bài tập

1. Chạy `docker history project-agent` và tìm layer lớn nhất. Vì sao nó lớn?
2. Thử xóa dòng `USER appuser`, build lại, chạy `whoami`. Rồi thêm lại dòng đó.
3. Dùng `docker compose exec db psql -U agent -d agent` đếm số tin nhắn đã lưu.
4. (Nâng cao) Viết lại Dockerfile theo kiểu **multi-stage build**: một stage cài thư viện, stage cuối chỉ copy kết quả. So sánh dung lượng image. Tham khảo [Multi-stage builds](https://docs.docker.com/build/building/multi-stage/).

## Checklist hoàn thành

- [ ] Hiểu image, container, layer, volume, network
- [ ] Có Dockerfile chạy bằng user thường, `.env` không nằm trong image
- [ ] `docker compose up -d --build` chạy được cả hệ thống
- [ ] Thành thạo `logs`, `exec`, `run --rm`, `ps`, `down`
- [ ] Đã commit và push

➡️ Tiếp theo: [Bài 12: Bảo mật](bai-12-bao-mat.md)
