from __future__ import annotations

import os
import re
import sys
from urllib.parse import urlparse

import app


def fail(message: str) -> None:
    print(f"Xato: {message}")
    raise SystemExit(1)


def main() -> None:
    public_url = os.environ.get("OSINT_PUBLIC_URL", "").strip().rstrip("/")
    if not app.TELEGRAM_BOT_TOKEN:
        fail("TELEGRAM_BOT_TOKEN muhit o'zgaruvchisi kiritilmagan.")
    if not app.TELEGRAM_WEBHOOK_SECRET:
        fail("TELEGRAM_WEBHOOK_SECRET muhit o'zgaruvchisi kiritilmagan.")
    if not re.fullmatch(r"[A-Za-z0-9_-]{16,256}", app.TELEGRAM_WEBHOOK_SECRET):
        fail("TELEGRAM_WEBHOOK_SECRET 16–256 ta harf, raqam, _ yoki - belgisidan iborat bo'lsin.")
    parsed = urlparse(public_url)
    if parsed.scheme != "https" or not parsed.netloc:
        fail("OSINT_PUBLIC_URL haqiqiy https manzil bo'lishi kerak.")

    identity = app.telegram_call("getMe")
    if not identity.get("ok"):
        fail(str(identity.get("description", "Bot tokeni tekshirilmadi.")))
    username = str(identity.get("result", {}).get("username", ""))
    webhook_url = f"{public_url}/api/telegram/webhook"
    webhook = app.telegram_call(
        "setWebhook",
        {
            "url": webhook_url,
            "secret_token": app.TELEGRAM_WEBHOOK_SECRET,
            "allowed_updates": ["message", "callback_query"],
            "drop_pending_updates": False,
        },
    )
    if not webhook.get("ok"):
        fail(str(webhook.get("description", "Webhook o'rnatilmadi.")))
    commands = app.telegram_call(
        "setMyCommands",
        {
            "commands": [
                {"command": "start", "description": "Botni boshlash"},
                {"command": "yangi", "description": "Yangi murojaat yaratish"},
                {"command": "yuborish", "description": "Dalillarni mutaxassisga yuborish"},
                {"command": "murojaatlarim", "description": "Murojaatlar holatini ko'rish"},
                {"command": "bekor", "description": "Faol murojaatni bekor qilish"},
                {"command": "yordam", "description": "Foydalanish tartibi"},
            ]
        },
    )
    if not commands.get("ok"):
        fail(str(commands.get("description", "Bot buyruqlari o'rnatilmadi.")))
    print(f"Bot ulandi: @{username}")
    print(f"Webhook: {webhook_url}")


if __name__ == "__main__":
    main()
