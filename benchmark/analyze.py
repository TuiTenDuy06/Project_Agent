"""Đọc kết quả của run_benchmark.py và in bảng tổng hợp."""

import argparse
import json
from pathlib import Path


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    values = sorted(values)
    return values[min(len(values) - 1, int(len(values) * p))]


def fmt(value: float | None, scale: float = 1, digits: int = 2) -> str:
    return "-" if value is None else f"{value * scale:.{digits}f}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Thư mục kết quả, ví dụ benchmark/results/20261030-101500")
    args = parser.parse_args()

    files = sorted(Path(args.input).glob("c*.json"), key=lambda f: int(f.stem[1:]))
    print(
        "| Concurrency | Thành công | Req/s | Token/s | TTFT p50 (ms) | TTFT p99 (ms) "
        "| TPOT p50 (ms) | Latency p50 (s) | Latency p90 (s) | Latency p99 (s) |"
    )
    print("|---|---|---|---|---|---|---|---|---|---|")
    for f in files:
        data = json.loads(f.read_text())
        ok = [r for r in data["results"] if r["ok"]]
        total = len(data["results"])
        ttft = [r["ttft"] for r in ok if "ttft" in r]
        tpot = [r["tpot"] for r in ok if r.get("tpot") is not None]
        latency = [r["latency"] for r in ok]
        tokens = sum(r.get("output_tokens", 0) for r in ok)
        duration = data["duration"]
        print(
            f"| {data['concurrency']} | {len(ok)}/{total} | {len(ok) / duration:.2f} "
            f"| {tokens / duration:.1f} | {fmt(percentile(ttft, 0.5), 1000, 0)} "
            f"| {fmt(percentile(ttft, 0.99), 1000, 0)} | {fmt(percentile(tpot, 0.5), 1000, 1)} "
            f"| {fmt(percentile(latency, 0.5))} | {fmt(percentile(latency, 0.9))} "
            f"| {fmt(percentile(latency, 0.99))} |"
        )
        errors = {r["error"] for r in data["results"] if not r["ok"]}
        for e in list(errors)[:3]:
            print(f"  lỗi c={data['concurrency']}: {e}")


if __name__ == "__main__":
    main()
