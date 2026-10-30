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
