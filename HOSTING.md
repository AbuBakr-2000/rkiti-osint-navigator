# Tekin hostingga joylash

## Tavsiya: alwaysdata Free

Ushbu dastur tashqi Python paketlarisiz WSGI va SQLite bilan ishlaydi. Shu sababli doimiy disk, Python WSGI va HTTPS taqdim etadigan alwaysdata Free eng sodda tekin variant hisoblanadi.

Free tarifning asosiy chegaralari: 1 GB SSD, 256 MB RAM, 1/4 CPU va 3 kunlik zaxira nusxa. U shaxsiy/notijoriy loyiha uchun mo'ljallangan va bepul hisobda faqat `*.alwaysdata.net` manzilidan foydalaniladi. Institutning rasmiy, doimiy foydalaniladigan tizimi uchun tashkilot tasdiqlagan server hamda axborot xavfsizligi talablari qo'llanishi kerak.

## 1. Qaysi arxivni yuklash kerak

`deploy` papkasida ikkita tayyor paket bo'ladi:

- `osint-navigator-hosting-current.zip` — hozirgi 7 ta kategoriya, 38 ta vosita va ularning batafsil ma'lumotlari bilan ko'chadi. Tayyor katalogni darhol ishlatish uchun shu variantni tanlang.
- `osint-navigator-hosting-empty.zip` — baza bo'sh yaratiladi; kategoriya va vositalarni admin panel orqali noldan kiritasiz. Faqat katalogni butunlay yangidan tuzmoqchi bo'lsangiz tanlang.

Arxivni kompyuterda oching. Ichida `osint-navigator` papkasi bo'lishi kerak.

## 2. alwaysdata hisobini tayyorlash

1. `https://www.alwaysdata.com/` saytida Free hisob yarating.
2. Panelda `Remote access -> SSH/SFTP` bo'limiga o'ting va SFTP kirishini yoqing.
3. FileZilla dasturida quyidagi ulanishni yarating:
   - Protocol: `SFTP - SSH File Transfer Protocol`
   - Host: `ssh-ACCOUNT.alwaysdata.net`
   - Port: `22`
   - User: `ACCOUNT`
   - Password: alwaysdata hisob paroli
4. Ochilgan `osint-navigator` papkasini serverdagi `/home/ACCOUNT/` ichiga yuklang.

Natijada serverda `/home/ACCOUNT/osint-navigator/app.py` fayli mavjud bo'lishi kerak. `ACCOUNT` o'rniga alwaysdata hisob nomini yozing.

## 3. Python WSGI saytini yaratish

alwaysdata panelida `Web -> Sites -> Add a site` bo'limini oching va quyidagilarni kiriting:

- Name: `OSINT Navigator`
- Address: alwaysdata bergan `ACCOUNT.alwaysdata.net` manzili
- Type: `Python WSGI`
- Application path: `/home/ACCOUNT/osint-navigator/wsgi.py`
- Working directory: `/home/ACCOUNT/osint-navigator`
- Python version: `3.11` yoki yangiroq

`Environment variables` bo'limiga bir qatordan quyidagilarni kiriting:

```text
OSINT_PRODUCTION=1
OSINT_ADMIN_USERNAME=osintadmin
OSINT_ADMIN_PASSWORD=BU_YERGA_KUCHLI_VA_MAXFIY_PAROL
OSINT_DB_PATH=/home/ACCOUNT/osint-navigator/data/osint.sqlite3
OSINT_JSON_BACKUP_PATH=/home/ACCOUNT/osint-navigator/data/catalog-backup.json
OSINT_SEED_DEMO=0
OSINT_SECURE_COOKIE=1
OSINT_PUBLIC_URL=https://ACCOUNT.alwaysdata.net
TELEGRAM_BOT_TOKEN=BOTFATHER_BERGAN_TOKEN
TELEGRAM_BOT_USERNAME=BOT_USERNAME
TELEGRAM_WEBHOOK_SECRET=KAMIDA_16_BELGILI_TASODIFIY_MAXFIY_QIYMAT
TELEGRAM_ADMIN_CHAT_ID=
TELEGRAM_REQUIRE_APPROVAL=0
TELEGRAM_MAX_EVIDENCE=50
```

Parol kamida 16 belgidan iborat, boshqa joyda ishlatilmagan va taxmin qilish qiyin bo'lsin. Parolni arxiv yoki kod ichiga yozmang; u faqat hostingning yopiq environment maydonida turishi kerak.

Sozlamalarni saqlang. Sayt sozlamasida Let's Encrypt SSL'ni va HTTP so'rovlarini HTTPS'ga yo'naltirishni yoqing, so'ng saytni `Restart` yoki `Reload` qiling.

## 4. Birinchi kirish

1. Saytni `https://ACCOUNT.alwaysdata.net/` manzilida tekshiring.
2. Admin sahifasini faqat to'g'ridan-to'g'ri `https://ACCOUNT.alwaysdata.net/admin/` orqali oching.
3. Login sifatida `OSINT_ADMIN_USERNAME`, parol sifatida `OSINT_ADMIN_PASSWORD` maydoniga kiritgan qiymatingizdan foydalaning.
4. Bo'sh paketda avval `Kategoriyalar`, keyin `Vositalar` bo'limiga ma'lumot kiriting.

