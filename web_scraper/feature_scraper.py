import requests
from datetime import datetime
from urllib.parse import urlparse
import urllib.parse
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from web_scraper.text_scraper import TextScraper
import ipaddress
import subprocess
import re
import ssl
import socket
shortening_services = r"bit\.ly|goo\.gl|shorte\.st|go2l\.ink|x\.co|ow\.ly|t\.co|tinyurl|tr\.im|is\.gd|cli\.gs|" \
                      r"yfrog\.com|migre\.me|ff\.im|tiny\.cc|url4\.eu|twit\.ac|su\.pr|twurl\.nl|snipurl\.com|" \
                      r"short\.to|BudURL\.com|ping\.fm|post\.ly|Just\.as|bkite\.com|snipr\.com|fic\.kr|loopt\.us|" \
                      r"doiop\.com|short\.ie|kl\.am|wp\.me|rubyurl\.com|om\.ly|to\.ly|bit\.do|t\.co|lnkd\.in|db\.tt|" \
                      r"qr\.ae|adf\.ly|goo\.gl|bitly\.com|cur\.lv|tinyurl\.com|ow\.ly|bit\.ly|ity\.im|q\.gs|is\.gd|" \
                      r"po\.st|bc\.vc|twitthis\.com|u\.to|j\.mp|buzurl\.com|cutt\.us|u\.bb|yourls\.org|x\.co|" \
                      r"prettylinkpro\.com|scrnch\.me|filoops\.info|vzturl\.com|qr\.net|1url\.com|tweez\.me|v\.gd|" \
                      r"tr\.im|link\.zip\.net"
