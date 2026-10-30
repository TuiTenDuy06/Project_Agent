from fastapi.testclient import TestClient

from agent import app as app_module

# Không dùng "with TestClient(...)" để app không mở kết nối database
client = TestClient(app_module.app)


def test_chat_tra_ve_ket_qua_agent(monkeypatch):
    monkeypatch.setattr(
        app_module, "run_agent", lambda sid, msg: {"reply": "Chào bạn", "tools_used": []}
    )
    res = client.post("/chat", json={"session_id": "abc", "message": "Xin chào"})
    assert res.status_code == 200
    assert res.json() == {"reply": "Chào bạn", "tools_used": []}


def test_chat_tu_choi_tin_nhan_rong():
    res = client.post("/chat", json={"session_id": "abc", "message": ""})
    assert res.status_code == 422


def test_chat_tu_choi_session_id_la():
    res = client.post("/chat", json={"session_id": "a b;DROP", "message": "hi"})
    assert res.status_code == 422


def test_chat_tra_503_khi_agent_loi(monkeypatch):
    def hong(sid, msg):
        raise RuntimeError("LLM sập")

    monkeypatch.setattr(app_module, "run_agent", hong)
    res = client.post("/chat", json={"session_id": "abc", "message": "hi"})
    assert res.status_code == 503


def test_admin_can_api_key():
    res = client.get("/admin/handoffs")
    assert res.status_code == 401


def test_admin_tu_choi_khoa_sai():
    res = client.get("/admin/handoffs", headers={"X-API-Key": "sai"})
    assert res.status_code == 401
