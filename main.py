from web_scraper.nuclei_scraper import NucleiScraper
from web_scraper.text_scraper import TextScraper
from web_scraper.img_scraper import ImageScraper
from web_scraper.export import Export
import time
domain='chinhphu.vn'

result= Export(domain)
results = result.get_surface_features()
start=time.perf_counter()
# result.get_nuclei_info(tech=True,vuln=False)
execute_time=time.perf_counter()-start
print(result.print_report())
print(f'Thời gian thực thi hàm: {execute_time:.6f} giây')