## 5. Telegram botni ulash

1. Telegramdagi `@BotFather` orqali yangi bot yarating va token oling.
2. Yuqoridagi `TELEGRAM_BOT_TOKEN`, `TELEGRAM_BOT_USERNAME` hamda tasodifiy `TELEGRAM_WEBHOOK_SECRET` qiymatlarini alwaysdata environment sozlamalariga kiriting.
3. `OSINT_PUBLIC_URL` qiymatini saytingizning to'liq HTTPS manzili bilan kiriting; oxirida `/` bo'lmasin.
4. alwaysdata SSH terminalida quyidagi buyruqni bir marta bajaring:

```bash
cd /home/ACCOUNT/osint-navigator
python bot_setup.py
```

Terminalda bot username va webhook manzili ko'rinsa, ulanish tayyor. Saytdagi `Mutaxassis bilan bog'lanish` tugmasi bot username sozlanganida Telegram botni ochadi; aks holda avvalgi telefon raqami ko'rsatiladi.

`TELEGRAM_REQUIRE_APPROVAL=1` qiymati yopiq foydalanish rejimini yoqadi. Bu rejimda yangi foydalanuvchini admin paneldagi `Bot foydalanuvchilari` bo'limidan tasdiqlash kerak.

## 6. Admin login yoki parolini o'zgartirish

1. alwaysdata panelida `Web -> Sites -> OSINT Navigator` sahifasini oching.
2. `Environment variables` ichidagi `OSINT_ADMIN_PASSWORD` qiymatini yangi maxfiy parolga almashtiring. Loginni o'zgartirish uchun `OSINT_ADMIN_USERNAME` qiymatini tahrirlang.
3. `Save` bosing va saytni `Restart/Reload` qiling.
4. Admin sahifasiga yangi ma'lumotlar bilan qayta kiring.

Parol o'zgargach uni ishonchli password managerda saqlang. Parolni Telegram, ochiq hujjat yoki kod orqali yubormang.

## 7. Tekin tarifning muhim shartlari

- Yangi Free profil bloklanmasligi uchun alwaysdata boshqaruv paneliga kamida har 120 kunda bir marta kiring. Profil yoshi oshgani sayin bu muddat uzayadi.
- Free tarif faqat shaxsiy va daromad keltirmaydigan foydalanishga mo'ljallangan; tijorat yoki tashkilotning rasmiy sayti uchun tarif shartlarini oldindan alwaysdata bilan aniqlashtiring.
- Free tarifda faqat `ACCOUNT.alwaysdata.net` manzili ishlaydi va zaxira nusxalari 3 kun saqlanadi.
- Ushbu katalog tashqi OSINT xizmatlariga faqat havola beradi; ularning ishlashi, mavjudligi va foydalanish shartlari tegishli xizmat operatoriga bog'liq.

## 8. Keyingi yangilanish va zaxira nusxa

- Admin ma'lumotlari `/home/ACCOUNT/osint-navigator/data/osint.sqlite3` faylida saqlanadi; har bir katalog o'zgarishidan so'ng o'qiladigan `/home/ACCOUNT/osint-navigator/data/catalog-backup.json` nusxasi yangilanadi. Mutaxassis javobiga biriktirilgan fayllar `/home/ACCOUNT/osint-navigator/data/bot-replies` papkasida saqlanadi.
- Admin paneldagi `JSON eksport` katalogni kompyuterga yuklaydi. `JSON import` joriy katalogni tasdiqlashdan keyin to'liq almashtiradi.
- Fayllarni yangilaganda `data` papkasini ustidan yozmang; aks holda kiritilgan katalog yo'qolishi mumkin.
- Yangilashdan oldin `osint.sqlite3` va `catalog-backup.json` fayllarini SFTP orqali kompyuterga yuklab oling.
- Kod fayllarini yuklagach saytni `Restart/Reload` qiling.
- Xatolik bo'lsa alwaysdata panelidagi sayt loglarini tekshiring. Eng ko'p uchraydigan sabablar — noto'g'ri `Application path`, `Working directory`, `ACCOUNT` yoki production parolining standart `admin123` bo'lib qolishi.

## Mahalliy kompyuterda admin paroli

Oddiy `run.ps1` bilan ishga tushirilganda mahalliy login `admin`, parol `admin123`. Kuchli parol bilan ishga tushirish uchun `run-secure.ps1` ni oching: u login va parolni terminalda so'raydi, parolni faylga yozmaydi.

## PythonAnywhere muqobili

PythonAnywhere Beginner rejimida 1 web app va 512 MB disk mavjud, lekin bepul web app muddati va tashqi internet cheklovlari bor. Shu loyiha uchun alwaysdata Free sodda va mosroq; PythonAnywhere faqat muqobil variant sifatida tavsiya qilinadi.
