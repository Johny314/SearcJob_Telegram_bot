from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from handlers.common import send_menu, generate_back_button
from services.database_service import get_last_searches, add_to_search_history
from services.search_service import fetch_vacancies

# Константы для идентификации шагов
SEARCH_WAITING_FOR_QUERY = 0


async def prompt_search_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Промежуточный шаг: предлагает ввести текстовый запрос для поиска вакансий.
    """
    user_id = update.callback_query.from_user.id

    # Получаем историю запросов пользователя
    history = await get_last_searches(user_id=user_id, limit=5)

    # Формируем кнопки истории
    buttons = []
    for query in history:
        buttons.append([InlineKeyboardButton(query, callback_data=f"search_query_{query}")])

    # Добавляем кнопку для ручного ввода нового запроса
    buttons.append([InlineKeyboardButton("Введите новый запрос", callback_data="search_new_query")])

    # Добавляем кнопку "Назад"
    buttons.append([InlineKeyboardButton("⬅️ Назад", callback_data="action_back")])

    # Формируем разметку кнопок
    reply_markup = InlineKeyboardMarkup(buttons)

    # Отправляем сообщение с предложением ввести данные
    await send_menu(update, "Введите текст для поиска или выберите из истории:", reply_markup)
    return SEARCH_WAITING_FOR_QUERY


async def execute_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Выполняет поиск вакансий по запросу.
    """
    user_id = update.message.from_user.id
    query = update.message.text

    # Сохраняем запрос в историю
    await add_to_search_history(user_id=user_id, search_query=query)

    # Запрашиваем вакансии через сервис
    try:
        data = await fetch_vacancies(query=query, page=0, per_page=5)

        if data and data.get("items"):
            results = "\n\n".join(
                f"{item['name']} — {item['employer']['name']}\n{item['alternate_url']}"
                for item in data["items"]
            )
        else:
            results = "По вашему запросу вакансий не найдено."
    except Exception as e:
        results = f"Произошла ошибка: {e}"

    # Отправляем результаты
    await context.bot.send_message(chat_id=update.message.chat_id, text=results)


async def search_query_from_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает выбор запроса из истории.
    Выполняет поиск по выбранному запросу.
    """
    query = update.callback_query.data.removeprefix("search_query_")

    # Выполняем поиск так же, как в execute_search()
    try:
        data = await fetch_vacancies(query=query, page=0, per_page=5)

        if data and data.get("items"):
            results = "\n\n".join(
                f"{item['name']} — {item['employer']['name']}\n{item['alternate_url']}"
                for item in data["items"]
            )
        else:
            results = "По вашему запросу вакансий не найдено."
    except Exception as e:
        results = f"Произошла ошибка: {e}"

    # Отправляем результаты
    await send_menu(update, results, reply_markup=generate_back_button())
