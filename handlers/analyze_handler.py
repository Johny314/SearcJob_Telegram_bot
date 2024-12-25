from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from constants import ANALYZE_WAITING_FOR_QUERY
from services import fetch_vacancies, extract_skills, process_vacancies, format_skills_output # Импорт корректных функций
from handlers.common import send_menu


async def prompt_analyze_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Предлагает пользователю ввести запрос для анализа навыков или выбрать запрос из истории.
    """
    # Достаем историю запросов пользователя
    user_data = context.user_data
    history = user_data.get("analyze_query_history", [])

    # Формируем кнопки: сначала для истории, потом другие действия
    buttons = []
    if history:
        for query in history:
            buttons.append([InlineKeyboardButton(query, callback_data=f"analyze_query_{query}")])

    # Добавляем кнопку для ввода нового запроса и возврата
    buttons.append([InlineKeyboardButton("Ввести новый запрос для анализа", callback_data="analyze_new_query")])
    buttons.append([InlineKeyboardButton("⬅️ Назад", callback_data="action_back")])

    reply_markup = InlineKeyboardMarkup(buttons)

    # Отправляем сообщение
    await send_menu(update, "Выберите действие для анализа навыков:", reply_markup)
    return ANALYZE_WAITING_FOR_QUERY


async def execute_analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Выполняет анализ навыков на основе текста, введенного пользователем.
    """
    user_id = update.message.from_user.id
    query = update.message.text

    # Проверка текста запроса
    query = query.strip() if query else None
    if not query:
        await context.bot.send_message(chat_id=update.message.chat_id, text="Пожалуйста, введите текст для анализа.")
        return ANALYZE_WAITING_FOR_QUERY

    # Сохраняем запрос в историю
    user_data = context.user_data
    history = user_data.get("analyze_query_history", [])
    if query not in history:
        history.append(query)
        user_data["analyze_query_history"] = history

    # Выполняем запрос API
    data = await fetch_vacancies(query=query, page=0, per_page=50)

    if not data or "items" not in data:
        await context.bot.send_message(
            chat_id=update.message.chat_id,
            text="Не удалось получить данные о вакансиях. Попробуйте ещё раз."
        )
        return ConversationHandler.END

    # Анализируем данные
    top_skills, total_vacancies = process_vacancies(data)

    # Формируем результат
    if total_vacancies > 0 and top_skills:
        results = format_skills_output(top_skills, total_vacancies)
    else:
        results = "Не удалось извлечь навыки из предоставленных вакансий."

    # Отправляем результат пользователю
    await context.bot.send_message(chat_id=update.message.chat_id, text=results)
    return ConversationHandler.END


async def analyze_query_from_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Выполняет анализ навыков на основе выбранного запроса из истории.
    """
    query = update.callback_query.data

    # Извлекаем текст запроса из callback_data
    query = query.removeprefix("analyze_query_").strip() if query else None
    if not query:
        await context.bot.send_message(
            chat_id=update.callback_query.message.chat_id,
            text="Запрос из истории отсутствует или некорректен."
        )
        return ConversationHandler.END

    try:
        # Выполняем поиск вакансий
        data = await fetch_vacancies(query=query, page=0, per_page=50)

        # Проверяем корректность данных
        if not data or "items" not in data:
            await context.bot.send_message(
                chat_id=update.callback_query.message.chat_id,
                text="К сожалению, мы не смогли получить данные. Попробуйте ещё раз."
            )
            return ConversationHandler.END

        # Анализируем данные
        top_skills, total_vacancies = process_vacancies(data)

        # Формируем результат
        if total_vacancies > 0 and top_skills:
            results = format_skills_output(top_skills, total_vacancies)
        else:
            results = "Не удалось извлечь навыки из предоставленных вакансий."

        # Отправляем результат
        await context.bot.send_message(chat_id=update.callback_query.message.chat_id, text=results)
    except Exception as e:
        await context.bot.send_message(
            chat_id=update.callback_query.message.chat_id,
            text=f"Произошла ошибка при анализе навыков: {e}"
        )
        print(f"Ошибка выполнения анализа из истории: {e}")

    return ConversationHandler.END


