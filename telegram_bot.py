from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from config import TELEGRAM_TOKEN


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Бот запущен"
    )


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    print("Получено сообщение:", text)

    await update.message.reply_text(
        f"Получил: {text}"
    )


def run_telegram_bot():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        MessageHandler(filters.TEXT, message_handler)
    )

    print("Telegram бот запущен")

    app.run_polling()