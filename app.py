from __future__ import annotations

import base64
import hashlib
import hmac
import json
import mimetypes
import os
import re
import secrets
import socket
import sqlite3
import threading
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
DATA_DIR = BASE_DIR / "data"
DB_PATH = Path(os.environ.get("OSINT_DB_PATH", DATA_DIR / "osint.sqlite3")).expanduser()
JSON_BACKUP_PATH = Path(
    os.environ.get("OSINT_JSON_BACKUP_PATH", DB_PATH.with_name("catalog-backup.json"))
).expanduser()
HOST = os.environ.get("OSINT_HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", os.environ.get("OSINT_PORT", "8000")))
ADMIN_USERNAME = os.environ.get("OSINT_ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("OSINT_ADMIN_PASSWORD", "admin123")
SEED_DEMO = os.environ.get("OSINT_SEED_DEMO", "0").strip().lower() in {"1", "true", "yes", "on"}
PRODUCTION = os.environ.get("OSINT_PRODUCTION", "0").strip().lower() in {"1", "true", "yes", "on"}
SECURE_COOKIE = PRODUCTION or os.environ.get("OSINT_SECURE_COOKIE", "0").strip().lower() in {"1", "true", "yes", "on"}
SESSION_TTL = 8 * 60 * 60
SESSIONS: dict[str, float] = {}
CATALOG_FORMAT = "osint-navigator-catalog"
CATALOG_VERSION = 1
CATALOG_BACKUP_LOCK = threading.Lock()
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_BOT_USERNAME = os.environ.get("TELEGRAM_BOT_USERNAME", "").strip().lstrip("@")
TELEGRAM_WEBHOOK_SECRET = os.environ.get("TELEGRAM_WEBHOOK_SECRET", "").strip()
TELEGRAM_ADMIN_CHAT_ID = os.environ.get("TELEGRAM_ADMIN_CHAT_ID", "").strip()
TELEGRAM_REQUIRE_APPROVAL = os.environ.get("TELEGRAM_REQUIRE_APPROVAL", "0").strip().lower() in {"1", "true", "yes", "on"}
TELEGRAM_MAX_EVIDENCE = max(1, min(int(os.environ.get("TELEGRAM_MAX_EVIDENCE", "50")), 100))
TELEGRAM_API_BASE = "https://api.telegram.org"
BOT_REPLY_DIR = Path(os.environ.get("OSINT_BOT_REPLY_DIR", DATA_DIR / "bot-replies")).expanduser()
BOT_LOCK = threading.RLock()


CATEGORY_SEED = [
    {
        "name": "Kriptoaktiv hamyon va tranzaksiya hashi",
        "slug": "crypto",
        "description": "Kriptoaktiv hamyon manzili yoki tranzaksiya hashi bo'yicha blokcheyn yozuvlari, mablag'lar harakati va reputatsiyaga oid ochiq ma'lumotlarni tekshirish.",
        "details": """Mazkur yo'nalishdagi vositalar yordamida quyidagi tekshiruvlarni amalga oshirish mumkin:
- BTC, ETH, TRON va boshqa qo'llab-quvvatlanadigan tarmoqlarda hamyon manzili yoki tranzaksiya hashini tekshirish.
- Tranzaksiya holati, vaqt belgisi, yuboruvchi va qabul qiluvchi manzillar hamda o'tkazilgan aktivlar haqidagi ochiq yozuvlarni ko'rish.
- Hamyonlar o'rtasidagi mablag'lar oqimi, ehtimoliy klaster va ochiq reputatsiya belgilarini qiyosiy tahlil qilish.

Natijalarni qayd etish tartibi:
- Tekshirilgan tarmoq, indikator, vosita URL manzili, sana-vaqt va ahamiyatli tranzaksiya identifikatorlarini qayd eting.
- Blokcheyn yozuvidagi manzil yoki klaster muayyan shaxsga tegishli ekanini qo'shimcha dalillarsiz tasdiqlangan deb hisoblamang.
- Muhim holatlarni kamida ikkita mustaqil explorer yoki boshqa ishonchli manba orqali qiyosiy tekshiring.""",
        "icon": "₿",
        "tags": ["BTC", "ETH", "TRON", "XMR"],
        "sort_order": 10,
    },
    {
        "name": "Telegram manbalarini tekshirish",
        "slug": "telegram",
        "description": "Telegram username, public ID, ochiq kanal va guruhlar bo'yicha profil, kontent, faollik hamda bog'lanishga oid ma'lumotlarni tekshirish.",
        "details": """Mazkur yo'nalishdagi vositalar yordamida quyidagi tekshiruvlarni amalga oshirish mumkin:
- Telegram username, public ID yoki ochiq havola bo'yicha mavjud profil, kanal yoxud guruh yozuvlarini aniqlash.
- Ochiq kanal tavsifi, postlar, havolalar, auditoriya ko'rsatkichlari va faollik davrlarini tekshirish.
- Turli xizmatlarda qayd etilgan ochiq ma'lumotlarni qiyoslash va keyingi tekshiruv yo'nalishlarini belgilash.

Natijalarni qayd etish tartibi:
- Username, public ID, manba havolasi, ko'rilgan sana-vaqt va tekshiruv uchun ahamiyatli ochiq yozuvlarni qayd eting.
- Tashqi botlarga parol, autentifikatsiya kodi, access token, tergov siri yoki oshkor etilishi cheklangan ma'lumot yubormang.
- Bir xil username yoki nom mosligi shaxs aynanligini tasdiqlamasligini inobatga olib, natijani mustaqil manbalar bilan tekshiring.""",
        "icon": "telegram",
        "tags": ["Username", "Kanal", "ID"],
        "sort_order": 20,
    },
    {
        "name": "Username va ijtimoiy tarmoq profillari",
        "slug": "username",
        "description": "Username, shaxs nomi, email yoki telefon raqami bo'yicha ochiq platformalardagi ehtimoliy profillar va username mavjudligini tekshirish.",
        "details": """Mazkur yo'nalishdagi vositalar yordamida quyidagi tekshiruvlarni amalga oshirish mumkin:
- Username turli ochiq platformalarda ishlatilayotgani yoki foydalanish uchun mavjudligini dastlabki tekshirish.
- Shaxs nomi, email yoki telefon raqami bo'yicha ehtimoliy ochiq profil va havolalarni aniqlash.
- Topilgan profillardagi nom, tasvir, tavsif, havola va boshqa ochiq identifikatorlarni o'zaro qiyoslash.

Natijalarni qayd etish tartibi:
- So'rov qiymati, platforma, profil URL manzili, ko'rilgan sana-vaqt va moslikni asoslovchi belgilarni qayd eting.
- Bir xil username yoki aloqa identifikatori profillarning aynan bir shaxsga tegishli ekanini mustaqil ravishda tasdiqlamaydi.
- Har bir ahamiyatli moslikni qo'shimcha identifikator va kamida bitta mustaqil manba orqali tekshiring.""",
        "icon": "@",
        "tags": ["Username", "Social", "Profil"],
        "sort_order": 30,
    },
    {
        "name": "Qidiruv tizimlari",
        "slug": "search",
        "description": "Google Search, Yandex Search, Microsoft Bing va 2GIS orqali shaxs, tashkilot, aloqa identifikatori, manzil, texnik indikator yoki kalit so'zga oid ochiq ma'lumotlarni qidirish.",
        "details": """Mazkur yo'nalishdagi vositalar yordamida quyidagi tekshiruvlarni amalga oshirish mumkin:
- Shaxs nomi, username, telefon raqami, email, IP manzil, domen, URL yoki boshqa kalit so'z bo'yicha indekslangan ochiq manbalarni qidirish.
- Qidiruv operatorlari yordamida natijalarni muayyan domen, fayl turi, sana yoki aniq ibora bo'yicha aniqlashtirish.
- Turli qidiruv tizimlari natijalarini qiyoslash orqali qo'shimcha manba va bog'lanishlarni aniqlash.
- 2GIS orqali tashkilot nomi, manzil yoki telefon raqami bo'yicha ochiq xarita va katalog yozuvlarini tekshirish.

Natijalarni qayd etish tartibi:
- Ahamiyatli natijaning sarlavhasi, URL manzili, qidiruv so'rovi hamda tekshiruv sanasi va vaqtini qayd eting.
- Qidiruv natijasidagi ma'lumotni asl manbada tekshiring va kamida bitta mustaqil manba bilan qiyoslang.
- Ism yoki boshqa belgi mosligi shaxs aynanligini mustaqil ravishda tasdiqlamasligini inobatga oling.
- Xarita va katalogdagi foydalanuvchi tahriri hamda ma'lumotning yangilangan sanasini inobatga oling.""",
        "icon": "search",
        "tags": ["Google", "Yandex", "Bing", "2GIS"],
        "sort_order": 35,
    },
    {
        "name": "Domen, IP va URL ma'lumotlari",
        "slug": "network",
        "description": "Domen, IP yoki URL bo'yicha ro'yxatdan o'tish, DNS, sertifikat, arxiv, infratuzilma va reputatsiyaga oid ochiq ma'lumotlarni tekshirish.",
        "details": """Mazkur yo'nalishdagi vositalar yordamida quyidagi tekshiruvlarni amalga oshirish mumkin:
- Domen va IP resurslari bo'yicha WHOIS yoki RDAP ro'yxatga olish yozuvlari, status va vakolatli xizmatlarni tekshirish.
- DNS yozuvlari, subdomenlar, Certificate Transparency ma'lumotlari va bog'liq infratuzilmani aniqlash.
- URL yoki domenning arxiv nusxalari, skan natijalari, yo'naltirishlari va ochiq reputatsiya belgilarini qiyoslash.

Natijalarni qayd etish tartibi:
- Tekshirilgan indikator, so'rov turi, vosita URL manzili, sana-vaqt va muhim texnik yozuvlarni qayd eting.
- Ochiq skan xizmatiga maxfiy yoki xizmatga oid URL yuborishdan oldin uning oshkor bo'lish xavfini baholang.
- Texnik resursning muayyan shaxs yoki tashkilotga tegishliligini qo'shimcha dalillarsiz tasdiqlangan deb hisoblamang.""",
        "icon": "⌁",
        "tags": ["IP", "Domen", "URL", "DNS"],
        "sort_order": 40,
    },
    {
        "name": "APK, zararli fayl va phishing havolalarni tekshirish",
        "slug": "mobile-threats",
        "description": "APK, mobil ilova paketi, fayl, hash yoki shubhali URL bo'yicha zararli kod, xavfli ruxsatlar, reputatsiya va phishing belgilarini tekshirish.",
        "details": """Mazkur yo'nalishdagi vositalar yordamida quyidagi tekshiruvlarni amalga oshirish mumkin:
- APK yoki AAB faylining manifesti, ruxsatlari, komponentlari, sertifikati, kodi va resurslaridagi ehtimoliy xavf belgilarini dastlabki tahlil qilish.
- Fayl hashi, paket nomi va boshqa identifikatorlar bo'yicha mavjud reputatsiya hamda avvalgi tahlil natijalarini tekshirish.
- Shubhali URL bo'yicha yo'naltirishlar zanjiri, sahifa tasviri, tarmoq so'rovlari, reputatsiya va phishing belgilarini qiyosiy tahlil qilish.

Natijalarni qayd etish tartibi:
- Asl faylni o'zgartirmasdan saqlang; uning kriptografik hash qiymati, olingan manbasi, vosita URL manzili va tekshiruv sana-vaqtini qayd eting.
- Tergov siri, xizmatga oid yoki oshkor etilishi cheklangan fayl va URLlarni public tahlil xizmatiga yuborishdan oldin tegishli vakolat hamda ma'lumotning oshkor bo'lish xavfini baholang; imkon qadar avval hash va mavjud hisobot bo'yicha qidiring.
- Avtomatik tahlil natijasini yakuniy xulosa deb hisoblamang; ahamiyatli holatlarni kamida bitta mustaqil vosita va zarur hollarda ajratilgan ekspert muhitida tekshiring.""",
        "icon": "auto",
        "tags": ["APK", "Android", "Phishing", "URL"],
        "sort_order": 50,
    },
    {
        "name": "Rasm, fayl va metadata tekshiruvi",
        "slug": "media",
        "description": "Rasm yoki fayl bo'yicha o'xshash manbalar, EXIF va metadata, ehtimoliy tahrir belgilari hamda hash reputatsiyasini tekshirish.",
        "details": """Mazkur yo'nalishdagi vositalar yordamida quyidagi tekshiruvlarni amalga oshirish mumkin:
- Reverse image search yordamida o'xshash tasvirlar, avvalgi e'lonlar va ehtimoliy dastlabki manbalarni aniqlash.
- Rasm yoki fayldagi EXIF va boshqa metadata yozuvlarini ko'rish hamda ularning mavjudligini qayd etish.
- Tasvirdagi siqilish farqlari, ehtimoliy tahrir belgilari va fayl hashining ochiq reputatsiyasini dastlabki tekshirish.

Natijalarni qayd etish tartibi:
- Asl fayl nusxasini o'zgartirmasdan saqlang, imkon qadar uning kriptografik hash qiymatini va olingan manbasini qayd eting.
- Metadata mavjud emasligi fayl albatta tahrirlanganini, tahrir belgisi esa muayyan harakatni mustaqil ravishda tasdiqlamasligini inobatga oling.
- Vosita URL manzili, tekshiruv sanasi, qo'llangan usul va ahamiyatli natijalarni qayd eting.""",
        "icon": "◈",
        "tags": ["Rasm", "EXIF", "Fayl", "Hash"],
        "sort_order": 60,
    },
]


TOOL_SEED = [
    ("Blockchair", "blockchair", "crypto", "Ko'p blokcheynli explorer va manzil yoki tranzaksiya qidiruvi.", "https://blockchair.com/", "https://blockchair.com/search?q={query}", "▦", ["wallet", "tx-hash"], ["BTC", "ETH", "BCH", "LTC"], ["Explorer", "Multi-chain"], "free", False, True, 10),
    ("Etherscan", "etherscan", "crypto", "Ethereum manzillari, tokenlar, kontraktlar va tranzaksiyalar.", "https://etherscan.io/", "https://etherscan.io/search?f=0&q={query}", "Ξ", ["wallet", "tx-hash", "contract"], ["ETH", "EVM"], ["Explorer", "Smart contract"], "free", False, True, 20),
    ("OXT.me", "oxt", "crypto", "Bitcoin tranzaksiya grafigi va blokcheyn tahlili.", "https://oxt.me/", "", "◫", ["wallet", "tx-hash"], ["BTC"], ["Graph", "Privacy"], "free", False, True, 30),
    ("Bitcoin Who's Who", "bitcoin-whos-who", "crypto", "Bitcoin manzili reputatsiyasi va abuse hisobotlarini tekshirish.", "https://bitcoinwhoswho.com/", "", "₿", ["wallet"], ["BTC"], ["Reputation", "Abuse"], "free-tier", False, False, 50),
    ("Blockscan", "blockscan", "crypto", "EVM tarmoqlari bo'ylab manzil va tranzaksiyalarni qidirish.", "https://blockscan.com/", "", "⬡", ["wallet", "tx-hash"], ["EVM"], ["Multi-chain", "Explorer"], "free", False, False, 60),
    ("Arkham Intelligence", "arkham", "crypto", "Kripto subyektlari, manzillar va oqimlarni vizual tahlil qilish.", "https://platform.arkhamintelligence.com/", "", "A", ["wallet", "tx-hash", "entity"], ["Multi-chain"], ["Graph", "Attribution"], "free-tier", True, True, 100),
    ("MetaSleuth", "metasleuth", "crypto", "Kripto mablag' oqimlarini grafik ko'rinishda kuzatish.", "https://metasleuth.io/", "", "M", ["wallet", "tx-hash"], ["Multi-chain"], ["Graph", "Tracing"], "free-tier", True, True, 110),
    ("TRONSCAN", "tronscan", "crypto", "TRON manzil, token, kontrakt va tranzaksiyalari explorer'i.", "https://tronscan.org/", "https://tronscan.org/#/search-result?query={query}", "T", ["wallet", "tx-hash", "contract"], ["TRON", "TRC20"], ["Explorer", "Token"], "free", False, True, 130),

    ("Telegram ID orqali qidirish", "telegram-web", "telegram", "Telegram ID yoki ochiq profil identifikatori bo'yicha mavjud ma'lumotlarni tekshirish.", "https://telegram.me/fs_officialtbot?start=010183759D5600000000", "https://telegram.me/fs_officialtbot?start=010183759D5600000000", "telegram", ["telegram-id"], ["Telegram"], ["ID"], "free", False, True, 10),
    ("TGStat", "tgstat", "telegram", "Telegram kanallari statistikasi, postlar va auditoriya dinamikasi.", "https://tgstat.com/", "", "TG", ["telegram-username", "telegram-channel"], ["Telegram"], ["Analytics", "Channel"], "free-tier", False, True, 20),
    ("Telegram Username orqali qidirish", "username-telegram", "telegram", "Telegram username asosida profilga oid ochiq ma'lumotlarni tekshirish.", "https://telegram.me/fs_officialtbot?start=010183759D5600000000", "https://telegram.me/fs_officialtbot?start=010183759D5600000000", "telegram", ["telegram-username"], ["Telegram"], ["Username", "Telegram"], "free", False, True, 30),
    ("Lyzem", "lyzem", "telegram", "Public Telegram xabarlari va kanallari bo'yicha qidiruv.", "https://lyzem.com/", "", "L", ["telegram-username", "telegram-channel", "keyword"], ["Telegram"], ["Search", "Messages"], "free", False, False, 50),
    ("Kropiva UA Bot", "kropiva-uabot", "telegram", "Telegram orqali taqdim etiladigan ochiq qidiruv xizmatini vakolat doirasida tekshirish uchun ochish.", "https://t.me/Kropiva_uabot", "", "telegram", ["telegram-username", "username", "phone", "email", "keyword"], ["Telegram"], ["Bot", "External service", "Manual verification"], "free-tier", True, True, 60),
    ("TGShield", "tgshield", "telegram", "TGShield tashqi yo'naltirish sahifasi orqali taqdim etiladigan Telegram tekshiruv xizmatini ochish.", "https://sherlock1.pro/tgshield/go.php", "", "text:TG", ["telegram-username", "username", "phone", "email", "keyword"], ["Telegram"], ["External redirect", "Manual verification"], "free-tier", True, True, 70),
    ("Fun Xeyes Bot", "fun-xeyes-bot", "telegram", "Telegram botida mavjud ochiq qidiruv imkoniyatlarini vakolat doirasida tekshirish uchun ochish.", "https://telegram.me/fun_xeyes_bot?start=010183759D5600000000", "", "telegram", ["telegram-username", "username", "phone", "email", "keyword"], ["Telegram"], ["Bot", "External service", "Manual verification"], "free-tier", True, True, 80),

    ("Instant Username Search", "instant-username", "username", "Username mavjudligini bir nechta public platformada tezkor tekshirish.", "https://instantusername.com/", "https://instantusername.com/?q={query}", "auto", ["username", "telegram-username"], ["Social media"], ["Accounts", "Availability"], "free", False, True, 10),
    ("Fingerprint.to", "fingerprint-to", "username", "Username, email manzil yoki telefon raqami bo'yicha ochiq platformalardagi ehtimoliy mosliklarni qidirish.", "https://fingerprint.to/demo", "", "auto", ["name", "username", "email", "phone"], ["Social media"], ["Identity", "Accounts"], "free-tier", False, True, 80),
    ("IDCrawl", "idcrawl", "username", "Shaxs nomi, username, email manzil yoki telefon raqami bo'yicha ochiq profil va ma'lumotlarni qidirish.", "https://www.idcrawl.com/", "", "auto", ["name", "username", "email", "phone"], ["Social media", "Web"], ["People search", "Accounts"], "free", False, True, 90),

    ("Google Search", "google-search", "search", "Shaxs nomi, username va boshqa indikatorlar bo'yicha Google indeksidagi ochiq veb-manbalarni qidirish.", "https://www.google.com/", "https://www.google.com/search?q={query}", "google", ["name", "username", "telegram-username", "email", "phone", "ip", "asn", "domain", "url", "wallet", "tx-hash", "file-hash", "keyword"], ["Web"], ["Search", "Indexed data"], "free", False, True, 10),
    ("Yandex Search", "yandex-search", "search", "Shaxs nomi, username va boshqa indikatorlar bo'yicha Yandex indeksidagi ochiq veb-manbalarni qidirish.", "https://yandex.ru/", "https://yandex.ru/search/?text={query}", "auto", ["name", "username", "telegram-username", "email", "phone", "ip", "asn", "domain", "url", "wallet", "tx-hash", "file-hash", "keyword"], ["Web"], ["Search", "Indexed data"], "free", False, True, 20),
    ("Microsoft Bing", "bing", "search", "Shaxs nomi, username va boshqa indikatorlar bo'yicha Microsoft Bing indeksidagi ochiq veb-manbalarni qidirish.", "https://www.bing.com/", "https://www.bing.com/search?q={query}", "auto", ["name", "username", "telegram-username", "email", "phone", "ip", "asn", "domain", "url", "wallet", "tx-hash", "file-hash", "keyword"], ["Web"], ["Search", "Indexed data"], "free", False, True, 30),

    ("crt.sh", "crtsh", "network", "Certificate Transparency jurnallaridan domen va subdomen izlash.", "https://crt.sh/", "https://crt.sh/?q={query}", "crt", ["domain", "certificate"], ["TLS"], ["Certificates", "Subdomains"], "free", False, True, 60),
    ("DNSDumpster", "dnsdumpster", "network", "DNS yozuvlari va domen xaritasini tekshirish.", "https://dnsdumpster.com/", "", "DNS", ["domain"], ["DNS"], ["Mapping", "Records"], "free", False, False, 70),
    ("WHOIS", "whois", "network", "Domen ro'yxatdan o'tish ma'lumotlarini ko'rish.", "https://who.is/", "https://who.is/whois/{query}", "W", ["domain", "ip"], ["Internet"], ["Registration", "Ownership"], "free", False, False, 80),
    ("Wayback Machine", "wayback-machine", "network", "Domen yoki URLning arxivlangan tarixiy nusxalarini aniqlash va o'zgarishlarni qiyosiy tekshirish.", "https://web.archive.org/", "https://web.archive.org/web/*/{query}", "auto", ["url", "domain"], ["Web"], ["Archive", "History"], "free", False, True, 110),
    (".UZ domen ma'muriyati", "cctld-uz", "network", ".UZ domen nomining mavjudligi va public ro'yxatga olish holatiga oid ma'lumotlarni tekshirish.", "https://new.cctld.uz/", "", "auto", ["domain"], ["DNS", ".UZ"], ["Registration", "Uzbekistan"], "free", False, True, 120),
    ("ICANN Lookup", "icann-lookup", "network", "Domen yoki IP resursiga oid public ro'yxatga olish ma'lumotlarini RDAP orqali tekshirish.", "https://lookup.icann.org/", "https://lookup.icann.org/en/lookup?name={query}", "auto", ["domain", "ip"], ["Internet", "RDAP"], ["Registration", "Registry"], "free", False, True, 130),
    ("RDAP.org", "rdap", "network", "Domen, IP manzil yoki ASN bo'yicha tuzilmaviy public ro'yxatga olish ma'lumotlarini olish.", "https://about.rdap.org/", "https://rdap.org/domain/{query}", "auto", ["domain", "ip", "asn"], ["Internet", "RDAP"], ["Registration", "Structured data"], "free", False, True, 140),

    ("2GIS", "2gis", "search", "Manzil, tashkilot nomi yoki telefon raqami bo'yicha ochiq xarita va tashkilot ma'lumotlarini tekshirish.", "https://2gis.uz/", "https://2gis.uz/tashkent/search/{query}", "auto", ["address", "name", "phone", "keyword"], ["Uzbekistan", "Map"], ["Places", "Organizations"], "free", False, True, 40),

    ("MobSF Live", "mobsf-live", "mobile-threats", "APK yoki AAB faylining kodi, manifesti, ruxsatlari, sertifikati va ehtimoliy xavf belgilarini tahlil qilish.", "https://mobsf.live/", "", "auto", ["apk", "aab", "file", "file-hash"], ["Android", "iOS"], ["Static analysis", "Dynamic analysis"], "free", False, True, 10),
    ("Koodous", "koodous", "mobile-threats", "APK, paket nomi yoki hash bo'yicha Android ilovalari reputatsiyasi va mavjud tahlil ma'lumotlarini tekshirish.", "https://koodous.com/", "", "auto", ["apk", "file", "file-hash", "package"], ["Android"], ["APK repository", "Malware research"], "free-tier", True, True, 20),
    ("VirusTotal URL", "virustotal-url", "mobile-threats", "URL, domen va IP reputatsiyasini bir nechta xavfsizlik manbasi orqali tekshirish.", "https://www.virustotal.com/gui/home/url", "https://www.virustotal.com/gui/search/{query}", "VT", ["url", "domain", "ip", "file-hash"], ["Internet"], ["Reputation", "Threat intelligence"], "free-tier", False, True, 30),
    ("urlscan.io", "urlscan", "mobile-threats", "Shubhali veb-sahifa, yo'naltirishlar va tarmoq so'rovlarini xavfsiz muhitda tahlil qilish.", "https://urlscan.io/", "https://urlscan.io/search/#page.domain:{query}", "u", ["url", "domain", "ip"], ["Web"], ["Screenshot", "Network requests"], "free-tier", False, True, 40),
    ("VirusTotal Files", "virustotal-files", "mobile-threats", "Fayl yoki hashni antivirus va threat-intelligence manbalari orqali tekshirish.", "https://www.virustotal.com/gui/home/upload", "https://www.virustotal.com/gui/search/{query}", "VT", ["apk", "file", "file-hash"], ["Files", "Android"], ["Malware", "Reputation"], "free-tier", False, True, 50),

    ("Google Lens", "google-lens", "media", "Rasm bo'yicha o'xshash tasvir va manbalarni qidirish.", "https://lens.google.com/", "", "G", ["image"], ["Images"], ["Reverse search", "Visual"], "free", False, True, 10),
    ("Yandex Images", "yandex-images", "media", "Reverse image search yordamida o'xshash tasvirlar va ehtimoliy manbalarni aniqlash.", "https://yandex.com/images/", "", "Y", ["image"], ["Images"], ["Reverse search", "Visual"], "free", False, True, 20),
    ("EXIF.tools", "exif-tools", "media", "Rasm va fayllardagi EXIF metama'lumotlarini ko'rish.", "https://exif.tools/", "", "EX", ["image", "file"], ["Metadata"], ["EXIF", "File"], "free", False, True, 40),
    ("FotoForensics", "fotoforensics", "media", "Rasm qatlamlari va siqilish izlarini dastlabki tahlil qilish.", "https://fotoforensics.com/", "", "FF", ["image"], ["Images"], ["ELA", "Forensics"], "free", False, True, 50),
]


FORMAL_TOOL_DESCRIPTIONS = {
    "blockchair": "Bir nechta blokcheyn bo'yicha hamyon manzili va tranzaksiya hashiga oid ma'lumotlarni tekshirish.",
    "etherscan": "Ethereum hamyon manzili, token, smart-kontrakt va tranzaksiyaga oid ma'lumotlarni tekshirish.",
    "oxt": "Bitcoin tranzaksiyalari grafigi va blokcheyn ma'lumotlarini tahlil qilish.",
    "bitcoin-whos-who": "Bitcoin manzili reputatsiyasi va abuse hisobotlariga oid ochiq ma'lumotlarni tekshirish.",
    "blockscan": "EVM tarmoqlari bo'yicha hamyon manzili va tranzaksiyaga oid ma'lumotlarni tekshirish.",
    "arkham": "Kriptoaktiv subyektlari, hamyon manzillari va mablag'lar oqimini vizual tahlil qilish.",
    "metasleuth": "Kriptoaktivlar harakatini grafik shaklda kuzatish va o'zaro bog'liqliklarni tahlil qilish.",
    "tronscan": "TRON hamyon manzili, token, smart-kontrakt va tranzaksiyaga oid ma'lumotlarni tekshirish.",
    "telegram-web": "Telegram public ID yoki ochiq profil identifikatori bo'yicha mavjud ma'lumotlarni tekshirish.",
    "tgstat": "Telegram kanallari statistikasi, postlar va auditoriya dinamikasini tahlil qilish.",
    "username-telegram": "Telegram username asosida public profilga oid ochiq ma'lumotlarni tekshirish.",
    "telemetr": "Telegram kanallari katalogi, statistikasi va ochiq faollik ko'rsatkichlarini tahlil qilish.",
    "lyzem": "Public Telegram xabarlari va kanallariga oid ochiq ma'lumotlarni aniqlash.",
    "kropiva-uabot": "Telegram orqali taqdim etiladigan tashqi qidiruv xizmatining mavjud public imkoniyatlarini vakolat doirasida tekshirish.",
    "tgshield": "TGShield tashqi yo'naltirish sahifasi orqali taqdim etiladigan Telegram tekshiruv xizmatini vakolat doirasida ochish.",
    "fun-xeyes-bot": "Telegram botida taqdim etiladigan tashqi qidiruv xizmatining mavjud public imkoniyatlarini vakolat doirasida tekshirish.",
    "instant-username": "Username bir nechta public platformada ro'yxatdan o'tkazilgan yoki foydalanish uchun mavjud ekanini dastlabki tekshirish.",
    "google-search": "Shaxs nomi, username va boshqa indikatorlar bo'yicha Google indeksidagi ochiq veb-manbalarni qidirish.",
    "yandex-search": "Shaxs nomi, username va boshqa indikatorlar bo'yicha Yandex indeksidagi ochiq veb-manbalarni qidirish.",
    "bing": "Shaxs nomi, username va boshqa indikatorlar bo'yicha Microsoft Bing indeksidagi ochiq veb-manbalarni qidirish.",
    "fingerprint-to": "Username, email manzil yoki telefon raqami bo'yicha ochiq platformalardagi ehtimoliy mosliklarni qidirish.",
    "idcrawl": "Shaxs nomi, username, email manzil yoki telefon raqami bo'yicha ochiq profil va ma'lumotlarni qidirish.",
    "mobsf-live": "APK yoki AAB faylining kodi, manifesti, ruxsatlari, sertifikati va ehtimoliy zararli belgilarini dastlabki tahlil qilish.",
    "koodous": "APK, paket nomi yoki hash bo'yicha Android ilovalari reputatsiyasi va mavjud tahlil ma'lumotlarini tekshirish.",
    "virustotal-url": "URL, domen va IP reputatsiyasini bir nechta xavfsizlik manbasi orqali tekshirish.",
    "urlscan": "Shubhali veb-sahifa, yo'naltirishlar, sahifa tasviri va tarmoq so'rovlarini tahlil qilish.",
    "crtsh": "Certificate Transparency jurnallari orqali domen va subdomenlarni aniqlash.",
    "dnsdumpster": "DNS yozuvlari va domen infratuzilmasi xaritasiga oid ma'lumotlarni tekshirish.",
    "whois": "Domenning ro'yxatdan o'tkazilishiga oid ochiq WHOIS ma'lumotlarini tekshirish.",
    "wayback-machine": "Domen yoki URLning arxivlangan tarixiy nusxalarini aniqlash va o'zgarishlarni qiyosiy tekshirish.",
    "cctld-uz": ".UZ domen nomining mavjudligi va public ro'yxatga olish holatiga oid ma'lumotlarni tekshirish.",
    "icann-lookup": "Domen yoki IP resursiga oid public ro'yxatga olish ma'lumotlarini RDAP orqali tekshirish.",
    "rdap": "Domen, IP manzil yoki ASN bo'yicha tuzilmaviy public ro'yxatga olish ma'lumotlarini olish.",
    "2gis": "Manzil, tashkilot nomi yoki telefon raqami bo'yicha ochiq xarita va tashkilot ma'lumotlarini tekshirish.",
    "google-lens": "Rasmga o'xshash tasvirlar va ehtimoliy dastlabki manbalarni aniqlash.",
    "yandex-images": "Reverse image search yordamida o'xshash tasvirlar va ehtimoliy manbalarni aniqlash.",
    "exif-tools": "Rasm va fayllardagi EXIF hamda boshqa metadata ma'lumotlarini tekshirish.",
    "fotoforensics": "Rasm qatlamlari, siqilish farqlari va ehtimoliy tahrir belgilarini dastlabki tahlil qilish.",
    "virustotal-files": "Fayl yoki hash qiymatini antivirus va threat-intelligence manbalari orqali tekshirish.",
}


REQUESTED_TOOL_DETAILS = {
    "mobsf-live": """Tekshiruv doirasida amalga oshiriladigan harakatlar:
- APK yoki AAB faylining manifesti, so'ralgan ruxsatlari, komponentlari, sertifikati, kodi va resurslarini statik tahlil qilish.
- Ehtimoliy zararli API chaqiruvlari, qattiq kodlangan kalitlar, zaif sozlamalar, kuzatuv kutubxonalari va tarmoq manzillarini aniqlash.
- Qo'llab-quvvatlanadigan muhitda dinamik tahlil natijalari orqali ilovaning tarmoq va xulq-atvor belgilarini tekshirish.

Natijadan foydalanish tartibi:
- Asl faylning hash qiymati, olingan manbasi, tahlil sanasi, MobSF hisobot identifikatori va ahamiyatli topilmalar qayd etiladi.
- Public MobSF nusxasiga tergov siri yoki oshkor etilishi cheklangan fayl yuborilmaydi; bunday material alohida va nazorat qilinadigan MobSF muhitida tekshiriladi.
- Avtomatik topilma yakuniy ekspert xulosasi hisoblanmaydi va zarur hollarda boshqa vosita hamda qo'lda kod tahlili bilan tasdiqlanadi.""",
    "koodous": """Tekshiruv doirasida amalga oshiriladigan harakatlar:
- APK fayli hashi, paket nomi yoki boshqa identifikator bo'yicha Koodous bazasidagi mavjud yozuv va tahlil natijalarini qidirish.
- Ilova versiyasi, sertifikat, ruxsatlar, aniqlangan xatti-harakatlar va hamjamiyat reputatsiyasiga oid ochiq belgilarni qiyoslash.
- Bir paket yoki sertifikatga bog'liq boshqa APK namunalarini keyingi tekshiruv yo'nalishi sifatida aniqlash.

Natijadan foydalanish tartibi:
- Hash, paket nomi, tekshiruv URL manzili, sana-vaqt va ahamiyatli natijalar qayd etiladi.
- Maxfiy faylni public xizmatga yuklash o'rniga avval hash va mavjud hisobot bo'yicha qidirish tavsiya etiladi.
- Reputatsiya belgisi yoki avtomatik tasnif mustaqil dalil hisoblanmaydi; natija boshqa manba va nazorat qilinadigan tahlil bilan tekshiriladi.""",
    "virustotal-url": """Tekshiruv doirasida amalga oshiriladigan harakatlar:
- URL, domen yoki IP bo'yicha mavjud antivirus, reputatsiya va threat-intelligence natijalarini qiyoslash.
- Aniqlashlar tarixi, bog'langan resurslar va xavfsizlik yetkazib beruvchilari qaytargan baholarni ko'rib chiqish.
- Tekshiruv uchun ahamiyatli indikatorlarni keyingi mustaqil tahlilga ajratish.

Natijadan foydalanish tartibi:
- So'rov qiymati, natija URL manzili, tekshiruv sanasi va muhim aniqlashlar qayd etiladi.
- Yangi URL yoki faylni public xizmatga yuborish natijani xizmat hamjamiyati va hamkorlari bilan ulashishi mumkin; tergov siri yoki oshkor etilishi cheklangan indikator vakolatsiz yuborilmaydi.
- Bir yoki bir nechta dvigatel aniqlashi yakuniy xulosa emas; natija kontekst va mustaqil manbalar bilan tekshiriladi.""",
    "virustotal-files": """Tekshiruv doirasida amalga oshiriladigan harakatlar:
- APK yoki boshqa faylning hash qiymati bo'yicha mavjud antivirus va threat-intelligence hisobotlarini qidirish.
- Zarur va vakolatli holatda faylni skanerlash, aniqlashlar, fayl turi, imzo, xatti-harakat va bog'liq indikatorlarni ko'rib chiqish.
- Muhim domen, URL, IP, sertifikat yoki hashlarni keyingi tekshiruv uchun ajratish.

Natijadan foydalanish tartibi:
- Asl fayl hashi, manbasi, hisobot URL manzili, tahlil sanasi va ahamiyatli natijalar qayd etiladi.
- Public xizmatga yuborilgan fayl xizmat hamjamiyati va hamkorlari bilan ulashilishi mumkin; maxfiy yoki oshkor etilishi cheklangan material vakolatsiz yuklanmaydi.
- Antivirus aniqlashlari yakuniy ekspert xulosasi hisoblanmaydi va boshqa vosita hamda nazorat qilinadigan muhitdagi tahlil bilan tekshiriladi.""",
    "kropiva-uabot": """Tekshiruv doirasida amalga oshiriladigan harakatlar:
- Telegram orqali taqdim etiladigan tashqi xizmat sahifasini ochish va undagi joriy public qidiruv imkoniyatlarini ko'rib chiqish.
- Xizmat qaytargan natijadan keyingi tekshiruv yo'nalishlarini belgilash uchun foydalanish.
- Ahamiyatli natijaning havolasi, ko'rilgan sana-vaqti va tekshiruv kontekstini qayd etish.

Natijadan foydalanish tartibi:
- Bot operatori, xizmatning joriy funksiyalari va ma'lumot manbalari mustaqil ravishda tasdiqlanmagan; undan faqat tegishli vakolat va qonuniy asos doirasida foydalaniladi.
- Botga tergov siri, parol, autentifikatsiya kodi, access token, xizmat hujjati yoki oshkor etilishi cheklangan boshqa ma'lumot yuborilmaydi.
- Olingan natija mustaqil dalil sifatida qabul qilinmaydi; ahamiyatli holatlar rasmiy va kamida bitta mustaqil manba orqali tekshiriladi.""",
    "tgshield": """Tekshiruv doirasida amalga oshiriladigan harakatlar:
- TGShield tashqi yo'naltirish sahifasini ochish va xizmat taqdim etayotgan joriy public tekshiruv imkoniyatlarini ko'rib chiqish.
- Xizmat qaytargan ochiq natijalardan keyingi tekshiruv yo'nalishini belgilash uchun foydalanish.
- Yakuniy yo'naltirilgan domen, natija havolasi hamda ko'rilgan sana-vaqtni qayd etish.

Natijadan foydalanish tartibi:
- Sahifa tashqi manzilga yo'naltirishi mumkin; ma'lumot kiritishdan oldin yakuniy domen va ulanish xavfsizligi alohida tekshiriladi.
- Xizmat operatori, funksiyalari va ma'lumot manbalari mustaqil ravishda tasdiqlanmagan; parol, autentifikatsiya kodi, access token, tergov siri yoki oshkor etilishi cheklangan ma'lumot kiritilmaydi.
- Olingan natija mustaqil dalil hisoblanmaydi va rasmiy hamda mustaqil manbalar orqali qiyosiy tekshiriladi.""",
    "fun-xeyes-bot": """Tekshiruv doirasida amalga oshiriladigan harakatlar:
- Telegram orqali taqdim etiladigan tashqi bot sahifasini ochish va undagi joriy public qidiruv imkoniyatlarini ko'rib chiqish.
- Xizmat qaytargan natijadan keyingi tekshiruv yo'nalishlarini belgilash uchun foydalanish.
- Ahamiyatli natijaning havolasi, ko'rilgan sana-vaqti va tekshiruv kontekstini qayd etish.

Natijadan foydalanish tartibi:
- Bot operatori, xizmatning joriy funksiyalari va ma'lumot manbalari mustaqil ravishda tasdiqlanmagan; undan faqat tegishli vakolat va qonuniy asos doirasida foydalaniladi.
- Botga tergov siri, parol, autentifikatsiya kodi, access token, xizmat hujjati yoki oshkor etilishi cheklangan boshqa ma'lumot yuborilmaydi.
- Olingan natija mustaqil dalil sifatida qabul qilinmaydi; ahamiyatli holatlar rasmiy va kamida bitta mustaqil manba orqali tekshiriladi.""",
    "instant-username": """Tekshiruv doirasida amalga oshiriladigan harakatlar:
- Username bir nechta public platformada ishlatilayotgan yoki foydalanish uchun mavjud ekanini dastlabki tekshirish.
- Aniqlangan platforma va ehtimoliy profil havolalarini keyingi manzilli tekshiruv uchun qayd etish.
- Bir xil username bo'yicha topilgan profillardagi public identifikatorlarni o'zaro qiyoslash.

Natijadan foydalanish tartibi:
- “Band”, “mavjud” yoki “noma'lum” holati profilning muayyan shaxsga tegishli ekanini tasdiqlamaydi; har bir natija tegishli platformaning o'zida qayta tekshiriladi.
- Xizmat natijasi vaqtinchalik keshga bog'liq yoki platformadagi keyingi o'zgarishlardan ortda qolgan bo'lishi mumkin.
- Shaxs aynanligi kamida bitta qo'shimcha identifikator va mustaqil manba bilan tasdiqlanadi; so'rov, sana-vaqt va natija havolasi qayd etiladi.""",
    "wayback-machine": """Tekshiruv doirasida amalga oshiriladigan harakatlar:
- Domen yoki URL bo'yicha arxivlangan veb-sahifa nusxalarini aniqlash.
- Sahifa mazmuni, aloqa rekvizitlari va tashqi havolalardagi tarixiy o'zgarishlarni qiyoslash.
- Tekshiruv uchun ahamiyatli nusxaning arxiv URL manzili va qayd etilgan sanasini rasmiylashtirish.

Natijadan foydalanish tartibi:
- Arxiv nusxasi mustaqil tasdiq sifatida emas, tekshiruv versiyasini shakllantiruvchi ochiq manba sifatida baholanadi.
- Muhim holatlar boshqa mustaqil manbalar bilan qiyosiy tekshiriladi va ko'rish sanasi qayd etiladi.""",
    "cctld-uz": """Tekshiruv doirasida amalga oshiriladigan harakatlar:
- .UZ domen nomining mavjudligi va public ro'yxatga olish holatini tekshirish.
- Domen nomi, ro'yxatga olish xizmati hamda ochiq e'lon qilingan tegishli rekvizitlarni qayd etish.
- O'zbekiston milliy domen hududiga aloqador keyingi tekshiruv yo'nalishlarini belgilash.

Natijadan foydalanish tartibi:
- Xizmat test rejimida ishlashi mumkinligi inobatga olinadi.
- Faqat public ma'lumotlardan foydalaniladi; domen nomi muayyan shaxsga tegishli ekanligi qo'shimcha dalillarsiz tasdiqlangan deb hisoblanmaydi.""",
    "icann-lookup": """Tekshiruv doirasida amalga oshiriladigan harakatlar:
- Domen yoki internet raqam resursiga oid public ro'yxatga olish ma'lumotlarini RDAP orqali tekshirish.
- Registrar, registry, domen holati, nameserver va DNSSEC haqidagi mavjud yozuvlarni qayd etish.
- Ro'yxatga olish voqealari va vakolatli xizmatga oid havolalarni qiyosiy tekshirish.

Natijadan foydalanish tartibi:
- Maxfiylik sababli yashirilgan maydonlar mavjud bo'lishi mumkin.
- Ro'yxatga olish yozuvi domen foydalanuvchisining shaxsini mustaqil ravishda tasdiqlamaydi; natija boshqa dalillar bilan tekshiriladi.""",
    "rdap": """Tekshiruv doirasida amalga oshiriladigan harakatlar:
- Domen, IP manzil yoki ASN bo'yicha tuzilmaviy RDAP ma'lumotlarini olish.
- Vakolatli registry, holat, hodisa sanalari, nameserver, tarmoq diapazoni va tegishli bildirishnomalarni tekshirish.
- Natijadagi havola va identifikatorlar asosida keyingi tekshiruv yo'nalishlarini belgilash.

Natijadan foydalanish tartibi:
- RDAP.org so'rovni tegishli vakolatli RDAP xizmatiga yo'naltirishi mumkin.
- Aniqlangan texnik resurs muayyan shaxsga tegishli ekanligi qo'shimcha dalillarsiz tasdiqlangan deb baholanmaydi.""",
    "dnsdumpster": """Tekshiruv doirasida amalga oshiriladigan harakatlar:
- Domen bilan bog'liq public DNS yozuvlari va hostlarni aniqlash.
- Subdomenlar, pochta xizmatlari va ehtimoliy tarmoq infratuzilmasi o'rtasidagi aloqalarni xaritalash.
- Aniqlangan IP manzil va hostlarni boshqa mustaqil texnik manbalar orqali qiyosiy tekshirish.

Natijadan foydalanish tartibi:
- Natijalar passiv DNS va ochiq manbalarga asoslanishi sababli ularning dolzarbligi alohida tekshiriladi.
- Tekshiruv sanasi, domen va aniqlangan yozuvlar manba havolasi bilan qayd etiladi.""",
    "urlscan": """Tekshiruv doirasida amalga oshiriladigan harakatlar:
- URL, domen yoki IP bo'yicha avvalgi public skan natijalarini qidirish.
- Sahifa tasviri, tarmoq so'rovlari, HTTP javoblari, domenlar va IP aloqalarini tahlil qilish.
- Sertifikat, yo'naltirish va yuklangan resurslar asosida bog'liq infratuzilmani aniqlash.

Natijadan foydalanish tartibi:
- Maxfiy yoki xizmatga oid URLni public skanga yuborishdan oldin ma'lumotning oshkor bo'lish xavfi baholanadi.
- Natija URL manzili, skan sanasi va ahamiyatli texnik ko'rsatkichlar qayd etiladi.""",
    "google-search": """Tekshiruv doirasida amalga oshiriladigan harakatlar:
- Shaxs nomi, username, telefon raqami, email, IP manzil, domen, URL yoki kalit so'z bo'yicha Google indeksidagi ochiq sahifalarni qidirish.
- Qidiruv operatorlari yordamida natijalarni aniq ibora, muayyan domen yoki fayl turi bo'yicha aniqlashtirish.
- Ahamiyatli natijaning sarlavhasi, URL manzili va ko'rish sanasini qayd etish.

Natijadan foydalanish tartibi:
- Qidiruv natijasi tekshiruv uchun yo'naltiruvchi ma'lumot hisoblanadi va undagi holatlar asl manbada tekshiriladi.
- Ism, username yoki boshqa belgi mosligi qo'shimcha identifikatorlarsiz shaxs aynanligini tasdiqlamaydi.""",
    "yandex-search": """Tekshiruv doirasida amalga oshiriladigan harakatlar:
- Shaxs nomi, username, telefon raqami, email, IP manzil, domen, URL yoki kalit so'z bo'yicha Yandex indeksidagi ochiq sahifalarni qidirish.
- Turli yozilish shakllari va qidiruv operatorlari orqali muqobil manbalarni aniqlash.
- Ahamiyatli natijaning sarlavhasi, URL manzili va ko'rish sanasini qayd etish.

Natijadan foydalanish tartibi:
- Qidiruv natijasi tekshiruv uchun yo'naltiruvchi ma'lumot hisoblanadi va undagi holatlar asl manbada tekshiriladi.
- Ism, username yoki boshqa belgi mosligi qo'shimcha identifikatorlarsiz shaxs aynanligini tasdiqlamaydi.""",
    "bing": """Tekshiruv doirasida amalga oshiriladigan harakatlar:
- Shaxs nomi, username, telefon raqami, email, domen yoki URL bo'yicha indekslangan ochiq sahifalarni qidirish.
- Microsoft Bing qidiruv operatorlari yordamida hujjat, rasm, yangilik va muayyan domen doirasidagi natijalarni aniqlashtirish.
- Ahamiyatli natijaning sarlavhasi, URL manzili va ko'rish sanasini qayd etish.

Natijadan foydalanish tartibi:
- Qidiruv natijasi tekshiruv uchun yo'naltiruvchi ma'lumot hisoblanadi va undagi holatlar asl manbada tekshiriladi.
- Shaxslar o'rtasidagi o'xshashlik yoki ism mosligi qo'shimcha identifikatorlarsiz aynanlikni tasdiqlamaydi.""",
    "2gis": """Tekshiruv doirasida amalga oshiriladigan harakatlar:
- Manzil, tashkilot nomi yoki telefon raqami bo'yicha ochiq tashkilot kartochkalari va xarita ma'lumotlarini qidirish.
- Tashkilot manzili, aloqa rekvizitlari, ish vaqti va ochiq e'lon qilingan filiallarni tekshirish.
- Joylashuvni boshqa rasmiy va mustaqil manbalar bilan qiyosiy tekshirish.

Natijadan foydalanish tartibi:
- Xarita va katalog ma'lumotlarining yangilangan sanasi hamda ehtimoliy foydalanuvchi tahrirlari inobatga olinadi.
- Natija tashkilotning rasmiy manbasi va zarur hollarda joyida tekshiruv bilan tasdiqlanadi.""",
    "fingerprint-to": """Tekshiruv doirasida amalga oshiriladigan harakatlar:
- Username, email manzil yoki telefon raqami bo'yicha public platformalardagi ehtimoliy mosliklarni qidirish.
- Aniqlangan profil havolalari, nom va boshqa ochiq belgilarni o'zaro qiyoslash.
- Mosliklardan keyingi tekshiruv yo'nalishlari sifatida foydalanish.

Natijadan foydalanish tartibi:
- Bir xil username yoki aloqa identifikatori profillarning aynan bir shaxsga tegishli ekanligini o'z-o'zidan tasdiqlamaydi.
- Har bir moslik kamida bitta qo'shimcha identifikator va mustaqil manba orqali tekshiriladi; xizmat shartlari hamda shaxsga doir ma'lumotlarni himoya qilish talablari saqlanadi.""",
    "idcrawl": """Tekshiruv doirasida amalga oshiriladigan harakatlar:
- Shaxs nomi, username, email manzil yoki telefon raqami bo'yicha public profil va yozuvlarni qidirish.
- Ehtimoliy bog'liq ijtimoiy tarmoq profillari va aloqa ma'lumotlarini qiyoslash.
- Aniqlangan havolalarni keyingi manzilli tekshiruv uchun qayd etish.

Natijadan foydalanish tartibi:
- Natijalar shaxsning aynanligini yoki ma'lumotning dolzarbligini mustaqil ravishda tasdiqlamaydi.
- Xizmat natijalaridan kredit, ishga qabul qilish, sug'urta, uy-joy yoki qonun bilan alohida tartibga solingan qarorlar uchun foydalanilmaydi; ahamiyatli ma'lumotlar mustaqil manbalar orqali tekshiriladi.""",
}


def apply_catalog_migrations(db: sqlite3.Connection) -> None:
    """Apply one-time content changes without overwriting later admin edits."""
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS catalog_migrations (
            migration_id TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    koodous_fix_id = "20260908_koodous_stable_url"
    if not db.execute(
        "SELECT 1 FROM catalog_migrations WHERE migration_id = ?", (koodous_fix_id,)
    ).fetchone():
        db.execute("UPDATE tools SET query_url_template='', updated_at=CURRENT_TIMESTAMP WHERE slug='koodous'")
        db.execute("INSERT INTO catalog_migrations (migration_id) VALUES (?)", (koodous_fix_id,))
    migration_id = "20260908_mobile_threats"
    if db.execute(
        "SELECT 1 FROM catalog_migrations WHERE migration_id = ?", (migration_id,)
    ).fetchone():
        return

    category = next(item for item in CATEGORY_SEED if item["slug"] == "mobile-threats")
    existing_category = db.execute(
        "SELECT id FROM categories WHERE slug = ?", (category["slug"],)
    ).fetchone()
    if existing_category:
        category_id = existing_category["id"]
    else:
        cursor = db.execute(
            """
            INSERT INTO categories (name, slug, description, details, icon, tags, featured, sort_order, enabled)
            VALUES (?, ?, ?, ?, ?, ?, 0, ?, 1)
            """,
            (
                category["name"], category["slug"], category["description"], category["details"],
                category["icon"], json.dumps(category["tags"], ensure_ascii=False), category["sort_order"],
            ),
        )
        category_id = cursor.lastrowid

    migrated_slugs = {"mobsf-live", "koodous", "virustotal-url", "urlscan", "virustotal-files"}
    for tool in TOOL_SEED:
        if tool[1] not in migrated_slugs:
            continue
        (
            name, slug, _category_slug, description, url, query_template, icon, input_types,
            networks, tags, access, login_required, featured, sort_order,
        ) = tool
        values = (
            name, category_id, FORMAL_TOOL_DESCRIPTIONS.get(slug, description),
            REQUESTED_TOOL_DETAILS.get(slug, ""), url, query_template, icon,
            json.dumps(input_types, ensure_ascii=False), json.dumps(networks, ensure_ascii=False),
            json.dumps(tags, ensure_ascii=False), access, int(login_required), int(featured), sort_order,
        )
        existing_tool = db.execute("SELECT id FROM tools WHERE slug = ?", (slug,)).fetchone()
        if existing_tool:
            db.execute(
                """
                UPDATE tools SET name=?, category_id=?, description=?, details=?, url=?, query_url_template=?,
                    icon=?, input_types=?, networks=?, tags=?, access=?, login_required=?, featured=?, sort_order=?,
                    enabled=1, updated_at=CURRENT_TIMESTAMP
                WHERE id=?
                """,
                values + (existing_tool["id"],),
            )
        else:
            db.execute(
                """
                INSERT INTO tools (
                    name, category_id, description, details, url, query_url_template, icon,
                    input_types, networks, tags, access, login_required, featured, sort_order, enabled, slug
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                """,
                values + (slug,),
            )
    db.execute("INSERT INTO catalog_migrations (migration_id) VALUES (?)", (migration_id,))


def database() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_database() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with database() as db:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                slug TEXT NOT NULL UNIQUE,
                description TEXT NOT NULL DEFAULT '',
                details TEXT NOT NULL DEFAULT '',
                icon TEXT NOT NULL DEFAULT '◈',
                tags TEXT NOT NULL DEFAULT '[]',
                featured INTEGER NOT NULL DEFAULT 0,
                sort_order INTEGER NOT NULL DEFAULT 0,
                enabled INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS tools (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                slug TEXT NOT NULL UNIQUE,
                category_id INTEGER NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                details TEXT NOT NULL DEFAULT '',
                url TEXT NOT NULL,
                query_url_template TEXT NOT NULL DEFAULT '',
                icon TEXT NOT NULL DEFAULT '◈',
                input_types TEXT NOT NULL DEFAULT '[]',
                networks TEXT NOT NULL DEFAULT '[]',
                tags TEXT NOT NULL DEFAULT '[]',
                access TEXT NOT NULL DEFAULT 'free',
                login_required INTEGER NOT NULL DEFAULT 0,
                featured INTEGER NOT NULL DEFAULT 0,
                sort_order INTEGER NOT NULL DEFAULT 0,
                enabled INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
            )
            """
        )
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS bot_users (
                telegram_user_id INTEGER PRIMARY KEY,
                chat_id INTEGER NOT NULL,
                username TEXT NOT NULL DEFAULT '',
                first_name TEXT NOT NULL DEFAULT '',
                last_name TEXT NOT NULL DEFAULT '',
                approved INTEGER NOT NULL DEFAULT 1,
                blocked INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                last_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS bot_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_code TEXT UNIQUE,
                telegram_user_id INTEGER NOT NULL,
                category_id INTEGER,
                status TEXT NOT NULL DEFAULT 'draft',
                summary TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                submitted_at TEXT,
                closed_at TEXT,
                FOREIGN KEY (telegram_user_id) REFERENCES bot_users(telegram_user_id) ON DELETE RESTRICT,
                FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
            )
            """
        )
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS bot_evidence (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id INTEGER NOT NULL,
                kind TEXT NOT NULL,
                value TEXT NOT NULL DEFAULT '',
                caption TEXT NOT NULL DEFAULT '',
                telegram_message_id INTEGER,
                telegram_file_id TEXT NOT NULL DEFAULT '',
                telegram_file_unique_id TEXT NOT NULL DEFAULT '',
                file_name TEXT NOT NULL DEFAULT '',
                mime_type TEXT NOT NULL DEFAULT '',
                file_size INTEGER NOT NULL DEFAULT 0,
                sha256 TEXT NOT NULL DEFAULT '',
                sort_order INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (request_id) REFERENCES bot_requests(id) ON DELETE CASCADE
            )
            """
        )
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS bot_replies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id INTEGER NOT NULL,
                kind TEXT NOT NULL DEFAULT 'text',
                body TEXT NOT NULL DEFAULT '',
                file_name TEXT NOT NULL DEFAULT '',
                mime_type TEXT NOT NULL DEFAULT '',
                local_path TEXT NOT NULL DEFAULT '',
                telegram_message_id INTEGER,
                delivery_status TEXT NOT NULL DEFAULT 'pending',
                error TEXT NOT NULL DEFAULT '',
                sort_order INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                sent_at TEXT,
                FOREIGN KEY (request_id) REFERENCES bot_requests(id) ON DELETE CASCADE
            )
            """
        )
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS bot_sessions (
                telegram_user_id INTEGER PRIMARY KEY,
                draft_request_id INTEGER,
                state TEXT NOT NULL DEFAULT 'idle',
                selected_category_slug TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (telegram_user_id) REFERENCES bot_users(telegram_user_id) ON DELETE CASCADE,
                FOREIGN KEY (draft_request_id) REFERENCES bot_requests(id) ON DELETE SET NULL
            )
            """
        )
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS bot_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_user_id INTEGER,
                request_id INTEGER,
                event_type TEXT NOT NULL,
                payload TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (telegram_user_id) REFERENCES bot_users(telegram_user_id) ON DELETE SET NULL,
                FOREIGN KEY (request_id) REFERENCES bot_requests(id) ON DELETE SET NULL
            )
            """
        )
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS bot_updates (
                update_id INTEGER PRIMARY KEY,
                received_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        category_columns = {row["name"] for row in db.execute("PRAGMA table_info(categories)")}
        tool_columns = {row["name"] for row in db.execute("PRAGMA table_info(tools)")}
        if "details" not in category_columns:
            db.execute("ALTER TABLE categories ADD COLUMN details TEXT NOT NULL DEFAULT ''")
        if "featured" not in category_columns:
            db.execute("ALTER TABLE categories ADD COLUMN featured INTEGER NOT NULL DEFAULT 0")
        if "details" not in tool_columns:
            db.execute("ALTER TABLE tools ADD COLUMN details TEXT NOT NULL DEFAULT ''")
        db.execute("CREATE INDEX IF NOT EXISTS idx_tools_category ON tools(category_id, enabled, sort_order)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_categories_enabled ON categories(enabled, sort_order)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_categories_display ON categories(enabled, featured, sort_order)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_bot_requests_status ON bot_requests(status, updated_at)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_bot_requests_user ON bot_requests(telegram_user_id, updated_at)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_bot_evidence_request ON bot_evidence(request_id, sort_order)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_bot_replies_request ON bot_replies(request_id, sort_order)")

        if SEED_DEMO and db.execute("SELECT COUNT(*) FROM categories").fetchone()[0] == 0:
            for category in CATEGORY_SEED:
                db.execute(
                    "INSERT INTO categories (name, slug, description, details, icon, tags, featured, sort_order) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        category["name"],
                        category["slug"],
                        category["description"],
                        category.get("details", ""),
                        category["icon"],
                        json.dumps(category["tags"], ensure_ascii=False),
                        int(category["slug"] in {"telegram", "search", "network"}),
                        category["sort_order"],
                    ),
                )

        if SEED_DEMO and db.execute("SELECT COUNT(*) FROM tools").fetchone()[0] == 0:
            category_ids = {row["slug"]: row["id"] for row in db.execute("SELECT id, slug FROM categories")}
            for tool in TOOL_SEED:
                (
                    name,
                    slug,
                    category_slug,
                    description,
                    url,
                    query_template,
                    icon,
                    input_types,
                    networks,
                    tags,
                    access,
                    login_required,
                    featured,
                    sort_order,
                ) = tool
                description = FORMAL_TOOL_DESCRIPTIONS.get(slug, description)
                details = REQUESTED_TOOL_DETAILS.get(slug, "")
                db.execute(
                    """
                    INSERT INTO tools (
                        name, slug, category_id, description, details, url, query_url_template, icon,
                        input_types, networks, tags, access, login_required, featured, sort_order
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        name,
                        slug,
                        category_ids[category_slug],
                        description,
                        details,
                        url,
                        query_template,
                        icon,
                        json.dumps(input_types, ensure_ascii=False),
                        json.dumps(networks, ensure_ascii=False),
                        json.dumps(tags, ensure_ascii=False),
                        access,
                        int(login_required),
                        int(featured),
                        sort_order,
                    ),
                )
        if db.execute("SELECT COUNT(*) FROM categories").fetchone()[0] > 0:
            apply_catalog_migrations(db)
        db.execute("PRAGMA optimize")
    sync_catalog_backup()


def decode_json_list(value: str | None) -> list[str]:
    try:
        data = json.loads(value or "[]")
        return [str(item) for item in data] if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def row_to_category(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "slug": row["slug"],
        "description": row["description"],
        "details": row["details"],
        "icon": row["icon"],
        "tags": decode_json_list(row["tags"]),
        "featured": bool(row["featured"]),
        "sort_order": row["sort_order"],
        "enabled": bool(row["enabled"]),
        "tool_count": row["tool_count"] if "tool_count" in row.keys() else 0,
    }


def row_to_tool(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "slug": row["slug"],
        "category_id": row["category_id"],
        "category_slug": row["category_slug"] if "category_slug" in row.keys() else "",
        "category_name": row["category_name"] if "category_name" in row.keys() else "",
        "description": row["description"],
        "details": row["details"],
        "url": row["url"],
        "query_url_template": row["query_url_template"],
        "icon": row["icon"],
        "input_types": decode_json_list(row["input_types"]),
        "networks": decode_json_list(row["networks"]),
        "tags": decode_json_list(row["tags"]),
        "access": row["access"],
        "login_required": bool(row["login_required"]),
        "featured": bool(row["featured"]),
        "sort_order": row["sort_order"],
        "enabled": bool(row["enabled"]),
    }


def telegram_call(
    method: str,
    payload: dict[str, object] | None = None,
    file_field: str = "",
    file_name: str = "",
    file_bytes: bytes | None = None,
    mime_type: str = "application/octet-stream",
) -> dict:
    if not TELEGRAM_BOT_TOKEN:
        return {"ok": False, "description": "TELEGRAM_BOT_TOKEN sozlanmagan."}
    url = f"{TELEGRAM_API_BASE}/bot{TELEGRAM_BOT_TOKEN}/{method}"
    payload = payload or {}
    headers: dict[str, str] = {"User-Agent": "OSINTNavigatorBot/1.0"}
    if file_field and file_bytes is not None:
        boundary = f"----OSINTNavigator{uuid.uuid4().hex}"
        chunks: list[bytes] = []
        for key, value in payload.items():
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            chunks.extend([
                f"--{boundary}\r\n".encode(),
                f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode(),
                str(value).encode("utf-8"), b"\r\n",
            ])
        safe_name = Path(file_name or "file.bin").name.replace('"', "")
        chunks.extend([
            f"--{boundary}\r\n".encode(),
            f'Content-Disposition: form-data; name="{file_field}"; filename="{safe_name}"\r\n'.encode(),
            f"Content-Type: {mime_type}\r\n\r\n".encode(),
            file_bytes, b"\r\n", f"--{boundary}--\r\n".encode(),
        ])
        body = b"".join(chunks)
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    else:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json; charset=utf-8"
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result if isinstance(result, dict) else {"ok": False, "description": "Noto'g'ri Telegram javobi."}
    except urllib.error.HTTPError as error:
        try:
            payload_error = json.loads(error.read().decode("utf-8"))
            if isinstance(payload_error, dict):
                return payload_error
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass
        return {"ok": False, "description": f"Telegram HTTP xatosi: {error.code}"}
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        return {"ok": False, "description": f"Telegram bilan aloqa xatosi: {error}"}


def telegram_send_text(chat_id: int | str, text: str, reply_markup: dict | None = None) -> dict:
    payload: dict[str, object] = {
        "chat_id": chat_id,
        "text": text[:4096],
        "disable_web_page_preview": True,
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return telegram_call("sendMessage", payload)


def bot_categories_keyboard() -> dict:
    with database() as db:
        rows = db.execute(
            "SELECT name, slug FROM categories WHERE enabled = 1 ORDER BY featured DESC, sort_order, name"
        ).fetchall()
    keyboard = [[{"text": row["name"][:60], "callback_data": f"cat:{row['slug']}"}] for row in rows]
    keyboard.extend([
        [{"text": "Boshqa turdagi dalil", "callback_data": "cat:other"}],
        [{"text": "Murojaatlarim", "callback_data": "requests:list"}],
    ])
    return {"inline_keyboard": keyboard}


def bot_control_keyboard() -> dict:
    return {
        "inline_keyboard": [
            [
                {"text": "Mutaxassisga yuborish", "callback_data": "request:submit"},
                {"text": "Bekor qilish", "callback_data": "request:cancel"},
            ],
            [{"text": "Dalil turini o'zgartirish", "callback_data": "menu:categories"}],
        ]
    }


def upsert_bot_user(user: dict, chat_id: int) -> sqlite3.Row:
    telegram_user_id = int(user.get("id", 0))
    approved_default = 0 if TELEGRAM_REQUIRE_APPROVAL else 1
    with database() as db:
        db.execute(
            """
            INSERT INTO bot_users (telegram_user_id, chat_id, username, first_name, last_name, approved)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(telegram_user_id) DO UPDATE SET
                chat_id=excluded.chat_id, username=excluded.username, first_name=excluded.first_name,
                last_name=excluded.last_name, updated_at=CURRENT_TIMESTAMP, last_seen_at=CURRENT_TIMESTAMP
            """,
            (
                telegram_user_id, chat_id, str(user.get("username", ""))[:100],
                str(user.get("first_name", ""))[:200], str(user.get("last_name", ""))[:200],
                approved_default,
            ),
        )
        return db.execute("SELECT * FROM bot_users WHERE telegram_user_id = ?", (telegram_user_id,)).fetchone()


def get_or_create_draft(telegram_user_id: int, category_slug: str = "") -> int:
    with BOT_LOCK, database() as db:
        session = db.execute(
            "SELECT draft_request_id FROM bot_sessions WHERE telegram_user_id = ?", (telegram_user_id,)
        ).fetchone()
        if session and session["draft_request_id"]:
            request = db.execute(
                "SELECT id FROM bot_requests WHERE id = ? AND status = 'draft'", (session["draft_request_id"],)
            ).fetchone()
            if request:
                category = db.execute("SELECT id FROM categories WHERE slug = ?", (category_slug,)).fetchone() if category_slug else None
                db.execute(
                    "UPDATE bot_requests SET category_id=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                    (category["id"] if category else None, request["id"]),
                )
                db.execute(
                    "UPDATE bot_sessions SET selected_category_slug=?, state='collecting', updated_at=CURRENT_TIMESTAMP WHERE telegram_user_id=?",
                    (category_slug, telegram_user_id),
                )
                return int(request["id"])

        category = db.execute("SELECT id FROM categories WHERE slug = ?", (category_slug,)).fetchone() if category_slug else None
        cursor = db.execute(
            "INSERT INTO bot_requests (telegram_user_id, category_id, status) VALUES (?, ?, 'draft')",
            (telegram_user_id, category["id"] if category else None),
        )
        request_id = int(cursor.lastrowid)
        request_code = f"RKITI-{datetime.now(timezone.utc).year}-{request_id:06d}"
        db.execute("UPDATE bot_requests SET request_code=? WHERE id=?", (request_code, request_id))
        db.execute(
            """
            INSERT INTO bot_sessions (telegram_user_id, draft_request_id, state, selected_category_slug)
            VALUES (?, ?, 'collecting', ?)
            ON CONFLICT(telegram_user_id) DO UPDATE SET
                draft_request_id=excluded.draft_request_id, state='collecting',
                selected_category_slug=excluded.selected_category_slug, updated_at=CURRENT_TIMESTAMP
            """,
            (telegram_user_id, request_id, category_slug),
        )
        db.execute(
            "INSERT INTO bot_events (telegram_user_id, request_id, event_type) VALUES (?, ?, 'draft_created')",
            (telegram_user_id, request_id),
        )
        return request_id


def classify_indicator(value: str, selected_slug: str = "") -> tuple[str, list[str]]:
    text = value.strip()
    if re.fullmatch(r"0x[a-fA-F0-9]{64}", text):
        return "tx-hash", ["crypto", "search"]
    if re.fullmatch(r"0x[a-fA-F0-9]{40}", text) or re.fullmatch(r"(?:bc1|[13])[a-zA-HJ-NP-Z0-9]{25,62}", text) or re.fullmatch(r"T[a-zA-Z0-9]{33}", text):
        return "wallet", ["crypto", "search"]
    if re.fullmatch(r"[a-fA-F0-9]{64}", text):
        return "file-hash", ["crypto", "mobile-threats", "media", "search"]
    if re.fullmatch(r"(?:https?://)?(?:www\.)?t\.me/[a-zA-Z0-9_]+", text, re.I) or re.fullmatch(r"@[a-zA-Z][a-zA-Z0-9_]{3,}", text):
        return "telegram-username", ["telegram", "username", "search"]
    if re.fullmatch(r"(?:\d{1,3}\.){3}\d{1,3}", text) or (":" in text and re.fullmatch(r"[a-fA-F0-9:]{4,}", text)):
        return "ip", ["network", "search"]
    if re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", text):
        return "email", ["username", "search"]
    if re.fullmatch(r"https?://\S+", text, re.I):
        return "url", ["mobile-threats", "network", "search"]
    if re.fullmatch(r"[^\s]+\.(?:apk|aab)", text, re.I):
        return "apk", ["mobile-threats", "media"]
    if re.fullmatch(r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}", text, re.I):
        return "domain", ["network", "mobile-threats", "search"]
    if re.fullmatch(r"[a-fA-F0-9]{32}|[a-fA-F0-9]{40}", text):
        return "file-hash", ["mobile-threats", "media", "search"]
    if selected_slug == "telegram" and re.fullmatch(r"\d{5,20}", text):
        return "telegram-id", ["telegram", "search"]
    if re.fullmatch(r"\+?[\d\s().-]{8,}", text):
        return "phone", ["search", "username"]
    if re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_.-]{2,31}", text):
        return "username", ["username", "telegram", "search"]
    return "text", [selected_slug] if selected_slug else ["search"]


def recommended_bot_tools(kind: str, categories: list[str]) -> list[sqlite3.Row]:
    with database() as db:
        rows = db.execute(
            """
            SELECT t.name, t.url, t.input_types, c.slug AS category_slug
            FROM tools t JOIN categories c ON c.id=t.category_id
            WHERE t.enabled=1 AND c.enabled=1
            ORDER BY t.featured DESC, t.sort_order, t.name
            """
        ).fetchall()
    ranked = []
    for row in rows:
        inputs = decode_json_list(row["input_types"])
        score = (80 if kind in inputs else 0) + (40 - categories.index(row["category_slug"]) * 5 if row["category_slug"] in categories else 0)
        if score > 0:
            ranked.append((score, row))
    ranked.sort(key=lambda item: -item[0])
    return [row for _, row in ranked[:3]]


def add_bot_evidence(request_id: int, message: dict, selected_slug: str) -> tuple[int, str, list[str]]:
    caption = str(message.get("caption", ""))[:4000]
    items: list[dict[str, object]] = []
    text = str(message.get("text", "")).strip()
    if text:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        for line in (lines if len(lines) > 1 else [text]):
            kind, categories = classify_indicator(line, selected_slug)
            items.append({"kind": kind, "value": line[:8000], "categories": categories})
    elif message.get("photo"):
        media = message["photo"][-1]
        items.append({"kind": "image", "media": media, "categories": ["media"]})
    elif message.get("video"):
        media = message["video"]
        items.append({"kind": "video", "media": media, "categories": ["media"]})
    elif message.get("document"):
        media = message["document"]
        file_name = str(media.get("file_name", ""))
        mime = str(media.get("mime_type", ""))
        is_apk = file_name.lower().endswith((".apk", ".aab")) or mime == "application/vnd.android.package-archive"
        items.append({"kind": "apk" if is_apk else "document", "media": media, "categories": ["mobile-threats", "media"] if is_apk else ["media"]})
    elif message.get("audio"):
        items.append({"kind": "audio", "media": message["audio"], "categories": ["media"]})
    elif message.get("voice"):
        items.append({"kind": "voice", "media": message["voice"], "categories": ["media"]})
    else:
        return 0, "", []

    for item in items:
        media = item.get("media") if isinstance(item.get("media"), dict) else {}
        if int(media.get("file_size", 0) or 0) > 20 * 1024 * 1024:
            return -1, "too-large", []

    first_kind = str(items[0]["kind"])
    first_categories = list(items[0]["categories"])
    with BOT_LOCK, database() as db:
        current_count = db.execute("SELECT COUNT(*) FROM bot_evidence WHERE request_id=?", (request_id,)).fetchone()[0]
        available = max(0, TELEGRAM_MAX_EVIDENCE - current_count)
        if not available:
            return -2, "limit", []
        for offset, item in enumerate(items[:available], start=1):
            media = item.get("media") if isinstance(item.get("media"), dict) else {}
            db.execute(
                """
                INSERT INTO bot_evidence (
                    request_id, kind, value, caption, telegram_message_id, telegram_file_id,
                    telegram_file_unique_id, file_name, mime_type, file_size, sort_order
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    request_id, str(item["kind"]), str(item.get("value", "")), caption,
                    message.get("message_id"), str(media.get("file_id", "")),
                    str(media.get("file_unique_id", "")), str(media.get("file_name", ""))[:255],
                    str(media.get("mime_type", ""))[:200], int(media.get("file_size", 0) or 0),
                    current_count + offset,
                ),
            )
        added = min(len(items), available)
        db.execute("UPDATE bot_requests SET updated_at=CURRENT_TIMESTAMP WHERE id=?", (request_id,))
        db.execute(
            "INSERT INTO bot_events (request_id, event_type, payload) VALUES (?, 'evidence_added', ?)",
            (request_id, json.dumps({"count": added, "kind": first_kind}, ensure_ascii=False)),
        )
    return added, first_kind, first_categories


