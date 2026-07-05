from playwright.sync_api import sync_playwright
# import asyncio
PROFILE_PATH = "Data/profile"


def traffic_tracker():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process"
            ]
        )

        context_options = {
            "viewport": {"width": 1920, "height": 1080},
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "locale": "en-US",
            "timezone_id": "America/New_York",
            "permissions": ["geolocation"],
            "java_script_enabled": True,
            "accept_downloads": True,
            "ignore_https_errors": False
        }

        context = browser.new_context(**context_options)

        # stealth
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });

            window.chrome = { runtime: {} };

            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });

            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
        """)

        page = context.new_page()

        page.goto("https://ahrefs.com/traffic-checker")

        page.wait_for_timeout(10000)

        input("Press Enter to close...")

        browser.close()

def web_crawler(url):
    with sync_playwright() as p:

        
        context = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_PATH,
            executable_path="/usr/bin/chromium",
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled"
            ]
        )

        pages = context.pages

        
        if pages:
            page = pages[0]
        else:
            page = context.new_page()

        print("[*] Opening with existing session...")
        page.goto(url)

        print("[+] Session loaded ✅")
        print("[+] Bạn có thể thao tác hoặc để code chạy tiếp")

        input(">>> Nhấn ENTER để đóng...")

        context.close()

if __name__ == "__main__":
    traffic_tracker()