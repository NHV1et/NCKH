# from playwright.sync_api import sync_playwright
# from seleniumbase import sb_cdp
import socket
from sslyze import (
    Scanner,
    ServerNetworkLocation,
    ServerScanRequest,
    ScanCommand
)


def scan_tls_vulnerabilities(hostname: str):

    request = ServerScanRequest(
        server_location=ServerNetworkLocation(
            hostname=hostname,
            port=443
        ),
        scan_commands={
            ScanCommand.HEARTBLEED,
            ScanCommand.ROBOT,
            ScanCommand.OPENSSL_CCS_INJECTION,
            ScanCommand.TLS_COMPRESSION,
            ScanCommand.TLS_FALLBACK_SCSV,
            ScanCommand.SESSION_RENEGOTIATION,
            ScanCommand.TLS_EXTENDED_MASTER_SECRET,
            ScanCommand.TLS_1_3_EARLY_DATA,
        }
    )

    scanner = Scanner()
    scanner.queue_scans([request])

    for result in scanner.get_results():

        report = {
            "host": hostname
        }

        report["heartbleed"] = (
            result.scan_result
                  .heartbleed
                  .result
        )

        report["robot"] = (
            result.scan_result
                  .robot
                  .result
        )

        report["ccs_injection"] = (
            result.scan_result
                  .openssl_ccs_injection
                  .result
        )

        report["tls_compression"] = (
            result.scan_result
                  .tls_compression
                  .result
        )

        report["fallback_scsv"] = (
            result.scan_result
                  .tls_fallback_scsv
                  .result
        )

        report["renegotiation"] = (
            result.scan_result
                  .session_renegotiation
                  .result
        )

        report["extended_master_secret"] = (
            result.scan_result
                  .tls_extended_master_secret
                  .result
        )

        report["early_data"] = (
            result.scan_result
                  .tls_1_3_early_data
                  .result
        )

        return report


def get_similar_info():
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


def get_ssl_provider(domain):
    context = ssl.create_default_context()

    with socket.create_connection((domain, 443), timeout=10) as sock:
        with context.wrap_socket(sock, server_hostname=domain) as ssock:
            cert = ssock.getpeercert()

    issuer = dict(x[0] for x in cert["issuer"])

    return issuer



if __name__ == '__main__':
    result = scan_tls_vulnerabilities("moet.gov.vn")
    print(result)
    # sb = sb_cdp.Chrome()
    domains = [
    "mod.gov.vn",
    "bqp.vn",
    "bocongan.gov.vn",
    "mofa.gov.vn",
    "moha.gov.vn",
    "moj.gov.vn",
    "mof.gov.vn",
    "moit.gov.vn",
    "mae.gov.vn",
    "moc.gov.vn",
    "bvhttdl.gov.vn",
    "most.gov.vn",
    "moet.gov.vn",
    "moh.gov.vn",
    "bdtg.gov.vn",
    "vpcp.chinhphu.vn",
    "sbv.gov.vn",
    "thanhtra.gov.vn"
]
    city_domain = [
    "hanoi.gov.vn",
    "hochiminhcity.gov.vn",
    "haiphong.gov.vn",
    "danang.gov.vn",
    "cantho.gov.vn",
    "hue.gov.vn",
    "dongnai.gov.vn",
    "angiang.gov.vn",
    "bacninh.gov.vn",
    "caobang.gov.vn",
    "camau.gov.vn",
    "dienbien.gov.vn",
    "daklak.gov.vn",
    "dongthap.gov.vn",
    "gialai.gov.vn",
    "hatinh.gov.vn",
    "hungyen.gov.vn",
    "khanhhoa.gov.vn",
    "laichau.gov.vn",
    "laocai.gov.vn",
    "lamdong.gov.vn",
    "langson.gov.vn",
    "nghean.gov.vn",
    "ninhbinh.gov.vn",
    "phutho.gov.vn",
    "quangngai.gov.vn",
    "quangninh.gov.vn",
    "quangtri.gov.vn",
    "sonla.gov.vn",
    "thanhhoa.gov.vn",
    "thainguyen.gov.vn",
    "tuyenquang.gov.vn",
    "tayninh.gov.vn",
    "vinhlong.gov.vn"
]
    