def bot_draft_summary(request_id: int) -> tuple[str, int]:
    with database() as db:
        row = db.execute(
            """
            SELECT r.request_code, c.name AS category_name, COUNT(e.id) AS evidence_count
            FROM bot_requests r LEFT JOIN categories c ON c.id=r.category_id
            LEFT JOIN bot_evidence e ON e.request_id=r.id WHERE r.id=? GROUP BY r.id
            """,
            (request_id,),
        ).fetchone()
    if not row:
        return "", 0
    return f"{row['request_code']} · {row['category_name'] or 'Boshqa turdagi dalil'}", int(row["evidence_count"])


def submit_bot_request(telegram_user_id: int) -> tuple[bool, str, int | None]:
    with BOT_LOCK, database() as db:
        session = db.execute("SELECT draft_request_id FROM bot_sessions WHERE telegram_user_id=?", (telegram_user_id,)).fetchone()
        request_id = int(session["draft_request_id"]) if session and session["draft_request_id"] else 0
        if not request_id:
            return False, "Yuboriladigan faol murojaat topilmadi.", None
        evidence_count = db.execute("SELECT COUNT(*) FROM bot_evidence WHERE request_id=?", (request_id,)).fetchone()[0]
        if not evidence_count:
            return False, "Avval kamida bitta dalil yoki indikator yuboring.", request_id
        row = db.execute("SELECT request_code FROM bot_requests WHERE id=? AND status='draft'", (request_id,)).fetchone()
        if not row:
            return False, "Mazkur murojaat avval yuborilgan yoki bekor qilingan.", request_id
        db.execute(
            "UPDATE bot_requests SET status='new', submitted_at=CURRENT_TIMESTAMP, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (request_id,),
        )
        db.execute(
            "UPDATE bot_sessions SET draft_request_id=NULL, state='idle', selected_category_slug='', updated_at=CURRENT_TIMESTAMP WHERE telegram_user_id=?",
            (telegram_user_id,),
        )
        db.execute(
            "INSERT INTO bot_events (telegram_user_id, request_id, event_type) VALUES (?, ?, 'submitted')",
            (telegram_user_id, request_id),
        )
        return True, str(row["request_code"]), request_id


