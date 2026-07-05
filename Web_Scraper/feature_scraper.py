from urllib.parse import urlparse,urlencode
import ipaddress
import re
import requests
from concurrent.futures import ThreadPoolExecutor
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
# 0: Fake, 1:Real, 2:Sus
# Cái chạy đa luồng = ThreadPool này là code AI, cho đến ngày 5 / 7 / 2026 chưa học về 
                                                # Chạy đa luồng trong Python #
shortening_services = r"bit\.ly|goo\.gl|shorte\.st|go2l\.ink|x\.co|ow\.ly|t\.co|tinyurl|tr\.im|is\.gd|cli\.gs|" \
                      r"yfrog\.com|migre\.me|ff\.im|tiny\.cc|url4\.eu|twit\.ac|su\.pr|twurl\.nl|snipurl\.com|" \
                      r"short\.to|BudURL\.com|ping\.fm|post\.ly|Just\.as|bkite\.com|snipr\.com|fic\.kr|loopt\.us|" \
                      r"doiop\.com|short\.ie|kl\.am|wp\.me|rubyurl\.com|om\.ly|to\.ly|bit\.do|t\.co|lnkd\.in|db\.tt|" \
                      r"qr\.ae|adf\.ly|goo\.gl|bitly\.com|cur\.lv|tinyurl\.com|ow\.ly|bit\.ly|ity\.im|q\.gs|is\.gd|" \
                      r"po\.st|bc\.vc|twitthis\.com|u\.to|j\.mp|buzurl\.com|cutt\.us|u\.bb|yourls\.org|x\.co|" \
                      r"prettylinkpro\.com|scrnch\.me|filoops\.info|vzturl\.com|qr\.net|1url\.com|tweez\.me|v\.gd|" \
                      r"tr\.im|link\.zip\.net"

class FeatureExtractor:
    def __init__(self):
        self.features = dict()

    # def add_feature(self, key, value):
    #     self.features[key] = value

    # def _safe_run(self, method_name, url):
    #     try:
    #         getattr(self, method_name)(url)
    #     except Exception as exc:
    #         self.add_feature(method_name, f"Error: {exc}")
    
    # def check_result(self):
    #     print(self.features)

    # def run_parallel_checks(self, url):
    #     self.features = dict()
    #     check_methods = [
    #         "has_ip",
    #         "have_sus_sign",
    #         "has_prefix",
    #         "has_signature",
    #         "has_icon",
    #         "get_length",
    #         "redirection",
    #         "httpDomain",
    #         "tinyURL",
    #         "has_index",
    #     ]

    #     with ThreadPoolExecutor(max_workers=min(8, len(check_methods))) as executor:
    #         futures = [executor.submit(self._safe_run, method_name, url) for method_name in check_methods]
    #         for future in futures:
    #             future.result()

    #     return self.features

    def has_ip(self, url):
        try:
            ipaddress.ip_address(url)
            # self.add_feature("Have_IP", 0)
            return 0
        except ValueError:
            # self.add_feature("Have_IP", 1)
            return 1
    
    def have_sus_sign(self, url):
        # self.add_feature(
        #     "has_@",
        #     0 if "@" in url else 1
        # )
        return 0 if "@" in url else 1

    def has_prefix(self, url):
        # has_dash = 0 if '-' in urlparse(url).netloc else 1
        # self.add_feature("has_-", has_dash)
        return 0 if '-' in urlparse(url).netloc else 1

    def has_signature(self, url):
        domain = urlparse(url).hostname

        if not domain:
            print('Vcl nạp URL vào mà cái hàm nạy chạy không ra ảo vkl')
            self.add_feature("has_signature","Error")
        
        domain = domain.lower()

        if (domain.endswith(".gov.vn")
            or domain == "gov.vn"
            or domain.endswith(".gov")
            or domain.endswith(".vn")):
            # self.add_feature("has_signature",1)
            return 1
        else:
            # self.add_feature("has_signature",0)
            return 0

    def has_icon(self, url):
        try:
            html = requests.get(url, timeout=5).text
            soup = BeautifulSoup(html, "html.parser")

            icon = soup.find(
                "link",
                rel=lambda x: x and "icon" in x.lower()
            )

            if icon:
                # self.add_feature('has_icon',1)
                return 1
            else:
                # self.add_feature('has_icon',0)
                return 0
        except:
            print('Hàm check icon bị lỗi, kiểm tra lại')
            return   
    
    def get_length(self, url):
        # self.add_feature(
        #     "long_url",
        #     1 if len(url) <= 40 else 0
        # )
        return 1 if len(url) <= 40 else 0
    
    def redirection(self,url):
        pos = url.rfind('//')
        if pos > 6:
            if pos > 7:
                # self.add_feature("url_has_//",0)
                return 0 
            else:
                # self.add_feature("url_has_//",1) 
                return 1
        else:
            # self.add_feature("url_has_//",1) 
            return 1
    
    def httpDomain(self,url):
        domain = urlparse(url).netloc
        if 'https' in domain:
            # self.add_feature("domain_has_https",0)
            return 0
        else:
            # self.add_feature("domain_has_https",1)
            return 1
    
    def tinyURL(self,url):
        match=re.search(shortening_services,url)
        if match:
            # self.add_feature("shortcut_url",0)
            return 0
        else:
            # self.add_feature("shortcut_url",1)
            return 1

    def has_index(self, url):
        try:
            domain = urlparse(url).hostname
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(
                    f"https://www.google.com/search?q=site:{domain}",
                    wait_until="networkidle"
                )
                content = page.content().lower()

                browser.close()

                not_indexed_keywords = [
                    "did not match any documents",
                    "không tìm thấy kết quả nào",
                    "không cho kết quả nào"
                ]

                if any(
                    keyword in content
                    for keyword in not_indexed_keywords):
                    # self.add_feature("indexed",0)
                    return 0
                else:
                    # self.add_feature("indexed",1)
                    return 1
        except:
            print("Lỗi tại hàm check index!")
            return

    
if __name__ == "__main__":
    feature_extractor = FeatureExtractor()
    feature_extractor.run_parallel_checks('https://moet.gov.vn/')
    feature_extractor.check_result()

