import os
from playwright.sync_api import sync_playwright

def save_session(url):
    PROFILE_PATH = "Data/profile"

    with sync_playwright() as p:

        context = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_PATH,
            executable_path="/usr/bin/chromium",
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled"
            ]
        )

        page = context.new_page()

        print("[*] Opening page...")
        page.goto(url)

        print("[!] Giải Cloudflare + thao tác như user...")
        input(">>> Xong rồi ENTER để lưu session")

        context.close()

class BaseStorage:

    def __init__(self):
        self.saved_folders = {}

    def get_folder(self, folder_type="text"):
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        default_map = {
            "text": os.path.join(BASE_DIR, "Data", "Text_Info"),
            "image": os.path.join(BASE_DIR, "Data", "Image_Info"),
        }

        default_name = default_map.get(folder_type)

        # 1. ưu tiên folder có sẵn
        if os.path.exists(default_name):
            return default_name

        # 2. folder đã nhớ
        if folder_type in self.saved_folders:
            return self.saved_folders[folder_type]

        # 3. tạo mới (auto, không hỏi input nữa)
        os.makedirs(default_name, exist_ok=True)
        self.saved_folders[folder_type] = default_name

        return default_name
    
if __name__ == "__main__":
    pass
    # chạy thử
    # save_session("https://ahrefs.com/traffic-checker")