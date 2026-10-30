from types import SimpleNamespace

from agent import agent, llm, memory, tools


class FakeMessage:
    def __init__(self, content=None, tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls

    def model_dump(self, exclude_none=False):
        return {"role": "assistant", "content": self.content}


def fake_response(message):
    return SimpleNamespace(choices=[SimpleNamespace(message=message)], usage=None)


def tool_call(name, arguments):
    return SimpleNamespace(
        id="call_1", function=SimpleNamespace(name=name, arguments=arguments)
    )


def setup_fakes(monkeypatch, responses):
    """LLM trả lần lượt các response cho trước; memory và tool không chạm database."""
    calls = []

    def fake_chat(messages, tools=None):
        calls.append(list(messages))
        return fake_response(responses.pop(0))

    monkeypatch.setattr(llm, "chat", fake_chat)
    monkeypatch.setattr(memory, "load", lambda sid: [])
    monkeypatch.setattr(memory, "save", lambda sid, msg, reply: None)
    monkeypatch.setattr(tools, "execute", lambda name, args, sid: '[{"gia": 15000}]')
    return calls


def test_tra_loi_thang_khi_khong_can_tool(monkeypatch):
    setup_fakes(monkeypatch, [FakeMessage(content="Chào bạn!")])
    result = agent.run_agent("s1", "Xin chào")
    assert result == {"reply": "Chào bạn!", "tools_used": []}


def test_goi_tool_roi_tra_loi(monkeypatch):
    calls = setup_fakes(
        monkeypatch,
        [
            FakeMessage(tool_calls=[tool_call("tim_san_pham", '{"tu_khoa": "bánh mì"}')]),
            FakeMessage(content="Bánh mì giá 15.000đ"),
        ],
    )
    result = agent.run_agent("s1", "Bánh mì giá bao nhiêu?")
    assert result["tools_used"] == ["tim_san_pham"]
    assert result["reply"] == "Bánh mì giá 15.000đ"
    # Lần gọi LLM thứ 2 phải có kết quả tool
    assert calls[1][-1] == {
        "role": "tool",
        "tool_call_id": "call_1",
        "content": '[{"gia": 15000}]',
    }


def test_dung_lai_sau_max_steps(monkeypatch):
    lap_mai = [
        FakeMessage(tool_calls=[tool_call("khuyen_mai_dang_chay", "{}")])
        for _ in range(agent.MAX_STEPS)
    ]
    setup_fakes(monkeypatch, lap_mai)
    result = agent.run_agent("s1", "hi")
    assert result["reply"] == agent.FALLBACK_REPLY
    assert len(result["tools_used"]) == agent.MAX_STEPS
