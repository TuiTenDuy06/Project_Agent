from agent.db import pool

MAX_TURNS = 10  # chỉ đưa 10 lượt hỏi-đáp gần nhất vào prompt


def load(session_id: str) -> list[dict]:
    with pool.connection() as conn:
        rows = conn.execute(
            """
            SELECT role, content FROM messages
            WHERE session_id = %s
            ORDER BY id DESC
            LIMIT %s
            """,
            (session_id, MAX_TURNS * 2),
        ).fetchall()
    return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]


def save(session_id: str, user_message: str, reply: str) -> None:
    with pool.connection() as conn:
        conn.execute(
            """
            INSERT INTO messages (session_id, role, content)
            VALUES (%s, 'user', %s), (%s, 'assistant', %s)
            """,
            (session_id, user_message, session_id, reply),
        )
