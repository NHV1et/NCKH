from Web_Scraper.text_scrap.text_scraper import Text_Scrapper
from Web_Scraper.text_scrap.port_scanner import PortScanner
from Data.luu_tru import BaseStorage
from urllib.parse import urlparse
import json
from datetime import datetime
import os

def format_data(url, text_data, port_data,label = None):
    domain = urlparse(url).netloc
    return {
        'domain': domain,
        'raw': {
            'content': text_data if text_data else {},
            'ports': port_data.get("PORTS", []),
            'traffic': 4400
            # Placeholder mấy cái dưới
        },
        'label': label
    }

def main(url:str):
    text_scrapper = Text_Scrapper()
    port_scanner = PortScanner()
    storage = BaseStorage()

    text_data = text_scrapper.scrape_web_dong(url)
    port_data = port_scanner.port_scanner(url)

    final = format_data(url, text_data, port_data,label='real')
    text_folder = storage.get_folder(folder_type='text')
    domain = urlparse(url).netloc
    text_filename = f"{domain}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    text_filepath = os.path.join(text_folder, text_filename)

    with open(text_filepath, 'w', encoding='utf-8') as f:
        json.dump(final, f, indent=4, ensure_ascii=False)

    print(f'Đã lưu thành công tại: {text_filepath}')
    return final

    
if __name__ == "__main__":
    a = main('https://mae.gov.vn/')
    




