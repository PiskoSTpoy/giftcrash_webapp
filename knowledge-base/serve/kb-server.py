#!/usr/bin/env python3
"""
Локальный веб-сервер базы знаний «Аркона» с защитой логином/паролем.

Раздаёт папку knowledge-base/ (на уровень выше этого файла), чтобы работала
полная интерактивная версия (index.html) с боковым меню и поиском.
Вместе с Cloudflare-туннелем даёт доступ с телефонов по https-ссылке.

Запуск (обычно через start-windows.bat):
    python kb-server.py
Затем открыть http://localhost:8000  (локально)
или https-ссылку от cloudflared (с телефона).
"""
import base64
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

# ─── НАСТРОЙКИ ─────────────────────────────────────────────────────────────
LOGIN = "arkona"          # ← поменяйте логин
PASSWORD = "arkona2026"   # ← ОБЯЗАТЕЛЬНО поменяйте пароль
PORT = 8000
# ───────────────────────────────────────────────────────────────────────────

# Папка с базой знаний — на уровень выше папки serve/
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EXPECTED = "Basic " + base64.b64encode(f"{LOGIN}:{PASSWORD}".encode()).decode()


class AuthHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def do_AUTH(self):
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="Arkona KB"')
        self.send_header("Content-Length", "0")
        self.end_headers()

    def guard(self):
        if self.headers.get("Authorization") != EXPECTED:
            self.do_AUTH()
            return False
        return True

    def do_GET(self):
        if self.guard():
            super().do_GET()

    def do_HEAD(self):
        if self.guard():
            super().do_HEAD()

    def log_message(self, fmt, *args):
        pass  # тихий лог


if __name__ == "__main__":
    httpd = ThreadingHTTPServer(("0.0.0.0", PORT), AuthHandler)
    print("=" * 60)
    print("  База знаний «Аркона» запущена")
    print(f"  Локально:  http://localhost:{PORT}")
    print(f"  Логин:     {LOGIN}")
    print(f"  Пароль:    {PASSWORD}")
    print("  (поменяйте логин/пароль в начале файла kb-server.py)")
    print("  Остановить: закройте это окно")
    print("=" * 60)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
