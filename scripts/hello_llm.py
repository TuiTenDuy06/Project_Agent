from agent import llm

messages = [
    {"role": "system", "content": "Bạn là trợ lý của chuỗi cửa hàng tiện lợi. Trả lời ngắn gọn bằng tiếng Việt."},
    {"role": "user", "content": "Gợi ý cho mình một bữa sáng nhanh ở cửa hàng tiện lợi."},
]

resp = llm.chat(messages)

print("Trả lời:", resp.choices[0].message.content)
print("Token đầu vào:", resp.usage.prompt_tokens)
print("Token đầu ra:", resp.usage.completion_tokens)
