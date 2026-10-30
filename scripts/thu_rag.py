import sys

from agent import rag
from agent.db import pool

query = " ".join(sys.argv[1:]) or "bánh mì bị mốc có đổi được không"

with pool:
    for row in rag.search(query):
        print(f"[{row['distance']:.3f}] {row['source']}")
        print("   ", row["content"][:120].replace("\n", " "))
