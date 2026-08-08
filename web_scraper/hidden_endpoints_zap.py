
import json
import subprocess
import time
from zapv2 import ZAPv2

# Về sau phải cấu hình lại cái 2 dòng config sau API key của start_zap do nó không được bảo mật
# 1. Cho phép truy cập từ mọi nơi (Wildcard Access)
# 2. Nguy cơ thực thi mã từ xa (Remote Code Execution - RCE)
# 3. Rò rỉ thông tin nhạy cảm
# 4. Vô hiệu hóa cơ chế kiểm tra Host Header: Chấp nhận mọi tiêu đề host
# Tóm lại là cái này chỉ viết trong giai đoạn test thôi, về sau vào production thì phải cấu hình lại!
# Moi ca cai API key m ko dung duoc thi nho set cai cua m v.

class ZapScan:
    def __init__(self, api_key, port='8080'): #Port mặc định rồi muốn thì đổi
        self.api_key = api_key
        self.port = port
        self.process = None
        self.zap = None

    def start_zap(self):
        cmd = [
            "/usr/share/zaproxy/zap.sh",
            "-daemon",
            "-port", self.port,
            "-config",
            f"api.key={self.api_key}",
            "-config", "api.addrs.addr.name=.*",
            "-config", "api.addrs.addr.regex=true"
        ]

        self.process = subprocess.Popen(cmd)
        self.zap = ZAPv2(
            apikey=self.api_key,
            proxies={
                'http': f'http://127.0.0.1:{self.port}', # Mặc định cũng chạy từ 127.0.0.1, muốn đổi thì cấu hình từ trong app 
                                                         # zaproxy GUI (Không bt nữa do t cứ dùng sẵn thôi)
                'https': f'http://127.0.0.1:{self.port}'
            }
        )
        return self.process

    def wait_for_zap(self, timeout=60):
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                version = self.zap.core.version
                print(f"ZAP API sẵn sàng! Version: {version}")
                return True
            except Exception:
                time.sleep(1)

        raise TimeoutError("Đạp Timeout rồi!")

    def spider_scan(self, target):
        if not self.zap:
            raise RuntimeError("ZAP client chưa được khởi tạo. Gọi start_zap trước.")

        spider_id = self.zap.spider.scan(target)
        while int(self.zap.spider.status(spider_id)) < 100:
            print(self.zap.spider.status(spider_id))
            time.sleep(1)

        return spider_id

    def ajax_scan(self, target):
        if not self.zap:
            raise RuntimeError("ZAP client chưa được khởi tạo. Gọi start_zap trước.")

        self.zap.clientSpider.scan(browser='firefox-headless', url=target) # Khong duoc thi thay lai bang Ajax
        while self.zap.clientSpider.status == "running":
            print("AJAX Spider đang chạy...")
            time.sleep(2)

        return self.zap.core.urls()

    def kill(self):
        try:
            self.zap.core.shutdown()
            time.sleep(3)
        except Exception as e:
            print(f'Lỗi khi tắt: {e}')        
    def json_format(self, urls:list):
        return {
            'hidden_endpoint_urls':urls
        }


if __name__ == '__main__':
    TARGET = "https://public-firing-range.appspot.com"
    API_KEY = "6n0416d5530furf9hee2c6ve5s"
    PORT = '8080'

    scanner = ZapScan(API_KEY, PORT)
    scanner.start_zap()
    print("Đợi ZAP khởi động...")
    scanner.wait_for_zap()
    print('Phiên bản ZAP:', scanner.zap.core.version)

    print("AJAX Spider...")
    urls = scanner.ajax_scan(TARGET)
    print("AJAX Spider hoàn tất")
    print(f'Test sau khi gọi hàm format xem đã chuẩn chưa: \n {scanner.json_format(urls)}')
    scanner.kill()

    
    