def cancel_bot_draft(telegram_user_id: int) -> bool:
    with BOT_LOCK, database() as db:
        session = db.execute("SELECT draft_request_id FROM bot_sessions WHERE telegram_user_id=?", (telegram_user_id,)).fetchone()
        request_id = int(session["draft_request_id"]) if session and session["draft_request_id"] else 0
        if request_id:
            db.execute("DELETE FROM bot_requests WHERE id=? AND status='draft'", (request_id,))
        db.execute(
            """
            INSERT INTO bot_sessions (telegram_user_id, state) VALUES (?, 'idle')
            ON CONFLICT(telegram_user_id) DO UPDATE SET draft_request_id=NULL, state='idle',
                selected_category_slug='', updated_at=CURRENT_TIMESTAMP
            """,
            (telegram_user_id,),
        )
        return bool(request_id)


def bot_request_list(telegram_user_id: int) -> str:
    labels = {"draft": "Tayyorlanmoqda", "new": "Yangi", "in_progress": "Ko'rib chiqilmoqda", "answered": "Javob berilgan", "closed": "Yopilgan"}
    with database() as db:
        rows = db.execute(
            """
            SELECT r.request_code, r.status, r.created_at, COUNT(e.id) AS evidence_count
            FROM bot_requests r LEFT JOIN bot_evidence e ON e.request_id=r.id
            WHERE r.telegram_user_id=? AND r.status!='draft'
            GROUP BY r.id ORDER BY r.id DESC LIMIT 10
            """,
            (telegram_user_id,),
        ).fetchall()
    if not rows:
        return "Hozircha yuborilgan murojaatlar mavjud emas."
    lines = ["So'nggi murojaatlaringiz:"]
    for row in rows:
        lines.append(f"• {row['request_code']} — {labels.get(row['status'], row['status'])} — {row['evidence_count']} ta dalil")
    return "\n".join(lines)


