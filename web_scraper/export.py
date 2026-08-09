import json
import os
from datetime import datetime
from web_scraper.text_scraper import TextScraper
from web_scraper.img_scraper import ImageScraper
from web_scraper.tool_scraper import ToolScraper
from web_scraper.feature_scraper import FeatureScraper
from web_scraper.ssl_scraper import SslScraper
from web_scraper.hidden_endpoints_zap import ZapScan
class Export:
    def __init__(self,domain):
        self.report = {}
        self.domain = domain
        now= datetime.now().strftime("%Y%m%d_%H%M%S")
        self.saved_file=f'scrap_{domain}_{now}'
    def get_Text(self):     
        text_scraper = TextScraper()
        text_scraper.scanning(self.report, domain=self.domain,surface=False,deep=True)
    def get_img(self):
        image_scraper = ImageScraper()
        self.report['Images'] = image_scraper.scanning(self.domain,self.saved_file)
    def get_tool_info(self):
        tool_scraper = ToolScraper(self.domain)
        ssl_scanner = SslScraper()
        zap_scanner = ZapScan(api_key='6n0416d5530furf9hee2c6ve5s', port='8080')
        self.report['technologies']=tool_scraper.whatweb_scan()
        self.report['waf']=tool_scraper.waf_scan()
        self.report['cves']=tool_scraper.cve_scan()
        self.report['hidden_endpoints']=zap_scanner.ajax_scan(self.domain)
        self.report['ssl_vulnerabilities']=ssl_scanner.scan_tls_vulnerabilities(self.domain)
        self.report['nikto_vulnerabilities']=tool_scraper.nikto_scan()
        self.report['wapiti_vulnerabilities']=tool_scraper.wapiti_scan()

    def get_feature_info(self,domain=True,ssl=True,port=True,dns=True):
        feature_scraper = FeatureScraper(self.domain)
        feature_scraper.scanning(self.report,scan_domain=domain,scan_ssl=ssl,scan_port=port,scan_dns=dns)
    def get_deep_features(self,domain=True,ssl=True,port=True,dns=True):
        self.get_feature_info(domain=domain,ssl=ssl,port=port,dns=dns)        
        self.get_tool_info()
    def get_surface_features(self):
        feature_scraper = FeatureScraper(self.domain)
        text_scraper = TextScraper()
        self.report['has_ip_address_in_url'] = feature_scraper.has_ip()
        self.report['has_sus_sign'] = feature_scraper.have_sus_sign()
        self.report['has_prefix'] = feature_scraper.has_prefix()
        self.report['has_signature'] = feature_scraper.has_signature()
        self.report['has_icon'] = feature_scraper.has_icon()
        self.report['long_url'] = feature_scraper.get_length()
        self.report['domain_has_https'] = feature_scraper.httpDomain()
        self.report['shortcut_url'] = feature_scraper.tinyURL()
        self.report['has_index'] = feature_scraper.has_index()

        self.report['has_sus_port'] = feature_scraper.sus_port()
        self.report['has_dns_records'] = feature_scraper.has_dns_records()
        self.report['short_domain_age'] = feature_scraper.domain_age()
        self.report['short_domain_registation_length'] = feature_scraper.domain_registation_length()
        self.report['trusted_ssl_certificate'] = feature_scraper.trusted_ssl_certificate()
        self.report['disabled_right_click'] = feature_scraper.disabled_right_click()
        self.report['on_mouse_over'] = feature_scraper.on_mouse_over()
        self.report['multi_web_forward'] = feature_scraper.web_forward()
        self.report['abnormal_url_anchor'] = feature_scraper.abnormal_url_anchor()
        text_scraper.scanning(self.report,self.domain,surface=True,deep=False)
        self.report['has_nca'] = feature_scraper.has_nca()
        self.report['high_web_rank']=feature_scraper.high_web_rank()
        self.report['high_domain_rating']=feature_scraper.high_domain_rating()
    def print_report(self):
        return json.dumps(self.report,indent=2,ensure_ascii=False)
    def to_json(self):
        os.makedirs(self.saved_file,exist_ok=True)
        path=os.path.join(self.saved_file,'report.json')      
        with open(path, 'w') as f:
            json.dump(self.report, f, indent=2, ensure_ascii=False)
