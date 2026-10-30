import json
import logging
import re

PHONE_RE = re.compile(r"(?:\+84|0)\d{9}")


def mask_pii(text: str) -> str:
    """Che số điện thoại: 0912345678 -> 091****678."""
    return PHONE_RE.sub(lambda m: m.group()[:3] + "****" + m.group()[-3:], text)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        data = {
            "time": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "msg": mask_pii(record.getMessage()),
        }
        if record.exc_info:
            data["exc"] = self.formatException(record.exc_info)
        return json.dumps(data, ensure_ascii=False)


def setup_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)