def notify_admin_about_request(request_id: int) -> None:
    if not TELEGRAM_ADMIN_CHAT_ID:
        return
    with database() as db:
        row = db.execute(
            """
            SELECT r.request_code, c.name AS category_name, u.first_name, u.last_name, u.username,
                   COUNT(e.id) AS evidence_count
            FROM bot_requests r JOIN bot_users u ON u.telegram_user_id=r.telegram_user_id
            LEFT JOIN categories c ON c.id=r.category_id LEFT JOIN bot_evidence e ON e.request_id=r.id
            WHERE r.id=? GROUP BY r.id
            """,
            (request_id,),
        ).fetchone()
    if row:
        identity = " ".join(part for part in [row["first_name"], row["last_name"]] if part).strip()
        if row["username"]:
            identity += f" (@{row['username']})"
        telegram_send_text(
            TELEGRAM_ADMIN_CHAT_ID,
            f"Yangi murojaat: {row['request_code']}\nYo'nalish: {row['category_name'] or 'Boshqa'}\nDalillar: {row['evidence_count']} ta\nFoydalanuvchi: {identity or 'Noma\'lum'}",
        )


def process_telegram_update(update: dict) -> None:
    update_id = int(update.get("update_id", 0) or 0)
    if update_id:
        with BOT_LOCK, database() as db:
            cursor = db.execute("INSERT OR IGNORE INTO bot_updates (update_id) VALUES (?)", (update_id,))
            if not cursor.rowcount:
                return
    callback = update.get("callback_query") if isinstance(update.get("callback_query"), dict) else None
    message = callback.get("message") if callback else update.get("message")
    user = callback.get("from") if callback else (message or {}).get("from")
    if not isinstance(message, dict) or not isinstance(user, dict):
        return
    chat = message.get("chat") if isinstance(message.get("chat"), dict) else {}
    chat_id = int(chat.get("id", 0) or 0)
    telegram_user_id = int(user.get("id", 0) or 0)
    if not chat_id or not telegram_user_id:
        return
    if chat.get("type") != "private":
        telegram_send_text(chat_id, "Xizmatdan faqat bot bilan shaxsiy muloqot oynasida foydalaning.")
        return
    bot_user = upsert_bot_user(user, chat_id)
    if bot_user["blocked"]:
        return
    if TELEGRAM_REQUIRE_APPROVAL and not bot_user["approved"]:
        telegram_send_text(chat_id, "Akkauntingiz administrator tasdig'ini kutmoqda. Tasdiqlangach, botdan foydalanishingiz mumkin.")
        return

    callback_data = str(callback.get("data", "")) if callback else ""
    if callback:
        telegram_call("answerCallbackQuery", {"callback_query_id": callback.get("id")})
    text = str(message.get("text", "")).strip()
    command = text.split()[0].split("@")[0].lower() if text.startswith("/") else ""

    if command in {"/start", "/yangi"} or callback_data == "menu:categories":
        telegram_send_text(
            chat_id,
            "Dalil yoki tekshiruv yo'nalishini tanlang. Keyingi bosqichda bir murojaat doirasida bir nechta ID, IP, URL, rasm, video, APK va boshqa fayllarni ketma-ket yuborishingiz mumkin.",
            bot_categories_keyboard(),
        )
        return
    if command in {"/murojaatlarim", "/requests"} or callback_data == "requests:list":
        telegram_send_text(chat_id, bot_request_list(telegram_user_id), {"inline_keyboard": [[{"text": "Yangi murojaat", "callback_data": "menu:categories"}]]})
        return
    if command == "/yordam":
        telegram_send_text(chat_id, "1. Yo'nalishni tanlang.\n2. Barcha dalillarni birma-bir yuboring.\n3. Tayyor bo'lgach «Mutaxassisga yuborish» tugmasini bosing.\n\nTelefon raqamingiz talab qilinmaydi; javob shu Telegram chatiga yuboriladi.")
        return
    if command == "/bekor" or callback_data == "request:cancel":
        removed = cancel_bot_draft(telegram_user_id)
        telegram_send_text(chat_id, "Tayyorlanayotgan murojaat bekor qilindi." if removed else "Bekor qilinadigan faol murojaat mavjud emas.", bot_categories_keyboard())
        return
    if command == "/yuborish" or callback_data == "request:submit":
        ok, result, request_id = submit_bot_request(telegram_user_id)
        if ok:
            telegram_send_text(chat_id, f"Murojaat qabul qilindi. Ro'yxatga olish raqami: {result}. Mutaxassis javobi aynan shu chatga yuboriladi.", {"inline_keyboard": [[{"text": "Murojaatlarim", "callback_data": "requests:list"}, {"text": "Yangi murojaat", "callback_data": "menu:categories"}]]})
            if request_id:
                notify_admin_about_request(request_id)
        else:
            telegram_send_text(chat_id, result, bot_control_keyboard())
        return
    if callback_data.startswith("cat:"):
        category_slug = callback_data.split(":", 1)[1]
        if category_slug == "other":
            category_slug = ""
            category_name = "Boshqa turdagi dalil"
        else:
            with database() as db:
                category = db.execute("SELECT name FROM categories WHERE slug=? AND enabled=1", (category_slug,)).fetchone()
            if not category:
                telegram_send_text(chat_id, "Tanlangan yo'nalish mavjud emas. Qayta tanlang.", bot_categories_keyboard())
                return
            category_name = str(category["name"])
        request_id = get_or_create_draft(telegram_user_id, category_slug)
        summary, count = bot_draft_summary(request_id)
        telegram_send_text(chat_id, f"Yo'nalish: {category_name}.\nDalillarni bittadan yoki ketma-ket yuboring. Matnda bir nechta indikator bo'lsa, ularni alohida qatorlarda yozing.\n\n{summary} · hozir {count} ta dalil.", bot_control_keyboard())
        return

    if command:
        telegram_send_text(chat_id, "Buyruq aniqlanmadi. /start orqali yangi murojaatni boshlang yoki /yordam buyrug'idan foydalaning.")
        return
    with database() as db:
        session = db.execute("SELECT selected_category_slug FROM bot_sessions WHERE telegram_user_id=?", (telegram_user_id,)).fetchone()
    selected_slug = str(session["selected_category_slug"]) if session else ""
    request_id = get_or_create_draft(telegram_user_id, selected_slug)
    added, kind, categories = add_bot_evidence(request_id, message, selected_slug)
    if added < 0:
        message_text = "Murojaatdagi dalillar soni belgilangan chegaraga yetdi. Murojaatni mutaxassisga yuboring yoki ortiqcha dalillarni alohida yangi murojaatda taqdim eting." if kind == "limit" else "Fayl hajmi Telegram Bot API yuklab olish chegarasidan (20 MB) oshadi. Faylni 20 MB dan kichik qismlarga ajrating yoki vakolatli yopiq saqlash manziliga havola yuboring."
        telegram_send_text(chat_id, message_text, bot_control_keyboard())
        return
    if not added:
        telegram_send_text(chat_id, "Mazkur xabar turi qabul qilinmadi. Matn, rasm, video, audio yoki fayl yuboring.", bot_control_keyboard())
        return
    summary, count = bot_draft_summary(request_id)
    tools = recommended_bot_tools(kind, categories)
    tool_text = ""
    if tools:
        tool_text = "\n\nDastlabki tekshiruv uchun mos vositalar:\n" + "\n".join(f"• {row['name']}: {row['url']}" for row in tools)
    telegram_send_text(chat_id, f"{added} ta dalil qabul qilindi. Jami: {count}/{TELEGRAM_MAX_EVIDENCE}.\n{summary}{tool_text}\n\nBoshqa dalillarni yuborishni davom ettirishingiz mumkin.", bot_control_keyboard())


