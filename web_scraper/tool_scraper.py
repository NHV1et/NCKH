from datetime import datetime
import os
import subprocess
import tempfile
import json,time
class ToolScraper:
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
    def cve_scan(self):
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
    def waf_scan(self):
        try:
            command = [
                'nuclei',
                '-u', self.url,
                '-j', '-silent',
                '-t', 'http/technologies/waf-detect.yaml',
                '-timeout', '5',
                '-retries', '0',
                '-severity', 'info'
            ]
            result = subprocess.run(command, capture_output=True, text=True)
            if result.stdout:
                wafs={}
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        try:
                            data = json.loads(line)
                            wafs['waf-name'] = data.get('matcher-name') if data.get('matcher-name') else None
                        except json.JSONDecodeError:
                            continue                              
                return wafs
            return []
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
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        safe_host = self.url.replace("http://", "").replace("https://", "").replace("/", "_")
        saved_file =f"nikto_scan_{safe_host}_{timestamp}"

        command = [
            'nikto',
            '-h', self.url,
            '-Tuning', '123a',
            '-timeout', '5',
            '-maxtime', '30',
            '-Format', 'json',
            '-output', saved_file
        ]

        try:
            subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            saved_file=f"{saved_file}.json"
            if not os.path.exists(saved_file):
                return {"error": "Nikto scan returned an empty output file."}
            
            with open(saved_file, encoding='utf-8') as f:
                data = json.load(f)
            return data[0].get('vulnerabilities', [])
        except (json.JSONDecodeError, FileNotFoundError) as e:
            return {"error": f"Unable to parse Nikto output: {e}"}
        finally:
            if os.path.exists(saved_file):
                os.remove(saved_file)
            return {}
    def wapiti_scan(self):
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            tmp_path = f.name
        command = [
            'wapiti',
            '-u', self.url,
            '--scope', 'url',
            '-m', 'sql,xss,xxe,ssrf,redirect,csrf,brute_login_form',
            '--max-links-per-page', '50',
            '--max-files-per-dir', '50',
            '--depth', '2',
            '--timeout', '10',
            '--max-scan-time', '120',
            '-f', 'json',
            '-o', tmp_path,
            '--no-bugreport'
        ]

        subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        try:
            with open(tmp_path, encoding='utf-8') as f:
                data = json.load(f)
                return data.get('vulnerabilities', {})
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
        finally:
            os.unlink(tmp_path)
            return {}
    def scanning(self,report:dict,scan_tech=True,scan_vuln=True):
        if scan_tech:
            report['technologies']=self.scrape_tech()
        if scan_vuln:
            report['vulnerabilities']=self.scrape_vuln()

if __name__ == "__main__":
    scraper=ToolScraper('https://moit.gov.vn')
    report={}
    start=time.perf_counter()
    report['waf']=scraper.scan_waf()
    execute_time=time.perf_counter()-start
    print(f'Thời gian quét waf: {execute_time:.6f} giây')
    print(json.dumps(report,indent=4,ensure_ascii=False))