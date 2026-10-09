# RKITI OSINT — AlwaysData’da botni saqlagan holda yangilash

Ushbu tartib `rkiti-osint` hisobidagi mavjud sayt, SQLite katalogi, Telegram foydalanuvchilari, murojaatlar, dalillar, mutaxassis javoblari va maxfiy environment qiymatlarini saqlab qoladi.

## Doimiy manzillar

- Loyiha: `/home/rkiti-osint/osint-navigator`
- Sayt: `https://rkiti-osint.alwaysdata.net`
- WSGI: `/home/rkiti-osint/osint-navigator/wsgi.py`
- Baza: `/home/rkiti-osint/osint-navigator/data/osint.sqlite3`
- JSON zaxira: `/home/rkiti-osint/osint-navigator/data/catalog-backup.json`
- Bot javob fayllari: `/home/rkiti-osint/osint-navigator/data/bot-replies`
- Webhook: `https://rkiti-osint.alwaysdata.net/api/telegram/webhook`

## 1. Yangilashdan oldingi tekshiruv

```bash
cd /home/rkiti-osint/osint-navigator
python --version
test -f app.py
test -f wsgi.py
test -f data/osint.sqlite3
ls -lh data/osint.sqlite3
```

Python 3.11 yoki undan yangi versiya tavsiya etiladi.

## 2. To‘liq zaxira

```bash
cd /home/rkiti-osint/osint-navigator
stamp="$(date +%Y%m%d-%H%M%S)"
backup_dir="/home/rkiti-osint/osint-navigator/backups/pre-update-$stamp"
mkdir -p "$backup_dir"
cp -a app.py wsgi.py static data "$backup_dir"/
test -f bot_setup.py && cp -a bot_setup.py "$backup_dir"/
test -f .env && cp -a .env "$backup_dir"/
printf 'Zaxira: %s\n' "$backup_dir"
ls -lah "$backup_dir"
```

Terminal chiqargan zaxira manzilini saqlab qo‘ying. `data/` papkasini SFTP orqali kompyuterga ham yuklab olish tavsiya etiladi.

## 3. Environment qiymatlarini tekshirish

AlwaysData panelidagi site environment maydonida quyidagi nomlar mavjud bo‘lishi kerak. Haqiqiy token, parol va secretni hujjat yoki ZIP faylga yozmang.

```text
OSINT_ADMIN_USERNAME
OSINT_ADMIN_PASSWORD
OSINT_PRODUCTION=1
OSINT_PUBLIC_URL=https://rkiti-osint.alwaysdata.net
OSINT_DB_PATH=/home/rkiti-osint/osint-navigator/data/osint.sqlite3
OSINT_JSON_BACKUP_PATH=/home/rkiti-osint/osint-navigator/data/catalog-backup.json
OSINT_BOT_REPLY_DIR=/home/rkiti-osint/osint-navigator/data/bot-replies
TELEGRAM_BOT_TOKEN
TELEGRAM_BOT_USERNAME=rkiti_osint_bot
TELEGRAM_WEBHOOK_SECRET
TELEGRAM_ADMIN_CHAT_ID
TELEGRAM_REQUIRE_APPROVAL=0
TELEGRAM_MAX_EVIDENCE=50
```

Mavjud `TELEGRAM_BOT_TOKEN` va `TELEGRAM_WEBHOOK_SECRET` qiymatlarini yangilash vaqtida almashtirmang. `TELEGRAM_REQUIRE_APPROVAL=1` faqat yangi foydalanuvchilar admin tasdig‘idan keyin botdan foydalanishi kerak bo‘lsa yoqiladi.

## 4. Paketni xavfsiz ochish

Paketni `updates/` papkasiga yuklang, so‘ng:

```bash
cd /home/rkiti-osint/osint-navigator
update_zip="updates/rkiti-osint-complete-bot-safe-update-20260914.zip"
update_dir="/home/rkiti-osint/osint-navigator/.update-20260914-full-height-hero"
if test -e "$update_dir"; then
    update_dir="${update_dir}-$(date +%H%M%S)"
fi
mkdir "$update_dir"
python -m zipfile -l "$update_zip"
python -m zipfile -e "$update_zip" "$update_dir"
test -f "$update_dir/app.py"
test -f "$update_dir/wsgi.py"
test -f "$update_dir/bot_setup.py"
test -f "$update_dir/static/index.html"
test -f "$update_dir/static/app.js"
test -f "$update_dir/static/styles.css"
test ! -e "$update_dir/data"
test ! -e "$update_dir/.env"
python -m py_compile "$update_dir/app.py" "$update_dir/wsgi.py" "$update_dir/bot_setup.py"
printf 'Tekshirilgan paket: %s\n' "$update_dir"
```

