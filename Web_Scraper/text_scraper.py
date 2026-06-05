# Giả sử là bên main khởi động selenium driver 
# Lên rồi, giờ code thuần trong giả định đấy thôi#
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

class Text_Scrapper():

    def __init__(self):
        self.saved_text_folder = None
        self.driver = None
    
    def _setup_driver(self):
        options = Options()
        options.binary_location = "/usr/bin/firefox"
        options.add_argument("--headless")
        service = Service(executable_path="/usr/bin/geckodriver")
        return webdriver.Firefox(service=service, options=options)
    
    def get_folder(self, folder_type="text"):
        """Logic ưu tiên: Thư mục cứng (Text_Info/Image_Info) > Thư mục đã nhớ > Nhập mới"""
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        default_map = {
            "text": os.path.join(BASE_DIR, "Data", "Text_Info"),
            #"image": os.path.join(BASE_DIR, "Data", "Image_Info")
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
    
    def get_all_meta(self):
        meta_tags = self.driver.find_elements(By.TAG_NAME, "meta")
        meta_data = []
        for tag in meta_tags:
            name_att = tag.get_attribute("name")
            property_att = tag.get_attribute("property")
            content_att = tag.get_attribute("content")
            
            meta_name = name_att if name_att else property_att
            if meta_name and content_att:
                meta_data.append({
                    "name": meta_name,
                    "content": content_att
                })
        return meta_data
    
    def loc_text(self):
        meta_data = self.get_all_meta()
        domain = self.driver.current_url.split("//")[1].split("/")[0]
        language=self.driver.find_element(By.XPATH,'//html').get_attribute('lang')
        result={
            'meta_data': meta_data,
            'Language':language,
            'Paragraph':[],
            'Links':[],
            'Heading':[],
            'Image':[],
        }
        for p in self.driver.find_elements(By.TAG_NAME,'p'):
            result['Paragraph'].append(p.text)
        for a in self.driver.find_elements(By.TAG_NAME,'a'):
            result['Links'].append(a.get_attribute('href'))
        for h in self.driver.find_elements(By.XPATH,'//h1|//h2|//h3|//h4|//h5|//h6'):
            result['Heading'].append(h.text)
        for img in self.driver.find_elements(By.TAG_NAME,'img'):
            result['Image'].append(img.get_attribute('src'))

        folder_name = self.get_folder(folder_type="text")
        with open(f"{folder_name}/{domain}_{datetime.now()}.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=4, ensure_ascii=False)
    
    def scrape_web_dong(self, url):
        if not self.driver:
            self.driver = self._setup_driver()
        self.driver.get(url)
        time.sleep(5)

        self.loc_text()
        