import logging
import secrets
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, Field

from agent.agent import run_agent
from agent.config import settings
from agent.db import pool
from agent.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    pool.open(wait=True)  # mở pool khi app khởi động, lỗi ngay nếu không kết nối được
    yield
    pool.close()  # đóng pool khi app tắt


app = FastAPI(title="Agent CSKH Tiện Lợi 24h", lifespan=lifespan)

if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["POST"],
        allow_headers=["Content-Type"],
    )

Instrumentator().instrument(app).expose(app, include_in_schema=False)


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    message: str = Field(min_length=1, max_length=1000)


class ChatResponse(BaseModel):
    reply: str
    tools_used: list[str]


def require_admin(x_api_key: str = Header(default="")) -> None:
    # compare_digest: so sánh chống đoán khóa theo thời gian phản hồi
    if not settings.admin_api_key or not secrets.compare_digest(
        x_api_key, settings.admin_api_key
    ):
        raise HTTPException(status_code=401, detail="Sai hoặc thiếu API key")


@app.get("/health")
def health():
    with pool.connection() as conn:
        conn.execute("SELECT 1")
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    start = time.perf_counter()
    try:
        result = run_agent(req.session_id, req.message)
    except Exception:
        logger.exception("Lỗi khi xử lý chat session=%s", req.session_id)
        raise HTTPException(
            status_code=503, detail="Hệ thống đang bận, bạn thử lại sau ít phút nhé."
        )
    logger.info(
        "chat session=%s latency=%.2fs", req.session_id, time.perf_counter() - start
    )
    return result


@app.get("/admin/handoffs", dependencies=[Depends(require_admin)])
def list_handoffs():
    with pool.connection() as conn:
        return conn.execute(
            """
            SELECT id, session_id, reason, phone, status, created_at
            FROM handoffs
            WHERE status = 'moi'
            ORDER BY created_at
            """
        ).fetchall()


# Đặt cuối cùng: mọi đường dẫn khác trả về giao diện chat
app.mount(
    "/", StaticFiles(directory=Path(__file__).parent / "static", html=True), name="web"
)
