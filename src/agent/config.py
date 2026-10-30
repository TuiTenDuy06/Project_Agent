from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM dùng để trò chuyện
    llm_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    llm_api_key: str
    llm_model: str = "gemini-2.5-flash"

    # Model tạo embedding cho RAG. Để trống = dùng chung server với LLM.
    embed_base_url: str | None = None
    embed_api_key: str | None = None
    embed_model: str = "gemini-embedding-001"

    database_url: str = "postgresql://agent:agent@localhost:5432/agent"

    # Khóa bảo vệ các API quản trị (/admin/...)
    admin_api_key: str = ""
    # Các domain khác được phép gọi API từ trình duyệt
    cors_origins: list[str] = []


settings = Settings()
