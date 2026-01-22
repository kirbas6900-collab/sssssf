import datetime
import calendar
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

TOKEN = "8533132786:AAGW6a8UH_J0NwrlIfeeBMpnA8voilfrxAA"
CHAT_ID = None

PERCENT, SHIFT, CASH, BONUS = range(4)

salary_data = {
    "first": [],
    "second": []
}

def get_period():
    day = datetime.datetime.now().day
    return "first" if day <= 14 else "second"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global CHAT_ID
    CHAT_ID = update.message.chat_id

    keyboard = [["💰 Узнать ЗП", "📝 Отчет о смене"]]
    await update.message.reply_text(
        "Выберите действие:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

# -------- ОТЧЕТ --------

async def report_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите % с продажи:")
    return PERCENT

async def percent_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["percent"] = float(update.message.text)
    await update.message.reply_text("Введите выход за смену:")
    return SHIFT

async def shift_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["shift"] = float(update.message.text)
    await update.message.reply_text("Введите сумму кассы:")
    return CASH

async def cash_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["cash"] = float(update.message.text)
    await update.message.reply_text("Введите премии (если нет — 0):")
    return BONUS

async def bonus_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bonus = float(update.message.text)
    data = context.user_data

    total = (data["cash"] * data["percent"] / 100) + data["shift"] + bonus
    period = get_period()
    salary_data[period].append(total)

    await update.message.reply_text(
        f"✅ Отчет сохранен\nЗаработано за смену: {total:.2f}"
    )
    return ConversationHandler.END

# -------- ЗП --------

async def salary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    period = get_period()
    total = sum(salary_data[period])
    name = "1–14" if period == "first" else "15–конец месяца"

    await update.message.reply_text(
        f"💰 Ваша ЗП за период {name}:\n{total:.2f}"
    )

# -------- АВТОВЫПЛАТА --------

async def auto_payout(context: ContextTypes.DEFAULT_TYPE):
    global CHAT_ID
    if CHAT_ID is None:
        return

    today = datetime.datetime.now()
    day = today.day
    last_day = calendar.monthrange(today.year, today.month)[1]

    if day == 15:
        period, name = "first", "1–14"
    elif day == last_day:
        period, name = "second", "15–конец месяца"
    else:
        return

    total = sum(salary_data[period])
    salary_data[period].clear()

    await context.bot.send_message(
        chat_id=CHAT_ID,
        text=f"💸 Выплата ЗП\nПериод: {name}\nИтого: {total:.2f}"
    )

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & filters.Regex("Отчет"), report_start)],
        states={
            PERCENT: [MessageHandler(filters.TEXT, percent_step)],
            SHIFT: [MessageHandler(filters.TEXT, shift_step)],
            CASH: [MessageHandler(filters.TEXT, cash_step)],
            BONUS: [MessageHandler(filters.TEXT, bonus_step)],
        },
        fallbacks=[]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("ЗП"), salary))
    app.add_handler(conv)

    app.job_queue.run_daily(
        auto_payout,
        time=datetime.time(hour=10, minute=0)
    )

    app.run_polling()

if __name__ == "__main__":
    main()
