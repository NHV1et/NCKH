from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
import time,json,os
class BlockScraper:
    CONTENT_TAGS = {"p", "h1", "h2", "h3", "h4", "h5", "h6",
                "img", "figure", "li", "blockquote", "pre", "table"}

    NOISE_TAGS   = {"script", "style", "noscript", "svg",
                "head", "meta", "link"}

    MAX_DIRECT_DIV_CHILDREN = 3
    def __init__(self):
        self.driver = None

    def normalize_url(self, url:str):
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "http://" + url
        return url

    def initDriver(self):
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
        self.driver = webdriver.Chrome(options=options)
        return self.driver
    def is_content_container(self, element) -> bool:
        """
        Kiểm tra xem 1 div có phải container nội dung thật không.
        Tiêu chí: bên trong có ít nhất 1 thẻ nội dung trực tiếp
        (p, h1-h6, img, li...) — không phải chỉ toàn div con.
        """
        result = self.driver.execute_script("""
            const el       = arguments[0];
            const children = Array.from(el.children);

            const CONTENT = new Set(['P','H1','H2','H3','H4','H5','H6',
                                    'IMG','FIGURE','LI','BLOCKQUOTE',
                                    'PRE','TABLE','FIGCAPTION','SPAN','A']);
            const NOISE   = new Set(['SCRIPT','STYLE','NOSCRIPT','SVG']);

            // Đếm số con trực tiếp là thẻ nội dung
            const contentChildren = children.filter(c => CONTENT.has(c.tagName));

            // Đếm số div con trực tiếp
            const divChildren = children.filter(c => c.tagName === 'DIV'
                                                || c.tagName === 'SECTION'
                                                || c.tagName === 'ARTICLE');

            // Visible không
            const rect = el.getBoundingClientRect();
            const isVisible = rect.width > 0 && rect.height > 0;

            return {
                hasContent:    contentChildren.length > 0,
                contentCount:  contentChildren.length,
                divCount:      divChildren.length,
                isVisible:     isVisible,
                innerTextLen:  el.innerText?.trim().length || 0,
            };
        """, element)

        if not result:
            return False

        # Có ít nhất 1 thẻ nội dung trực tiếp
        if not result["hasContent"]:
            return False

        # Không bị ẩn
        if not result["isVisible"]:
            return False

        # Nội dung không quá ngắn
        if result["innerTextLen"] < 20:
            return False

        # Không phải layout wrapper (quá nhiều div con)
        if result["divCount"] > self.MAX_DIRECT_DIV_CHILDREN and result["contentCount"] == 0:
            return False

        return True


    def extract_block_content(self, element) -> dict | None:
        """
        Trích xuất toàn bộ nội dung trong 1 container div
        theo đúng thứ tự DOM, giữ liên kết text ↔ ảnh
        """
        data = self.driver.execute_script("""
            const el       = arguments[0];
            const NOISE    = new Set(['SCRIPT','STYLE','NOSCRIPT','SVG','BUTTON']);
            const elements = [];

            function walk(node, depth) {
                if (NOISE.has(node.tagName)) return;

                const tag  = node.tagName.toLowerCase();
                const text = node.innerText?.trim() || '';
                const rect = node.getBoundingClientRect();

                // Bỏ element ẩn
                if (rect.width === 0 && rect.height === 0) return;

                // Ghi nhận thẻ nội dung
                const RECORD = new Set(['p','h1','h2','h3','h4','h5','h6',
                                        'img','figure','li','blockquote',
                                        'figcaption','table','pre']);
                if (RECORD.has(tag)) {
                    const entry = { tag, depth };

                    if (tag === 'img') {
                        entry.src = node.src || node.getAttribute('data-src') || '';
                        entry.alt = node.alt || '';
                    } else if (tag === 'figure') {
                        const img = node.querySelector('img');
                        const cap = node.querySelector('figcaption');
                        entry.src     = img?.src || img?.getAttribute('data-src') || '';
                        entry.alt     = img?.alt || '';
                        entry.caption = cap?.innerText?.trim() || '';
                    } else {
                        if (!text) return;
                        entry.text = text;
                    }

                    elements.push(entry);

                    // Không đi sâu vào figure (đã lấy hết rồi)
                    if (tag === 'figure') return;
                }

                // Đệ quy vào children
                for (const child of node.children) {
                    walk(child, depth + 1);
                }
            }

            // Duyệt children trực tiếp của container
            for (const child of el.children) {
                walk(child, 0);
            }

            // Lấy bounding box của container
            const scrollY = window.scrollY;
            const scrollX = window.scrollX;
            const r       = el.getBoundingClientRect();

            return {
                elements: elements,
                bbox: {
                    x:      Math.round(r.left + scrollX),
                    y:      Math.round(r.top  + scrollY),
                    width:  Math.round(r.width),
                    height: Math.round(r.height),
                },
                tag:        el.tagName.toLowerCase(),
                class_name: el.className || '',
                id:         el.id || '',
            };
        """, element)

        if not data or not data["elements"]:
            return None

        return data


    def find_content_containers(self) -> list:
        """
        Duyệt toàn bộ DOM, tìm các div là content container thật.
        Tránh lấy trùng (nếu div cha đã lấy thì không lấy div con nữa).
        """
        # Lấy tất cả div, section, article
        candidates = self.driver.find_elements(
            By.CSS_SELECTOR, "div, section, article, main, aside"
        )
        print(f"  Tổng candidates: {len(candidates)}")

        # Lọc ra các container thật
        containers = []
        for el in candidates:
            try:
                if self.is_content_container(el):
                    containers.append(el)
            except:
                continue

        print(f"  Content containers: {len(containers)}")

        # Lọc bỏ container con nếu cha đã được chọn
        # (tránh lấy cùng nội dung 2 lần)
        def is_descendant_of_selected(self, el, selected_els):
            return self.driver.execute_script("""
                const el       = arguments[0];
                const selected = arguments[1];
                for (const s of selected) {
                    if (s !== el && s.contains(el)) return true;
                }
                return false;
            """, el, selected_els)

        unique = []
        for el in containers:
            try:
                if not is_descendant_of_selected(self, el, unique):
                    unique.append(el)
            except:
                continue

        print(f"  Sau khi lọc trùng: {len(unique)} containers")
        return unique


    def scrape_dom_blocks(self,url: str) -> dict:

        try:
            self.driver.get(url)
            time.sleep(2)

            # Scroll để load lazy content
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1)
            self.driver.execute_script("window.scrollTo(0, 0)")
            time.sleep(0.5)

            print(f"\n[Đang phân tích DOM]: {url}")
            containers = self.find_content_containers()

            blocks = []
            for idx, container in enumerate(containers, start=1):
                try:
                    content = self.extract_block_content(container)
                    if not content:
                        continue

                    block = {
                        "block_id":  f"block_{idx:03d}",
                        "dom_tag":   content["tag"],
                        "dom_class": content["class_name"][:80],  # Trim dài
                        "dom_id":    content["id"],
                        "bbox":      content["bbox"],
                        "elements":  []
                    }

                    for order, el in enumerate(content["elements"], start=1):
                        entry = {
                            "order": order,
                            "type":  el["tag"],
                        }
                        if "text"    in el: entry["text"]    = el["text"]
                        if "src"     in el: entry["src"]     = el["src"]
                        if "alt"     in el: entry["alt"]     = el["alt"]
                        if "caption" in el: entry["caption"] = el["caption"]

                        block["elements"].append(entry)

                    blocks.append(block)
                    print(f"  [block_{idx:03d}] <{content['tag']}> "
                        f"→ {len(content['elements'])} elements")

                except Exception as e:
                    print(f"  [block_{idx:03d}] Lỗi: {e}")
                    continue

            return {
                "url":          url,
                "title":        self.driver.title,
                "total_blocks": len(blocks),
                "blocks":       blocks,
            }

        finally:
            self.driver.quit()
    def scanning(self, domain):
        if not self.driver:
            self.driver=self.initDriver()
        self.driver.get(self.normalize_url(domain))
        return self.scrape_dom_blocks(domain)
scraper = BlockScraper()
result = scraper.scanning("https://chinhphu.vn")  
with open(f"report_chinhphu.json", 'w') as f:
    json.dump(result, f, indent=2, ensure_ascii=False)