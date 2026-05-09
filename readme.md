# HR Baholash Telegram Boti — Qo'llanma

## 1. Kutubxonalarni o'rnating
```bash
pip install -r requirements.txt
```

## 2. bot.py ni oching va ushbu 3 qatorni to'ldiring
```python
TELEGRAM_TOKEN = "BU_YERGA_TELEGRAM_TOKEN_YOZING"
NOTION_TOKEN   = "BU_YERGA_NOTION_TOKEN_YOZING"
NOTION_DATABASE_ID = "BU_YERGA_NOTION_DATABASE_ID_YOZING"
```

## 3. Notion Database ustunlarini yarating
Notion da yangi Database oching va quyidagi ustunlarni qo'shing:

| Ustun nomi            | Turi   |
|-----------------------|--------|
| Xodim ismi            | Title  |
| Baholovchi            | Text   |
| Rol                   | Select (Xodim / Rahbar) |
| Vazifalarni bajarish  | Number |
| Jamoada ishlash       | Number |
| Muammo hal qilish     | Number |
| Kommunikatsiya        | Number |
| Tashabbuskorlik       | Number |
| Umumiy ball           | Number |
| Izoh                  | Text   |

## 4. Botni ishga tushiring
```bash
python bot.py
```

## Bot qanday ishlaydi?
- /start — baholashni boshlaydi
- Rol tanlanadi: Xodim yoki Rahbar
- 5 ta savol (1-5 ball)
- Ixtiyoriy izoh (/skip — o'tkazib yuborish)
- Natija avtomatik Notion ga saqlanadi

## /bekor — baholashni to'xtatish
```
