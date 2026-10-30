import os

# Giá trị giả để import được code mà không cần .env thật
os.environ.setdefault("LLM_API_KEY", "test-key")
os.environ.setdefault("ADMIN_API_KEY", "test-admin-key")
