from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
import time


class Text_Scrapper():

    def __init__(self):
        # self.saved_text_folder = None
        self.driver = None
    
    def _setup_driver(self):
        options = Options()
        options.binary_location = "/usr/bin/firefox"
        options.add_argument("--headless")
        service = Service(executable_path="/usr/bin/geckodriver")
        return webdriver.Firefox(service=service, options=options)
    
    
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
        # domain = self.driver.current_url.split("//")[1].split("/")[0]
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
        return result

        # folder_name = self.get_folder(folder_type="text")
        # with open(f"{folder_name}/{domain}_{datetime.now()}.json", "w", encoding="utf-8") as f:
        #     json.dump(result, f, indent=4, ensure_ascii=False)
    
    def scrape_web_dong(self, url):
        if not self.driver:
            self.driver = self._setup_driver()
        self.driver.get(url)
        time.sleep(5)

        return self.loc_text()
        