from web_scraper.export import Export
import time
domain='hanoi.thuhoibotaichinh.com'

result= Export(domain)
start=time.perf_counter()
# result.get_nuclei_info(tech=True,vuln=False)
result.get_surface_features()
execute_time=time.perf_counter()-start
result.to_json()
print(f'Thời gian thực thi quét: {execute_time:.6f} giây')
'''
EMC:Dạng script, siteId dễ bị copypaste từ web thật 
ssl: Nên xác định do ai cung cấp (tin cậy-> real), hàng free(kém tin cậy-> fake)
Tìm hiểu đặc trưng riêng của web an toàn(báo chí, điện lực, ngân hàng,v.v) 
Trường hợp trang web có trong whitelist đổi tên miền
AI: Chọn 1 template, dựa trên phản hồi nuclei, AI sẽ đưa ra quyết định chạy template nào tiếp
'''