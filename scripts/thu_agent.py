import logging
import sys

from agent.agent import run_agent
from agent.db import pool

logging.basicConfig(level=logging.INFO)

question = " ".join(sys.argv[1:]) or "Cửa hàng Quận 1 còn sữa tươi không?"

with pool:
    result = run_agent("thu-nghiem", question)

print("\nTool đã dùng:", result["tools_used"])
print("Trả lời:", result["reply"])
