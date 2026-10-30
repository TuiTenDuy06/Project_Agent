import json
import logging

from agent import rag
from agent.db import pool

logger = logging.getLogger(__name__)


def tim_san_pham(tu_khoa: str, ma_cua_hang: str | None = None) -> list[dict]:
    with pool.connection() as conn:
        return conn.execute(
            """
            SELECT p.name AS ten, p.price AS gia, s.code AS ma_cua_hang,
                   s.name AS cua_hang, i.quantity AS ton_kho
            FROM products p
            LEFT JOIN inventory i ON i.product_id = p.id
            LEFT JOIN stores s ON s.id = i.store_id
            WHERE p.name ILIKE %(q)s
              AND (%(store)s::text IS NULL OR s.code = %(store)s)
            ORDER BY p.name, s.code
            LIMIT 20
            """,
            {"q": f"%{tu_khoa}%", "store": ma_cua_hang},
        ).fetchall()


def khuyen_mai_dang_chay() -> list[dict]:
    with pool.connection() as conn:
        return conn.execute(
            """
            SELECT title AS ten, description AS mo_ta,
                   start_date AS bat_dau, end_date AS ket_thuc
            FROM promotions
            WHERE CURRENT_DATE BETWEEN start_date AND end_date
            ORDER BY end_date
            """
        ).fetchall()


def tim_cua_hang(khu_vuc: str) -> list[dict]:
    with pool.connection() as conn:
        return conn.execute(
            """
            SELECT code AS ma, name AS ten, address AS dia_chi, district AS quan,
                   city AS thanh_pho, open_time AS mo_cua, close_time AS dong_cua,
                   phone AS dien_thoai
            FROM stores
            WHERE district ILIKE %(q)s OR address ILIKE %(q)s OR city ILIKE %(q)s
            ORDER BY code
            LIMIT 10
            """,
            {"q": f"%{khu_vuc}%"},
        ).fetchall()


def tra_cuu_chinh_sach(cau_hoi: str) -> list[dict]:
    return [
        {"nguon": row["source"], "noi_dung": row["content"]}
        for row in rag.search(cau_hoi)
    ]


def chuyen_nhan_vien(
    session_id: str, ly_do: str, so_dien_thoai: str | None = None
) -> dict:
    with pool.connection() as conn:
        row = conn.execute(
            """
            INSERT INTO handoffs (session_id, reason, phone)
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            (session_id, ly_do, so_dien_thoai),
        ).fetchone()
    return {"ma_yeu_cau": row["id"], "trang_thai": "Đã chuyển cho nhân viên"}


FUNCTIONS = {
    "tim_san_pham": tim_san_pham,
    "khuyen_mai_dang_chay": khuyen_mai_dang_chay,
    "tim_cua_hang": tim_cua_hang,
    "tra_cuu_chinh_sach": tra_cuu_chinh_sach,
    "chuyen_nhan_vien": chuyen_nhan_vien,
}

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "tim_san_pham",
            "description": "Tìm sản phẩm theo tên, trả về giá (VND) và tồn kho ở từng cửa hàng.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tu_khoa": {
                        "type": "string",
                        "description": "Tên hoặc một phần tên sản phẩm, có dấu. Ví dụ: sữa tươi",
                    },
                    "ma_cua_hang": {
                        "type": "string",
                        "description": "Mã cửa hàng nếu khách hỏi một cửa hàng cụ thể. Ví dụ: Q1-01",
                    },
                },
                "required": ["tu_khoa"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "khuyen_mai_dang_chay",
            "description": "Liệt kê các chương trình khuyến mãi đang diễn ra hôm nay.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "tim_cua_hang",
            "description": "Tìm cửa hàng theo quận, đường hoặc thành phố. Trả về địa chỉ và giờ mở cửa.",
            "parameters": {
                "type": "object",
                "properties": {
                    "khu_vuc": {
                        "type": "string",
                        "description": "Quận, tên đường hoặc thành phố. Ví dụ: Quận 1",
                    }
                },
                "required": ["khu_vuc"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "tra_cuu_chinh_sach",
            "description": "Tra cứu chính sách đổi trả, thẻ thành viên, thanh toán, giao hàng và câu hỏi thường gặp.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cau_hoi": {"type": "string", "description": "Câu hỏi của khách"}
                },
                "required": ["cau_hoi"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "chuyen_nhan_vien",
            "description": "Chuyển cuộc trò chuyện cho nhân viên khi khách khiếu nại, bực bội, yêu cầu gặp người thật, hoặc vấn đề vượt quá khả năng.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ly_do": {"type": "string", "description": "Tóm tắt vấn đề của khách"},
                    "so_dien_thoai": {
                        "type": "string",
                        "description": "Số điện thoại khách cung cấp để nhân viên gọi lại, nếu có",
                    },
                },
                "required": ["ly_do"],
            },
        },
    },
]


def execute(name: str, arguments: str, session_id: str) -> str:
    """Chạy tool theo yêu cầu của LLM, luôn trả về chuỗi JSON."""
    func = FUNCTIONS.get(name)
    if func is None:
        return json.dumps({"loi": f"Không có tool tên {name}"}, ensure_ascii=False)
    try:
        args = json.loads(arguments or "{}")
        if name == "chuyen_nhan_vien":
            args["session_id"] = session_id
        result = func(**args)
    except (json.JSONDecodeError, TypeError) as e:
        return json.dumps({"loi": f"Tham số không hợp lệ: {e}"}, ensure_ascii=False)
    except Exception:
        logger.exception("Tool %s bị lỗi", name)
        return json.dumps({"loi": "Hệ thống tra cứu đang lỗi"}, ensure_ascii=False)
    # default=str: đổi ngày, giờ sang chuỗi để JSON hóa được
    return json.dumps(result, ensure_ascii=False, default=str)
