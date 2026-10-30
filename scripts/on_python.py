import json


# 3a. Type hint
def tinh_tong(gia: int, so_luong: int = 1) -> int:
    return gia * so_luong


def tim_ma(ma: str | None = None) -> list[dict]:
    # str | None nghĩa là: chuỗi hoặc None
    return [] if ma is None else [{"ma": ma}]


print(tinh_tong(15000, 2))
print(tim_ma("Q1-01"))


# 3b. **kwargs
def tim_san_pham(tu_khoa: str, ma_cua_hang: str | None = None) -> str:
    return f"Tìm '{tu_khoa}' ở cửa hàng {ma_cua_hang}"


args = {"tu_khoa": "sữa", "ma_cua_hang": "Q1-01"}
print(tim_san_pham(**args))  # giống tim_san_pham(tu_khoa="sữa", ma_cua_hang="Q1-01")

ham = {"tim_san_pham": tim_san_pham}  # dict ánh xạ tên -> hàm
print(ham["tim_san_pham"](**args))

# 3c. Xử lý ngoại lệ
for chuoi in ['{"a": 1}', "{hỏng"]:
    try:
        print(json.loads(chuoi))
    except json.JSONDecodeError as e:
        print("JSON không hợp lệ:", e)

# 3d. with
with open("scripts/tam.txt", "w", encoding="utf-8") as f:
    f.write("xin chào")
# ra khỏi khối with, file đã tự đóng

with open("scripts/tam.txt", encoding="utf-8") as f:
    print(f.read())

# 3e. Decorator
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
