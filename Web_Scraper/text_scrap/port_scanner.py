import subprocess
from urllib.parse import urlparse


class PortScanner:

    def __init__(self, timeout=70):
        self.timeout = timeout

    def parse_nmap_output(self, output):
        results = []

        for line in output.splitlines():
            if "/tcp" in line and "open" in line:
                parts = line.split()

                results.append({
                    "PORT": parts[0],
                    "STATE": parts[1],
                    "SERVICE": parts[2]
                })

        return results

    def port_scanner(self, url):
        domain = urlparse(url).netloc

        command = [
            "nmap",
            "-p", "1-1000",
            "-T3",
            domain
        ]

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            return {
                "PORTS": self.parse_nmap_output(result.stdout),
                "error": result.stderr
            }

        except subprocess.SubprocessError:
            return {
                "PORTS": [],
                "error": "Scan failed"
            }