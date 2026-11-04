import http.server
import socket
import socketserver
import subprocess
import sys
from pathlib import Path

PORT = 8000
HTML_FILE = Path(__file__).parent / "index.html"
if not HTML_FILE.exists():
    HTML_FILE = Path(__file__).parent / "moscow_turgenev_walk.html"

def get_ip_addresses():
    ips = set()
    try:
        output = subprocess.check_output(["ifconfig"], text=True)
        for line in output.splitlines():
            line = line.strip()
            if line.startswith("inet ") and not line.startswith("inet 127."):
                parts = line.split()
                if len(parts) >= 2:
                    ips.add(parts[1])
    except Exception:
        pass

    if not ips:
        try:
            for info in socket.getaddrinfo(socket.gethostname(), None):
                ip = info[4][0]
                if not ip.startswith("127.") and ":" not in ip:
                    ips.add(ip)
        except Exception:
            pass

    # Sort so local Wi-Fi/Ethernet (192.168.x / 10.x / 172.x) comes first
    return sorted(ips, key=lambda ip: (not ip.startswith("192.168."), not ip.startswith("10."), ip))

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def _serve_html(self, send_body=True):
        if HTML_FILE.exists():
            content = HTML_FILE.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            if send_body:
                self.wfile.write(content)
            return True
        return False

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            if self._serve_html(send_body=True):
                return
        super().do_GET()

    def do_HEAD(self):
        if self.path in ("/", "/index.html"):
            if self._serve_html(send_body=False):
                return
        super().do_HEAD()

    def log_message(self, format, *args):
        sys.stderr.write(f"[{self.log_date_time_string()}] {self.address_string()} - {format % args}\n")

if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("0.0.0.0", PORT), CustomHandler) as httpd:
        print("=" * 54)
        print(f" Веб-сервер запущен на порту {PORT}")
        print("=" * 54)
        print(f" Локально (на этом компьютере):")
        print(f"   -> http://localhost:{PORT}")
        print(f"\n В локальной сети (Wi-Fi / LAN для телефона и др.):")
        for ip in get_ip_addresses():
            print(f"   -> http://{ip}:{PORT}")
        print("=" * 54)
        print(" Для остановки сервера нажмите Ctrl+C\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nСервер остановлен.")
