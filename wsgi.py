"""PythonAnywhere va alwaysdata uchun WSGI kirish nuqtasi."""

from __future__ import annotations

import io
import re
from email.message import Message
from http import HTTPStatus
from typing import Callable, Iterable

from app import ADMIN_PASSWORD, OSINTHandler, PRODUCTION, init_database


if PRODUCTION and ADMIN_PASSWORD == "admin123":
    raise RuntimeError("Production uchun OSINT_ADMIN_PASSWORD ni kuchli parolga o'zgartiring.")

init_database()


class WSGIRequest(OSINTHandler):
    def __init__(self, environ: dict) -> None:
        self.command = str(environ.get("REQUEST_METHOD", "GET")).upper()
        query = str(environ.get("QUERY_STRING", ""))
        self.path = str(environ.get("PATH_INFO", "/")) + (f"?{query}" if query else "")
        self.request_version = str(environ.get("SERVER_PROTOCOL", "HTTP/1.1"))
        self.requestline = f"{self.command} {self.path} {self.request_version}"
        self.client_address = (str(environ.get("REMOTE_ADDR", "")), 0)
        self.server = None
        self.close_connection = True

        self.headers = Message()
        for key, value in environ.items():
            if key.startswith("HTTP_"):
                name = key[5:].replace("_", "-").title()
                self.headers[name] = str(value)
        if environ.get("CONTENT_TYPE"):
            self.headers["Content-Type"] = str(environ["CONTENT_TYPE"])
        if environ.get("CONTENT_LENGTH"):
            self.headers["Content-Length"] = str(environ["CONTENT_LENGTH"])

        max_length = 48_000_000 if re.fullmatch(r"/api/admin/requests/\d+/reply", str(environ.get("PATH_INFO", ""))) else 2_000_000 if environ.get("PATH_INFO") == "/api/telegram/webhook" else 1_000_000
        try:
            length = min(int(environ.get("CONTENT_LENGTH") or 0), max_length)
        except ValueError:
            length = 0
        body = environ["wsgi.input"].read(length) if length else b""
        self.rfile = io.BytesIO(body)
        self.wfile = io.BytesIO()
        self.response_status = HTTPStatus.OK
        self.response_headers: list[tuple[str, str]] = []

    def send_response(self, code: int, message: str | None = None) -> None:
        self.response_status = HTTPStatus(code)

    def send_header(self, keyword: str, value: str) -> None:
        self.response_headers.append((keyword, value))

    def end_headers(self) -> None:
        return

    def send_error(
        self,
        code: int,
        message: str | None = None,
        explain: str | None = None,
    ) -> None:
        status = HTTPStatus(code)
        text = message or status.phrase
        body = f"{status.value} {text}".encode("utf-8")
        self.send_response(status.value)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:
        return


def application(environ: dict, start_response: Callable) -> Iterable[bytes]:
    request = WSGIRequest(environ)
    handler = getattr(request, f"do_{request.command}", None)
    if handler is None:
        request.send_error(HTTPStatus.METHOD_NOT_ALLOWED)
    else:
        handler()

    status = request.response_status
    start_response(f"{status.value} {status.phrase}", request.response_headers)
    return [request.wfile.getvalue()]
