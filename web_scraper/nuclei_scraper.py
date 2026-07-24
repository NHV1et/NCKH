import os
import subprocess
import tempfile
import json,time
from sslyze import Scanner, ServerScanRequest, ServerNetworkLocation,ScanCommand
class NucleiScraper:
    def __init__(self, url):
        self.url = url
#----------------------NUCLEI--------------------------------
    def scrape_tech(self):
      try:
        command = [
        'nuclei', '-u', self.url,
        '-j', '-silent',
        '-t', 'http/technologies',
        '-c', '30', 
        '-timeout', '5',
        '-retries', '0',
        '-severity','info'
    ]
        #command=['nuclei','-u',self.url,'-j','-silent','-t','http/technologies']
        start=time.perf_counter()
        result = subprocess.run(command, capture_output=True, text=True)
        execute_time=time.perf_counter()-start
        print(f'Thời gian chạy nuclei: {execute_time:.6f} giây')
        if result.stdout:
            techs=[]
            techs_template=set()
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    try:
                        data = json.loads(line)
                        techs_template.add(data.get('template-id'))
                        if data.get('matcher-name'):           
                            techs.append({
                                'template-id': data.get('template-id'),
                                'description': data.get('info', {}).get('description'),
                                'matcher-name': data.get('matcher-name'),
                            })
                        elif data.get('extracted-results'):
                            techs.append({
                                'template-id': data.get('template-id'),
                                'description': data.get('info', {}).get('description'),
                                'extracted-results': data.get('extracted-results'),
                            })
                       # techs.append(data.get('matcher-name')) if data.get('matcher-name') else None
                    except json.JSONDecodeError:
                        continue                              
            return techs
      except subprocess.CalledProcessError as e:
        return f"[!] Lỗi: {e.stderr}"        
    def scrape_vuln(self):
      try:
        # ssl, http/misconfiguration, http/vulnerabilities, dns, default-logins, http/exposures, cves
        #whatweb, pentest
        command = [
            'nuclei',
            '-u', self.url,
            '-j', '-silent',
            '-t', 'ssl/,http/misconfiguration/,http/exposures/',

            '-c', '30',          
            '-timeout', '5',      
            '-retries', '0',     

            '-exclude-severity', 'info',
        ]
        start=time.perf_counter()
        result = subprocess.run(command, capture_output=True, text=True)
        execute_time=time.perf_counter()-start
        print(f'Thời gian chạy nuclei: {execute_time:.6f} giây')
        if result.stdout:
            vulns=[]
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    try:
                        data = json.loads(line)
                        vulns.append({
                            'template-id': data.get('template-id'),
                            'type': data.get('type'),
                            'matcher-name': data.get('matcher-name') if data.get('matcher-name') else None,
                            'description': data.get('info', {}).get('description'),
                            'severity': data.get('info', {}).get('severity'),
                        })
                    except json.JSONDecodeError:
                        continue                              
            return vulns
      except subprocess.CalledProcessError as e:
        return f"[!] Lỗi: {e.stderr}" 
    def scrape_cve(self):
        try:
            command = [
                'nuclei',
                '-u', self.url,
                '-j', '-silent',
                '-profile', 'cves',
                '-c', '30',
                '-timeout', '5',
                '-retries', '0',
                '-exclude-severity', 'info',
            ]
            start=time.perf_counter()
            result = subprocess.run(command, capture_output=True, text=True)
            execute_time=time.perf_counter()-start
            print(f'Thời gian quét cve: {execute_time:.6f} giây')
            if result.stdout:
                cves=[]
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        try:
                            data = json.loads(line)
                            cves.append({
                                'template-id': data.get('template-id'),
                                'type': data.get('type'),
                                'matcher-name': data.get('matcher-name') if data.get('matcher-name') else None,
                                'description': data.get('info', {}).get('description'),
                                'severity': data.get('info', {}).get('severity'),
                            })
                        except json.JSONDecodeError:
                            continue                              
                return cves
        except subprocess.CalledProcessError as e:
            return f"[!] Lỗi: {e.stderr}"
#------------------------------------------------------------
    def whatweb_scan(self):
        try:
            command = [
                'whatweb',
                self.url,
                '--log-json', '-',
                '-q'
            ]
            start=time.perf_counter()
            result = subprocess.run(command, capture_output=True, text=True)
            execute_time=time.perf_counter()-start
            print(f'Thời gian chạy whatweb: {execute_time:.6f} giây')
            if result.stdout:
                try:
                    data = json.loads(result.stdout)
                    print(json.dumps(data[0]['plugins'], indent=4,ensure_ascii=False))
                except json.JSONDecodeError:
                    return f"[!] Lỗi: Không thể phân tích kết quả JSON từ whatweb."
        except subprocess.CalledProcessError as e:
            return f"[!] Lỗi: {e.stderr}"
    def nikto_scan(self):
        try:
            with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
                tmp_path = f.name
            command = [
                'nikto',
                '-h', self.url,
                '-ssl',
                '-Tuning', '1234abc',
                '-timeout', '5',
                '-maxtime', '60',
                '-Format', 'json',
                '-output', tmp_path
            ]
            start=time.perf_counter()
            subprocess.run(command,stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            execute_time=time.perf_counter()-start
            print(f'Thời gian chạy nikto: {execute_time:.6f} giây')
            try:
                with open(tmp_path) as f:
                    data = json.load(f)
                    return data.get('vulnerabilities', [])  
            except (json.JSONDecodeError, FileNotFoundError):
                return []
            finally:
                os.unlink(tmp_path)
        except Exception as e:
            return f"[!] Lỗi: {str(e)}"
    def scanning(self,report:dict,scan_tech=True,scan_vuln=True):
        if scan_tech:
            report['technologies']=self.scrape_tech()
        if scan_vuln:
            report['vulnerabilities']=self.scrape_vuln()
