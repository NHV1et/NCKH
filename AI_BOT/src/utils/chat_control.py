from src.stage_full.ollama_client import full_model
from llama_index.core.llms import ChatMessage

llm = full_model()

# Lưu lịch sử hội thoại
messages = []

def ask_bot(question):

    messages.append(
        ChatMessage(
            role="user",
            content=question
        )
    )

    response = llm.chat(messages)

    messages.append(response.message)

    return response.message.content