from src.utils.chat_control import ask_bot

while True:
    user_input = input("Bạn: ")

    if user_input.lower() == "exit":
        break

    answer = ask_bot(user_input)

    print("Bot:", answer)