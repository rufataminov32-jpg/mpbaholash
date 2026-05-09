import logging
import os
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ConversationHandler, filters, ContextTypes
)
from notion_client import Client

# ===================== SOZLAMALAR =====================
import os
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
NOTION_TOKEN = os.environ["NOTION_TOKEN"]
NOTION_DATABASE_ID = os.environ["NOTION_DATABASE_ID"]

# ===================== LOGGING =====================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===================== NOTION =====================
notion = Client(auth=NOTION_TOKEN)

# ===================== HOLATLAR =====================
(
    ROL_TANLASH,
    ISM_KIRISH,
    BAHOLANUVCHI_ISM,
    SAVOL_1, SAVOL_2, SAVOL_3, SAVOL_4, SAVOL_5,
    IZOH,
) = range(9)

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

# ===================== NOTION GA SAQLASH =====================
def notion_ga_saqlash(data: dict):
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
            "Umumiy ball": {"number": round(sum([
                data["ball_1"], data["ball_2"], data["ball_3"],
                data["ball_4"], data["ball_5"]
            ]) / 5, 2)},
            "Izoh": {"rich_text": [{"text": {"content": data.get("izoh", "")}}]},
        }
    )

# ===================== HANDLERLAR =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Xush kelibsiz!\n\n"
        "Bu bot xodimlarni 360° baholash uchun mo'ljallangan.\n\n"
        "Siz qanday rolda baholayapsiz?",
        reply_markup=ReplyKeyboardMarkup(
            [["👤 Xodim (o'zini baholaydi)", "👔 Rahbar (xodimni baholaydi)"]],
            resize_keyboard=True, one_time_keyboard=True
        )
    )
    return ROL_TANLASH

async def rol_tanlash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    matn = update.message.text
    if "Xodim" in matn:
        context.user_data["rol"] = "Xodim"
        await update.message.reply_text(
            "✍️ Ismingizni kiriting:",
            reply_markup=ReplyKeyboardRemove()
        )
        return ISM_KIRISH
    elif "Rahbar" in matn:
        context.user_data["rol"] = "Rahbar"
        await update.message.reply_text(
            "✍️ Ismingizni kiriting:",
            reply_markup=ReplyKeyboardRemove()
        )
        return ISM_KIRISH
    else:
        await update.message.reply_text("Iltimos, tugmadan tanlang.")
        return ROL_TANLASH

async def ism_kirish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["baholovchi"] = update.message.text.strip()
    if context.user_data["rol"] == "Xodim":
        context.user_data["baholanuvchi"] = update.message.text.strip()
        await update.message.reply_text(
            f"✅ Salom, {context.user_data['baholovchi']}!\n\n"
            f"{SAVOLLAR[0]}",
            reply_markup=BALL_KLAVIATURA
        )
        return SAVOL_1
    else:
        await update.message.reply_text(
            f"✅ Salom, {context.user_data['baholovchi']}!\n\n"
            "Baholaydigan xodimingizning ismini kiriting:"
        )
        return BAHOLANUVCHI_ISM

async def baholanuvchi_ism(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["baholanuvchi"] = update.message.text.strip()
    await update.message.reply_text(
        f"📋 {context.user_data['baholanuvchi']} uchun baholash boshlanadi.\n\n"
        f"{SAVOLLAR[0]}",
        reply_markup=BALL_KLAVIATURA
    )
    return SAVOL_1

async def savol_javob(update: Update, context: ContextTypes.DEFAULT_TYPE, savol_raqam: int):
    matn = update.message.text.strip()
    if matn not in ["1", "2", "3", "4", "5"]:
        await update.message.reply_text("Iltimos, 1 dan 5 gacha ball bering:", reply_markup=BALL_KLAVIATURA)
        return savol_raqam + SAVOL_1 - 1

    context.user_data[f"ball_{savol_raqam}"] = int(matn)

    if savol_raqam < 5:
        await update.message.reply_text(SAVOLLAR[savol_raqam], reply_markup=BALL_KLAVIATURA)
        return savol_raqam + SAVOL_1
    else:
        await update.message.reply_text(
            "💬 Qo'shimcha izoh yozing (yoki /skip bosing):",
            reply_markup=ReplyKeyboardRemove()
        )
        return IZOH

async def s1(update, context): return await savol_javob(update, context, 1)
async def s2(update, context): return await savol_javob(update, context, 2)
async def s3(update, context): return await savol_javob(update, context, 3)
async def s4(update, context): return await savol_javob(update, context, 4)
async def s5(update, context): return await savol_javob(update, context, 5)

async def izoh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["izoh"] = update.message.text.strip()
    return await saqlash(update, context)

async def skip_izoh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["izoh"] = ""
    return await saqlash(update, context)

async def saqlash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = context.user_data
    try:
        notion_ga_saqlash(data)
        umumiy = round(sum([data[f"ball_{i}"] for i in range(1, 6)]) / 5, 2)
        await update.message.reply_text(
            f"✅ Baholash muvaffaqiyatli saqlandi!\n\n"
            f"👤 Xodim: {data['baholanuvchi']}\n"
            f"📊 Umumiy ball: {umumiy}/5\n\n"
            f"Natijalar Notion ga yuborildi. Rahmat! 🙏\n\n"
            f"Yangi baholash uchun /start bosing."
        )
    except Exception as e:
        logger.error(f"Notion xatosi: {e}")
        await update.message.reply_text(
            "❌ Xatolik yuz berdi. NOTION_TOKEN va DATABASE_ID ni tekshiring.\n"
            f"Xato: {str(e)}"
        )
    return ConversationHandler.END

async def bekor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Baholash bekor qilindi.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# ===================== ASOSIY =====================
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ROL_TANLASH: [MessageHandler(filters.TEXT & ~filters.COMMAND, rol_tanlash)],
            ISM_KIRISH: [MessageHandler(filters.TEXT & ~filters.COMMAND, ism_kirish)],
            BAHOLANUVCHI_ISM: [MessageHandler(filters.TEXT & ~filters.COMMAND, baholanuvchi_ism)],
            SAVOL_1: [MessageHandler(filters.TEXT & ~filters.COMMAND, s1)],
            SAVOL_2: [MessageHandler(filters.TEXT & ~filters.COMMAND, s2)],
            SAVOL_3: [MessageHandler(filters.TEXT & ~filters.COMMAND, s3)],
            SAVOL_4: [MessageHandler(filters.TEXT & ~filters.COMMAND, s4)],
            SAVOL_5: [MessageHandler(filters.TEXT & ~filters.COMMAND, s5)],
            IZOH: [
                CommandHandler("skip", skip_izoh),
                MessageHandler(filters.TEXT & ~filters.COMMAND, izoh),
            ],
        },
        fallbacks=[CommandHandler("bekor", bekor)],
    )

    app.add_handler(conv)
    logger.info("Bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()
