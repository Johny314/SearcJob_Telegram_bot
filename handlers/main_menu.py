from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes


# Генерация главного меню
async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает команду /start. Показывает главное меню."""
    keyboard = [
        [
            InlineKeyboardButton("Поиск 🔍", callback_data="search"),
            InlineKeyboardButton("Анализ 📊", callback_data="analyze"),
        ],
        [
            InlineKeyboardButton("О боте ℹ️", callback_data="about"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            "Выберите действие:", reply_markup=reply_markup
        )