import os
import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ConversationHandler, filters, ContextTypes, CallbackQueryHandler
)
from notion_client import Client

# ===================== SOZLAMALAR =====================
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
NOTION_TOKEN = os.environ["NOTION_TOKEN"]
NOTION_DATABASE_ID = os.environ["NOTION_DATABASE_ID"]
ADMIN_ID = int(os.environ.get("ADMIN_ID", "8249797818"))

# Xodimlar ro'yxati (xotirada saqlanadi)
# Format: {telegram_id: "Ism Familiya"}
xodimlar = {}

# ===================== LOGGING =====================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===================== NOTION =====================
notion = Client(auth=NOTION_TOKEN)

# ===================== HOLATLAR =====================
(
    ROL_TANLASH,
    BAHOLANUVCHI_TANLASH,
    SAVOL_1, SAVOL_2, SAVOL_3, SAVOL_4, SAVOL_5,
    IZOH,
    ADMIN_XODIM_ISM,
    ADMIN_XODIM_ID,
) = range(10)

# ===================== SAVOLLAR =====================
SAVOLLAR = [
    "1️⃣ Vazifalarni o'z vaqtida bajarish\n(1 = juda past, 5 = a'lo)",
    "2️⃣ Jamoada ishlash va hamkorlik\n(1 = juda past, 5 = a'lo)",
    "3️⃣ Muammolarni mustaqil hal qilish\n(1 = juda past, 5 = a'lo)",
    "4️⃣ Kommunikatsiya va muloqot\n(1 = juda past, 5 = a'lo)",
    "5️⃣ Tashabbuskorlik va yangi g'oyalar\n(1 = juda past, 5 = a'lo)",
]

BALL_KLAVIATURA = ReplyKeyboardMarkup(
    [["1", "2", "3", "4", "5"]], resize_keyboard=True, one_time_keyboard=True
)

# ===================== YORDAMCHI =====================
def admin_tekshir(user_id): return user_id == ADMIN_ID
def xodim_tekshir(user_id): return user_id in xodimlar

# ===================== NOTION =====================
def notion_ga_saqlash(data):
    notion.pages.create(
        parent={"database_id": NOTION_DATABASE_ID},
        properties={
            "Xodim ismi": {"title": [{"text": {"content": data["baholanuvchi"]}}]},
            "Baholovchi": {"rich_text": [{"text": {"content": data["baholovchi"]}}]},
            "Rol": {"select": {"name": data["rol"]}},
            "Vazifalarni bajarish": {"number": data["ball_1"]},
            "Jamoada ishlash": {"number": data["ball_2"]},
            "Muammo hal qilish": {"number": data["ball_3"]},
            "Kommunikatsiya": {"number": data["ball_4"]},
            "Tashabbuskorlik": {"number": data["ball_5"]},
            "Umumiy ball": {"number": round(sum([data[f"ball_{i}"] for i in range(1,6)]) / 5, 2)},
            "Izoh": {"rich_text": [{"text": {"content": data.get("izoh", "")}}]},
        }
    )

def notion_dan_natijalar():
    return notion.databases.query(database_id=NOTION_DATABASE_ID).get("results", [])

# ===================== START =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if admin_tekshir(user_id):
        await update.message.reply_text(
            "👋 Salom, Admin!\n\n"
            "📋 *Buyruqlar:*\n"
            "/add\\_employee — xodim qo'shish\n"
            "/list\\_employees — xodimlar ro'yxati\n"
            "/remove\\_employee — xodim o'chirish\n"
            "/results — so'nggi natijalar\n"
            "/remind — eslatma yuborish\n"
            "/baholash — baholashni boshlash",
            parse_mode="Markdown"
        )
        return ConversationHandler.END
    if not xodim_tekshir(user_id):
        await update.message.reply_text("❌ Siz ro'yxatda yo'qsiz.\nAdmin bilan bog'laning.")
        return ConversationHandler.END
    await update.message.reply_text(
        f"👋 Salom, {xodimlar[user_id]}!\n\n/baholash — baholashni boshlash"
    )
    return ConversationHandler.END

# ===================== BAHOLASH =====================
async def baholash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not xodim_tekshir(user_id) and not admin_tekshir(user_id):
        await update.message.reply_text("❌ Siz ro'yxatda yo'qsiz.")
        return ConversationHandler.END
    await update.message.reply_text(
        "Siz qanday rolda baholayapsiz?",
        reply_markup=ReplyKeyboardMarkup(
            [["👤 Xodim (o'zini baholaydi)", "👔 Rahbar (xodimni baholaydi)"]],
            resize_keyboard=True, one_time_keyboard=True
        )
    )
    return ROL_TANLASH

