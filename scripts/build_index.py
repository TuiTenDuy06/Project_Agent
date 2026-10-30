"""Đọc các file Markdown trong data/knowledge, cắt đoạn, tạo embedding, lưu vào bảng documents."""

from pathlib import Path

from agent import llm
from agent.db import pool

KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent / "data" / "knowledge"
BATCH_SIZE = 50


def split_markdown(text: str) -> list[str]:
    """Cắt theo tiêu đề '## ': mỗi mục là một đoạn."""
    chunks, current = [], []
    for line in text.splitlines():
        if line.startswith("## ") and current:
            chunks.append("\n".join(current).strip())
            current = []
        current.append(line)
    chunks.append("\n".join(current).strip())
    return [c for c in chunks if c]


def main() -> None:
    items = []
    for path in sorted(KNOWLEDGE_DIR.glob("*.md")):
        for chunk in split_markdown(path.read_text(encoding="utf-8")):
            items.append((path.name, chunk))
    print(f"Có {len(items)} đoạn từ {KNOWLEDGE_DIR}")

    with pool, pool.connection() as conn:
        conn.execute("TRUNCATE documents")  # xây lại từ đầu mỗi lần chạy
        for i in range(0, len(items), BATCH_SIZE):
            batch = items[i : i + BATCH_SIZE]
            vectors = llm.embed([content for _, content in batch])
            for (source, content), vector in zip(batch, vectors):
                conn.execute(
                    "INSERT INTO documents (source, content, embedding) VALUES (%s, %s, %s::vector)",
                    (source, content, str(vector)),
                )
            print(f"Đã lưu {i + len(batch)}/{len(items)}")


if __name__ == "__main__":
    main()
