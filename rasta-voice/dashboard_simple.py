#!/usr/bin/env python3
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import subprocess
import os

PORT = 8085
PIPELINE_PROCESS = None

class DashboardHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = Path('dashboard.html').read_text()
            self.wfile.write(html.encode())
        elif self.path == '/api/transcripts':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            transcripts = []
            log_file = Path('live_transcripts.jsonl')
            if log_file.exists():
                with open(log_file) as f:
                    for i, line in enumerate(f, 1):
                        if line.strip():
                            data = json.loads(line)
                            data['id'] = i
                            transcripts.append(data)

            self.wfile.write(json.dumps({"entries": transcripts}).encode())
        elif self.path == '/api/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            status = {"running": PIPELINE_PROCESS is not None and PIPELINE_PROCESS.poll() is None}
            self.wfile.write(json.dumps(status).encode())
        else:
            super().do_GET()

    def do_POST(self):
        global PIPELINE_PROCESS
        if self.path == '/api/start':
            if PIPELINE_PROCESS is None or PIPELINE_PROCESS.poll() is not None:
                PIPELINE_PROCESS = subprocess.Popen([
                    str(Path('venv/Scripts/python.exe')),
                    'rasta_live.py'
                ])
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "started"}).encode())

        elif self.path == '/api/stop':
            if PIPELINE_PROCESS and PIPELINE_PROCESS.poll() is None:
                PIPELINE_PROCESS.terminate()
                PIPELINE_PROCESS = None
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "stopped"}).encode())

        elif self.path == '/api/clear':
            log_file = Path('live_transcripts.jsonl')
            if log_file.exists():
                log_file.unlink()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "cleared"}).encode())

        elif self.path == '/api/config':
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            config = json.loads(body)
            Path('voice_config.json').write_text(json.dumps(config, indent=2))
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "saved"}).encode())

        elif self.path == '/api/nuke':
            # Kill ALL rasta_live processes (emergency stop)
            try:
                # Kill tracked process
                if PIPELINE_PROCESS and PIPELINE_PROCESS.poll() is None:
                    PIPELINE_PROCESS.terminate()
                    PIPELINE_PROCESS = None

                # Kill any other rasta_live processes
                import psutil
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        cmdline = ' '.join(proc.info['cmdline'] or [])
                        if 'rasta_live' in cmdline:
                            proc.kill()
                    except:
                        pass

                killed = 'all processes terminated'
            except ImportError:
                # psutil not available, use shell command
                subprocess.run(['bash', '-c', 'pkill -9 -f rasta_live || kill -9 $(ps aux | grep rasta_live | grep -v grep | awk \'{print $2}\') 2>/dev/null'],
                             stderr=subprocess.DEVNULL)
                killed = 'kill command executed'

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": killed}).encode())

        else:
            self.send_error(404)

print(f"Dashboard starting on http://localhost:{PORT}")
HTTPServer(('0.0.0.0', PORT), DashboardHandler).serve_forever()
