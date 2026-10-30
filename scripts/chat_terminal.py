from agent import llm

messages = [
    {"role": "system", "content": "Bạn là trợ lý của chuỗi cửa hàng tiện lợi Tiện Lợi 24h. Trả lời ngắn gọn."},
]

print("Gõ câu hỏi, gõ 'thoat' để kết thúc.")
while True:
    question = input("\nBạn: ").strip()
    if question.lower() == "thoat":
        break
    if not question:
        continue

    messages.append({"role": "user", "content": question})
    resp = llm.chat(messages)
    answer = resp.choices[0].message.content
    messages.append({"role": "assistant", "content": answer})

    print("Bot:", answer)
    print(f"(đã gửi {len(messages)} tin nhắn, {resp.usage.prompt_tokens} token đầu vào)")
