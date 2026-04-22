import base64
import json
import os
import requests as req
from openai import OpenAI


client = OpenAI(
    base_url = 'http://localhost:11434/v1',
    api_key='ollama',
)

IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp")
 
def is_image_path(text):
    """Kiểm tra có phải đường dẫn file ảnh local không."""
    return os.path.isfile(text) and text.lower().endswith(IMAGE_EXTS)
 
def is_image_url(text):
    """Kiểm tra có phải URL trỏ tới ảnh không."""
    return text.startswith("http") and text.lower().endswith(IMAGE_EXTS)
 
def load_image_base64(path):
    """Đọc file ảnh local → base64."""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")
 
def fetch_image_base64(url):
    """Tải ảnh từ URL → base64."""
    response = req.get(url, timeout=10)
    response.raise_for_status()
    return base64.b64encode(response.content).decode("utf-8")
 
def get_mime(path_or_url):
    """Lấy MIME type từ đuôi file."""
    ext = path_or_url.lower().split(".")[-1]
    return {"jpg": "image/jpeg", "jpeg": "image/jpeg",
            "png": "image/png", "webp": "image/webp",
            "gif": "image/gif", "bmp": "image/bmp"}.get(ext, "image/png")
 
def build_image_message(b64, mime):
    """Tạo message dạng multimodal gửi cho vision model."""
    return {
        "role": "user",
        "content": [
            {
                "type": "image_url",
                "image_url": {"url": f"data:{mime};base64,{b64}"},
            },
            {
                "type": "text",
                "text": "Đọc URL hoặc text trong ảnh này, sau đó phân tích xem website đó là REAL / FAKE / SUSPICIOUS."
            }
        ]
    }

prompt = """ Always respond in Vietnamese
# Role: You are a Phishing Website Detection System.

# Task:
# - Analyze the URL provided by the user.
# - Provide a conclusion: REAL / FAKE / SUSPICIOUS.
# - Provide a clear and concise explanation.

# Rules:
# - Prioritize input data (features, system results).
# - Do not make unfounded speculations.
# - If uncertain → return SUSPICIOUS.
"""
# Always respond in Vietnamese

#messages = [{"role": "system", "content": prompt}]

   #test thử 

FEW_SHOT_EXAMPLES = [
    ("data/chinhphu.json", "REAL"),
    ("data/phishing_example.json", "FAKE"),
    
]

def build_few_shot_prompt():
    examples = ""
    for path, label in FEW_SHOT_EXAMPLES:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        examples += f"\nVí dụ — Kết quả: {label}\n{json.dumps(data, ensure_ascii=False, indent=2)}\n"
    
    return f"""Bạn là hệ thống phát hiện phishing.
Dưới đây là các ví dụ để học:
{examples}
Hãy phân tích JSON mới theo đúng định dạng trên.
Luôn trả lời bằng tiếng Việt.
"""

few_shot_prompt = build_few_shot_prompt()

messages = [
    {
        "role": "system",
        "content": prompt + "\n\n" + few_shot_prompt
    }
]
#...

while True:
    user_input = input("You: ")
    if user_input == "exit":
        break

    if is_image_path(user_input) or is_image_url(user_input):
        print("Đang đọc ảnh...")
        try:
            if is_image_path(user_input):
                b64  = load_image_base64(user_input)
            else:
                b64  = fetch_image_base64(user_input)
            mime = get_mime(user_input)
            messages.append(build_image_message(b64, mime))
        except Exception as e:
            print(f"Không đọc được ảnh: {e}\n")
            continue
    #...
    else:
        messages.append({"role": "user", "content": user_input})


    #content = [{"type": "text", "text": user_input}]

    response = client.chat.completions.create(
    model="qwen2.5vl:7b",
    stream=True,
    messages=messages
    )

    print("\nBot: ", end="")
    bot_reply = ""
    for chunk in response:
        bot_reply += chunk.choices[0].delta.content or ""
        print(chunk.choices[0].delta.content or " ", end='', flush=True)
    print("\n")
    messages.append({"role": "assistant", "content": bot_reply})

 