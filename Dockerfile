FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml ./
COPY src ./src
RUN pip install .

COPY scripts ./scripts
COPY data ./data
COPY eval ./eval

RUN useradd --create-home appuser
USER appuser

EXPOSE 8080
CMD ["uvicorn", "agent.app:app", "--host", "0.0.0.0", "--port", "8080"]
