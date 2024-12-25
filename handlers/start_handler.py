from telegram import Update
from telegram.ext import ContextTypes

from handlers.common import display_main_menu


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start. Показывает главное меню."""
    user = update.effective_user
    await display_main_menu(update, context)
