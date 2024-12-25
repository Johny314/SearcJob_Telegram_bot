from telegram import Update
from telegram.ext import ContextTypes
from handlers.common import generate_back_button, send_menu


async def about_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик отображения информации 'О боте'."""
    about_message = (
        "Этот бот предназначен для поиска вакансий на платформе hh.ru "
        "и анализа ключевых компетенций на основе текстов вакансий."
    )
    await send_menu(update, about_message, reply_markup=generate_back_button())