Buyruqlardan biri xato qaytarsa, fayllarni joriy loyiha ustiga ko‘chirmang.

## 5. Yangilanishni qo‘llash

```bash
cd /home/rkiti-osint/osint-navigator
cp -a "$update_dir/app.py" ./app.py
cp -a "$update_dir/wsgi.py" ./wsgi.py
cp -a "$update_dir/bot_setup.py" ./bot_setup.py
cp -a "$update_dir/static/." ./static/
python -m py_compile app.py wsgi.py bot_setup.py
test -s data/osint.sqlite3
test -w data/osint.sqlite3
```

`data/` papkasini yangilanish paketidan ko‘chirmang.

## 6. AlwaysData sayt sozlamasi

- Type: `Python WSGI`
- Application path: `/home/rkiti-osint/osint-navigator/wsgi.py`
- Working directory: `/home/rkiti-osint/osint-navigator`
- Python: mavjud 3.11+ versiyani saqlang

Environment qiymatlari saqlanganini tekshirib, `Web → Sites → Restart` tugmasini bosing.

## 7. Saytni tekshirish

```bash
python - <<'PY'
import json
import urllib.request

for path in ("/health", "/api/categories", "/api/tools", "/api/bot/config"):
    url = "https://rkiti-osint.alwaysdata.net" + path
    with urllib.request.urlopen(url, timeout=20) as response:
        body = response.read().decode("utf-8")
        print(response.status, path, body[:300])
PY
```

`/health` javobida `"ok": true` va `"bot_configured": true` bo‘lishi kerak. `/api/bot/config` javobida `https://t.me/rkiti_osint_bot` ko‘rinishi kerak.

## 8. Webhookni qayta tasdiqlash

Sayt muvaffaqiyatli ishga tushganidan keyingina:

```bash
cd /home/rkiti-osint/osint-navigator
python bot_setup.py
```

Kutiladigan natija:

```text
Bot ulandi: @rkiti_osint_bot
Webhook: https://rkiti-osint.alwaysdata.net/api/telegram/webhook
```

Webhook holatini maxfiy qiymatlarni chiqarmasdan tekshirish:

```bash
python - <<'PY'
import os
import app

result = app.telegram_call("getWebhookInfo")
if not result.get("ok"):
    raise SystemExit(result.get("description", "getWebhookInfo xatosi"))
info = result.get("result", {})
expected = os.environ["OSINT_PUBLIC_URL"].rstrip("/") + "/api/telegram/webhook"
print("Webhook:", info.get("url", ""))
print("Kutilgan:", expected)
print("Kutilayotgan update:", info.get("pending_update_count", 0))
print("Oxirgi xato:", info.get("last_error_message", "yo‘q"))
if info.get("url") != expected:
    raise SystemExit("Webhook manzili mos emas")
PY
```

## 9. Botning yakuniy funksional testi

1. `@rkiti_osint_bot` ichida `/start` yuboring.
2. Yo‘nalishlardan birini tanlang.
3. Bir nechta matn indikatorini alohida qatorlarda yuboring.
4. Rasm, video yoki hujjat yuboring.
5. `Mutaxassisga yuborish` tugmasini bosing.
6. Admin panelda murojaat va barcha dalillar ko‘ringanini tekshiring.
7. Faqat matn bilan javob yuborib ko‘ring.
8. Faqat fayl bilan javob yuborib ko‘ring.
9. Javob aynan murojaat yuborgan Telegram chatiga yetib kelganini tekshiring.

## 10. Loglar

AlwaysData panelida `Web → Sites → Logs` ni oching yoki:

```bash
ls -lt /home/rkiti-osint/admin/logs/uwsgi/
tail -n 100 /home/rkiti-osint/admin/logs/uwsgi/*.log
```

## 11. Rollback

Xatolik bo‘lsa, saqlangan aniq zaxira manzilini kiriting:

```bash
cd /home/rkiti-osint/osint-navigator
backup_dir="/home/rkiti-osint/osint-navigator/backups/pre-update-YYYYMMDD-HHMMSS"
cp -a "$backup_dir/app.py" ./app.py
cp -a "$backup_dir/wsgi.py" ./wsgi.py
test -f "$backup_dir/bot_setup.py" && cp -a "$backup_dir/bot_setup.py" ./bot_setup.py
cp -a "$backup_dir/static/." ./static/
python -m py_compile app.py wsgi.py bot_setup.py
```

Keyin saytni qayta ishga tushiring. Oddiy kod rollbackida `data/`ni qaytarmang: aks holda yangilanishdan keyin kelgan yangi murojaatlar yo‘qolishi mumkin.
