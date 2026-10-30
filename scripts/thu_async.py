import asyncio
import time

import httpx


async def goi(client: httpx.AsyncClient, i: int) -> int:
    # httpbin chờ 1 giây rồi mới trả lời
    resp = await client.get("https://httpbin.org/delay/1")
    print(f"Request {i} xong: {resp.status_code}")
    return resp.status_code


async def main():
    async with httpx.AsyncClient(timeout=30) as client:
        start = time.perf_counter()
        # Gửi 5 request cùng lúc
        await asyncio.gather(*(goi(client, i) for i in range(5)))
        print(f"Tổng thời gian: {time.perf_counter() - start:.1f} giây")


asyncio.run(main())
