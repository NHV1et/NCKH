import os
import time
import json
import signal
import subprocess
from pathlib import Path
from urllib.parse import urlparse
import requests


ZAP_HOST = "127.0.0.1"
ZAP_PORT = "8080"
ZAP_API = f"http://{ZAP_HOST}:{ZAP_PORT}"
ZAP_PATH = "/usr/bin/zaproxy" # May t phai config cung ntn moi chay duoc, ve sau vo may m thi thu lenh "locate zaproxy" roi thay tuong ung 
                              # Hoac la thu cach nao de khong can viet Path cung ntn

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_SUBDIR = "Data/Text_Info" # Sau m muốn nhét vào chỗ nào thì sửa cái OUTPUT, cái PROJECT_ROOT mặc định trỏ về chính
                                 # NCKH
OUTPUT_DIR = PROJECT_ROOT / OUTPUT_SUBDIR

AJAX_TIMEOUT = 180

TARGET_URLS = [
    "https://nmap.org/",
    "https://chinhphu.vn/"
]

session = requests.Session()
session.trust_env = False

def zap_get(path, params=None, timeout=30):
    url = f"{ZAP_API}{path}"

    response = session.get(
        url,
        params=params or {},
        timeout=timeout
    )

    response.raise_for_status()
    return response.json()


def start_zap_daemon():
    cmd = [
        ZAP_PATH,
        "-daemon",
        "-host",
        ZAP_HOST,
        "-port",
        ZAP_PORT,
        "-config",
        "api.disablekey=true",
        "-config",
        "api.addrs.addr.name=127.0.0.1",
        "-config",
        "api.addrs.addr.regex=false",
    ]
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
        preexec_fn=os.setsid
    )

    return process


def wait_for_zap_ready(process, timeout=120):
    print("Đang bật ZAP")

    start_time = time.time()

    while time.time() - start_time < timeout:
        if process.poll() is not None:
            raise RuntimeError("Không bật lên thành công")

        try:
            data = zap_get("/JSON/core/view/version/", timeout=5)

            print("[+] ZAP API lên rồi!")
            print("[+] ZAP version:", data.get("version"))

            return True

        except Exception:
            time.sleep(2)

    raise TimeoutError("Timeout, xem lại code hay cấu hình!")


def stop_zap_daemon(process):
    if process is None:
        return

    try:
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        process.wait(timeout=15)

    except Exception:
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        except Exception:
            pass



def get_domain(url):
    return urlparse(url).netloc


def is_same_domain(url, target_domain):
    try:
        return urlparse(url).netloc == target_domain
    except Exception:
        return False


def safe_filename_from_url(url):
    domain = get_domain(url)

    safe_name = (
        domain
        .replace(":", "_")
        .replace("/", "_")
    )

    return f"{safe_name}_hidden_endpoints.json"



def access_target(target_url):
    print(f"Đang quét link {target_url}")

    zap_get(
        "/JSON/core/action/accessUrl/",
        params={
            "url": target_url,
            "followRedirects": "true"
        }
    )

    time.sleep(3)


def run_traditional_spider(target_url,max_wait_seconds=120, max_children=100):
    
    print("Đang quét thường...")
    data = zap_get(
        "/JSON/spider/action/scan/",
        params={
            "url": target_url,
            "maxChildren": str(max_children),
            "recurse": "true",
            "subtreeOnly": "true"
        }
    )

    scan_id = data.get("scan")

    if not scan_id:
        raise RuntimeError(f"Không quét được {data}")

    start_time = time.time()
    last_progress = -1

    while True:
        status_data = zap_get(
            "/JSON/spider/view/status/",
            params={
                "scanId": scan_id
            }
        )

        progress = int(status_data.get("status", 0))

        if progress != last_progress:
            print(f"Tiến độ: {progress}%")
            last_progress = progress

        if progress >= 100:
            break

        if time.time() - start_time > max_wait_seconds:
            print("Timeout")

            try:
                zap_get(
                    "/JSON/spider/action/stop/",
                    params={
                        "scanId": scan_id
                    }
                )
            except Exception:
                try:
                    zap_get("/JSON/spider/action/stopAllScans/")
                except Exception:
                    pass

            break

        time.sleep(2)

    print("Quét thường xong HOẶC timeout")

def configure_ajax_spider(
    max_crawl_depth=5,
    max_crawl_states=50,
    max_duration_minutes=2
):

    try:
        zap_get(
            "/JSON/ajaxSpider/action/setOptionMaxCrawlDepth/",
            params={
                "Integer": str(max_crawl_depth)
            }
        )
    except Exception as e:
        print(f"Không set max depth được: {e}")

    try:
        zap_get(
            "/JSON/ajaxSpider/action/setOptionMaxCrawlStates/",
            params={
                "Integer": str(max_crawl_states)
            }
        )
    except Exception as e:
        print(f"Set state cào không thành công: {e}")

    try:
        zap_get(
            "/JSON/ajaxSpider/action/setOptionMaxDuration/",
            params={
                "Integer": str(max_duration_minutes)
            }
        )
    except Exception as e:
        print(f"Set max duration thất bại: {e}")