def row_to_bot_request(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "request_code": row["request_code"],
        "telegram_user_id": row["telegram_user_id"],
        "category_name": row["category_name"] if "category_name" in row.keys() else "",
        "category_slug": row["category_slug"] if "category_slug" in row.keys() else "",
        "status": row["status"],
        "summary": row["summary"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "submitted_at": row["submitted_at"],
        "closed_at": row["closed_at"],
        "username": row["username"] if "username" in row.keys() else "",
        "first_name": row["first_name"] if "first_name" in row.keys() else "",
        "last_name": row["last_name"] if "last_name" in row.keys() else "",
        "evidence_count": row["evidence_count"] if "evidence_count" in row.keys() else 0,
        "reply_count": row["reply_count"] if "reply_count" in row.keys() else 0,
    }


def bot_request_detail(request_id: int) -> dict | None:
    with database() as db:
        request = db.execute(
            """
            SELECT r.*, c.name AS category_name, c.slug AS category_slug,
                   u.username, u.first_name, u.last_name, u.chat_id,
                   (SELECT COUNT(*) FROM bot_evidence e WHERE e.request_id=r.id) AS evidence_count,
                   (SELECT COUNT(*) FROM bot_replies p WHERE p.request_id=r.id) AS reply_count
            FROM bot_requests r JOIN bot_users u ON u.telegram_user_id=r.telegram_user_id
            LEFT JOIN categories c ON c.id=r.category_id WHERE r.id=?
            """,
            (request_id,),
        ).fetchone()
        if not request:
            return None
        evidence = db.execute(
            "SELECT * FROM bot_evidence WHERE request_id=? ORDER BY sort_order, id", (request_id,)
        ).fetchall()
        replies = db.execute(
            "SELECT id, kind, body, file_name, mime_type, delivery_status, error, created_at, sent_at FROM bot_replies WHERE request_id=? ORDER BY sort_order, id",
            (request_id,),
        ).fetchall()
    payload = row_to_bot_request(request)
    payload["chat_id"] = request["chat_id"]
    payload["evidence"] = [dict(row) for row in evidence]
    payload["replies"] = [dict(row) for row in replies]
    return payload


def deliver_bot_reply(reply_id: int) -> tuple[bool, str]:
    with database() as db:
        row = db.execute(
            """
            SELECT p.*, r.request_code, u.chat_id
            FROM bot_replies p JOIN bot_requests r ON r.id=p.request_id
            JOIN bot_users u ON u.telegram_user_id=r.telegram_user_id WHERE p.id=?
            """,
            (reply_id,),
        ).fetchone()
    if not row:
        return False, "Javob yozuvi topilmadi."
    if row["kind"] == "text":
        result = telegram_send_text(row["chat_id"], f"Mutaxassis javobi · {row['request_code']}\n\n{row['body']}")
    else:
        local_path = Path(row["local_path"])
        try:
            file_bytes = local_path.read_bytes()
        except OSError as error:
            result = {"ok": False, "description": f"Javob faylini o'qib bo'lmadi: {error}"}
        else:
            method = "sendPhoto" if row["kind"] == "photo" else "sendVideo" if row["kind"] == "video" else "sendDocument"
            field = "photo" if row["kind"] == "photo" else "video" if row["kind"] == "video" else "document"
            result = telegram_call(
                method,
                {"chat_id": row["chat_id"], "caption": f"Mutaxassis javobi · {row['request_code']}"},
                field, row["file_name"], file_bytes, row["mime_type"] or "application/octet-stream",
            )
    ok = bool(result.get("ok"))
    description = "" if ok else str(result.get("description", "Telegram xatosi."))[:1000]
    message_id = None
    if ok and isinstance(result.get("result"), dict):
        message_id = result["result"].get("message_id")
    with database() as db:
        db.execute(
            """
            UPDATE bot_replies SET delivery_status=?, error=?, telegram_message_id=?,
                sent_at=CASE WHEN ? THEN CURRENT_TIMESTAMP ELSE sent_at END WHERE id=?
            """,
            ("sent" if ok else "failed", description, message_id, int(ok), reply_id),
        )
        if ok:
            db.execute(
                "UPDATE bot_requests SET status='answered', updated_at=CURRENT_TIMESTAMP WHERE id=? AND status NOT IN ('closed','draft')",
                (row["request_id"],),
            )
            db.execute(
                "INSERT INTO bot_events (request_id, event_type, payload) VALUES (?, 'reply_sent', ?)",
                (row["request_id"], json.dumps({"reply_id": reply_id, "kind": row["kind"]})),
            )
    return ok, description


def create_and_deliver_replies(request_id: int, data: dict) -> dict:
    text = str(data.get("text", "")).strip()
    files = data.get("files", [])
    if not isinstance(files, list):
        raise ValueError("Javob fayllari ro'yxat ko'rinishida bo'lsin.")
    if len(text) > 12_000:
        raise ValueError("Javob matni 12 000 belgidan oshmasin.")
    if len(files) > 5:
        raise ValueError("Bir yuborishda ko'pi bilan 5 ta fayl biriktiring.")
    if not text and not files:
        raise ValueError("Javob matni yoki kamida bitta fayl kiriting.")
    with database() as db:
        request = db.execute("SELECT id FROM bot_requests WHERE id=? AND status!='draft'", (request_id,)).fetchone()
    if not request:
        raise ValueError("Yuborilgan murojaat topilmadi.")

    prepared: list[tuple[str, str, str, bytes]] = []
    total_bytes = 0
    for file in files:
        if not isinstance(file, dict):
            raise ValueError("Fayl ma'lumoti noto'g'ri.")
        name = Path(str(file.get("name", "file.bin"))).name[:180] or "file.bin"
        mime = str(file.get("type", "application/octet-stream"))[:200]
        encoded = str(file.get("data", ""))
        if "," in encoded:
            encoded = encoded.split(",", 1)[1]
        try:
            file_bytes = base64.b64decode(encoded, validate=True)
        except (ValueError, TypeError):
            raise ValueError(f"{name} faylining kodlanishi noto'g'ri.")
        if len(file_bytes) > 20 * 1024 * 1024:
            raise ValueError(f"{name} fayli 20 MB dan oshmasin.")
        total_bytes += len(file_bytes)
        if total_bytes > 30 * 1024 * 1024:
            raise ValueError("Bir yuborishdagi fayllarning jami hajmi 30 MB dan oshmasin.")
        kind = "photo" if mime.startswith("image/") else "video" if mime.startswith("video/") else "document"
        prepared.append((kind, name, mime, file_bytes))

    BOT_REPLY_DIR.mkdir(parents=True, exist_ok=True)
    reply_ids: list[int] = []
    with BOT_LOCK, database() as db:
        sort_order = db.execute("SELECT COALESCE(MAX(sort_order), 0) FROM bot_replies WHERE request_id=?", (request_id,)).fetchone()[0]
        if text:
            sort_order += 10
            cursor = db.execute(
                "INSERT INTO bot_replies (request_id, kind, body, sort_order) VALUES (?, 'text', ?, ?)",
                (request_id, text, sort_order),
            )
            reply_ids.append(int(cursor.lastrowid))
        request_dir = BOT_REPLY_DIR / str(request_id)
        request_dir.mkdir(parents=True, exist_ok=True)
        for kind, name, mime, file_bytes in prepared:
            sort_order += 10
            stored_name = f"{uuid.uuid4().hex}-{name}"
            local_path = request_dir / stored_name
            local_path.write_bytes(file_bytes)
            cursor = db.execute(
                """
                INSERT INTO bot_replies (request_id, kind, file_name, mime_type, local_path, sort_order)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (request_id, kind, name, mime, str(local_path), sort_order),
            )
            reply_ids.append(int(cursor.lastrowid))
        db.execute("UPDATE bot_requests SET status='in_progress', updated_at=CURRENT_TIMESTAMP WHERE id=? AND status='new'", (request_id,))

    delivered = 0
    errors: list[str] = []
    for reply_id in reply_ids:
        ok, error = deliver_bot_reply(reply_id)
        delivered += int(ok)
        if error:
            errors.append(error)
    return {"ok": not errors, "created": len(reply_ids), "delivered": delivered, "errors": errors}


def fetch_telegram_evidence(evidence_id: int) -> tuple[bytes, str, str]:
    with database() as db:
        evidence = db.execute(
            "SELECT telegram_file_id, file_name, mime_type FROM bot_evidence WHERE id=?", (evidence_id,)
        ).fetchone()
    if not evidence or not evidence["telegram_file_id"]:
        raise ValueError("Yuklab olinadigan Telegram fayli mavjud emas.")
    result = telegram_call("getFile", {"file_id": evidence["telegram_file_id"]})
    if not result.get("ok") or not isinstance(result.get("result"), dict):
        raise ValueError(str(result.get("description", "Telegram fayl ma'lumotini qaytarmadi.")))
    file_path = str(result["result"].get("file_path", ""))
    if not file_path:
        raise ValueError("Telegram fayl manzilini qaytarmadi.")
    url = f"{TELEGRAM_API_BASE}/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            body = response.read(21 * 1024 * 1024)
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise ValueError(f"Telegram faylini yuklab bo'lmadi: {error}")
    if len(body) > 20 * 1024 * 1024:
        raise ValueError("Telegram fayli 20 MB yuklab olish chegarasidan oshadi.")
    name = evidence["file_name"] or Path(file_path).name or f"evidence-{evidence_id}"
    return body, str(name), evidence["mime_type"] or "application/octet-stream"


def clean_slug(value: object) -> str:
    slug = str(value or "").strip().lower()
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        raise ValueError("Slug faqat kichik lotin harflari, raqam va chiziqchadan iborat bo'lsin.")
    return slug


def clean_url(value: object, optional: bool = False) -> str:
    url = str(value or "").strip()
    if optional and not url:
        return ""
    parsed = urlparse(url.replace("{query}", "sample"))
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("URL manzilini http yoki https protokoli bilan to'g'ri kiriting.")
    return url


def clean_list(value: object) -> list[str]:
    if isinstance(value, list):
        items = value
    else:
        items = str(value or "").split(",")
    return list(dict.fromkeys(str(item).strip() for item in items if str(item).strip()))


def clean_details(value: object) -> str:
    details = str(value or "").strip()
    if len(details) > 20_000:
        raise ValueError("Batafsil ma'lumot 20 000 belgidan oshmasin.")
    return details


def clean_icon(value: object) -> str:
    icon = str(value or "auto").strip() or "auto"
    if len(icon) > 500:
        raise ValueError("Ikon qiymati 500 belgidan oshmasin.")
    if icon.startswith(("http://", "https://")):
        return clean_url(icon)
    return icon


def clean_catalog_text(value: object, label: str, maximum: int, required: bool = False) -> str:
    text = str(value or "").strip()
    if required and not text:
        raise ValueError(f"{label} kiritilmagan.")
    if len(text) > maximum:
        raise ValueError(f"{label} {maximum} belgidan oshmasin.")
    return text


def clean_catalog_bool(value: object, label: str, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and value in {0, 1}:
        return bool(value)
    raise ValueError(f"{label} true yoki false qiymatida bo'lsin.")


def clean_sort_order(value: object, default: int) -> int:
    if value is None:
        return default
    if isinstance(value, bool):
        raise ValueError("Tartib raqami butun son bo'lsin.")
    try:
        order = int(value)
    except (TypeError, ValueError) as error:
        raise ValueError("Tartib raqami butun son bo'lsin.") from error
    if not 0 <= order <= 1_000_000:
        raise ValueError("Tartib raqami 0 dan 1 000 000 gacha bo'lsin.")
    return order


def catalog_snapshot() -> dict:
    with database() as db:
        category_rows = db.execute(
            "SELECT * FROM categories ORDER BY sort_order, name"
        ).fetchall()
        tool_rows = db.execute(
            """
            SELECT t.*, c.slug AS category_slug, c.name AS category_name
            FROM tools t JOIN categories c ON c.id = t.category_id
            ORDER BY c.sort_order, t.sort_order, t.name
            """
        ).fetchall()

    categories = []
    for row in category_rows:
        item = row_to_category(row)
        categories.append({key: item[key] for key in (
            "name", "slug", "description", "details", "icon", "tags",
            "featured", "sort_order", "enabled",
        )})

    tools = []
    for row in tool_rows:
        item = row_to_tool(row)
        tools.append({key: item[key] for key in (
            "name", "slug", "category_slug", "description", "details", "url",
            "query_url_template", "icon", "input_types", "networks", "tags",
            "access", "login_required", "featured", "sort_order", "enabled",
        )})

    return {
        "format": CATALOG_FORMAT,
        "version": CATALOG_VERSION,
        "exported_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "categories": categories,
        "tools": tools,
    }


def sync_catalog_backup(snapshot: dict | None = None) -> bool:
    try:
        payload = snapshot or catalog_snapshot()
        encoded = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        JSON_BACKUP_PATH.parent.mkdir(parents=True, exist_ok=True)
        temporary = JSON_BACKUP_PATH.with_name(
            f".{JSON_BACKUP_PATH.name}.{os.getpid()}.{threading.get_ident()}.tmp"
        )
        with CATALOG_BACKUP_LOCK:
            try:
                with temporary.open("wb") as stream:
                    stream.write(encoded)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temporary, JSON_BACKUP_PATH)
            finally:
                if temporary.exists():
                    temporary.unlink()
        return True
    except OSError as error:
        print(f"[catalog-backup] JSON backup yaratilmadi: {error}")
        return False


def normalize_catalog_import(data: dict) -> tuple[list[dict], list[dict]]:
    if data.get("format") != CATALOG_FORMAT or data.get("version") != CATALOG_VERSION:
        raise ValueError("JSON fayl OSINT Navigator katalogining 1-versiya formatida emas.")
    if data.get("confirm_replace") is not True:
        raise ValueError("Katalogni almashtirish tasdiqlanmagan.")

    category_items = data.get("categories")
    tool_items = data.get("tools")
    if not isinstance(category_items, list) or not isinstance(tool_items, list):
        raise ValueError("JSON faylda categories va tools ro'yxatlari bo'lishi kerak.")
    if len(category_items) > 200 or len(tool_items) > 5_000:
        raise ValueError("JSON fayldagi katalog yozuvlari ruxsat etilgan chegaradan oshgan.")

    categories: list[dict] = []
    category_slugs: set[str] = set()
    for index, raw in enumerate(category_items, start=1):
        if not isinstance(raw, dict):
            raise ValueError(f"{index}-kategoriya yozuvi obyekt ko'rinishida emas.")
        slug = clean_slug(raw.get("slug"))
        if slug in category_slugs:
            raise ValueError(f"Kategoriya slugi takrorlangan: {slug}.")
        category_slugs.add(slug)
        categories.append({
            "name": clean_catalog_text(raw.get("name"), "Kategoriya nomi", 200, True),
            "slug": slug,
            "description": clean_catalog_text(raw.get("description"), "Kategoriya tavsifi", 5_000),
            "details": clean_details(raw.get("details")),
            "icon": clean_icon(raw.get("icon")),
            "tags": clean_list(raw.get("tags")),
            "featured": clean_catalog_bool(raw.get("featured"), "Kategoriya ustuvorligi", False),
            "sort_order": clean_sort_order(raw.get("sort_order"), index * 10),
            "enabled": clean_catalog_bool(raw.get("enabled"), "Kategoriya holati", True),
        })
    if sum(category["featured"] for category in categories) > 3:
        raise ValueError("Birinchi qator uchun ko'pi bilan 3 ta tekshiruv yo'nalishini tanlang.")

    tools: list[dict] = []
    tool_slugs: set[str] = set()
    for index, raw in enumerate(tool_items, start=1):
        if not isinstance(raw, dict):
            raise ValueError(f"{index}-vosita yozuvi obyekt ko'rinishida emas.")
        slug = clean_slug(raw.get("slug"))
        if slug in tool_slugs:
            raise ValueError(f"Vosita slugi takrorlangan: {slug}.")
        tool_slugs.add(slug)
        category_slug = clean_slug(raw.get("category_slug"))
        if category_slug not in category_slugs:
            raise ValueError(f"{slug} vositasi uchun kategoriya topilmadi: {category_slug}.")
        access = str(raw.get("access", "free")).strip()
        if access not in {"free", "free-tier", "paid"}:
            raise ValueError(f"{slug} vositasining foydalanish turi noto'g'ri.")
        tools.append({
            "name": clean_catalog_text(raw.get("name"), "Vosita nomi", 200, True),
            "slug": slug,
            "category_slug": category_slug,
            "description": clean_catalog_text(raw.get("description"), "Vosita tavsifi", 5_000),
            "details": clean_details(raw.get("details")),
            "url": clean_url(raw.get("url")),
            "query_url_template": clean_url(raw.get("query_url_template"), optional=True),
            "icon": clean_icon(raw.get("icon")),
            "input_types": clean_list(raw.get("input_types")),
            "networks": clean_list(raw.get("networks")),
            "tags": clean_list(raw.get("tags")),
            "access": access,
            "login_required": clean_catalog_bool(raw.get("login_required"), "Login talabi", False),
            "featured": clean_catalog_bool(raw.get("featured"), "Vosita ustuvorligi", False),
            "sort_order": clean_sort_order(raw.get("sort_order"), index * 10),
            "enabled": clean_catalog_bool(raw.get("enabled"), "Vosita holati", True),
        })
    return categories, tools


def replace_catalog_from_json(data: dict) -> tuple[int, int]:
    categories, tools = normalize_catalog_import(data)
    with database() as db:
        db.execute("DELETE FROM tools")
        db.execute("DELETE FROM categories")
        category_ids: dict[str, int] = {}
        for category in categories:
            cursor = db.execute(
                """
                INSERT INTO categories (name, slug, description, details, icon, tags, featured, sort_order, enabled)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    category["name"], category["slug"], category["description"], category["details"],
                    category["icon"], json.dumps(category["tags"], ensure_ascii=False),
                    int(category["featured"]), category["sort_order"], int(category["enabled"]),
                ),
            )
            category_ids[category["slug"]] = cursor.lastrowid
        for tool in tools:
            db.execute(
                """
                INSERT INTO tools (
                    name, slug, category_id, description, details, url, query_url_template, icon,
                    input_types, networks, tags, access, login_required, featured, sort_order, enabled
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    tool["name"], tool["slug"], category_ids[tool["category_slug"]],
                    tool["description"], tool["details"], tool["url"], tool["query_url_template"],
                    tool["icon"], json.dumps(tool["input_types"], ensure_ascii=False),
                    json.dumps(tool["networks"], ensure_ascii=False),
                    json.dumps(tool["tags"], ensure_ascii=False), tool["access"],
                    int(tool["login_required"]), int(tool["featured"]),
                    tool["sort_order"], int(tool["enabled"]),
                ),
            )
        db.execute("PRAGMA optimize")
    return len(categories), len(tools)


class OSINTHandler(BaseHTTPRequestHandler):
    server_version = "OSINTNavigator/1.0"

    def log_message(self, format: str, *args) -> None:
        print(f"[{self.log_date_time_string()}] {format % args}")

    def send_json(self, payload: object, status: int = 200, headers: dict[str, str] | None = None) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        if headers:
            for key, value in headers.items():
                self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, path: Path) -> None:
        try:
            resolved = path.resolve(strict=True)
            if STATIC_DIR.resolve() not in resolved.parents and resolved != STATIC_DIR.resolve():
                self.send_error(HTTPStatus.FORBIDDEN)
                return
            body = resolved.read_bytes()
        except (FileNotFoundError, OSError):
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        mime_type = "application/geo+json" if resolved.suffix.lower() == ".geojson" else (mimetypes.guess_type(str(resolved))[0] or "application/octet-stream")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", f"{mime_type}; charset=utf-8" if mime_type.startswith("text/") else mime_type)
        self.send_header("Content-Length", str(len(body)))
        cacheable = resolved.suffix.lower() in {".css", ".js", ".json", ".geojson", ".png", ".jpg", ".jpeg", ".webp", ".ico", ".woff", ".woff2"}
        self.send_header("Cache-Control", "public, max-age=300" if cacheable else "no-cache")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def send_bytes(self, body: bytes, mime_type: str, file_name: str = "") -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", mime_type or "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        if file_name:
            safe_name = Path(file_name).name.replace('"', "")
            self.send_header("Content-Disposition", f'attachment; filename="{safe_name}"')
        self.end_headers()
        self.wfile.write(body)

    def read_json(self, max_bytes: int = 1_000_000) -> dict:
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 0 or length > max_bytes:
                raise ValueError(f"Yuborilgan ma'lumot hajmi {max_bytes // 1_000_000} MB chegaradan oshdi.")
            data = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            return data if isinstance(data, dict) else {}
        except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
            raise ValueError("Yuborilgan ma'lumot formati noto'g'ri.")

    def session_token(self) -> str | None:
        cookie = SimpleCookie(self.headers.get("Cookie", ""))
        morsel = cookie.get("osint_admin_session")
        if not morsel:
            return None
        token = morsel.value
        expires = SESSIONS.get(token, 0)
        if expires < time.time():
            SESSIONS.pop(token, None)
            return None
        return token

    def require_admin(self) -> bool:
        if self.session_token():
            return True
        self.send_json({"error": "Administrator hisobiga kiring."}, HTTPStatus.UNAUTHORIZED)
        return False

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/health":
            self.send_json({"ok": True, "bot_configured": bool(TELEGRAM_BOT_TOKEN and TELEGRAM_BOT_USERNAME and TELEGRAM_WEBHOOK_SECRET)})
            return

        if path == "/api/bot/config":
            enabled = bool(TELEGRAM_BOT_TOKEN and TELEGRAM_BOT_USERNAME and TELEGRAM_WEBHOOK_SECRET)
            self.send_json({
                "enabled": enabled,
                "url": f"https://t.me/{TELEGRAM_BOT_USERNAME}" if enabled else "",
            })
            return

        if path == "/api/categories":
            with database() as db:
                rows = db.execute(
                    """
                    SELECT c.*, COUNT(t.id) AS tool_count
                    FROM categories c
                    LEFT JOIN tools t ON t.category_id = c.id AND t.enabled = 1
                    WHERE c.enabled = 1
                    GROUP BY c.id
                    ORDER BY c.featured DESC, c.sort_order, c.name
                    """
                ).fetchall()
            self.send_json([row_to_category(row) for row in rows])
            return

        if path == "/api/tools":
            category = parse_qs(parsed.query).get("category", [""])[0]
            sql = """
                SELECT t.*, c.slug AS category_slug, c.name AS category_name
                FROM tools t JOIN categories c ON c.id = t.category_id
                WHERE t.enabled = 1 AND c.enabled = 1
            """
            params: list[object] = []
            if category:
                sql += " AND c.slug = ?"
                params.append(category)
            sql += " ORDER BY t.featured DESC, t.sort_order, t.name"
            with database() as db:
                rows = db.execute(sql, params).fetchall()
            self.send_json([row_to_tool(row) for row in rows])
            return

        if path == "/api/admin/session":
            self.send_json({"authenticated": bool(self.session_token()), "username": ADMIN_USERNAME})
            return

        if path == "/api/admin/catalog/export":
            if not self.require_admin():
                return
            self.send_json(
                catalog_snapshot(),
                headers={"Content-Disposition": 'attachment; filename="osint-catalog.json"'},
            )
            return

        if path == "/api/admin/categories":
            if not self.require_admin():
                return
            with database() as db:
                rows = db.execute(
                    """
                    SELECT c.*, COUNT(t.id) AS tool_count
                    FROM categories c LEFT JOIN tools t ON t.category_id = c.id
                    GROUP BY c.id ORDER BY c.featured DESC, c.sort_order, c.name
                    """
                ).fetchall()
            self.send_json([row_to_category(row) for row in rows])
            return

        if path == "/api/admin/tools":
            if not self.require_admin():
                return
            with database() as db:
                rows = db.execute(
                    """
                    SELECT t.*, c.slug AS category_slug, c.name AS category_name
                    FROM tools t JOIN categories c ON c.id = t.category_id
                    ORDER BY c.featured DESC, c.sort_order, t.featured DESC, t.sort_order, t.name
                    """
                ).fetchall()
            self.send_json([row_to_tool(row) for row in rows])
            return

        if path == "/api/admin/requests":
            if not self.require_admin():
                return
            status = parse_qs(parsed.query).get("status", [""])[0]
            sql = """
                SELECT r.*, c.name AS category_name, c.slug AS category_slug,
                       u.username, u.first_name, u.last_name,
                       (SELECT COUNT(*) FROM bot_evidence e WHERE e.request_id=r.id) AS evidence_count,
                       (SELECT COUNT(*) FROM bot_replies p WHERE p.request_id=r.id) AS reply_count
                FROM bot_requests r JOIN bot_users u ON u.telegram_user_id=r.telegram_user_id
                LEFT JOIN categories c ON c.id=r.category_id WHERE r.status!='draft'
            """
            params: list[object] = []
            if status:
                sql += " AND r.status=?"
                params.append(status)
            sql += " ORDER BY CASE r.status WHEN 'new' THEN 0 WHEN 'in_progress' THEN 1 WHEN 'answered' THEN 2 ELSE 3 END, r.updated_at DESC, r.id DESC"
            with database() as db:
                rows = db.execute(sql, params).fetchall()
            self.send_json([row_to_bot_request(row) for row in rows])
            return

        request_match = re.fullmatch(r"/api/admin/requests/(\d+)", path)
        if request_match:
            if not self.require_admin():
                return
            detail = bot_request_detail(int(request_match.group(1)))
            if not detail:
                self.send_json({"error": "Murojaat topilmadi."}, HTTPStatus.NOT_FOUND)
                return
            self.send_json(detail)
            return

        if path == "/api/admin/bot-users":
            if not self.require_admin():
                return
            with database() as db:
                rows = db.execute(
                    """
                    SELECT u.*, COUNT(r.id) AS request_count
                    FROM bot_users u LEFT JOIN bot_requests r ON r.telegram_user_id=u.telegram_user_id AND r.status!='draft'
                    GROUP BY u.telegram_user_id ORDER BY u.last_seen_at DESC
                    """
                ).fetchall()
            self.send_json([dict(row) for row in rows])
            return

        evidence_match = re.fullmatch(r"/api/admin/evidence/(\d+)/download", path)
        if evidence_match:
            if not self.require_admin():
                return
            try:
                body, name, mime_type = fetch_telegram_evidence(int(evidence_match.group(1)))
                self.send_bytes(body, mime_type, name)
            except ValueError as error:
                self.send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
            return

        if path in {"/", "/index.html", "/guide", "/guide/"} or path.startswith("/category/"):
            self.send_file(STATIC_DIR / "index.html")
            return
        if path == "/favicon.ico":
            self.send_response(HTTPStatus.NO_CONTENT)
            self.end_headers()
            return
        if path in {"/admin", "/admin/"}:
            self.send_file(STATIC_DIR / "admin.html")
            return
        if path.startswith("/static/"):
            self.send_file(STATIC_DIR / path.removeprefix("/static/"))
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/telegram/webhook":
            supplied_secret = self.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
            if not TELEGRAM_BOT_TOKEN or not TELEGRAM_WEBHOOK_SECRET:
                self.send_json({"error": "Telegram webhook sozlanmagan."}, HTTPStatus.SERVICE_UNAVAILABLE)
                return
            if not hmac.compare_digest(supplied_secret, TELEGRAM_WEBHOOK_SECRET):
                self.send_json({"error": "Webhook imzosi noto'g'ri."}, HTTPStatus.FORBIDDEN)
                return
            try:
                update = self.read_json(2_000_000)
            except ValueError as error:
                self.send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
                return
            self.send_json({"ok": True})
            threading.Thread(target=process_telegram_update, args=(update,), daemon=True).start()
            return
        try:
            json_limit = 48_000_000 if re.fullmatch(r"/api/admin/requests/\d+/reply", path) else 1_000_000
            data = self.read_json(json_limit)
        except ValueError as error:
            self.send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
            return

        if path == "/api/admin/login":
            username = str(data.get("username", ""))
            password = str(data.get("password", ""))
            valid = hmac.compare_digest(username, ADMIN_USERNAME) and hmac.compare_digest(
                hashlib.sha256(password.encode()).digest(),
                hashlib.sha256(ADMIN_PASSWORD.encode()).digest(),
            )
            if not valid:
                self.send_json({"error": "Administrator login yoki paroli noto'g'ri."}, HTTPStatus.UNAUTHORIZED)
                return
            token = secrets.token_urlsafe(32)
            SESSIONS[token] = time.time() + SESSION_TTL
            secure = "; Secure" if SECURE_COOKIE else ""
            self.send_json(
                {"ok": True, "username": ADMIN_USERNAME},
                headers={"Set-Cookie": f"osint_admin_session={token}; Path=/; HttpOnly; SameSite=Strict; Max-Age={SESSION_TTL}{secure}"},
            )
            return

        if path == "/api/admin/logout":
            token = self.session_token()
            if token:
                SESSIONS.pop(token, None)
            self.send_json(
                {"ok": True},
                headers={"Set-Cookie": "osint_admin_session=; Path=/; HttpOnly; SameSite=Strict; Max-Age=0"},
            )
            return

        if not self.require_admin():
            return

        reply_match = re.fullmatch(r"/api/admin/requests/(\d+)/reply", path)
        if reply_match:
            try:
                result = create_and_deliver_replies(int(reply_match.group(1)), data)
                self.send_json(result)
            except (ValueError, OSError) as error:
                self.send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
            return

        retry_match = re.fullmatch(r"/api/admin/replies/(\d+)/deliver", path)
        if retry_match:
            ok, error = deliver_bot_reply(int(retry_match.group(1)))
            self.send_json({"ok": ok, "error": error}, HTTPStatus.OK if ok else HTTPStatus.BAD_GATEWAY)
            return

        if path == "/api/admin/catalog/import":
            try:
                category_count, tool_count = replace_catalog_from_json(data)
                backup_written = sync_catalog_backup()
                self.send_json({
                    "ok": True,
                    "categories": category_count,
                    "tools": tool_count,
                    "backup_written": backup_written,
                })
            except sqlite3.IntegrityError:
                self.send_json(
                    {"error": "JSON katalogida takrorlangan yoki o'zaro mos bo'lmagan yozuv mavjud."},
                    HTTPStatus.CONFLICT,
                )
            except (ValueError, TypeError) as error:
                self.send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
            return
        if path == "/api/admin/categories":
            self.save_category(data)
            return
        if path == "/api/admin/tools":
            self.save_tool(data)
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_PUT(self) -> None:
        if not self.require_admin():
            return
        path = urlparse(self.path).path
        try:
            data = self.read_json()
            item_id = int(path.rstrip("/").split("/")[-1])
        except (ValueError, IndexError):
            self.send_json({"error": "Noto'g'ri so'rov."}, HTTPStatus.BAD_REQUEST)
            return
        if path.startswith("/api/admin/requests/"):
            status = str(data.get("status", "")).strip()
            if status not in {"new", "in_progress", "answered", "closed"}:
                self.send_json({"error": "Murojaat holati noto'g'ri."}, HTTPStatus.BAD_REQUEST)
                return
            summary = str(data.get("summary", "")).strip()
            if len(summary) > 10_000:
                self.send_json({"error": "Ichki izoh 10 000 belgidan oshmasin."}, HTTPStatus.BAD_REQUEST)
                return
            with database() as db:
                cursor = db.execute(
                    """
                    UPDATE bot_requests SET status=?, summary=?, updated_at=CURRENT_TIMESTAMP,
                        closed_at=CASE WHEN ?='closed' THEN CURRENT_TIMESTAMP ELSE NULL END
                    WHERE id=? AND status!='draft'
                    """,
                    (status, summary, status, item_id),
                )
            if not cursor.rowcount:
                self.send_json({"error": "Murojaat topilmadi."}, HTTPStatus.NOT_FOUND)
                return
            self.send_json({"ok": True})
            return
        if path.startswith("/api/admin/bot-users/"):
            approved = int(bool(data.get("approved", False)))
            blocked = int(bool(data.get("blocked", False)))
            with database() as db:
                cursor = db.execute(
                    "UPDATE bot_users SET approved=?, blocked=?, updated_at=CURRENT_TIMESTAMP WHERE telegram_user_id=?",
                    (approved, blocked, item_id),
                )
            if not cursor.rowcount:
                self.send_json({"error": "Bot foydalanuvchisi topilmadi."}, HTTPStatus.NOT_FOUND)
                return
            self.send_json({"ok": True})
            return
        if path.startswith("/api/admin/categories/"):
            self.save_category(data, item_id)
            return
        if path.startswith("/api/admin/tools/"):
            self.save_tool(data, item_id)
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_DELETE(self) -> None:
        if not self.require_admin():
            return
        path = urlparse(self.path).path
        try:
            item_id = int(path.rstrip("/").split("/")[-1])
        except (ValueError, IndexError):
            self.send_json({"error": "Noto'g'ri ID."}, HTTPStatus.BAD_REQUEST)
            return
        with database() as db:
            if path.startswith("/api/admin/categories/"):
                db.execute("DELETE FROM categories WHERE id = ?", (item_id,))
            elif path.startswith("/api/admin/tools/"):
                db.execute("DELETE FROM tools WHERE id = ?", (item_id,))
            else:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
        self.send_json({"ok": True, "backup_written": sync_catalog_backup()})

    def save_category(self, data: dict, item_id: int | None = None) -> None:
        try:
            name = str(data.get("name", "")).strip()
            if not name:
                raise ValueError("Tekshiruv yo'nalishi nomini kiriting.")
            featured = int(bool(data.get("featured", False)))
            with database() as db:
                if featured:
                    params: tuple[object, ...] = ()
                    sql = "SELECT COUNT(*) FROM categories WHERE featured = 1"
                    if item_id is not None:
                        sql += " AND id != ?"
                        params = (item_id,)
                    if db.execute(sql, params).fetchone()[0] >= 3:
                        raise ValueError("Birinchi qator uchun ko'pi bilan 3 ta tekshiruv yo'nalishini tanlang.")

                if item_id is None:
                    sort_order = db.execute("SELECT COALESCE(MAX(sort_order), 0) + 10 FROM categories").fetchone()[0]
                else:
                    current = db.execute("SELECT sort_order FROM categories WHERE id = ?", (item_id,)).fetchone()
                    if not current:
                        raise ValueError("Tekshiruv yo'nalishi aniqlanmadi.")
                    sort_order = current["sort_order"]

                values = (
                    name,
                    clean_slug(data.get("slug")),
                    str(data.get("description", "")).strip(),
                    clean_details(data.get("details")),
                    clean_icon(data.get("icon")),
                    json.dumps(clean_list(data.get("tags")), ensure_ascii=False),
                    featured,
                    sort_order,
                    int(bool(data.get("enabled", True))),
                )
                if item_id is None:
                    cursor = db.execute(
                        "INSERT INTO categories (name, slug, description, details, icon, tags, featured, sort_order, enabled) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        values,
                    )
                    item_id = cursor.lastrowid
                else:
                    db.execute(
                        """
                        UPDATE categories SET name=?, slug=?, description=?, details=?, icon=?, tags=?, featured=?, sort_order=?, enabled=?,
                        updated_at=CURRENT_TIMESTAMP WHERE id=?
                        """,
                        values + (item_id,),
                    )
            self.send_json({"ok": True, "id": item_id, "backup_written": sync_catalog_backup()})
        except sqlite3.IntegrityError:
            self.send_json({"error": "Bu slug allaqachon mavjud."}, HTTPStatus.CONFLICT)
        except (ValueError, TypeError) as error:
            self.send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)

    def save_tool(self, data: dict, item_id: int | None = None) -> None:
        try:
            name = str(data.get("name", "")).strip()
            if not name:
                raise ValueError("OSINT vositasi nomini kiriting.")
            category_id = int(data.get("category_id"))
            with database() as db:
                if item_id is None:
                    sort_order = db.execute(
                        "SELECT COALESCE(MAX(sort_order), 0) + 10 FROM tools WHERE category_id = ?",
                        (category_id,),
                    ).fetchone()[0]
                else:
                    current = db.execute("SELECT category_id, sort_order FROM tools WHERE id = ?", (item_id,)).fetchone()
                    if not current:
                        raise ValueError("OSINT vositasi aniqlanmadi.")
                    if current["category_id"] == category_id:
                        sort_order = current["sort_order"]
                    else:
                        sort_order = db.execute(
                            "SELECT COALESCE(MAX(sort_order), 0) + 10 FROM tools WHERE category_id = ?",
                            (category_id,),
                        ).fetchone()[0]

                values = (
                    name,
                    clean_slug(data.get("slug")),
                    category_id,
                    str(data.get("description", "")).strip(),
                    clean_details(data.get("details")),
                    clean_url(data.get("url")),
                    clean_url(data.get("query_url_template"), optional=True),
                    clean_icon(data.get("icon")),
                    json.dumps(clean_list(data.get("input_types")), ensure_ascii=False),
                    json.dumps(clean_list(data.get("networks")), ensure_ascii=False),
                    json.dumps(clean_list(data.get("tags")), ensure_ascii=False),
                    str(data.get("access", "free")),
                    int(bool(data.get("login_required", False))),
                    int(bool(data.get("featured", False))),
                    sort_order,
                    int(bool(data.get("enabled", True))),
                )
                if item_id is None:
                    cursor = db.execute(
                        """
                        INSERT INTO tools (
                            name, slug, category_id, description, details, url, query_url_template, icon,
                            input_types, networks, tags, access, login_required, featured, sort_order, enabled
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        values,
                    )
                    item_id = cursor.lastrowid
                else:
                    db.execute(
                        """
                        UPDATE tools SET name=?, slug=?, category_id=?, description=?, details=?, url=?, query_url_template=?, icon=?,
                        input_types=?, networks=?, tags=?, access=?, login_required=?, featured=?, sort_order=?, enabled=?,
                        updated_at=CURRENT_TIMESTAMP WHERE id=?
                        """,
                        values + (item_id,),
                    )
            self.send_json({"ok": True, "id": item_id, "backup_written": sync_catalog_backup()})
        except sqlite3.IntegrityError:
            self.send_json({"error": "Slug takrorlangan yoki tekshiruv yo'nalishi aniqlanmadi."}, HTTPStatus.CONFLICT)
        except (ValueError, TypeError) as error:
            self.send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)


