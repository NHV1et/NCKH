from playwright.sync_api import sync_playwright
from seleniumbase import sb_cdp

sb = sb_cdp.Chrome()

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(
        sb.get_endpoint_url()
    )
    context = browser.contexts[0]

    page = context.pages[0]

    try:

        page.goto("https://ahrefs.com/traffic-checker")
        print(page.title())
        print(page.url)

        # Search xong thi moi co captcha
        
        page.locator('input[placeholder="Enter domain or URL"]').click()
        page.locator('input[placeholder="Enter domain or URL"]').type("huce.edu.vn",
                                                                      delay=100)
        page.keyboard.press("Enter")
        # page.screenshot(path="before.png")
        sb.solve_captcha()
        sb.sleep(3)
        # page.screenshot(path="After.png")
        traffic_label = page.get_by_text("Organic traffic")
        print(f"so element dung cai cum lol: {traffic_label.count()}")
        print(traffic_label.locator("xpath=..").inner_text())
    except Exception as e:
        print(f"Loi: {e}")
