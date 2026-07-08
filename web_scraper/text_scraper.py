from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
import re
class TextScraper:
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
        "Chrome/150.0.0.0 Safari/537.36"
        )
        self.driver = webdriver.Chrome(options=options)
        return self.driver
    def get_text(self):
        result = {
            'Heading': [],
            'Paragraph': [],
            'Link': []
        }
        for t in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            t_data = self.driver.find_elements(By.TAG_NAME, t)
            for el in t_data:
                text = el.text.strip()
                if text:
                    result['Heading'].append({
                        'Level': t,
                        'Text': text
                    })
        p_data = self.driver.find_elements(By.TAG_NAME, 'p')
        for el in p_data:
            text = el.text.strip()
            if text:
                result['Paragraph'].append(text)
        a_data = self.driver.find_elements(By.TAG_NAME, 'a')
        for el in a_data:
            href = el.get_attribute('href') or ""
            text = el.text.strip()
            if href and text:
                result['Link'].append({
                    'Text': text,
                    'URL': href
                })
        return result 
    def check_emc_tracking(self):
        scripts = self.driver.find_elements(
            By.CSS_SELECTOR, 'script[type="text/javascript"]'
        )
        for script in enumerate(scripts):
            try:
                content = script.get_attribute("innerHTML") or ""
                if not content.strip():
                    continue

                has_govaq   = "_govaq"                      in content
                has_tracker = "f-emc.ngsp.gov.vn/tracking"  in content
                has_js      = "f-emc.ngsp.gov.vn/embed"     in content
                if not (has_govaq and (has_tracker or has_js)):
                    continue
                site_id     = None
                tracker_url = None

                # Thu thập tất cả biến được khai báo trong script 
                # var tên_biến = "giá trị" hoặc 'giá trị'
                declared_vars = {}
                for match in re.finditer(
                    r"var\s+(\w+)\s*=\s*['\"]([^'\"]+)['\"]",
                    content
                ):
                    var_name  = match.group(1)
                    var_value = match.group(2)
                    declared_vars[var_name] = var_value

                # Tìm setSiteId
                # Kiểu 1: setSiteId', '1914'
                match = re.search(
                    r"setSiteId['\",\s]+['\"](\d+)['\"]",
                    content
                )
                if match:
                    site_id = match.group(1)
                else:
                    # Kiểu 2: setSiteId', ten_bien 
                    match = re.search(
                        r"setSiteId['\",\s]+([a-zA-Z_]\w*)\s*[\])]",
                        content
                    )
                    if match:
                        var_name = match.group(1)
                        site_id  = declared_vars.get(var_name)

                # Tìm setTrackerUrl 
                # Kiểu 1: setTrackerUrl', 'https://...'
                match = re.search(
                    r"setTrackerUrl['\",\s]+'(https?://[^'\"]+)'",
                    content
                )
                if match:
                    tracker_url = match.group(1)
                else:
                    # Kiểu 2: setTrackerUrl', ten_bien
                    match = re.search(
                        r"setTrackerUrl['\",\s]+([a-zA-Z_]\w*)\s*[\])]",
                        content
                    )
                    if match:
                        var_name    = match.group(1)
                        tracker_url = declared_vars.get(var_name)

                if site_id and tracker_url:
                    return 1
                # return {
                #     "has_emc":     True,
                #     "site_id":     site_id,
                #     "tracker_url": tracker_url,
                # }
            except:
                continue
        return 0
        # return {
        #     "has_emc":     False,
        #     "site_id":     None,
        #     "tracker_url": None,
        # }
 
    def scanning(self,domain):
        if not self.driver:
            self.driver=self.initDriver()
        self.driver.get(self.normalize_url(domain))
        return self.check_emc_tracking()
