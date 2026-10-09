# OSINT Navigator

OSINT vositalari katalogi, murojaatlarni boshqarish paneli va ko'p dalilli Telegram botga ega Python dasturi.

## Ishga tushirish

Python 3.11 yoki yangiroq versiya kerak.

```powershell
python app.py
```

Windowsda login va parolni faylga yozmasdan kiritish uchun `run-secure.ps1` ni ishga tushirish mumkin. Hostingda login va parol `OSINT_ADMIN_USERNAME` hamda `OSINT_ADMIN_PASSWORD` environment qiymatlari orqali boshqariladi.

Yangi o'rnatishda baza bo'sh yaratiladi. Eski demo ma'lumotlari bilan ishga tushirish kerak bo'lsa, serverni boshlashdan oldin `OSINT_SEED_DEMO=1` muhit o'zgaruvchisini belgilang.

So'ng quyidagi sahifalarni oching:

- sayt: `http://127.0.0.1:8000/`
- admin panel: `http://127.0.0.1:8000/admin/`

Mahalliy demo uchun standart login:

- login: `admin`
- parol: `admin123`

Productionda parolni albatta o'zgartiring:

```powershell
$env:OSINT_ADMIN_PASSWORD="kuchli-yangi-parol"
python app.py
```

## Ma'lumotlarni boshqarish

Admin paneldan kategoriya va vositalarni qo'shish, tahrirlash, yashirish yoki o'chirish mumkin. Tartib raqami avtomatik belgilanadi. Kategoriya formasidagi `Birinchi qatorga chiqarish` belgisi orqali ko'pi bilan 3 ta ustuvor bo'lim tanlanadi; vosita formasidagi `Kategoriya ichida yuqoriga chiqarish` belgisi esa muhim vositalarni ro'yxat boshiga olib chiqadi. Har bir yozuv uchun tergovchi ushbu bo'lim yoki vosita orqali nimalar qila olishini izohlovchi batafsil matn kiritiladi. Ikon maydonidagi `auto` qiymati vosita saytining favicon/logosini avtomatik oladi; tayyor brend nomi, to'liq rasm URL'i yoki `text:IP` ko'rinishidagi matnli belgi ham ishlaydi. Barcha ma'lumotlar `data/osint.sqlite3` bazasida saqlanadi va har bir o'zgarishdan so'ng `data/catalog-backup.json` nusxasi atomar usulda yangilanadi. Admin paneldagi `JSON eksport` va `JSON import` tugmalari katalogni ko'chirish yoki qayta tiklash imkonini beradi.

Sayt, kategoriya sahifalari, login va admin panel TailAdmin form-layout uslubidagi bir xil adaptiv dizayn tizimidan foydalanadi. Lotin va kirill matni bir xil ko'rinishi uchun ikkala yozuvni to'liq qo'llaydigan Manrope shrift oilasi ishlatiladi. Light/dark rejim foydalanuvchi qurilmasiga mos tanlanadi va keyingi tashrif uchun brauzerda eslab qolinadi. `UZ / ЎЗ` tugmasi lotin va o'zbek kirill yozuvlarini almashtiradi; texnik atamalar (`username`, `ID`, `email`, `hash`, `URL`, `API` va boshqalar) o'zgarmaydi. Bosh va kategoriya sahifalaridagi interaktiv Globe Magic UI namunasi asosidagi COBE WebGL kutubxonasidan foydalanadi. Sahifa fonidagi past kontrastli koordinata to'ri hamda hero ichidagi statik tarmoq tugunlari OSINT mavzusini kuchaytiradi, lekin kontent o'qilishiga xalaqit bermaydi. Kutubxona yuklanmasa, adaptiv CSS globus ko'rinishda qoladi. Kartochkalarda servisning o'z logosi yoki kontekstga mos mavzuli ikon ko'rsatiladi.

## Telegram bot

Bot bir murojaat doirasida bir nechta matnli indikator, rasm, video, audio, APK/AAB va boshqa fayllarni qabul qiladi. Tergovchi yo'nalishni tanlaydi, dalillarni ketma-ket yuboradi va `Mutaxassisga yuborish` tugmasi bilan murojaatni ro'yxatdan o'tkazadi. Telefon raqami so'ralmaydi: foydalanuvchining Telegram `user_id` va shaxsiy chat `chat_id` qiymati saqlanadi, mutaxassis javobi aynan shu chatga yuboriladi. Admin paneldagi `Murojaatlar` bo'limida dalillar ko'riladi, holat va ichki izoh boshqariladi, matn hamda bir nechta fayldan iborat javob yuboriladi. `Bot foydalanuvchilari` bo'limi foydalanuvchini tasdiqlash yoki bloklash imkonini beradi.

Bot sozlamalari kodga yozilmaydi. `.env.example` dagi nomlar bo'yicha hostingning yopiq environment maydoniga quyidagilarni kiriting:

```text
OSINT_PUBLIC_URL=https://sizning-domeningiz.example
TELEGRAM_BOT_TOKEN=BotFather-bergan-token
TELEGRAM_BOT_USERNAME=bot_username
TELEGRAM_WEBHOOK_SECRET=kamida_16_belgili_tasodifiy_qiymat
TELEGRAM_ADMIN_CHAT_ID=ixtiyoriy
TELEGRAM_REQUIRE_APPROVAL=0
```

Sayt HTTPS manzilida ishga tushgach webhook va bot buyruqlarini bir marta ro'yxatdan o'tkazing:

```powershell
python bot_setup.py
```

`TELEGRAM_REQUIRE_APPROVAL=1` bo'lsa, yangi foydalanuvchi admin paneldan tasdiqlanmaguncha botdan foydalana olmaydi. Telegramdan kelgan fayllar bazada `file_id` orqali qayd etiladi; mutaxassis yuborgan fayllar `data/bot-replies` ichida saqlanadi. Ushbu papka va SQLite bazani birga zaxiralash kerak.

## Tuzilma

```text
app.py                 Backend, API va SQLite
bot_setup.py           Telegram webhook va bot buyruqlarini ulash
data/osint.sqlite3     Avtomatik yaratiladigan ma'lumotlar bazasi
data/catalog-backup.json  Avtomatik yangilanadigan o'qiladigan JSON nusxa
static/index.html      Asosiy sayt
static/app.js          Qidiruv, filtr va kartochkalar
static/icon-system.js  Avtomatik servis logolari va ikon fallback tizimi
static/world-map.js    Yengil 2D Mercator xarita renderi
static/world-110m.geojson  Natural Earth mamlakat konturlari
static/styles.css      Sayt dizayni
static/admin.html      Admin panel
static/admin.js        Admin boshqaruvi
static/admin.css       Admin panel dizayni
.env.example           Maxfiy bo'lmagan environment sozlamalari namunasi
```

Qidiruv qiymatlari bazaga yozilmaydi. Har bir alohida “Batafsil” tugmasi sahifani yangilamasdan ichki modal oynani ochadi; vositaning asosiy kartochkasi bosilgandagina mos tashqi servis ochiladi.

Tekin hostingga joylash bo'yicha to'liq ko'rsatma `HOSTING.md` faylida. `build-hosting-packages.ps1` bo'sh baza va joriy baza bilan ikkita tayyor hosting arxivini yaratadi.