class FeatureScraper:
    def __init__(self, domain):
        self.domain = domain
        self.response=requests.get(f'https://{self.domain}')
        self.headers = {
            "Authorization": "Bearer inet_sk_64896d99f0cf1c30ac0b28368cf015703f294d2f001a25e7981834b751e649e9"
        }

    def get_Domain_info(self):
        response = requests.get(f'https://developers.inet.vn/api/gateway/v1/domain/whois/{self.domain}', headers=self.headers)
        data = response.json()['data']
        info={
            'Domain':data['domainName'],
            'Registrar':data['registrar'],
            'Creation_Date':data['creationDate'],
            'Expiration_Date':data['expirationDate'],
            'Registrant_Name':data['registrantName']
        }
        create_date = data['creationDate']
        
        domain_age=(datetime.now()-datetime.strptime(create_date,"%d-%m-%Y")).days        
        info['domainAge'] =f"{domain_age//365} years {domain_age%365} days"    

        return info
    def get_ssl_info(self):
        try:
            context = ssl.create_default_context()        
            # port 443 (HTTPS default)
            with socket.create_connection((self.domain, 443)) as sock:
                with context.wrap_socket(sock, server_hostname=self.domain) as ssock:
                    cert = ssock.getpeercert()
                    cipher=ssock.cipher()
                    version=ssock.version()
                    subject = dict(x[0] for x in cert['subject'])
                    issuer = dict(x[0] for x in cert['issuer'])
                    issued_to = subject.get('commonName', 'N/A')
                    issued_by = issuer.get('commonName', 'N/A')
                    issue_date = cert.get('notBefore', 'N/A')
                    expiry_date = cert.get('notAfter', 'N/A')
                    res={
                        'TLS_version':version,
                        'Cipher':cipher,
                        'Issued_to': issued_to,
                        'Issued_by': issued_by,
                        'Issue_date': issue_date,
                        'Expiry_date': expiry_date                    
                    }
                    return res

        except (socket.error, ssl.SSLError, ConnectionError) as e:
            print(f"Error retrieving SSL info for {self.domain}: {e}")
    def get_port_info(self):
        try:
            #command=['nmap','-sV','--top-ports','100','--open','-T4','--script=banner',self.domain] 
            command=['nmap','--top-ports','100','--open','-T4',self.domain] #Bỏ qua version, tập trung vào port proto service      
            result = subprocess.run(command, capture_output=True, text=True)
            if result.stdout:
                ports=[]
                for line in result.stdout.splitlines():
                    m = re.match(r'\s*(\d+)/(\w+)\s+open\s+(.+)', line)
                    if m:
                        port, proto, service = m.groups()
                        ports.append({"Port": port, "Proto": proto, "Service": service.strip()})
                return ports
        except subprocess.CalledProcessError as e:
            return f"[!] Lỗi: {e.stderr}"
    def get_dns_records(self):
        records_list=['A','AAAA',"MX",'NS','TXT','CNAME','SOA']
        info={}
        for type in records_list:
            result=subprocess.run(['dig','+short',type,self.domain],capture_output=True,text=True)
            records=[]
            if result.stdout.strip():
             for line in result.stdout.strip().splitlines():
                if line.strip():
                    records.append(line)
                    info[type]=records
        return info
    def scanning(self,report:dict,scan_domain=True,scan_ssl=True,scan_port=True,scan_dns=True):
        if scan_domain:
            report['domain_info']=self.get_Domain_info()
        if scan_ssl:
            report['ssl_info']=self.get_ssl_info()
        if scan_port:
            report['port_info']=self.get_port_info()
        if scan_dns:
            report['dns_info']=self.get_dns_records()

    def has_ip(self):
        try:
            ipaddress.ip_address(self.domain)
            # self.add_feature("Have_IP", 0)
            return 1
        except ValueError:
            # self.add_feature("Have_IP", 1)
            return 0
    
    def have_sus_sign(self):
        # self.add_feature(
        #     "has_@",
        #     0 if "@" in url else 1
        # )
        return 1 if "@" in self.domain else 0

    def has_prefix(self):
        # has_dash = 0 if '-' in urlparse(url).netloc else 1
        # self.add_feature("has_-", has_dash)
        return 1 if '-' in self.domain else 0

    def has_signature(self):        
        domain = self.domain.lower()

        if (domain.endswith(".gov.vn")
            or domain.endswith(".gov")
            or domain.endswith(".vn")):
            # self.add_feature("has_signature",1)
            return 0
        elif (domain.endswith(".com")
              or domain.endswith(".org")
              or domain.endswith(".net")
              or domain.endswith(".edu")):
            return 2
        else:
            # self.add_feature("has_signature",0)
            return 1

    def has_icon(self):
        try:
            html = requests.get(f'https://{self.domain}', timeout=5).text
            soup = BeautifulSoup(html, "html.parser")

            # icon = soup.find(
            #     "link",
            #     rel=lambda x: x and "icon" in x.lower()
            # )
            icon = soup.find("link", rel="shortcut icon")
            if icon:
                # self.add_feature('has_icon',1)
                return 0
            else:
                # self.add_feature('has_icon',0)
                return 1
        except:
            print('Hàm check icon bị lỗi, kiểm tra lại')
            return   
    
    def get_length(self):
        # self.add_feature(
        #     "long_url",
        #     1 if len(url) <= 40 else 0
        # )
        return 0 if len(self.domain) <= 40 else 1
        
    def httpDomain(self):
        if 'https' in self.domain:
            # self.add_feature("domain_has_https",0)
            return 1
        else:
            # self.add_feature("domain_has_https",1)
            return 0
    
    def tinyURL(self):
        match=re.search(shortening_services,self.domain)
        if match:
            # self.add_feature("shortcut_url",0)
            return 1
        else:
            # self.add_feature("shortcut_url",1)
            return 0

    def has_index(self):
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(
                    f"https://www.google.com/search?q=site:{self.domain}",
                    wait_until="networkidle"
                )
                content = page.content().lower()

                browser.close()

                not_indexed_keywords = [
                    "did not match any documents",
                    "không tìm thấy kết quả nào",
                    "không cho kết quả nào"
                ]

                if any(
                    keyword in content
                    for keyword in not_indexed_keywords):
                    # self.add_feature("indexed",0)
                    return 1
                else:
                    # self.add_feature("indexed",1)
                    return 0
        except Exception as e:
            print("Lỗi tại hàm check index!" + str(e))
            return
   
    def sus_port(self):
        try:
            #command=['nmap','-sV','--top-ports','100','--open','-T4','--script=banner',self.domain] detailed port info ->Lâu (41s)
            #Tối ưu bằng cách chỉ lấy danh sách port mở (5s)
            command=['nmap','--top-ports','100','--open','-T4',self.domain]     
            result = subprocess.run(command, capture_output=True, text=True)
            if result.stdout:
                ports=[]
                for line in result.stdout.splitlines():
                    m = re.match(r'\s*(\d+)/\w+\s+open\s+.+', line)
                    if m:
                        port = m.group(1)
                        ports.append(port)
                common_ports = ['21', '22', '23', '25', '53', '80', '110', '143', '443', '445', '3389']
                sus_ports = [port for port in ports if port not in common_ports]
                if len(sus_ports) > 0:
                    return 1
                else:
                    return 0
        except subprocess.CalledProcessError as e:
            return f"[!] Lỗi: {e.stderr}" 
    def has_dns_records(self):
        records_list=['A','AAAA',"MX",'NS','TXT','CNAME','SOA']
        info={}
        for type in records_list:
            result=subprocess.run(['dig','+short',type,self.domain],capture_output=True,text=True)
            records=[]
            if result.stdout.strip():
             for line in result.stdout.strip().splitlines():
                if line.strip():
                    records.append(line)
                    info[type]=records
        if info:
            return 0
        else:
            return 1
    def domain_info(self):
        response = requests.get(f'https://developers.inet.vn/api/gateway/v1/domain/whois/{self.domain}', headers=self.headers)
        return response.json()['data']
    def domain_age(self):        
        data = self.domain_info()
        create_date = data['creationDate']
        delta=(datetime.now()-datetime.strptime(create_date,"%d-%m-%Y")).days        
        if delta<365:
            return 1
        else:
            return 0
    def domain_registation_length(self):
        data = self.domain_info()
        create_date = data['creationDate']
        expire_date = data['expirationDate']
        delta=(datetime.strptime(expire_date,"%d-%m-%Y")-datetime.strptime(create_date,"%d-%m-%Y")).days        
        if delta<365:
            return 1
        else:
            return 0
    def trusted_ssl_certificate(self):
        try:
            context = ssl.create_default_context()        
            with socket.create_connection((self.domain, 443)) as sock:
                with context.wrap_socket(sock, server_hostname=self.domain) as ssock:
                    cert = ssock.getpeercert()
                    if not cert:
                        return -1 #Không có ssl
                    whitelist = [
                        "GlobalSign",
                        "DigiCert",
                        "GeoTrust",
                        "RapidSSL",
                        "Sectigo",
                        "Comodo CA",
                        "SSL.com",
                        "GoDaddy",
                        "Certum",
                        "Actalis",
                        "HARICA",
                        "Amazon Trust Services",
                        "Google Trust Services",
                        "Microsoft Azure App Service Certificate",
                        "Entrust",
                        "Thawte",
                        "VeriSign / Symantec legacy",
                        "IdenTrust",
                        "SwissSign",
                        "QuoVadis",
                        "ChamberSign",
                        "TrustAsia",
                        "SECOM Trust Systems",
                        "TWCA",
                        "eMudhra",
                        "Certigna",
                        "Disig",
                        "NetLock",
                        "CertEurope",
                        "TÜRKTRUST",
                        "Kamu SM",
                        "WISeKey",
                    ]
                    suslist = [
                        "Let's Encrypt",
                        "ZeroSSL",
                        "SSL For Free",
                        "Actalis Free Plan",
                        "Google Trust Services ACME",
                        "Cloudflare Universal SSL",
                        "AWS Certificate Manager public certificates",
                        "Google Cloud Google-managed SSL certificates",
                        "Azure App Service Managed Certificate",
                        "Hosting AutoSSL / cPanel AutoSSL",
                        "GitHub Pages HTTPS",
                        "Netlify managed HTTPS",
                        "Vercel managed certificates",
                        "Firebase Hosting SSL",
                        "Render managed TLS",
                        "Railway managed TLS",
                        "Fly.io managed TLS",
                        "Heroku Automated Certificate Management",
                        "Buypass Go SSL",
                    ]
                    issuer = dict(x[0] for x in cert['issuer'])
                    issuer_common_name = issuer.get('commonName', '')
                    if any(issuer_name in issuer_common_name for issuer_name in whitelist):
                        return 0 #Nhãn đáng tin cậy
                    elif any(sus_name in issuer_common_name for sus_name in suslist):
                        return 2 #Nhãn khả nghi
                    else:
                        return 1 #Nhãn không đáng tin 
        except (socket.error, ssl.SSLError, ConnectionError) as e:
            return 1
    def disabled_right_click(self):
        if 'oncontextmenu="return false"' in self.response.text:
            return 1
        else:
            return 0
    def on_mouse_over(self):
        if 'onmouseover="window.status' in self.response.text:
            return 1
        else:
            return 0
    def web_forward(self):
        if len(self.response.history)>2:
            return 1
        else:
            return 0
    def abnormal_url_anchor(self):
        soup = BeautifulSoup(self.response.text, "html.parser")
        all_tags = soup.find_all("a")
        hash_anchors = soup.find_all("a", href="#")
        percentage = (len(hash_anchors) / len(all_tags)) * 100 if all_tags else 0
        if percentage > 60:
            return 1
        else:
            return 0
    def has_nca(self):
        response=requests.get(f'https://tinnhiemmang.vn/handle_cert?id={self.domain}')
        if response.status_code==200:
            return 0
        else:
            return 1
    def high_web_rank(self):
        token="69edd463697344a19227e22d861fc4479f2d53e4b1b"
        url = f"https://www.similarweb.com/website/{self.domain}/"
        encoded_url = urllib.parse.quote_plus(url)
        response=requests.get(f'https://api.scrape.do/?token={token}&url={encoded_url}&super=true')
        if response.status_code==200:
            html=response.text
            soup = BeautifulSoup(html, "html.parser")
            title_p = soup.find("p", attrs={"data-test": "country-rank"})
            if title_p:
                parent_item = title_p.find_parent("div", class_="wa-rank-list__item")
                value_p = parent_item.find("p", class_="wa-rank-list__value")              
                if value_p:
                    rank_text = value_p.get_text(strip=True).replace("#", "")
                    #print(f"Rank: {rank_text}")
                    if rank_text <100000:
                        return 0
            return 1
    def high_domain_rating(self):
        url = "https://api.ahrefs.com/v3/public/domain-rating-free"
        headers = {
            "Accept": "application/json",
            "Authorization": "Bearer uOZjV548u4LBcMPeKR4OoQFuqAN5W5yCdEdB2Nsy"
        }
        params = {
            "target": self.domain,
            "output": "json"
        }
        response = requests.get(url, headers=headers, params=params)
        if response.status_code==200:
            data=response.json()
            score=data['domain_rating']['domain_rating']
            if score>50:
                return 0
            return 1