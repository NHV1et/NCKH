#1. Kiem tra tech
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

from typeguard import value
# Nếu dùng request thì khi mò web phải viết header user, còn request_html thì không cần,  
# nhưng request_html lại không lấy được dữ liệu từ API, nên mình sẽ dùng request để lấy dữ liệu từ API,  
# còn selenium để mò web nếu cần thiết (chưa biết mò cái gì)
class WebScraper:
    def __init__(self):
        # Bộ nhớ đệm để ghi nhớ folder đã nhập
        self.saved_text_folder = None
        self.saved_image_folder = None
        self.driver = None

    def _setup_driver(self):
        """Cấu hình driver (Chế độ cấu hình cứng cho Kali/WSL)"""
        options = Options()
        options.binary_location = "/usr/bin/firefox"
        options.add_argument("--headless")
        service = Service(executable_path="/usr/bin/geckodriver")
        return webdriver.Firefox(service=service, options=options)
    
    

    def get_folder(self, folder_type="text"):
        """Logic ưu tiên: Thư mục cứng (Text_Info/Image_Info) > Thư mục đã nhớ > Nhập mới"""
        default_map = {"text": "Text_Info", "image": "Image_Info"}
        default_name = default_map.get(folder_type)
        
        # 1. Ưu tiên folder cứng có sẵn
        if os.path.exists(default_name):
            return default_name

        # 2. Kiểm tra folder đã ghi nhớ trong phiên làm việc
        saved_attr = f"saved_{folder_type}_folder"
        if getattr(self, saved_attr):
            return getattr(self, saved_attr)

        # 3. Nếu chưa có gì, mới bắt đầu hỏi
        new_folder = input(f"Nhập tên thư mục lưu {folder_type} (Sẽ ghi nhớ cho các lần sau): ").strip()
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
    
    def loc_text(self):
        get_all_meta()
        domain = self.driver.current_url.split("//")[1].split("/")[0]
        language=self.driver.find_element(By.XPATH,'//html').get_attribute('lang')
        result={
            'meta_data':get_all_meta(),
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
        self.download_image()


    


    

def choose_folder(folder_name:str):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

# def extractMeta(value):
#     data = []
#     selector = f"meta[name='{value}'], meta[property='{value}']"
#     elements = driver.find_elements(By.CSS_SELECTOR, selector)

#     for element in elements:
#         content = element.get_attribute("content")
#         if content:
#             data.append(content)
#     return data



def kiem_tra_ten_mien(domain:str):

    
    # API link (Chỉ Vi en)
    url = f"https://whois.inet.vn/api/whois/domainspecify/{domain}"
    
    try:
        # Gửi yêu cầu lấy dữ liệu
        response = requests.get(url)
        
        # Chuyển về json
        data = response.json()
        print(data)
    except Exception as e:
        print(f"Có lỗi xảy ra: {e}")



kiem_tra_ten_mien("thuvienso.hcmute.edu.vn")





# scrapper = WebScraper()

# scrapper.scrape_web_dong("https://chinhphu.vn/")



