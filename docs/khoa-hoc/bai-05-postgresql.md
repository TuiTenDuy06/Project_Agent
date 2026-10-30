# Bài 05: Database PostgreSQL cho cửa hàng

## Mục tiêu

Sau bài này bạn sẽ:

- Hiểu database quan hệ, bảng, khóa chính, khóa ngoại.
- Viết được câu lệnh SQL cơ bản: `SELECT`, `WHERE`, `JOIN`, `INSERT`, `ORDER BY`, `LIMIT`.
- Chạy **PostgreSQL bằng Docker Compose**.
- Thiết kế và tạo các bảng: cửa hàng, sản phẩm, tồn kho, khuyến mãi, kèm dữ liệu mẫu.
- Kết nối database từ Python bằng **psycopg** và **connection pool**.
- Hiểu **SQL injection** và cách phòng tránh.

## Kiến thức cần học

| Chủ đề | Tài liệu |
|---|---|
| SQL từ cơ bản | [SQLBolt](https://sqlbolt.com/), bài tập SQL tương tác, làm bài 1–12 |
| PostgreSQL tutorial | [PostgreSQL Tutorial](https://www.postgresqltutorial.com/) |
| Kiểu dữ liệu PostgreSQL | [PostgreSQL docs: Data Types](https://www.postgresql.org/docs/16/datatype.html) |
| psycopg 3 | [psycopg: Basic module usage](https://www.psycopg.org/psycopg3/docs/basic/usage.html) |
| Connection pool | [psycopg_pool](https://www.psycopg.org/psycopg3/docs/advanced/pool.html) |
| Docker Compose | [Docker Compose: Quickstart](https://docs.docker.com/compose/gettingstarted/) |
| SQL injection | [OWASP: SQL Injection](https://owasp.org/www-community/attacks/SQL_Injection) |

---

## Phần lý thuyết

### 1. Database quan hệ

Database quan hệ lưu dữ liệu thành các **bảng** (table), giống bảng tính Excel:

- Mỗi **cột** (column) có tên và kiểu dữ liệu cố định.
- Mỗi **hàng** (row) là một bản ghi.
- **Khóa chính** (primary key) là cột định danh duy nhất mỗi hàng, thường là `id`.
- **Khóa ngoại** (foreign key) là cột trỏ tới khóa chính của bảng khác, tạo **quan hệ** giữa các bảng.

### 2. Thiết kế dữ liệu cho chuỗi cửa hàng

```
stores (cửa hàng)            products (sản phẩm)
┌────┬───────┬──────┐        ┌────┬───────┬──────────┬───────┐
│ id │ code  │ name │        │ id │ sku   │ name     │ price │
├────┼───────┼──────┤        ├────┼───────┼──────────┼───────┤
│ 1  │ Q1-01 │ ...  │        │ 1  │ SP001 │ Sữa tươi │ 36000 │
└────┴───────┴──────┘        └────┴───────┴──────────┴───────┘
        ▲                              ▲
        │ store_id                     │ product_id
        │     inventory (tồn kho)      │
        │   ┌──────────┬────────────┬──────────┐
        └───│ store_id │ product_id │ quantity │
            └──────────┴────────────┴──────────┘

promotions (khuyến mãi): id, title, description, start_date, end_date
```

Vì sao tách bảng `inventory`? Một sản phẩm có ở **nhiều** cửa hàng, mỗi cửa hàng có **nhiều** sản phẩm. Đây là quan hệ **nhiều-nhiều**, nên cần một bảng trung gian lưu số lượng của từng cặp (cửa hàng, sản phẩm).

**Giá lưu bằng `INTEGER` (đơn vị đồng)**, không dùng số thực. Số thực (`float`) có sai số làm tròn, ví dụ `0.1 + 0.2 = 0.30000000000000004`. Với tiền thì không chấp nhận được sai số như vậy. Tiền Việt không có phần lẻ, nên số nguyên là lựa chọn hoàn hảo.

### 3. Vì sao chạy database bằng Docker?

Cài PostgreSQL trực tiếp lên máy khá rắc rối và mỗi hệ điều hành mỗi kiểu. Với Docker, **một lệnh** là có PostgreSQL, giống hệt bản sẽ chạy trên máy chủ. Ta dùng image `pgvector/pgvector:pg16`: đây là PostgreSQL 16 có sẵn extension **pgvector**, cần cho RAG ở Bài 07.

### 4. Connection pool

Mở một kết nối database tốn thời gian, khoảng vài chục mili-giây. **Connection pool** là "hồ" giữ sẵn vài kết nối mở. Mỗi request mượn một kết nối, dùng xong trả lại hồ. Như vậy app nhanh hơn và không mở quá nhiều kết nối làm database quá tải.

### 5. SQL injection

Giả sử bạn ghép chuỗi như thế này:

```python
# ❌ TUYỆT ĐỐI KHÔNG LÀM THẾ NÀY
sql = f"SELECT * FROM products WHERE name = '{tu_khoa}'"
```

Nếu `tu_khoa` là `x'; DROP TABLE products; --`, câu SQL thành lệnh **xóa bảng**! Đây là SQL injection, một trong những lỗ hổng phổ biến và nguy hiểm nhất.

**Cách đúng:** dùng **tham số** (`%s` hoặc `%(ten)s`), để thư viện tự xử lý an toàn:

```python
# ✅ Đúng
conn.execute("SELECT * FROM products WHERE name = %s", (tu_khoa,))
```

Với agent, điều này **càng quan trọng**, vì tham số tool đến từ LLM, mà LLM thì làm theo lời khách hàng. Kẻ xấu có thể dụ LLM truyền chuỗi độc hại vào.

---

## Thực hành từng bước

> Kích hoạt môi trường ảo: `cd ~/project_agent && source .venv/bin/activate`. Mở Docker Desktop (Windows/macOS).

### Bước 1: Tạo file SQL tạo bảng

```bash
mkdir -p db/init
```

Tạo file `db/init/01_schema.sql`:

```sql
CREATE TABLE stores (
    id          SERIAL PRIMARY KEY,
    code        TEXT UNIQUE NOT NULL,
    name        TEXT NOT NULL,
    address     TEXT NOT NULL,
    district    TEXT NOT NULL,
    city        TEXT NOT NULL,
    open_time   TIME NOT NULL,
    close_time  TIME NOT NULL,
    phone       TEXT
);

CREATE TABLE products (
    id        SERIAL PRIMARY KEY,
    sku       TEXT UNIQUE NOT NULL,
    name      TEXT NOT NULL,
    category  TEXT NOT NULL,
    price     INTEGER NOT NULL CHECK (price >= 0)  -- đơn vị: đồng
);

CREATE TABLE inventory (
    store_id    INTEGER NOT NULL REFERENCES stores(id),
    product_id  INTEGER NOT NULL REFERENCES products(id),
    quantity    INTEGER NOT NULL CHECK (quantity >= 0),
    PRIMARY KEY (store_id, product_id)
);

CREATE TABLE promotions (
    id           SERIAL PRIMARY KEY,
    title        TEXT NOT NULL,
    description  TEXT NOT NULL,
    start_date   DATE NOT NULL,
    end_date     DATE NOT NULL CHECK (end_date >= start_date)
);
```

Giải thích các từ khóa:

- `SERIAL PRIMARY KEY`: số nguyên tự tăng (1, 2, 3…), là khóa chính.
- `UNIQUE`: không được trùng, ví dụ hai cửa hàng không thể cùng mã `Q1-01`.
- `NOT NULL`: bắt buộc có giá trị.
- `REFERENCES stores(id)`: khóa ngoại. Database **từ chối** tồn kho của cửa hàng không tồn tại.
- `CHECK (price >= 0)`: ràng buộc. Database từ chối giá âm.
- `PRIMARY KEY (store_id, product_id)`: khóa chính gồm 2 cột. Mỗi cặp cửa hàng–sản phẩm chỉ có một dòng.

💡 Ràng buộc (`NOT NULL`, `CHECK`, `REFERENCES`) là **tuyến phòng thủ cuối cùng**. Kể cả khi code có bug, database vẫn không cho lưu dữ liệu vô lý.

### Bước 2: Tạo dữ liệu mẫu

Tạo file `db/init/02_seed.sql` (file dài, bạn có thể copy):

```sql
INSERT INTO stores (code, name, address, district, city, open_time, close_time, phone) VALUES
('Q1-01', 'Tiện Lợi 24h Nguyễn Huệ', '12 Nguyễn Huệ, Phường Bến Nghé', 'Quận 1', 'TP.HCM', '00:00', '23:59', '02811110001'),
('Q1-02', 'Tiện Lợi 24h Lê Lợi', '88 Lê Lợi, Phường Bến Thành', 'Quận 1', 'TP.HCM', '06:00', '23:00', '02811110002'),
('Q3-01', 'Tiện Lợi 24h Võ Văn Tần', '45 Võ Văn Tần, Phường 6', 'Quận 3', 'TP.HCM', '06:00', '22:00', '02811110003'),
('BT-01', 'Tiện Lợi 24h Xô Viết Nghệ Tĩnh', '201 Xô Viết Nghệ Tĩnh, Phường 17', 'Bình Thạnh', 'TP.HCM', '00:00', '23:59', '02811110004'),
('HK-01', 'Tiện Lợi 24h Hàng Bài', '30 Hàng Bài', 'Hoàn Kiếm', 'Hà Nội', '06:00', '23:00', '02422220001');

INSERT INTO products (sku, name, category, price) VALUES
('SP001', 'Sữa tươi Vinamilk không đường 1L', 'Sữa', 36000),
('SP002', 'Sữa tươi TH True Milk ít đường 180ml', 'Sữa', 9000),
('SP003', 'Bánh mì sandwich trứng', 'Đồ ăn nhanh', 15000),
('SP004', 'Cơm nắm cá ngừ', 'Đồ ăn nhanh', 18000),
('SP005', 'Mì ly Hảo Hảo tôm chua cay', 'Mì gói', 12000),
('SP006', 'Nước suối Aquafina 500ml', 'Nước uống', 6000),
('SP007', 'Cà phê sữa đá lon Highlands 235ml', 'Nước uống', 17000),
('SP008', 'Khăn giấy Pulppy 100 tờ', 'Gia dụng', 14000),
('SP009', 'Kem đánh răng P/S 180g', 'Chăm sóc cá nhân', 32000),
('SP010', 'Snack Oishi tôm cay 40g', 'Bánh kẹo', 7000);

-- Mỗi cửa hàng có tồn kho ngẫu nhiên từ 0 đến 50 cho mọi sản phẩm
INSERT INTO inventory (store_id, product_id, quantity)
SELECT s.id, p.id, floor(random() * 51)::int
FROM stores s CROSS JOIN products p;

INSERT INTO promotions (title, description, start_date, end_date) VALUES
('Combo sáng', 'Bánh mì sandwich + sữa tươi 180ml chỉ 20.000đ, áp dụng 6h-10h', CURRENT_DATE - 7, CURRENT_DATE + 30),
('Mua 2 tặng 1 mì ly', 'Mua 2 mì ly Hảo Hảo bất kỳ tặng 1 mì ly cùng loại', CURRENT_DATE - 3, CURRENT_DATE + 14),
('Giảm 10% hóa đơn từ 200.000đ', 'Dành cho thành viên hạng Bạc trở lên', CURRENT_DATE - 30, CURRENT_DATE - 1);
```

Chú ý:

- `CROSS JOIN` tạo mọi cặp (cửa hàng, sản phẩm): 5 × 10 = 50 dòng tồn kho.
- Khuyến mãi dùng `CURRENT_DATE ± n` để luôn có 2 chương trình đang chạy và 1 chương trình **đã hết hạn**. Agent phải biết lọc bỏ chương trình hết hạn.
- Tên cửa hàng, sản phẩm và giá đều là **dữ liệu giả lập để học**.

### Bước 3: Chạy PostgreSQL bằng Docker Compose

Tạo file `compose.yaml` ở thư mục gốc:

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

volumes:
  pgdata:
```

Giải thích:

- `image`: phần mềm cần chạy (PostgreSQL 16 có pgvector).
- `environment`: tạo user `agent`, database `agent`. `${POSTGRES_PASSWORD:-agent}` nghĩa là lấy biến `POSTGRES_PASSWORD` từ file `.env`; nếu không có thì dùng `agent`. Máy bạn dùng mật khẩu `agent` cho tiện. **Máy chủ thật bắt buộc đặt mật khẩu mạnh** (Bài 15).
- `ports: "127.0.0.1:5432:5432"`: mở cổng 5432 **chỉ cho chính máy này** (`127.0.0.1`). Nếu viết `"5432:5432"` thì database mở ra cả Internet khi chạy trên máy chủ. Đây là lỗi bảo mật rất phổ biến.
- `volumes: pgdata`: dữ liệu lưu ở một ổ đĩa riêng của Docker, **không mất khi tắt container**.
- `./db/init:/docker-entrypoint-initdb.d`: PostgreSQL tự chạy mọi file `.sql` trong thư mục này **theo thứ tự tên file**, nhưng **chỉ lần đầu tiên**, khi database còn trống.
- `healthcheck`: Docker kiểm tra định kỳ xem database sẵn sàng chưa.
- `restart: unless-stopped`: tự khởi động lại nếu bị sập.

Khởi động:

```bash
docker compose up -d db
```

`-d` (detached) nghĩa là chạy nền. Kiểm tra trạng thái:

```bash
docker compose ps
```

Đợi cột STATUS hiện `healthy`. Xem log nếu có vấn đề:

```bash
docker compose logs db
```

Trong log bạn sẽ thấy dòng `running /docker-entrypoint-initdb.d/01_schema.sql`, nghĩa là các file SQL đã chạy.

### Bước 4: Thực hành SQL với psql

`psql` là công cụ dòng lệnh của PostgreSQL. Ta chạy nó **bên trong container**:

```bash
docker compose exec db psql -U agent -d agent
```

Dấu nhắc đổi thành `agent=#`. Gõ thử từng câu SQL (nhớ dấu `;` ở cuối):

```sql
\dt
```

`\dt` liệt kê các bảng.

```sql
SELECT * FROM stores;
```

```sql
SELECT name, price FROM products WHERE price < 15000 ORDER BY price;
```

```sql
SELECT name, price FROM products WHERE name ILIKE '%sữa%';
```

`ILIKE` là tìm kiếm không phân biệt hoa thường. `%` khớp với chuỗi bất kỳ.

**JOIN**: tìm tồn kho sữa tươi ở từng cửa hàng:

```sql
SELECT p.name, s.code, i.quantity
FROM products p
JOIN inventory i ON i.product_id = p.id
JOIN stores s ON s.id = i.store_id
WHERE p.name ILIKE '%sữa tươi%'
ORDER BY s.code;
```

Đọc câu này thế nào: lấy bảng `products` (đặt tên tắt `p`), nối với `inventory` khi `product_id` khớp, nối tiếp với `stores` khi `store_id` khớp, rồi lọc và sắp xếp.

Khuyến mãi **đang chạy**:

```sql
SELECT title, end_date FROM promotions
WHERE CURRENT_DATE BETWEEN start_date AND end_date;
```

Chỉ ra 2 dòng. Chương trình hết hạn đã bị lọc.

Thử vi phạm ràng buộc:

```sql
INSERT INTO products (sku, name, category, price) VALUES ('SP999', 'Test', 'Test', -5);
```

Database báo lỗi `violates check constraint`. Ràng buộc đã bảo vệ dữ liệu.

Thoát psql:

```sql
\q
```

### Bước 5: Kết nối từ Python

Thêm thư viện vào `dependencies` trong `pyproject.toml`:

```toml
    "psycopg[binary,pool]>=3.2",
```

Cài lại:

```bash
pip install -e ".[dev]"
```

Thêm dòng sau vào `.env`:

```bash
DATABASE_URL=postgresql://agent:agent@localhost:5432/agent
```

Và vào `.env.example`:

```bash
DATABASE_URL=postgresql://agent:agent@localhost:5432/agent
```

Cấu trúc URL: `postgresql://<user>:<mật khẩu>@<máy>:<cổng>/<tên database>`.

Mở `src/agent/config.py`, thêm thuộc tính vào class `Settings` (dưới dòng `llm_model`):

```python
    database_url: str = "postgresql://agent:agent@localhost:5432/agent"
```

Tạo file `src/agent/db.py`:

```python
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from agent.config import settings

# open=False: chỉ mở kết nối khi app khởi động (hoặc khi script gọi pool.open()).
pool = ConnectionPool(
    settings.database_url,
    min_size=1,
    max_size=10,
    kwargs={"row_factory": dict_row},
    open=False,
)
```

Giải thích:

- `min_size=1, max_size=10`: luôn giữ ít nhất 1 kết nối, tối đa 10.
- `row_factory=dict_row`: mỗi dòng kết quả là một `dict` như `{"name": "...", "price": 36000}` thay vì `tuple`. Dễ đọc hơn và đổi sang JSON thẳng được.
- `open=False`: không kết nối ngay khi import. Nhờ vậy viết test không cần database (Bài 10).

### Bước 6: Thử truy vấn bằng Python

Tạo file `scripts/thu_db.py`:

```python
from agent.db import pool

tu_khoa = "sữa"

# "with pool" mở pool và tự đóng khi xong
with pool, pool.connection() as conn:
    rows = conn.execute(
        "SELECT name, price FROM products WHERE name ILIKE %s ORDER BY price",
        (f"%{tu_khoa}%",),
    ).fetchall()

for row in rows:
    print(f"{row['name']}: {row['price']:,}đ")
```

Chạy:

```bash
python scripts/thu_db.py
```

Kết quả: 2 loại sữa và giá.

Chú ý cách truyền `tu_khoa`: ta đưa `%` vào **giá trị tham số**, không ghép vào câu SQL. Dấu phẩy trong `(f"%{tu_khoa}%",)` là bắt buộc, vì nó tạo **tuple một phần tử**.

`pool.connection()` dùng với `with` sẽ: mượn kết nối từ hồ; tự **commit** (lưu thay đổi) khi khối `with` chạy xong không lỗi; tự **rollback** (hủy thay đổi) nếu có lỗi; rồi trả kết nối về hồ.

### Bước 7: Cho app dùng database

Cập nhật `src/agent/app.py`: thêm `lifespan` để mở và đóng pool cùng app, và cho `/health` kiểm tra database. Thay phần đầu file đến hết hàm `health` như sau. Hàm `chat` giữ nguyên.

```python
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from agent import llm
from agent.db import pool

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    pool.open(wait=True)  # mở pool khi app khởi động, lỗi ngay nếu không kết nối được
    yield
    pool.close()  # đóng pool khi app tắt


app = FastAPI(title="Agent CSKH Tiện Lợi 24h", lifespan=lifespan)

SYSTEM_PROMPT = "Bạn là trợ lý chăm sóc khách hàng của chuỗi cửa hàng tiện lợi Tiện Lợi 24h. Trả lời ngắn gọn."


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    message: str = Field(min_length=1, max_length=1000)


class ChatResponse(BaseModel):
    reply: str
    tools_used: list[str]


@app.get("/health")
def health():
    with pool.connection() as conn:
        conn.execute("SELECT 1")
    return {"status": "ok"}
```

🧠 **Hiểu sâu:** `lifespan` là đoạn code chạy **một lần khi app bật** (trước `yield`) và **một lần khi app tắt** (sau `yield`). `wait=True` làm app **không khởi động** nếu không kết nối được database. Thà báo lỗi ngay còn hơn chạy "có vẻ ổn" rồi hỏng khi khách hỏi.

Chạy lại server:

```bash
uvicorn agent.app:app --reload --port 8080
```

```bash
curl http://localhost:8080/health
```

Giờ thử tắt database:

```bash
docker compose stop db
```

```bash
curl -i http://localhost:8080/health
```

Kết quả là lỗi `500`: `/health` đã phát hiện database chết. Bật lại database:

```bash
docker compose start db
```

### Bước 8: Commit

```bash
git add compose.yaml db/ pyproject.toml .env.example src/ scripts/thu_db.py
```

```bash
git commit -m "Bài 05: PostgreSQL, schema cửa hàng, kết nối từ Python"
```

```bash
git push
```

---

## Kiểm tra kết quả

- [ ] `docker compose ps` thấy `db` ở trạng thái `healthy`.
- [ ] Trong psql, `SELECT count(*) FROM inventory;` ra `50`.
- [ ] `python scripts/thu_db.py` in 2 loại sữa và giá.
- [ ] `/health` trả `ok` khi database chạy và lỗi khi database tắt.

## Lỗi thường gặp

| Lỗi | Nguyên nhân | Cách sửa |
|---|---|---|
| `Bind for 127.0.0.1:5432 failed: port is already allocated` | Máy đã có PostgreSQL khác chạy ở cổng 5432 | Tắt PostgreSQL kia, hoặc đổi thành `"127.0.0.1:5433:5432"` và sửa `DATABASE_URL` sang cổng `5433` |
| `connection refused` / `PoolTimeout` | Database chưa chạy hoặc chưa sẵn sàng | `docker compose ps`, đợi `healthy` |
| `password authentication failed` | Mật khẩu trong `DATABASE_URL` không khớp | Kiểm tra `.env`. Nếu đã đổi `POSTGRES_PASSWORD` sau lần chạy đầu, xem dòng tiếp theo |
| Sửa file `.sql` mà bảng không đổi | Các file trong `initdb.d` chỉ chạy **lần đầu** | Khi học: xóa sạch rồi tạo lại bằng `docker compose down -v` rồi `docker compose up -d db` |
| `relation "products" does not exist` | File SQL lỗi khi khởi tạo | Xem `docker compose logs db` để tìm lỗi SQL |

> ⚠️ **Cảnh báo:** `docker compose down -v` **xóa vĩnh viễn toàn bộ dữ liệu** trong database (`-v` xóa volume). Trên máy học thì không sao. **Tuyệt đối không chạy lệnh này trên máy chủ thật.**

## Bài tập

1. Viết câu SQL tìm **3 sản phẩm đắt nhất** (gợi ý: `ORDER BY ... DESC LIMIT 3`).
2. Viết câu SQL đếm **tổng số lượng tồn kho của mỗi cửa hàng** (gợi ý: `GROUP BY s.code` và `SUM(i.quantity)`).
3. Viết câu SQL tìm các cửa hàng **mở cửa 24 giờ** (`open_time = '00:00'`).
4. Làm hết 12 bài đầu trên [SQLBolt](https://sqlbolt.com/).
5. Thử SQL injection **an toàn** trong `thu_db.py`: đặt `tu_khoa = "x' OR '1'='1"`. Có sản phẩm nào bị lộ ra không? Vì sao?

## Checklist hoàn thành

- [ ] Hiểu bảng, khóa chính, khóa ngoại, ràng buộc
- [ ] Viết được `SELECT ... JOIN ... WHERE ... ORDER BY`
- [ ] PostgreSQL chạy bằng Docker Compose với dữ liệu mẫu
- [ ] Hiểu connection pool và luôn dùng tham số `%s` thay vì ghép chuỗi
- [ ] `/health` kiểm tra được database
- [ ] Đã commit và push

➡️ Tiếp theo: [Bài 06: Tool calling, trái tim của agent](bai-06-tool-calling.md)
