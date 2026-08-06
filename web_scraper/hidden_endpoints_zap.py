import socket
import subprocess
import time
from zapv2 import ZAPv2

# Về sau phải cấu hình lại cái 2 dòng config sau API key của start_zap do nó không được bảo mật 
# 1. Cho phép truy cập từ mọi nơi (Wildcard Access) 
# 2. Nguy cơ thực thi mã từ xa (Remote Code Execution - RCE) 
# 3. Rò rỉ thông tin nhạy cảm 
# 4. Vô hiệu hóa cơ chế kiểm tra Host Header: Chấp nhận mọi tiêu đề host 
# Tóm lại là cái này chỉ viết trong giai đoạn test thôi, về sau vào production thì phải cấu hình lại!#

TARGET = "https://public-firing-range.appspot.com"
API_KEY = "6n0416d5530furf9hee2c6ve5s"
PORT = '8080'
def start_zap():
    cmd = [
        "/usr/share/zaproxy/zap.sh",
        "-daemon",
        "-port", "8080",
        '-config',
        f"api.key={API_KEY}",
        "-config", "api.addrs.addr.name=.*", 
        "-config", "api.addrs.addr.regex=true"
    ]

    process = subprocess.Popen(
        cmd
    )

    print(f"Dịch vụ đang lắng nghe tại:",{process.pid})
    return process

def wait_for_zap(zap_client, timeout=60):
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            version = zap_client.core.version
            print(f"ZAP API sẵn sàng! Version: {version}")
            return True
        except Exception:
            time.sleep(1)

    raise TimeoutError(
        f"Đạp Timeout rồi!"
    )


if __name__ == "__main__":
    start_zap()
    print("Đợi ZAP khởi động...")
    zap = ZAPv2(apikey=API_KEY,
                proxies={
                    'http': f'http://127.0.0.1:{PORT}', 
                    'https': f'http://127.0.0.1:{PORT}'
                })
    print("Vị trí chạy file:",zap.base)
    wait_for_zap(zap_client=zap)
    print('Phiên bản ZAP:',zap.core.version)
    print("Spider thường...")
    spider_id = zap.spider.scan(TARGET)

    while int(zap.spider.status(spider_id)) < 100:
        print(zap.spider.status(spider_id))
        time.sleep(1)

    print("Spider xong")
    print("AJAX Spider...")
    zap.ajaxSpider.scan(TARGET)

    while zap.ajaxSpider.status == "running":
        print("AJAX Spider đang chạy...")
        time.sleep(2)

    print("AJAX Spider hoàn tất")

    print("URLs tìm thấy:")
    for url in zap.core.urls():
        print(url)