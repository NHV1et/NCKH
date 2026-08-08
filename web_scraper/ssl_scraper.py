import json
from sslyze import (
            Scanner,
            ServerNetworkLocation,
            ServerScanRequest,
            ScanCommand
        )

from pathlib import Path

class SSL_Scraper():
    def __init__(self):
        pass

    def scan_tls_vulnerabilities(self,hostname: str):
        scanner = Scanner()
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

        scanner.queue_scans([request])

        for result in scanner.get_results():
            print('Kieu du lieu cua robot:', type(result.scan_result
                                .robot
                                .result.robot_result.value))

            print('Kieu du lieu cua css_in',type(result.scan_result
                                .openssl_ccs_injection
                                .result.is_vulnerable_to_ccs_injection))

            print('Kieu du lieu cua tls_com',type(result.scan_result
                                .tls_compression
                                .result.supports_compression))
            print('Kieu du lieu cua fallback_scsv',type( result.scan_result
                                .tls_fallback_scsv
                                .result.supports_fallback_scsv))
            print('Kieu du lieu cua renegotiation',type( result.scan_result
                                .session_renegotiation
                                .result.client_renegotiations_success_count))
            report = {
                "host": hostname
            }

            report["heartbleed"] = (
                result.scan_result
                    .heartbleed
                    .result.is_vulnerable_to_heartbleed
            )

            report["robot"] = (
                result.scan_result
                    .robot
                    .result.robot_result.value
            )

            report["ccs_injection"] = (
                result.scan_result
                    .openssl_ccs_injection
                    .result.is_vulnerable_to_ccs_injection
            )

            report["tls_compression"] = (
                result.scan_result
                    .tls_compression
                    .result.supports_compression
            )

            report["fallback_scsv"] = (
                result.scan_result
                    .tls_fallback_scsv
                    .result.supports_fallback_scsv
            )

            report["supports_secure_renegotiation"] = (
                result.scan_result
                    .session_renegotiation
                    .result.supports_secure_renegotiation
            )

            report['is_vulnerable_to_client_renegotiation_dos'] = (
                result.scan_result
                                    .session_renegotiation
                                    .result.is_vulnerable_to_client_renegotiation_dos
            )

            report['client_renegotiations_success_count'] = (result.scan_result
                                                .session_renegotiation
                                                .result.client_renegotiations_success_count)

            report["extended_master_secret"] = (
                result.scan_result
                    .tls_extended_master_secret
                    .result.supports_ems_extension
            )

            report["early_data"] = (
                result.scan_result
                    .tls_1_3_early_data
                    .result.supports_early_data
            )
            
            return report

if __name__ == '__main__':
    ssl_scanner = SSL_Scraper()
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
    
    # print(ssl_scanner.scan_tls_vulnerabilities('danang.gov.vn'))
    bao_cao = []
    for domain in city_domain:
        try:
            bao_cao.append(ssl_scanner.scan_tls_vulnerabilities(domain))
        except Exception as e:
            print('Trong lúc quét, domain', ' ', domain,'bị lỗi:', ' ',e)

    with open(
                Path(__file__).resolve().parent.parent / "report_json" / f"web_thanh_pho_ssl_vul_report.json",
                "w",
                encoding="utf-8"
            ) as f:
                json.dump(bao_cao, f, indent=4)

    
