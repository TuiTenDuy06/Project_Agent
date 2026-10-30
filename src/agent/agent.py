import logging
import time

from prometheus_client import Counter, Histogram

from agent import llm, memory, tools
from agent.prompts import SYSTEM_PROMPT

logger = logging.getLogger(__name__)

MAX_STEPS = 5  # chặn vòng lặp vô hạn nếu LLM cứ gọi tool mãi
FALLBACK_REPLY = "Xin lỗi, mình chưa xử lý được yêu cầu này. Bạn thử hỏi lại ngắn gọn hơn nhé."

LLM_SECONDS = Histogram("llm_request_seconds", "Thời gian mỗi lần gọi LLM")
LLM_TOKENS = Counter("llm_tokens_total", "Số token LLM đã dùng", ["loai"])
TOOL_CALLS = Counter("agent_tool_calls_total", "Số lần agent gọi tool", ["tool"])


def run_agent(session_id: str, user_message: str) -> dict:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *memory.load(session_id),
        {"role": "user", "content": user_message},
    ]
    tools_used = []
    reply = FALLBACK_REPLY

    for _ in range(MAX_STEPS):
        start = time.perf_counter()
        resp = llm.chat(messages, tools=tools.TOOL_SCHEMAS)
        LLM_SECONDS.observe(time.perf_counter() - start)
        if resp.usage:
            LLM_TOKENS.labels("input").inc(resp.usage.prompt_tokens)
            LLM_TOKENS.labels("output").inc(resp.usage.completion_tokens)

        msg = resp.choices[0].message
        if not msg.tool_calls:
            reply = msg.content or FALLBACK_REPLY
            break

        # Phải gửi lại chính tin nhắn có tool_calls thì LLM mới hiểu kết quả tool
        messages.append(msg.model_dump(exclude_none=True))
        for call in msg.tool_calls:
            name = call.function.name
            TOOL_CALLS.labels(name).inc()
            tools_used.append(name)
            result = tools.execute(name, call.function.arguments, session_id)
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result})

    memory.save(session_id, user_message, reply)
    logger.info("session=%s tools=%s", session_id, tools_used)
    return {"reply": reply, "tools_used": tools_used}
