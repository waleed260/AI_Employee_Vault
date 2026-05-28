import http.server
import json
import os
import socket
import subprocess
import sys
from pathlib import Path
from datetime import datetime

VAULT = Path(__file__).parent.parent / "vault_data"
HOST = "0.0.0.0"
PORT = 8082

def count_files(folder):
    p = VAULT / folder
    return len([f for f in p.iterdir() if f.is_file()]) if p.exists() else 0

def check_port(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.settimeout(1)
        return s.connect_ex(("localhost", port)) == 0
    finally:
        s.close()

def get_last_logs():
    log_dir = VAULT / "Logs"
    logs = []
    if log_dir.exists():
        files = sorted(log_dir.glob("*.json"), reverse=True)[:5]
        for f in files:
            try:
                data = json.loads(f.read_text())
                if isinstance(data, list):
                    for entry in data[-5:]:
                        logs.append(entry)
                elif isinstance(data, dict):
                    logs.append(data)
            except:
                pass
    return logs[-10:]

def get_system_info():
    info = {}
    try:
        r = subprocess.run(["python3", "--version"], capture_output=True, text=True, timeout=2)
        info["python"] = r.stdout.strip() or r.stderr.strip()
    except:
        info["python"] = "unknown"
    try:
        r = subprocess.run(["node", "--version"], capture_output=True, text=True, timeout=2)
        info["node"] = r.stdout.strip() or r.stderr.strip()
    except:
        info["node"] = "not found"
    return info

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write((VAULT / "dashboard.html").read_bytes())
        elif self.path == "/api/dashboard":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            mcp_core = check_port(8080)
            mcp_social = check_port(8081)
            playwright = check_port(8808)
            data = {
                "vault": {
                    "needs_action": count_files("Needs_Action"),
                    "pending_approval": count_files("Pending_Approval"),
                    "inbox": count_files("Inbox"),
                    "done": count_files("Done"),
                    "rejected": count_files("Rejected"),
                    "plans": count_files("Plans"),
                },
                "services": {
                    "mcp_core": mcp_core,
                    "mcp_social": mcp_social,
                    "playwright": playwright,
                    "orchestrator": "checking..." if mcp_core else False,
                    "gmail": mcp_core,
                },
                "activity": [
                    {"time": e.get("timestamp","")[-8:], "action": e.get("action",""), "details": e.get("details","")}
                    for e in get_last_logs()
                ],
                "system": get_system_info(),
            }
            self.wfile.write(json.dumps(data, indent=2).encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not found")

    def log_message(self, format, *args):
        pass

if __name__ == "__main__":
    server = http.server.HTTPServer((HOST, PORT), Handler)
    print(f"Dashboard: http://localhost:{PORT}")
    server.serve_forever()
