from agent.llm import client

for model in client.models.list():
    print(model.id)
