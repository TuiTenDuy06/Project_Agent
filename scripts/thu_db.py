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