async def rol_tanlash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    matn = update.message.text
    context.user_data["baholovchi"] = xodimlar.get(user_id, update.effective_user.full_name)

    if "Xodim" in matn:
        context.user_data["rol"] = "Xodim"
        context.user_data["baholanuvchi"] = xodimlar.get(user_id, update.effective_user.full_name)
        await update.message.reply_text(SAVOLLAR[0], reply_markup=BALL_KLAVIATURA)
        return SAVOL_1
    elif "Rahbar" in matn:
        context.user_data["rol"] = "Rahbar"
        if not xodimlar:
            await update.message.reply_text("❌ Xodimlar ro'yxati bo'sh.", reply_markup=ReplyKeyboardRemove())
            return ConversationHandler.END
        tugmalar = [[ism] for uid, ism in xodimlar.items() if uid != user_id]
        if not tugmalar:
            await update.message.reply_text("❌ Baholanadigan xodim yo'q.", reply_markup=ReplyKeyboardRemove())
            return ConversationHandler.END
        await update.message.reply_text(
            "Qaysi xodimni baholaysiz?",
            reply_markup=ReplyKeyboardMarkup(tugmalar, resize_keyboard=True, one_time_keyboard=True)
        )
        return BAHOLANUVCHI_TANLASH
    await update.message.reply_text("Iltimos, tugmadan tanlang.")
    return ROL_TANLASH

async def baholanuvchi_tanlash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["baholanuvchi"] = update.message.text.strip()
    await update.message.reply_text(
        f"📋 {context.user_data['baholanuvchi']} uchun baholash:\n\n{SAVOLLAR[0]}",
        reply_markup=BALL_KLAVIATURA
    )
    return SAVOL_1

async def savol_javob(update: Update, context: ContextTypes.DEFAULT_TYPE, n: int):
    matn = update.message.text.strip()
    if matn not in ["1","2","3","4","5"]:
        await update.message.reply_text("Iltimos, 1-5 orasida ball bering:", reply_markup=BALL_KLAVIATURA)
        return SAVOL_1 + n - 1
    context.user_data[f"ball_{n}"] = int(matn)
    if n < 5:
        await update.message.reply_text(SAVOLLAR[n], reply_markup=BALL_KLAVIATURA)
        return SAVOL_1 + n
    await update.message.reply_text("💬 Izoh yozing (yoki /skip):", reply_markup=ReplyKeyboardRemove())
    return IZOH

async def s1(u, c): return await savol_javob(u, c, 1)
async def s2(u, c): return await savol_javob(u, c, 2)
async def s3(u, c): return await savol_javob(u, c, 3)
async def s4(u, c): return await savol_javob(u, c, 4)
async def s5(u, c): return await savol_javob(u, c, 5)

async def izoh_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["izoh"] = update.message.text.strip()
    return await saqlash(update, context)

async def skip_izoh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["izoh"] = ""
    return await saqlash(update, context)

