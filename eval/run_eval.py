"""Chạy các tình huống mẫu qua agent thật và chấm điểm tự động."""

import json
import uuid
from pathlib import Path

from agent.agent import run_agent
from agent.db import pool

CASES = Path(__file__).resolve().parent / "cases.json"


def check(case: dict, result: dict) -> list[str]:
    problems = []
    expect_tool = case["expect_tool"]
    if expect_tool and expect_tool not in result["tools_used"]:
        problems.append(f"không gọi tool {expect_tool} (đã gọi: {result['tools_used']})")
    if expect_tool is None and result["tools_used"]:
        problems.append(f"không nên gọi tool nhưng đã gọi {result['tools_used']}")
    if case["expect_any"] and not any(s in result["reply"] for s in case["expect_any"]):
        problems.append(f"câu trả lời thiếu một trong {case['expect_any']}")
    return problems


def main() -> None:
    cases = json.loads(CASES.read_text(encoding="utf-8"))
    passed = 0
    with pool:
        for case in cases:
            result = run_agent(f"eval-{uuid.uuid4().hex[:8]}", case["message"])
            problems = check(case, result)
            status = "ĐẠT" if not problems else "TRƯỢT"
            passed += not problems
            print(f"[{status}] {case['message']}")
            print(f"    -> {result['reply'][:150]}")
            for p in problems:
                print(f"    !! {p}")
    print(f"\nKết quả: {passed}/{len(cases)} đạt ({passed / len(cases):.0%})")


if __name__ == "__main__":
    main()
