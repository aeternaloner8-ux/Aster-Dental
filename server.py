"""
ВЕЛОРА — мини-сервер для лендинга velora-homes.html.

Без внешних зависимостей (только стандартная библиотека Python):
- отдаёт статические файлы сайта,
- принимает заявки с формы (POST /api/lead) и сохраняет их в SQLite (leads.db),
- показывает список заявок (GET /api/leads).

Запуск:   python3 server.py
Открыть:  http://127.0.0.1:8000
Заявки:   http://127.0.0.1:8000/api/leads
"""

import json
import os
import sqlite3
from datetime import datetime
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(ROOT, "leads.db")
PORT = 8000


def init_db():
    con = sqlite3.connect(DB_PATH)
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS leads (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT NOT NULL,
            phone      TEXT NOT NULL,
            email      TEXT,
            message    TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    con.commit()
    con.close()


def save_lead(d):
    con = sqlite3.connect(DB_PATH)
    cur = con.execute(
        "INSERT INTO leads (name, phone, email, message, created_at) VALUES (?, ?, ?, ?, ?)",
        (
            (d.get("name") or "").strip(),
            (d.get("phone") or "").strip(),
            (d.get("email") or "").strip(),
            (d.get("message") or "").strip(),
            datetime.now().isoformat(timespec="seconds"),
        ),
    )
    con.commit()
    rid = cur.lastrowid
    con.close()
    return rid


class Handler(SimpleHTTPRequestHandler):
    def _json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/", ""):
            self.path = "/velora-homes.html"
        if self.path.startswith("/api/leads"):
            con = sqlite3.connect(DB_PATH)
            con.row_factory = sqlite3.Row
            rows = [dict(r) for r in con.execute("SELECT * FROM leads ORDER BY id DESC")]
            con.close()
            return self._json(200, {"count": len(rows), "leads": rows})
        return super().do_GET()

    def do_POST(self):
        if self.path.rstrip("/") == "/api/lead":
            try:
                length = int(self.headers.get("Content-Length", 0))
                data = json.loads(self.rfile.read(length) or b"{}")
            except Exception:
                return self._json(400, {"ok": False, "error": "Некорректный JSON"})
            if not (data.get("name") or "").strip() or not (data.get("phone") or "").strip():
                return self._json(422, {"ok": False, "error": "Имя и телефон обязательны"})
            rid = save_lead(data)
            print(f"[заявка #{rid}] {data.get('name')} — {data.get('phone')}")
            return self._json(200, {"ok": True, "id": rid})
        return self._json(404, {"ok": False, "error": "Не найдено"})

    def log_message(self, fmt, *args):
        pass  # тихий лог (заявки печатаем сами)


if __name__ == "__main__":
    init_db()
    handler = partial(Handler, directory=ROOT)
    print(f"ВЕЛОРА: http://127.0.0.1:{PORT}   (Ctrl+C — остановить)")
    print(f"Заявки -> {DB_PATH}   список: http://127.0.0.1:{PORT}/api/leads")
    ThreadingHTTPServer(("127.0.0.1", PORT), handler).serve_forever()
