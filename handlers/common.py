import os

from dotenv import load_dotenv
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import ContextTypes, ConversationHandler

# Загрузка переменных окружения
load_dotenv()

ANALYZE_WAITING_FOR_QUERY = int(os.getenv("ANALYZE_WAITING_FOR_QUERY"))
SEARCH_WAITING_FOR_QUERY = int(os.getenv("SEARCH_WAITING_FOR_QUERY"))

def generate_main_menu():
    """Генерация главного меню."""
    keyboard = [
        [InlineKeyboardButton("🔍 Поиск вакансий", callback_data="action_search")],
        [InlineKeyboardButton("🧩 Анализ навыков", callback_data="action_analyze")],
        [InlineKeyboardButton("ℹ️ О боте", callback_data="action_about")]
    ]
    return InlineKeyboardMarkup(keyboard)


def generate_back_button():
    """Генерация кнопки возврата в главное меню."""
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data="action_back")]])


async def send_menu(update, message: str, reply_markup=None):
    """Универсальная функция для отправки сообщения с меню."""
    if update.message:
        await update.message.reply_text(message, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup)


async def display_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отображает главное меню."""
    reply_markup = generate_main_menu()
    await send_menu(update, "Выберите действие из меню:", reply_markup)

async def handle_new_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Ожидание ввода нового текстового запроса от пользователя.
    """
    callback_data = update.callback_query.data

    # Определяем, какое состояние возвращать (поиск или анализ)
    if callback_data == "search_new_query":
        state = SEARCH_WAITING_FOR_QUERY
    elif callback_data == "analyze_new_query":
        state = ANALYZE_WAITING_FOR_QUERY
    else:
        # Если коллбэк некорректный, возвращаем в главное меню
        await display_main_menu(update, context)
        return ConversationHandler.END

    # Спрашиваем у пользователя текст запроса
    await context.bot.send_message(
        chat_id=update.callback_query.message.chat_id,
        text="Введите текст вашего запроса:"
    )
    return state

async def handle_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик кнопки "⬅️ Назад", возвращает пользователя в главное меню.
    """
    await display_main_menu(update, context)
    return ConversationHandler.END