class ExclusiveThreadingHTTPServer(ThreadingHTTPServer):
    """Windowsda bir portda ikki eski server nusxasi yonma-yon qolishini to'xtatadi."""

    daemon_threads = True
    allow_reuse_address = False

    def server_bind(self) -> None:
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


def main() -> None:
    if PRODUCTION and ADMIN_PASSWORD == "admin123":
        raise RuntimeError("Production uchun OSINT_ADMIN_PASSWORD ni kuchli parolga o'zgartiring.")
    init_database()
    try:
        server = ExclusiveThreadingHTTPServer((HOST, PORT), OSINTHandler)
    except OSError as error:
        if getattr(error, "winerror", None) == 10048 or getattr(error, "errno", None) == 98:
            raise SystemExit(
                f"{HOST}:{PORT} porti band. Avval ishlayotgan OSINT Navigator oynasini Ctrl+C bilan to'xtating."
            ) from error
        raise
    print("\nOSINT Navigator ishga tushdi")
    print(f"Sayt:        http://{HOST}:{PORT}/")
    print(f"Admin panel: http://{HOST}:{PORT}/admin/")
    print(f"Login:       {ADMIN_USERNAME}")
    if ADMIN_PASSWORD == "admin123":
        print("Parol:       admin123 (production uchun OSINT_ADMIN_PASSWORD ni o'zgartiring)")
    print("To'xtatish:  Ctrl+C\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer to'xtatildi.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
