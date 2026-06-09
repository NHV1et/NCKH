import json
import nodriver as nd
import asyncio

async def main():
    browser = await nd.start()
    page = await browser.get('https://ahrefs.com/traffic-checker')
    await asyncio.sleep(60)
    origin = await page.evaluate('window.location.origin')
    cookies = await browser._cookies.get_all()

    # Đoạn format dưới xem có phải sửa không
    cookies_format = [
        {
            'name': c.name,
            'value': c.value,
            'domain': c.domain,
            'path': c.path,
            'expires': c.expires if c.expires is not None else -1.0,
            'httpOnly': c.http_only,
            'secure': c.secure,
            'sameSite': c.same_site.name.capitalize() if c.same_site else 'Lax'
        }
        for c in cookies
    ]

    local_storage_items = await page.get_local_storage()
    local_storage = [
        {
            'name': key,
            'value': value
        }
        for key, value in local_storage_items.items()
    ]

    session_data = {
        'cookies': cookies_format,
        'origins': [
            {
                'origin': origin,
                'localStorage': local_storage
            }
        ]
    }

    with open('authen.json', 'w') as f:
        json.dump(data, f, indent=2)

    await asyncio.sleep(5)