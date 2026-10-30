from openai import OpenAI

from agent.config import settings

client = OpenAI(
    base_url=settings.llm_base_url,
    api_key=settings.llm_api_key,
    timeout=30,
    max_retries=2,
)

embed_client = OpenAI(
    base_url=settings.embed_base_url or settings.llm_base_url,
    api_key=settings.embed_api_key or settings.llm_api_key,
    timeout=30,
    max_retries=2,
)


def chat(messages: list[dict], tools: list[dict] | None = None):
    kwargs = {"model": settings.llm_model, "messages": messages, "temperature": 0.2}
    if tools:
        kwargs["tools"] = tools
    return client.chat.completions.create(**kwargs)


def embed(texts: list[str]) -> list[list[float]]:
    resp = embed_client.embeddings.create(model=settings.embed_model, input=texts)
    return [item.embedding for item in resp.data]
