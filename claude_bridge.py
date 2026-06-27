"""
Claude Bridge Server
====================
Local HTTP server yang menjembatani N8N dengan Claude Code CLI.
Jalankan script ini sebelum menjalankan N8N workflow.

Usage:
    python claude_bridge.py

Server berjalan di: http://127.0.0.1:PORT (default: 8765)
Endpoint: POST /reply
Body   : {"prompt": "your prompt here"}
Returns: {"reply": "...", "exitCode": 0, "error": ""}

Setup:
    1. Install Claude Code CLI: https://claude.ai/code
    2. Ganti CLAUDE_PATH di bawah sesuai path claude.exe di komputer kamu
    3. Jalankan: python claude_bridge.py
    4. Test: lihat README.md bagian "Test bridge"
"""

import http.server
import json
import subprocess
import sys

# ============================================================
# KONFIGURASI — Sesuaikan dengan setup lokal kamu
# ============================================================

# Path ke claude.exe — cari dengan: Get-Command claude (PowerShell)
CLAUDE_PATH = r"C:\Users\YOUR_USERNAME\.local\bin\claude.exe"

# Port server (pastikan tidak bentrok dengan aplikasi lain)
PORT = 8765

# Host (jangan diubah — localhost only untuk keamanan)
HOST = "127.0.0.1"

# Timeout per request dalam detik
TIMEOUT = 60

# ============================================================


class ClaudeBridgeHandler(http.server.BaseHTTPRequestHandler):

    def do_POST(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode("utf-8"))

            prompt = data.get("prompt", "").strip()

            if not prompt:
                self._send_error(400, "Field 'prompt' kosong atau tidak ada.")
                return

            print(f"[REQUEST] Prompt length: {len(prompt)} chars")

            result = subprocess.run(
                [CLAUDE_PATH, "-p", prompt],
                capture_output=True,
                text=True,
                timeout=TIMEOUT,
                encoding="utf-8",
                errors="replace"
            )

            raw_output = result.stdout.strip()
            clean_reply = raw_output.strip('"').strip()

            if result.returncode != 0:
                print(f"[WARNING] Claude exit code: {result.returncode}")
                print(f"[WARNING] stderr: {result.stderr[:200]}")

            print(f"[REPLY] {clean_reply[:80]}...")

            response = json.dumps({
                "reply": clean_reply,
                "exitCode": result.returncode,
                "error": result.stderr[:500] if result.stderr else ""
            }, ensure_ascii=False)

            self._send_json(200, response)

        except subprocess.TimeoutExpired:
            print("[ERROR] Claude CLI timeout!")
            self._send_error(504, "Claude CLI timeout setelah 60 detik.")

        except json.JSONDecodeError:
            self._send_error(400, "Request body bukan JSON valid.")

        except FileNotFoundError:
            print(f"[ERROR] Claude CLI tidak ditemukan di: {CLAUDE_PATH}")
            self._send_error(500, f"Claude CLI tidak ditemukan. Periksa CLAUDE_PATH di script.")

        except Exception as e:
            print(f"[ERROR] {str(e)}")
            self._send_error(500, str(e))

    def _send_json(self, code, body_str):
        encoded = body_str.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _send_error(self, code, message):
        body = json.dumps({"error": message}).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        print(f"[{self.address_string()}] {format % args}")


def main():
    print("=" * 50)
    print("  Claude Bridge Server")
    print("=" * 50)
    print(f"  Host    : {HOST}:{PORT}")
    print(f"  Claude  : {CLAUDE_PATH}")
    print(f"  Timeout : {TIMEOUT}s per request")
    print("=" * 50)
    print("  Tekan Ctrl+C untuk stop server")
    print()

    try:
        server = http.server.HTTPServer((HOST, PORT), ClaudeBridgeHandler)
        print(f"[OK] Server berjalan di http://{HOST}:{PORT}/reply")
        print("[OK] Siap menerima request dari N8N...\n")
        server.serve_forever()

    except OSError as e:
        if "10048" in str(e) or "Address already in use" in str(e):
            print(f"[ERROR] Port {PORT} sudah dipakai proses lain.")
            print(f"        Ganti PORT di script ini, atau kill proses yang memakai port tersebut.")
        else:
            print(f"[ERROR] {e}")
        sys.exit(1)

    except KeyboardInterrupt:
        print("\n[STOP] Server dihentikan.")
        sys.exit(0)


if __name__ == "__main__":
    main()
