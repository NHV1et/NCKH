import requests
import json
from datetime import datetime
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import NoSuchElementException
import time

class Image_Scrapper():
     
    def _setup_driver(self):

        # Về sau có máy xịn hoặc cấu hình ko lỗi thì ko cần gọi 
        # Cái này cũng được #
        """Cấu hình driver (Chế độ cấu hình cứng cho Kali/WSL)"""
        options = Options()
        options.binary_location = "/usr/bin/firefox"
        options.add_argument("--headless")
        service = Service(executable_path="/usr/bin/geckodriver")
        return webdriver.Firefox(service=service, options=options)

    def get_folder(self, folder_type="text"):
        """Logic ưu tiên: Thư mục cứng (Text_Info/Image_Info) > Thư mục đã nhớ > Nhập mới"""
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        default_map = {
            #"text": os.path.join(BASE_DIR, "Data", "Text_Info"),
            "image": os.path.join(BASE_DIR, "Data", "Image_Info")
        }

        default_name = default_map.get(folder_type)

        # 1. Ưu tiên folder cứng có sẵn
        if os.path.exists(default_name):
            return default_name

        # 2. Folder đã nhớ
        saved_attr = f"saved_{folder_type}_folder"
        if getattr(self, saved_attr):
            return getattr(self, saved_attr)

        # 3. Hỏi user
        new_folder = input(f"Nhập tên thư mục lưu {folder_type}: ").strip()
        if not os.path.exists(new_folder):
            os.makedirs(new_folder)

        setattr(self, saved_attr, new_folder)
        return new_folder
    
    def download_image(self):
        parent_folder = self.get_folder(folder_type="image")
        try:
            domain = self.driver.current_url.split("//")[1].split("/")[0]
            timestamp = datetime.now()
            subfolder_name = f"{domain}_{timestamp}"
            target_path = os.path.join(parent_folder, subfolder_name)
            os.makedirs(target_path, exist_ok=True)
            images = self.driver.find_elements(By.TAG_NAME, "img")
            for index, img in enumerate(images):
                try:
                    image_url = img.get_attribute("src")
                    if not image_url or not image_url.startswith('http'):
                        continue
                    
                    
                    img_response = requests.get(image_url, timeout=10)
                    if img_response.status_code == 200:
                        
                        file_name = f"img_{index}.jpg"
                        file_full_path = os.path.join(target_path, file_name)
                        
                        with open(file_full_path, "wb") as f:
                            f.write(img_response.content)
                except Exception as e:
                    print(f"Lỗi khi tải ảnh thứ {index}: {e}")
                    continue
        except Exception as e:
            print(f"Lỗi hệ thống khi xử lý thư mục hoặc URL: {e}")
