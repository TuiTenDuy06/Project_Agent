import json

from agent import tools
from agent.logging_config import mask_pii


def test_tool_khong_ton_tai():
    result = json.loads(tools.execute("xoa_database", "{}", "s1"))
    assert "loi" in result


def test_tham_so_sai():
    result = json.loads(tools.execute("tim_cua_hang", '{"sai_ten": "Q1"}', "s1"))
    assert "loi" in result


def test_json_hong():
    result = json.loads(tools.execute("tim_cua_hang", "{khong phai json", "s1"))
    assert "loi" in result


def test_che_so_dien_thoai():
    assert mask_pii("Gọi tôi 0912345678 nhé") == "Gọi tôi 091****678 nhé"
    assert mask_pii("+84912345678") == "+84****678"
