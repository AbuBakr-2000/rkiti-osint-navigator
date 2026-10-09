# RKITI OSINT — Mercator xarita va qo‘llanma yangilanishi

Ushbu paket mavjud OSINT Navigator dizayn tizimini saqlagan holda public interfeysni yangilaydi. SQLite katalogi, admin ma’lumotlari, Telegram bot murojaatlari va `data/` papkasiga tegmaydi.

## Paket tarkibi

- `app.py` — `/guide` marshruti va `.geojson` MIME turi;
- `static/index.html` — ixcham hero va umumiy qo‘llanma sahifasi;
- `static/styles.css` — 2D xarita, karusel va qo‘llanma responsiv uslublari;
- `static/app.js` — 7 yo‘nalishli karusellar, qidiruv va 3 bosqichli qo‘llanma;
- `static/i18n.js` — yangi tashrif uchun o‘zbek kirill yozuvi standart rejim;
- `static/world-map.js` — kutubxonasiz Mercator proyeksiyasi;
- `static/world-110m.geojson` — ixchamlashtirilgan Natural Earth mamlakat konturlari;
- `static/media/telegram-desktop-real.png` — haqiqiy Telegram Desktop interfeysi.

Eski `static/globe.js` olib tashlangan va WebGL ishlatilmaydi.

## Production serverga o‘rnatish

1. Loyiha katalogiga o‘ting:

   ```bash
   cd /home/rkiti-osint/osint-navigator
   ```

2. Yangilanishdan oldin amaldagi kodni zaxiralang:

   ```bash
   stamp="$(date +%Y%m%d-%H%M%S)"
   backup_dir="backups/mercator-guide-$stamp"
   mkdir -p "$backup_dir"
   cp -a app.py static "$backup_dir/"
   ```

3. Paketni alohida vaqtinchalik katalogga oching:

   ```bash
   update_dir="/tmp/rkiti-osint-mercator-guide-$stamp"
   mkdir -p "$update_dir"
   unzip -q rkiti-osint-mercator-guide-update-20260911.zip -d "$update_dir"
   ```

4. Paket tarkibini tekshiring:

   ```bash
   find "$update_dir" -maxdepth 4 -type f -print
   ```

5. Faqat paketdagi kod va statik fayllarni nusxalang:

   ```bash
   cp -a "$update_dir/app.py" ./app.py
   cp -a "$update_dir/static/." ./static/
   ```

6. Python sintaksisini tekshiring:

   ```bash
   python -m py_compile app.py wsgi.py bot_setup.py
   ```

7. AlwaysData paneli orqali WSGI saytni qayta ishga tushiring. Oddiy Linux serverida esa institutda qo‘llanadigan servis boshqaruvchisi orqali jarayonni restart qiling.

8. Quyidagilarni tekshiring:

   - `/` bosh sahifa, 2D xarita va indikator qidiruvi;
   - `/category/telegram` va boshqa kategoriya sahifalari;
   - `/guide` interaktiv qo‘llanma;
   - karusel tugmalari, klaviatura va touch scroll;
   - dark/light va `UZ / ЎЗ` rejimlari;
   - mutaxassis bilan aloqa menyusi;
   - `/admin/` kirish va katalog boshqaruvi.

## Muhim saqlash qoidasi

Yangilanish va rollback vaqtida quyidagilarni almashtirmang yoki o‘chirmang:

- `data/`;
- `.env`;
- bot orqali yuborilgan fayllar papkasi;
- production parollari va secretlar.

## Rollback

Muammo kuzatilsa, zaxiradagi fayllarni qaytaring va sayt jarayonini restart qiling:

```bash
cp -a "$backup_dir/app.py" ./app.py
cp -a "$backup_dir/static/." ./static/
```

## Manbalar va litsenziya

- Xarita geoma’lumotlari: Natural Earth, public domain.
- Telegram Desktop skrinshoti: Telegram LLC, Wikimedia Commons, GPLv3 yoki undan keyingi versiya.
