from agent import llm
from agent.db import pool


def search(query: str, k: int = 3) -> list[dict]:
    [vector] = llm.embed([query])
    with pool.connection() as conn:
        return conn.execute(
            """
            SELECT source, content, embedding <=> %s::vector AS distance
            FROM documents
            ORDER BY distance
            LIMIT %s
            """,
            (str(vector), k),
        ).fetchall()
