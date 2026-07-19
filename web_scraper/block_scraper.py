from playwright.sync_api import sync_playwright
from seleniumbase import sb_cdp
sb = sb_cdp.Chrome()
domains = ["facebook.com","youtube.com","chinhphu.vn","moet.gov.vn","huce.edu.vn","udemy.com"]
with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(
        sb.get_endpoint_url()
    )
    context = browser.contexts[0]
    page = context.pages[0]
    for name in domains:
        try:
            page.goto(f"https://www.similarweb.com/api/website/{name}")
            print(page.title())
            print(page.url)
            print(page.locator("pre").text_content())
            sb.sleep(3)
        except Exception as e:
            print(f"Loi: {e}")
