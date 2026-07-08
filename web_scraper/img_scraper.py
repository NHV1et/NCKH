import requests
import os
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
class ImageScraper:
    def __init__(self):
        self.driver = None
    def normalize_url(self, url):
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "http://" + url
        return url
    def initDriver(self):
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
        )
        self.driver = webdriver.Chrome(options=options)
        return self.driver
    def scrape_images(self,perfect_url,saved_file):
        img_data = self.driver.find_elements(By.TAG_NAME, 'img')
        img_info=[]
        url=set()
        img_path=os.path.join(saved_file,'img_files')
        os.makedirs(img_path,exist_ok=True)  
        for i,e in enumerate(img_data,start=1):      
            link=e.get_attribute('src') or ""
            alt=e.get_attribute('alt') or ""
            if not link or link in url or link.startswith("data:image"):
                continue
            url.add(link)   
            abs_url=urljoin(perfect_url,link)

            try:
                img_response = requests.get(abs_url)
                img_response.raise_for_status()
                fname=f'image_{i}.jpg'
                path=os.path.join(img_path,fname)
                with open(path, "wb") as img_file:
                    img_file.write(img_response.content)
                img_info.append({
                            'index':i,
                            'url':abs_url,
                            'alt':alt,
                            'file name':fname
                })
            except Exception as e:
                print(f"Có lỗi xảy ra khi tải ảnh: {e}")
            except requests.exceptions.HTTPError as h:
                print(f"Lỗi http: {h}")
        return img_info 
    def scanning(self,domain,saved_file):
        if not self.driver:
            self.driver=self.initDriver()
        if saved_file and not os.path.exists(saved_file):
            os.makedirs(saved_file)
        self.driver.get(self.normalize_url(domain))
        img_info=self.scrape_images(self.normalize_url(domain), saved_file)
        return img_info