async def saqlash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = context.user_data
    try:
        notion_ga_saqlash(data)
        umumiy = round(sum([data[f"ball_{i}"] for i in range(1,6)]) / 5, 2)
        await update.message.reply_text(
            f"✅ Saqlandi!\n\n👤 {data['baholanuvchi']}\n📊 Umumiy ball: {umumiy}/5\n\nRahmat! 🙏"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Xatolik: {str(e)}")
    return ConversationHandler.END

# ===================== ADMIN BUYRUQLARI =====================
async def add_employee_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_tekshir(update.effective_user.id):
        await update.message.reply_text("❌ Faqat admin uchun.")
        return ConversationHandler.END
    await update.message.reply_text("Xodimning to'liq ismini kiriting:", reply_markup=ReplyKeyboardRemove())
    return ADMIN_XODIM_ISM

async def add_employee_ism(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["yangi_ism"] = update.message.text.strip()
    await update.message.reply_text(
        f"✅ Ism: {context.user_data['yangi_ism']}\n\n"
        "Endi xodimning Telegram ID sini kiriting.\n"
        "(Xodim @userinfobot ga /start yuborisin)"
    )
    return ADMIN_XODIM_ID

async def add_employee_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        uid = int(update.message.text.strip())
        ism = context.user_data["yangi_ism"]
        xodimlar[uid] = ism
        await update.message.reply_text(f"✅ {ism} ro'yxatga qo'shildi!\nID: {uid}")
    except ValueError:
        await update.message.reply_text("❌ Noto'g'ri ID. Qaytadan /add_employee bosing.")
    return ConversationHandler.END

async def list_employees(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_tekshir(update.effective_user.id):
        await update.message.reply_text("❌ Faqat admin uchun.")
        return
    if not xodimlar:
        await update.message.reply_text("📋 Xodimlar ro'yxati bo'sh.")
        return
    matn = "📋 *Xodimlar ro'yxati:*\n\n"
    for uid, ism in xodimlar.items():
        matn += f"👤 {ism}\n"
    await update.message.reply_text(matn, parse_mode="Markdown")

async def remove_employee(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_tekshir(update.effective_user.id):
        await update.message.reply_text("❌ Faqat admin uchun.")
        return
    if not xodimlar:
        await update.message.reply_text("📋 Xodimlar ro'yxati bo'sh.")
        return
    tugmalar = [[InlineKeyboardButton(ism, callback_data=f"del_{uid}")] for uid, ism in xodimlar.items()]
    await update.message.reply_text("Qaysi xodimni o'chirmoqchisiz?", reply_markup=InlineKeyboardMarkup(tugmalar))

async def remove_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = int(query.data.replace("del_", ""))
    if uid in xodimlar:
        ism = xodimlar.pop(uid)
        await query.edit_message_text(f"✅ {ism} o'chirildi.")
    else:
        await query.edit_message_text("❌ Topilmadi.")

async def results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_tekshir(update.effective_user.id):
        await update.message.reply_text("❌ Faqat admin uchun.")
        return
    try:
        natijalar = notion_dan_natijalar()
        if not natijalar:
            await update.message.reply_text("📊 Hozircha natijalar yo'q.")
            return
        matn = "📊 *So'nggi 5 ta baholash:*\n\n"
        for item in natijalar[:5]:
            p = item["properties"]
            ism = p["Xodim ismi"]["title"][0]["text"]["content"] if p["Xodim ismi"]["title"] else "—"
            ball = p["Umumiy ball"]["number"] or 0
            rol = p["Rol"]["select"]["name"] if p["Rol"]["select"] else "—"
            matn += f"👤 {ism} | {rol} | ⭐ {ball}/5\n"
        await update.message.reply_text(matn, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Xatolik: {str(e)}")

async def remind(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_tekshir(update.effective_user.id):
        await update.message.reply_text("❌ Faqat admin uchun.")
        return
    if not xodimlar:
        await update.message.reply_text("❌ Xodimlar ro'yxati bo'sh.")
        return
    yuborildi = 0
    for uid in xodimlar:
        try:
            await context.bot.send_message(
                chat_id=uid,
                text="🔔 Eslatma: Baholash vaqti keldi!\n/baholash buyrug'ini yuboring."
            )
            yuborildi += 1
        except Exception as e:
            logger.warning(f"Eslatma yuborilmadi {uid}: {e}")
    await update.message.reply_text(f"✅ {yuborildi} ta xodimga eslatma yuborildi.")

async def bekor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Bekor qilindi.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# ===================== ASOSIY =====================
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    baholash_conv = ConversationHandler(
        entry_points=[CommandHandler("baholash", baholash)],
        states={
            ROL_TANLASH: [MessageHandler(filters.TEXT & ~filters.COMMAND, rol_tanlash)],
            BAHOLANUVCHI_TANLASH: [MessageHandler(filters.TEXT & ~filters.COMMAND, baholanuvchi_tanlash)],
            SAVOL_1: [MessageHandler(filters.TEXT & ~filters.COMMAND, s1)],
            SAVOL_2: [MessageHandler(filters.TEXT & ~filters.COMMAND, s2)],
            SAVOL_3: [MessageHandler(filters.TEXT & ~filters.COMMAND, s3)],
            SAVOL_4: [MessageHandler(filters.TEXT & ~filters.COMMAND, s4)],
            SAVOL_5: [MessageHandler(filters.TEXT & ~filters.COMMAND, s5)],
            IZOH: [
                CommandHandler("skip", skip_izoh),
                MessageHandler(filters.TEXT & ~filters.COMMAND, izoh_handler),
            ],
        },
        fallbacks=[CommandHandler("bekor", bekor)],
    )

    add_conv = ConversationHandler(
        entry_points=[CommandHandler("add_employee", add_employee_start)],
        states={
            ADMIN_XODIM_ISM: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_employee_ism)],
            ADMIN_XODIM_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_employee_id)],
        },
        fallbacks=[CommandHandler("bekor", bekor)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(baholash_conv)
    app.add_handler(add_conv)
    app.add_handler(CommandHandler("list_employees", list_employees))
    app.add_handler(CommandHandler("remove_employee", remove_employee))
    app.add_handler(CommandHandler("results", results))
    app.add_handler(CommandHandler("remind", remind))
    app.add_handler(CallbackQueryHandler(remove_callback, pattern="^del_"))

    logger.info("Bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()