def run_ajax_spider(
    target_url,
    max_wait_seconds=120,
    max_crawl_depth=5,
    max_crawl_states=50,
    max_duration_minutes=2
):
    print("Quét AJAX...")

    configure_ajax_spider(
        max_crawl_depth=max_crawl_depth,
        max_crawl_states=max_crawl_states,
        max_duration_minutes=max_duration_minutes
    )

    zap_get(
        "/JSON/ajaxSpider/action/scan/",
        params={
            "url": target_url
        }
    )

    start_time = time.time()

    while True:
        status_data = zap_get("/JSON/ajaxSpider/view/status/")
        status = status_data.get("status")

        print(f" Trạng thái: {status}")

        if status != "running":
            break

        if time.time() - start_time > max_wait_seconds:
            print("Timeout")

            try:
                zap_get("/JSON/ajaxSpider/action/stop/")
            except Exception:
                pass

            break

        time.sleep(5)

    print("Quét AJAX hoàn thành HOẶC timeout")

def collect_urls(target_url):
    target_domain = get_domain(target_url)

    data = zap_get("/JSON/core/view/urls/")
    all_urls = data.get("urls", [])

    same_domain_urls = sorted({
        url for url in all_urls
        if is_same_domain(url, target_domain)
    })

    return same_domain_urls


def find_interesting_endpoints(urls):
    interesting_keywords = [
        "/api/",
        "/ajax/",
        "/graphql",
        "/rest/",
        "/v1/",
        "/v2/",
        "/v3/",
        "/admin",
        "/internal",
        "/private",
        "/hidden",
        "/debug",
        "/config",
        "/auth",
        "/token",
        "/user",
        "/account",
        "/profile",
        "/upload",
    ]

    endpoints = []

    for url in urls:
        lowered = url.lower()

        if any(keyword in lowered for keyword in interesting_keywords):
            endpoints.append(url)

    return sorted(set(endpoints))


def collect_passive_alerts(target_url):
    data = zap_get(
        "/JSON/core/view/alerts/",
        params={
            "baseurl": target_url
        }
    )

    alerts = data.get("alerts", [])

    simplified_alerts = []

    for alert in alerts:
        simplified_alerts.append({
            "risk": alert.get("risk"),
            "confidence": alert.get("confidence"),
            "name": alert.get("name"),
            "url": alert.get("url"),
            "param": alert.get("param"),
            "description": alert.get("description"),
            "solution": alert.get("solution"),
        })

    return simplified_alerts


def clear_zap_session():
    
    zap_get(
        "/JSON/core/action/newSession/",
        params={
            "name": "",
            "overwrite": "true"
        }
    )

    time.sleep(2)

# Traditional Spider limits
TRADITIONAL_SPIDER_TIMEOUT = 120
TRADITIONAL_SPIDER_MAX_CHILDREN = 100

# AJAX Spider limits
AJAX_TIMEOUT = 120
AJAX_MAX_CRAWL_DEPTH = 5
AJAX_MAX_CRAWL_STATES = 50
AJAX_MAX_DURATION_MINUTES = 2

def scan_target(target_url):
    print("\n" + "=" * 70)
    print(f"[+] Target: {target_url}")
    print("=" * 70)

    clear_zap_session()

    access_target(target_url)

    run_traditional_spider(target_url,max_wait_seconds=TRADITIONAL_SPIDER_TIMEOUT,
                           max_children=TRADITIONAL_SPIDER_MAX_CHILDREN)

    run_ajax_spider(
        target_url,
        max_wait_seconds=TRADITIONAL_SPIDER_TIMEOUT,
        max_crawl_depth=AJAX_MAX_CRAWL_DEPTH,
        max_crawl_states=AJAX_MAX_CRAWL_STATES,
        max_duration_minutes=AJAX_MAX_DURATION_MINUTES
    )

    urls = collect_urls(target_url)
    interesting_endpoints = find_interesting_endpoints(urls)
    passive_alerts = collect_passive_alerts(target_url)

    report = {
        "target": target_url,
        "domain": get_domain(target_url),
        "total_urls_found": len(urls),
        "total_interesting_endpoints": len(interesting_endpoints),
        "total_passive_alerts": len(passive_alerts),
        "all_urls": urls,
        "interesting_endpoints": interesting_endpoints,
        "passive_alerts": passive_alerts,
    }

    return report


def save_single_report(report, output_dir):
    output_file = safe_filename_from_url(report["target"])
    output_path = output_dir / output_file

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"[+] Single report saved to: {output_path.resolve()}")

    return output_path


def save_all_reports(all_reports, output_dir):
    output_path = output_dir / "all_hidden_endpoints_report.json"

    summary = {
        "total_targets": len(all_reports),
        "reports": all_reports,
    }

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"[+] Combined report saved to: {output_path.resolve()}")

    return output_path


def main():
    output_dir = OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    zap_process = None
    all_reports = []

    try:
        zap_process = start_zap_daemon()

        wait_for_zap_ready(
            process=zap_process,
            timeout=120
        )

        for target_url in TARGET_URLS:
            try:
                report = scan_target(target_url)

                all_reports.append(report)

                save_single_report(
                    report=report,
                    output_dir=output_dir
                )

                print("\n[+] Interesting endpoints:")
                for endpoint in report["interesting_endpoints"]:
                    print(f"    {endpoint}")

                print("\n[+] Passive alerts:")
                for alert in report["passive_alerts"]:
                    print(
                        f"    [{alert['risk']}] {alert['name']} - {alert['url']}"
                    )

            except Exception as e:
                print(f"[!] Failed to scan {target_url}")
                print(f"[!] Error: {e}")

                all_reports.append({
                    "target": target_url,
                    "domain": get_domain(target_url),
                    "error": str(e),
                })

        save_all_reports(
            all_reports=all_reports,
            output_dir=output_dir
        )

    finally:
        stop_zap_daemon(zap_process)


if __name__ == "__main__":
    main()